"""
Generate supplementary analysis plots from existing run outputs.

No inference re-run required. All plots read from summary.json (produced by
summarise_runs.py) and prediction JSONL files in the run directories.

Usage:
    python scripts/generate_analysis_plots.py \
        --canonical-dir outputs/runs/canonical_full \
        --tempeval-dir  outputs/runs/tempeval_full \
        --maven-ere-dir outputs/runs/maven_ere_full \
        --canonical-analysis outputs/analysis/canonical_full \
        --tempeval-analysis  outputs/analysis/tempeval_full \
        --maven-ere-analysis outputs/analysis/maven_ere_full \
        --out outputs/analysis/supplementary_plots
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Make `src` importable when this script is invoked directly from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DatasetBundle:
    key: str
    label: str
    summary: Dict[str, Any]
    run_dirs: List[Path]
    manifest: Dict[str, Dict[str, Any]]


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _load_manifest(base_dir: Path) -> Dict[str, Dict[str, Any]]:
    manifest_path = base_dir / "run_manifest.json"
    if not manifest_path.exists():
        return {}
    raw = _read_json(manifest_path)
    if isinstance(raw, dict) and isinstance(raw.get("runs"), dict):
        return {str(run_id): dict(meta) for run_id, meta in raw["runs"].items()}
    if isinstance(raw, dict):
        return {str(run_id): dict(meta) for run_id, meta in raw.items()}
    return {}


def _find_run_dirs(
    base_dir: Path, *, predictions_filename: str = "predictions.jsonl"
) -> List[Path]:
    """Find run directories containing the requested prediction JSONL file."""
    if not base_dir.is_dir():
        return []
    if (base_dir / predictions_filename).exists():
        return [base_dir]
    return sorted(
        child
        for child in base_dir.iterdir()
        if child.is_dir() and (child / predictions_filename).exists()
    )


def _model_label_from_report(
    report: Dict[str, Any],
    manifest: Dict[str, Dict[str, Any]],
) -> str:
    run_id = str(report.get("run_id", ""))
    meta = manifest.get(run_id, {})
    return str(
        meta.get("model_label")
        or report.get("model_metadata", {}).get("model")
        or run_id
        or "unknown"
    )


def _load_predictions_by_model(
    run_dirs: List[Path],
    manifest: Dict[str, Dict[str, Any]],
    *,
    predictions_filename: str = "predictions.jsonl",
) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {}
    for run_dir in run_dirs:
        report_path = run_dir / "report.json"
        if not report_path.exists():
            continue
        report = _read_json(report_path)
        label = _model_label_from_report(report, manifest)
        preds = _read_jsonl(run_dir / predictions_filename)
        if label not in result:
            result[label] = []
        result[label].extend(preds)
    return result


def _write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Plot 1: Violation type × model rate heatmap
# ---------------------------------------------------------------------------


def plot_violation_type_model_heatmap(
    summary: Dict[str, Any],
    out_dir: Path,
) -> None:
    """Heatmap of affected_task_rate for each (violation_type, model) pair."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    failure_rows = [
        r
        for r in summary.get("failure_breakdown", [])
        if r.get("failure_scope") in ("verification", "ltl_formula")
    ]
    if not failure_rows:
        return

    violation_types = sorted({r["failure_type"] for r in failure_rows})
    models = sorted({r["model_label"] for r in failure_rows})

    matrix = [
        [
            next(
                (
                    r["affected_task_rate"]
                    for r in failure_rows
                    if r["failure_type"] == vt and r["model_label"] == m
                ),
                0.0,
            )
            for m in models
        ]
        for vt in violation_types
    ]

    fig_h = max(4, len(violation_types) * 0.55 + 1)
    fig_w = max(6, len(models) * 1.8 + 1)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(matrix, cmap="YlOrRd", vmin=0.0, vmax=1.0, aspect="auto")
    plt.colorbar(im, ax=ax, label="Affected task rate")

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=30, ha="right", fontsize=9)
    ax.set_yticks(range(len(violation_types)))
    ax.set_yticklabels(violation_types, fontsize=8)
    ax.set_title("Violation Type × Model: Affected Task Rate")

    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            ax.text(
                j,
                i,
                f"{val:.2f}",
                ha="center",
                va="center",
                fontsize=7,
                color="white" if val > 0.5 else "black",
            )

    fig.tight_layout()
    out_path = out_dir / "violation_type_model_heatmap.png"
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(str(out_path))


