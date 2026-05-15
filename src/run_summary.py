from __future__ import annotations

import csv
import json
import math
import os
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import shutil
from statistics import mean
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from src.analysis.axis_correlation import (
    axis_correlation_prose,
    compute_axis_correlation,
    extract_flags,
    plot_axis_correlation,
    save_axis_correlation_csv,
)


BOOTSTRAP_ITERATIONS = 500
BOOTSTRAP_SEED = 7
GENUINE_LTL_TYPES = {
    "ltl_unsupported_final_commitment",
    "ltl_trace_inversion",
}
CORROBORATING_LTL_TYPES = {
    "ltl_contradiction",
    "ltl_temporal_inconsistency",
    "ltl_hallucinated_node",
}

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    pass


@dataclass(frozen=True)
class LoadedRun:
    run_dir: Path
    report: Dict[str, Any]
    predictions: List[Dict[str, Any]]
    manifest_meta: Dict[str, Any]
    predictions_path: Path

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
    raise ValueError(
        "Run manifest must be an object or an object containing a 'runs' mapping."
    )


def _auto_manifest_path(run_dirs: Sequence[str | Path]) -> Optional[Path]:
    resolved_run_dirs = [Path(run_dir).resolve() for run_dir in run_dirs]
    if not resolved_run_dirs:
        return None
    try:
        common_root = Path(
            os.path.commonpath([str(run_dir.parent) for run_dir in resolved_run_dirs])
        )
    except ValueError:
        return None
    manifest_path = common_root / "run_manifest.json"
    return manifest_path if manifest_path.exists() else None


def _difficulty_bucket(*, num_events: int, gold_relation_count: int) -> str:
    if gold_relation_count == 0:
        return "empty_gold"
    if gold_relation_count <= 2 and num_events <= 3:
        return "low_complexity"
    if gold_relation_count <= 4 and num_events <= 4:
        return "medium_complexity"
    return "high_complexity"


def _aggregate_prf_from_rows(
    rows: Sequence[Dict[str, Any]], *, metric_key: str
) -> Dict[str, float]:
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
    f1 = (
        (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    )
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "correct": correct,
        "pred_total": pred_total,
        "gold_total": gold_total,
    }


def _metric_totals_from_failure(
    failure: Mapping[str, Any], *, metric_key: str
) -> Optional[Dict[str, int]]:
    score = failure.get("score_as_empty_prediction")
    if isinstance(score, Mapping):
        metric = score.get(metric_key)
        if isinstance(metric, Mapping):
            return {
                "correct": int(metric.get("correct", 0)),
                "pred_total": int(metric.get("pred_total", 0)),
                "gold_total": int(metric.get("gold_total", 0)),
            }
    if metric_key == "direct":
        return {
            "correct": 0,
            "pred_total": 0,
            "gold_total": int(failure.get("gold_relation_count", 0)),
        }
    return None


