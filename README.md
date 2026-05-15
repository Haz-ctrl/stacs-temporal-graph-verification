# stacs-temporal-graph-verification

**Author:** Hashim Iqbal

**MSci Dissertation Artefact**

**Dissertation Title:**  
*"Verifying Language Model Reasoning Using Temporal Graph Constraints: A Structured Evaluation Approach"*

## Overview

This repository evaluates temporal reasoning outputs from language models by converting structured predictions into temporal graphs, constructing a step-indexed reasoning trace, checking intrinsic temporal specifications, and scoring predictions against gold temporal relations.

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

It is not yet a full general LTL model checker. The current verifier combines a typed invariant library with a focused, graph-grounded LTL subset over step traces, which is documented in [evaluation_design.md](docs/evaluation_design.md) and [literature_alignment.md](docs/literature_alignment.md).

## Repository Layout

```text
stacs-temporal-graph-verification/
├── data/                          # JSONL datasets (canonical, TempEval-3, MAVEN-ERE, diagnostic)
├── docs/                          # Design notes, schema, reproducibility guide
├── manifests/                     # Model sweep manifests (JSON list of model configs)
├── outputs/
│   ├── runs/                      # Per-run artefacts (one timestamped dir per run)
│   └── analysis/                  # Summarised CSVs, plots, and report.md per group
├── scripts/
│   ├── convert_tempeval_style.py  # Convert simplified TempEval-style JSONL → canonical
│   ├── evaluate_pairwise_run.py   # Export pairwise classification audit for a run
│   ├── generate_analysis_plots.py # Generate all supplementary dissertation plots
│   ├── generate_temporal_dataset.py # Generate new synthetic JSONL datasets
│   ├── import_maven_ere.py       # Convert MAVEN-ERE temporal JSONL → canonical JSONL
│   ├── import_matres.py          # Convert MATRES + TimeML → canonical JSONL
│   ├── import_tempeval3.py        # Convert TempEval-3 TimeML files → canonical JSONL
│   ├── run_llm_baseline.py        # Run a single model on a dataset
│   ├── run_model_sweep.py         # Run multiple models sequentially from a manifest
│   ├── summarise_runs.py          # Aggregate run dirs → CSVs, plots, and report.md
│   └── validate_dataset.py        # Validate a JSONL dataset before running
├── src/
│   ├── analysis/
│   │   ├── axis_correlation.py    # Intrinsic-axis pairwise correlation
│   │   └── correctness_correlation.py  # RQ3 verifier-to-correctness correlation
│   ├── constraints.py
│   ├── dataset.py
│   ├── dataset_validation.py
│   ├── evaluation.py
│   ├── ltl.py
│   ├── ollama_client.py
│   ├── prediction_schema.py
│   ├── results.py
│   ├── schemas.py
│   ├── specs.py
│   ├── structured_predictor.py
│   ├── taxonomy.py
│   ├── temporal_graph.py
│   └── trace.py
├── tests/
├── tools/
│   └── verifier_explorer.html     # Self-contained browser-based run inspector
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

Validate the external-style and diagnostic slices:

```bash
python -m scripts.validate_dataset --data data/tempeval_eval.jsonl --profile generic
python -m scripts.validate_dataset --data data/diagnostic_eval.jsonl --profile generic
```

Run the baseline pipeline with gold labels as predictions:

```bash
python -m scripts.run_llm_baseline --pred-source gold
```

Run the structured Ollama pipeline:

```bash
python -m scripts.run_llm_baseline --model qwen3.5:9b --pred-source llm
```

Run a lab-style model sweep from a JSON manifest:

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
  --log-raw \
  --continue-on-error
```

By default the sweep also summarises completed runs into
`outputs/analysis/<sweep-name>` when the output root is under `outputs/runs`.
Use `--analysis-out <path>` to choose a different analysis directory, or
`--skip-analysis` if you only want raw run artefacts.

Summarise a set of completed runs into tables and plots:

```bash
python -m scripts.summarise_runs --runs outputs/runs/canonical_full --out outputs/analysis/canonical_full
```

The summariser is designed for supervisor-facing evaluation work. It writes:

- `summary.csv`: top-line per-run metrics, uncertainty intervals, and diagnostic rates
- `category_breakdown.csv`: category-specific fidelity and consistency summaries
- `difficulty_breakdown.csv`: structural complexity slices
- `failure_breakdown.csv`: parse and verification failures using affected-task rates
- `counterexamples.md`: representative parse and verification failures
- `report.md`: narrative summary that warns when a run is only a screening-scale slice
- `plots/`: static PNG figures for reports and slides

Generate supplementary dissertation plots (requires summarised analysis directories):

```bash
python scripts/generate_analysis_plots.py \
    --canonical-dir  outputs/runs/canonical_v2 \
    --tempeval-dir   outputs/runs/tempeval_v2 \
    --maven-ere-dir  outputs/runs/maven_ere_v2 \
    --canonical-analysis outputs/analysis/canonical_v2 \
    --tempeval-analysis  outputs/analysis/tempeval_v2 \
    --maven-ere-analysis outputs/analysis/maven_ere_v2 \
    --out outputs/analysis/supplementary_plots
```

The cross-dataset and RQ3 correlation plots compare the canonical synthetic,
TempEval-3, and MAVEN-ERE analysis outputs. Synthetic-only diagnostic plots
still use the canonical categories.

Inspect any run interactively in the browser (no server needed):

