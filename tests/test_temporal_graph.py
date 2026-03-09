from __future__ import annotations

import pytest

from src.temporal_graph import (
    ALLOWED_RELATIONS,
    TemporalGraph,
    _to_edge,
    canonicalise_relation,
)


def test_allowed_relations_contains_expected_labels() -> None:
    assert ALLOWED_RELATIONS == frozenset({"BEFORE", "AFTER", "SIMULTANEOUS", "UNKNOWN"})


def test_canonicalise_relation_normalises_case_and_whitespace() -> None:
    assert canonicalise_relation(" before ") == "BEFORE"
    assert canonicalise_relation("after") == "AFTER"
    assert canonicalise_relation("Simultaneous") == "SIMULTANEOUS"
    assert canonicalise_relation("unknown") == "UNKNOWN"


def test_canonicalise_relation_rejects_empty_relation() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        canonicalise_relation("   ")


def test_canonicalise_relation_rejects_unsupported_relation() -> None:
    with pytest.raises(ValueError, match="Unsupported relation label"):
        canonicalise_relation("DURING")


def test_to_edge_accepts_tuple_and_canonicalises_relation() -> None:
    edge = _to_edge(("A", "B", " before "))
    assert edge == ("A", "B", "BEFORE")


def test_to_edge_accepts_list_and_canonicalises_relation() -> None:
    edge = _to_edge(["A", "B", "after"])
    assert edge == ("A", "B", "AFTER")


def test_to_edge_rejects_wrong_length() -> None:
    with pytest.raises(ValueError, match="expected 3 items"):
        _to_edge(("A", "B"))  # type: ignore[arg-type]


def test_to_edge_rejects_invalid_relation() -> None:
    with pytest.raises(ValueError, match="Unsupported relation label"):
        _to_edge(("A", "B", "DURING"))


def test_to_edge_rejects_empty_source() -> None:
    with pytest.raises(ValueError, match="source"):
        _to_edge(("", "B", "BEFORE"))


def test_to_edge_rejects_empty_target() -> None:
    with pytest.raises(ValueError, match="target"):
        _to_edge(("A", "   ", "BEFORE"))


def test_add_event_adds_node() -> None:
    graph = TemporalGraph()
    graph.add_event("Event A")
    assert graph.nodes() == ["Event A"]


def test_add_event_rejects_empty_string() -> None:
    graph = TemporalGraph()
    with pytest.raises(ValueError, match="non-empty"):
        graph.add_event("")


def test_add_relation_auto_adds_missing_nodes() -> None:
    graph = TemporalGraph()
    graph.add_relation("A", "B", "BEFORE")

    assert sorted(graph.nodes()) == ["A", "B"]
    assert graph.edges() == [("A", "B", "BEFORE")]


def test_add_relation_rejects_invalid_relation() -> None:
    graph = TemporalGraph()
    with pytest.raises(ValueError, match="Unsupported relation label"):
        graph.add_relation("A", "B", "DURING")


def test_add_edges_accepts_mixed_list_and_tuple_inputs() -> None:
    graph = TemporalGraph()
    graph.add_edges(
        [
            ("A", "B", "BEFORE"),
            ["B", "C", "after"],
            ("C", "D", "SIMULTANEOUS"),
        ]
    )

    assert set(graph.edges()) == {
        ("A", "B", "BEFORE"),
        ("B", "C", "AFTER"),
        ("C", "D", "SIMULTANEOUS"),
    }


def test_edges_for_relation_filters_correctly() -> None:
    graph = TemporalGraph()
    graph.add_edges(
        [
            ("A", "B", "BEFORE"),
            ("B", "C", "AFTER"),
            ("C", "D", "BEFORE"),
        ]
    )

    assert set(graph.edges_for_relation("BEFORE")) == {
        ("A", "B", "BEFORE"),
        ("C", "D", "BEFORE"),
    }


def test_relations_set_returns_canonical_edge_set() -> None:
    graph = TemporalGraph()
    graph.add_edges([("A", "B", "before"), ("B", "C", "AFTER")])

    assert graph.relations_set() == {
        ("A", "B", "BEFORE"),
        ("B", "C", "AFTER"),
    }


