# Temporal Verification Evaluation Summary

- Runs analysed: `5`
- Highest parse success: `Llama 3.1 8B` at `1.000`
- Highest fidelity closure F1: `Qwen 3.5 9B` at `0.952`
- Highest validity-expectation alignment: `Llama 3.1 8B` at `0.936`
- Best ambiguity abstention: `Gemma 3 12B` at `0.933`
- Best contradiction detection: `Llama 3.1 8B` at `0.980`
- Largest fidelity closure-direct gap: `DeepSeek R1 7B` at `0.152`

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
| DeepSeek R1 7B | 0.776 | 0.004 |
| Qwen 3.5 9B | 0.916 | 0.084 |
| Llama 3.1 8B | 1.0 | 0.0 |
| Mistral 7B | 0.98 | 0.0 |
| Gemma 3 12B | 1.0 | 0.0 |
- `Qwen 3.5 9B` has a transport failure rate of `0.084`. Comparative claims for that run should be treated as infrastructure-confounded until rerun with stronger retry settings.

## Top-line Table

| model_label | conditional_validity_rate | validity_expectation_alignment_rate_e2e | conditional_trace_grounding_rate | fidelity_direct_f1 | fidelity_closure_f1_full | fidelity_closure_gap | closure_coverage | fidelity_closure_f1_committed | ambiguity_overcommitment_rate | contradiction_detection_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | 0.9226804123711341 | 0.62 | 0.9432989690721649 | 0.687603305785124 | 0.8392701998262381 | 0.1516668940411141 | 1.0 | 0.8392701998262381 | 0.8076923076923077 | 0.2391304347826087 |
| Qwen 3.5 9B | 0.8122270742358079 | 0.88 | 0.9737991266375546 | 0.821556886227545 | 0.9521988527724666 | 0.13064196654492166 | 1.0 | 0.9521988527724666 | 0.82 | 0.8541666666666666 |
| Llama 3.1 8B | 0.744 | 0.936 | 0.944 | 0.6278538812785388 | 0.7273816656680645 | 0.0995277843895257 | 0.9928571428571429 | 0.7317661241711875 | 0.8333333333333334 | 0.98 |
| Mistral 7B | 0.6081632653061224 | 0.732 | 0.7591836734693878 | 0.3314447592067989 | 0.3007778738115817 | -0.03066688539521717 | 0.9926470588235294 | 0.3023457862728062 | 1.0 | 0.8 |
| Gemma 3 12B | 0.992 | 0.792 | 1.0 | 0.5796019900497512 | 0.6093432633716994 | 0.029741273321948203 | 1.0 | 0.6093432633716994 | 0.06666666666666667 | 0.0 |

## LTL Layer

`ltl_genuine_violation_rate` counts task-specific trace formulas that are not reducible to the invariant layer: unsupported final commitments checked with `F(supports(...))`, and mid-trace inversions checked with nested `G` over step supports.

`ltl_invariant_corroboration_rate` counts the three static formulas that mirror invariant failures (`ltl_contradiction`, `ltl_temporal_inconsistency`, `ltl_hallucinated_node`). These are useful for trace localisation but should be reported separately from genuine trace-level signal.

| model_label | ltl_genuine_violation_rate | ltl_invariant_corroboration_rate |
| --- | --- | --- |
| DeepSeek R1 7B | 0.03608247422680412 | 0.06701030927835051 |
| Qwen 3.5 9B | 0.18777292576419213 | 0.17903930131004367 |
| Llama 3.1 8B | 0.256 | 0.2 |
| Mistral 7B | 0.37142857142857144 | 0.2 |
| Gemma 3 12B | 0.008 | 0.0 |

> **Note (Gemma 3 12B)**: `conditional_validity_rate ≈ 1.0` and `contradiction_detection_rate = 0.0`. A model that abstains universally on contradiction items looks clean under intrinsic checks but fails the task. This demonstrates why intrinsic-only scoring is insufficient — both intrinsic validity and task correctness must be evaluated together.

## Category Notes

