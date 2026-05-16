import os
os.environ["PYTHONUTF8"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import json
import re
import time
import random
from pathlib import Path
from collections import Counter, defaultdict

import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel


base_model_name = "mistralai/Mistral-7B-Instruct-v0.2"
adapter_path = r"C:\developer\LogDetAction\v2.0\qlora_classifier_test_model"

test_path = Path(r"C:\developer\LogDetAction\v2.0\split_classifier\test.jsonl")
results_path = Path(r"C:\developer\LogDetAction\v2.0\evaluation_qlora_classifier_100_results.csv")

TEST_LIMIT = 100
RANDOM_SEED = 42

LABELS = ["benign", "suspicious", "malicious"]


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


def safe_div(num, den):
    return num / den if den else 0.0


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


def build_prompt(log_entry):
    return f"""### Instruction:
Classify the following cybersecurity log entry using only one label: benign, suspicious, or malicious.
Return only the label in this format: Label: <label>.

### Input:
{log_entry}

### Response:
"""


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


print("\nTest dosyası okunuyor...")
with open(test_path, "r", encoding="utf-8") as f:
    all_items = [json.loads(line) for line in f]

random.seed(RANDOM_SEED)
sample_items = random.sample(all_items, TEST_LIMIT)

print(f"Toplam test havuzu: {len(all_items)}")
print(f"Seçilen örnek sayısı: {len(sample_items)}")

true_distribution = Counter(extract_label(item["output"]) for item in sample_items)
print("Seçilen 100 örneğin true label dağılımı:", dict(true_distribution))


three_class_correct = 0
attack_correct = 0
total = 0

confusion = {
    true_label: {pred_label: 0 for pred_label in LABELS + ["none"]}
    for true_label in LABELS
}

results = []

for i, item in enumerate(sample_items, start=1):
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

    results.append({
        "sample_id": i,
        "true_label": true_label,
        "predicted_label": pred_label,
        "three_class_correct": three_class_ok,
        "true_attack_label": true_attack_label,
        "pred_attack_label": pred_attack_label,
        "attack_detection_correct": attack_ok,
        "inference_time_sec": round(inference_time, 3),
        "log_preview": log_entry[:180],
        "model_answer": model_answer
    })

    print("=" * 80)
    print(f"Sample {i}/{TEST_LIMIT}")
    print("TRUE LABEL:", true_label)
    print("PRED LABEL:", pred_label)
    print("3-CLASS CORRECT:", three_class_ok)
    print("ATTACK DETECTION CORRECT:", attack_ok)
    print(f"Inference Time: {inference_time:.3f} sec")
    print("MODEL ANSWER:", model_answer)


three_class_accuracy = three_class_correct / total if total else 0
attack_accuracy = attack_correct / total if total else 0

df = pd.DataFrame(results)
df.to_csv(results_path, index=False, encoding="utf-8-sig")

print("=" * 80)
print(f"3-Class Accuracy: {three_class_correct}/{total} = {three_class_accuracy:.2f}")
print(f"Attack Detection Accuracy: {attack_correct}/{total} = {attack_accuracy:.2f}")
print("Average Inference Time:", round(df["inference_time_sec"].mean(), 3), "sec")
print("Median Inference Time:", round(df["inference_time_sec"].median(), 3), "sec")

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
        f"precision={precision:.2f} | "
        f"recall={recall:.2f} | "
        f"f1={f1:.2f}"
    )

print("\nSonuçlar kaydedildi:")
print(results_path)