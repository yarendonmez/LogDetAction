import os
os.environ["PYTHONUTF8"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import json
import re
import time
import random
from pathlib import Path
from collections import defaultdict, Counter

import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel


# =========================================================
# AYARLAR
# =========================================================

base_model_name = "mistralai/Mistral-7B-Instruct-v0.2"

adapter_path = r"C:\developer\LogDetAction\v2.0\qlora_classifier_balanced_model"

test_path = Path(r"C:\developer\LogDetAction\v2.0\split_classifier\test.jsonl")

results_path = Path(r"C:\developer\LogDetAction\v2.0\evaluation_qlora_classifier_balanced_model_results.csv")

RANDOM_SEED = 42

SAMPLES_PER_CLASS = 100

LABELS = ["benign", "suspicious", "malicious"]


# =========================================================
# LABEL FONKSİYONLARI
# =========================================================

def extract_label(text):
    """
    Metinden benign / suspicious / malicious label bilgisini çıkarır.
    """
    match = re.search(
        r"Label:\s*(benign|suspicious|malicious)|\b(benign|suspicious|malicious)\b",
        text,
        re.I
    )

    if not match:
        return None

    return (match.group(1) or match.group(2)).lower()


def to_attack_label(label):
    """
    3-class label değerini attack / non_attack formatına dönüştürür.
    """
    if label == "malicious":
        return "attack"

    if label in ["benign", "suspicious"]:
        return "non_attack"

    return None


def safe_div(num, den):
    return num / den if den else 0.0


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

print("\nClassifier-only QLoRA adapter yükleniyor...")
model = PeftModel.from_pretrained(base_model, adapter_path)
model.eval()


# =========================================================
# PROMPT
# =========================================================

def build_prompt(log_entry):
    """
    Classifier-only prompt.
    Modelden sadece Label üretmesi beklenir.
    """
    return f"""### Instruction:
Classify the following cybersecurity log entry using only one label: benign, suspicious, or malicious.
Return only the label in this format: Label: <label>.

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
        max_length=256
    ).to(model.device)

    start_time = time.time()

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=12,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    end_time = time.time()

    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    if "### Response:" in full_text:
        answer = full_text.split("### Response:")[-1].strip()
    else:
        answer = full_text.strip()

    return answer, end_time - start_time


# =========================================================
# BALANCED TEST SET OLUŞTURMA
# =========================================================

print("\nTest dosyası okunuyor...")

items_by_label = defaultdict(list)

with open(test_path, "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        label = extract_label(item["output"])

        if label in LABELS:
            items_by_label[label].append(item)

print("\nTest setindeki toplam label dağılımı:")
for label in LABELS:
    print(f"{label}: {len(items_by_label[label])}")

random.seed(RANDOM_SEED)

selected_items = []

for label in LABELS:
    available = len(items_by_label[label])
    sample_count = min(SAMPLES_PER_CLASS, available)

    selected = random.sample(items_by_label[label], sample_count)
    selected_items.extend(selected)

    print(f"\nSeçilen {label}: {sample_count}/{available}")

random.shuffle(selected_items)

print("\nToplam seçilen örnek:", len(selected_items))

selected_distribution = Counter(
    extract_label(item["output"]) for item in selected_items
)

print("Balanced test true label dağılımı:", dict(selected_distribution))


# =========================================================
# EVALUATION
# =========================================================

three_class_correct = 0
attack_correct = 0
total = 0

confusion = {
    true_label: {pred_label: 0 for pred_label in LABELS + ["none"]}
    for true_label in LABELS
}

results = []

wrong_cases = []

for i, item in enumerate(selected_items, start=1):
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

    pred_key = pred_label if pred_label in LABELS else "none"

    if true_label in LABELS:
        confusion[true_label][pred_key] += 1

    result = {
        "sample_id": i,
        "true_label": true_label,
        "predicted_label": pred_label,
        "three_class_correct": three_class_ok,
        "true_attack_label": true_attack_label,
        "pred_attack_label": pred_attack_label,
        "attack_detection_correct": attack_ok,
        "inference_time_sec": round(inference_time, 3),
        "log_preview": log_entry[:200],
        "model_answer": model_answer
    }

    results.append(result)

    if not three_class_ok:
        wrong_cases.append(result)

    if i % 25 == 0:
        print(f"{i}/{len(selected_items)} tamamlandı...")


# =========================================================
# SONUÇLAR
# =========================================================

three_class_accuracy = three_class_correct / total if total else 0
attack_accuracy = attack_correct / total if total else 0

df = pd.DataFrame(results)
df.to_csv(results_path, index=False, encoding="utf-8-sig")

print("=" * 80)
print(f"3-Class Accuracy: {three_class_correct}/{total} = {three_class_accuracy:.4f}")
print(f"Attack Detection Accuracy: {attack_correct}/{total} = {attack_accuracy:.4f}")

print("\nAverage Inference Time:", round(df["inference_time_sec"].mean(), 3), "sec")
print("Median Inference Time:", round(df["inference_time_sec"].median(), 3), "sec")
print("Min Inference Time:", round(df["inference_time_sec"].min(), 3), "sec")
print("Max Inference Time:", round(df["inference_time_sec"].max(), 3), "sec")

print("\nConfusion Matrix:")
confusion_df = pd.DataFrame(confusion).T
print(confusion_df)

print("\nPer-class metrics:")

for label in LABELS:
    tp = confusion[label][label]
    fp = sum(confusion[other][label] for other in LABELS if other != label)
    fn = sum(confusion[label][other] for other in LABELS + ["none"] if other != label)

    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = safe_div(2 * precision * recall, precision + recall)

    print(
        f"{label:10s} | "
        f"precision={precision:.4f} | "
        f"recall={recall:.4f} | "
        f"f1={f1:.4f}"
    )

print("\nYanlış sınıflandırılan örnek sayısı:", len(wrong_cases))

if wrong_cases:
    print("\nİlk 10 yanlış örnek:")
    for case in wrong_cases[:10]:
        print("-" * 80)
        print("sample_id:", case["sample_id"])
        print("true_label:", case["true_label"])
        print("predicted_label:", case["predicted_label"])
        print("log_preview:", case["log_preview"])
        print("model_answer:", case["model_answer"])

print("\nSonuçlar kaydedildi:")
print(results_path)