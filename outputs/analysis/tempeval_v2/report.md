# Temporal Verification Evaluation Summary

- Runs analysed: `5`
- Highest parse success: `Llama 3.1 8B` at `1.000`
- Highest fidelity closure F1: `Qwen 3.5 9B` at `0.855`
- Highest validity-expectation alignment: `Gemma 3 12B` at `0.998`
- Largest fidelity closure-direct gap: `Gemma 3 12B` at `0.060`

## Interpretation

- Intrinsic graph validity and trace grounding, exact direct-edge fidelity, closure-level reasoning, ambiguity discipline, and contradiction detection should be read as separate capabilities.
- `validity_expectation_alignment_rate_e2e` checks whether the verifier outcome matches the task intent end-to-end, so clean-but-wrong contradiction abstention does not look deceptively strong.
- Intrinsic validity is a necessary-but-not-sufficient signal: no intrinsically invalid prediction was also label-correct, but intrinsically valid predictions still achieve only partial label accuracy. Both conditions must be checked.
- `fidelity_direct_f1` and `fidelity_closure_f1` are computed on gold-bearing tasks only, excluding empty-gold ambiguity items from the fidelity headline.
- Closure scoring only covers ordering-bearing relations. On datasets with many `SIMULTANEOUS` labels, closure F1 should be interpreted alongside direct F1 rather than in isolation.
- Closure F1 is reported in two forms: `fidelity_closure_f1_full` (headline — treats uncommitted pairs as false negatives) and `fidelity_closure_f1_committed` (conditional on commitment only). Read `closure_coverage` alongside both.
- Direct-vs-closure gaps indicate when a model recovers the implied temporal ordering while still missing the intended explicit representation.
- This dataset does not contain ambiguity or contradiction control slices, so consistency-specific plots are intentionally omitted.

## Pipeline Diagnostics

Parse robustness and transport stability are infrastructure signals, not reasoning quality indicators. They are separated here to avoid conflation with the reasoning metrics in the top-line table.

| model_label | parse_success_rate | transport_failure_rate |
| --- | --- | --- |
| DeepSeek R1 7B | 0.8024193548387096 | 0.0 |
| Qwen 3.5 9B | 0.8407258064516129 | 0.008064516129032258 |
| Llama 3.1 8B | 1.0 | 0.0 |
| Mistral 7B | 1.0 | 0.0 |
| Gemma 3 12B | 1.0 | 0.0 |

- This run set evaluates a single task family: `tempeval_relation`. Category-wise plots should be read as dataset-wide summaries rather than cross-category diagnostics.

## Top-line Table

| model_label | conditional_validity_rate | validity_expectation_alignment_rate_e2e | conditional_trace_grounding_rate | fidelity_direct_f1 | fidelity_closure_f1_full | fidelity_closure_gap | closure_coverage | fidelity_closure_f1_committed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | 0.8592964824120602 | 0.6895161290322581 | 0.864321608040201 | 0.4623115577889447 | 0.49709302325581395 | 0.03478146546686922 | 0.9506172839506173 | 0.5551948051948052 |
| Qwen 3.5 9B | 0.9712230215827338 | 0.8165322580645161 | 0.9976019184652278 | 0.8009592326139089 | 0.8549618320610687 | 0.054002599447159794 | 0.8865671641791045 | 0.9427609427609428 |
| Llama 3.1 8B | 0.9919354838709677 | 0.9919354838709677 | 0.9919354838709677 | 0.3608870967741936 | 0.3800695249130938 | 0.0191824281389002 | 0.964824120603015 | 0.4270833333333333 |
| Mistral 7B | 0.8004032258064516 | 0.8004032258064516 | 0.9818548387096774 | 0.4399141630901288 | 0.4817518248175182 | 0.0418376617273894 | 0.871859296482412 | 0.5706051873198847 |
| Gemma 3 12B | 0.9979838709677419 | 0.9979838709677419 | 0.9979838709677419 | 0.5467479674796748 | 0.6072234762979684 | 0.060475508818293555 | 0.9874371859296482 | 0.6844783715012722 |

## LTL Layer

