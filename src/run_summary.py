from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BOOTSTRAP_ITERATIONS = 500
BOOTSTRAP_SEED = 7


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


def _bootstrap_ci(
    items: Sequence[Any],
    *,
    metric_fn: Callable[[Sequence[Any]], Optional[float]],
    iterations: int = BOOTSTRAP_ITERATIONS,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[Optional[float], Optional[float]]:
    if not items:
        return (None, None)
    rng = random.Random(seed)
    values: List[float] = []
    for _ in range(iterations):
        sample = [items[rng.randrange(len(items))] for _ in range(len(items))]
        metric = metric_fn(sample)
        if metric is not None:
            values.append(float(metric))
    if not values:
        return (None, None)
    values.sort()
    lower_index = int(0.025 * (len(values) - 1))
    upper_index = int(0.975 * (len(values) - 1))
    return (values[lower_index], values[upper_index])


def _combine_task_entries(run: LoadedRun) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for row in run.predictions:
        entries.append(
            {
                "id": row.get("id"),
                "category": row.get("category", "unknown"),
                "parsed": True,
                "prediction": row,
                "failure": None,
                "num_events": len(row.get("events", [])),
                "gold_relation_count": len(row.get("gold_relations", [])),
                "expected_valid": bool(row.get("expected_valid", True)),
            }
        )
    for failure in run.report.get("failures", []):
        entries.append(
            {
                "id": failure.get("id"),
                "category": failure.get("task_category", "unknown"),
                "parsed": False,
                "prediction": None,
                "failure": failure,
                "num_events": int(failure.get("num_events", 0)),
                "gold_relation_count": int(failure.get("gold_relation_count", 0)),
                "expected_valid": bool(failure.get("expected_valid", True)),
            }
        )
    return entries


def _expected_valid_parsed_rows(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [row for row in rows if row.get("expected_valid", True)]


def _trace_grounded_rate(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if not rows:
        return None
    def is_grounded(row: Dict[str, Any]) -> bool:
        verification = row.get("verification", {})
        if "trace_grounded" in verification:
            return bool(verification.get("trace_grounded"))
        violation_types = {item.get("type") for item in verification.get("violations", [])}
        return not bool({"unsupported_reasoning_step", "unsupported_reasoning_reference"} & violation_types)
    return sum(1 for row in rows if is_grounded(row)) / len(rows)


def _closure_preservation_rate(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if not rows:
        return None
    return sum(1 for row in rows if row.get("score", {}).get("preserves_ordering_closure")) / len(rows)


def _abstention_rate(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if not rows:
        return None
    return sum(1 for row in rows if row.get("score", {}).get("abstained")) / len(rows)


def _overcommitment_rate(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if not rows:
        return None
    return sum(1 for row in rows if row.get("score", {}).get("has_overcommitment")) / len(rows)


def _invalidity_rate(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if not rows:
        return None
    return sum(1 for row in rows if not row.get("verification", {}).get("is_valid")) / len(rows)


def _average_first_violation_step(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    steps = [
        int(row.get("verification", {}).get("first_violation_step"))
        for row in rows
        if row.get("verification", {}).get("first_violation_step") is not None
    ]
    if not steps:
        return None
    return mean(steps)


def _contradiction_detected(row: Dict[str, Any]) -> bool:
    verification = row.get("verification", {})
    violation_types = {item.get("type") for item in verification.get("violations", [])}
    formula_types = {item.get("type") for item in verification.get("formula_violations", [])}
    return bool(
        {"contradiction", "cycle", "temporal_inconsistency"} & violation_types
        or {"ltl_contradiction", "ltl_temporal_inconsistency"} & formula_types
    )


def _contradiction_detection_rate(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if not rows:
        return None
    return sum(1 for row in rows if _contradiction_detected(row)) / len(rows)


def _metric_or_none(rows: Sequence[Dict[str, Any]], *, metric_key: str) -> Optional[float]:
    if not rows:
        return None
    aggregate = _aggregate_prf_from_rows(rows, metric_key=metric_key)
    if aggregate["gold_total"] == 0:
        return None
    return aggregate["f1"]


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
    parsed_rows = list(run.predictions)
    combined_entries = _combine_task_entries(run)
    expected_valid_parsed_rows = _expected_valid_parsed_rows(parsed_rows)
    ambiguous_rows = [row for row in parsed_rows if row.get("category") == "ambiguous"]
    contradiction_rows = [row for row in parsed_rows if row.get("category") == "contradiction"]

    direct = report["metrics_expected_valid_only"]["direct"]
    closure = report["metrics_expected_valid_only"]["closure"]
    parse_ci_low, parse_ci_high = _bootstrap_ci(
        combined_entries,
        metric_fn=lambda sample: sum(1 for item in sample if item["parsed"]) / len(sample),
    )
    conditional_ci_low, conditional_ci_high = _bootstrap_ci(
        parsed_rows,
        metric_fn=lambda sample: sum(
            1 for row in sample if row.get("verification", {}).get("is_valid")
        ) / len(sample) if sample else None,
    )
    direct_ci_low, direct_ci_high = _bootstrap_ci(
        expected_valid_parsed_rows,
        metric_fn=lambda sample: _metric_or_none(sample, metric_key="direct"),
    )
    closure_ci_low, closure_ci_high = _bootstrap_ci(
        expected_valid_parsed_rows,
        metric_fn=lambda sample: _metric_or_none(sample, metric_key="closure"),
    )

    return {
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
        "parse_success_count": len(parsed_rows),
        "repair_hit_count": report.get("repair_hit_count", 0),
        "repair_hit_rate": report.get("repair_hit_rate", 0.0),
        "parse_success_rate": report.get("parse_success_rate", 0.0),
        "parse_success_ci_low": parse_ci_low,
        "parse_success_ci_high": parse_ci_high,
        "transport_failure_rate": (
            sum(int(value) for value in report.get("transport_failure_counts", {}).values())
            / max(int(report.get("num_tasks", 0)), 1)
        ),
        "conditional_validity_rate": report.get("conditional_validity_rate"),
        "conditional_validity_ci_low": conditional_ci_low,
        "conditional_validity_ci_high": conditional_ci_high,
        "conditional_trace_grounding_rate": (
            report.get("conditional_trace_grounding_rate")
            if report.get("conditional_trace_grounding_rate") is not None
            else _trace_grounded_rate(parsed_rows)
        ),
        "validity_rate": report.get("validity_rate", 0.0),
        "parsed_expected_valid_tasks": len(expected_valid_parsed_rows),
        "direct_precision": direct["precision"],
        "direct_recall": direct["recall"],
        "direct_f1": direct["f1"],
        "direct_f1_ci_low": direct_ci_low,
        "direct_f1_ci_high": direct_ci_high,
        "closure_precision": closure["precision"],
        "closure_recall": closure["recall"],
        "closure_f1": closure["f1"],
        "closure_f1_ci_low": closure_ci_low,
        "closure_f1_ci_high": closure_ci_high,
        "closure_minus_direct_f1": closure["f1"] - direct["f1"],
        "closure_preservation_rate": _closure_preservation_rate(expected_valid_parsed_rows),
        "ambiguity_abstention_rate": _abstention_rate(ambiguous_rows),
        "ambiguity_overcommitment_rate": _overcommitment_rate(ambiguous_rows),
        "contradiction_detection_rate": _contradiction_detection_rate(contradiction_rows),
        "contradiction_invalidity_rate": _invalidity_rate(contradiction_rows),
        "avg_first_violation_step": _average_first_violation_step(parsed_rows),
        "screening_warning": report["num_tasks"] <= 25,
    }


def _group_tasks_by_dimension(
    run: LoadedRun,
    *,
    dimension: str,
) -> List[Dict[str, Any]]:
    parsed_by_key: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    failures_by_key: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for row in run.predictions:
        key = (
            str(row.get("category", "unknown"))
            if dimension == "category"
            else _difficulty_bucket(
                num_events=len(row.get("events", [])),
                gold_relation_count=len(row.get("gold_relations", [])),
            )
        )
        parsed_by_key[key].append(row)

    for failure in run.report.get("failures", []):
        key = (
            str(failure.get("task_category", "unknown"))
            if dimension == "category"
            else _difficulty_bucket(
                num_events=int(failure.get("num_events", 0)),
                gold_relation_count=int(failure.get("gold_relation_count", 0)),
            )
        )
        failures_by_key[key].append(failure)

    all_keys = sorted(set(parsed_by_key) | set(failures_by_key))
    rows: List[Dict[str, Any]] = []
    for key in all_keys:
        parsed_rows = parsed_by_key.get(key, [])
        failed_rows = failures_by_key.get(key, [])
        expected_valid_rows = _expected_valid_parsed_rows(parsed_rows)
        gold_bearing_rows = [
            row for row in expected_valid_rows
            if len(row.get("gold_relations", [])) > 0
        ]
        rows.append(
            {
                "run_id": run.run_id,
                "model_label": run.label,
                dimension: key,
                "num_tasks": len(parsed_rows) + len(failed_rows),
                "num_parsed": len(parsed_rows),
                "num_failures": len(failed_rows),
                "expected_valid_parsed_tasks": len(expected_valid_rows),
                "gold_bearing_parsed_tasks": len(gold_bearing_rows),
                "parse_success_rate": (
                    len(parsed_rows) / (len(parsed_rows) + len(failed_rows))
                    if (len(parsed_rows) + len(failed_rows))
                    else 0.0
                ),
                "conditional_validity_rate": (
                    sum(1 for row in parsed_rows if row.get("verification", {}).get("is_valid")) / len(parsed_rows)
                    if parsed_rows else None
                ),
                "invalidity_rate": _invalidity_rate(parsed_rows),
                "trace_grounding_rate": _trace_grounded_rate(parsed_rows),
                "direct_f1": _metric_or_none(gold_bearing_rows, metric_key="direct"),
                "closure_f1": _metric_or_none(gold_bearing_rows, metric_key="closure"),
                "closure_preservation_rate": _closure_preservation_rate(expected_valid_rows),
                "abstention_rate": _abstention_rate(parsed_rows),
                "overcommitment_rate": _overcommitment_rate(parsed_rows),
                "contradiction_detection_rate": _contradiction_detection_rate(parsed_rows),
                "avg_first_violation_step": _average_first_violation_step(parsed_rows),
                "analysis_focus": (
                    "consistency"
                    if key in {"ambiguous", "contradiction", "empty_gold"}
                    else "fidelity"
                ),
            }
        )
    return rows


def _failure_rows(run: LoadedRun) -> List[Dict[str, Any]]:
    total_tasks = max(int(run.report.get("num_tasks", 0)), 1)
    affected: Dict[tuple[str, str], set[str]] = defaultdict(set)
    event_counts: Dict[tuple[str, str], int] = defaultdict(int)

    for failure in run.report.get("failures", []):
        failure_category = str(failure.get("category", "unknown"))
        scope = "transport" if failure_category.startswith("transport_") else "parse"
        key = (scope, failure_category)
        affected[key].add(str(failure.get("id")))
        event_counts[key] += 1

    for row in run.predictions:
        verification = row.get("verification", {})
        task_id = str(row.get("id"))
        for violation in verification.get("violations", []):
            key = ("verification", str(violation.get("type", "unknown")))
            affected[key].add(task_id)
            event_counts[key] += 1
        for violation in verification.get("formula_violations", []):
            key = ("ltl_formula", str(violation.get("type", "unknown")))
            affected[key].add(task_id)
            event_counts[key] += 1

    rows: List[Dict[str, Any]] = []
    for (scope, failure_type), task_ids in sorted(affected.items()):
        rows.append(
            {
                "run_id": run.run_id,
                "model_label": run.label,
                "failure_scope": scope,
                "failure_type": failure_type,
                "event_count": event_counts[(scope, failure_type)],
                "affected_tasks": len(task_ids),
                "affected_task_rate": len(task_ids) / total_tasks,
            }
        )
    return rows


def _parse_failure_sections(run: LoadedRun, *, limit: int = 2) -> List[str]:
    sections: List[str] = []
    for failure in run.report.get("failures", [])[:limit]:
        sections.append(
            "\n".join(
                [
                    f"### {run.label} :: parse failure :: {failure.get('id')}",
                    f"- Task category: `{failure.get('task_category', 'unknown')}`",
                    f"- Parse failure type: `{failure.get('category')}`",
                    f"- Error: `{failure.get('error')}`",
                ]
            )
        )
    return sections


def _verification_counterexample_sections(run: LoadedRun, *, limit: int = 3) -> List[str]:
    candidate_rows = [
        row for row in run.predictions
        if (not row.get("verification", {}).get("is_valid"))
        or row.get("verification", {}).get("formula_violations")
    ]
    candidate_rows.sort(
        key=lambda row: (
            len(row.get("verification", {}).get("formula_violations", []))
            + len(row.get("verification", {}).get("violations", [])),
            -(row.get("verification", {}).get("first_violation_step") or 10_000),
        ),
        reverse=True,
    )
    sections: List[str] = []
    seen_categories: set[str] = set()
    for row in candidate_rows:
        category = str(row.get("category", "unknown"))
        if category in seen_categories and len(sections) >= limit:
            continue
        seen_categories.add(category)
        verification = row.get("verification", {})
        violation_types = [item.get("type", "") for item in verification.get("violations", [])]
        formula_types = [item.get("type", "") for item in verification.get("formula_violations", [])]
        sections.append(
            "\n".join(
                [
                    f"### {run.label} :: verification :: {row.get('id')}",
                    f"- Category: `{category}`",
                    f"- First violation step: `{verification.get('first_violation_step')}`",
                    f"- Invariant violations: `{', '.join(violation_types) or 'none'}`",
                    f"- LTL violations: `{', '.join(formula_types) or 'none'}`",
                    f"- Predicted edges: `{row.get('pred_edges')}`",
                    f"- Question: {row.get('question')}",
                ]
            )
        )
        if len(sections) >= limit:
            break
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
    fig, ax = plt.subplots(figsize=(6.5, 5))
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
    stacks: Mapping[str, Sequence[float]],
    title: str,
    ylabel: str,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bottoms = [0.0] * len(labels)
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


def _plot_average_first_violation_step(path: Path, summary_rows: Sequence[Dict[str, Any]]) -> None:
    labels = [row["model_label"] for row in summary_rows]
    values = [float(row["avg_first_violation_step"] or 0.0) for row in summary_rows]
    _plot_bar(
        path,
        labels=labels,
        values=values,
        title="Average First Violation Step",
        ylabel="Average step index",
    )


def _generate_plots(
    out_dir: Path,
    summary_rows: Sequence[Dict[str, Any]],
    category_rows: Sequence[Dict[str, Any]],
    failure_rows: Sequence[Dict[str, Any]],
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
    _plot_bar(
        plots_dir / "conditional_trace_grounding_rate.png",
        labels=labels,
        values=[float(row["conditional_trace_grounding_rate"] or 0.0) for row in summary_rows],
        title="Conditional Trace Grounding Rate by Model",
        ylabel="Rate",
    )
    _plot_bar(
        plots_dir / "transport_failure_rate.png",
        labels=labels,
        values=[float(row["transport_failure_rate"]) for row in summary_rows],
        title="Transport Failure Rate by Model",
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
    _plot_bar(
        plots_dir / "closure_gap.png",
        labels=labels,
        values=[float(row["closure_minus_direct_f1"]) for row in summary_rows],
        title="Closure Minus Direct F1",
        ylabel="F1 gap",
    )
    _plot_scatter(
        plots_dir / "parse_success_vs_closure_scatter.png",
        x_values=[float(row["parse_success_rate"]) for row in summary_rows],
        y_values=[float(row["closure_f1"]) for row in summary_rows],
        labels=labels,
        title="Parse Success vs Closure F1",
        xlabel="Parse success rate",
        ylabel="Closure F1",
    )
    _plot_average_first_violation_step(plots_dir / "average_first_violation_step.png", summary_rows)

    _plot_bar(
        plots_dir / "contradiction_detection_rate.png",
        labels=labels,
        values=[float(row["contradiction_detection_rate"] or 0.0) for row in summary_rows],
        title="Contradiction Detection Rate",
        ylabel="Rate",
    )
    _plot_grouped_bars(
        plots_dir / "ambiguity_behaviour.png",
        labels=labels,
        series={
            "abstention_rate": [float(row["ambiguity_abstention_rate"] or 0.0) for row in summary_rows],
            "overcommitment_rate": [float(row["ambiguity_overcommitment_rate"] or 0.0) for row in summary_rows],
        },
        title="Ambiguity Behaviour",
        ylabel="Rate",
    )

    category_parse_rows = [row for row in category_rows if row.get("category")]
    category_names = sorted({row["category"] for row in category_parse_rows})
    if category_names:
        parse_series: Dict[str, List[float]] = {}
        for label in labels:
            label_rows = {row["category"]: row for row in category_parse_rows if row["model_label"] == label}
            parse_series[label] = [float(label_rows.get(category, {}).get("parse_success_rate", 0.0)) for category in category_names]
        _plot_grouped_bars(
            plots_dir / "category_parse_success.png",
            labels=category_names,
            series=parse_series,
            title="Category-wise Parse Success",
            ylabel="Rate",
        )

    fidelity_categories = sorted(
        {
            row["category"]
            for row in category_rows
            if row.get("category")
            and row.get("analysis_focus") == "fidelity"
            and row.get("closure_f1") is not None
        }
    )
    if fidelity_categories:
        series: Dict[str, List[float]] = {}
        for label in labels:
            label_rows = {row["category"]: row for row in category_rows if row["model_label"] == label}
            series[label] = [
                float(label_rows.get(category, {}).get("closure_f1") or 0.0)
                for category in fidelity_categories
            ]
        _plot_grouped_bars(
            plots_dir / "fidelity_category_closure_f1.png",
            labels=fidelity_categories,
            series=series,
            title="Closure F1 on Fidelity-bearing Categories",
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
                        float(row["affected_tasks"])
                        for row in failure_rows
                        if row["failure_scope"] == "parse"
                        and row["failure_type"] == failure_type
                        and row["model_label"] == label
                    ),
                    0.0,
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
            ylabel="Affected tasks",
        )

    for scope, filename, title in [
        ("verification", "verification_task_incidence.png", "Invariant Failure Task Incidence"),
        ("ltl_formula", "ltl_task_incidence.png", "LTL Failure Task Incidence"),
    ]:
        failure_types = sorted(
            {
                row["failure_type"]
                for row in failure_rows
                if row["failure_scope"] == scope
            }
        )
        if failure_types:
            stacks = {
                failure_type: [
                    next(
                        (
                            float(row["affected_task_rate"])
                            for row in failure_rows
                            if row["failure_scope"] == scope
                            and row["failure_type"] == failure_type
                            and row["model_label"] == label
                        ),
                        0.0,
                    )
                    for label in labels
                ]
                for failure_type in failure_types
            }
            _plot_stacked_bars(
                plots_dir / filename,
                labels=labels,
                stacks=stacks,
                title=title,
                ylabel="Affected-task rate",
            )


def _markdown_table(rows: Sequence[Dict[str, Any]], *, columns: Sequence[str]) -> List[str]:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append(
            "| "
            + " | ".join(
                "NA" if row.get(column) is None else str(row.get(column))
                for column in columns
            )
            + " |"
        )
    return [header, separator, *body]


def _narrative_report(
    summary_rows: Sequence[Dict[str, Any]],
    category_rows: Sequence[Dict[str, Any]],
) -> str:
    if not summary_rows:
        return "# Temporal Verification Evaluation Summary\n\nNo runs analysed.\n"

    best_parse = max(summary_rows, key=lambda row: float(row["parse_success_rate"]))
    best_closure = max(summary_rows, key=lambda row: float(row["closure_f1"]))
    best_ambiguity = max(summary_rows, key=lambda row: float(row["ambiguity_abstention_rate"] or 0.0))
    best_contradiction = max(summary_rows, key=lambda row: float(row["contradiction_detection_rate"] or 0.0))
    largest_gap = max(summary_rows, key=lambda row: float(row["closure_minus_direct_f1"]))
    screening_mode = any(bool(row["screening_warning"]) for row in summary_rows)

    report_lines = [
        "# Temporal Verification Evaluation Summary",
        "",
        f"- Runs analysed: `{len(summary_rows)}`",
        f"- Highest parse success: `{best_parse['model_label']}` at `{best_parse['parse_success_rate']:.3f}`",
        f"- Highest closure F1: `{best_closure['model_label']}` at `{best_closure['closure_f1']:.3f}`",
        f"- Best ambiguity abstention: `{best_ambiguity['model_label']}` at `{float(best_ambiguity['ambiguity_abstention_rate'] or 0.0):.3f}`",
        f"- Best contradiction detection: `{best_contradiction['model_label']}` at `{float(best_contradiction['contradiction_detection_rate'] or 0.0):.3f}`",
        f"- Largest closure-direct gap: `{largest_gap['model_label']}` at `{largest_gap['closure_minus_direct_f1']:.3f}`",
        "",
        "## Interpretation",
        "",
    ]
    if screening_mode:
        report_lines.extend(
            [
                "- This is a screening-scale analysis. The current runs are useful for promotion and failure profiling, not final ranking claims.",
                "- Small categories such as `long_chain` should be treated as directional evidence only.",
            ]
        )
    report_lines.extend(
        [
            "- Parse robustness, transport stability, intrinsic graph validity, trace grounding, exact direct-edge fidelity, closure-level reasoning, ambiguity discipline, and contradiction detection should be read as separate capabilities.",
            "- Direct-vs-closure gaps indicate when a model recovers the implied temporal ordering while still missing the intended explicit representation.",
            "- Ambiguous and contradiction categories are consistency-oriented slices. They should not be interpreted through raw F1 alone.",
            "",
            "## Top-line Table",
            "",
        ]
    )
    report_lines.extend(
        _markdown_table(
            summary_rows,
            columns=[
                "model_label",
                "parse_success_rate",
                "transport_failure_rate",
                "conditional_validity_rate",
                "conditional_trace_grounding_rate",
                "direct_f1",
                "closure_f1",
                "closure_minus_direct_f1",
                "ambiguity_overcommitment_rate",
                "contradiction_detection_rate",
            ],
        )
    )
    report_lines.extend(["", "## Category Notes", ""])
    category_focus_rows = [
        row for row in category_rows
        if row.get("category") in {"ambiguous", "contradiction", "linear_chain", "transitive_reasoning"}
    ]
    report_lines.extend(
        _markdown_table(
            category_focus_rows,
            columns=[
                "model_label",
                "category",
                "parse_success_rate",
                "conditional_validity_rate",
                "trace_grounding_rate",
                "direct_f1",
                "closure_f1",
                "abstention_rate",
                "overcommitment_rate",
                "contradiction_detection_rate",
            ],
        )
    )
    report_lines.extend(
        [
            "",
            "## Plot Reading Guide",
            "",
            "- `parse_success_rate.png`: pipeline robustness, not reasoning quality.",
            "- `transport_failure_rate.png`: infrastructure instability, not model behaviour.",
            "- `conditional_trace_grounding_rate.png`: whether reasoning annotations align with the final answer structure.",
            "- `direct_vs_closure_f1.png`: representation fidelity versus ordering recovery.",
            "- `ambiguity_behaviour.png`: abstention discipline versus overcommitment.",
            "- `contradiction_detection_rate.png`: consistency-focused performance on contradiction tasks.",
            "- `verification_task_incidence.png`: task-level prevalence of invariant failure modes.",
            "- `ltl_task_incidence.png`: trace-level corroboration of structural failures; do not read this as independent evidence from the invariant layer.",
        ]
    )
    return "\n".join(report_lines) + "\n"


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
        parse_sections = _parse_failure_sections(run)
        verification_sections = _verification_counterexample_sections(run)
        if parse_sections or verification_sections:
            counterexample_text.append(f"## {run.label}")
            counterexample_text.append("")
            counterexample_text.extend(parse_sections)
            if parse_sections:
                counterexample_text.append("")
            counterexample_text.extend(verification_sections)
            counterexample_text.append("")
    (out_path / "counterexamples.md").write_text("\n".join(counterexample_text), encoding="utf-8")

    (out_path / "report.md").write_text(
        _narrative_report(summary_rows, category_rows),
        encoding="utf-8",
    )

    _generate_plots(out_path, summary_rows, category_rows, failure_rows)
    return {
        "summary": summary_rows,
        "category_breakdown": category_rows,
        "difficulty_breakdown": difficulty_rows,
        "failure_breakdown": failure_rows,
    }