def test_is_acyclic_true_for_chain() -> None:
    graph = TemporalGraph()
    graph.add_edges([("A", "B", "BEFORE"), ("B", "C", "BEFORE")])

    assert graph.is_acyclic() is True
    assert graph.find_cycles() == []


def test_is_acyclic_false_for_cycle() -> None:
    graph = TemporalGraph()
    graph.add_edges(
        [
            ("A", "B", "BEFORE"),
            ("B", "C", "BEFORE"),
            ("C", "A", "BEFORE"),
        ]
    )

    assert graph.is_acyclic() is False
    cycles = graph.find_cycles()
    assert cycles != []
    assert any(set(cycle) == {"A", "B", "C"} for cycle in cycles)


def test_transitive_closure_pairs_returns_reachable_pairs() -> None:
    graph = TemporalGraph()
    graph.add_edges([("A", "B", "BEFORE"), ("B", "C", "BEFORE")])

    assert graph.transitive_closure_pairs() == {
        ("A", "B"),
        ("B", "C"),
        ("A", "C"),
    }


def test_implied_before_pairs_matches_transitive_closure() -> None:
    graph = TemporalGraph()
    graph.add_edges([("A", "B", "BEFORE"), ("B", "C", "BEFORE")])

    assert graph.implied_before_pairs() == graph.transitive_closure_pairs()


def test_pairs_for_relation_returns_only_requested_relation_pairs() -> None:
    graph = TemporalGraph()
    graph.add_edges(
        [
            ("A", "B", "BEFORE"),
            ("B", "C", "AFTER"),
            ("C", "D", "BEFORE"),
        ]
    )

    assert graph.pairs_for_relation("BEFORE") == {
        ("A", "B"),
        ("C", "D"),
    }
    assert graph.pairs_for_relation("AFTER") == {
        ("B", "C"),
    }


def test_has_direct_contradiction_false_when_none_present() -> None:
    graph = TemporalGraph()
    graph.add_edges([("A", "B", "BEFORE"), ("B", "C", "BEFORE")])

    assert graph.has_direct_contradiction("BEFORE") is False
    assert graph.direct_contradictions("BEFORE") == []


def test_has_direct_contradiction_true_for_reverse_before_edges() -> None:
    graph = TemporalGraph()
    graph.add_edges([("A", "B", "BEFORE"), ("B", "A", "BEFORE")])

    assert graph.has_direct_contradiction("BEFORE") is True
    assert graph.direct_contradictions("BEFORE") == [("A", "B")]


def test_direct_contradictions_returns_sorted_unique_pairs() -> None:
    graph = TemporalGraph()
    graph.add_edges(
        [
            ("B", "A", "BEFORE"),
            ("A", "B", "BEFORE"),
            ("C", "D", "BEFORE"),
            ("D", "C", "BEFORE"),
        ]
    )

    assert graph.direct_contradictions("BEFORE") == [("A", "B"), ("C", "D")]


def test_temporal_inconsistencies_empty_for_consistent_before_graph() -> None:
    graph = TemporalGraph()
    graph.add_edges(
        [
            ("A", "B", "BEFORE"),
            ("B", "C", "BEFORE"),
        ]
    )

    assert graph.temporal_inconsistencies("BEFORE") == []


def test_temporal_inconsistencies_detects_cycle_pairs() -> None:
    graph = TemporalGraph()
    graph.add_edges(
        [
            ("A", "B", "BEFORE"),
            ("B", "C", "BEFORE"),
            ("C", "A", "BEFORE"),
        ]
    )

    inconsistencies = graph.temporal_inconsistencies("BEFORE")
    assert inconsistencies == [("A", "B"), ("A", "C"), ("B", "C")]


def test_temporal_inconsistencies_rejects_non_before_relation() -> None:
    graph = TemporalGraph()
    graph.add_edges([("A", "B", "AFTER")])

    with pytest.raises(ValueError, match="supports BEFORE only"):
        graph.temporal_inconsistencies("AFTER")


def test_unknown_nodes_returns_sorted_unknown_nodes() -> None:
    graph = TemporalGraph()
    graph.add_edges(
        [
            ("A", "B", "BEFORE"),
            ("Ghost", "A", "BEFORE"),
            ("Phantom", "B", "AFTER"),
        ]
    )

    assert graph.unknown_nodes(["A", "B"]) == ["Ghost", "Phantom"]