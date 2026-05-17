# LogDetAction v2.0

**LLM-Based Cybersecurity Log Analysis System**  
Local full-stack web application — university graduation project prototype.

---

## System Architecture

```
Browser (React + Vite) → FastAPI Backend → QLoRA GPU Pipeline → SQLite + CSV
       localhost:5173         localhost:8000       RTX 4060 Laptop GPU
```

### Model Pipeline

| Module | Role | Adapter |
|--------|------|---------|
| LLM-A  | Classification (benign / suspicious / malicious) | `qlora_classifier_test_model` |
| LLM-B  | Explanation generation | `qlora_test_model` |
| LLM-C  | Recommendation generation | `qlora_test_model` (shared with LLM-B in prototype) |

Base model: `mistralai/Mistral-7B-Instruct-v0.2` (4-bit QLoRA)

### Analysis Modes

| Mode | CLI / API | Behaviour |
|------|-----------|-----------|
| **Fast Mode** | `combined` (default) | Explanation + Recommendation in one model call. Lower latency. |
| **Detailed Mode** | `separate` | Separate calls for LLM-B and LLM-C. Demonstrates modular architecture. |

---

## Quick Start

### 1. Backend

```powershell
# From project root, activate the existing venv
.\.venv\Scripts\Activate.ps1

# Install backend dependencies (first time)
pip install fastapi uvicorn[standard] python-multipart sqlalchemy aiosqlite pydantic-settings python-dotenv pandas

# Copy environment config
Copy-Item .env.example .env   # edit paths if needed

# Start backend
$env:PYTHONUTF8=1
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Model loading takes ~30–60 seconds on first start. Watch the terminal for:
```
INFO: All models ready in X.XXs
```

### 2. Frontend

Open a second terminal:

```powershell
cd frontend
npm install   # first time only
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Environment Configuration

All config is in `.env`. Key variables:

```env
CLASSIFIER_ADAPTER_PATH=C:\developer\LogDetAction\v2.0\qlora_classifier_test_model
ANALYSIS_ADAPTER_PATH=C:\developer\LogDetAction\v2.0\qlora_test_model
BASE_MODEL_ID=mistralai/Mistral-7B-Instruct-v0.2
DEVICE=cuda
DEFAULT_ANALYSIS_MODE=combined
RESULTS_DIR=backend/results/pipeline
DB_PATH=backend/logdetaction.db
```

See `.env.example` for all options.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | System and model status |
| POST | `/api/analyze/file` | Upload `.txt`, `.log`, or `.csv` |
| POST | `/api/analyze/text` | Submit pasted multiline logs |
| GET | `/api/results` | Analysis history |
| GET | `/api/results/{id}` | Full result with per-log rows |
| GET | `/api/results/{id}/download` | Download CSV |

### Analysis Mode

Pass `analysis_mode` as `combined` (default) or `separate`:

```bash
# File upload
curl -X POST http://localhost:8000/api/analyze/file \
  -F "file=@sample_logs.txt" \
  -F "analysis_mode=combined"

# Text input
curl -X POST http://localhost:8000/api/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"text": "login attempt [ubuntu/ubuntu] succeeded", "analysis_mode": "combined"}'
```

---

## Folder Structure

