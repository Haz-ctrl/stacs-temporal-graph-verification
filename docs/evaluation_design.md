# Evaluation Design Note

This repository uses two distinct notions of success:

## Intrinsic Verification

Intrinsic verification asks whether the predicted temporal structure is self-consistent, grounded in the task event set, and satisfies the active temporal specification.

Examples:

- a prediction can be intrinsically valid but still miss gold edges
- a prediction can preserve the gold ordering closure while using a different direct edge set
- a prediction with a cycle or unsupported event reference is intrinsically invalid regardless of gold match

Intrinsic verification now has two internal layers:

- invariant checks for direct structural properties
- focused LTL checks over a step-indexed reasoning trace

The current LTL layer is deliberately narrow. It supports a graph-grounded subset of temporal logic over predicates such as `before(a,b)`, `mentions_event(e)`, `supports(edge)`, and `has_violation(kind)`. It is intended as a formal-verification step forward, not as a complete general-purpose temporal logic engine.

## Gold Scoring

Gold scoring compares prediction and reference using multiple views:

### Direct-edge correctness

Exact match over canonical labelled triples.

This captures representation fidelity:

- `("A", "B", "BEFORE")` is different from `("B", "A", "AFTER")`
- extra transitive edges lower direct precision even if closure is preserved

### Closure-equivalent correctness

Ordering closure is computed after:

- normalising `AFTER`
- collapsing `SIMULTANEOUS` groups
- excluding `UNKNOWN` from ordering edges

This captures whether the model preserved implied temporal ordering even when direct edge sets differ.

### Representation completeness

Per-task scoring also reports:

- missing direct edges
- spurious direct edges
- missing closure pairs
- spurious closure pairs
- whether ordering closure is preserved exactly

### Abstention and overcommitment

If gold has no temporal commitments and prediction asserts informative relations, the task is flagged as overcommitment.

This matters for ambiguous or underspecified tasks because predicting something is not always better than abstaining.

## Why This Split Matters

Without this separation, the system risks conflating:

- structural inconsistency with ordinary prediction error
- exact representation mismatch with reasoning mismatch
- abstention failure with low recall

Those conflations would distort dissertation conclusions, especially when comparing models or prompting strategies.

## LTL-Specific Reporting

Run outputs now also expose:

- active invariant and formula specifications
- formula violation counts by type
- first violating trace step
- counterexample summaries that reference the failing subformula and implicated step

This makes the verifier more useful for failure analysis and supervisor demos because temporal-spec failures can be localised to reasoning trace positions instead of only being reported as flat validity flags.

## Supported LTL Fragment

The LTL layer operates over a bounded, graph-grounded fragment of temporal logic. It is not a general-purpose LTL model checker.

**Supported predicates** (evaluated against a step-indexed reasoning trace):

- `before(a, b)` — edge (a, b, BEFORE) present in prediction graph at this step
- `after(a, b)` — edge (a, b, AFTER) present
- `simultaneous(a, b)` — edge (a, b, SIMULTANEOUS) present
- `unknown(a, b)` — edge (a, b, UNKNOWN) present
- `supports(edge)` — any reasoning step at or before this step supports the given edge
- `mentions_event(e)` — event e is mentioned in a reasoning step at or before this step
- `has_violation(kind)` — a violation of type `kind` has been recorded at this step

**Supported operators** (over the step-indexed trace of reasoning steps):

- `G φ` — φ holds at every step (globally)
- `F φ` — φ holds at some step (eventually)
- `X φ` — φ holds at the next step
- `φ U ψ` — φ holds until ψ holds
- Boolean connectives: `¬`, `∧`, `∨`

**Not supported:**

- General LTL over unbounded state spaces or infinite traces
- Nested fixpoints (μ-calculus / CTL*)
- Past-time operators (PLTL)
- Full TimeML interval algebra end-to-end
- Model checking over branching time or concurrent traces

## Verifier Calibration

The verifier constraint library has not been evaluated against an external gold standard for violation detection accuracy. Whether the constraints correctly fire on genuinely invalid predictions — and do not fire on valid ones — has not been measured against independent human annotations.

This is a known limitation flagged for follow-up work. Until calibration is performed, `conditional_validity_rate` should be interpreted as the rate at which the verifier classifies predictions as valid, not as independently verified reasoning quality.
