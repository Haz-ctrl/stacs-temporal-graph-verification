# Changes — Interim Dissertation Tightening

This document records all changes made as part of the interim submission tightening pass. Changes are grouped by task and list every modified file with the rationale.

---

## Task 1: Coverage-Aware Closure F1

**Problem addressed:** Closure F1 was reported without a coverage denominator. A model that abstains on most pairs and gets the remainder right can appear as a strong ordering recoverer. The committed-only and full variants were not distinguished.

**Files modified:**

- `src/run_summary.py`
  - Added `_closure_coverage()` helper: computes the fraction of gold-bearing tasks for which the model made a non-UNKNOWN ordering commitment.
  - Added `_committed_closure_prf()` helper: micro-averages PRF only over tasks where both gold and pred produce ordering pairs.
  - Updated `_run_row()` to emit three new summary.csv columns: `closure_coverage`, `fidelity_closure_f1_committed`, `fidelity_closure_f1_full`.
  - Added deprecation comment on the existing `fidelity_closure_f1` column (identical to `fidelity_closure_f1_full`; kept for backward compatibility).
  - Updated `_narrative_report()`: added coverage caveat interpretation bullet; added `closure_coverage` and `fidelity_closure_f1_full` to the top-line table.

**Files created:**

- `tests/test_closure_coverage.py` — 8 unit tests covering coverage=0 edge case, committed F1 perfect/zero, full F1 relationship to committed F1.

---

## Task 2: Intrinsic Axis Correlation Analysis

**Problem addressed:** `verifier_valid` and `trace_grounded` are presented as independent axes, but near-identical accuracy (~45% on TempEval) suggests collinearity. No correlation analysis existed.

**Files created:**

- `src/analysis/__init__.py` — package marker.
- `src/analysis/axis_correlation.py`
  - `extract_flags()`: extracts binary flags (parse_success, verifier_valid, trace_grounded) from predictions + failures.
  - `compute_axis_correlation()`: pairwise Pearson and phi matrices; agreement counts.
  - `axis_correlation_prose()`: factually neutral prose summary; flags collinear pairs (|ρ| > 0.90).
  - `save_axis_correlation_csv()`: writes pairwise stats to CSV.
  - `plot_axis_correlation()`: matplotlib heatmap PNG of Pearson matrix.
- `tests/test_axis_correlation.py` — 13 unit tests covering fully correlated, anti-correlated, constant (NaN), extract_flags, and prose.

**Files modified:**

- `src/run_summary.py`
  - Imports axis_correlation module.
  - In `summarise_runs()`: per-run generation of `axis_correlation_{model}.csv` and `axis_correlation_{model}.png`.
  - Updated `_narrative_report()` signature to accept `correlation_prose_blocks`; adds "Axis Correlation" section when blocks are non-empty.

---

## Task 3: Dissertation Prose Tightening

### Task 3a — `src/run_summary.py` narrative changes

**Problem addressed:** parse_success_rate and transport_failure_rate were mixed into the top-line reasoning table. Intrinsic validity was not explicitly framed as necessary-but-not-sufficient. No coverage caveat appeared next to closure F1. Gemma's contradiction paradox was not called out.

**Files modified:**

- `src/run_summary.py` (`_narrative_report()`)
  - Added "Pipeline Diagnostics" section (separate table: model_label, parse_success_rate, transport_failure_rate) before the top-line reasoning table.
  - Top-line table now contains reasoning metrics only: conditional_validity_rate, validity_expectation_alignment_rate_e2e, conditional_trace_grounding_rate, fidelity_direct_f1, fidelity_closure_f1_full, fidelity_closure_gap, closure_coverage, fidelity_closure_f1_committed.
  - Rewrote interpretation bullets: "Intrinsic validity is a necessary-but-not-sufficient signal..."
  - Added Gemma-paradox callout: when any model has conditional_validity_rate ≥ 0.99 and contradiction_detection_rate == 0.0 in a contradiction-containing dataset, a named blockquote note is emitted.
  - Added `num_tasks` to the category breakdown table columns so n < 30 cells are visible.

### Task 3b — Static docs and new files

**Files modified:**

- `docs/evaluation_design.md`
  - Added "Supported LTL Fragment" subsection: precise predicate list (confirmed from `src/trace.py`), operator list (G/F/X/U + booleans), explicit "not supported" list.
  - Added "Verifier Calibration" subsection: honest statement that the verifier has not been evaluated against external gold annotations.

- `docs/literature_alignment.md`
  - Renamed "Full formal verification" section to "Graph-grounded LTL fragment (not full formal verification)" to remove overstated claim.
  - Added "Explicitly Scoped-Out Work" section: verifier calibration, RQ3, TORQUE-style benchmarks. All framed as scoped-out, not failures.

**Files created:**

- `docs/threats_to_validity.md` — six-section threats document:
  - Construct validity: metrics operationalise graph-level properties, not cognitive reasoning.
  - Internal validity: verifier not calibrated; Qwen transport failure confound.
  - External validity: 7B–12B model range; TempEval single domain; author-constructed synthetic.
  - Statistical validity: per-cell n often < 30; no significance tests; single run per model.
  - Formal-methods scope: G/F/X/U fragment; not general LTL.
  - Dataset validity: synthetic experimenter bias; TempEval IAA caveat on SIMULTANEOUS/UNKNOWN (TODO: verify IAA rate from TempEval paper).

---

## Task 4: RQ3 Scoping

**Problem addressed:** RQ3 (confidence–verification correlation) was implicitly present in the literature alignment but not explicitly marked as unaddressed at interim.

**Files modified:**

- `docs/limitations.md`
  - Added explicit RQ3 deferral note with pointer to `docs/rq3_future_work.md`.

- `docs/literature_alignment.md` (also modified in Task 3b)
  - Added "Explicitly Scoped-Out Work" section covering RQ3.

**Files created:**

- `docs/rq3_future_work.md` — concrete plan covering:
  - Required changes to `OllamaClient` for logprob capture.
  - Three confidence signal options (token entropy, sequence logprob, self-reported) with cost/quality trade-offs.
  - Spearman ρ correlation analysis design with permutation test.
  - Estimated engineering cost (~9 hours + lab rerun).
  - Open questions on logprob availability and self-reported confidence calibration.

---

## Task 5: Smoke Test and Regeneration

- All 132 tests pass after changes.
- Regenerated `outputs/analysis/tempeval_full/`: summary.csv, report.md, category_breakdown.csv, failure_breakdown.csv, all plots, 5× axis_correlation_{model}.csv, 5× axis_correlation_{model}.png.
- Regenerated `outputs/analysis/canonical_full/`: same set of files. Gemma 3 12B paradox note appears in canonical report.md (conditional_validity_rate=1.0 + contradiction_detection_rate=0.0).

---

## Bugs Observed but Not Fixed

- `src/run_summary.py`: The `_has_non_null_metric` and `_has_meaningful_rate` helpers are defined but appear unused in the current code (likely vestigial from an earlier conditional plot filter). No behaviour is broken; not fixed to avoid expanding scope.
