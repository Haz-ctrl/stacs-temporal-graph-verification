"""
Verifier-to-correctness correlation analysis for RQ3.

RQ3 is reframed as: Are verifier signals (including genuine LTL trace-level
violations) correlated with task correctness, and how does the predictive power
vary across models? The original comparison against self-reported confidence is
not possible because models consistently return null confidence values. The
analysis instead compares structural verifier signals against each other and
against task correctness.

Signals measured per task:
  - is_valid: binary graph validity flag from the verifier
  - trace_grounded: binary trace groundedness flag
  - violation_count: total structural violation count (sum of violation_counts dict)
  - first_violation_step: step index of first violation (NaN when no violation occurred)
  - ltl_genuine_violation_count: unsupported final commitment + trace inversion count
  - ltl_corroboration_count: invariant-corroborating LTL count

Correctness: binary — 1 if score.direct.correct > 0, else 0. Tasks with no
gold_relations are excluded from all computations.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from scipy.stats import pointbiserialr, spearmanr


_SIGNALS: Tuple[Tuple[str, str, bool], ...] = (
    ("is_valid", "Graph validity flag (binary)", True),
    ("trace_grounded", "Reasoning trace groundedness (binary)", True),
    ("violation_count", "Total structural violation count", False),
    ("first_violation_step", "Step index of first violation (NaN when none)", False),
    (
        "ltl_genuine_violation_count",
        "Count of genuine LTL violations (unsupported_commitment + trace_inversion)",
        False,
    ),
    (
        "ltl_corroboration_count",
        "Count of invariant-corroborating LTL violations (contradiction + inconsistency + hallucination)",
        False,
    ),
)


@dataclass(frozen=True)
class CorrelationResult:
    signal: str
    description: str
    n: int
    spearman_rho: float
    spearman_p: float
    point_biserial_r: Optional[float]
    point_biserial_p: Optional[float]


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _extract_verifier_signals(record: Mapping[str, Any]) -> Dict[str, float]:
    """Extract numeric verifier signals from a prediction record."""
    verification = record.get("verification", {})
    is_valid = 1.0 if bool(verification.get("is_valid", False)) else 0.0
    trace_grounded = 1.0 if bool(verification.get("trace_grounded", True)) else 0.0
    vc = verification.get("violation_counts", {})
    violation_count = float(sum(vc.values())) if isinstance(vc, dict) else 0.0
    fvc = verification.get("formula_violation_counts", {})
    genuine_ltl_count = (
        float(
            fvc.get("ltl_unsupported_final_commitment", 0)
            + fvc.get("ltl_trace_inversion", 0)
        )
        if isinstance(fvc, dict)
        else 0.0
    )
    corroboration_count = (
        float(
            fvc.get("ltl_contradiction", 0)
            + fvc.get("ltl_temporal_inconsistency", 0)
            + fvc.get("ltl_hallucinated_node", 0)
        )
        if isinstance(fvc, dict)
        else 0.0
    )
    fvs = verification.get("first_violation_step")
    first_violation_step = float(fvs) if fvs is not None else float("nan")
    return {
        "is_valid": is_valid,
        "trace_grounded": trace_grounded,
        "violation_count": violation_count,
        "first_violation_step": first_violation_step,
        "ltl_genuine_violation_count": genuine_ltl_count,
        "ltl_corroboration_count": corroboration_count,
    }


def _extract_correctness(record: Mapping[str, Any]) -> Optional[float]:
    """Return 1.0 if direct.correct > 0, 0.0 if not, None if no gold_relations."""
    if not record.get("gold_relations"):
        return None
    correct = int(record.get("score", {}).get("direct", {}).get("correct", 0))
    return 1.0 if correct > 0 else 0.0


def _spearman_safe(xs: Sequence[float], ys: Sequence[float]) -> Tuple[float, float]:
    """Spearman correlation dropping NaN pairs; returns (nan, nan) for n < 5."""
    pairs = [(x, y) for x, y in zip(xs, ys) if not (math.isnan(x) or math.isnan(y))]
    if len(pairs) < 5:
        return (float("nan"), float("nan"))
    xs_clean, ys_clean = zip(*pairs)
    result = spearmanr(xs_clean, ys_clean)
    return (float(result.statistic), float(result.pvalue))


def _pointbiserial_safe(
    xs: Sequence[float], ys: Sequence[float]
) -> Tuple[Optional[float], Optional[float]]:
    """Point-biserial correlation dropping NaN pairs; returns (None, None) for n < 5."""
    pairs = [(x, y) for x, y in zip(xs, ys) if not (math.isnan(x) or math.isnan(y))]
    if len(pairs) < 5:
        return (None, None)
    xs_clean, ys_clean = zip(*pairs)
    result = pointbiserialr(xs_clean, ys_clean)
    return (float(result.statistic), float(result.pvalue))


def analyse_run(
    predictions_path: Path,
    *,
    model_label: str = "",
    dataset: str = "",
) -> List[CorrelationResult]:
    """
    Compute verifier-to-correctness correlations from a predictions.jsonl file.

    Excludes tasks with no gold_relations. Returns one CorrelationResult per
    verifier signal defined in _SIGNALS.

    Args:
        predictions_path: Path to predictions.jsonl for a completed run.
        model_label: Human-readable model identifier (for caller use; not used internally).
        dataset: Dataset identifier (for caller use; not used internally).

    Returns:
        List of CorrelationResult, one per verifier signal.
    """
    records = _read_jsonl(predictions_path)

    correctness_values: List[float] = []
    signal_values: Dict[str, List[float]] = {name: [] for name, _, _ in _SIGNALS}

    for record in records:
        c = _extract_correctness(record)
        if c is None:
            continue
        sigs = _extract_verifier_signals(record)
        correctness_values.append(c)
        for name, _, _ in _SIGNALS:
            signal_values[name].append(sigs[name])

    results: List[CorrelationResult] = []
    for name, description, is_binary in _SIGNALS:
        xs = signal_values[name]
        rho, sp = _spearman_safe(xs, correctness_values)
        pairs_clean = [(x, y) for x, y in zip(xs, correctness_values) if not math.isnan(x)]
        n = len(pairs_clean)
        if is_binary:
            pbr, pbp = _pointbiserial_safe(xs, correctness_values)
        else:
            pbr, pbp = None, None
        results.append(
            CorrelationResult(
                signal=name,
                description=description,
                n=n,
                spearman_rho=rho,
                spearman_p=sp,
                point_biserial_r=pbr,
                point_biserial_p=pbp,
            )
        )
    return results


def batch_analyse(
    run_spec: List[Tuple[Path, str, str]],
) -> List[dict]:
    """
    Analyse multiple runs and return a flat list of dicts for DataFrame construction.

    Args:
        run_spec: List of (predictions_path, model_label, dataset_label) tuples.

    Returns:
        Flat list of dicts, one per (run, signal) combination.
    """
    rows: List[dict] = []
    for path, model_label, dataset_label in run_spec:
        results = analyse_run(path, model_label=model_label, dataset=dataset_label)
        for result in results:
            rows.append(
                {
                    "model_label": model_label,
                    "dataset": dataset_label,
                    "signal": result.signal,
                    "description": result.description,
                    "n": result.n,
                    "spearman_rho": result.spearman_rho,
                    "spearman_p": result.spearman_p,
                    "point_biserial_r": result.point_biserial_r,
                    "point_biserial_p": result.point_biserial_p,
                }
            )
    return rows
