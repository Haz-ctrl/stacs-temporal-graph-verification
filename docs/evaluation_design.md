# Evaluation Design Note

This repository uses two distinct notions of success:

## Intrinsic Verification

Intrinsic verification asks whether the predicted temporal structure is self-consistent and grounded in the task event set.

Examples:

- a prediction can be intrinsically valid but still miss gold edges
- a prediction can preserve the gold ordering closure while using a different direct edge set
- a prediction with a cycle or unsupported event reference is intrinsically invalid regardless of gold match

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
