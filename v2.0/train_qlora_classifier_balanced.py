import os

os.environ["PYTHONUTF8"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from pathlib import Path
from collections import Counter

import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from bitsandbytes.optim import PagedAdamW8bit
from tqdm import tqdm


model_name = "mistralai/Mistral-7B-Instruct-v0.2"

train_path = r"C:\developer\LogDetAction\v2.0\split_classifier\train_balanced_3000.jsonl"

output_dir = Path(r"C:\developer\LogDetAction\v2.0\qlora_classifier_balanced_model")
checkpoint_dir = Path(r"C:\developer\LogDetAction\v2.0\qlora_classifier_balanced_checkpoints")

output_dir.mkdir(parents=True, exist_ok=True)
checkpoint_dir.mkdir(parents=True, exist_ok=True)

MAX_LENGTH = 256

GRADIENT_ACCUMULATION_STEPS = 4
LEARNING_RATE = 2e-4

SAVE_EVERY_OPTIMIZER_STEP = 100


print("CUDA aktif mi?", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    torch.backends.cuda.matmul.allow_tf32 = True


print("\nBalanced classifier dataset yükleniyor...")

dataset = load_dataset(
    "json",
    data_files=train_path,
    split="train"
)

print("Dataset örnek sayısı:", len(dataset))

label_counter = Counter()

for item in dataset:
    output = item["output"].lower()

    if "benign" in output:
        label_counter["benign"] += 1
    elif "suspicious" in output:
        label_counter["suspicious"] += 1
    elif "malicious" in output:
        label_counter["malicious"] += 1

print("Label dağılımı:", dict(label_counter))


print("\nTokenizer yükleniyor...")

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"


def build_training_text(example):
    return f"""### Instruction:
{example["instruction"]}

### Input:
{example["input"]}

### Response:
{example["output"]}"""


def tokenize_example(example):
    text = build_training_text(example)

    tokens = tokenizer(
        text,
        max_length=MAX_LENGTH,
        truncation=True,
        padding="max_length"
    )

    tokens["labels"] = tokens["input_ids"].copy()

    return tokens


print("\nDataset tokenize ediliyor...")

dataset = dataset.map(
    tokenize_example,
    remove_columns=dataset.column_names
)

dataset.set_format(type="torch")


bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)


print("\nModel yükleniyor...")

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map={"": 0},
    dtype=torch.float16,
)

model.config.use_cache = False


print("\nModel balanced classifier QLoRA için hazırlanıyor...")

model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
    ],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)

print("\nEğitilebilir parametreler:")
model.print_trainable_parameters()


optimizer = PagedAdamW8bit(
    [p for p in model.parameters() if p.requires_grad],
    lr=LEARNING_RATE
)


print("\nBalanced classifier training başlıyor...\n")

model.train()
optimizer.zero_grad(set_to_none=True)

optimizer_step = 0
running_loss = 0.0

progress_bar = tqdm(range(len(dataset)), desc="Training")

for step, example in enumerate(dataset, start=1):

    batch = {
        "input_ids": example["input_ids"].unsqueeze(0).to(model.device),
        "attention_mask": example["attention_mask"].unsqueeze(0).to(model.device),
        "labels": example["labels"].unsqueeze(0).to(model.device),
    }

    outputs = model(**batch)

    loss = outputs.loss / GRADIENT_ACCUMULATION_STEPS
    loss.backward()

    running_loss += loss.item() * GRADIENT_ACCUMULATION_STEPS

    if step % GRADIENT_ACCUMULATION_STEPS == 0:
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)

        optimizer_step += 1

        if optimizer_step % 10 == 0:
            avg_loss = running_loss / (10 * GRADIENT_ACCUMULATION_STEPS)
            print(f"Optimizer Step: {optimizer_step} | Avg Loss: {avg_loss:.4f}")
            running_loss = 0.0

        if optimizer_step % SAVE_EVERY_OPTIMIZER_STEP == 0:
            ckpt_path = checkpoint_dir / f"checkpoint-{optimizer_step}"
            model.save_pretrained(ckpt_path)
            tokenizer.save_pretrained(ckpt_path)
            print(f"\nCheckpoint kaydedildi: {ckpt_path}\n")

    progress_bar.update(1)

progress_bar.close()


print("\nBalanced classifier training tamamlandı. Model kaydediliyor...")

model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)

print("\nBalanced classifier adapter kaydedildi:")
print(output_dir)