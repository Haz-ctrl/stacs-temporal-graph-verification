from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from src.evaluation import compute_prf
from src.temporal_graph import TemporalGraph, canonicalise_relation


PAIRWISE_LABELS: tuple[str, ...] = ("BEFORE", "AFTER", "SIMULTANEOUS", "UNKNOWN")
UNMAPPABLE_LABEL = "UNMAPPABLE"


@dataclass(frozen=True)
class PairwiseInstance:
    task_id: str
    source: str
    target: str
    gold_label: str
    predicted_label: str
    verifier_valid: bool
    trace_grounded: bool


def _explicit_unknown_pair(
    pred_edges: Iterable[Sequence[str]], source: str, target: str
) -> bool:
    for left, right, relation in pred_edges:
        if (
            str(left) == source
            and str(right) == target
            and canonicalise_relation(str(relation)) == "UNKNOWN"
        ):
            return True
    return False


def derive_pairwise_label(
    *,
    events: Sequence[str],
    pred_events: Sequence[str],
    pred_edges: Iterable[Sequence[str]],
) -> str:
    if len(events) != 2:
        raise ValueError("Pairwise label derivation requires exactly two task events.")

    source, target = str(events[0]), str(events[1])
    graph = TemporalGraph()
    graph.add_events(events)
    graph.add_events(pred_events)
    graph.add_edges(pred_edges)

    entailed: List[str] = []
    if graph.entails_edge((source, target, "SIMULTANEOUS")):
        entailed.append("SIMULTANEOUS")
    if graph.entails_edge((source, target, "BEFORE")):
        entailed.append("BEFORE")
    if graph.entails_edge((source, target, "AFTER")):
        entailed.append("AFTER")

    if len(entailed) == 1:
        return entailed[0]
    if len(entailed) > 1:
        return UNMAPPABLE_LABEL
    if _explicit_unknown_pair(pred_edges, source, target):
        return "UNKNOWN"
    return "UNKNOWN"


def pairwise_instance_from_record(record: Mapping[str, Any]) -> PairwiseInstance:
    gold_relations = list(record.get("gold_relations", []))
    events = list(record.get("events", []))
    if len(events) != 2:
        raise ValueError(
            f"Task {record.get('id')} is not pairwise: expected 2 events, found {len(events)}"
        )
    if len(gold_relations) != 1:
        raise ValueError(
            f"Task {record.get('id')} is not single-label pairwise: expected 1 gold relation, found {len(gold_relations)}"
        )

    gold_source, gold_target, gold_label = gold_relations[0]
    verification = dict(record.get("verification", {}))
    predicted_label = derive_pairwise_label(
        events=events,
        pred_events=list(record.get("pred_events", [])),
        pred_edges=list(record.get("pred_edges", [])),
    )
    return PairwiseInstance(
        task_id=str(record.get("id")),
        source=str(gold_source),
        target=str(gold_target),
        gold_label=canonicalise_relation(str(gold_label)),
        predicted_label=predicted_label,
        verifier_valid=bool(verification.get("is_valid")),
        trace_grounded=bool(verification.get("trace_grounded")),
    )


def confusion_matrix(instances: Sequence[PairwiseInstance]) -> List[Dict[str, int]]:
    predicted_labels = list(PAIRWISE_LABELS) + [UNMAPPABLE_LABEL]
    rows: List[Dict[str, int]] = []
    for gold_label in predicted_labels:
        row = {"gold_label": gold_label}
        for predicted_label in predicted_labels:
            row[predicted_label] = sum(
                1
                for instance in instances
                if instance.gold_label == gold_label
                and instance.predicted_label == predicted_label
            )
        row["total"] = sum(row[predicted_label] for predicted_label in predicted_labels)
        rows.append(row)
    return rows


def per_label_metrics(
    instances: Sequence[PairwiseInstance],
) -> List[Dict[str, float | int | str]]:
    rows: List[Dict[str, float | int | str]] = []
    for label in PAIRWISE_LABELS:
        correct = sum(
            1
            for instance in instances
            if instance.gold_label == label and instance.predicted_label == label
        )
        pred_total = sum(
            1 for instance in instances if instance.predicted_label == label
        )
        gold_total = sum(1 for instance in instances if instance.gold_label == label)
        prf = compute_prf(correct, pred_total, gold_total)
        rows.append(
            {
                "label": label,
                "precision": prf.precision,
                "recall": prf.recall,
                "f1": prf.f1,
                "correct": prf.correct,
                "pred_total": prf.pred_total,
                "gold_total": prf.gold_total,
            }
        )
    return rows


def verification_slices(
    instances: Sequence[PairwiseInstance],
) -> List[Dict[str, float | int | str]]:
    slices = {
        "all_tasks": list(instances),
        "verifier_valid": [
            instance for instance in instances if instance.verifier_valid
        ],
        "verifier_invalid": [
            instance for instance in instances if not instance.verifier_valid
        ],
        "trace_grounded": [
            instance for instance in instances if instance.trace_grounded
        ],
        "trace_ungrounded": [
            instance for instance in instances if not instance.trace_grounded
        ],
    }
    rows: List[Dict[str, float | int | str]] = []
    for name, slice_instances in slices.items():
        total = len(slice_instances)
        accuracy = (
            sum(
                1
                for instance in slice_instances
                if instance.gold_label == instance.predicted_label
            )
            / total
            if total
            else 0.0
        )
        rows.append(
            {
                "slice": name,
                "num_tasks": total,
                "label_accuracy": accuracy,
            }
        )
    return rows
