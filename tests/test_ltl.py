from __future__ import annotations

from src.ltl import (
    And,
    Atom,
    Eventually,
    Globally,
    LTLEvaluator,
    Next,
    Not,
    Or,
    Until,
    formula_to_dict,
    formula_to_string,
)
from src.trace import TemporalState, TemporalTrace


def _trace_with_flags(
    *, contradictions: tuple[bool, ...], mentions_a: tuple[bool, ...]
) -> TemporalTrace:
    states = []
    for index, (has_contradiction, mentions_event_a) in enumerate(
        zip(contradictions, mentions_a)
    ):
        states.append(
            TemporalState(
                index=index,
                label=f"state_{index}",
                step_id=index + 1,
                is_final_state=index == len(contradictions) - 1,
                text=f"state {index}",
                support_edges=(),
                active_edges=(),
                mentioned_events=("A",) if mentions_event_a else (),
                violation_types=("contradiction",) if has_contradiction else (),
            )
        )
    return TemporalTrace(states=tuple(states))


# ---------------------------------------------------------------------------
# Boolean formulas and serialisation
# ---------------------------------------------------------------------------


def test_ltl_boolean_connectives_and_serialisation() -> None:
    trace = _trace_with_flags(contradictions=(False,), mentions_a=(True,))
    evaluator = LTLEvaluator(trace)
    formula = And(
        Atom("mentions_event", ("A",)), Not(Atom("has_violation", ("contradiction",)))
    )

    result = evaluator.evaluate(formula)

    assert result.satisfied is True
    assert formula_to_dict(formula) == {
        "op": "and",
        "left": {"op": "atom", "predicate": "mentions_event", "args": ["A"]},
        "right": {
            "op": "not",
            "arg": {
                "op": "atom",
                "predicate": "has_violation",
                "args": ["contradiction"],
            },
        },
    }
    assert formula_to_string(
        Or(Atom("mentions_event", ("A",)), Atom("mentions_event", ("B",)))
    ) == ("(mentions_event(A) | mentions_event(B))")


# ---------------------------------------------------------------------------
# Temporal operators
# ---------------------------------------------------------------------------


def test_ltl_temporal_operators_cover_next_eventually_globally_and_until() -> None:
    trace = _trace_with_flags(
        contradictions=(False, False, True),
        mentions_a=(False, True, True),
    )
    evaluator = LTLEvaluator(trace)

    assert evaluator.evaluate(Next(Atom("mentions_event", ("A",)))).satisfied is True
    assert (
        evaluator.evaluate(
            Eventually(Atom("has_violation", ("contradiction",)))
        ).satisfied
        is True
    )
    assert (
        evaluator.evaluate(
            Globally(Not(Atom("has_violation", ("contradiction",))))
        ).satisfied
        is False
    )
    assert (
        evaluator.evaluate(
            Until(
                Not(Atom("has_violation", ("contradiction",))),
                Atom("has_violation", ("contradiction",)),
            )
        ).satisfied
        is True
    )


# ---------------------------------------------------------------------------
# Failure reporting and edge cases
# ---------------------------------------------------------------------------


def test_ltl_reports_earliest_failure_step() -> None:
    trace = _trace_with_flags(
        contradictions=(False, True, True),
        mentions_a=(True, True, True),
    )
    evaluator = LTLEvaluator(trace)

    result = evaluator.evaluate(
        Globally(Not(Atom("has_violation", ("contradiction",))))
    )

    assert result.satisfied is False
    assert result.failure is not None
    assert result.failure.first_failure_step == 1
    assert (
        formula_to_string(result.failure.failing_formula)
        == "has_violation(contradiction)"
    )


def test_ltl_handles_empty_and_single_state_traces() -> None:
    empty_trace = TemporalTrace(states=())
    empty_result = LTLEvaluator(empty_trace).evaluate(Atom("is_final_state"))
    assert empty_result.satisfied is False
    assert empty_result.failure is not None
    assert empty_result.failure.first_failure_step == 0

    single_state_trace = _trace_with_flags(contradictions=(False,), mentions_a=(False,))
    single_result = LTLEvaluator(single_state_trace).evaluate(
        Next(Atom("is_final_state"))
    )
    assert single_result.satisfied is False
    assert single_result.failure is not None
    assert single_result.failure.first_failure_step == 0
