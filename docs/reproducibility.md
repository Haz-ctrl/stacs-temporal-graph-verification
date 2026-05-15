# Reproducibility & Experiment Workflow

This document is the end-to-end guide for running, summarising, and extending experiments.

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | ≥ 3.10 | virtual env strongly recommended |
| Ollama | latest | `brew install ollama` / platform installer |
| Models | — | pull each model before its first run (see below) |
| scipy | 1.13.x | installed via `requirements.txt` |

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Confirm Ollama is running:

```bash
ollama serve &    # or start via the desktop app
ollama list       # should show installed models
```

Pull a model before use:

```bash
ollama pull deepseek-r1:7b
ollama pull qwen3.5:9b
ollama pull llama3.1:8b
ollama pull mistral:7b
ollama pull gemma3:12b
```

---

## Pipeline Overview

```
Dataset (JSONL)
    │
    ▼
run_llm_baseline.py  ──►  outputs/runs/<run_id>/
    ├── config.json          (model tag, seed, temp, dataset version, git SHA)
    ├── predictions.jsonl    (per-task prediction + verification + scoring)
    └── report.json          (aggregate metrics)
    │
    ▼
summarise_runs.py  ──►  outputs/analysis/<group>/
    ├── summary.csv
    ├── category_breakdown.csv
    ├── difficulty_breakdown.csv
    ├── failure_breakdown.csv
    ├── counterexamples.md
    ├── report.md
    └── plots/*.png
    │
    ▼
generate_analysis_plots.py  ──►  outputs/analysis/supplementary_plots/
    └── (11 dissertation figures)
```

---

## Datasets

### Canonical synthetic set (primary)

```bash
python -m scripts.validate_dataset --data data/temporal_reasoning_eval.jsonl
```

250 tasks: 60 linear_chain, 50 transitive_reasoning, 30 long_chain, 60 ambiguous, 50 contradiction.

### TempEval-3 slice

```bash
python -m scripts.validate_dataset --data data/tempeval_eval.jsonl --profile generic
```

496 tasks derived from TempEval-3 Platinum event-event TLINKs. To rebuild from raw TimeML:

```bash
python -m scripts.import_tempeval3 \
  --input-root path/to/tempeval_3 \
  --split test \
  --output data/tempeval_eval.jsonl
```

### Diagnostic slice

```bash
python -m scripts.validate_dataset --data data/diagnostic_eval.jsonl --profile generic
```

Hand-authored stress tasks for ambiguity, temporal anchors, and richer relations.

### MAVEN-ERE slice

Validate the checked-in MAVEN-ERE validation slice:

```bash
python -m scripts.validate_dataset --data data/maven_ere_balanced_2to1.jsonl --profile generic
```

This checked-in slice was produced from the MAVEN-ERE `valid` split with:

- `EVENT-EVENT` pairs only
- supported labels only (`BEFORE`, `SIMULTANEOUS`)
- `OVERLAP` left excluded by default
- a `BEFORE` cap of `2.0x` the `SIMULTANEOUS` pool

To rebuild it from raw MAVEN-ERE:

```bash
python -m scripts.import_maven_ere \
  --input data/raw/MAVEN_ERE/valid.jsonl \
  --split valid \
  --output data/maven_ere_balanced_2to1.jsonl \
  --stats-out data/maven_ere_balanced_2to1_stats.json \
  --category maven_ere_temporal \
  --context-radius 1 \
  --before-multiplier 2.0 \
  --seed 42
```

Useful importer flags:

| Flag | Default | Purpose |
|------|---------|---------|
| `--coarsen-overlap` | off | Map MAVEN-ERE `OVERLAP` to `SIMULTANEOUS` |
| `--no-event-event-only` | off | Also include EVENT-TIMEX and TIMEX-TIMEX |
| `--max-tasks` | `0` | Hard cap after sampling |
| `--stats-out` | empty | Write conversion statistics JSON |

To generate unlabeled MAVEN-ERE test candidates for model inference:

```bash
python -m scripts.import_maven_ere \
  --input data/raw/MAVEN_ERE/test.jsonl \
  --split test \
  --output data/maven_ere_test_candidates.jsonl \
  --stats-out data/maven_ere_test_candidates_stats.json \
  --category maven_ere_temporal \
  --context-radius 1 \
  --test-sentence-window 1
```

### Generating new synthetic data

```bash
python -m scripts.generate_temporal_dataset \
  --out data/temporal_reasoning_eval_v2.jsonl \
  --n 300
```

Then validate before use:

```bash
python -m scripts.validate_dataset --data data/temporal_reasoning_eval_v2.jsonl
```

---

## Running Experiments

### Single model — LLM mode