```
open tools/verifier_explorer.html   # macOS
# then use the "Load predictions.jsonl" button
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

- `verification`: graph validity, trace grounding, formula-level violations, first-violation-step metadata, and active specification details
- `score`: direct metrics, closure metrics, closure preservation, abstention, and overcommitment

## Datasets

Current dataset files have different roles:

- `data/temporal_reasoning_eval.jsonl`: canonical runnable synthetic evaluation set
- `data/tempeval_eval.jsonl`: TempEval-3 Platinum event-event slice in canonical task format using a conservative coarse mapping onto `BEFORE`, `AFTER`, and `SIMULTANEOUS`
- `data/maven_ere_balanced_2to1.jsonl`: checked-in MAVEN-ERE validation slice with a 2:1 `BEFORE`:`SIMULTANEOUS` balance over EVENT-EVENT pairs
- `data/matres_balanced_small.jsonl`: checked-in MATRES TimeBank/AQUAINT slice balanced across `BEFORE`, `AFTER`, `SIMULTANEOUS`, and `UNKNOWN`
- `data/tempeval_style_fixture.jsonl`: simplified adapter input for TempEval-style conversion
- `data/diagnostic_eval.jsonl`: hand-authored diagnostic stress slice for ambiguity, anchors, and richer relations
- `data/sample_tasks.jsonl`: small quickstart example set using the same schema
- `data/synthetic_v2.jsonl`: legacy exploratory dataset with older category naming
- `data/constraint_fixtures.jsonl`: fixture-style examples for verifier-oriented checks

To rebuild the TempEval slice from raw TempEval-3 TimeML files:

```bash
python -m scripts.import_tempeval3 \
  --input-root path/to/tempeval_3 \
  --split test \
  --output data/tempeval_eval.jsonl
```

The checked-in external slice is derived from the TempEval-3 Platinum test documents and keeps only event-event TLINKs that map cleanly into the repo's current label set:

- `BEFORE`, `IBEFORE` -> `BEFORE`
- `AFTER`, `IAFTER` -> `AFTER`
- `SIMULTANEOUS`, `IDENTITY` -> `SIMULTANEOUS`

Interval relations such as `INCLUDES` or `IS_INCLUDED` are intentionally excluded rather than coerced.

To rebuild the checked-in MAVEN-ERE validation slice from the raw benchmark:

1. Download `MAVEN-ERE.zip` from the official [THU-KEG MAVEN-ERE repository](https://github.com/THU-KEG/MAVEN-ERE) using the [Tsinghua Cloud mirror](https://cloud.tsinghua.edu.cn/f/a7d1db6c44ea458bb6f0/).
2. Extract it so the raw files are under `data/raw/MAVEN_ERE/`.

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

For benchmark test-set prediction export:

```bash
python -m scripts.import_maven_ere \
  --input data/raw/MAVEN_ERE/test.jsonl \
  --split test \
  --output data/maven_ere_test_candidates.jsonl \
  --category maven_ere_temporal \
  --context-radius 1 \
  --test-sentence-window 1
```

To rebuild the checked-in MATRES slice, first place the matching TempEval-3 TimeBank/AQUAINT TimeML files under one local directory, then run:

```bash
python -m scripts.import_matres \
  --matres-input https://raw.githubusercontent.com/qiangning/MATRES/master/timebank.txt \
  --matres-input https://raw.githubusercontent.com/qiangning/MATRES/master/aquaint.txt \
  --timeml-root path/to/TempEval3/Training/TBAQ-cleaned \
  --output data/matres_balanced_small.jsonl \
  --stats-out data/matres_balanced_small_stats.json \
  --category matres_temporal \
  --max-per-label 100 \
  --seed 42
```

MATRES `VAGUE` is mapped to `UNKNOWN`. Report these tasks with direct/pairwise label metrics and abstention behaviour; `UNKNOWN` deliberately contributes no ordering edge, so closure F1 is not the right headline metric for that slice.

See [dataset_schema.md](docs/dataset_schema.md) for the canonical schema and current scope boundaries.

## Documentation

- [Architecture](docs/architecture.md)
- [Evaluation Design](docs/evaluation_design.md)
- [Evaluation Reporting](docs/evaluation_reporting.md)
- [Dataset Schema](docs/dataset_schema.md)
- [Reproducibility & Experiment Workflow](docs/reproducibility.md)
- [Limitations](docs/limitations.md)
- [Literature Alignment](docs/literature_alignment.md)
- [RQ3 Future Work](docs/rq3_future_work.md)

## Current Status

Implemented:

- typed task, prediction, verification, scoring, and report models
- temporal graph handling for `BEFORE`, `AFTER`, `SIMULTANEOUS`, and `UNKNOWN`
- intrinsic constraint verification separated from gold scoring
- step-indexed temporal traces for reasoning-step verification
- focused LTL operators `G`, `F`, `X`, and `U` over graph-grounded predicates
- label-aware direct metrics and ordering-closure metrics
- overcommitment and abstention reporting
- separate reporting for graph validity, trace grounding, parse failures, and transport failures
- reproducible run artefacts with dataset, code, and specification metadata
- model sweep orchestration for Ollama-backed lab evaluations
- cross-run aggregation with static plots and counterexample summaries
- TempEval-3 adapter, MAVEN-ERE adapter/submission builder, and diagnostic evaluation slice
- RQ3 verifier-to-correctness Spearman correlation module (`src/analysis/correctness_correlation.py`)
- eleven supplementary dissertation plots generated by `scripts/generate_analysis_plots.py`
- browser-based run inspector (`tools/verifier_explorer.html`)
- unit and integration tests for graph semantics, scoring, verification, parsing, and the runner

Still future work:

- logprob capture in `OllamaClient` for full RQ3 confidence-vs-correctness analysis
- TORQUE-style or MATRES temporal QA benchmark adapters
- a broader temporal specification language and user-facing formula parser
