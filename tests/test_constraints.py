from __future__ import annotations

from src.temporal_graph import TemporalGraph
from src.constraints import default_verifier


def _types(violations) -> set[str]:
    return {v.type for v in violations}


def test_cycle_violation():
    allowed = ["A", "B", "C"]
    pred_edges = [["A", "B", "BEFORE"], ["B", "C", "BEFORE"], ["C", "A", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    v = default_verifier()
    violations = v.verify(
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

    v = default_verifier()
    violations = v.verify(
        tg,
        allowed_events=allowed,
        gold_relations=[],
        pred_edges=pred_edges,
    )
    assert "contradiction" in _types(violations)


def test_hallucinated_node_violation():
    allowed = ["A", "B"]
    pred_edges = [["A", "B", "BEFORE"], ["A", "C", "BEFORE"]]  # C not allowed

    tg = TemporalGraph()
    tg.add_events(["A", "B", "C"])  # graph can contain it; constraint should catch it
    tg.add_edges(pred_edges)

    v = default_verifier()
    violations = v.verify(
        tg,
        allowed_events=allowed,  # only A,B allowed
        gold_relations=[],
        pred_edges=pred_edges,
    )
    assert "hallucinated_node" in _types(violations)


def test_missing_edge_violation():
    allowed = ["A", "B"]
    gold = [["A", "B", "BEFORE"]]
    pred_edges: list[list[str]] = []  # missing

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    v = default_verifier()
    violations = v.verify(
        tg,
        allowed_events=allowed,
        gold_relations=gold,
        pred_edges=pred_edges,
    )
    assert "missing_edge" in _types(violations)


def test_spurious_edge_violation():
    allowed = ["A", "B", "C"]
    gold = [["A", "B", "BEFORE"]]
    pred_edges = [["A", "B", "BEFORE"], ["B", "C", "BEFORE"]]  # extra edge

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    v = default_verifier()
    violations = v.verify(
        tg,
        allowed_events=allowed,
        gold_relations=gold,
        pred_edges=pred_edges,
    )
    assert "spurious_edge" in _types(violations)


def test_overcommitment_violation():
    allowed = ["A", "B"]
    gold: list[list[str]] = []  # ambiguous
    pred_edges = [["A", "B", "BEFORE"]]  # guessed

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    v = default_verifier()
    violations = v.verify(
        tg,
        allowed_events=allowed,
        gold_relations=gold,
        pred_edges=pred_edges,
    )
    assert "overcommitment" in _types(violations)