| model_label | category | num_tasks | parse_success_rate | validity_expectation_alignment_rate_e2e | trace_grounding_rate | direct_f1 | closure_f1 | abstention_rate | overcommitment_rate | contradiction_detection_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | ambiguous | 60 | 0.8666666666666667 | 0.8666666666666667 | 0.9615384615384616 | NA | NA | 0.19230769230769232 | 0.8076923076923077 | 0.0 |
| DeepSeek R1 7B | contradiction | 50 | 0.92 | 0.22 | 0.8695652173913043 | NA | NA | 0.06521739130434782 | 0.0 | 0.2391304347826087 |
| DeepSeek R1 7B | linear_chain | 60 | 0.6833333333333333 | 0.6333333333333333 | 0.9512195121951219 | 0.5106382978723404 | 0.7 | 0.0 | 0.0 | 0.0 |
| DeepSeek R1 7B | transitive_reasoning | 50 | 0.7 | 0.7 | 1.0 | 0.7354260089686099 | 1.0 | 0.0 | 0.0 | 0.0 |
| Qwen 3.5 9B | ambiguous | 60 | 0.8333333333333334 | 0.8333333333333334 | 1.0 | NA | NA | 0.18 | 0.82 | 0.0 |
| Qwen 3.5 9B | contradiction | 50 | 0.96 | 0.82 | 0.875 | NA | NA | 0.020833333333333332 | 0.0 | 0.8541666666666666 |
| Qwen 3.5 9B | linear_chain | 60 | 0.9666666666666667 | 0.9333333333333333 | 1.0 | 0.711111111111111 | 0.8267898383371824 | 0.0 | 0.0 | 0.0 |
| Qwen 3.5 9B | transitive_reasoning | 50 | 0.96 | 0.96 | 1.0 | 0.7774294670846394 | 1.0 | 0.0 | 0.0 | 0.0 |
| Llama 3.1 8B | ambiguous | 60 | 1.0 | 1.0 | 1.0 | NA | NA | 0.16666666666666666 | 0.8333333333333334 | 0.0 |
| Llama 3.1 8B | contradiction | 50 | 1.0 | 0.98 | 1.0 | NA | NA | 0.0 | 0.0 | 0.98 |
| Llama 3.1 8B | linear_chain | 60 | 1.0 | 0.8166666666666667 | 0.8333333333333334 | 0.3445692883895131 | 0.37558685446009393 | 0.0 | 0.0 | 0.016666666666666666 |
| Llama 3.1 8B | transitive_reasoning | 50 | 1.0 | 1.0 | 1.0 | 0.7358490566037735 | 1.0 | 0.0 | 0.0 | 0.0 |
| Mistral 7B | ambiguous | 60 | 0.9833333333333333 | 0.7 | 0.8813559322033898 | NA | NA | 0.0 | 1.0 | 0.0 |
| Mistral 7B | contradiction | 50 | 1.0 | 0.84 | 0.68 | NA | NA | 0.0 | 0.0 | 0.8 |
| Mistral 7B | linear_chain | 60 | 0.9333333333333333 | 0.7166666666666667 | 0.7678571428571429 | 0.3083700440528634 | 0.3081570996978852 | 0.0 | 0.0 | 0.017857142857142856 |
| Mistral 7B | transitive_reasoning | 50 | 1.0 | 0.6 | 0.56 | 0.5103448275862068 | 0.6646153846153847 | 0.0 | 0.0 | 0.0 |
| Gemma 3 12B | ambiguous | 60 | 1.0 | 1.0 | 1.0 | NA | NA | 0.9333333333333333 | 0.06666666666666667 | 0.0 |
| Gemma 3 12B | contradiction | 50 | 1.0 | 0.0 | 1.0 | NA | NA | 1.0 | 0.0 | 0.0 |
| Gemma 3 12B | linear_chain | 60 | 1.0 | 1.0 | 1.0 | 0.5101214574898786 | 0.5656565656565657 | 0.0 | 0.0 | 0.0 |
| Gemma 3 12B | transitive_reasoning | 50 | 1.0 | 0.96 | 1.0 | 0.7358490566037735 | 1.0 | 0.0 | 0.0 | 0.0 |

## Plot Reading Guide

- `parse_success_rate.png`: pipeline robustness, not reasoning quality.
- `transport_failure_rate.png`: infrastructure instability, not model behaviour.
- `conditional_trace_grounding_rate.png`: whether reasoning annotations align with the final answer structure.
- `validity_expectation_alignment_rate.png`: whether valid versus invalid outputs match task expectations end-to-end.
- `direct_vs_closure_f1.png`: representation fidelity versus ordering recovery on gold-bearing tasks only.
- `ambiguity_behaviour.png`: abstention discipline versus overcommitment.
- `contradiction_detection_rate.png`: conditional consistency-focused performance on parsed contradiction tasks.
- `verification_task_incidence.png`: task-level prevalence of invariant failure modes.
- `ltl_task_incidence.png`: task-level prevalence of all LTL formula failures.
- `genuine_ltl_incidence.png`: separates genuine trace-level LTL signal from invariant-corroborating LTL.

## Axis Correlation

Pairwise Pearson / phi correlations across intrinsic axes (parse_success, verifier_valid, trace_grounded). High correlation indicates the axes provide largely redundant signal; low correlation indicates they measure distinct things.

**DeepSeek R1 7B**: Collinear axis pairs (|ρ| > 0.90): `verifier_valid`–`trace_grounded` (ρ = 0.90). These axes provide largely redundant signal and should not be treated as independent evidence. Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.90 (n = 250). Weakest pairwise correlation: `parse_success`–`verifier_valid` at ρ = 0.85.
**Qwen 3.5 9B**: Strongest pairwise correlation: `parse_success`–`trace_grounded` at ρ = 0.87 (n = 250). Weakest pairwise correlation: `parse_success`–`verifier_valid` at ρ = 0.52.
**Llama 3.1 8B**: Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.38 (n = 250). Weakest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.38.
**Mistral 7B**: Strongest pairwise correlation: `verifier_valid`–`trace_grounded` at ρ = 0.56 (n = 250). Weakest pairwise correlation: `parse_success`–`verifier_valid` at ρ = 0.17.

See `axis_correlation_*.csv` and `axis_correlation_*.png` for full matrices.
