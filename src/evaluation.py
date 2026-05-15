from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Iterable, List, Set, Tuple

from src.results import PRFResult, TaskScore
from src.schemas import ReasoningStep
from src.temporal_graph import Edge, EdgeLike, TemporalGraph, _to_edge

OrderingPair = Tuple[str, str]


def canonical_edge_set(edges: Iterable[EdgeLike]) -> Set[Edge]:
    return {_to_edge(edge) for edge in edges}


def compute_prf(correct: int, pred_total: int, gold_total: int) -> PRFResult:
    precision = (correct / pred_total) if pred_total else 0.0
    recall = (correct / gold_total) if gold_total else 0.0
    f1 = (
        (2.0 * precision * recall / (precision + recall))
        if (precision + recall)
        else 0.0
    )
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


def _symmetric_canonical_edge(edge: Edge) -> Edge:
    """
    Normalise an edge to BEFORE orientation for symmetric direct F1.

    ``AFTER(A, B)`` and ``BEFORE(B, A)`` express the same ordering constraint.
    Converting both to a canonical BEFORE form ensures the two representations
    are treated as equal during set intersection in direct F1 computation.

    ``SIMULTANEOUS(A, B)`` and ``SIMULTANEOUS(B, A)`` are also equivalent, so
    simultaneous endpoints are sorted into a stable unordered representation.
    UNKNOWN edges are returned unchanged.
    """
    src, tgt, rel = edge
    if rel == "AFTER":
        return (tgt, src, "BEFORE")
    if rel == "SIMULTANEOUS" and tgt < src:
        return (tgt, src, rel)
    return (src, tgt, rel)


def direct_edge_prf(
    gold_edges: Iterable[EdgeLike], pred_edges: Iterable[EdgeLike]
) -> PRFResult:
    gold_set = {_symmetric_canonical_edge(e) for e in canonical_edge_set(gold_edges)}
    pred_set = {_symmetric_canonical_edge(e) for e in canonical_edge_set(pred_edges)}
    correct = len(gold_set & pred_set)
    return compute_prf(correct, len(pred_set), len(gold_set))


def _build_label_map(task_events: List[str]) -> Dict[str, str]:
    """
    Build a lookup table from predicted label variants to canonical task event labels.

    Three lookup keys are registered for each task event:
      1. Exact canonical string              e.g. "started [ei3]"
      2. Trigger word only (lowercased)      e.g. "started"
      3. Full label lowercased              e.g. "started [ei3]"

    If two task events share the same trigger word, the lookup for the trigger
    word alone is ambiguous and is omitted to avoid silent misattribution.
    """
    trigger_count: Dict[str, int] = {}

    for event in task_events:
        trigger = event.split("[")[0].strip().lower()
        trigger_count[trigger] = trigger_count.get(trigger, 0) + 1

    label_map: Dict[str, str] = {}
    for event in task_events:
        label_map[event] = event
        label_map[event.lower()] = event
        trigger = event.split("[")[0].strip().lower()
        if trigger_count[trigger] == 1:
            label_map[trigger] = event

    return label_map


def _remap_label(label: str, label_map: Dict[str, str]) -> str:
    """Return canonical label if a mapping exists, else return label unchanged."""
    if label in label_map:
        return label_map[label]
    lowered = label.lower()
    if lowered in label_map:
        return label_map[lowered]
    trigger = label.split("[")[0].strip().lower()
    if trigger in label_map:
        return label_map[trigger]
    return label


def normalise_pred_labels(
    pred_events: List[str],
    pred_edges: List[Edge],
    reasoning_steps: "List[ReasoningStep]",
    task_events: List[str],
) -> "Tuple[List[str], List[Edge], List[ReasoningStep]]":
    """
    Remap predicted event labels to their canonical task-event form.

    When models strip the ``[eiN]`` identifier from event names (emitting
    ``"started"`` instead of ``"started [ei3]"``), all downstream checks fail:
    ``unknown_nodes()`` flags them as hallucinated, and both direct and closure
    F1 are zero because string matching against gold labels fails.

    This function resolves each predicted label against the task's canonical
    event list using three lookup strategies (exact, case-insensitive full,
    unambiguous trigger word). Labels that match no known event are left
    unchanged so that genuine hallucinations are still caught by the verifier.

    The remapping is applied to ``pred_events``, both endpoints of every edge in
    ``pred_edges``, and the support edges inside every ``ReasoningStep``.
    """
    label_map = _build_label_map(task_events)

    normalised_events = [_remap_label(event, label_map) for event in pred_events]

    normalised_edges: List[Edge] = [
        (_remap_label(src, label_map), _remap_label(tgt, label_map), rel)
        for src, tgt, rel in pred_edges
    ]

    normalised_steps: List[ReasoningStep] = []
    for step in reasoning_steps:
        remapped_supports: List[Edge] = [
            (_remap_label(src, label_map), _remap_label(tgt, label_map), rel)
            for src, tgt, rel in step.supports
        ]
        normalised_steps.append(
            step.__class__(
                step_id=step.step_id,
                text=step.text,
                supports=remapped_supports,
                confidence=step.confidence,
            )
        )

    return normalised_events, normalised_edges, normalised_steps


def _ordering_pairs(
    allowed_events: List[str], edges: Iterable[EdgeLike]
) -> Set[OrderingPair]:
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
    symmetric_gold_set = {_symmetric_canonical_edge(edge) for edge in gold_set}
    symmetric_pred_set = {_symmetric_canonical_edge(edge) for edge in pred_set}

    direct = direct_edge_prf(gold_set, pred_set)
    closure = closure_prf(allowed_events, gold_set, pred_set)

    gold_pairs = _ordering_pairs(allowed_events, gold_set)
    pred_pairs = _ordering_pairs(allowed_events, pred_set)

    missing_direct_edges = sorted(symmetric_gold_set - symmetric_pred_set)
    spurious_direct_edges = sorted(symmetric_pred_set - symmetric_gold_set)
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
