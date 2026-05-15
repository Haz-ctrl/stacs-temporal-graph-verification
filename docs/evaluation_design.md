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
- `supports(edge)` — the current reasoning step supports the given edge
- `mentions_event(e)` — event e is mentioned in a reasoning step at or before this step
- `has_violation(kind)` — a violation of type `kind` has been recorded at this step

`supports(edge)` uses canonical temporal-edge matching: `AFTER(A,B)` and
`BEFORE(B,A)` are equivalent support, and `SIMULTANEOUS(A,B)` is matched
symmetrically. `UNKNOWN` remains exact.

**Supported operators** (over the step-indexed trace of reasoning steps):

- `G φ` — φ holds at every step (globally)
- `F φ` — φ holds at some step (eventually)
- `X φ` — φ holds at the next step
- `φ U ψ` — φ holds until ψ holds
- Boolean connectives: `¬`, `∧`, `∨`

### Task-Specific Formulas (Generated Per Prediction)

The default specification also generates formulas from each parsed prediction.
These formulas depend on the event names and relations in the model output, so
they are not stored as static specification entries.

#### `ltl_unsupported_final_commitment`

For every final predicted edge `(a, b, rel)` where `rel != UNKNOWN`, the verifier
generates:

```text
F(supports(a,b,rel))
```

This means that at least one reasoning step must semantically support the final
commitment. It detects cases where the final answer asserts an informative edge
that the reasoning trace never set up. Matching uses the canonical temporal-edge
semantics described above, so `AFTER(A,B)` can support `BEFORE(B,A)`.

This cannot be reduced to the existing `ReasoningSupportConstraint`. That
invariant checks the reverse direction: every step support must be entailed by
the final graph. The LTL formula checks whether every final commitment was
grounded somewhere in the step-indexed trace.

Example:

- Final prediction: `("a", "b", "BEFORE")`
- Reasoning steps: no step supports `("a", "b", "BEFORE")`
- Result: `ltl_unsupported_final_commitment` fires

If a reasoning step supports `("a", "b", "BEFORE")`, the formula passes. If the
final edge is `UNKNOWN`, no formula is generated because abstentions do not need
supporting temporal commitment.

#### `ltl_trace_inversion`

For every pair where a reasoning step supports `BEFORE(a,b)`, the verifier
generates:

```text
G(supports(a,b,BEFORE) -> G(!supports(b,a,BEFORE)))
```

The implementation represents implication as:

```text
G(!supports(a,b,BEFORE) | G(!supports(b,a,BEFORE)))
```

This detects mid-trace inversions: once the trace commits to `a BEFORE b`, a
later step must not support `b BEFORE a`.

The invariant layer can miss this because invariants primarily inspect the final
edge set and the final relation between step supports and final answers. A model
can temporarily invert its reasoning and then remove the contradiction from the
final prediction. The LTL formula still observes the step-indexed inconsistency.

Example:

- Step 1 supports `("a", "b", "BEFORE")`
- Step 2 supports `("b", "a", "BEFORE")`
- Result: `ltl_trace_inversion` fires

If all later supports preserve `("a", "b", "BEFORE")`, or if there are no
reasoning steps, no trace-inversion violation is raised.

### Why the Two LTL Categories Are Distinct

Category 1 is invariant-corroborating LTL:

```text
G(!has_violation(kind))
```

These formulas re-express invariant results as trace-level assertions for
`contradiction`, `temporal_inconsistency`, and `hallucinated_node`. Their value
is temporal localisation of known invariant failures: they show where a known
structural violation appears in the reasoning trace and whether it persists to
the final state.

Category 2 is genuine trace-level LTL. These formulas use `supports()` and
event-specific predicates to check properties the invariant layer cannot check
by itself:

- whether final commitments were trace-grounded, using `F`
- whether the reasoning trace is internally consistent in its ordering
  commitments, using `G` over step supports

Run summaries therefore report `ltl_genuine_violation_rate` separately from
`ltl_invariant_corroboration_rate`.

**Not supported:**

- General LTL over unbounded state spaces or infinite traces
- Nested fixpoints (μ-calculus / CTL*)
- Past-time operators (PLTL)
- Full TimeML interval algebra end-to-end
- Model checking over branching time or concurrent traces

## Verifier Calibration

The verifier constraint library has not been evaluated against an external gold standard for violation detection accuracy. Whether the constraints correctly fire on genuinely invalid predictions — and do not fire on valid ones — has not been measured against independent human annotations.

This is a known limitation flagged for follow-up work. Until calibration is performed, `conditional_validity_rate` should be interpreted as the rate at which the verifier classifies predictions as valid, not as independently verified reasoning quality.