# ---------------------------------------------------------------------------
# Plot 2: Verifier as screening signal
# ---------------------------------------------------------------------------


def plot_verifier_screening_signal(
    predictions_by_model: Dict[str, List[Dict[str, Any]]],
    out_dir: Path,
) -> None:
    """Precision/recall/specificity of is_valid=False as a screening signal."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    models = sorted(predictions_by_model.keys())
    precisions, recalls, specificities = [], [], []

    for model in models:
        gold_preds = [p for p in predictions_by_model[model] if p.get("gold_relations")]
        tp = sum(
            1
            for p in gold_preds
            if not p.get("verification", {}).get("is_valid", True)
            and p.get("score", {}).get("direct", {}).get("correct", 0) == 0
        )
        fp = sum(
            1
            for p in gold_preds
            if not p.get("verification", {}).get("is_valid", True)
            and p.get("score", {}).get("direct", {}).get("correct", 0) > 0
        )
        fn = sum(
            1
            for p in gold_preds
            if p.get("verification", {}).get("is_valid", True)
            and p.get("score", {}).get("direct", {}).get("correct", 0) == 0
        )
        tn = sum(
            1
            for p in gold_preds
            if p.get("verification", {}).get("is_valid", True)
            and p.get("score", {}).get("direct", {}).get("correct", 0) > 0
        )
        precisions.append(tp / (tp + fp) if (tp + fp) else 0.0)
        recalls.append(tp / (tp + fn) if (tp + fn) else 0.0)
        specificities.append(tn / (tn + fp) if (tn + fp) else 0.0)

    fig, ax = plt.subplots(figsize=(max(8, len(models) * 2.2), 5))
    width = 0.25
    pos = list(range(len(models)))
    ax.bar(
        [p - width for p in pos],
        precisions,
        width,
        label="Precision (invalid→incorrect)",
    )
    ax.bar(pos, recalls, width, label="Recall (incorrect→invalid)")
    ax.bar(
        [p + width for p in pos],
        specificities,
        width,
        label="Specificity (valid→correct)",
    )
    ax.set_xticks(pos)
    ax.set_xticklabels(models, rotation=25, ha="right")
    ax.set_ylabel("Rate")
    ax.set_ylim(0.0, 1.05)
    ax.set_title("Verifier as Screening Signal (Gold-bearing Tasks)")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    out_path = out_dir / "verifier_screening_signal.png"
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(str(out_path))


# ---------------------------------------------------------------------------
# Plot 3: Direct vs closure F1 by category
# ---------------------------------------------------------------------------


def plot_direct_vs_closure_f1_by_category(
    summary: Dict[str, Any],
    out_dir: Path,
) -> None:
    """Three-panel comparison of direct vs closure F1 for key fidelity categories."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    category_rows = summary.get("category_breakdown", [])
    categories = ["linear_chain", "transitive_reasoning", "long_chain"]
    models = sorted({r["model_label"] for r in category_rows})

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    width = 0.35

    for ax, cat in zip(axes, categories):
        cat_data = {
            r["model_label"]: r for r in category_rows if r.get("category") == cat
        }
        direct_vals = [
            float(cat_data.get(m, {}).get("direct_f1") or 0.0) for m in models
        ]
        closure_vals = [
            float(cat_data.get(m, {}).get("closure_f1") or 0.0) for m in models
        ]
        pos = list(range(len(models)))
        ax.bar([p - width / 2 for p in pos], direct_vals, width, label="Direct F1")
        ax.bar([p + width / 2 for p in pos], closure_vals, width, label="Closure F1")
        ax.set_xticks(pos)
        ax.set_xticklabels(models, rotation=30, ha="right", fontsize=8)
        ax.set_title(cat)
        ax.set_ylim(0.0, 1.05)

    axes[0].set_ylabel("F1")
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Direct vs Closure F1 by Category")
    fig.tight_layout()
    out_path = out_dir / "direct_vs_closure_f1_by_category.png"
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(str(out_path))


