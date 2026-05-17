"""
Loads base model + LoRA adapters once at startup.
Exposes singletons used by pipeline_service.
"""
import time
import logging
import os

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Shared singletons ─────────────────────────────────────────────────────────
tokenizer = None
model = None
model_loaded: bool = False
model_error: str | None = None
load_timings: dict = {}


def load_models() -> None:
    global tokenizer, model, model_loaded, model_error, load_timings

    total_start = time.time()
    timings: dict = {}

    try:
        device_info = (
            torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
        )
        logger.info("Loading models on device: %s", device_info)

        # Tokenizer
        t0 = time.time()
        tok = AutoTokenizer.from_pretrained(settings.BASE_MODEL_ID)
        tok.pad_token = tok.eos_token
        tok.padding_side = "right"
        timings["tokenizer_sec"] = round(time.time() - t0, 2)
        logger.info("Tokenizer loaded in %.2fs", timings["tokenizer_sec"])

        # BitsAndBytes quantization config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

        # Base model
        t0 = time.time()
        base = AutoModelForCausalLM.from_pretrained(
            settings.BASE_MODEL_ID,
            quantization_config=bnb_config,
            device_map={"": 0},
            torch_dtype=torch.float16,
        )
        timings["base_model_sec"] = round(time.time() - t0, 2)
        logger.info("Base model loaded in %.2fs", timings["base_model_sec"])

        # Classifier adapter (LLM-A)
        t0 = time.time()
        peft_model = PeftModel.from_pretrained(
            base,
            settings.CLASSIFIER_ADAPTER_PATH,
            adapter_name="classifier",
        )
        timings["classifier_adapter_sec"] = round(time.time() - t0, 2)
        logger.info("Classifier adapter loaded in %.2fs", timings["classifier_adapter_sec"])

        # Analysis adapter (LLM-B / LLM-C)
        t0 = time.time()
        peft_model.load_adapter(
            settings.ANALYSIS_ADAPTER_PATH,
            adapter_name="analysis",
        )
        timings["analysis_adapter_sec"] = round(time.time() - t0, 2)
        logger.info("Analysis adapter loaded in %.2fs", timings["analysis_adapter_sec"])

        peft_model.eval()

        timings["total_sec"] = round(time.time() - total_start, 2)
        logger.info("All models ready in %.2fs", timings["total_sec"])

        tokenizer = tok
        model = peft_model
        model_loaded = True
        load_timings = timings

    except Exception as exc:
        model_error = str(exc)
        model_loaded = False
        logger.exception("Model loading failed: %s", exc)
