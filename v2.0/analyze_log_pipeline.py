import os
os.environ["PYTHONUTF8"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import re
import sys
import time
from pathlib import Path

import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel


# =========================================================
# PATH AYARLARI
# =========================================================

BASE_MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"

# LLM-A: sadece sınıflandırma yapan adapter
CLASSIFIER_ADAPTER_PATH = r"C:\developer\LogDetAction\v2.0\qlora_classifier_test_model"

# LLM-B / LLM-C: açıklama ve öneri için kullanılacak full-output adapter
ANALYSIS_ADAPTER_PATH = r"C:\developer\LogDetAction\v2.0\qlora_test_model"

RESULTS_DIR = Path(r"C:\developer\LogDetAction\v2.0\results\pipeline")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# ANALYSIS MODE
# =========================================================
# combined: Explanation + Recommendation tek çağrıda üretilir.
# separate: Explanation ve Recommendation ayrı çağrılarla üretilir.
DEFAULT_ANALYSIS_MODE = "combined"


# =========================================================
# TEST LOGLARI
# Eğer komut satırından dosya verilmezse bu örnekler analiz edilir.
# =========================================================

DEFAULT_LOGS = [
    "CMD: cat /proc/cpuinfo | grep name | wc -l",
    "Remote SSH version: SSH-2.0-libssh-0.6.3",
    "081109 204512 26 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.203.166:50010 is added to blk_-2299586501391716260 size 67108864",
    "login attempt [ubuntu/ubuntu1234] succeeded",
]


# =========================================================
# YARDIMCI FONKSİYONLAR
# =========================================================

def extract_label(text):
    """
    Model cevabından benign / suspicious / malicious label bilgisini çıkarır.
    """
    match = re.search(
        r"Label:\s*(benign|suspicious|malicious)|\b(benign|suspicious|malicious)\b",
        text,
        re.I
    )

    if not match:
        return None

    return (match.group(1) or match.group(2)).lower()


def clean_after_response(full_text):
    """
    Üretilen cevaptan prompt kısmını temizler.
    """
    if "### Response:" in full_text:
        return full_text.split("### Response:")[-1].strip()

    return full_text.strip()


def normalize_explanation(text):
    """
    Explanation çıktısını formatlar.
    """
    text = text.strip()

    if "Recommendation:" in text:
        text = text.split("Recommendation:")[0].strip()

    if "Explanation:" in text:
        text = text.split("Explanation:", 1)[-1].strip()

    return "Explanation: " + text.strip()


def normalize_recommendation(text):
    """
    Recommendation çıktısını formatlar.
    """
    text = text.strip()

    if "Recommendation:" in text:
        text = text.split("Recommendation:", 1)[-1].strip()

    if "Explanation:" in text:
        text = text.split("Explanation:")[0].strip()

    return "Recommendation: " + text.strip()

def detect_log_context(log_entry):
    """
    Log satırının hangi genel log ailesine benzediğini kabaca belirler.
    Bu fonksiyon sınıflandırma yapmaz; sadece explanation/recommendation
    promptlarına yardımcı bağlam verir.
    """

    log_lower = log_entry.lower()

    ssh_shell_indicators = [
        "cmd:",
        "command",
        "login attempt",
        "failed password",
        "accepted password",
        "successful login",
        "remote ssh version",
        "ssh-",
        "authorized_keys",
        "chpasswd",
        "wget",
        "curl",
        "busybox",
        "shell",
        "session",
        "tty",
    ]

    distributed_fs_indicators = [
        "dfs.",
        "datanode",
        "namenode",
        "fsnamesystem",
        "packetresponder",
        "dataxceiver",
        "block",
        "blk_",
        "replicate",
        "addstoredblock",
        "allocateblock",
    ]

    web_server_indicators = [
        "http",
        "get ",
        "post ",
        "put ",
        "delete ",
        "status",
        "user-agent",
        "nginx",
        "apache",
        "404",
        "500",
        "403",
    ]

    auth_indicators = [
        "login",
        "logout",
        "authentication",
        "auth failed",
        "invalid user",
        "permission denied",
        "mfa",
        "token",
    ]

    firewall_network_indicators = [
        "firewall",
        "blocked",
        "denied",
        "allowed",
        "src=",
        "dst=",
        "source ip",
        "destination ip",
        "port",
        "tcp",
        "udp",
        "icmp",
    ]

    if any(indicator in log_lower for indicator in ssh_shell_indicators):
        return "ssh_shell_activity"

    if any(indicator in log_lower for indicator in distributed_fs_indicators):
        return "distributed_file_system"

    if any(indicator in log_lower for indicator in web_server_indicators):
        return "web_server"

    if any(indicator in log_lower for indicator in auth_indicators):
        return "authentication"

    if any(indicator in log_lower for indicator in firewall_network_indicators):
        return "network_security"

    return "generic"

def get_context_note(context):
    """
    Bulunan genel log tipine göre modele verilecek yardımcı context bilgisini döndürür.
    Bu bilgi hard-coded karar değildir; sadece açıklama/öneri üretimini yönlendirir.
    """

    if context == "ssh_shell_activity":
        return (
            "Possible context: The log resembles SSH, shell, or interactive session activity. "
            "If the event is classified as malicious, interpret commands, login attempts, "
            "client fingerprints, TTY events, and credential changes as potentially attacker-driven behavior. "
            "Base the analysis on observable indicators rather than assuming a specific dataset."
        )

    elif context == "distributed_file_system":
        return (
            "Possible context: The log resembles distributed file system activity. "
            "Block transfers, replication, node communication, and metadata updates may be normal operational events "
            "unless anomaly context or unusual correlation is present."
        )

    elif context == "web_server":
        return (
            "Possible context: The log resembles web server activity. "
            "Analyze HTTP method, status code, endpoint, user-agent, source information, and error pattern."
        )

    elif context == "authentication":
        return (
            "Possible context: The log resembles authentication activity. "
            "Analyze login result, user identity, source information, failed attempts, and privilege-related indicators."
        )

    elif context == "network_security":
        return (
            "Possible context: The log resembles firewall or network security activity. "
            "Analyze source, destination, port, protocol, action, and whether the event indicates scanning or blocking."
        )

    else:
        return (
            "Possible context: The log source is unknown. "
            "Analyze the observable behavior in a general SOC context without assuming a specific platform."
        )

def load_logs_from_file(file_path):
    """
    TXT/log dosyasından boş olmayan satırları okur.
    Her satır ayrı log kabul edilir.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Log dosyası bulunamadı: {path}")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        logs = [line.strip() for line in f if line.strip()]

    return logs

def sanitize_filename(name):
    """
    Dosya adını sonuç dosyası için güvenli hale getirir.
    Boşlukları ve özel karakterleri '_' yapar.
    """
    name = Path(name).stem
    name = re.sub(r"[^\w\-]+", "_", name, flags=re.UNICODE)
    name = name.strip("_")

    if not name:
        name = "logs"

    return name


def get_unique_output_path(input_file, analysis_mode):
    """
    Analiz edilen dosyaya ve analysis mode'a göre benzersiz sonuç dosyası üretir.

    Örnek:
    sample_logs_combined_results.csv
    sample_logs_combined_results_1.csv
    sample_logs_combined_results_2.csv
    """

    if input_file:
        base_name = sanitize_filename(input_file)
    else:
        base_name = "default_logs"

    file_name = f"{base_name}_{analysis_mode}_results.csv"
    output_path = RESULTS_DIR / file_name

    counter = 1

    while output_path.exists():
        file_name = f"{base_name}_{analysis_mode}_results_{counter}.csv"
        output_path = RESULTS_DIR / file_name
        counter += 1

    return output_path

# =========================================================
# MODEL YÜKLEME
# =========================================================

print("CUDA aktif mi?", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))

print("\nTokenizer yükleniyor...")

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

print("\nBase model yükleniyor...")

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_NAME,
    quantization_config=bnb_config,
    device_map={"": 0},
    dtype=torch.float16,
)

print("\nLLM-A classifier adapter yükleniyor...")

model = PeftModel.from_pretrained(
    base_model,
    CLASSIFIER_ADAPTER_PATH,
    adapter_name="classifier"
)

print("\nLLM-B / LLM-C analysis adapter yükleniyor...")

model.load_adapter(
    ANALYSIS_ADAPTER_PATH,
    adapter_name="analysis"
)

model.eval()


# =========================================================
# GENERATION
# =========================================================

def generate_with_adapter(prompt, adapter_name, max_new_tokens, max_length=512):
    """
    Aynı base model üzerinde farklı LoRA adapter seçerek cevap üretir.
    """
    model.set_adapter(adapter_name)

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_length
    ).to(model.device)

    start_time = time.time()

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    elapsed = time.time() - start_time

    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    answer = clean_after_response(full_text)

    return answer, elapsed


# =========================================================
# LLM-A: CLASSIFICATION
# =========================================================

def classify_log(log_entry):
    """
    LLM-A sınıflandırma modülü.
    Sadece label üretir.
    """
    prompt = f"""### Instruction:
Classify the following cybersecurity log entry using only one label: benign, suspicious, or malicious.
Return only the label in this format: Label: <label>.

### Input:
{log_entry}

### Response:
"""

    answer, elapsed = generate_with_adapter(
        prompt=prompt,
        adapter_name="classifier",
        max_new_tokens=12,
        max_length=256
    )

    label = extract_label(answer)

    return label, answer, elapsed



# =========================================================
# LLM-B: EXPLANATION
# =========================================================

def generate_explanation(log_entry, label):
    """
    LLM-B açıklama modülü.
    Genel log analizi yapar; bilinen log aileleri için yalnızca yardımcı context verir.
    """

    context = detect_log_context(log_entry)
    context_note = get_context_note(context)

    prompt = f"""### Instruction:
You are a cybersecurity SOC analyst.

The following log was classified as {label}.

{context_note}

Write one short technical explanation.

Rules:
- Return only one Explanation line.
- Do not rely only on dataset-specific assumptions.
- If the log source is unclear, base the explanation only on observable indicators.
- Explain the security meaning of the observed behavior.
- Do not write a recommendation.
- Do not recommend destructive or automatic actions.
- Keep the answer concise.

### Input:
{log_entry}

### Response:
Explanation:"""

    answer, elapsed = generate_with_adapter(
        prompt=prompt,
        adapter_name="analysis",
        max_new_tokens=80,
        max_length=512
    )

    explanation = normalize_explanation(answer)

    return explanation, elapsed

# =========================================================
# LLM-C: RECOMMENDATION
# =========================================================

def generate_recommendation(log_entry, label, explanation):
    """
    LLM-C öneri modülü.
    Genel, güvenli ve uygulanabilir SOC aksiyonu üretir.
    """

    context = detect_log_context(log_entry)
    context_note = get_context_note(context)

    prompt = f"""### Instruction:
You are a cybersecurity SOC analyst.

The following log was classified as {label}.

{context_note}

Based on the explanation, write one concrete security recommendation.

Rules:
- Return only one Recommendation line.
- Make the action specific and operational.
- Do not rely only on dataset-specific assumptions.
- Do not use vague advice such as only "monitor activity".
- Do not recommend destructive or automatic actions.
- Do not recommend password resets unless the log clearly shows credential compromise.
- Prefer investigation, correlation, IOC extraction, session reconstruction, source analysis, or analyst review.
- Keep the answer concise.

### Input:
Log:
{log_entry}

{explanation}

### Response:
Recommendation:"""

    answer, elapsed = generate_with_adapter(
        prompt=prompt,
        adapter_name="analysis",
        max_new_tokens=80,
        max_length=512
    )

    recommendation = normalize_recommendation(answer)

    return recommendation, elapsed

# =========================================================
# LLM-B + LLM-C: COMBINED ANALYSIS
# =========================================================

def generate_combined_analysis(log_entry, label):
    """
    LLM-B + LLM-C combined mode.
    Explanation ve Recommendation çıktısını tek model çağrısında üretir.
    Bu mod, sınırlı GPU ortamında latency azaltmak için kullanılır.
    """

    context = detect_log_context(log_entry)
    context_note = get_context_note(context)

    prompt = f"""### Instruction:
You are a cybersecurity SOC analyst.

The following log was classified as {label}.

{context_note}

Generate exactly two fields:
Explanation:
Recommendation:

Rules:
- Explanation must be one short technical sentence.
- Recommendation must be one concrete SOC action.
- Do not rely only on dataset-specific assumptions.
- Do not use vague advice such as "monitor activity" alone.
- If the log source is unclear, base the answer only on observable indicators.
- Do not recommend destructive or automatic actions.
- Do not recommend password resets unless the log clearly shows credential compromise.
- Prefer investigation, correlation, IOC extraction, session reconstruction, source analysis, or analyst review.
- Keep the answer concise.
- Return only these two lines.

### Input:
{log_entry}

### Response:
Explanation:"""

    answer, elapsed = generate_with_adapter(
        prompt=prompt,
        adapter_name="analysis",
        max_new_tokens=110,
        max_length=512
    )

    answer = answer.strip()

    # Model bazen doğrudan cümleyle başlarsa Explanation formatına sokuyoruz.
    if not answer.lower().startswith("explanation:"):
        answer = "Explanation: " + answer

    if "Recommendation:" in answer:
        explanation_part = answer.split("Recommendation:", 1)[0].strip()
        recommendation_part = answer.split("Recommendation:", 1)[1].strip()

        explanation = normalize_explanation(explanation_part)
        recommendation = "Recommendation: " + recommendation_part.strip()

    else:
        # Recommendation üretilemezse güvenli fallback öneri veriyoruz.
        explanation = normalize_explanation(answer)
        recommendation = (
            "Recommendation: Correlate this event with related logs, source indicators, "
            "session context, and neighboring events before escalation."
        )

    return explanation, recommendation, elapsed


# =========================================================
# PIPELINE
# =========================================================

def analyze_log(log_entry, analysis_mode=DEFAULT_ANALYSIS_MODE):
    """
    Ana pipeline:
    1. LLM-A ile sınıflandır.
    2. Benign ise dur.
    3. Malicious ise açıklama + öneri üret.
    4. Suspicious ise context-aware kontrol gerektiğini belirt.
    """

    label, raw_classification, classification_time = classify_log(log_entry)

    explanation = ""
    recommendation = ""
    explanation_time = 0.0
    recommendation_time = 0.0
    status = ""

    if label == "benign":
        status = "no_action"
        recommendation = "Recommendation: No action required."

    elif label == "malicious":
        status = f"analysis_generated_{analysis_mode}"

        if analysis_mode == "combined":
            explanation, recommendation, combined_time = generate_combined_analysis(
                log_entry=log_entry,
                label=label
            )

            explanation_time = combined_time
            recommendation_time = 0.0

        elif analysis_mode == "separate":
            explanation, explanation_time = generate_explanation(
                log_entry=log_entry,
                label=label
            )

            recommendation, recommendation_time = generate_recommendation(
                log_entry=log_entry,
                label=label,
                explanation=explanation
            )

        else:
            status = "invalid_analysis_mode"
            explanation = "Explanation: Invalid analysis mode selected."
            recommendation = "Recommendation: Use either combined or separate mode."

    elif label == "suspicious":
        status = "context_required"
        explanation = (
            "Explanation: The log was classified as suspicious, but this category "
            "may require block-level or session-level correlation before escalation."
        )
        recommendation = (
            "Recommendation: Correlate this event with related block IDs, session IDs, "
            "neighboring events, and anomaly history before taking action."
        )

    else:
        status = "label_not_extracted"
        explanation = "Explanation: The model output could not be parsed into a valid label."
        recommendation = "Recommendation: Review the log manually."

    total_time = classification_time + explanation_time + recommendation_time

    return {
        "log": log_entry,
        "label": label,
        "status": status,
        "analysis_mode": analysis_mode,
        "classification_time_sec": round(classification_time, 3),
        "explanation_time_sec": round(explanation_time, 3),
        "recommendation_time_sec": round(recommendation_time, 3),
        "total_time_sec": round(total_time, 3),
        "raw_classification": raw_classification,
        "explanation": explanation,
        "recommendation": recommendation,
    }


# =========================================================
# MAIN
# =========================================================

analysis_mode = DEFAULT_ANALYSIS_MODE
input_file = None

args = sys.argv[1:]

if "--mode" in args:
    mode_index = args.index("--mode")

    if mode_index + 1 < len(args):
        analysis_mode = args[mode_index + 1].lower().strip()

        if analysis_mode not in ["combined", "separate"]:
            print("Geçersiz analysis mode. combined veya separate kullanılmalı.")
            sys.exit(1)

        # --mode ve değerini argüman listesinden çıkar
        args.pop(mode_index + 1)
        args.pop(mode_index)

if len(args) > 0:
    input_file = args[0]

if input_file:
    print(f"\nLog dosyası okunuyor: {input_file}")
    logs = load_logs_from_file(input_file)
else:
    print("\nKomut satırından dosya verilmedi. DEFAULT_LOGS analiz edilecek.")
    logs = DEFAULT_LOGS

print(f"\nAnalysis Mode: {analysis_mode}")
print(f"\nAnaliz edilecek log sayısı: {len(logs)}\n")

output_path = get_unique_output_path(input_file, analysis_mode)

print("Sonuç dosyası oluşturulacak:")
print(output_path)

results = []

for i, log_entry in enumerate(logs, start=1):
    print("=" * 80)
    print(f"Log {i}/{len(logs)}")
    print("LOG:", log_entry[:250])

    result = analyze_log(log_entry, analysis_mode=analysis_mode)
    results.append(result)

    print("LABEL:", result["label"])
    print("STATUS:", result["status"])
    print("ANALYSIS MODE:", result["analysis_mode"])
    print("Classification Time:", result["classification_time_sec"], "sec")
    print("Explanation Time:", result["explanation_time_sec"], "sec")
    print("Recommendation Time:", result["recommendation_time_sec"], "sec")
    print("Total Time:", result["total_time_sec"], "sec")
    print(result["explanation"])
    print(result["recommendation"])

df = pd.DataFrame(results)
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print("\nPipeline analizi tamamlandı.")
print("Sonuç dosyası:")
print(output_path)

print("\nÖzet:")
print(df["label"].value_counts(dropna=False))

print("\nOrtalama süreler:")
print("Classification:", round(df["classification_time_sec"].mean(), 3), "sec")
print("Explanation:", round(df["explanation_time_sec"].mean(), 3), "sec")
print("Recommendation:", round(df["recommendation_time_sec"].mean(), 3), "sec")
print("Total:", round(df["total_time_sec"].mean(), 3), "sec")