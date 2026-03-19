# Architecture Overview

The implementation is organised as a research and evaluation pipeline with explicit boundaries delineating prediction, verification, scoring, and reporting.

## 1. Prediction

`src/structured_predictor.py` and `src/prediction_schema.py` are responsible for:

- prompting the model for strict structured JSON
- parsing that JSON into typed `ParsedPrediction` objects
- preserving raw output for reproducibility and debugging

The prediction layer is intentionally separate from gold labels and constraint logic.

## 2. Temporal Graph Construction

`src/temporal_graph.py` stores asserted temporal relations without collapsing them into a single edge per event pair.

Key semantics:

- `BEFORE(a, b)` contributes ordering edge `a -> b`
- `AFTER(a, b)` contributes ordering edge `b -> a`
- `SIMULTANEOUS(a, b)` creates an equivalence relation used before ordering closure
- `UNKNOWN(a, b)` is retained as a direct label but does not contribute to ordering closure

## 3. Intrinsic Verification

`src/constraints.py` verifies only intrinsic properties of the prediction:

- format: duplicate predicted edges
- grounding: hallucinated nodes and unsupported reasoning references
- intrinsic temporal consistency: antisymmetry, cycles, simultaneity conflicts, global inconsistency
- trace/spec checks: reasoning supports must be grounded in final predicted relations

This layer does not use gold labels.

## 4. Gold Scoring

`src/evaluation.py` scores predictions against gold relations:

- direct metrics: exact label-aware edge matching
- closure metrics: ordering closure after relation normalisation
- completeness diagnostics: missing/spurious direct edges and closure pairs
- abstention diagnostics: empty predictions and gold-empty overcommitment

This separation is important for research validity because a structurally valid prediction can still differ from gold, and a closure-equivalent prediction can still differ in direct edge representation.

## 5. Reporting

`scripts/run_llm_baseline.py` produces reproducible run artefacts:

- `config.json`
- `predictions.jsonl`
- `report.json`

The report records dataset metadata, code revision, model metadata, intrinsic validity counts, taxonomy counts, and aggregate scoring metrics.