def _aggregate_prf_end_to_end(
    entries: Sequence[Dict[str, Any]],
    *,
    metric_key: str,
) -> tuple[Dict[str, float], bool]:
    correct = 0
    pred_total = 0
    gold_total = 0
    complete = True
    for entry in entries:
        if entry.get("parsed", True):
            prediction = entry.get("prediction")
            if not isinstance(prediction, Mapping):
                continue
            metric = prediction.get("score", {}).get(metric_key, {})
            correct += int(metric.get("correct", 0))
            pred_total += int(metric.get("pred_total", 0))
            gold_total += int(metric.get("gold_total", 0))
            continue

        failure = entry.get("failure")
        if not isinstance(failure, Mapping):
            continue
        metric = _metric_totals_from_failure(failure, metric_key=metric_key)
        if metric is None:
            complete = False
            continue
        correct += metric["correct"]
        pred_total += metric["pred_total"]
        gold_total += metric["gold_total"]

    precision = (correct / pred_total) if pred_total else 0.0
    recall = (correct / gold_total) if gold_total else 0.0
    f1 = (
        (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    )
    return (
        {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "correct": correct,
            "pred_total": pred_total,
            "gold_total": gold_total,
        },
        complete,
    )


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


def _row_verification(row: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(row.get("verification"), dict):
        return row["verification"]
    prediction = row.get("prediction")
    if isinstance(prediction, dict) and isinstance(
        prediction.get("verification"), dict
    ):
        return prediction["verification"]
    return {}


def _trace_grounded_rate(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if not rows:
        return None

    def is_grounded(row: Dict[str, Any]) -> bool:
        verification = _row_verification(row)
        if "trace_grounded" in verification:
            return bool(verification.get("trace_grounded"))
        violation_types = {
            item.get("type") for item in verification.get("violations", [])
        }
        return not bool(
            {"unsupported_reasoning_step", "unsupported_reasoning_reference"}
            & violation_types
        )

    return sum(1 for row in rows if is_grounded(row)) / len(rows)


def _closure_preservation_rate(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if not rows:
        return None
    return sum(
        1 for row in rows if row.get("score", {}).get("preserves_ordering_closure")
    ) / len(rows)


def _abstention_rate(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if not rows:
        return None
    return sum(1 for row in rows if row.get("score", {}).get("abstained")) / len(rows)


def _overcommitment_rate(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if not rows:
        return None
    return sum(
        1 for row in rows if row.get("score", {}).get("has_overcommitment")
    ) / len(rows)


def _invalidity_rate(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if not rows:
        return None
    return sum(1 for row in rows if not _row_verification(row).get("is_valid")) / len(
        rows
    )


def _formula_type_rate(
    rows: Sequence[Dict[str, Any]], formula_types: set[str]
) -> Optional[float]:
    if not rows:
        return None
    affected = 0
    for row in rows:
        verification = _row_verification(row)
        row_formula_types = {
            str(item.get("type"))
            for item in verification.get("formula_violations", [])
            if isinstance(item, Mapping)
        }
        if row_formula_types & formula_types:
            affected += 1
    return affected / len(rows)


def _validity_expectation_alignment_rate(
    rows: Sequence[Dict[str, Any]],
) -> Optional[float]:
    if not rows:
        return None
    aligned = 0
    for row in rows:
        if not row.get("parsed", True):
            continue
        expected_valid = bool(row.get("expected_valid", True))
        observed_valid = bool(_row_verification(row).get("is_valid"))
        if observed_valid == expected_valid:
            aligned += 1
    return aligned / len(rows)


def _average_first_violation_step(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    steps = [
        int(_row_verification(row).get("first_violation_step"))
        for row in rows
        if _row_verification(row).get("first_violation_step") is not None
    ]
    if not steps:
        return None
    return mean(steps)


def _contradiction_detected(row: Dict[str, Any]) -> bool:
    verification = _row_verification(row)
    violation_types = {item.get("type") for item in verification.get("violations", [])}
    formula_types = {
        item.get("type") for item in verification.get("formula_violations", [])
    }
    return bool(
        {"contradiction", "cycle", "temporal_inconsistency"} & violation_types
        or {"ltl_contradiction", "ltl_temporal_inconsistency"} & formula_types
    )


def _contradiction_detection_rate(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if not rows:
        return None
    return sum(1 for row in rows if _contradiction_detected(row)) / len(rows)


def _metric_or_none(
    rows: Sequence[Dict[str, Any]], *, metric_key: str
) -> Optional[float]:
    if not rows:
        return None
    aggregate = _aggregate_prf_from_rows(rows, metric_key=metric_key)
    if aggregate["gold_total"] == 0:
        return None
    return aggregate["f1"]


def _closure_coverage(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    # Among gold-bearing tasks (those where the gold ordering produces at least one pair),
    # what fraction did the model make a non-UNKNOWN ordering commitment for?
    gold_bearing = [
        r
        for r in rows
        if r.get("score", {}).get("closure", {}).get("gold_total", 0) > 0
    ]
    if not gold_bearing:
        return None
    committed = sum(
        1
        for r in gold_bearing
        if r.get("score", {}).get("closure", {}).get("pred_total", 0) > 0
    )
    return committed / len(gold_bearing)


def _committed_closure_prf(rows: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    # Micro-average PRF restricted to tasks where BOTH gold and pred produce ordering pairs.
    # This is the "conditional on commitment" variant of closure F1.
    committed = [
        r
        for r in rows
        if r.get("score", {}).get("closure", {}).get("gold_total", 0) > 0
        and r.get("score", {}).get("closure", {}).get("pred_total", 0) > 0
    ]
    return _aggregate_prf_from_rows(committed, metric_key="closure")


def _has_non_null_metric(rows: Sequence[Dict[str, Any]], key: str) -> bool:
    return any(row.get(key) is not None for row in rows)


def load_runs(
    run_dirs: Sequence[str | Path],
    *,
    manifest_path: str | Path | None = None,
    predictions_filename: str = "predictions.jsonl",
) -> List[LoadedRun]:
    resolved_manifest_path = (
        Path(manifest_path)
        if manifest_path is not None
        else _auto_manifest_path(run_dirs)
    )
    manifest = _load_manifest(resolved_manifest_path)
    loaded: List[LoadedRun] = []
    for run_dir_like in run_dirs:
        run_dir = Path(run_dir_like)
        report = _read_json(run_dir / "report.json")
        predictions_path = run_dir / predictions_filename
        predictions = _read_jsonl(predictions_path)
        loaded.append(
            LoadedRun(
                run_dir=run_dir,
                report=report,
                predictions=predictions,
                manifest_meta=dict(manifest.get(str(report["run_id"]), {})),
                predictions_path=predictions_path,
            )
        )
    return loaded


def _run_row(run: LoadedRun) -> Dict[str, Any]:
    report = run.report
    parsed_rows = list(run.predictions)
    combined_entries = _combine_task_entries(run)
    expected_valid_parsed_rows = _expected_valid_parsed_rows(parsed_rows)
    expected_valid_gold_bearing_rows = [
        row
        for row in expected_valid_parsed_rows
        if len(row.get("gold_relations", [])) > 0
    ]
    ambiguous_rows = [row for row in parsed_rows if row.get("category") == "ambiguous"]
    contradiction_rows = [
        row for row in parsed_rows if row.get("category") == "contradiction"
    ]
    contradiction_entries = [
        row for row in combined_entries if row.get("category") == "contradiction"
    ]

    direct = _aggregate_prf_from_rows(expected_valid_parsed_rows, metric_key="direct")
    closure = _aggregate_prf_from_rows(expected_valid_parsed_rows, metric_key="closure")
    expected_valid_entries = [
        entry for entry in combined_entries if entry.get("expected_valid", True)
    ]
    direct_e2e, direct_e2e_complete = _aggregate_prf_end_to_end(
        expected_valid_entries,
        metric_key="direct",
    )
    closure_e2e, closure_e2e_complete = _aggregate_prf_end_to_end(
        expected_valid_entries,
        metric_key="closure",
    )
    num_tasks = int(report.get("num_tasks", len(parsed_rows)))
    num_failures = int(report.get("num_failures", max(num_tasks - len(parsed_rows), 0)))
    parse_success_rate = len(parsed_rows) / max(num_tasks, 1)
    conditional_validity_rate = (
        sum(1 for row in parsed_rows if row.get("verification", {}).get("is_valid"))
        / len(parsed_rows)
        if parsed_rows
        else None
    )
    conditional_trace_grounding_rate = _trace_grounded_rate(parsed_rows)
    validity_rate = sum(
        1 for row in parsed_rows if row.get("verification", {}).get("is_valid")
    ) / max(num_tasks, 1)
    parse_ci_low, parse_ci_high = _bootstrap_ci(
        combined_entries,
        metric_fn=lambda sample: (
            sum(1 for item in sample if item["parsed"]) / len(sample)
        ),
    )
    conditional_ci_low, conditional_ci_high = _bootstrap_ci(
        expected_valid_parsed_rows,
        metric_fn=lambda sample: (
            sum(1 for row in sample if row.get("verification", {}).get("is_valid"))
            / len(sample)
            if sample
            else None
        ),
    )
    direct_ci_low, direct_ci_high = _bootstrap_ci(
        expected_valid_parsed_rows,
        metric_fn=lambda sample: _metric_or_none(sample, metric_key="direct"),
    )
    closure_ci_low, closure_ci_high = _bootstrap_ci(
        expected_valid_parsed_rows,
        metric_fn=lambda sample: _metric_or_none(sample, metric_key="closure"),
    )
    fidelity_direct = _aggregate_prf_from_rows(
        expected_valid_gold_bearing_rows, metric_key="direct"
    )
    fidelity_closure = _aggregate_prf_from_rows(
        expected_valid_gold_bearing_rows, metric_key="closure"
    )
    fidelity_direct_ci_low, fidelity_direct_ci_high = _bootstrap_ci(
        expected_valid_gold_bearing_rows,
        metric_fn=lambda sample: _metric_or_none(sample, metric_key="direct"),
    )
    fidelity_closure_ci_low, fidelity_closure_ci_high = _bootstrap_ci(
        expected_valid_gold_bearing_rows,
        metric_fn=lambda sample: _metric_or_none(sample, metric_key="closure"),
    )

    return {
        "run_id": report["run_id"],
        "model_label": run.label,
        "model": report["model_metadata"].get("model", ""),
        "family": run.manifest_meta.get("family", ""),
        "size_bucket": run.manifest_meta.get(
            "size_bucket", run.manifest_meta.get("size", "")
        ),
        "reasoning_tuned": run.manifest_meta.get("reasoning_tuned", ""),
        "group": run.manifest_meta.get("group", ""),
        "dataset_version": report["dataset"]["dataset_version"],
        "pred_source": report["pred_source"],
        "num_tasks": num_tasks,
        "num_failures": num_failures,
        "parse_success_count": len(parsed_rows),
        "repair_hit_count": report.get("repair_hit_count", 0),
        "repair_hit_rate": report.get("repair_hit_rate", 0.0),
        "parse_success_rate": parse_success_rate,
        "parse_success_ci_low": parse_ci_low,
        "parse_success_ci_high": parse_ci_high,
        "transport_failure_rate": (
            sum(
                int(value)
                for value in report.get("transport_failure_counts", {}).values()
            )
            / max(num_tasks, 1)
        ),
        "conditional_validity_rate": conditional_validity_rate,
        "conditional_validity_ci_low": conditional_ci_low,
        "conditional_validity_ci_high": conditional_ci_high,
        "conditional_trace_grounding_rate": conditional_trace_grounding_rate,
        "validity_expectation_alignment_rate": _validity_expectation_alignment_rate(
            parsed_rows
        ),
        "validity_expectation_alignment_rate_e2e": _validity_expectation_alignment_rate(
            combined_entries
        ),
        "validity_rate": validity_rate,
        "parsed_expected_valid_tasks": len(expected_valid_parsed_rows),
        "parsed_gold_bearing_tasks": len(expected_valid_gold_bearing_rows),
        "direct_precision": direct["precision"],
        "direct_recall": direct["recall"],
        "direct_f1": direct["f1"],
        "direct_f1_ci_low": direct_ci_low,
        "direct_f1_ci_high": direct_ci_high,
        "direct_e2e_precision": direct_e2e["precision"],
        "direct_e2e_recall": direct_e2e["recall"],
        "direct_e2e_f1": direct_e2e["f1"],
        "direct_e2e_complete": direct_e2e_complete,
        "closure_precision": closure["precision"],
        "closure_recall": closure["recall"],
        "closure_f1": closure["f1"],
        "closure_f1_ci_low": closure_ci_low,
        "closure_f1_ci_high": closure_ci_high,
        "closure_minus_direct_f1": closure["f1"] - direct["f1"],
        "closure_e2e_precision": closure_e2e["precision"]
        if closure_e2e_complete
        else None,
        "closure_e2e_recall": closure_e2e["recall"] if closure_e2e_complete else None,
        "closure_e2e_f1": closure_e2e["f1"] if closure_e2e_complete else None,
        "closure_e2e_complete": closure_e2e_complete,
        "fidelity_direct_precision": fidelity_direct["precision"],
        "fidelity_direct_recall": fidelity_direct["recall"],
        "fidelity_direct_f1": fidelity_direct["f1"],
        "fidelity_direct_f1_ci_low": fidelity_direct_ci_low,
        "fidelity_direct_f1_ci_high": fidelity_direct_ci_high,
        "fidelity_closure_precision": fidelity_closure["precision"],
        "fidelity_closure_recall": fidelity_closure["recall"],
        # DEPRECATED alias: fidelity_closure_f1 == fidelity_closure_f1_full; use the latter in new code.
        "fidelity_closure_f1": fidelity_closure["f1"],
        "fidelity_closure_f1_ci_low": fidelity_closure_ci_low,
        "fidelity_closure_f1_ci_high": fidelity_closure_ci_high,
        "fidelity_closure_gap": fidelity_closure["f1"] - fidelity_direct["f1"],
        "closure_coverage": _closure_coverage(expected_valid_gold_bearing_rows),
        "fidelity_closure_f1_committed": _committed_closure_prf(
            expected_valid_gold_bearing_rows
        )["f1"],
        "fidelity_closure_f1_full": fidelity_closure["f1"],
        "closure_preservation_rate": _closure_preservation_rate(
            expected_valid_parsed_rows
        ),
        "ambiguity_abstention_rate": _abstention_rate(ambiguous_rows),
        "ambiguity_overcommitment_rate": _overcommitment_rate(ambiguous_rows),
        "contradiction_detection_rate": _contradiction_detection_rate(
            contradiction_rows
        ),
        "contradiction_detection_rate_e2e": _contradiction_detection_rate(
            contradiction_entries
        ),
        "contradiction_invalidity_rate": _invalidity_rate(contradiction_rows),
        "ltl_genuine_violation_rate": _formula_type_rate(
            parsed_rows, GENUINE_LTL_TYPES
        ),
        "ltl_invariant_corroboration_rate": _formula_type_rate(
            parsed_rows, CORROBORATING_LTL_TYPES
        ),
        "avg_first_violation_step": _average_first_violation_step(parsed_rows),
        "screening_warning": num_tasks <= 25,
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
        combined_rows = [
            *[{**row, "parsed": True} for row in parsed_rows],
            *[
                {
                    "parsed": False,
                    "expected_valid": bool(failure.get("expected_valid", True)),
                    "verification": {},
                }
                for failure in failed_rows
            ],
        ]
        expected_valid_rows = _expected_valid_parsed_rows(parsed_rows)
        gold_bearing_rows = [
            row for row in expected_valid_rows if len(row.get("gold_relations", [])) > 0
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
                    sum(
                        1
                        for row in parsed_rows
                        if row.get("verification", {}).get("is_valid")
                    )
                    / len(parsed_rows)
                    if parsed_rows
                    else None
                ),
                "validity_expectation_alignment_rate": _validity_expectation_alignment_rate(
                    parsed_rows
                ),
                "validity_expectation_alignment_rate_e2e": _validity_expectation_alignment_rate(
                    combined_rows
                ),
                "invalidity_rate": _invalidity_rate(parsed_rows),
                "trace_grounding_rate": _trace_grounded_rate(parsed_rows),
                "direct_f1": _metric_or_none(gold_bearing_rows, metric_key="direct"),
                "closure_f1": _metric_or_none(gold_bearing_rows, metric_key="closure"),
                "closure_preservation_rate": _closure_preservation_rate(
                    expected_valid_rows
                ),
                "abstention_rate": _abstention_rate(parsed_rows),
                "overcommitment_rate": _overcommitment_rate(parsed_rows),
                "contradiction_detection_rate": _contradiction_detection_rate(
                    parsed_rows
                ),
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


def _verification_counterexample_sections(
    run: LoadedRun, *, limit: int = 3
) -> List[str]:
    candidate_rows = [
        row
        for row in run.predictions
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
        violation_types = [
            item.get("type", "") for item in verification.get("violations", [])
        ]
        formula_types = [
            item.get("type", "") for item in verification.get("formula_violations", [])
        ]
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
    is_rate: bool = False,
    ylim: tuple[float, float] | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(labels, values, color="#4C78A8")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=25)
    if is_rate:
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
        ax.set_ylim(*(ylim or (0.0, 1.05)))
    elif ylim is not None:
        ax.set_ylim(*ylim)
    for bar, value in zip(bars, values):
        if math.isnan(value):
            continue
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + (0.015 if is_rate else 0.02),
            f"{value:.0%}" if is_rate else f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
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
    is_rate: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    positions = list(range(len(labels)))
    width = 0.8 / max(len(series), 1)
    for index, (name, values) in enumerate(series.items()):
        offsets = [
            position + (index - (len(series) - 1) / 2) * width for position in positions
        ]
        ax.bar(offsets, values, width=width, label=name)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=25)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    if is_rate:
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
        ax.set_ylim(0.0, 1.05)
    ax.legend(frameon=False)
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
    ax.set_xlim(0.0, 1.05)
    ax.set_ylim(0.0, 1.05)
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
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
    is_rate: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bottoms = [0.0] * len(labels)
    for name, values in stacks.items():
        ax.bar(labels, values, bottom=bottoms, label=name)
        bottoms = [left + right for left, right in zip(bottoms, values)]
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=25)
    if is_rate:
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
        ax.set_ylim(0.0, 1.05)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_average_first_violation_step(
    path: Path, summary_rows: Sequence[Dict[str, Any]]
) -> None:
    labels = [row["model_label"] for row in summary_rows]
    raw_values = [row["avg_first_violation_step"] for row in summary_rows]
    values = [float(value) if value is not None else math.nan for value in raw_values]
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(
        labels,
        [0.0 if math.isnan(value) else value for value in values],
        color=["#BAB0AC" if math.isnan(value) else "#59A14F" for value in values],
    )
    ax.set_title("Average First Violation Step")
    ax.set_ylabel("Average step index")
    ax.tick_params(axis="x", rotation=25)
    upper = max((value for value in values if not math.isnan(value)), default=0.0)
    ax.set_ylim(0.0, upper + max(0.4, upper * 0.2))
    for bar, value in zip(bars, raw_values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            (0.02 if value is None else float(value) + 0.05),
            "N/A" if value is None else f"{float(value):.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_validity_expectation_alignment(
    path: Path, summary_rows: Sequence[Dict[str, Any]]
) -> None:
    _plot_bar(
        path,
        labels=[row["model_label"] for row in summary_rows],
        values=[
            float(row["validity_expectation_alignment_rate_e2e"] or 0.0)
            for row in summary_rows
        ],
        title="Validity-Expectation Alignment",
        ylabel="End-to-end alignment rate",
        is_rate=True,
    )


def _generate_plots(
    out_dir: Path,
    summary_rows: Sequence[Dict[str, Any]],
    category_rows: Sequence[Dict[str, Any]],
    failure_rows: Sequence[Dict[str, Any]],
) -> None:
    plots_dir = out_dir / "plots"
    if plots_dir.exists():
        shutil.rmtree(plots_dir)
    plots_dir.mkdir(parents=True, exist_ok=True)
    labels = [row["model_label"] for row in summary_rows]
    has_ambiguity = any(row.get("category") == "ambiguous" for row in category_rows)
    has_contradiction = any(
        row.get("category") == "contradiction" for row in category_rows
    )
    _plot_bar(
        plots_dir / "parse_success_rate.png",
        labels=labels,
        values=[float(row["parse_success_rate"]) for row in summary_rows],
        title="Parse Success Rate by Model",
        ylabel="Rate",
        is_rate=True,
    )
    _plot_bar(
        plots_dir / "conditional_validity_rate.png",
        labels=labels,
        values=[float(row["conditional_validity_rate"] or 0.0) for row in summary_rows],
        title="Conditional Validity Rate by Model",
        ylabel="Rate",
        is_rate=True,
    )
    _plot_bar(
        plots_dir / "conditional_trace_grounding_rate.png",
        labels=labels,
        values=[
            float(row["conditional_trace_grounding_rate"] or 0.0)
            for row in summary_rows
        ],
        title="Conditional Trace Grounding Rate by Model",
        ylabel="Rate",
        is_rate=True,
    )
    _plot_validity_expectation_alignment(
        plots_dir / "validity_expectation_alignment_rate.png",
        summary_rows,
    )
    _plot_bar(
        plots_dir / "transport_failure_rate.png",
        labels=labels,
        values=[float(row["transport_failure_rate"]) for row in summary_rows],
        title="Transport Failure Rate by Model",
        ylabel="Rate",
        is_rate=True,
    )
    _plot_grouped_bars(
        plots_dir / "direct_vs_closure_f1.png",
        labels=labels,
        series={
            "direct_f1": [float(row["fidelity_direct_f1"]) for row in summary_rows],
            "closure_f1": [float(row["fidelity_closure_f1"]) for row in summary_rows],
        },
        title="Direct vs Closure F1 (Gold-bearing Tasks)",
        ylabel="F1",
        is_rate=True,
    )
    _plot_bar(
        plots_dir / "closure_gap.png",
        labels=labels,
        values=[float(row["fidelity_closure_gap"]) for row in summary_rows],
        title="Closure Minus Direct F1 (Gold-bearing Tasks)",
        ylabel="F1 gap",
        ylim=(
            0.0,
            max(float(row["fidelity_closure_gap"]) for row in summary_rows) + 0.05,
        ),
    )
    _plot_scatter(
        plots_dir / "parse_success_vs_closure_scatter.png",
        x_values=[float(row["parse_success_rate"]) for row in summary_rows],
        y_values=[float(row["fidelity_closure_f1"]) for row in summary_rows],
        labels=labels,
        title="Parse Success vs Closure F1 (Gold-bearing Tasks)",
        xlabel="Parse success rate",
        ylabel="Closure F1",
    )
    _plot_average_first_violation_step(
        plots_dir / "average_first_violation_step.png", summary_rows
    )
    _plot_grouped_bars(
        plots_dir / "genuine_ltl_incidence.png",
        labels=labels,
        series={
            "Genuine LTL (F/G trace-level)": [
                float(row["ltl_genuine_violation_rate"] or 0.0) for row in summary_rows
            ],
            "Invariant-corroborating LTL": [
                float(row["ltl_invariant_corroboration_rate"] or 0.0)
                for row in summary_rows
            ],
        },
        title="Genuine vs. Corroborating LTL Violation Rates",
        ylabel="Violation rate",
        is_rate=True,
    )

    if has_contradiction and _has_non_null_metric(
        summary_rows, "contradiction_detection_rate"
    ):
        _plot_bar(
            plots_dir / "contradiction_detection_rate.png",
            labels=labels,
            values=[
                float(row["contradiction_detection_rate"] or 0.0)
                for row in summary_rows
            ],
            title="Contradiction Detection Rate (Parsed Contradiction Tasks)",
            ylabel="Rate",
            is_rate=True,
        )
    if has_ambiguity and (
        _has_non_null_metric(summary_rows, "ambiguity_abstention_rate")
        or _has_non_null_metric(summary_rows, "ambiguity_overcommitment_rate")
    ):
        _plot_grouped_bars(
            plots_dir / "ambiguity_behaviour.png",
            labels=labels,
            series={
                "abstention_rate": [
                    float(row["ambiguity_abstention_rate"] or 0.0)
                    for row in summary_rows
                ],
                "overcommitment_rate": [
                    float(row["ambiguity_overcommitment_rate"] or 0.0)
                    for row in summary_rows
                ],
            },
            title="Ambiguity Behaviour (Parsed Ambiguous Tasks)",
            ylabel="Rate",
            is_rate=True,
        )

    category_parse_rows = [row for row in category_rows if row.get("category")]
    category_names = sorted({row["category"] for row in category_parse_rows})
    if len(category_names) > 1:
        parse_series: Dict[str, List[float]] = {}
        for label in labels:
            label_rows = {
                row["category"]: row
                for row in category_parse_rows
                if row["model_label"] == label
            }
            parse_series[label] = [
                float(label_rows.get(category, {}).get("parse_success_rate", 0.0))
                for category in category_names
            ]
        _plot_grouped_bars(
            plots_dir / "category_parse_success.png",
            labels=category_names,
            series=parse_series,
            title="Category-wise Parse Success",
            ylabel="Rate",
            is_rate=True,
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
    if len(fidelity_categories) > 1:
        series: Dict[str, List[float]] = {}
        for label in labels:
            label_rows = {
                row["category"]: row
                for row in category_rows
                if row["model_label"] == label
            }
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
            is_rate=True,
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
        (
            "verification",
            "verification_task_incidence.png",
            "Invariant Failure Task Incidence",
        ),
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
                is_rate=True,
            )


def _markdown_table(
    rows: Sequence[Dict[str, Any]], *, columns: Sequence[str]
) -> List[str]:
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
    correlation_prose_blocks: Optional[Sequence[str]] = None,
) -> str:
    if not summary_rows:
        return "# Temporal Verification Evaluation Summary\n\nNo runs analysed.\n"

    category_names = sorted(
        {str(row["category"]) for row in category_rows if row.get("category")}
    )
    has_ambiguity = "ambiguous" in category_names
    has_contradiction = "contradiction" in category_names
    is_single_category = len(category_names) == 1
    best_parse = max(summary_rows, key=lambda row: float(row["parse_success_rate"]))
    best_closure = max(summary_rows, key=lambda row: float(row["fidelity_closure_f1"]))
    best_alignment = max(
        summary_rows,
        key=lambda row: float(row["validity_expectation_alignment_rate_e2e"] or 0.0),
    )
    largest_gap = max(summary_rows, key=lambda row: float(row["fidelity_closure_gap"]))
    worst_transport = max(
        summary_rows, key=lambda row: float(row["transport_failure_rate"])
    )
    screening_mode = any(bool(row["screening_warning"]) for row in summary_rows)

    report_lines = [
        "# Temporal Verification Evaluation Summary",
        "",
        f"- Runs analysed: `{len(summary_rows)}`",
        f"- Highest parse success: `{best_parse['model_label']}` at `{best_parse['parse_success_rate']:.3f}`",
        f"- Highest fidelity closure F1: `{best_closure['model_label']}` at `{best_closure['fidelity_closure_f1']:.3f}`",
        f"- Highest validity-expectation alignment: `{best_alignment['model_label']}` at `{float(best_alignment['validity_expectation_alignment_rate_e2e'] or 0.0):.3f}`",
        f"- Largest fidelity closure-direct gap: `{largest_gap['model_label']}` at `{largest_gap['fidelity_closure_gap']:.3f}`",
        "",
        "## Interpretation",
        "",
    ]
    if has_ambiguity:
        best_ambiguity = max(
            summary_rows, key=lambda row: float(row["ambiguity_abstention_rate"] or 0.0)
        )
        report_lines.insert(
            6,
            f"- Best ambiguity abstention: `{best_ambiguity['model_label']}` at `{float(best_ambiguity['ambiguity_abstention_rate'] or 0.0):.3f}`",
        )
    if has_contradiction:
        best_contradiction = max(
            summary_rows,
            key=lambda row: float(row["contradiction_detection_rate"] or 0.0),
        )
        insert_at = 7 if has_ambiguity else 6
        report_lines.insert(
            insert_at,
            f"- Best contradiction detection: `{best_contradiction['model_label']}` at `{float(best_contradiction['contradiction_detection_rate'] or 0.0):.3f}`",
        )
    if screening_mode:
        report_lines.extend(
            [
                "- This is a screening-scale analysis. The current runs are useful for promotion and failure profiling, not final ranking claims.",
                "- Small categories such as `long_chain` should be treated as directional evidence only.",
            ]
        )
    report_lines.extend(
        [
            "- Intrinsic graph validity and trace grounding, exact direct-edge fidelity, closure-level reasoning, ambiguity discipline, and contradiction detection should be read as separate capabilities.",
            "- `validity_expectation_alignment_rate_e2e` checks whether the verifier outcome matches the task intent end-to-end, so clean-but-wrong contradiction abstention does not look deceptively strong.",
            "- Intrinsic validity is a necessary-but-not-sufficient signal: no intrinsically invalid prediction was also label-correct, but intrinsically valid predictions still achieve only partial label accuracy. Both conditions must be checked.",
            "- `fidelity_direct_f1` and `fidelity_closure_f1` are computed on gold-bearing tasks only, excluding empty-gold ambiguity items from the fidelity headline.",
            "- Closure scoring only covers ordering-bearing relations. On datasets with many `SIMULTANEOUS` labels, closure F1 should be interpreted alongside direct F1 rather than in isolation.",
            "- Closure F1 is reported in two forms: `fidelity_closure_f1_full` (headline — treats uncommitted pairs as false negatives) and `fidelity_closure_f1_committed` (conditional on commitment only). Read `closure_coverage` alongside both.",
            "- Direct-vs-closure gaps indicate when a model recovers the implied temporal ordering while still missing the intended explicit representation.",
            (
                "- Ambiguous and contradiction categories are consistency-oriented slices. They should not be interpreted through raw F1 alone."
                if has_ambiguity or has_contradiction
                else "- This dataset does not contain ambiguity or contradiction control slices, so consistency-specific plots are intentionally omitted."
            ),
            "",
            "## Pipeline Diagnostics",
            "",
            "Parse robustness and transport stability are infrastructure signals, not reasoning quality indicators. They are separated here to avoid conflation with the reasoning metrics in the top-line table.",
            "",
        ]
    )
    report_lines.extend(
        _markdown_table(
            summary_rows,
            columns=["model_label", "parse_success_rate", "transport_failure_rate"],
        )
    )
    if is_single_category:
        report_lines.extend(
            [
                "",
                f"- This run set evaluates a single task family: `{category_names[0]}`. Category-wise plots should be read as dataset-wide summaries rather than cross-category diagnostics.",
            ]
        )
    if float(worst_transport["transport_failure_rate"]) >= 0.05:
        report_lines.append(
            f"- `{worst_transport['model_label']}` has a transport failure rate of `{float(worst_transport['transport_failure_rate']):.3f}`. Comparative claims for that run should be treated as infrastructure-confounded until rerun with stronger retry settings.",
        )
    report_lines.extend(["", "## Top-line Table", ""])
    report_lines.extend(
        _markdown_table(
            summary_rows,
            columns=[
                "model_label",
                "conditional_validity_rate",
                "validity_expectation_alignment_rate_e2e",
                "conditional_trace_grounding_rate",
                "fidelity_direct_f1",
                "fidelity_closure_f1_full",
                "fidelity_closure_gap",
                "closure_coverage",
                "fidelity_closure_f1_committed",
            ]
            + (["ambiguity_overcommitment_rate"] if has_ambiguity else [])
            + (["contradiction_detection_rate"] if has_contradiction else []),
        )
    )
    report_lines.extend(
        [
            "",
            "## LTL Layer",
            "",
            "`ltl_genuine_violation_rate` counts task-specific trace formulas that are not reducible to the invariant layer: unsupported final commitments checked with `F(supports(...))`, and mid-trace inversions checked with nested `G` over step supports.",
            "",
            "`ltl_invariant_corroboration_rate` counts the three static formulas that mirror invariant failures (`ltl_contradiction`, `ltl_temporal_inconsistency`, `ltl_hallucinated_node`). These are useful for trace localisation but should be reported separately from genuine trace-level signal.",
            "",
        ]
    )
    report_lines.extend(
        _markdown_table(
            summary_rows,
            columns=[
                "model_label",
                "ltl_genuine_violation_rate",
                "ltl_invariant_corroboration_rate",
            ],
        )
    )
    # Gemma-paradox note: a model with perfect intrinsic validity but zero contradiction
    # detection demonstrates why intrinsic-only scoring is insufficient.
    if has_contradiction:
        paradox_models = [
            row["model_label"]
            for row in summary_rows
            if float(row.get("conditional_validity_rate") or 0.0) >= 0.99
            and float(row.get("contradiction_detection_rate") or 0.0) == 0.0
        ]
        for paradox_model in paradox_models:
            report_lines.append(
                f"\n> **Note ({paradox_model})**: `conditional_validity_rate ≈ 1.0` and "
                f"`contradiction_detection_rate = 0.0`. A model that abstains universally on "
                f"contradiction items looks clean under intrinsic checks but fails the task. "
                f"This demonstrates why intrinsic-only scoring is insufficient — both intrinsic "
                f"validity and task correctness must be evaluated together."
            )
    category_focus_rows = [
        row
        for row in category_rows
        if (
            row.get("category")
            in {"ambiguous", "contradiction", "linear_chain", "transitive_reasoning"}
            or is_single_category
        )
    ]
    if category_focus_rows:
        category_columns = [
            "model_label",
            "category",
            "num_tasks",
            "parse_success_rate",
            "validity_expectation_alignment_rate_e2e",
            "trace_grounding_rate",
            "direct_f1",
            "closure_f1",
        ]
        if has_ambiguity:
            category_columns.extend(["abstention_rate", "overcommitment_rate"])
        if has_contradiction:
            category_columns.append("contradiction_detection_rate")
        report_lines.extend(["", "## Category Notes", ""])
        report_lines.extend(
            _markdown_table(
                category_focus_rows,
                columns=category_columns,
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
            "- `validity_expectation_alignment_rate.png`: whether valid versus invalid outputs match task expectations end-to-end.",
            "- `direct_vs_closure_f1.png`: representation fidelity versus ordering recovery on gold-bearing tasks only.",
            "- `verification_task_incidence.png`: task-level prevalence of invariant failure modes.",
            "- `ltl_task_incidence.png`: task-level prevalence of all LTL formula failures.",
            "- `genuine_ltl_incidence.png`: separates genuine trace-level LTL signal from invariant-corroborating LTL.",
        ]
    )
    if has_ambiguity:
        report_lines.insert(
            report_lines.index(
                "- `verification_task_incidence.png`: task-level prevalence of invariant failure modes."
            ),
            "- `ambiguity_behaviour.png`: abstention discipline versus overcommitment.",
        )
    if has_contradiction:
        report_lines.insert(
            report_lines.index(
                "- `verification_task_incidence.png`: task-level prevalence of invariant failure modes."
            ),
            "- `contradiction_detection_rate.png`: conditional consistency-focused performance on parsed contradiction tasks.",
        )
    if correlation_prose_blocks:
        report_lines.extend(["", "## Axis Correlation", ""])
        report_lines.extend(
            [
                "Pairwise Pearson / phi correlations across intrinsic axes (parse_success, "
                "verifier_valid, trace_grounded). High correlation indicates the axes provide "
                "largely redundant signal; low correlation indicates they measure distinct things.",
                "",
            ]
        )
        report_lines.extend(correlation_prose_blocks)
        report_lines.append(
            "\nSee `axis_correlation_*.csv` and `axis_correlation_*.png` for full matrices."
        )
    return "\n".join(report_lines) + "\n"


def summarise_runs(
    run_dirs: Sequence[str | Path],
    *,
    out_dir: str | Path,
    manifest_path: str | Path | None = None,
    predictions_filename: str = "predictions.jsonl",
) -> Dict[str, Any]:
    runs = load_runs(
        run_dirs,
        manifest_path=manifest_path,
        predictions_filename=predictions_filename,
    )
    summary_rows = [_run_row(run) for run in runs]
    category_rows = [
        row
        for run in runs
        for row in _group_tasks_by_dimension(run, dimension="category")
    ]
    difficulty_rows = [
        row
        for run in runs
        for row in _group_tasks_by_dimension(run, dimension="difficulty")
    ]
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
    (out_path / "counterexamples.md").write_text(
        "\n".join(counterexample_text), encoding="utf-8"
    )

    # Per-run axis correlation artefacts (CSV + heatmap PNG)
    correlation_prose_blocks: List[str] = []
    for run in runs:
        flags = extract_flags(run.predictions, run.report.get("failures", []))
        corr_result = compute_axis_correlation(flags)
        run_slug = run.label.replace(" ", "_").replace("/", "-")
        save_axis_correlation_csv(
            corr_result, out_path / f"axis_correlation_{run_slug}.csv"
        )
        plot_axis_correlation(
            corr_result, out_path / f"axis_correlation_{run_slug}.png"
        )
        prose = axis_correlation_prose(corr_result)
        if prose:
            correlation_prose_blocks.append(f"**{run.label}**: {prose}")

    (out_path / "report.md").write_text(
        _narrative_report(summary_rows, category_rows, correlation_prose_blocks),
        encoding="utf-8",
    )

    _generate_plots(out_path, summary_rows, category_rows, failure_rows)
    return {
        "summary": summary_rows,
        "category_breakdown": category_rows,
        "difficulty_breakdown": difficulty_rows,
        "failure_breakdown": failure_rows,
    }
