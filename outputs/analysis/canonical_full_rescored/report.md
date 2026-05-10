# Temporal Verification Evaluation Summary

- Runs analysed: `5`
- Highest parse success: `Llama 3.1 8B` at `1.000`
- Highest fidelity closure F1: `Qwen 3.5 9B` at `0.952`
- Highest validity-expectation alignment: `Llama 3.1 8B` at `0.980`
- Best ambiguity abstention: `Gemma 3 12B` at `0.733`
- Best contradiction detection: `Llama 3.1 8B` at `0.900`
- Largest fidelity closure-direct gap: `DeepSeek R1 7B` at `0.147`

## Interpretation

- Intrinsic graph validity and trace grounding, exact direct-edge fidelity, closure-level reasoning, ambiguity discipline, and contradiction detection should be read as separate capabilities.
- `validity_expectation_alignment_rate_e2e` checks whether the verifier outcome matches the task intent end-to-end, so clean-but-wrong contradiction abstention does not look deceptively strong.
- Intrinsic validity is a necessary-but-not-sufficient signal: no intrinsically invalid prediction was also label-correct, but intrinsically valid predictions still achieve only partial label accuracy. Both conditions must be checked.
- `fidelity_direct_f1` and `fidelity_closure_f1` are computed on gold-bearing tasks only, excluding empty-gold ambiguity items from the fidelity headline.
- Closure scoring only covers ordering-bearing relations. On datasets with many `SIMULTANEOUS` labels, closure F1 should be interpreted alongside direct F1 rather than in isolation.
- Closure F1 is reported in two forms: `fidelity_closure_f1_full` (headline — treats uncommitted pairs as false negatives) and `fidelity_closure_f1_committed` (conditional on commitment only). Read `closure_coverage` alongside both.
- Direct-vs-closure gaps indicate when a model recovers the implied temporal ordering while still missing the intended explicit representation.
- Ambiguous and contradiction categories are consistency-oriented slices. They should not be interpreted through raw F1 alone.

## Pipeline Diagnostics

Parse robustness and transport stability are infrastructure signals, not reasoning quality indicators. They are separated here to avoid conflation with the reasoning metrics in the top-line table.

| model_label | parse_success_rate | transport_failure_rate |
| --- | --- | --- |
| DeepSeek R1 7B | 0.7733333333333333 | 0.006666666666666667 |
| Qwen 3.5 9B | 0.9333333333333333 | 0.06666666666666667 |
| Llama 3.1 8B | 1.0 | 0.0 |
| Mistral 7B | 0.9666666666666667 | 0.0 |
| Gemma 3 12B | 1.0 | 0.0 |
- `Qwen 3.5 9B` has a transport failure rate of `0.067`. Comparative claims for that run should be treated as infrastructure-confounded until rerun with stronger retry settings.

## Top-line Table

| model_label | conditional_validity_rate | validity_expectation_alignment_rate_e2e | conditional_trace_grounding_rate | fidelity_direct_f1 | fidelity_closure_f1_full | fidelity_closure_gap | closure_coverage | fidelity_closure_f1_committed | ambiguity_overcommitment_rate | contradiction_detection_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | 0.9741379310344828 | 0.6733333333333333 | 0.9396551724137931 | 0.6518218623481782 | 0.7991169977924946 | 0.14729513544431638 | 1.0 | 0.7991169977924946 | 0.88 | 0.125 |
| Qwen 3.5 9B | 0.9 | 0.9 | 0.9571428571428572 | 0.8081123244929797 | 0.9521322889469104 | 0.14401996445393073 | 1.0 | 0.9521322889469104 | 0.6538461538461539 | 0.7368421052631579 |
| Llama 3.1 8B | 0.8733333333333333 | 0.98 | 0.96 | 0.5798816568047337 | 0.7062706270627063 | 0.12638897025797258 | 0.99 | 0.7187237615449201 | 1.0 | 0.9 |
| Mistral 7B | 0.8758620689655172 | 0.9266666666666666 | 0.7793103448275862 | 0.3813084112149533 | 0.39540229885057465 | 0.01409388763562136 | 1.0 | 0.39540229885057465 | 1.0 | 0.8 |
| Gemma 3 12B | 1.0 | 0.8666666666666667 | 1.0 | 0.6512345679012346 | 0.768729641693811 | 0.1174950737925764 | 1.0 | 0.768729641693811 | 0.26666666666666666 | 0.0 |

> **Note (Gemma 3 12B)**: `conditional_validity_rate ≈ 1.0` and `contradiction_detection_rate = 0.0`. A model that abstains universally on contradiction items looks clean under intrinsic checks but fails the task. This demonstrates why intrinsic-only scoring is insufficient — both intrinsic validity and task correctness must be evaluated together.

## Category Notes

