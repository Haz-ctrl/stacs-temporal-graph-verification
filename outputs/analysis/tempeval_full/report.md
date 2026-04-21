# Temporal Verification Evaluation Summary

- Runs analysed: `5`
- Highest parse success: `Llama 3.1 8B` at `1.000`
- Highest fidelity closure F1: `Gemma 3 12B` at `0.602`
- Highest validity-expectation alignment: `Gemma 3 12B` at `0.998`
- Largest fidelity closure-direct gap: `Gemma 3 12B` at `0.252`

## Interpretation

- Parse robustness, transport stability, intrinsic graph validity, trace grounding, exact direct-edge fidelity, closure-level reasoning, ambiguity discipline, and contradiction detection should be read as separate capabilities.
- `validity_expectation_alignment_rate_e2e` checks whether the verifier outcome matches the task intent end-to-end, so clean-but-wrong contradiction abstention does not look deceptively strong.
- `fidelity_direct_f1` and `fidelity_closure_f1` are computed on gold-bearing tasks only, excluding empty-gold ambiguity items from the fidelity headline.
- Closure scoring only covers ordering-bearing relations. On datasets with many `SIMULTANEOUS` labels, closure F1 should be interpreted alongside direct F1 rather than in isolation.
- Direct-vs-closure gaps indicate when a model recovers the implied temporal ordering while still missing the intended explicit representation.
- This dataset does not contain ambiguity or contradiction control slices, so consistency-specific plots are intentionally omitted.

- This run set evaluates a single task family: `tempeval_relation`. Category-wise plots should be read as dataset-wide summaries rather than cross-category diagnostics.

- `Qwen 3.5 9B` has a transport failure rate of `0.190`. Comparative claims for that run should be treated as infrastructure-confounded until rerun with stronger retry settings.

## Top-line Table

| model_label | parse_success_rate | transport_failure_rate | conditional_validity_rate | validity_expectation_alignment_rate_e2e | conditional_trace_grounding_rate | fidelity_direct_f1 | fidelity_closure_f1 | fidelity_closure_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | 0.8729838709677419 | 0.020161290322580645 | 0.48267898383371827 | 0.4213709677419355 | 0.45958429561200925 | 0.20138888888888892 | 0.22857142857142856 | 0.02718253968253964 |
| Qwen 3.5 9B | 0.7943548387096774 | 0.18951612903225806 | 0.5355329949238579 | 0.4254032258064516 | 0.5355329949238579 | 0.31218274111675126 | 0.3968 | 0.08461725888324872 |
| Llama 3.1 8B | 1.0 | 0.0 | 0.8165322580645161 | 0.8165322580645161 | 0.8165322580645161 | 0.2600806451612903 | 0.30500582072176946 | 0.04492517556047915 |
| Mistral 7B | 0.9979838709677419 | 0.0 | 0.8646464646464647 | 0.8629032258064516 | 0.8949494949494949 | 0.2287655719139298 | 0.40414507772020725 | 0.17537950580627745 |
| Gemma 3 12B | 1.0 | 0.0 | 0.9979838709677419 | 0.9979838709677419 | 0.9979838709677419 | 0.35066258919469934 | 0.6024915062287657 | 0.25182891703406635 |

## Category Notes

| model_label | category | parse_success_rate | validity_expectation_alignment_rate_e2e | trace_grounding_rate | direct_f1 | closure_f1 |
| --- | --- | --- | --- | --- | --- | --- |
| DeepSeek R1 7B | tempeval_relation | 0.8729838709677419 | 0.4213709677419355 | 0.45958429561200925 | 0.20138888888888892 | 0.22857142857142856 |
| Qwen 3.5 9B | tempeval_relation | 0.7943548387096774 | 0.4254032258064516 | 0.5355329949238579 | 0.31218274111675126 | 0.3968 |
| Llama 3.1 8B | tempeval_relation | 1.0 | 0.8165322580645161 | 0.8165322580645161 | 0.2600806451612903 | 0.30500582072176946 |
| Mistral 7B | tempeval_relation | 0.9979838709677419 | 0.8629032258064516 | 0.8949494949494949 | 0.2287655719139298 | 0.40414507772020725 |
| Gemma 3 12B | tempeval_relation | 1.0 | 0.9979838709677419 | 0.9979838709677419 | 0.35066258919469934 | 0.6024915062287657 |

## Plot Reading Guide

- `parse_success_rate.png`: pipeline robustness, not reasoning quality.
- `transport_failure_rate.png`: infrastructure instability, not model behaviour.
- `conditional_trace_grounding_rate.png`: whether reasoning annotations align with the final answer structure.
- `validity_expectation_alignment_rate.png`: whether valid versus invalid outputs match task expectations end-to-end.
- `direct_vs_closure_f1.png`: representation fidelity versus ordering recovery on gold-bearing tasks only.
- `verification_task_incidence.png`: task-level prevalence of invariant failure modes.
- `ltl_task_incidence.png`: trace-level corroboration of structural failures; do not read this as independent evidence from the invariant layer.
