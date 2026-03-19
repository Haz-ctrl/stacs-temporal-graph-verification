from __future__ import annotations

from src.schemas import ReasoningStep
from src.trace import TemporalState, TemporalTrace, build_temporal_trace


def test_build_temporal_trace_creates_step_states_and_final_state() -> None:
    trace = build_temporal_trace(
        allowed_events=["A", "B", "C"],
        pred_edges=[
            ("A", "B", "BEFORE"),
            ("C", "B", "AFTER"),
            ("A", "C", "SIMULTANEOUS"),
            ("B", "C", "UNKNOWN"),
        ],
        reasoning_steps=[
            ReasoningStep(
                step_id=1,
                text="A happened before B.",
                supports=[("A", "B", "BEFORE")],
            ),
            ReasoningStep(
                step_id=2,
                text="C is discussed with A.",
                supports=[("A", "C", "SIMULTANEOUS")],
            ),
        ],
    )

    assert len(trace) == 3

    first = trace.state(0)
    assert first.label == "step_1"
    assert first.is_final_state is False
    assert first.support_edges == (("A", "B", "BEFORE"),)
    assert first.active_edges == (("A", "B", "BEFORE"),)
    assert "A" in first.mentioned_events
    assert "B" in first.mentioned_events

    second = trace.state(1)
    assert second.label == "step_2"
    assert second.active_edges == (
        ("A", "B", "BEFORE"),
        ("A", "C", "SIMULTANEOUS"),
    )

    final = trace.state(2)
    assert final.label == "final_prediction"
    assert final.is_final_state is True
    assert final.active_edges == (
        ("A", "B", "BEFORE"),
        ("C", "B", "AFTER"),
        ("A", "C", "SIMULTANEOUS"),
        ("B", "C", "UNKNOWN"),
    )


def test_temporal_trace_predicates_cover_relations_support_mentions_and_violations() -> None:
    base_trace = TemporalTrace(
        states=(
            TemporalState(
                index=0,
                label="step_1",
                step_id=1,
                is_final_state=False,
                text="A before B",
                support_edges=(("A", "B", "BEFORE"),),
                active_edges=(
                    ("A", "B", "BEFORE"),
                    ("C", "B", "AFTER"),
                    ("A", "C", "SIMULTANEOUS"),
                    ("B", "C", "UNKNOWN"),
                ),
                mentioned_events=("A", "B"),
            ),
            TemporalState(
                index=1,
                label="final_prediction",
                step_id=None,
                is_final_state=True,
                text="final",
                support_edges=(),
                active_edges=(("A", "B", "BEFORE"),),
                mentioned_events=("A", "B"),
            ),
        )
    ).with_violations([set(), {"contradiction", "hallucinated_node"}])

    assert base_trace.predicate_holds(0, "before", ("A", "B")) is True
    assert base_trace.predicate_holds(0, "after", ("C", "B")) is True
    assert base_trace.predicate_holds(0, "simultaneous", ("A", "C")) is True
    assert base_trace.predicate_holds(0, "unknown", ("B", "C")) is True
    assert base_trace.predicate_holds(0, "supports", ("A", "B", "BEFORE")) is True
    assert base_trace.predicate_holds(0, "mentions_event", ("A",)) is True
    assert base_trace.predicate_holds(1, "has_violation", ("contradiction",)) is True
    assert base_trace.predicate_holds(1, "introduced_violation", ("hallucinated_node",)) is True
    assert base_trace.predicate_holds(1, "is_final_state", ()) is True
    assert base_trace.predicate_holds(0, "has_violation", ("contradiction",)) is False
