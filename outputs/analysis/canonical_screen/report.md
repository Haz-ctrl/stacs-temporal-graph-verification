# Temporal Verification Evaluation Summary

- Runs analysed: `5`
- Highest parse success: `Llama 3.1 8B` at `1.000`
- Highest closure F1: `Qwen 3.5 9B` at `0.935`
- Best ambiguity abstention: `Gemma 3 12B` at `0.600`
- Best contradiction detection: `Qwen 3.5 9B` at `1.000`
- Largest closure-direct gap: `Llama 3.1 8B` at `0.262`

## Interpretation

- This is a screening-scale analysis. The current runs are useful for promotion and failure profiling, not final ranking claims.
- Small categories such as `long_chain` should be treated as directional evidence only.
- Parse robustness, transport stability, intrinsic graph validity, trace grounding, exact direct-edge fidelity, closure-level reasoning, ambiguity discipline, and contradiction detection should be read as separate capabilities.
- Direct-vs-closure gaps indicate when a model recovers the implied temporal ordering while still missing the intended explicit representation.
- Ambiguous and contradiction categories are consistency-oriented slices. They should not be interpreted through raw F1 alone.

## Top-line Table

| model_label | parse_success_rate | transport_failure_rate | conditional_validity_rate | conditional_trace_grounding_rate | direct_f1 | closure_f1 | closure_minus_direct_f1 | ambiguity_overcommitment_rate | contradiction_detection_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | 0.75 | 0.0 | 1.0 | 1.0 | 0.7037037037037038 | 0.8865979381443299 | 0.18289423444062602 | 0.6666666666666666 | 0.0 |
| Qwen 3.5 9B | 0.9 | 0.0 | 0.7222222222222222 | 0.7777777777777778 | 0.7647058823529412 | 0.935064935064935 | 0.1703590527119938 | 0.5 | 1.0 |
| Llama 3.1 8B | 1.0 | 0.0 | 0.75 | 0.95 | 0.4935064935064935 | 0.7559055118110236 | 0.2623990183045301 | 1.0 | 1.0 |
| Mistral 7B | 0.95 | 0.0 | 0.6842105263157895 | 0.7894736842105263 | 0.4126984126984127 | 0.4666666666666667 | 0.053968253968254 | 1.0 | 0.75 |
| Gemma 3 12B | 1.0 | 0.0 | 0.95 | 0.95 | 0.7323943661971831 | 0.9344262295081968 | 0.20203186331101364 | 0.4 | 0.0 |

## Category Notes

| model_label | category | parse_success_rate | conditional_validity_rate | trace_grounding_rate | direct_f1 | closure_f1 | abstention_rate | overcommitment_rate | contradiction_detection_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | ambiguous | 0.6 | 1.0 | 1.0 | NA | NA | 0.3333333333333333 | 0.6666666666666666 | 0.0 |
| DeepSeek R1 7B | contradiction | 1.0 | 1.0 | 1.0 | NA | NA | 0.0 | 0.0 | 0.0 |
| DeepSeek R1 7B | linear_chain | 0.6 | 1.0 | 1.0 | 0.5 | 0.4444444444444444 | 0.0 | 0.0 | 0.0 |
| DeepSeek R1 7B | transitive_reasoning | 0.8 | 1.0 | 1.0 | 0.7142857142857143 | 1.0 | 0.0 | 0.0 | 0.0 |
| Qwen 3.5 9B | ambiguous | 0.8 | 0.75 | 0.75 | NA | NA | 0.5 | 0.5 | 0.0 |
| Qwen 3.5 9B | contradiction | 1.0 | 0.0 | 0.25 | NA | NA | 0.0 | 0.0 | 1.0 |
| Qwen 3.5 9B | linear_chain | 1.0 | 1.0 | 1.0 | 0.7272727272727272 | 0.8275862068965518 | 0.0 | 0.0 | 0.0 |
| Qwen 3.5 9B | transitive_reasoning | 1.0 | 1.0 | 1.0 | 0.8571428571428571 | 1.0 | 0.0 | 0.0 | 0.0 |
| Llama 3.1 8B | ambiguous | 1.0 | 1.0 | 1.0 | NA | NA | 0.0 | 1.0 | 0.0 |
| Llama 3.1 8B | contradiction | 1.0 | 0.0 | 1.0 | NA | NA | 0.0 | 0.0 | 1.0 |
| Llama 3.1 8B | linear_chain | 1.0 | 0.8 | 0.8 | 0.0 | 0.21428571428571427 | 0.0 | 0.0 | 0.0 |
| Llama 3.1 8B | transitive_reasoning | 1.0 | 1.0 | 1.0 | 0.7027027027027027 | 1.0 | 0.0 | 0.0 | 0.0 |
| Mistral 7B | ambiguous | 0.8 | 1.0 | 1.0 | NA | NA | 0.0 | 1.0 | 0.0 |
| Mistral 7B | contradiction | 1.0 | 0.25 | 0.75 | NA | NA | 0.0 | 0.0 | 0.75 |
| Mistral 7B | linear_chain | 1.0 | 0.8 | 0.8 | 0.4210526315789474 | 0.4615384615384615 | 0.0 | 0.0 | 0.2 |
| Mistral 7B | transitive_reasoning | 1.0 | 0.6 | 0.6 | 0.5454545454545454 | 0.7368421052631579 | 0.0 | 0.0 | 0.0 |
| Gemma 3 12B | ambiguous | 1.0 | 1.0 | 1.0 | NA | NA | 0.6 | 0.4 | 0.0 |
| Gemma 3 12B | contradiction | 1.0 | 1.0 | 1.0 | NA | NA | 1.0 | 0.0 | 0.0 |
| Gemma 3 12B | linear_chain | 1.0 | 1.0 | 1.0 | 0.7 | 0.8000000000000002 | 0.0 | 0.0 | 0.0 |
| Gemma 3 12B | transitive_reasoning | 1.0 | 0.8 | 0.8 | 0.7027027027027027 | 1.0 | 0.0 | 0.0 | 0.0 |

## Plot Reading Guide

- `parse_success_rate.png`: pipeline robustness, not reasoning quality.
- `transport_failure_rate.png`: infrastructure instability, not model behaviour.
- `conditional_trace_grounding_rate.png`: whether reasoning annotations align with the final answer structure.
- `direct_vs_closure_f1.png`: representation fidelity versus ordering recovery.
- `ambiguity_behaviour.png`: abstention discipline versus overcommitment.
- `contradiction_detection_rate.png`: consistency-focused performance on contradiction tasks.
- `verification_task_incidence.png`: task-level prevalence of invariant failure modes.
- `ltl_task_incidence.png`: trace-level corroboration of structural failures; do not read this as independent evidence from the invariant layer.