# ---------------------------------------------------------------------------
# Plot 4: Cross-dataset comparison
# ---------------------------------------------------------------------------


def plot_cross_dataset_comparison(
    datasets: Sequence[DatasetBundle],
    out_dir: Path,
) -> None:
    """Side-by-side direct and closure F1 across evaluation datasets."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def _idx(rows: List[Dict[str, Any]], key: str) -> Dict[str, float]:
        return {r["model_label"]: float(r.get(key) or 0.0) for r in rows}

    summary_rows = {
        dataset.label: dataset.summary.get("summary", []) for dataset in datasets
    }
    models = sorted({r["model_label"] for rows in summary_rows.values() for r in rows})
    direct_by_dataset = {
        label: _idx(rows, "fidelity_direct_f1") for label, rows in summary_rows.items()
    }
    closure_by_dataset = {
        label: _idx(rows, "fidelity_closure_f1_full")
        for label, rows in summary_rows.items()
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    width = min(0.25, 0.8 / max(1, len(datasets)))
    pos = list(range(len(models)))
    offsets = [(i - (len(datasets) - 1) / 2) * width for i in range(len(datasets))]

    for ax, title, metric_by_dataset in [
        (ax1, "Direct F1", direct_by_dataset),
        (ax2, "Coverage-aware Closure F1", closure_by_dataset),
    ]:
        for dataset, offset in zip(datasets, offsets):
            values = metric_by_dataset[dataset.label]
            ax.bar(
                [p + offset for p in pos],
                [values.get(m, 0.0) for m in models],
                width,
                label=dataset.label,
            )
        ax.set_xticks(pos)
        ax.set_xticklabels(models, rotation=25, ha="right")
        ax.set_ylim(0.0, 1.05)
        ax.set_ylabel("F1")
        ax.set_title(title)
        ax.legend(frameon=False, fontsize=8)

    fig.suptitle("Cross-dataset Performance Comparison")
    fig.tight_layout()
    out_path = out_dir / "cross_dataset_comparison.png"
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(str(out_path))


# ---------------------------------------------------------------------------
# Plot 5: First violation step distribution
# ---------------------------------------------------------------------------


def plot_first_violation_step_distribution(
    predictions_by_model: Dict[str, List[Dict[str, Any]]],
    out_dir: Path,
) -> None:
    """Density-normalised histogram of first_violation_step per model."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    has_data = False

    for model in sorted(predictions_by_model.keys()):
        steps = [
            int(p["verification"]["first_violation_step"])
            for p in predictions_by_model[model]
            if p.get("verification", {}).get("first_violation_step") is not None
        ]
        if steps:
            n_bins = max(5, len(set(steps)))
            ax.hist(steps, bins=n_bins, density=True, alpha=0.6, label=model)
            has_data = True

    if not has_data:
        plt.close(fig)
        return

    ax.set_xlabel("First violation step index")
    ax.set_ylabel("Density")
    ax.set_title("First Violation Step Distribution (Synthetic Dataset)")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    out_path = out_dir / "first_violation_step_distribution.png"
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(str(out_path))


# ---------------------------------------------------------------------------
# Plot 6: Model × category performance matrix
# ---------------------------------------------------------------------------