```bash
python -m scripts.run_llm_baseline \
  --model qwen3.5:9b \
  --data data/temporal_reasoning_eval.jsonl \
  --pred-source llm \
  --seed 42 \
  --temperature 0.0 \
  --max-tasks 0 \
  --base-url http://localhost:11434 \
  --timeout-s 120 \
  --max-retries 3 \
  --retry-backoff-s 2.0 \
  --output-root outputs/runs \
  --validate-data \
  --log-raw
```

Useful flags:

| Flag | Default | Purpose |
|------|---------|---------|
| `--model` | — | Ollama model tag |
| `--data` | `data/temporal_reasoning_eval.jsonl` | Dataset path |
| `--pred-source` | `llm` | `llm`, `gold`, `empty`, `noisy` |
| `--seed` | 42 | Random seed for non-LLM sources |
| `--temperature` | 0.0 | Sampling temperature |
| `--max-tasks` | 0 (all) | Limit tasks for screening runs |
| `--base-url` | `http://localhost:11434` | Ollama endpoint |
| `--timeout-s` | client default | Per-request read timeout |
| `--max-retries` | client default | Transport retry attempts |
| `--retry-backoff-s` | client default | Exponential backoff base |
| `--log-raw` | off | Save raw model output per task |
| `--validate-data` | on | Validate input JSONL before running |
| `--strict-data` | off | Tighten dataset validation checks |
| `--output-root` | `outputs/runs/` | Where to write run dirs |

### Sanity check without a model

Before spending time on LLM runs, use gold mode to confirm the pipeline:

```bash
python -m scripts.run_llm_baseline --pred-source gold
python -m scripts.run_llm_baseline --pred-source empty
```

Gold mode should produce near-perfect scores; empty mode produces all-zero scores.

### Full sweep from a manifest

A manifest is a JSON list of model configs:

```json
[
  {
    "model": "qwen3.5:9b",
    "label": "Qwen 3.5 9B",
    "family": "qwen",
    "size": "9b",
    "reasoning_tuned": false,
    "group": "baseline",
    "notes": ""
  },
  {
    "model": "deepseek-r1:7b",
    "label": "DeepSeek R1 7B",
    "family": "deepseek",
    "size": "7b",
    "reasoning_tuned": true,
    "group": "reasoning",
    "notes": "Chain-of-thought tuned"
  }
]
```

| Field | Required | Purpose |
|-------|----------|---------|
| `model` | yes | Ollama tag |
| `label` | yes | Human-readable name for plots |
| `family` | no | Model family for grouping |
| `size` | no | Parameter count for axis labelling |
| `reasoning_tuned` | no | Boolean flag for RQ analysis |
| `group` | no | Sweep subgroup for filtering |
| `notes` | no | Free text |

```bash
python -m scripts.run_model_sweep \
  --manifest manifests/lab_models.json \
  --data data/temporal_reasoning_eval.jsonl \
  --seed 42 \
  --temperature 0.0 \
  --max-tasks 0 \
  --base-url http://localhost:11434 \
  --timeout-s 120 \
  --max-retries 3 \
  --retry-backoff-s 2.0 \
  --output-root outputs/runs/canonical_full \
  --continue-on-error \
  --log-raw
```

To sweep across a second dataset without repeating model pulls:

```bash
python -m scripts.run_model_sweep \
  --manifest manifests/lab_models.json \
  --data data/tempeval_eval.jsonl \
  --seed 42 \
  --temperature 0.0 \
  --base-url http://localhost:11434 \
  --timeout-s 120 \
  --max-retries 3 \
  --retry-backoff-s 2.0 \
  --output-root outputs/runs/tempeval_full \
  --continue-on-error \
  --log-raw
```

To run the same sweep on MAVEN-ERE:

```bash
python -m scripts.run_model_sweep \
  --manifest manifests/lab_models.json \
  --data data/maven_ere_balanced_2to1.jsonl \
  --seed 42 \
  --temperature 0.0 \
  --max-tasks 0 \
  --base-url http://localhost:11434 \
  --timeout-s 120 \
  --max-retries 3 \
  --retry-backoff-s 2.0 \
  --output-root outputs/runs/maven_ere_full \
  --continue-on-error \
  --log-raw
```

Sweep-level flags:

| Flag | Default | Purpose |
|------|---------|---------|
| `--manifest` | — | JSON list of model entries |
| `--data` | `data/temporal_reasoning_eval.jsonl` | Dataset path for every manifest entry |
| `--seed` | 42 | Shared random seed |
| `--temperature` | 0.0 | Shared decoding temperature |
| `--max-tasks` | 0 | Shared task limit unless overridden per entry |
| `--base-url` | `http://localhost:11434` | Shared Ollama endpoint |
| `--timeout-s` | client default | Shared read timeout unless overridden per entry |
| `--max-retries` | client default | Shared transport retries unless overridden per entry |
| `--retry-backoff-s` | client default | Shared retry backoff unless overridden per entry |
| `--output-root` | `outputs/runs` | Root directory for created run dirs and sweep metadata |
| `--log-raw` | off | Save raw model outputs |
| `--continue-on-error` | off | Record failed models in `sweep_index.json` and continue |

