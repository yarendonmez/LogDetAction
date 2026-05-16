📄 System Feasibility & Dataset Strategy Report

Project: Intelligent Log Analysis and Threat Detection System
Prepared for: BM495 Project
Environment: Local Training & Log Processing System

1️⃣ System Hardware Analysis

Based on the system performance screenshots, the hardware configuration is:

CPU: Intel i7-13650HX
GPU: NVIDIA RTX 4060 Laptop GPU
VRAM: 8 GB

RAM: 16 GB
Available RAM (typical): ~5.8 GB

Storage: NVMe SSD
Free Disk Space: ~260 GB

Operating System: Windows
Hardware Capability Assessment
Component	Status	Notes
CPU	✅ Strong	Suitable for parsing and preprocessing
GPU	✅ Suitable	Supports QLoRA training
RAM	⚠️ Limited	Requires chunk processing
Disk	✅ Strong	NVMe allows fast dataset processing
Key Limitation

The primary bottleneck is:

RAM (16GB total)

Not:

GPU
Disk
CPU
2️⃣ Dataset Strategy Decision

The selected dataset structure follows a SOC-style mixed log environment, simulating realistic cybersecurity operations.

Selected Dataset Architecture
System Logs (Normal + Failure)
            +
Attack Logs (Real Intrusions)
            +
Background Logs (Noise)

This structure improves:

realism
detection capability
evaluation quality
explainability
Recommended Dataset Sources
🥇 HDFS Dataset (Primary System Logs)
Source: LogPai HDFS Dataset
Type: Distributed System Logs

Recommended Size:

400,000 logs

Reason:

Industry-standard dataset
Widely used in anomaly detection
Structured enough for parsing
🥈 BGL Dataset (Secondary System Logs)
Source: BlueGene/L Logs
Type: Supercomputer Logs

Recommended Size:

250,000 logs

Reason:

Adds diversity
Reduces overfitting
Improves generalization
🥇 Cowrie Honeypot Dataset (Attack Logs)
Source: Cowrie SSH Honeypot Logs
Type: Real Attack Logs

Recommended Size:

120,000 logs

Reason:

Contains real intrusion attempts
Suitable for malicious behavior learning
Final Dataset Size Plan
HDFS   → 400,000 logs
BGL    → 250,000 logs
Cowrie → 120,000 logs

Total  → ~770,000 logs

This size is:

✅ Safe for RAM
✅ Suitable for training
✅ Realistic for research
3️⃣ Parsing Strategy Decision
Should Raw Logs Be Used Without Parsing?

Short Answer:

❌ Not recommended

Reason:

Raw logs are:

unstructured
memory-heavy
difficult to analyze
Recommended Parsing Strategy

Instead of full parsing, a Minimal Parsing Approach will be used.

Minimal Log Schema
timestamp
source
message
label
dataset
raw_message

Example:

timestamp: 2008-11-09 20:36:15
source: dfs.DataNode
message: PacketResponder block blk_38865049064139660
label: benign
dataset: HDFS
raw_message: original log line
Benefits of Minimal Parsing
✔ Reduces RAM usage
✔ Improves model learning
✔ Enables filtering
✔ Supports dashboard queries
✔ Keeps raw logs intact
4️⃣ Database Strategy

Selected database:

PostgreSQL

Reason:

✔ Stable
✔ Handles large logs
✔ Python compatible
✔ Fast indexing
Database Table Design
Table: logs

log_id
timestamp
source
message
dataset
label
confidence
explanation
recommendation
raw_message
Storage Strategy

Logs will be inserted using:

chunk-based insertion

Example:

chunk_size = 10000

This prevents:

RAM overflow
5️⃣ Model Training Strategy

Based on available hardware:

RTX 4060 (8GB VRAM)
RAM: 16GB

Full model training:

❌ Not feasible

Fine-tuning:

✅ Feasible
Selected Training Method
QLoRA Fine-Tuning

Why:

✔ Low memory usage
✔ GPU compatible
✔ Fast training
✔ Research-grade method
Recommended Models
Primary Model
Mistral-7B-Instruct (4-bit)

Estimated VRAM:

~6 GB

Fits GPU safely.

Alternative Model
Qwen2-7B-Instruct (4-bit)
Lightweight Test Model
TinyLlama

Used for:

pipeline testing
6️⃣ Training Dataset Size Plan
Training   → 200,000 logs
Validation → 50,000 logs
Test       → 50,000 logs

Total Used for Training:

300,000 logs

Remaining logs:

Used for inference testing
7️⃣ Memory Optimization Strategy

Required due to:

Limited RAM (~5.8 GB usable)
Optimization Methods
Chunk Processing
chunk_size = 10000

Used for:

loading logs
parsing
inserting into database
Lazy Loading
Load only required data

Avoids:

full dataset loading
Quantization

Model precision:

4-bit quantization

This reduces:

VRAM usage
8️⃣ Pipeline Overview

Final processing pipeline:

Dataset Download
        ↓
Parsing (Minimal)
        ↓
Database Insertion
        ↓
Dataset Labeling
        ↓
Model Training (QLoRA)
        ↓
Evaluation
        ↓
Dashboard Visualization
9️⃣ Identified Risks
⚠️ RAM Overflow Risk

Cause:

Loading large logs at once

Mitigation:

Chunk processing
⚠️ Training Failure Risk

Cause:

Improper model size

Mitigation:

Use quantized models
⚠️ Dataset Imbalance Risk

Cause:

Too many benign logs

Mitigation:

Balance labels
⚠️ Storage Growth Risk

Cause:

Raw logs accumulation

Mitigation:

Archive old logs
🔟 Strengths of Current Design
✔ Realistic SOC dataset structure
✔ Compatible with hardware
✔ Modular pipeline design
✔ Supports explainable AI
✔ Scalable architecture
✔ Uses real-world logs
1️⃣1️⃣ Weaknesses
⚠️ RAM limitations
⚠️ Requires careful memory control
⚠️ Training time may be long
⚠️ Parsing complexity
1️⃣2️⃣ Opportunities
✔ Extend to real-time detection
✔ Add SIEM integration
✔ Expand dataset sources
✔ Deploy as web dashboard
1️⃣3️⃣ Threats (Technical Risks)
⚠️ Dataset corruption
⚠️ GPU overheating
⚠️ Storage exhaustion
⚠️ Model overfitting
📌 Final Technical Conclusion

This system is:

✅ Feasible on current hardware
✅ Suitable for academic research
✅ Capable of real-world simulation

With:

Minimal Parsing
Chunk Processing
QLoRA Training
Mixed SOC Dataset

the project can be implemented successfully and reliably on the available system.