def plot_model_category_performance_matrix(
    summary: Dict[str, Any],
    out_dir: Path,
) -> None:
    """Heatmap of per-model per-category performance using category-appropriate metrics."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    category_rows = summary.get("category_breakdown", [])
    categories = [
        "linear_chain",
        "transitive_reasoning",
        "long_chain",
        "ambiguous",
        "contradiction",
    ]
    models = sorted({r["model_label"] for r in category_rows})

    # Metric selection per category
    def _cell_metric(cat: str, row: Dict[str, Any]) -> Optional[float]:
        if cat == "ambiguous":
            v = row.get("abstention_rate")
        elif cat == "contradiction":
            v = row.get("contradiction_detection_rate")
        else:
            v = row.get("closure_f1")
        return float(v) if v is not None else None

    matrix: List[List[float]] = []
    for cat in categories:
        row_vals: List[float] = []
        for model in models:
            cat_row = next(
                (
                    r
                    for r in category_rows
                    if r.get("category") == cat and r["model_label"] == model
                ),
                {},
            )
            val = _cell_metric(cat, cat_row)
            row_vals.append(val if val is not None else float("nan"))
        matrix.append(row_vals)

    fig_h = max(4, len(categories) * 0.8 + 1)
    fig_w = max(6, len(models) * 1.8 + 1)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    display = [[0.0 if math.isnan(v) else v for v in row] for row in matrix]
    im = ax.imshow(display, cmap="RdYlGn", vmin=0.0, vmax=1.0, aspect="auto")
    plt.colorbar(im, ax=ax)

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=30, ha="right", fontsize=9)
    ax.set_yticks(range(len(categories)))
    ax.set_yticklabels(categories, fontsize=9)
    ax.set_title("Model × Category Performance Matrix")

    for i, row_vals in enumerate(matrix):
        for j, val in enumerate(row_vals):
            label = f"{val:.2f}" if not math.isnan(val) else "N/A"
            ax.text(j, i, label, ha="center", va="center", fontsize=8)

    fig.tight_layout()
    out_path = out_dir / "model_category_performance_matrix.png"
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(str(out_path))


# ---------------------------------------------------------------------------
# Plot 7: Ambiguity discipline and contradiction detection
# ---------------------------------------------------------------------------


def plot_ambiguity_and_contradiction(
    summary: Dict[str, Any],
    out_dir: Path,
) -> None:
    """Stacked bar for ambiguity behaviour and bar for contradiction detection rate."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    summary_rows = summary.get("summary", [])
    models = [r["model_label"] for r in summary_rows]
    abstention = [
        float(r.get("ambiguity_abstention_rate") or 0.0) for r in summary_rows
    ]
    overcommit = [
        float(r.get("ambiguity_overcommitment_rate") or 0.0) for r in summary_rows
    ]
    contradiction = [
        float(r.get("contradiction_detection_rate") or 0.0) for r in summary_rows
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.bar(models, abstention, label="Abstention rate")
    ax1.bar(models, overcommit, bottom=abstention, label="Over-commitment rate")
    ax1.set_ylabel("Rate")
    ax1.set_ylim(0.0, 1.05)
    ax1.set_title("Ambiguity Discipline by Model")
    ax1.tick_params(axis="x", rotation=25)
    ax1.legend(frameon=False, fontsize=8)

    bars = ax2.bar(models, contradiction, color="#4C78A8")
    ax2.set_ylabel("Rate")
    ax2.set_ylim(0.0, 1.05)
    ax2.set_title("Contradiction Detection Rate by Model")
    ax2.tick_params(axis="x", rotation=25)
    for bar, val in zip(bars, contradiction):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.02,
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.tight_layout()
    out_path = out_dir / "ambiguity_discipline_and_contradiction.png"
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(str(out_path))


# ---------------------------------------------------------------------------
# Plot 8: RQ3 Spearman ρ heatmap
# ---------------------------------------------------------------------------


def plot_rq3_spearman_heatmap(
    datasets: Sequence[DatasetBundle],
    out_dir: Path,
    *,
    predictions_filename: str = "predictions.jsonl",
) -> None:
    """Spearman ρ heatmap of verifier signals vs task correctness (RQ3)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from src.analysis.correctness_correlation import batch_analyse

    run_spec: List[Tuple[Path, str, str]] = []
    for dataset in datasets:
        for run_dir in dataset.run_dirs:
            preds = run_dir / predictions_filename
            report_file = run_dir / "report.json"
            if preds.exists() and report_file.exists():
                report = _read_json(report_file)
                label = _model_label_from_report(report, dataset.manifest)
                run_spec.append((preds, label, dataset.label))

    if not run_spec:
        return

    rows = batch_analyse(run_spec)

    csv_path = out_dir / "correctness_correlation.csv"
    _write_csv(csv_path, rows)
    print(str(csv_path))

    signal_names = [
        "is_valid",
        "trace_grounded",
        "violation_count",
        "first_violation_step",
        "ltl_genuine_violation_count",
        "ltl_corroboration_count",
    ]
    row_labels = sorted({f"{r['model_label']} / {r['dataset']}" for r in rows})

    matrix: List[List[float]] = []
    significance: List[List[bool]] = []
    for row_label in row_labels:
        row_rhos: List[float] = []
        row_sig: List[bool] = []
        for sig in signal_names:
            match = next(
                (
                    r
                    for r in rows
                    if f"{r['model_label']} / {r['dataset']}" == row_label
                    and r["signal"] == sig
                ),
                None,
            )
            rho = float(match["spearman_rho"]) if match else float("nan")
            p = float(match["spearman_p"]) if match else float("nan")
            row_rhos.append(rho)
            row_sig.append(not math.isnan(p) and p < 0.05)
        matrix.append(row_rhos)
        significance.append(row_sig)

    fig_h = max(4, len(row_labels) * 0.8 + 1)
    fig_w = max(8, len(signal_names) * 2 + 1)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    display = [[0.0 if math.isnan(v) else v for v in row] for row in matrix]
    im = ax.imshow(display, cmap="coolwarm", vmin=-1.0, vmax=1.0, aspect="auto")
    plt.colorbar(im, ax=ax, label="Spearman ρ")

    ax.set_xticks(range(len(signal_names)))
    ax.set_xticklabels(signal_names, rotation=30, ha="right", fontsize=9)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=8)
    ax.set_title("RQ3: Verifier Signals vs Correctness (Spearman ρ)")

    for i, (row_rhos, row_sig) in enumerate(zip(matrix, significance)):
        for j, (val, sig) in enumerate(zip(row_rhos, row_sig)):
            label = f"{val:.2f}" if not math.isnan(val) else "N/A"
            if sig:
                label += "*"
            ax.text(j, i, label, ha="center", va="center", fontsize=8)

    fig.tight_layout()
    out_path = out_dir / "rq3_spearman_heatmap.png"
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(str(out_path))


# ---------------------------------------------------------------------------
# Plot 9: Task accuracy by verifier verdict
# ---------------------------------------------------------------------------


def plot_accuracy_by_verifier_verdict(
    predictions_by_model: Dict[str, List[Dict[str, Any]]],
    out_dir: Path,
) -> None:
    """Paired bars of direct-edge accuracy split by is_valid verdict per model."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    models = sorted(predictions_by_model.keys())
    valid_accs, invalid_accs, valid_counts, invalid_counts = [], [], [], []

    for model in models:
        gold_preds = [p for p in predictions_by_model[model] if p.get("gold_relations")]
        valid_preds = [
            p for p in gold_preds if p.get("verification", {}).get("is_valid")
        ]
        invalid_preds = [
            p for p in gold_preds if not p.get("verification", {}).get("is_valid")
        ]

        def _acc(lst: List[Dict[str, Any]]) -> float:
            if not lst:
                return 0.0
            return sum(
                1
                for p in lst
                if p.get("score", {}).get("direct", {}).get("correct", 0) > 0
            ) / len(lst)

        valid_accs.append(_acc(valid_preds))
        invalid_accs.append(_acc(invalid_preds))
        valid_counts.append(len(valid_preds))
        invalid_counts.append(len(invalid_preds))

    fig, ax = plt.subplots(figsize=(max(8, len(models) * 2.2), 5))
    width = 0.35
    pos = list(range(len(models)))
    bars1 = ax.bar(
        [p - width / 2 for p in pos],
        valid_accs,
        width,
        label="is_valid=True",
        color="#59A14F",
    )
    bars2 = ax.bar(
        [p + width / 2 for p in pos],
        invalid_accs,
        width,
        label="is_valid=False",
        color="#E15759",
    )

    for bar, count in zip(bars1, valid_counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"n={count}",
            ha="center",
            va="bottom",
            fontsize=7,
        )
    for bar, count in zip(bars2, invalid_counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"n={count}",
            ha="center",
            va="bottom",
            fontsize=7,
        )

    ax.set_xticks(pos)
    ax.set_xticklabels(models, rotation=25, ha="right")
    ax.set_ylabel("Direct-edge accuracy")
    ax.set_ylim(0.0, 1.2)
    ax.set_title("Task Accuracy by Verifier Verdict (Gold-bearing Tasks)")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    out_path = out_dir / "accuracy_by_verifier_verdict.png"
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(str(out_path))


# ---------------------------------------------------------------------------
# Plot 10: Failure scope contribution
# ---------------------------------------------------------------------------


def plot_failure_scope_contribution(
    summary: Dict[str, Any],
    out_dir: Path,
) -> None:
    """Stacked bar of cumulative affected_task_rate per failure scope per model."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    failure_rows = summary.get("failure_breakdown", [])
    summary_rows = summary.get("summary", [])
    models = [r["model_label"] for r in summary_rows]

    scope_order = ["parse", "transport", "verification", "ltl_formula"]
    scope_colors = {
        "parse": "#E15759",
        "transport": "#F28E2B",
        "verification": "#4C78A8",
        "ltl_formula": "#59A14F",
    }

    stacks: Dict[str, List[float]] = {
        scope: [
            sum(
                r.get("affected_task_rate", 0.0)
                for r in failure_rows
                if r["model_label"] == m and r["failure_scope"] == scope
            )
            for m in models
        ]
        for scope in scope_order
    }

    fig, ax = plt.subplots(figsize=(max(8, len(models) * 2), 5))
    bottoms = [0.0] * len(models)
    for scope in scope_order:
        vals = stacks[scope]
        ax.bar(models, vals, bottom=bottoms, label=scope, color=scope_colors[scope])
        bottoms = [b + v for b, v in zip(bottoms, vals)]

    ax.set_ylabel("Cumulative affected task rate")
    ax.set_title("Failure Scope Contribution by Model")
    ax.tick_params(axis="x", rotation=25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    out_path = out_dir / "failure_scope_contribution.png"
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(str(out_path))


# ---------------------------------------------------------------------------
# Plot 11: Genuine vs corroborating LTL incidence
# ---------------------------------------------------------------------------


def plot_genuine_ltl_violation_incidence(
    summary_df: Sequence[Dict[str, Any]],
    output_dir: Path,
) -> None:
    """Grouped bars for genuine and invariant-corroborating LTL rates."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not summary_df:
        return

    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    models = [str(row.get("model_label", "unknown")) for row in summary_df]
    genuine = [
        float(row.get("ltl_genuine_violation_rate") or 0.0) for row in summary_df
    ]
    corroborating = [
        float(row.get("ltl_invariant_corroboration_rate") or 0.0) for row in summary_df
    ]

    fig, ax = plt.subplots(figsize=(max(8, len(models) * 2.0), 5))
    width = 0.35
    pos = list(range(len(models)))
    ax.bar(
        [p - width / 2 for p in pos],
        genuine,
        width,
        label="Genuine LTL (F/G trace-level)",
        color="#4C78A8",
    )
    ax.bar(
        [p + width / 2 for p in pos],
        corroborating,
        width,
        label="Invariant-corroborating LTL",
        color="#9D9D9D",
    )
    ax.set_xticks(pos)
    ax.set_xticklabels(models, rotation=25, ha="right")
    ax.set_ylabel("Violation rate")
    ax.set_ylim(0.0, 1.05)
    ax.set_title("Genuine vs. Corroborating LTL Violation Rates")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    out_path = plots_dir / "genuine_ltl_incidence.png"
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(str(out_path))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate supplementary analysis plots from existing run outputs."
    )
    parser.add_argument(
        "--canonical-dir",
        default="outputs/runs/canonical_full",
        help="Directory containing canonical (synthetic) run subdirectories.",
    )
    parser.add_argument(
        "--tempeval-dir",
        default="outputs/runs/tempeval_full",
        help="Directory containing TempEval-3 run subdirectories.",
    )
    parser.add_argument(
        "--maven-ere-dir",
        default="outputs/runs/maven_ere_full",
        help="Directory containing MAVEN-ERE run subdirectories.",
    )
    parser.add_argument(
        "--canonical-analysis",
        default="outputs/analysis/canonical_full",
        help="Analysis output directory for canonical runs (must contain summary.json).",
    )
    parser.add_argument(
        "--tempeval-analysis",
        default="outputs/analysis/tempeval_full",
        help="Analysis output directory for TempEval-3 runs (must contain summary.json).",
    )
    parser.add_argument(
        "--maven-ere-analysis",
        default="outputs/analysis/maven_ere_full",
        help="Analysis output directory for MAVEN-ERE runs (must contain summary.json).",
    )
    parser.add_argument(
        "--out",
        default="outputs/analysis/supplementary_plots",
        help="Output directory for supplementary plots.",
    )
    parser.add_argument(
        "--predictions-file",
        default="predictions.jsonl",
        help="Prediction JSONL filename inside each run directory.",
    )
    args = parser.parse_args()

    canonical_dir = Path(args.canonical_dir)
    tempeval_dir = Path(args.tempeval_dir)
    maven_ere_dir = Path(args.maven_ere_dir)
    canonical_analysis = Path(args.canonical_analysis)
    tempeval_analysis = Path(args.tempeval_analysis)
    maven_ere_analysis = Path(args.maven_ere_analysis)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    canonical_summary = _read_json(canonical_analysis / "summary.json")
    tempeval_summary = _read_json(tempeval_analysis / "summary.json")
    maven_ere_summary = _read_json(maven_ere_analysis / "summary.json")

    canonical_run_dirs = _find_run_dirs(
        canonical_dir,
        predictions_filename=args.predictions_file,
    )
    tempeval_run_dirs = _find_run_dirs(
        tempeval_dir,
        predictions_filename=args.predictions_file,
    )
    maven_ere_run_dirs = _find_run_dirs(
        maven_ere_dir,
        predictions_filename=args.predictions_file,
    )

    canonical_manifest = _load_manifest(canonical_dir)
    tempeval_manifest = _load_manifest(tempeval_dir)
    maven_ere_manifest = _load_manifest(maven_ere_dir)

    datasets = [
        DatasetBundle(
            key="synthetic",
            label="Synthetic",
            summary=canonical_summary,
            run_dirs=canonical_run_dirs,
            manifest=canonical_manifest,
        ),
        DatasetBundle(
            key="tempeval",
            label="TempEval-3",
            summary=tempeval_summary,
            run_dirs=tempeval_run_dirs,
            manifest=tempeval_manifest,
        ),
        DatasetBundle(
            key="maven_ere",
            label="MAVEN-ERE",
            summary=maven_ere_summary,
            run_dirs=maven_ere_run_dirs,
            manifest=maven_ere_manifest,
        ),
    ]

    canonical_predictions_by_model = _load_predictions_by_model(
        canonical_run_dirs,
        canonical_manifest,
        predictions_filename=args.predictions_file,
    )

    n_plots = 0

    plot_violation_type_model_heatmap(canonical_summary, out_dir)
    n_plots += 1

    plot_verifier_screening_signal(canonical_predictions_by_model, out_dir)
    n_plots += 1

    plot_direct_vs_closure_f1_by_category(canonical_summary, out_dir)
    n_plots += 1

    plot_cross_dataset_comparison(datasets, out_dir)
    n_plots += 1

    plot_first_violation_step_distribution(canonical_predictions_by_model, out_dir)
    n_plots += 1

    plot_model_category_performance_matrix(canonical_summary, out_dir)
    n_plots += 1

    plot_ambiguity_and_contradiction(canonical_summary, out_dir)
    n_plots += 1

    plot_rq3_spearman_heatmap(
        datasets,
        out_dir,
        predictions_filename=args.predictions_file,
    )
    n_plots += 1

    plot_accuracy_by_verifier_verdict(canonical_predictions_by_model, out_dir)
    n_plots += 1

    plot_failure_scope_contribution(canonical_summary, out_dir)
    n_plots += 1

    plot_genuine_ltl_violation_incidence(canonical_summary.get("summary", []), out_dir)
    n_plots += 1

    print(f"Generated {n_plots} plots to {out_dir}")


if __name__ == "__main__":
    main()
