# Temporal Verification Evaluation Summary

- Runs analysed: `5`
- Highest parse success: `Llama 3.1 8B` at `1.000`
- Highest fidelity closure F1: `Gemma 3 12B` at `0.602`
- Highest validity-expectation alignment: `Gemma 3 12B` at `0.998`
- Best ambiguity abstention: `DeepSeek R1 7B` at `0.000`
- Best contradiction detection: `DeepSeek R1 7B` at `0.000`
- Largest fidelity closure-direct gap: `Gemma 3 12B` at `0.252`

## Interpretation

- Parse robustness, transport stability, intrinsic graph validity, trace grounding, exact direct-edge fidelity, closure-level reasoning, ambiguity discipline, and contradiction detection should be read as separate capabilities.
- `validity_expectation_alignment_rate_e2e` checks whether the verifier outcome matches the task intent end-to-end, so clean-but-wrong contradiction abstention does not look deceptively strong.
- `fidelity_direct_f1` and `fidelity_closure_f1` are computed on gold-bearing tasks only, excluding empty-gold ambiguity items from the fidelity headline.
- Direct-vs-closure gaps indicate when a model recovers the implied temporal ordering while still missing the intended explicit representation.
- Ambiguous and contradiction categories are consistency-oriented slices. They should not be interpreted through raw F1 alone.

## Top-line Table

| model_label | parse_success_rate | transport_failure_rate | conditional_validity_rate | validity_expectation_alignment_rate_e2e | conditional_trace_grounding_rate | fidelity_direct_f1 | fidelity_closure_f1 | fidelity_closure_gap | ambiguity_overcommitment_rate | contradiction_detection_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | 0.8729838709677419 | 0.020161290322580645 | 0.48267898383371827 | 0.4213709677419355 | 0.45958429561200925 | 0.20138888888888892 | 0.22857142857142856 | 0.02718253968253964 | NA | NA |
| Qwen 3.5 9B | 0.7943548387096774 | 0.18951612903225806 | 0.5355329949238579 | 0.4254032258064516 | 0.5355329949238579 | 0.31218274111675126 | 0.3968 | 0.08461725888324872 | NA | NA |
| Llama 3.1 8B | 1.0 | 0.0 | 0.8165322580645161 | 0.8165322580645161 | 0.8165322580645161 | 0.2600806451612903 | 0.30500582072176946 | 0.04492517556047915 | NA | NA |
| Mistral 7B | 0.9979838709677419 | 0.0 | 0.8646464646464647 | 0.8629032258064516 | 0.8949494949494949 | 0.2287655719139298 | 0.40414507772020725 | 0.17537950580627745 | NA | NA |
| Gemma 3 12B | 1.0 | 0.0 | 0.9979838709677419 | 0.9979838709677419 | 0.9979838709677419 | 0.35066258919469934 | 0.6024915062287657 | 0.25182891703406635 | NA | NA |

## Category Notes

| model_label | category | parse_success_rate | validity_expectation_alignment_rate_e2e | trace_grounding_rate | direct_f1 | closure_f1 | abstention_rate | overcommitment_rate | contradiction_detection_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

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