```
LogDetAction/
├── backend/
│   ├── main.py              FastAPI app + lifespan
│   ├── config.py            pydantic-settings config
│   ├── database.py          async SQLAlchemy setup
│   ├── models/analysis.py   ORM models (analyses, log_results)
│   ├── schemas/analysis.py  Pydantic request/response schemas
│   ├── routers/
│   │   ├── upload.py        POST /api/analyze/file
│   │   ├── manual.py        POST /api/analyze/text
│   │   └── results.py       GET  /api/results/*
│   └── services/
│       ├── model_loader.py  Loads models once at startup
│       ├── pipeline_service.py  Core inference logic
│       ├── csv_service.py   CSV export
│       └── storage_service.py   SQLite read/write
│
├── frontend/
│   └── src/
│       ├── App.jsx          Root layout
│       ├── api/client.js    Axios API client
│       ├── store/           Zustand state
│       ├── hooks/           useAnalysis
│       ├── i18n/            EN / TR translations
│       └── components/
│           ├── layout/      Header
│           ├── input/       FileUploadZone, ManualInputPanel, ModeSelector
│           ├── dashboard/   SummaryCards, ResultTable, FilterBar, SearchInput
│           ├── shared/      LabelBadge, StatusBadge, LoadingOverlay, AnalystActionPanel
│           └── modals/      LogDetailModal
│
├── v2.0/                    Original experimental pipeline (reference, do not delete)
│   ├── analyze_log_pipeline.py
│   └── README.md
│
├── .env                     Local config (not committed)
├── .env.example             Config template
└── requirements.txt         Backend Python dependencies
```

---

## Known Limitations

- Trained primarily on **Cowrie SSH honeypot** and **HDFS** logs.
- Web server, firewall, authentication, and endpoint logs may show higher false positive rates.
- HDFS suspicious/anomaly detection requires block-level or session-level context; single-line classification is not reliable for that class.
- The `suspicious` class has lower precision — requires analyst correlation before escalation.

---

## Safety Boundaries

This system is a **read-only analysis tool**. It does NOT and MUST NOT:
- Block IPs or create firewall rules
- Lock or disable user accounts
- Execute system commands
- Delete, quarantine, or modify files
- Send alerts to external systems

All suggested analyst actions are **simulated** and require human approval.

---

## Sanal Ortam (`.venv`)

```powershell
cd c:\developer\LogDetAction
.\.venv\Scripts\Activate.ps1
```

`Activate.ps1` çalışmıyorsa:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Sistemi Çalıştırma Rehberi

Uygulamayı tam olarak ayağa kaldırmak için **3 ayrı terminal** açman gerekiyor.

### Terminal 1 — Backend (FastAPI)

```powershell
cd C:\developer\LogDetAction
.\.venv\Scripts\Activate.ps1
$env:PYTHONUTF8=1
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

> Model yüklenirken 30–60 saniye bekle. Terminalde şunu görünce hazır demektir:
> `INFO: All models ready in X.XXs`

---

### Terminal 2 — Frontend (React + Vite)

```powershell
cd C:\developer\LogDetAction\frontend
npm run dev
```

> Tarayıcıda aç: **http://localhost:5173**

---

### Terminal 3 — Canlı Log Üreticisi (Live Monitor demosu için)

Bu terminal sadece **Live Monitor** sekmesini test etmek istediğinde açılır.

```powershell
cd C:\developer\LogDetAction
.\.venv\Scripts\Activate.ps1
python backend/tools/log_generator.py
```

> Her 2 saniyede bir `backend/live/live_demo.log` dosyasına yeni bir log satırı yazar.  
> Durdurmak için **Ctrl+C** bas.

---

### Canlı İzleme Adımları (Live Monitor)

1. Yukarıdaki 3 terminali sırayla başlat.
2. Tarayıcıda **Live Monitor** sekmesine geç.
3. Analiz modunu seç (Fast Mode önerilir).
4. **Start Monitor** düğmesine bas.
5. Terminal 3'te log üretici çalışıyorsa, yeni satırlar otomatik analiz edilip tabloda görünür.
6. İzlemeyi durdurmak için **Stop Monitor** düğmesine bas.

---

### Hızlı Başvuru Tablosu

| Ne yapmak istiyorsun? | Komut |
|---|---|
| Backend başlat | `python -m uvicorn backend.main:app --reload` |
| Frontend başlat | `cd frontend && npm run dev` |
| Canlı log üret | `python backend/tools/log_generator.py` |
| Mevcut DB'yi sıfırla | `Remove-Item backend\logdetaction.db` |
| Test log dosyası oluştur | `python v2.0/build_test_samples.py` |