`ltl_genuine_violation_rate` counts task-specific trace formulas that are not reducible to the invariant layer: unsupported final commitments checked with `F(supports(...))`, and mid-trace inversions checked with nested `G` over step supports.

`ltl_invariant_corroboration_rate` counts the three static formulas that mirror invariant failures (`ltl_contradiction`, `ltl_temporal_inconsistency`, `ltl_hallucinated_node`). These are useful for trace localisation but should be reported separately from genuine trace-level signal.

| model_label | ltl_genuine_violation_rate | ltl_invariant_corroboration_rate |
| --- | --- | --- |
| DeepSeek R1 7B | 0.08793969849246232 | 0.05527638190954774 |
| Qwen 3.5 9B | 0.02877697841726619 | 0.0 |
| Llama 3.1 8B | 0.0 | 0.008064516129032258 |
| Mistral 7B | 0.1875 | 0.012096774193548387 |
| Gemma 3 12B | 0.0 | 0.0020161290322580645 |

## Category Notes

| model_label | category | num_tasks | parse_success_rate | validity_expectation_alignment_rate_e2e | trace_grounding_rate | direct_f1 | closure_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | tempeval_relation | 496 | 0.8024193548387096 | 0.6895161290322581 | 0.864321608040201 | 0.4623115577889447 | 0.49709302325581395 |
| Qwen 3.5 9B | tempeval_relation | 496 | 0.8407258064516129 | 0.8165322580645161 | 0.9976019184652278 | 0.8009592326139089 | 0.8549618320610687 |
| Llama 3.1 8B | tempeval_relation | 496 | 1.0 | 0.9919354838709677 | 0.9919354838709677 | 0.3608870967741936 | 0.3800695249130938 |
| Mistral 7B | tempeval_relation | 496 | 1.0 | 0.8004032258064516 | 0.9818548387096774 | 0.4399141630901288 | 0.4817518248175182 |
| Gemma 3 12B | tempeval_relation | 496 | 1.0 | 0.9979838709677419 | 0.9979838709677419 | 0.5467479674796748 | 0.6072234762979684 |

## Plot Reading Guide

- `parse_success_rate.png`: pipeline robustness, not reasoning quality.
- `transport_failure_rate.png`: infrastructure instability, not model behaviour.
- `conditional_trace_grounding_rate.png`: whether reasoning annotations align with the final answer structure.
- `validity_expectation_alignment_rate.png`: whether valid versus invalid outputs match task expectations end-to-end.
- `direct_vs_closure_f1.png`: representation fidelity versus ordering recovery on gold-bearing tasks only.
- `verification_task_incidence.png`: task-level prevalence of invariant failure modes.
- `ltl_task_incidence.png`: task-level prevalence of all LTL formula failures.
- `genuine_ltl_incidence.png`: separates genuine trace-level LTL signal from invariant-corroborating LTL.

## Axis Correlation

Pairwise Pearson / phi correlations across intrinsic axes (parse_success, verifier_valid, trace_grounded). High correlation indicates the axes provide largely redundant signal; low correlation indicates they measure distinct things.

**DeepSeek R1 7B**: Collinear axis pairs (|ρ| > 0.90): `verifier_valid`–`trace_grounded` (ρ = 0.99). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.99 (n = 496). Weakest pairwise correlation: `parse_success`–`verifier_valid` at ρ = 0.74.
**Qwen 3.5 9B**: Collinear axis pairs (|ρ| > 0.90): `parse_success`–`trace_grounded` (ρ = 0.99), `parse_success`–`verifier_valid` (ρ = 0.92), `verifier_valid`–`trace_grounded` (ρ = 0.91). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `parse_success`–`trace_grounded` at ρ = 0.99 (n = 496). Weakest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.91.
**Llama 3.1 8B**: Collinear axis pairs (|ρ| > 0.90): `verifier_valid`–`trace_grounded` (ρ = 1.00). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00 (n = 496). Weakest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00.
**Mistral 7B**: Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.27 (n = 496). Weakest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.27.
**Gemma 3 12B**: Collinear axis pairs (|ρ| > 0.90): `verifier_valid`–`trace_grounded` (ρ = 1.00). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00 (n = 496). Weakest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00.

See `axis_correlation_*.csv` and `axis_correlation_*.png` for full matrices.
