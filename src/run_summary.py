from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


@dataclass(frozen=True)
class LoadedRun:
    run_dir: Path
    report: Dict[str, Any]
    predictions: List[Dict[str, Any]]
    manifest_meta: Dict[str, Any]

    @property
    def run_id(self) -> str:
        return str(self.report["run_id"])

    @property
    def label(self) -> str:
        return str(
            self.manifest_meta.get("model_label")
            or self.report.get("model_metadata", {}).get("model")
            or self.run_id
        )


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


def _write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def _load_manifest(path: str | Path | None) -> Dict[str, Dict[str, Any]]:
    if path is None:
        return {}
    raw = _read_json(Path(path))
    if isinstance(raw, dict) and isinstance(raw.get("runs"), dict):
        return {str(run_id): dict(meta) for run_id, meta in raw["runs"].items()}
    if isinstance(raw, dict):
        return {str(run_id): dict(meta) for run_id, meta in raw.items()}
    raise ValueError("Run manifest must be an object or an object containing a 'runs' mapping.")


def _difficulty_bucket(*, num_events: int, gold_relation_count: int) -> str:
    if gold_relation_count == 0:
        return "empty_gold"
    if gold_relation_count <= 2 and num_events <= 3:
        return "low_complexity"
    if gold_relation_count <= 4 and num_events <= 4:
        return "medium_complexity"
    return "high_complexity"


def _aggregate_prf_from_rows(rows: Sequence[Dict[str, Any]], *, metric_key: str) -> Dict[str, float]:
    correct = 0
    pred_total = 0
    gold_total = 0
    for row in rows:
        score = row.get("score", {}).get(metric_key, {})
        correct += int(score.get("correct", 0))
        pred_total += int(score.get("pred_total", 0))
        gold_total += int(score.get("gold_total", 0))
    precision = (correct / pred_total) if pred_total else 0.0
    recall = (correct / gold_total) if gold_total else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "correct": correct,
        "pred_total": pred_total,
        "gold_total": gold_total,
    }


def load_runs(run_dirs: Sequence[str | Path], *, manifest_path: str | Path | None = None) -> List[LoadedRun]:
    manifest = _load_manifest(manifest_path)
    loaded: List[LoadedRun] = []
    for run_dir_like in run_dirs:
        run_dir = Path(run_dir_like)
        report = _read_json(run_dir / "report.json")
        predictions = _read_jsonl(run_dir / "predictions.jsonl")
        loaded.append(
            LoadedRun(
                run_dir=run_dir,
                report=report,
                predictions=predictions,
                manifest_meta=dict(manifest.get(str(report["run_id"]), {})),
            )
        )
    return loaded


def _run_row(run: LoadedRun) -> Dict[str, Any]:
    report = run.report
    direct = report["metrics_expected_valid_only"]["direct"]
    closure = report["metrics_expected_valid_only"]["closure"]
    overcommitment = report["overcommitment"]
    summary = {
        "run_id": report["run_id"],
        "model_label": run.label,
        "model": report["model_metadata"].get("model", ""),
        "family": run.manifest_meta.get("family", ""),
        "size_bucket": run.manifest_meta.get("size_bucket", run.manifest_meta.get("size", "")),
        "reasoning_tuned": run.manifest_meta.get("reasoning_tuned", ""),
        "group": run.manifest_meta.get("group", ""),
        "dataset_version": report["dataset"]["dataset_version"],
        "pred_source": report["pred_source"],
        "num_tasks": report["num_tasks"],
        "num_failures": report["num_failures"],
        "repair_hit_count": report.get("repair_hit_count", 0),
        "repair_hit_rate": report.get("repair_hit_rate", 0.0),
        "parse_success_rate": report.get("parse_success_rate", 0.0),
        "conditional_validity_rate": report.get("conditional_validity_rate"),
        "validity_rate": report.get("validity_rate", 0.0),
        "direct_precision": direct["precision"],
        "direct_recall": direct["recall"],
        "direct_f1": direct["f1"],
        "closure_precision": closure["precision"],
        "closure_recall": closure["recall"],
        "closure_f1": closure["f1"],
        "closure_minus_direct_f1": closure["f1"] - direct["f1"],
        "closure_preservation_rate": _closure_preservation_rate(run.predictions),
        "overcommitment_rate": overcommitment["task_overcommit_rate"],
        "avg_overcommit_edges_per_gold_empty_task": overcommitment["avg_overcommit_edges_per_gold_empty_task"],
    }
    return summary


def _closure_preservation_rate(predictions: Sequence[Dict[str, Any]]) -> float:
    if not predictions:
        return 0.0
    count = sum(1 for row in predictions if row.get("score", {}).get("preserves_ordering_closure"))
    return count / len(predictions)


