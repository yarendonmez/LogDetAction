import os
os.environ["PYTHONUTF8"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import json
import re
import time
from pathlib import Path

import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel


# =========================================================
# PATH AYARLARI
# =========================================================

base_model_name = "mistralai/Mistral-7B-Instruct-v0.2"

adapter_path = r"C:\developer\LogDetAction\v2.0\qlora_test_model"

test_path = Path(r"C:\developer\LogDetAction\v2.0\split\test.jsonl")

results_path = Path(r"C:\developer\LogDetAction\v2.0\evaluation_qlora_test_results.csv")


# =========================================================
# LABEL ÇIKARMA
# =========================================================

def extract_label(text):
    match = re.search(
        r"Label:\s*(benign|suspicious|malicious)|\b(benign|suspicious|malicious)\b",
        text,
        re.I
    )

    if not match:
        return None

    return (match.group(1) or match.group(2)).lower()


def to_attack_label(label):
    if label == "malicious":
        return "attack"
    if label in ["benign", "suspicious"]:
        return "non_attack"
    return None


# =========================================================
# MODEL YÜKLEME
# =========================================================

print("CUDA aktif mi?", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

print("\nTokenizer yükleniyor...")
tokenizer = AutoTokenizer.from_pretrained(base_model_name)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

print("\nBase model yükleniyor...")
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    quantization_config=bnb_config,
    device_map={"": 0},
    dtype=torch.float16,
)

print("\nQLoRA adapter yükleniyor...")
model = PeftModel.from_pretrained(base_model, adapter_path)

model.eval()


# =========================================================
# PROMPT FORMAT
# =========================================================

def build_prompt(log_entry):
    return f"""### Instruction:
Analyze the following cybersecurity log entry. Classify it as benign, suspicious, or malicious. Then provide a short technical explanation and one recommended action.

### Input:
{log_entry}

### Response:
"""


# =========================================================
# INFERENCE
# =========================================================

def ask_model(log_entry):
    prompt = build_prompt(log_entry)

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512
    ).to(model.device)

    start_time = time.time()

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=160,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )

    end_time = time.time()

    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Prompt kısmını cevaptan temizlemeye çalışıyoruz.
    if "### Response:" in full_text:
        answer = full_text.split("### Response:")[-1].strip()
    else:
        answer = full_text.strip()

    return answer, end_time - start_time


# =========================================================
# EVALUATION
# =========================================================

three_class_correct = 0
attack_correct = 0
total = 0

results = []

with open(test_path, "r", encoding="utf-8") as f:
    for i in range(10):
        item = json.loads(next(f))

        log_entry = item["input"]
        true_label = extract_label(item["output"])

        model_answer, inference_time = ask_model(log_entry)

        pred_label = extract_label(model_answer)

        true_attack_label = to_attack_label(true_label)
        pred_attack_label = to_attack_label(pred_label)

        three_class_ok = pred_label == true_label
        attack_ok = pred_attack_label == true_attack_label

        total += 1

        if three_class_ok:
            three_class_correct += 1

        if attack_ok:
            attack_correct += 1

        results.append({
            "sample_id": i + 1,
            "true_label": true_label,
            "predicted_label": pred_label,
            "three_class_correct": three_class_ok,
            "true_attack_label": true_attack_label,
            "pred_attack_label": pred_attack_label,
            "attack_detection_correct": attack_ok,
            "inference_time_sec": round(inference_time, 3),
            "log_preview": log_entry[:160],
            "model_answer": model_answer
        })

        print("=" * 80)
        print(f"Sample {i + 1}")
        print("TRUE LABEL:", true_label)
        print("PRED LABEL:", pred_label)
        print("TRUE ATTACK LABEL:", true_attack_label)
        print("PRED ATTACK LABEL:", pred_attack_label)
        print("3-CLASS CORRECT:", three_class_ok)
        print("ATTACK DETECTION CORRECT:", attack_ok)
        print(f"Inference Time: {inference_time:.3f} sec")

        print("\nLOG:")
        print(log_entry[:300])

        print("\nMODEL ANSWER:")
        print(model_answer)

three_class_accuracy = three_class_correct / total
attack_accuracy = attack_correct / total

print("=" * 80)
print(f"3-Class Accuracy: {three_class_correct}/{total} = {three_class_accuracy:.2f}")
print(f"Attack Detection Accuracy: {attack_correct}/{total} = {attack_accuracy:.2f}")

df = pd.DataFrame(results)
df.to_csv(results_path, index=False, encoding="utf-8-sig")

print("\nQLoRA evaluation sonuçları kaydedildi:")
print(results_path)

print("\nOrtalama inference süresi:")
print(round(df["inference_time_sec"].mean(), 3), "sec")