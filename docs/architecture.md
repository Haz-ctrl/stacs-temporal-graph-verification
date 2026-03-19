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

## 3. Trace Semantics

`src/trace.py` constructs a step-indexed `TemporalTrace` from reasoning steps plus a final prediction state.

Each trace state can expose graph-grounded predicates such as:

- asserted relation labels at that state
- supported edges referenced by the current reasoning step
- mentioned events
- accumulated invariant violations
- newly introduced violations

This provides the execution domain for temporal specifications without conflating reasoning-step order with the aggregate graph representation.

## 4. Intrinsic Verification and Temporal Specifications

`src/constraints.py` verifies only intrinsic properties of the prediction:

- format: duplicate predicted edges
- grounding: hallucinated nodes and unsupported reasoning references
- intrinsic temporal consistency: antisymmetry, cycles, simultaneity conflicts, global inconsistency
- trace/spec checks: reasoning supports must be grounded in final predicted relations

`src/specs.py` and `src/ltl.py` add a two-tier specification interface:

- built-in invariants for fast structural checks
- a focused LTL subset over trace predicates

The currently implemented LTL subset supports:

- boolean connectives
- `X` (next)
- `F` (eventually)
- `G` (globally)
- `U` (until)

This layer does not use gold labels.

## 5. Gold Scoring

`src/evaluation.py` scores predictions against gold relations:

- direct metrics: exact label-aware edge matching
- closure metrics: ordering closure after relation normalisation
- completeness diagnostics: missing/spurious direct edges and closure pairs
- abstention diagnostics: empty predictions and gold-empty overcommitment

This separation is important for research validity because a structurally valid prediction can still differ from gold, and a closure-equivalent prediction can still differ in direct edge representation.

## 6. Reporting

`scripts/run_llm_baseline.py` produces reproducible run artefacts:

- `config.json`
- `predictions.jsonl`
- `report.json`

The report records dataset metadata, code revision, model metadata, intrinsic validity counts, formula violation counts, first-violation-step summaries, taxonomy counts, and aggregate scoring metrics.
