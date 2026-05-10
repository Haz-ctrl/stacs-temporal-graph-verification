# Temporal Verification Evaluation Summary

- Runs analysed: `5`
- Highest parse success: `Llama 3.1 8B` at `1.000`
- Highest fidelity closure F1: `Qwen 3.5 9B` at `0.835`
- Highest validity-expectation alignment: `Gemma 3 12B` at `1.000`
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
| DeepSeek R1 7B | 0.8729838709677419 | 0.020161290322580645 |
| Qwen 3.5 9B | 0.7943548387096774 | 0.18951612903225806 |
| Llama 3.1 8B | 1.0 | 0.0 |
| Mistral 7B | 0.9979838709677419 | 0.0 |
| Gemma 3 12B | 1.0 | 0.0 |

- This run set evaluates a single task family: `tempeval_relation`. Category-wise plots should be read as dataset-wide summaries rather than cross-category diagnostics.
- `Qwen 3.5 9B` has a transport failure rate of `0.190`. Comparative claims for that run should be treated as infrastructure-confounded until rerun with stronger retry settings.

## Top-line Table

| model_label | conditional_validity_rate | validity_expectation_alignment_rate_e2e | conditional_trace_grounding_rate | fidelity_direct_f1 | fidelity_closure_f1_full | fidelity_closure_gap | closure_coverage | fidelity_closure_f1_committed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | 0.9515011547344111 | 0.8306451612903226 | 0.8983833718244804 | 0.4351851851851851 | 0.4707482993197279 | 0.03556311413454277 | 0.9335260115606936 | 0.5356037151702786 |
| Qwen 3.5 9B | 1.0 | 0.7943548387096774 | 1.0 | 0.7928843710292249 | 0.8352 | 0.04231562897077512 | 0.8927444794952681 | 0.9222614840989399 |
| Llama 3.1 8B | 0.9939516129032258 | 0.9939516129032258 | 0.9939516129032258 | 0.3689516129032258 | 0.3888242142025611 | 0.01987260129933527 | 0.9597989949748744 | 0.43717277486910994 |
| Mistral 7B | 0.9555555555555556 | 0.9536290322580645 | 0.9616161616161616 | 0.40996602491506234 | 0.45077720207253885 | 0.04081117715747651 | 0.783375314861461 | 0.5594855305466238 |
| Gemma 3 12B | 1.0 | 1.0 | 1.0 | 0.5443425076452599 | 0.6047565118912798 | 0.06041400424601984 | 0.9824120603015075 | 0.6828644501278772 |

## Category Notes

| model_label | category | num_tasks | parse_success_rate | validity_expectation_alignment_rate_e2e | trace_grounding_rate | direct_f1 | closure_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | tempeval_relation | 496 | 0.8729838709677419 | 0.8306451612903226 | 0.8983833718244804 | 0.4351851851851851 | 0.4707482993197279 |
| Qwen 3.5 9B | tempeval_relation | 496 | 0.7943548387096774 | 0.7943548387096774 | 1.0 | 0.7928843710292249 | 0.8352 |
| Llama 3.1 8B | tempeval_relation | 496 | 1.0 | 0.9939516129032258 | 0.9939516129032258 | 0.3689516129032258 | 0.3888242142025611 |
| Mistral 7B | tempeval_relation | 496 | 0.9979838709677419 | 0.9536290322580645 | 0.9616161616161616 | 0.40996602491506234 | 0.45077720207253885 |
| Gemma 3 12B | tempeval_relation | 496 | 1.0 | 1.0 | 1.0 | 0.5443425076452599 | 0.6047565118912798 |

## Plot Reading Guide

- `parse_success_rate.png`: pipeline robustness, not reasoning quality.
- `transport_failure_rate.png`: infrastructure instability, not model behaviour.
- `conditional_trace_grounding_rate.png`: whether reasoning annotations align with the final answer structure.
- `validity_expectation_alignment_rate.png`: whether valid versus invalid outputs match task expectations end-to-end.
- `direct_vs_closure_f1.png`: representation fidelity versus ordering recovery on gold-bearing tasks only.
- `verification_task_incidence.png`: task-level prevalence of invariant failure modes.
- `ltl_task_incidence.png`: trace-level corroboration of structural failures; do not read this as independent evidence from the invariant layer.

## Axis Correlation

Pairwise Pearson / phi correlations across intrinsic axes (parse_success, verifier_valid, trace_grounded). High correlation indicates the axes provide largely redundant signal; low correlation indicates they measure distinct things.

**DeepSeek R1 7B**: Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.86 (n = 496). Weakest pairwise correlation: `parse_success`–`trace_grounded` at ρ = 0.73.
**Qwen 3.5 9B**: Collinear axis pairs (|ρ| > 0.90): `verifier_valid`–`trace_grounded` (ρ = 1.00), `parse_success`–`verifier_valid` (ρ = 1.00), `parse_success`–`trace_grounded` (ρ = 1.00). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00 (n = 496). Weakest pairwise correlation: `parse_success`–`trace_grounded` at ρ = 1.00.
**Llama 3.1 8B**: Collinear axis pairs (|ρ| > 0.90): `verifier_valid`–`trace_grounded` (ρ = 1.00). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00 (n = 496). Weakest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00.
**Mistral 7B**: Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.83 (n = 496). Weakest pairwise correlation: `parse_success`–`verifier_valid` at ρ = 0.20.

See `axis_correlation_*.csv` and `axis_correlation_*.png` for full matrices.
