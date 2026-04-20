# Temporal Verification Evaluation Summary

- Runs analysed: `5`
- Highest parse success: `llama3.1:8b` at `1.000`
- Highest closure F1: `qwen3.5:9b` at `0.951`
- Best ambiguity abstention: `gemma3:12b` at `0.733`
- Best contradiction detection: `llama3.1:8b` at `0.900`
- Largest closure-direct gap: `qwen3.5:9b` at `0.171`

## Interpretation

- Parse robustness, transport stability, intrinsic graph validity, trace grounding, exact direct-edge fidelity, closure-level reasoning, ambiguity discipline, and contradiction detection should be read as separate capabilities.
- Direct-vs-closure gaps indicate when a model recovers the implied temporal ordering while still missing the intended explicit representation.
- Ambiguous and contradiction categories are consistency-oriented slices. They should not be interpreted through raw F1 alone.

## Top-line Table

| model_label | parse_success_rate | transport_failure_rate | conditional_validity_rate | conditional_trace_grounding_rate | direct_f1 | closure_f1 | closure_minus_direct_f1 | ambiguity_overcommitment_rate | contradiction_detection_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-r1:7b | 0.7733333333333333 | 0.006666666666666667 | 0.9741379310344828 | 0.9396551724137931 | 0.6192307692307693 | 0.7861020629750272 | 0.1668712937442579 | 0.88 | 0.125 |
| qwen3.5:9b | 0.9333333333333333 | 0.06666666666666667 | 0.9 | 0.9571428571428572 | 0.780120481927711 | 0.9513043478260869 | 0.17118386589837586 | 0.6538461538461539 | 0.7368421052631579 |
| llama3.1:8b | 1.0 | 0.0 | 0.8733333333333333 | 0.96 | 0.5500705218617772 | 0.6875502008032129 | 0.13747967894143576 | 1.0 | 0.9 |
| mistral:7b | 0.9666666666666667 | 0.0 | 0.8758620689655172 | 0.7793103448275862 | 0.3568904593639576 | 0.38264738598442705 | 0.025756926620469467 | 1.0 | 0.8 |
| gemma3:12b | 1.0 | 0.0 | 1.0 | 1.0 | 0.6432926829268294 | 0.7637540453074433 | 0.12046136238061389 | 0.26666666666666666 | 0.0 |

## Category Notes

| model_label | category | parse_success_rate | conditional_validity_rate | trace_grounding_rate | direct_f1 | closure_f1 | abstention_rate | overcommitment_rate | contradiction_detection_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-r1:7b | ambiguous | 0.8333333333333334 | 1.0 | 1.0 | NA | NA | 0.12 | 0.88 | 0.0 |
| deepseek-r1:7b | contradiction | 0.8 | 0.875 | 0.875 | NA | NA | 0.1875 | 0.0 | 0.125 |
| deepseek-r1:7b | linear_chain | 0.725 | 0.9655172413793104 | 0.9310344827586207 | 0.5954198473282443 | 0.676056338028169 | 0.0 | 0.0 | 0.0 |
| deepseek-r1:7b | transitive_reasoning | 0.825 | 1.0 | 1.0 | 0.7088607594936709 | 1.0 | 0.0 | 0.0 | 0.0 |
| qwen3.5:9b | ambiguous | 0.8666666666666667 | 1.0 | 1.0 | NA | NA | 0.34615384615384615 | 0.6538461538461539 | 0.0 |
| qwen3.5:9b | contradiction | 0.95 | 0.2631578947368421 | 0.6842105263157895 | NA | NA | 0.10526315789473684 | 0.0 | 0.7368421052631579 |
| qwen3.5:9b | linear_chain | 1.0 | 1.0 | 1.0 | 0.6847826086956521 | 0.8083623693379791 | 0.0 | 0.0 | 0.0 |
| qwen3.5:9b | transitive_reasoning | 0.975 | 1.0 | 1.0 | 0.7796610169491525 | 1.0 | 0.0 | 0.0 | 0.0 |
| llama3.1:8b | ambiguous | 1.0 | 1.0 | 1.0 | NA | NA | 0.0 | 1.0 | 0.0 |
| llama3.1:8b | contradiction | 1.0 | 0.1 | 1.0 | NA | NA | 0.0 | 0.0 | 0.9 |
| llama3.1:8b | linear_chain | 1.0 | 1.0 | 0.875 | 0.2857142857142857 | 0.3109540636042402 | 0.0 | 0.0 | 0.0 |
| llama3.1:8b | transitive_reasoning | 1.0 | 1.0 | 1.0 | 0.7083333333333333 | 1.0 | 0.0 | 0.0 | 0.0 |
| mistral:7b | ambiguous | 0.9333333333333333 | 0.9642857142857143 | 0.8928571428571429 | NA | NA | 0.0 | 1.0 | 0.03571428571428571 |
| mistral:7b | contradiction | 1.0 | 0.2 | 0.75 | NA | NA | 0.0 | 0.0 | 0.8 |
| mistral:7b | linear_chain | 0.95 | 0.9736842105263158 | 0.868421052631579 | 0.29333333333333333 | 0.3571428571428572 | 0.0 | 0.0 | 0.02631578947368421 |
| mistral:7b | transitive_reasoning | 1.0 | 1.0 | 0.55 | 0.5369649805447471 | 0.7210884353741497 | 0.0 | 0.0 | 0.0 |
| gemma3:12b | ambiguous | 1.0 | 1.0 | 1.0 | NA | NA | 0.7333333333333333 | 0.26666666666666666 | 0.0 |
| gemma3:12b | contradiction | 1.0 | 1.0 | 1.0 | NA | NA | 1.0 | 0.0 | 0.0 |
| gemma3:12b | linear_chain | 1.0 | 1.0 | 1.0 | 0.5 | 0.5896414342629482 | 0.0 | 0.0 | 0.0 |
| gemma3:12b | transitive_reasoning | 1.0 | 1.0 | 1.0 | 0.7083333333333333 | 1.0 | 0.0 | 0.0 | 0.0 |

## Plot Reading Guide

- `parse_success_rate.png`: pipeline robustness, not reasoning quality.
- `transport_failure_rate.png`: infrastructure instability, not model behaviour.
- `conditional_trace_grounding_rate.png`: whether reasoning annotations align with the final answer structure.
- `direct_vs_closure_f1.png`: representation fidelity versus ordering recovery.
- `ambiguity_behaviour.png`: abstention discipline versus overcommitment.
- `contradiction_detection_rate.png`: consistency-focused performance on contradiction tasks.
- `verification_task_incidence.png`: task-level prevalence of invariant failure modes.
- `ltl_task_incidence.png`: trace-level corroboration of structural failures; do not read this as independent evidence from the invariant layer.
