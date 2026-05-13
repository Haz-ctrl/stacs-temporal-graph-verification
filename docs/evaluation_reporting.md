# Evaluation Reporting Note

This project is evaluation-first. The analysis layer is intended to support research reporting, not only raw benchmarking.

## Read Top-line Metrics Carefully

The key run-level metrics answer different questions:

- `parse_success_rate`: can the model reliably enter the structured evaluation pipeline?
- `transport_failure_rate`: how much of the end-to-end failure is infrastructure rather than model behaviour?
- `conditional_validity_rate`: among parsed outputs, how often is the structure intrinsically valid?
- `validity_expectation_alignment_rate_e2e`: end-to-end, how often does the valid/invalid status match the task expectation?
- `conditional_trace_grounding_rate`: among parsed outputs, how often do reasoning annotations align with the final answer structure?
- `direct_f1`: how closely does the model match the intended explicit edge set?
- `closure_f1`: how well does the model recover the implied temporal ordering, even if the explicit representation is incomplete?
- `fidelity_direct_f1`: direct-edge F1 on gold-bearing tasks only
- `fidelity_closure_f1`: closure F1 on gold-bearing tasks only
- `closure_minus_direct_f1`: how large is the gap between ordering recovery and explicit fidelity?
- `ambiguity_abstention_rate`: how often does the model refrain from unsupported commitments?
- `ambiguity_overcommitment_rate`: how often does the model invent temporal commitments in ambiguous tasks?
- `contradiction_detection_rate`: how often do contradiction tasks trigger meaningful temporal inconsistency signals?

These should not be collapsed into a single “best model” score.

Use `conditional_validity_rate` and `validity_expectation_alignment_rate_e2e` together.

- A model can have high intrinsic validity by abstaining on contradiction tasks.
- The alignment metric checks whether that validity status was actually the right one for the task.

Use `fidelity_*` metrics when making fidelity claims.

- The original run-level `direct_f1` and `closure_f1` preserve the full expected-valid task mix.
- The `fidelity_*` variants remove empty-gold tasks so ambiguity slices do not dilute or distort fidelity headlines.

For MATRES-style `UNKNOWN` labels, prefer direct/pairwise reporting.

- MATRES `VAGUE` is mapped to `UNKNOWN`.
- `UNKNOWN` is an abstention label and contributes no ordering edge.
- Closure F1 should not be used as the headline metric for `UNKNOWN` examples; use pairwise label metrics, confusion matrices, and abstention/overcommitment behaviour instead.

## Screening vs Final Evaluation

When the run contains a small number of tasks, the generated `report.md` explicitly labels it as screening-scale analysis.

Interpret screening runs as:

- promotion evidence for full evaluation
- failure profiling
- prompt/schema stability checks

Do not use screening runs as the sole basis for dissertation-level ranking claims.

## Category Interpretation

Not every category should be treated as an ordinary F1 slice.

- `linear_chain`, `long_chain`, `transitive_reasoning` are primarily fidelity-oriented categories.
- `ambiguous` is a discipline category. Abstention and overcommitment matter more than F1.
- `contradiction` is a consistency category. Contradiction detection and invalidity matter more than F1.

For this reason, the analysis layer leaves direct/closure F1 blank when a category does not support a meaningful fidelity interpretation.

## Failure Analysis

`failure_breakdown.csv` reports:

- `event_count`: raw number of violation events
- `affected_tasks`: number of tasks that exhibited the failure
- `affected_task_rate`: task-level prevalence

Supervisor-facing discussion should focus on `affected_task_rate` unless there is a clear reason to discuss repeated violation events.

## Counterexamples

`counterexamples.md` is designed to support qualitative discussion in reports and meetings.

It includes:

- representative parse failures
- representative verification failures
- first violation step where available
- predicted edges and the original question text

Use these examples to explain *how* models fail, not only *how often*.

## Recommended Supervisor Narrative

A strong report built from this repository should argue that temporal reasoning quality decomposes into multiple capabilities:

1. structured-output robustness
2. transport stability
3. intrinsic temporal consistency
4. trace grounding
5. exact relational fidelity
6. closure-level ordering recovery
7. ambiguity discipline
8. contradiction detection

That is a stronger contribution than a flat leaderboard over a small benchmark.