def _group_tasks_by_dimension(
    run: LoadedRun,
    *,
    dimension: str,
) -> List[Dict[str, Any]]:
    parsed_by_key: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    failures_by_key: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for row in run.predictions:
        if dimension == "category":
            key = str(row.get("category", "unknown"))
        else:
            key = _difficulty_bucket(
                num_events=len(row.get("events", [])),
                gold_relation_count=len(row.get("gold_relations", [])),
            )
        parsed_by_key[key].append(row)

    for failure in run.report.get("failures", []):
        if dimension == "category":
            key = str(failure.get("task_category", "unknown"))
        else:
            key = _difficulty_bucket(
                num_events=int(failure.get("num_events", 0)),
                gold_relation_count=int(failure.get("gold_relation_count", 0)),
            )
        failures_by_key[key].append(failure)

    all_keys = sorted(set(parsed_by_key) | set(failures_by_key))
    rows: List[Dict[str, Any]] = []
    for key in all_keys:
        parsed_rows = parsed_by_key.get(key, [])
        failed_rows = failures_by_key.get(key, [])
        expected_valid_rows = [row for row in parsed_rows if row.get("expected_valid", True)]
        valid_rows = [row for row in parsed_rows if row.get("verification", {}).get("is_valid")]
        overcommit_rows = [
            row
            for row in parsed_rows
            if row.get("score", {}).get("has_overcommitment")
        ]
        rows.append(
            {
                "run_id": run.run_id,
                "model_label": run.label,
                dimension: key,
                "num_tasks": len(parsed_rows) + len(failed_rows),
                "num_parsed": len(parsed_rows),
                "num_failures": len(failed_rows),
                "parse_success_rate": (
                    len(parsed_rows) / (len(parsed_rows) + len(failed_rows))
                    if (len(parsed_rows) + len(failed_rows))
                    else 0.0
                ),
                "conditional_validity_rate": (
                    len(valid_rows) / len(parsed_rows) if parsed_rows else None
                ),
                "direct_f1": _aggregate_prf_from_rows(expected_valid_rows, metric_key="direct")["f1"],
                "closure_f1": _aggregate_prf_from_rows(expected_valid_rows, metric_key="closure")["f1"],
                "closure_preservation_rate": _closure_preservation_rate(parsed_rows),
                "overcommitment_rate": (
                    len(overcommit_rows) / len(parsed_rows) if parsed_rows else 0.0
                ),
            }
        )
    return rows


def _failure_rows(run: LoadedRun) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for category, count in sorted(run.report.get("parse_failure_counts", {}).items()):
        rows.append(
            {
                "run_id": run.run_id,
                "model_label": run.label,
                "failure_scope": "parse",
                "failure_type": category,
                "count": count,
            }
        )
    for category, count in sorted(run.report.get("violation_counts", {}).items()):
        rows.append(
            {
                "run_id": run.run_id,
                "model_label": run.label,
                "failure_scope": "verification",
                "failure_type": category,
                "count": count,
            }
        )
    for category, count in sorted(run.report.get("formula_violation_counts", {}).items()):
        rows.append(
            {
                "run_id": run.run_id,
                "model_label": run.label,
                "failure_scope": "ltl_formula",
                "failure_type": category,
                "count": count,
            }
        )
    return rows


def _counterexample_sections(run: LoadedRun, *, limit: int = 3) -> List[str]:
    invalid_rows = [
        row for row in run.predictions
        if (not row.get("verification", {}).get("is_valid"))
        or row.get("verification", {}).get("formula_violations")
    ]
    sections: List[str] = []
    for row in invalid_rows[:limit]:
        verification = row.get("verification", {})
        violation_types = [violation.get("type", "") for violation in verification.get("violations", [])]
        formula_types = [
            violation.get("type", "") for violation in verification.get("formula_violations", [])
        ]
        sections.append(
            "\n".join(
                [
                    f"### {run.label} :: {row.get('id')}",
                    f"- Category: `{row.get('category')}`",
                    f"- First violation step: `{verification.get('first_violation_step')}`",
                    f"- Invariant violations: `{', '.join(violation_types) or 'none'}`",
                    f"- LTL violations: `{', '.join(formula_types) or 'none'}`",
                    f"- Question: {row.get('question')}",
                ]
            )
        )
    return sections


