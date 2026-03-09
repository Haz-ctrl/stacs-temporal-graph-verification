from __future__ import annotations

from src.constraints import default_verifier
from src.schemas import ReasoningStep
from src.temporal_graph import TemporalGraph


def _types(violations) -> set[str]:
    return {v.type for v in violations}


def test_cycle_violation():
    allowed = ["A", "B", "C"]
    pred_edges = [["A", "B", "BEFORE"], ["B", "C", "BEFORE"], ["C", "A", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    verifier = default_verifier()
    violations = verifier.verify(
        tg,
        allowed_events=allowed,
        gold_relations=[],
        pred_edges=pred_edges,
    )
    assert "cycle" in _types(violations)


def test_direct_contradiction_violation():
    allowed = ["A", "B"]
    pred_edges = [["A", "B", "BEFORE"], ["B", "A", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    verifier = default_verifier()
    violations = verifier.verify(
        tg,
        allowed_events=allowed,
        gold_relations=[],
        pred_edges=pred_edges,
    )
    assert "contradiction" in _types(violations)


def test_temporal_inconsistency_violation():
    allowed = ["A", "B", "C"]
    pred_edges = [["A", "B", "BEFORE"], ["B", "C", "BEFORE"], ["C", "A", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    verifier = default_verifier()
    violations = verifier.verify(
        tg,
        allowed_events=allowed,
        gold_relations=[],
        pred_edges=pred_edges,
    )
    assert "temporal_inconsistency" in _types(violations)


def test_hallucinated_node_violation():
    allowed = ["A", "B"]
    pred_edges = [["A", "B", "BEFORE"], ["A", "C", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(["A", "B", "C"])
    tg.add_edges(pred_edges)

    verifier = default_verifier()
    violations = verifier.verify(
        tg,
        allowed_events=allowed,
        gold_relations=[],
        pred_edges=pred_edges,
    )
    assert "hallucinated_node" in _types(violations)


def test_missing_edge_violation():
    allowed = ["A", "B"]
    gold = [["A", "B", "BEFORE"]]
    pred_edges: list[list[str]] = []

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    verifier = default_verifier()
    violations = verifier.verify(
        tg,
        allowed_events=allowed,
        gold_relations=gold,
        pred_edges=pred_edges,
    )
    assert "missing_edge" in _types(violations)


def test_spurious_edge_violation():
    allowed = ["A", "B", "C"]
    gold = [["A", "B", "BEFORE"]]
    pred_edges = [["A", "B", "BEFORE"], ["B", "C", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    verifier = default_verifier()
    violations = verifier.verify(
        tg,
        allowed_events=allowed,
        gold_relations=gold,
        pred_edges=pred_edges,
    )
    assert "spurious_edge" in _types(violations)


def test_overcommitment_violation():
    allowed = ["A", "B"]
    gold: list[list[str]] = []
    pred_edges = [["A", "B", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    verifier = default_verifier()
    violations = verifier.verify(
        tg,
        allowed_events=allowed,
        gold_relations=gold,
        pred_edges=pred_edges,
    )
    assert "overcommitment" in _types(violations)


def test_duplicate_edge_violation():
    allowed = ["A", "B"]
    pred_edges = [
        ["A", "B", "BEFORE"],
        ["A", "B", "BEFORE"],
    ]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    verifier = default_verifier()
    violations = verifier.verify(
        tg,
        allowed_events=allowed,
        gold_relations=[],
        pred_edges=pred_edges,
    )
    assert "duplicate_edge" in _types(violations)


def test_reasoning_support_violation_when_step_support_missing_from_predictions():
    allowed = ["A", "B", "C"]
    pred_edges = [["A", "B", "BEFORE"]]
    reasoning_steps = [
        ReasoningStep(
            step_id=1,
            text="From the prompt, B happened before C.",
            supports=[("B", "C", "BEFORE")],
        )
    ]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    verifier = default_verifier()
    violations = verifier.verify(
        tg,
        allowed_events=allowed,
        gold_relations=[],
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
    )
    assert "unsupported_reasoning_step" in _types(violations)


def test_reasoning_support_no_violation_when_supports_match_predictions():
    allowed = ["A", "B", "C"]
    pred_edges = [["A", "B", "BEFORE"], ["B", "C", "BEFORE"]]
    reasoning_steps = [
        ReasoningStep(
            step_id=1,
            text="The prompt states A happened before B.",
            supports=[("A", "B", "BEFORE")],
        ),
        ReasoningStep(
            step_id=2,
            text="The prompt states B happened before C.",
            supports=[("B", "C", "BEFORE")],
        ),
    ]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    verifier = default_verifier()
    violations = verifier.verify(
        tg,
        allowed_events=allowed,
        gold_relations=[],
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
    )
    assert "unsupported_reasoning_step" not in _types(violations)


def test_no_violation_for_clean_consistent_prediction():
    allowed = ["A", "B", "C"]
    gold = [["A", "B", "BEFORE"], ["B", "C", "BEFORE"]]
    pred_edges = [["A", "B", "BEFORE"], ["B", "C", "BEFORE"]]
    reasoning_steps = [
        ReasoningStep(
            step_id=1,
            text="A happened before B.",
            supports=[("A", "B", "BEFORE")],
        ),
        ReasoningStep(
            step_id=2,
            text="B happened before C.",
            supports=[("B", "C", "BEFORE")],
        ),
    ]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    verifier = default_verifier()
    violations = verifier.verify(
        tg,
        allowed_events=allowed,
        gold_relations=gold,
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
    )
    assert violations == []