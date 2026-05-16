import json
import re
import time
import requests
import pandas as pd
from pathlib import Path

# Test veri seti yolu
test_path = Path(r"C:\developer\LogDetAction\v2.0\split\test.jsonl")

# Sonuçların kaydedileceği CSV dosyası
results_path = Path(r"C:\developer\LogDetAction\v2.0\evaluation_results.csv")

# LM Studio local server endpoint
url = "http://localhost:1234/v1/chat/completions"


def extract_true_label(output_text):
    """
    Test veri setindeki gerçek etiketi çıkarır.
    Örnek:
    Label: malicious
    """
    match = re.search(
        r"Label:\s*(benign|suspicious|malicious)",
        output_text,
        re.I
    )
    return match.group(1).lower() if match else None


def extract_pred_label(response_text):
    """
    Model cevabındaki tahmin edilen etiketi çıkarır.
    """
    match = re.search(
        r"Label:\s*(benign|suspicious|malicious)",
        response_text,
        re.I
    )
    return match.group(1).lower() if match else None


def ask_model(log_entry):
    """
    LM Studio üzerinden local LLM modeline tek bir log gönderir.
    Modelden istenen davranış:
    - Eğer log benign ise sadece Label ve Recommendation döndürür.
    - Eğer log suspicious veya malicious ise Label, Explanation ve Recommendation döndürür.
    """

    prompt = f"""
You are a cybersecurity SOC analyst.

Analyze the following log entry and classify it using only one of these labels:
- benign
- suspicious
- malicious

Label definitions:
- benign: normal system activity with no security concern.
- suspicious: abnormal system behavior or anomaly, but without clear attacker action.
- malicious: clear attacker behavior, unauthorized access, credential abuse, command execution, malware download, persistence, or privilege abuse.

Important rules:
- Password modification attempts must be classified as malicious.
- authorized_keys modification must be classified as malicious.
- Shell command execution by an unknown actor must be classified as malicious.
- Malware download activity must be classified as malicious.
- Unauthorized SSH or honeypot attacker activity must be classified as malicious.
- Normal HDFS block operations should usually be classified as benign.
- HDFS anomaly-like behavior without clear attacker action should be classified as suspicious.

Output rules:
- If the label is benign, DO NOT generate an explanation.
- If the label is benign, answer only with:
Label: benign
Recommendation: No action required.

- If the label is suspicious or malicious, answer exactly with:
Label: suspicious / malicious
Explanation: one short technical explanation
Recommendation: one concrete security action

Log:
{log_entry}
"""

    payload = {
        "model": "mistral-7b-instruct-v0.2",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "max_tokens": 220
    }

    start_time = time.time()

    response = requests.post(
        url,
        json=payload,
        timeout=120
    )

    end_time = time.time()

    response.raise_for_status()

    response_text = response.json()["choices"][0]["message"]["content"]

    inference_time = end_time - start_time

    return response_text, inference_time


correct = 0
total = 0
results = []

with open(test_path, "r", encoding="utf-8") as f:

    # İlk 10 örnek test edilir.
    for i in range(10):

        item = json.loads(next(f))

        log_entry = item["input"]
        true_label = extract_true_label(item["output"])

        model_answer, inference_time = ask_model(log_entry)
        pred_label = extract_pred_label(model_answer)

        total += 1
        is_correct = pred_label == true_label

        if is_correct:
            correct += 1

        results.append({
            "sample_id": i + 1,
            "true_label": true_label,
            "predicted_label": pred_label,
            "correct": is_correct,
            "inference_time_sec": round(inference_time, 3),
            "log_length": len(log_entry),
            "log_preview": log_entry[:120],
            "model_answer": model_answer
        })

        print("=" * 80)
        print(f"Sample {i + 1}")
        print(f"TRUE LABEL: {true_label}")
        print(f"PRED LABEL: {pred_label}")
        print(f"Inference Time: {inference_time:.3f} sec")

        print("\nLOG:")
        print(log_entry[:300])

        print("\nMODEL ANSWER:")
        print(model_answer)

accuracy = correct / total if total > 0 else 0

print("=" * 80)
print(f"Accuracy: {correct}/{total} = {accuracy:.2f}")

df = pd.DataFrame(results)

df.to_csv(
    results_path,
    index=False,
    encoding="utf-8-sig"
)

print("\nEvaluation sonuçları kaydedildi:")
print(results_path)