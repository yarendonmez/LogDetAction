import json
import re
import time
import requests
import pandas as pd
from pathlib import Path

test_path = Path(r"C:\developer\LogDetAction\v2.0\split\test.jsonl")
results_path = Path(r"C:\developer\LogDetAction\v2.0\evaluation_stepwise_results.csv")

url = "http://localhost:1234/v1/chat/completions"


def extract_label(text):
    match = re.search(r"\b(benign|suspicious|malicious)\b", text, re.I)
    return match.group(1).lower() if match else None


def to_attack_label(label):
    if label == "malicious":
        return "attack"
    if label in ["benign", "suspicious"]:
        return "non_attack"
    return None


def call_model(prompt, max_tokens=120):
    payload = {
        "model": "mistral-7b-instruct-v0.2",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": max_tokens
    }

    start = time.time()
    response = requests.post(url, json=payload, timeout=120)
    end = time.time()

    response.raise_for_status()
    answer = response.json()["choices"][0]["message"]["content"].strip()

    return answer, end - start


def classify_log(log_entry):
    prompt = f"""
You are a cybersecurity SOC analyst.

Classify the following log entry using only one label:
benign, suspicious, or malicious.

Definitions:
- benign: normal system activity with no security concern.
- suspicious: abnormal system behavior without clear attacker action.
- malicious: clear attacker behavior, unauthorized access, credential abuse, command execution, malware download, persistence, or privilege abuse.

Important rules:
- Password modification commands are malicious.
- authorized_keys modification is malicious.
- Unknown shell command execution is malicious.
- Malware download activity is malicious.
- Honeypot attacker activity is malicious.
- Normal HDFS block operations are benign.
- HDFS anomaly-like behavior without attacker action is suspicious.

Return only the label word. Do not explain.

Log:
{log_entry}
"""
    answer, elapsed = call_model(prompt, max_tokens=20)
    label = extract_label(answer)
    return label, answer, elapsed


def explain_log(log_entry, label):
    prompt = f"""
You are a cybersecurity SOC analyst.

The following log was classified as {label}.

Write one short technical explanation for why this log is {label}.
Do not include a recommendation.

Log:
{log_entry}
"""
    answer, elapsed = call_model(prompt, max_tokens=120)
    return answer, elapsed


def recommend_action(log_entry, label, explanation):
    prompt = f"""
You are a cybersecurity SOC analyst.

The following log was classified as {label}.

Log:
{log_entry}

Explanation:
{explanation}

Write one concrete security recommendation.
Return only the recommendation sentence.
"""
    answer, elapsed = call_model(prompt, max_tokens=100)
    return answer, elapsed


three_class_correct = 0
attack_correct = 0
total = 0
results = []

with open(test_path, "r", encoding="utf-8") as f:
    for i in range(10):
        item = json.loads(next(f))

        log_entry = item["input"]
        true_label = extract_label(item["output"])

        pred_label, raw_classification_answer, classification_time = classify_log(log_entry)

        explanation = ""
        recommendation = ""
        explanation_time = 0.0
        recommendation_time = 0.0

        if pred_label in ["suspicious", "malicious"]:
            explanation, explanation_time = explain_log(log_entry, pred_label)
            recommendation, recommendation_time = recommend_action(log_entry, pred_label, explanation)
        elif pred_label == "benign":
            recommendation = "No action required."

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

three_class_accuracy = three_class_correct / total
attack_accuracy = attack_correct / total

print("=" * 80)
print(f"3-Class Accuracy: {three_class_correct}/{total} = {three_class_accuracy:.2f}")
print(f"Attack Detection Accuracy: {attack_correct}/{total} = {attack_accuracy:.2f}")

df = pd.DataFrame(results)
df.to_csv(results_path, index=False, encoding="utf-8-sig")

print("\nStepwise evaluation sonuçları kaydedildi:")
print(results_path)

print("\nOrtalama süreler:")
print("Classification:", round(df["classification_time_sec"].mean(), 3), "sec")
print("Explanation:", round(df["explanation_time_sec"].mean(), 3), "sec")
print("Recommendation:", round(df["recommendation_time_sec"].mean(), 3), "sec")
print("Total:", round(df["total_time_sec"].mean(), 3), "sec")