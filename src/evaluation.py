from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Set, Tuple

from src.temporal_graph import EdgeLike, TemporalGraph, _to_edge

Edge = Tuple[str, str, str]


@dataclass(frozen=True)
class PRFResult:
    precision: float
    recall: float
    f1: float
    correct: int
    pred_total: int
    gold_total: int


def canonical_edge_set(edges: Iterable[EdgeLike]) -> Set[Edge]:
    """
    Convert an iterable of edge-like triples into a canonical set.
    """
    return {_to_edge(edge) for edge in edges}


def compute_prf(correct: int, pred_total: int, gold_total: int) -> PRFResult:
    """
    Compute precision, recall, and F1 from counts.
    """
    precision = (correct / pred_total) if pred_total else 0.0
    recall = (correct / gold_total) if gold_total else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return PRFResult(
        precision=precision,
        recall=recall,
        f1=f1,
        correct=correct,
        pred_total=pred_total,
        gold_total=gold_total,
    )


def aggregate_prf(correct: int, pred_total: int, gold_total: int) -> PRFResult:
    """
    Convenience wrapper for aggregate reporting across many tasks.
    """
    return compute_prf(correct, pred_total, gold_total)


def direct_edge_prf(gold_edges: Iterable[EdgeLike], pred_edges: Iterable[EdgeLike]) -> PRFResult:
    """
    Compute direct edge precision/recall/F1 using exact canonical edge match.
    """
    gold_set = canonical_edge_set(gold_edges)
    pred_set = canonical_edge_set(pred_edges)
    correct = len(gold_set & pred_set)
    return compute_prf(correct, len(pred_set), len(gold_set))


def closure_prf(
    allowed_events: List[str],
    gold_edges: Iterable[EdgeLike],
    pred_edges: Iterable[EdgeLike],
) -> PRFResult:
    """
    Compute precision/recall/F1 over transitive closure reachability pairs.

    This reflects whether the predicted graph preserves the implied temporal
    ordering structure, even when direct edge sets differ.
    """
    gold_graph = TemporalGraph()
    gold_graph.add_events(allowed_events)
    gold_graph.add_edges(gold_edges)

    pred_graph = TemporalGraph()
    pred_graph.add_events(allowed_events)
    pred_graph.add_edges(pred_edges)

    gold_pairs = gold_graph.transitive_closure_pairs()
    pred_pairs = pred_graph.transitive_closure_pairs()
    correct = len(gold_pairs & pred_pairs)

    return compute_prf(correct, len(pred_pairs), len(gold_pairs))