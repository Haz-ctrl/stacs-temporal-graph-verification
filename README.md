# stacs-temporal-graph-verification
**Author: Hashim Iqbal**

This repository contains the primary software artefact developed during my MSci Dissertation.

**Dissertation Title:**  
*"Verifying Language Model Reasoning Using Temporal Graph Constraints: A Structured Evaluation Approach"*

---

## Overview

This project investigates whether Large Language Model (LLM) reasoning can be:

1. Represented as a temporal graph
2. Verified against structural constraints (e.g. acyclicity, contradiction detection)
3. Evaluated using structured metrics beyond surface-level correctness

The repository contains:

- A JSONL task format for temporal reasoning problems
- An Ollama-based LLM integration (lab GPU compatible)
- A reproducible experiment runner
- Structured run outputs under `outputs/runs/`

This README focuses on **minimal setup and usage**.  
The final version will serve as a higher-level project overview.

---

# Project Structure (Current)

```

stacs-temporal-graph-verification/
├── data/                  # JSONL datasets
├── outputs/               # Run artefacts (timestamped)
│   └── runs/
├── scripts/
│   ├── lab_install_ollama.sh
│   ├── ollama_env.sh
|   ├── generate_temporal_dataset.py
|   ├── validate_dataset.py
│   └── run_llm_baseline.py
├── src/
│   ├── dataset.py
|   ├── dataset_validation.py
|   ├── constraints.py
|   ├── temporal_graph.py
│   ├── ollama_client.py
│   └── ollama_predictor.py
├── tests/
|   ├── test_constraints.py
├── requirements.txt
└── README.md

````

---

# Quickstart (Environment Setup)

## 1. SSH into a Lab GPU machine

```bash
ssh <username>@<lab-machine>
````

Confirm GPU availability:

```bash
nvidia-smi
```

---

## 2. Navigate to repository root

```bash
cd /path/to/stacs-temporal-graph-verification
```

---

## 3. Create and activate virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

---

# Ollama Setup (Lab AMD GPU)

> The download links on the CS wiki are outdated.
> This repository includes helper scripts to simplify installation, and pulls releases from GitHub.


## User install (run once or everytime you want to upgrade)

Run once on a lab machine, or everytime you need to upgrade the client

```bash
./scripts/lab_install_ollama.sh 0.17.6
```
You can specify a version *X.Y.Z* which will default to installing version 0.17.6 of the client.

This:

* Downloads Ollama binaries
* Installs them into `~/opt/ollama`
* Installs ROCm libraries for AMD GPUs
* Auto updates symlinks everytime a new version is installed


---

## Per-Shell Setup

Each new shell session:

```bash
source scripts/ollama_env.sh
```

This:

* Adds Ollama to PATH
* Verifies installation
* Checks server health
* Displays available models

---

## Start Ollama Server

If not already running:

```bash
nohup ollama serve > ~/ollama_serve.log 2>&1 &
```

Sanity check:

```bash
curl -s http://localhost:11434/api/tags | head
```

---

## Pull a Model

```bash
ollama pull qwen3.5:9b
```

List available models:

```bash
ollama list
```

---

# Running the LLM Baseline

Always run from the **repository root**.

```bash
python -m scripts.run_llm_baseline --model qwen3.5:9b
```

Optional arguments:

```bash
--data data/sample_tasks.jsonl
--temperature 0.0
--seed 42
--max-tasks 5
```

---

# Output Structure

Each run creates:

```
outputs/runs/<timestamp>/
├── config.json          # Reproducibility snapshot
├── predictions.jsonl    # Model outputs
└── report.json          # Summary metadata
```

Runs are timestamped in UTC to ensure reproducibility and traceability.

---

# Dataset Format (JSONL)

Each line in `data/*.jsonl` must be a single JSON object:

```json
{
  "id": "t001",
  "question": "...",
  "events": ["Event A", "Event B"],
  "gold_relations": [
    ["Event A", "Event B", "BEFORE"]
  ]
}
```

One object per line.

---

# Development Notes

Current implemented components:

* JSONL dataset loader
* Ollama client wrapper
* Strict JSON edge extraction
* Reproducible run script
* Timestamped experiment artefacts

Planned next components:

* Temporal graph construction (NetworkX)
* Constraint verification (acyclicity, contradictions, hallucinated nodes)
* Edge-level evaluation metrics (precision / recall / F1)
* Multi-model benchmarking
* Benchmark dataset adapters

---

# Running Tests
*Once again from the repository root*
```bash
pytest -q
```

---

# Notes on Reproducibility

Each run records:

* Model tag
* Temperature
* Seed
* Ollama server metadata
* Dataset path
* Timestamp (UTC)

This ensures experiments can be reproduced or audited later.

---

# Important

* Always run scripts using `python -m scripts.<script_name>` from the repo root.
* Do not store model binaries in the repository.
* Do not commit contents of `outputs/runs/`.

---
