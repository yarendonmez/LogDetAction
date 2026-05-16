# Dataset Selection Summary – Cowrie Honeypot Logs

## Overview

This document summarizes the selection strategy and current status of the Cowrie Honeypot dataset used in the log anomaly detection / intrusion detection project.

The goal is to construct a balanced dataset that includes malicious log behavior while maintaining manageable processing size for model training.

---

# Dataset Source

Dataset:

Cowrie Honeypot Logs  
Source:

https://www.kaggle.com/datasets/xmlyna/cowrie-honeypot

Dataset Type:

Attack / Malicious Logs

---

# Dataset Structure

The dataset consists of daily JSON log files.

Each file:

- Represents **one day of attack activity**
- Contains multiple event logs
- Each line is a JSON record

Example:

```json
{
  "eventid": "cowrie.login.failed",
  "src_ip": "61.177.173.37",
  "username": "root",
  "password": "123456"
}