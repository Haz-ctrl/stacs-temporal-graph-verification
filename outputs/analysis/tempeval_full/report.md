# Temporal Verification Evaluation Summary

- Runs analysed: `5`
- Highest parse success: `Llama 3.1 8B` at `1.000`
- Highest fidelity closure F1: `Gemma 3 12B` at `0.602`
- Highest validity-expectation alignment: `Gemma 3 12B` at `0.998`
- Largest fidelity closure-direct gap: `Gemma 3 12B` at `0.252`

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
| DeepSeek R1 7B | 0.48267898383371827 | 0.4213709677419355 | 0.45958429561200925 | 0.20138888888888892 | 0.22857142857142856 | 0.02718253968253964 | 0.9335260115606936 | 0.26006191950464397 |
| Qwen 3.5 9B | 0.5355329949238579 | 0.4254032258064516 | 0.5355329949238579 | 0.31218274111675126 | 0.3968 | 0.08461725888324872 | 0.8927444794952681 | 0.4381625441696113 |
| Llama 3.1 8B | 0.8165322580645161 | 0.8165322580645161 | 0.8165322580645161 | 0.2600806451612903 | 0.30500582072176946 | 0.04492517556047915 | 0.9597989949748744 | 0.34293193717277487 |
| Mistral 7B | 0.8646464646464647 | 0.8629032258064516 | 0.8949494949494949 | 0.2287655719139298 | 0.40414507772020725 | 0.17537950580627745 | 0.783375314861461 | 0.5016077170418006 |
| Gemma 3 12B | 0.9979838709677419 | 0.9979838709677419 | 0.9979838709677419 | 0.35066258919469934 | 0.6024915062287657 | 0.25182891703406635 | 0.9824120603015075 | 0.680306905370844 |

## Category Notes

| model_label | category | num_tasks | parse_success_rate | validity_expectation_alignment_rate_e2e | trace_grounding_rate | direct_f1 | closure_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | tempeval_relation | 496 | 0.8729838709677419 | 0.4213709677419355 | 0.45958429561200925 | 0.20138888888888892 | 0.22857142857142856 |
| Qwen 3.5 9B | tempeval_relation | 496 | 0.7943548387096774 | 0.4254032258064516 | 0.5355329949238579 | 0.31218274111675126 | 0.3968 |
| Llama 3.1 8B | tempeval_relation | 496 | 1.0 | 0.8165322580645161 | 0.8165322580645161 | 0.2600806451612903 | 0.30500582072176946 |
| Mistral 7B | tempeval_relation | 496 | 0.9979838709677419 | 0.8629032258064516 | 0.8949494949494949 | 0.2287655719139298 | 0.40414507772020725 |
| Gemma 3 12B | tempeval_relation | 496 | 1.0 | 0.9979838709677419 | 0.9979838709677419 | 0.35066258919469934 | 0.6024915062287657 |

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

**DeepSeek R1 7B**: Collinear axis pairs (|ρ| > 0.90): `verifier_valid`–`trace_grounded` (ρ = 0.96). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.96 (n = 496). Weakest pairwise correlation: `parse_success`–`trace_grounded` at ρ = 0.31.
**Qwen 3.5 9B**: Collinear axis pairs (|ρ| > 0.90): `verifier_valid`–`trace_grounded` (ρ = 1.00). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00 (n = 496). Weakest pairwise correlation: `parse_success`–`trace_grounded` at ρ = 0.44.
**Llama 3.1 8B**: Collinear axis pairs (|ρ| > 0.90): `verifier_valid`–`trace_grounded` (ρ = 1.00). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00 (n = 496). Weakest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00.
**Mistral 7B**: Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.85 (n = 496). Weakest pairwise correlation: `parse_success`–`verifier_valid` at ρ = 0.11.
**Gemma 3 12B**: Collinear axis pairs (|ρ| > 0.90): `verifier_valid`–`trace_grounded` (ρ = 1.00). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00 (n = 496). Weakest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 1.00.

See `axis_correlation_*.csv` and `axis_correlation_*.png` for full matrices.
