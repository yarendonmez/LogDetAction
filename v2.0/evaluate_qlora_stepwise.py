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

results_path = Path(r"C:\developer\LogDetAction\v2.0\evaluation_qlora_stepwise_results.csv")


# Kaç örnek test edilecek?
TEST_LIMIT = 10


# =========================================================
# LABEL ÇIKARMA FONKSİYONLARI
# =========================================================

def extract_label(text):
    """
    Model cevabından benign / suspicious / malicious etiketini çıkarır.
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
    3 sınıfı attack / non_attack formatına dönüştürür.
    malicious = attack
    benign + suspicious = non_attack
    """
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
# GENEL GENERATION FONKSİYONU
# =========================================================

def generate_answer(prompt, max_new_tokens):
    """
    Modele prompt gönderir ve cevabı döndürür.
    Süreyi de ölçer.
    """

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
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    end_time = time.time()

    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Prompt kısmını cevaptan ayırmaya çalışıyoruz.
    if "### Response:" in full_text:
        answer = full_text.split("### Response:")[-1].strip()
    else:
        answer = full_text.strip()

    return answer, end_time - start_time


# =========================================================
# 1. ADIM: SADECE SINIFLANDIRMA
# =========================================================

def classify_log(log_entry):
    """
    İlk aşama sadece sınıflandırma yapar.
    Burada açıklama ve öneri istemiyoruz.
    """

    prompt = f"""### Instruction:
Analyze the following cybersecurity log entry.
Classify it using only one of these labels:
benign, suspicious, malicious.

Return only the label in this exact format:
Label: benign
or
Label: suspicious
or
Label: malicious

### Input:
{log_entry}

### Response:
"""

    answer, elapsed = generate_answer(prompt, max_new_tokens=12)

    pred_label = extract_label(answer)

    return pred_label, answer, elapsed


# =========================================================
# 2. ADIM: AÇIKLAMA ÜRETME
# =========================================================

def explain_log(log_entry, label):
    """
    Sadece suspicious veya malicious loglar için açıklama üretir.
    Benign loglar için çağrılmaz.
    """

    prompt = f"""### Instruction:
You are a cybersecurity SOC analyst.
The following log was classified as {label}.
Write one short technical explanation.
Do not include a recommendation.

### Input:
{log_entry}

### Response:
Explanation:"""

    answer, elapsed = generate_answer(prompt, max_new_tokens=90)

    # Cevap "Explanation:" ile başlamazsa normalize edelim.
    if not answer.lower().startswith("explanation:"):
        answer = "Explanation: " + answer.strip()

    return answer, elapsed


# =========================================================
# 3. ADIM: ÖNERİ ÜRETME
# =========================================================

def recommend_action(log_entry, label, explanation):
    """
    Sadece suspicious veya malicious loglar için öneri üretir.
    """

    prompt = f"""### Instruction:
You are a cybersecurity SOC analyst.
The following log was classified as {label}.
Based on the explanation, write one concrete security recommendation.
Return only the recommendation.

### Input:
Log:
{log_entry}

{explanation}

### Response:
Recommendation:"""

    answer, elapsed = generate_answer(prompt, max_new_tokens=70)

    if not answer.lower().startswith("recommendation:"):
        answer = "Recommendation: " + answer.strip()

    return answer, elapsed


# =========================================================
# EVALUATION
# =========================================================

three_class_correct = 0
attack_correct = 0
total = 0

results = []

with open(test_path, "r", encoding="utf-8") as f:

    for i in range(TEST_LIMIT):

        item = json.loads(next(f))

        log_entry = item["input"]
        true_label = extract_label(item["output"])

        # ------------------------------
        # 1. Classification
        # ------------------------------
        pred_label, raw_classification_answer, classification_time = classify_log(log_entry)

        explanation = ""
        recommendation = ""
        explanation_time = 0.0
        recommendation_time = 0.0

        # ------------------------------
        # 2-3. Eğer benign değilse detay üret
        # ------------------------------
        if pred_label in ["suspicious", "malicious"]:
            explanation, explanation_time = explain_log(log_entry, pred_label)
            recommendation, recommendation_time = recommend_action(
                log_entry,
                pred_label,
                explanation
            )

        elif pred_label == "benign":
            recommendation = "Recommendation: No action required."

        else:
            recommendation = "Recommendation: Label could not be extracted."

        total_time = classification_time + explanation_time + recommendation_time

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
            "classification_time_sec": round(classification_time, 3),
            "explanation_time_sec": round(explanation_time, 3),
            "recommendation_time_sec": round(recommendation_time, 3),
            "total_time_sec": round(total_time, 3),
            "log_preview": log_entry[:160],
            "raw_classification_answer": raw_classification_answer,
            "explanation": explanation,
            "recommendation": recommendation
        })

        print("=" * 80)
        print(f"Sample {i + 1}")
        print("TRUE LABEL:", true_label)
        print("PRED LABEL:", pred_label)
        print("TRUE ATTACK LABEL:", true_attack_label)
        print("PRED ATTACK LABEL:", pred_attack_label)
        print("3-CLASS CORRECT:", three_class_ok)
        print("ATTACK DETECTION CORRECT:", attack_ok)

        print(f"Classification Time: {classification_time:.3f} sec")
        print(f"Explanation Time: {explanation_time:.3f} sec")
        print(f"Recommendation Time: {recommendation_time:.3f} sec")
        print(f"Total Time: {total_time:.3f} sec")

        print("\nLOG:")
        print(log_entry[:300])

        print("\nCLASSIFICATION ANSWER:")
        print(raw_classification_answer)

        if explanation:
            print("\nEXPLANATION:")
            print(explanation)

        print("\nRECOMMENDATION:")
        print(recommendation)


three_class_accuracy = three_class_correct / total if total > 0 else 0
attack_accuracy = attack_correct / total if total > 0 else 0

print("=" * 80)
print(f"3-Class Accuracy: {three_class_correct}/{total} = {three_class_accuracy:.2f}")
print(f"Attack Detection Accuracy: {attack_correct}/{total} = {attack_accuracy:.2f}")

df = pd.DataFrame(results)
df.to_csv(results_path, index=False, encoding="utf-8-sig")

print("\nQLoRA stepwise evaluation sonuçları kaydedildi:")
print(results_path)

print("\nOrtalama süreler:")
print("Classification:", round(df["classification_time_sec"].mean(), 3), "sec")
print("Explanation:", round(df["explanation_time_sec"].mean(), 3), "sec")
print("Recommendation:", round(df["recommendation_time_sec"].mean(), 3), "sec")
print("Total:", round(df["total_time_sec"].mean(), 3), "sec")