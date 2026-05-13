# Temporal Verification Evaluation Summary

- Runs analysed: `5`
- Highest parse success: `Gemma 3 12B` at `1.000`
- Highest fidelity closure F1: `Qwen 3.5 9B` at `0.822`
- Highest validity-expectation alignment: `Gemma 3 12B` at `1.000`
- Largest fidelity closure-direct gap: `Mistral 7B` at `0.100`

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
| DeepSeek R1 7B | 0.936 | 0.012 |
| Qwen 3.5 9B | 0.742 | 0.13 |
| Llama 3.1 8B | 0.998 | 0.0 |
| Mistral 7B | 0.998 | 0.0 |
| Gemma 3 12B | 1.0 | 0.0 |

- This run set evaluates a single task family: `maven_ere_temporal`. Category-wise plots should be read as dataset-wide summaries rather than cross-category diagnostics.
- `Qwen 3.5 9B` has a transport failure rate of `0.130`. Comparative claims for that run should be treated as infrastructure-confounded until rerun with stronger retry settings.

## Top-line Table

| model_label | conditional_validity_rate | validity_expectation_alignment_rate_e2e | conditional_trace_grounding_rate | fidelity_direct_f1 | fidelity_closure_f1_full | fidelity_closure_gap | closure_coverage | fidelity_closure_f1_committed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | 0.9658119658119658 | 0.904 | 0.9658119658119658 | 0.44919786096256686 | 0.49375866851595 | 0.04456080755338315 | 0.9053627760252366 | 0.6202090592334495 |
| Qwen 3.5 9B | 0.9838274932614556 | 0.73 | 1.0 | 0.796221322537112 | 0.8223552894211577 | 0.02613396688404568 | 0.8745098039215686 | 0.9237668161434976 |
| Llama 3.1 8B | 0.9979959919839679 | 0.996 | 0.9979959919839679 | 0.3350050150451354 | 0.3794037940379404 | 0.04439877899280498 | 0.8765060240963856 | 0.48109965635738833 |
| Mistral 7B | 0.4228456913827655 | 0.422 | 0.9859719438877755 | 0.5166846071044133 | 0.6170212765957448 | 0.10033666949133146 | 0.8614457831325302 | 0.8111888111888111 |
| Gemma 3 12B | 1.0 | 1.0 | 1.0 | 0.5476923076923077 | 0.6414141414141414 | 0.09372183372183374 | 0.9669669669669669 | 0.7888198757763976 |

## LTL Layer

`ltl_genuine_violation_rate` counts task-specific trace formulas that are not reducible to the invariant layer: unsupported final commitments checked with `F(supports(...))`, and mid-trace inversions checked with nested `G` over step supports.

`ltl_invariant_corroboration_rate` counts the three static formulas that mirror invariant failures (`ltl_contradiction`, `ltl_temporal_inconsistency`, `ltl_hallucinated_node`). These are useful for trace localisation but should be reported separately from genuine trace-level signal.

| model_label | ltl_genuine_violation_rate | ltl_invariant_corroboration_rate |
| --- | --- | --- |
| DeepSeek R1 7B | 0.008547008547008548 | 0.02564102564102564 |
| Qwen 3.5 9B | 0.016172506738544475 | 0.0 |
| Llama 3.1 8B | 0.0 | 0.002004008016032064 |
| Mistral 7B | 0.5751503006012024 | 0.01002004008016032 |
| Gemma 3 12B | 0.0 | 0.0 |

## Category Notes

| model_label | category | num_tasks | parse_success_rate | validity_expectation_alignment_rate_e2e | trace_grounding_rate | direct_f1 | closure_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | maven_ere_temporal | 500 | 0.936 | 0.904 | 0.9658119658119658 | 0.44919786096256686 | 0.49375866851595 |
| Qwen 3.5 9B | maven_ere_temporal | 500 | 0.742 | 0.73 | 1.0 | 0.796221322537112 | 0.8223552894211577 |
| Llama 3.1 8B | maven_ere_temporal | 500 | 0.998 | 0.996 | 0.9979959919839679 | 0.3350050150451354 | 0.3794037940379404 |
| Mistral 7B | maven_ere_temporal | 500 | 0.998 | 0.422 | 0.9859719438877755 | 0.5166846071044133 | 0.6170212765957448 |
| Gemma 3 12B | maven_ere_temporal | 500 | 1.0 | 1.0 | 1.0 | 0.5476923076923077 | 0.6414141414141414 |

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

**DeepSeek R1 7B**: Collinear axis pairs (|ρ| > 0.90): `verifier_valid`–`trace_grounded` (ρ = 1.00). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00 (n = 500). Weakest pairwise correlation: `parse_success`–`trace_grounded` at ρ = 0.80.
**Qwen 3.5 9B**: Collinear axis pairs (|ρ| > 0.90): `parse_success`–`trace_grounded` (ρ = 1.00), `verifier_valid`–`trace_grounded` (ρ = 0.97), `parse_success`–`verifier_valid` (ρ = 0.97). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `parse_success`–`trace_grounded` at ρ = 1.00 (n = 500). Weakest pairwise correlation: `parse_success`–`verifier_valid` at ρ = 0.97.
**Llama 3.1 8B**: Collinear axis pairs (|ρ| > 0.90): `verifier_valid`–`trace_grounded` (ρ = 1.00). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00 (n = 500). Weakest pairwise correlation: `parse_success`–`trace_grounded` at ρ = 0.71.
**Mistral 7B**: Strongest pairwise correlation: `parse_success`–`trace_grounded` at ρ = 0.35 (n = 500). Weakest pairwise correlation: `parse_success`–`verifier_valid` at ρ = 0.04.

See `axis_correlation_*.csv` and `axis_correlation_*.png` for full matrices.
