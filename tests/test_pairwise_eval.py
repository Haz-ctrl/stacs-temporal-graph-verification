from __future__ import annotations

from src.pairwise_eval import (
    UNMAPPABLE_LABEL,
    confusion_matrix,
    derive_pairwise_label,
    pairwise_instance_from_record,
    per_label_metrics,
    verification_slices,
)


def test_derive_pairwise_label_maps_before_after_and_unknown() -> None:
    assert derive_pairwise_label(
        events=["A", "B"],
        pred_events=["A", "B"],
        pred_edges=[["A", "B", "BEFORE"]],
    ) == "BEFORE"
    assert derive_pairwise_label(
        events=["A", "B"],
        pred_events=["A", "B"],
        pred_edges=[["A", "B", "AFTER"]],
    ) == "AFTER"
    assert derive_pairwise_label(
        events=["A", "B"],
        pred_events=["A", "B"],
        pred_edges=[],
    ) == "UNKNOWN"


def test_derive_pairwise_label_marks_contradictory_graph_unmappable() -> None:
    assert derive_pairwise_label(
        events=["A", "B"],
        pred_events=["A", "B"],
        pred_edges=[["A", "B", "BEFORE"], ["B", "A", "BEFORE"]],
    ) == UNMAPPABLE_LABEL


def test_pairwise_metrics_and_slices() -> None:
    records = [
        {
            "id": "t1",
            "events": ["A", "B"],
            "pred_events": ["A", "B"],
            "gold_relations": [["A", "B", "BEFORE"]],
            "pred_edges": [["A", "B", "BEFORE"]],
            "verification": {"is_valid": True, "trace_grounded": True},
        },
        {
            "id": "t2",
            "events": ["A", "B"],
            "pred_events": ["A", "B"],
            "gold_relations": [["A", "B", "AFTER"]],
            "pred_edges": [],
            "verification": {"is_valid": False, "trace_grounded": False},
        },
    ]
    instances = [pairwise_instance_from_record(record) for record in records]

    matrix_rows = confusion_matrix(instances)
    before_row = next(row for row in matrix_rows if row["gold_label"] == "BEFORE")
    after_row = next(row for row in matrix_rows if row["gold_label"] == "AFTER")
    assert before_row["BEFORE"] == 1
    assert after_row["UNKNOWN"] == 1

    metric_rows = per_label_metrics(instances)
    before_metrics = next(row for row in metric_rows if row["label"] == "BEFORE")
    assert before_metrics["f1"] == 1.0

    slice_rows = verification_slices(instances)
    valid_slice = next(row for row in slice_rows if row["slice"] == "verifier_valid")
    invalid_slice = next(row for row in slice_rows if row["slice"] == "verifier_invalid")
    assert valid_slice["label_accuracy"] == 1.0
    assert invalid_slice["label_accuracy"] == 0.0