def _plot_bar(
    path: Path,
    *,
    labels: Sequence[str],
    values: Sequence[float],
    title: str,
    ylabel: str,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_grouped_bars(
    path: Path,
    *,
    labels: Sequence[str],
    series: Mapping[str, Sequence[float]],
    title: str,
    ylabel: str,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    positions = list(range(len(labels)))
    width = 0.8 / max(len(series), 1)
    for index, (name, values) in enumerate(series.items()):
        offsets = [position + (index - (len(series) - 1) / 2) * width for position in positions]
        ax.bar(offsets, values, width=width, label=name)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=25)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_scatter(
    path: Path,
    *,
    x_values: Sequence[float],
    y_values: Sequence[float],
    labels: Sequence[str],
    title: str,
    xlabel: str,
    ylabel: str,
) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(x_values, y_values)
    for x_value, y_value, label in zip(x_values, y_values, labels):
        ax.annotate(label, (x_value, y_value))
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_stacked_bars(
    path: Path,
    *,
    labels: Sequence[str],
    stacks: Mapping[str, Sequence[int]],
    title: str,
    ylabel: str,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bottoms = [0] * len(labels)
    for name, values in stacks.items():
        ax.bar(labels, values, bottom=bottoms, label=name)
        bottoms = [left + right for left, right in zip(bottoms, values)]
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_first_violation_histogram(path: Path, runs: Sequence[LoadedRun]) -> None:
    all_steps: List[int] = []
    for run in runs:
        for step, count in run.report.get("first_violation_step_histogram", {}).items():
            all_steps.extend([int(step)] * int(count))
    fig, ax = plt.subplots(figsize=(7, 4))
    if all_steps:
        bins = list(range(0, max(all_steps) + 2))
        ax.hist(all_steps, bins=bins, align="left", rwidth=0.8)
    ax.set_title("First Violation Step Distribution")
    ax.set_xlabel("First violation step")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _generate_plots(
    out_dir: Path,
    summary_rows: Sequence[Dict[str, Any]],
    category_rows: Sequence[Dict[str, Any]],
    failure_rows: Sequence[Dict[str, Any]],
    runs: Sequence[LoadedRun],
) -> None:
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    labels = [row["model_label"] for row in summary_rows]
    _plot_bar(
        plots_dir / "parse_success_rate.png",
        labels=labels,
        values=[float(row["parse_success_rate"]) for row in summary_rows],
        title="Parse Success Rate by Model",
        ylabel="Rate",
    )
    _plot_bar(
        plots_dir / "conditional_validity_rate.png",
        labels=labels,
        values=[float(row["conditional_validity_rate"] or 0.0) for row in summary_rows],
        title="Conditional Validity Rate by Model",
        ylabel="Rate",
    )
    _plot_grouped_bars(
        plots_dir / "direct_vs_closure_f1.png",
        labels=labels,
        series={
            "direct_f1": [float(row["direct_f1"]) for row in summary_rows],
            "closure_f1": [float(row["closure_f1"]) for row in summary_rows],
        },
        title="Direct vs Closure F1",
        ylabel="F1",
    )
    ambiguous_rows = [row for row in category_rows if row.get("category") == "ambiguous"]
    if ambiguous_rows:
        _plot_bar(
            plots_dir / "ambiguous_overcommitment_rate.png",
            labels=[row["model_label"] for row in ambiguous_rows],
            values=[float(row["overcommitment_rate"]) for row in ambiguous_rows],
            title="Overcommitment Rate on Ambiguous Tasks",
            ylabel="Rate",
        )
    category_names = sorted({row["category"] for row in category_rows if "category" in row})
    if category_names:
        series: Dict[str, List[float]] = {}
        for label in labels:
            label_rows = {
                row["category"]: row
                for row in category_rows
                if row["model_label"] == label and "category" in row
            }
            series[label] = [float(label_rows.get(category, {}).get("closure_f1", 0.0)) for category in category_names]
        _plot_grouped_bars(
            plots_dir / "category_closure_f1.png",
            labels=category_names,
            series=series,
            title="Category-wise Closure F1",
            ylabel="F1",
        )
    parse_failure_types = sorted(
        {row["failure_type"] for row in failure_rows if row["failure_scope"] == "parse"}
    )
    if parse_failure_types:
        stacks = {
            failure_type: [
                next(
                    (
                        int(row["count"])
                        for row in failure_rows
                        if row["failure_scope"] == "parse"
                        and row["failure_type"] == failure_type
                        and row["model_label"] == label
                    ),
                    0,
                )
                for label in labels
            ]
            for failure_type in parse_failure_types
        }
        _plot_stacked_bars(
            plots_dir / "parse_failure_taxonomy.png",
            labels=labels,
            stacks=stacks,
            title="Parse Failure Taxonomy",
            ylabel="Count",
        )
    violation_types = sorted(
        {
            row["failure_type"]
            for row in failure_rows
            if row["failure_scope"] in {"verification", "ltl_formula"}
        }
    )
    if violation_types:
        stacks = {
            violation_type: [
                sum(
                    int(row["count"])
                    for row in failure_rows
                    if row["failure_scope"] in {"verification", "ltl_formula"}
                    and row["failure_type"] == violation_type
                    and row["model_label"] == label
                )
                for label in labels
            ]
            for violation_type in violation_types
        }
        _plot_stacked_bars(
            plots_dir / "verification_violation_taxonomy.png",
            labels=labels,
            stacks=stacks,
            title="Verification and Formula Violation Taxonomy",
            ylabel="Count",
        )
    _plot_scatter(
        plots_dir / "direct_vs_closure_scatter.png",
        x_values=[float(row["direct_f1"]) for row in summary_rows],
        y_values=[float(row["closure_f1"]) for row in summary_rows],
        labels=labels,
        title="Direct F1 vs Closure F1",
        xlabel="Direct F1",
        ylabel="Closure F1",
    )
    _plot_scatter(
        plots_dir / "parse_success_vs_closure_scatter.png",
        x_values=[float(row["parse_success_rate"]) for row in summary_rows],
        y_values=[float(row["closure_f1"]) for row in summary_rows],
        labels=labels,
        title="Parse Success Rate vs Closure F1",
        xlabel="Parse success rate",
        ylabel="Closure F1",
    )
    _plot_first_violation_histogram(plots_dir / "first_violation_histogram.png", runs)


def summarise_runs(
    run_dirs: Sequence[str | Path],
    *,
    out_dir: str | Path,
    manifest_path: str | Path | None = None,
) -> Dict[str, Any]:
    runs = load_runs(run_dirs, manifest_path=manifest_path)
    summary_rows = [_run_row(run) for run in runs]
    category_rows = [row for run in runs for row in _group_tasks_by_dimension(run, dimension="category")]
    difficulty_rows = [row for run in runs for row in _group_tasks_by_dimension(run, dimension="difficulty")]
    failure_rows = [row for run in runs for row in _failure_rows(run)]

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    _write_csv(out_path / "summary.csv", summary_rows)
    _write_csv(out_path / "category_breakdown.csv", category_rows)
    _write_csv(out_path / "difficulty_breakdown.csv", difficulty_rows)
    _write_csv(out_path / "failure_breakdown.csv", failure_rows)
    _write_json(
        out_path / "summary.json",
        {
            "summary": summary_rows,
            "category_breakdown": category_rows,
            "difficulty_breakdown": difficulty_rows,
            "failure_breakdown": failure_rows,
        },
    )

    counterexample_text = ["# Counterexamples", ""]
    for run in runs:
        sections = _counterexample_sections(run)
        if sections:
            counterexample_text.extend(sections)
            counterexample_text.append("")
    (out_path / "counterexamples.md").write_text("\n".join(counterexample_text), encoding="utf-8")

    best_parse = max(summary_rows, key=lambda row: float(row["parse_success_rate"])) if summary_rows else None
    best_closure = max(summary_rows, key=lambda row: float(row["closure_f1"])) if summary_rows else None
    largest_gap = max(summary_rows, key=lambda row: float(row["closure_minus_direct_f1"])) if summary_rows else None
    report_lines = [
        "# Temporal Verification Evaluation Summary",
        "",
        f"- Runs analysed: `{len(summary_rows)}`",
    ]
    if best_parse is not None:
        report_lines.append(
            f"- Highest parse success: `{best_parse['model_label']}` at `{best_parse['parse_success_rate']:.3f}`"
        )
    if best_closure is not None:
        report_lines.append(
            f"- Highest closure F1: `{best_closure['model_label']}` at `{best_closure['closure_f1']:.3f}`"
        )
    if largest_gap is not None:
        report_lines.append(
            f"- Largest closure-direct gap: `{largest_gap['model_label']}` at `{largest_gap['closure_minus_direct_f1']:.3f}`"
        )
    report_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Treat parse robustness, formal validity, direct relational fidelity, closure reasoning, and overcommitment as separate capabilities.",
            "- Use category and difficulty breakdowns to explain where apparent model strength is coming from.",
            "- Use `counterexamples.md` for supervisor-facing examples of step-localised failures.",
        ]
    )
    (out_path / "report.md").write_text("\n".join(report_lines), encoding="utf-8")

    _generate_plots(out_path, summary_rows, category_rows, failure_rows, runs)
    return {
        "summary": summary_rows,
        "category_breakdown": category_rows,
        "difficulty_breakdown": difficulty_rows,
        "failure_breakdown": failure_rows,
    }
