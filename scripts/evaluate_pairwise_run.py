from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt

from src.pairwise_eval import (
    PAIRWISE_LABELS,
    UNMAPPABLE_LABEL,
    confusion_matrix,
    pairwise_instance_from_record,
    per_label_metrics,
    verification_slices,
)


def _load_predictions(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            rows.append(json.loads(line))
    return rows


def _write_csv(
    path: Path, rows: List[Dict[str, Any]], *, fieldnames: List[str]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _plot_confusion_matrix(path: Path, rows: List[Dict[str, Any]]) -> None:
    labels = list(PAIRWISE_LABELS) + [UNMAPPABLE_LABEL]
    matrix = [[int(row[label]) for label in labels] for row in rows]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    image = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=25)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("Gold label")
    ax.set_title("Pairwise Relation Confusion Matrix")
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            ax.text(j, i, str(value), ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_verification_accuracy(path: Path, rows: List[Dict[str, Any]]) -> None:
    labels = [str(row["slice"]) for row in rows if row["slice"] != "all_tasks"]
    values = [
        float(row["label_accuracy"]) for row in rows if row["slice"] != "all_tasks"
    ]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(labels, values, color="#4C78A8")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Label accuracy")
    ax.set_title("Pairwise Label Accuracy by Verification Slice")
    ax.tick_params(axis="x", rotation=25)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.02,
            f"{value:.0%}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export pairwise classification audits for a completed run."
    )
    parser.add_argument(
        "--run",
        required=True,
        help="Run directory containing predictions.jsonl and report.json.",
    )
    parser.add_argument(
        "--out", required=True, help="Output directory for audit CSVs and plots."
    )
    args = parser.parse_args()

    run_dir = Path(args.run)
    predictions_path = run_dir / "predictions.jsonl"
    if not predictions_path.exists():
        raise ValueError(f"Missing predictions file: {predictions_path}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_rows = _load_predictions(predictions_path)
    instances = [pairwise_instance_from_record(row) for row in raw_rows]

    audit_rows: List[Dict[str, Any]] = []
    for row, instance in zip(raw_rows, instances):
        verification = dict(row.get("verification", {}))
        score = dict(row.get("score", {}))
        audit_rows.append(
            {
                "task_id": instance.task_id,
                "category": row.get("category", ""),
                "gold_label": instance.gold_label,
                "predicted_label": instance.predicted_label,
                "label_correct": int(instance.gold_label == instance.predicted_label),
                "verifier_valid": int(instance.verifier_valid),
                "trace_grounded": int(instance.trace_grounded),
                "direct_f1": float(dict(score.get("direct", {})).get("f1", 0.0)),
                "closure_f1": float(dict(score.get("closure", {})).get("f1", 0.0)),
                "first_violation_step": verification.get("first_violation_step"),
                "num_violations": len(list(verification.get("violations", []))),
                "num_formula_violations": len(
                    list(verification.get("formula_violations", []))
                ),
                "question": row.get("question", ""),
                "gold_relations": json.dumps(
                    row.get("gold_relations", []), ensure_ascii=True
                ),
                "pred_edges": json.dumps(row.get("pred_edges", []), ensure_ascii=True),
                "answer": row.get("answer", ""),
            }
        )

    confusion_rows = confusion_matrix(instances)
    metrics_rows = per_label_metrics(instances)
    slice_rows = verification_slices(instances)

    _write_csv(
        out_dir / "pairwise_task_audit.csv",
        audit_rows,
        fieldnames=list(audit_rows[0].keys()) if audit_rows else ["task_id"],
    )
    _write_csv(
        out_dir / "pairwise_confusion_matrix.csv",
        confusion_rows,
        fieldnames=["gold_label", *PAIRWISE_LABELS, UNMAPPABLE_LABEL, "total"],
    )
    _write_csv(
        out_dir / "pairwise_label_metrics.csv",
        metrics_rows,
        fieldnames=[
            "label",
            "precision",
            "recall",
            "f1",
            "correct",
            "pred_total",
            "gold_total",
        ],
    )
    _write_csv(
        out_dir / "verification_accuracy_slices.csv",
        slice_rows,
        fieldnames=["slice", "num_tasks", "label_accuracy"],
    )

    _plot_confusion_matrix(out_dir / "pairwise_confusion_matrix.png", confusion_rows)
    _plot_verification_accuracy(
        out_dir / "verification_accuracy_slices.png", slice_rows
    )

    print(f"Exported pairwise audit for {len(instances)} tasks -> {out_dir}")


if __name__ == "__main__":
    main()