Manifest entries can also override `base_url`, `max_tasks`, `timeout_s`, `max_retries`, and `retry_backoff_s` per model.

---

## Summarising Runs

Point `summarise_runs.py` at a directory that contains one or more run subdirectories:

```bash
python -m scripts.summarise_runs \
  --runs outputs/runs/canonical_full \
  --out outputs/analysis/canonical_full
```

For TempEval:

```bash
python -m scripts.summarise_runs \
  --runs outputs/runs/tempeval_full \
  --out outputs/analysis/tempeval_full
```

For MAVEN-ERE:

```bash
python -m scripts.summarise_runs \
  --runs outputs/runs/maven_ere_full \
  --out outputs/analysis/maven_ere_full
```

Output files:

| File | Contents |
|------|----------|
| `summary.csv` | Per-run top-line metrics, uncertainty intervals, diagnostic rates |
| `category_breakdown.csv` | Category-specific fidelity and consistency |
| `difficulty_breakdown.csv` | Structural complexity slices |
| `failure_breakdown.csv` | Parse and verification failure rates |
| `counterexamples.md` | Representative parse and verification failures |
| `report.md` | Narrative summary (warns when run is screening-scale only) |
| `plots/*.png` | Static figures for reports and slides |

---

## Generating Dissertation Plots

Requires completed canonical and TempEval analysis directories:

```bash
python scripts/generate_analysis_plots.py \
  --canonical-dir   outputs/runs/canonical_full \
  --tempeval-dir    outputs/runs/tempeval_full \
  --canonical-analysis outputs/analysis/canonical_full \
  --tempeval-analysis  outputs/analysis/tempeval_full \
  --out outputs/analysis/supplementary_plots
```

The 10 output figures:

| Filename | Description |
|----------|-------------|
| `violation_type_model_heatmap.png` | YlOrRd heatmap of violation frequency by model |
| `verifier_screening_signal.png` | Grouped bars: precision, recall, specificity |
| `direct_vs_closure_f1_by_category.png` | Direct F1 vs closure F1, split by category |
| `cross_dataset_comparison.png` | Canonical vs TempEval direct and closure F1 |
| `first_violation_step_distribution.png` | Density histogram of first violation step per model |
| `model_category_performance_matrix.png` | RdYlGn heatmap (model × category) |
| `ambiguity_and_contradiction.png` | Stacked bar (abstention rate) + bar (contradiction rate) |
| `rq3_spearman_heatmap.png` | Verifier-signal × correctness Spearman correlations |
| `accuracy_by_verifier_verdict.png` | Paired bars: accuracy when valid vs invalid |
| `failure_scope_contribution.png` | Stacked bar of failure scope by model |

A `rq3_spearman_correlations.csv` is also written alongside the plots.

---

## Inspecting Runs in the Browser

```bash
open tools/verifier_explorer.html   # macOS
```

Then click **Load predictions.jsonl** and select any `predictions.jsonl` from a run directory. No server required — all processing is client-side.

The explorer shows:
- task list with category chip, pass/fail dot, and free-text filter
- prediction detail: events, predicted relations, gold relations (colour-coded)
- verification panel: violations by type with first-violation-step highlighted in the trace
- aggregate statistics: validity rate, avg F1, category distribution, top-5 violation types

---

## Adding New Models

1. Pull the model: `ollama pull <tag>`
2. Add an entry to the relevant manifest in `manifests/`
3. Re-run the sweep command — existing run dirs are unaffected
4. Re-run `summarise_runs.py` to regenerate analysis outputs
5. Re-run `generate_analysis_plots.py` to refresh plots

---

## Adding New Datasets

1. Validate the JSONL: `python -m scripts.validate_dataset --data <path>`
2. Run a gold-mode sanity check: `python -m scripts.run_llm_baseline --pred-source gold --data <path>`
3. Create a dedicated output root: `--output-root outputs/runs/<new_group>`
4. Run the sweep with `--data <path>`
5. Point `summarise_runs.py` at the new output root

---

## Reproducibility Guarantees

Each run writes a `config.json` recording:

- dataset path and `dataset_version` (SHA-256 of the JSONL)
- model tag and provider metadata
- seed and sampling temperature
- prediction source
- code revision (`git rev-parse HEAD`)

The non-LLM sources (`gold`, `empty`, `noisy`) are deterministic with a fixed seed. LLM sources depend on Ollama's sampling implementation and local model weights; results may differ across Ollama versions even with `temperature=0`.

To reproduce a specific run: match the `model`, `seed`, `temperature`, `pred_source`, and `dataset_version` fields from `config.json`.

---

## Determinism Note

The synthetic and non-LLM modes are fully deterministic with a fixed seed.

LLM mode depends on the server-side model implementation, sampling settings, and local model availability. The run report stores model metadata and an Ollama tag snapshot to aid in reconstruction.