| model_label | category | num_tasks | parse_success_rate | validity_expectation_alignment_rate_e2e | trace_grounding_rate | direct_f1 | closure_f1 | abstention_rate | overcommitment_rate | contradiction_detection_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | ambiguous | 30 | 0.8333333333333334 | 0.8333333333333334 | 1.0 | NA | NA | 0.12 | 0.88 | 0.0 |
| DeepSeek R1 7B | contradiction | 20 | 0.8 | 0.1 | 0.875 | NA | NA | 0.1875 | 0.0 | 0.125 |
| DeepSeek R1 7B | linear_chain | 40 | 0.725 | 0.7 | 0.9310344827586207 | 0.5954198473282443 | 0.676056338028169 | 0.0 | 0.0 | 0.0 |
| DeepSeek R1 7B | transitive_reasoning | 40 | 0.825 | 0.825 | 1.0 | 0.7088607594936709 | 1.0 | 0.0 | 0.0 | 0.0 |
| Qwen 3.5 9B | ambiguous | 30 | 0.8666666666666667 | 0.8666666666666667 | 1.0 | NA | NA | 0.34615384615384615 | 0.6538461538461539 | 0.0 |
| Qwen 3.5 9B | contradiction | 20 | 0.95 | 0.7 | 0.6842105263157895 | NA | NA | 0.10526315789473684 | 0.0 | 0.7368421052631579 |
| Qwen 3.5 9B | linear_chain | 40 | 1.0 | 1.0 | 1.0 | 0.6847826086956521 | 0.8083623693379791 | 0.0 | 0.0 | 0.0 |
| Qwen 3.5 9B | transitive_reasoning | 40 | 0.975 | 0.975 | 1.0 | 0.7796610169491525 | 1.0 | 0.0 | 0.0 | 0.0 |
| Llama 3.1 8B | ambiguous | 30 | 1.0 | 1.0 | 1.0 | NA | NA | 0.0 | 1.0 | 0.0 |
| Llama 3.1 8B | contradiction | 20 | 1.0 | 0.9 | 1.0 | NA | NA | 0.0 | 0.0 | 0.9 |
| Llama 3.1 8B | linear_chain | 40 | 1.0 | 1.0 | 0.875 | 0.2967032967032967 | 0.3109540636042402 | 0.0 | 0.0 | 0.0 |
| Llama 3.1 8B | transitive_reasoning | 40 | 1.0 | 1.0 | 1.0 | 0.7083333333333333 | 1.0 | 0.0 | 0.0 | 0.0 |
| Mistral 7B | ambiguous | 30 | 0.9333333333333333 | 0.9 | 0.8928571428571429 | NA | NA | 0.0 | 1.0 | 0.03571428571428571 |
| Mistral 7B | contradiction | 20 | 1.0 | 0.8 | 0.75 | NA | NA | 0.0 | 0.0 | 0.8 |
| Mistral 7B | linear_chain | 40 | 0.95 | 0.925 | 0.868421052631579 | 0.29333333333333333 | 0.3571428571428572 | 0.0 | 0.0 | 0.02631578947368421 |
| Mistral 7B | transitive_reasoning | 40 | 1.0 | 1.0 | 0.55 | 0.5369649805447471 | 0.7210884353741497 | 0.0 | 0.0 | 0.0 |
| Gemma 3 12B | ambiguous | 30 | 1.0 | 1.0 | 1.0 | NA | NA | 0.7333333333333333 | 0.26666666666666666 | 0.0 |
| Gemma 3 12B | contradiction | 20 | 1.0 | 0.0 | 1.0 | NA | NA | 1.0 | 0.0 | 0.0 |
| Gemma 3 12B | linear_chain | 40 | 1.0 | 1.0 | 1.0 | 0.5 | 0.5896414342629482 | 0.0 | 0.0 | 0.0 |
| Gemma 3 12B | transitive_reasoning | 40 | 1.0 | 1.0 | 1.0 | 0.7083333333333333 | 1.0 | 0.0 | 0.0 | 0.0 |

## Plot Reading Guide

- `parse_success_rate.png`: pipeline robustness, not reasoning quality.
- `transport_failure_rate.png`: infrastructure instability, not model behaviour.
- `conditional_trace_grounding_rate.png`: whether reasoning annotations align with the final answer structure.
- `validity_expectation_alignment_rate.png`: whether valid versus invalid outputs match task expectations end-to-end.
- `direct_vs_closure_f1.png`: representation fidelity versus ordering recovery on gold-bearing tasks only.
- `ambiguity_behaviour.png`: abstention discipline versus overcommitment.
- `contradiction_detection_rate.png`: conditional consistency-focused performance on parsed contradiction tasks.
- `verification_task_incidence.png`: task-level prevalence of invariant failure modes.
- `ltl_task_incidence.png`: trace-level corroboration of structural failures; do not read this as independent evidence from the invariant layer.

## Axis Correlation

Pairwise Pearson / phi correlations across intrinsic axes (parse_success, verifier_valid, trace_grounded). High correlation indicates the axes provide largely redundant signal; low correlation indicates they measure distinct things.

**DeepSeek R1 7B**: Collinear axis pairs (|ρ| > 0.90): `parse_success`–`verifier_valid` (ρ = 0.95). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `parse_success`–`verifier_valid` at ρ = 0.95 (n = 150). Weakest pairwise correlation: `parse_success`–`trace_grounded` at ρ = 0.88.
**Qwen 3.5 9B**: Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.79 (n = 150). Weakest pairwise correlation: `parse_success`–`verifier_valid` at ρ = 0.61.
**Llama 3.1 8B**: Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = -0.08 (n = 150). Weakest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = -0.08.
**Mistral 7B**: Strongest pairwise correlation: `parse_success`–`verifier_valid` at ρ = 0.44 (n = 150). Weakest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.14.

See `axis_correlation_*.csv` and `axis_correlation_*.png` for full matrices.
