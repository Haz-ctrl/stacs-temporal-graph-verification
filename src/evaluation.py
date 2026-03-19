from __future__ import annotations

from dataclasses import asdict
from typing import Iterable, List, Set, Tuple

from src.results import PRFResult, TaskScore
from src.temporal_graph import Edge, EdgeLike, TemporalGraph, _to_edge

OrderingPair = Tuple[str, str]


def canonical_edge_set(edges: Iterable[EdgeLike]) -> Set[Edge]:
    return {_to_edge(edge) for edge in edges}


def compute_prf(correct: int, pred_total: int, gold_total: int) -> PRFResult:
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
    return compute_prf(correct, pred_total, gold_total)


def direct_edge_prf(gold_edges: Iterable[EdgeLike], pred_edges: Iterable[EdgeLike]) -> PRFResult:
    gold_set = canonical_edge_set(gold_edges)
    pred_set = canonical_edge_set(pred_edges)
    correct = len(gold_set & pred_set)
    return compute_prf(correct, len(pred_set), len(gold_set))


def _ordering_pairs(allowed_events: List[str], edges: Iterable[EdgeLike]) -> Set[OrderingPair]:
    graph = TemporalGraph()
    graph.add_events(allowed_events)
    graph.add_edges(edges)
    return graph.ordering_pairs()


def closure_prf(
    allowed_events: List[str],
    gold_edges: Iterable[EdgeLike],
    pred_edges: Iterable[EdgeLike],
) -> PRFResult:
    gold_pairs = _ordering_pairs(allowed_events, gold_edges)
    pred_pairs = _ordering_pairs(allowed_events, pred_edges)
    correct = len(gold_pairs & pred_pairs)
    return compute_prf(correct, len(pred_pairs), len(gold_pairs))


def score_prediction(
    *,
    allowed_events: List[str],
    gold_edges: Iterable[EdgeLike],
    pred_edges: Iterable[EdgeLike],
) -> TaskScore:
    gold_set = canonical_edge_set(gold_edges)
    pred_set = canonical_edge_set(pred_edges)

    direct = direct_edge_prf(gold_set, pred_set)
    closure = closure_prf(allowed_events, gold_set, pred_set)

    gold_pairs = _ordering_pairs(allowed_events, gold_set)
    pred_pairs = _ordering_pairs(allowed_events, pred_set)

    missing_direct_edges = sorted(gold_set - pred_set)
    spurious_direct_edges = sorted(pred_set - gold_set)
    missing_closure_pairs = [list(pair) for pair in sorted(gold_pairs - pred_pairs)]
    spurious_closure_pairs = [list(pair) for pair in sorted(pred_pairs - gold_pairs)]

    abstained = len(pred_set) == 0
    has_overcommitment = len(gold_set) == 0 and len(pred_set) > 0

    return TaskScore(
        direct=direct,
        closure=closure,
        missing_direct_edges=missing_direct_edges,
        spurious_direct_edges=spurious_direct_edges,
        missing_closure_pairs=missing_closure_pairs,
        spurious_closure_pairs=spurious_closure_pairs,
        preserves_ordering_closure=(gold_pairs == pred_pairs),
        has_overcommitment=has_overcommitment,
        abstained=abstained,
    )


def task_score_to_json(task_score: TaskScore) -> dict[str, object]:
    payload = asdict(task_score)
    payload["direct"] = asdict(task_score.direct)
    payload["closure"] = asdict(task_score.closure)
    return payload
