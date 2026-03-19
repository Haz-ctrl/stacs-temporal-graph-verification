# stacs-temporal-graph-verification

**Author:** Hashim Iqbal

**MSci Dissertation Artefact**

**Dissertation Title:**  
*"Verifying Language Model Reasoning Using Temporal Graph Constraints: A Structured Evaluation Approach"*

## Overview

This repository evaluates temporal reasoning outputs from language models by converting structured predictions into temporal graphs, checking intrinsic consistency constraints, and scoring predictions against gold temporal relations.

The current implementation is designed around four explicit layers:

1. `prediction`: parse structured model output into typed events, relations, and reasoning steps
2. `verification`: check intrinsic validity without consulting gold labels
3. `scoring`: compare predicted relations against gold direct edges and ordering closure
4. `reporting`: write reproducible run artefacts with metadata, per-task records, and aggregate metrics

This repo currently supports relation labels `BEFORE`, `AFTER`, `SIMULTANEOUS`, and `UNKNOWN`. Ordering evaluation normalises `AFTER`, collapses `SIMULTANEOUS` groups before closure, and treats `UNKNOWN` as abstention rather than an ordering edge.

## Research Scope

The implementation is aimed at:

- structured temporal reasoning evaluation
- temporal graph verification with interpretable failure analysis
- direct-edge and closure-level scoring
- reproducible experiment runs for dissertation reporting and demos

It is not yet a full general LTL model checker. The current verifier is a typed constraint library with a lightweight formal-spec direction, which is documented in [evaluation_design.md](docs/evaluation_design.md) and [literature_alignment.md](docs/literature_alignment.md).

## Repository Layout

```text
stacs-temporal-graph-verification/
├── data/
├── docs/
├── outputs/
│   └── runs/
├── scripts/
│   ├── generate_temporal_dataset.py
│   ├── run_llm_baseline.py
│   └── validate_dataset.py
├── src/
│   ├── constraints.py
│   ├── dataset.py
│   ├── dataset_validation.py
│   ├── evaluation.py
│   ├── ollama_client.py
│   ├── prediction_schema.py
│   ├── results.py
│   ├── schemas.py
│   ├── structured_predictor.py
│   ├── taxonomy.py
│   └── temporal_graph.py
├── tests/
├── requirements.txt
└── README.md
```

## Quickstart

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the test suite:

```bash
pytest -q
```

Validate the canonical synthetic dataset:

```bash
python -m scripts.validate_dataset --data data/temporal_reasoning_eval.jsonl
```

Run the baseline pipeline with gold labels as predictions:

```bash
python -m scripts.run_llm_baseline --pred-source gold
```

Run the structured Ollama pipeline:

```bash
python -m scripts.run_llm_baseline --model qwen3.5:9b --pred-source llm
```

Important defaults:

- default dataset: `data/temporal_reasoning_eval.jsonl`
- default output root: `outputs/runs/`
- dataset validation is enabled by default

## Run Outputs

Each run writes a timestamped directory under `outputs/runs/<timestamp>/` containing:

- `config.json`: run config, dataset version, and code revision
- `predictions.jsonl`: per-task records with prediction, verification, and scoring outputs
- `report.json`: aggregate metrics and run metadata

Per-task records now separate:

- `verification`: intrinsic validity and violation details
- `score`: direct metrics, closure metrics, closure preservation, abstention, and overcommitment

## Datasets

Current dataset files have different roles:

- `data/temporal_reasoning_eval.jsonl`: canonical runnable synthetic evaluation set
- `data/sample_tasks.jsonl`: small quickstart example set using the same schema
- `data/synthetic_v2.jsonl`: legacy exploratory dataset with older category naming
- `data/constraint_fixtures.jsonl`: fixture-style examples for verifier-oriented checks

See [dataset_schema.md](docs/dataset_schema.md) for the canonical schema and current scope boundaries.

## Documentation

- [Architecture](docs/architecture.md)
- [Evaluation Design](docs/evaluation_design.md)
- [Dataset Schema](docs/dataset_schema.md)
- [Reproducibility](docs/reproducibility.md)
- [Limitations](docs/limitations.md)
- [Literature Alignment](docs/literature_alignment.md)

## Current Status

Implemented:

- typed task, prediction, verification, scoring, and report models
- temporal graph handling for `BEFORE`, `AFTER`, `SIMULTANEOUS`, and `UNKNOWN`
- intrinsic constraint verification separated from gold scoring
- label-aware direct metrics and ordering-closure metrics
- overcommitment and abstention reporting
- reproducible run artefacts with dataset and code metadata
- unit and integration tests for graph semantics, scoring, verification, parsing, and the runner

Still future work:

- external benchmark adapters such as TORQUE- or TempEval-style imports
- richer visualisation and counterexample playback
- confidence calibration analysis
- a broader formal specification interface beyond the current constraint library
