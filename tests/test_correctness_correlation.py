"""Tests for src/analysis/correctness_correlation.py."""

from __future__ import annotations

import json
import math
import warnings
from pathlib import Path

from src.analysis.correctness_correlation import (
    _extract_correctness,
    _extract_verifier_signals,
    _pointbiserial_safe,
    _spearman_safe,
    analyse_run,
    batch_analyse,
)


# ---------------------------------------------------------------------------
# _extract_correctness
# ---------------------------------------------------------------------------


def _make_record(
    *, correct: int = 0, gold_relations=None, is_valid: bool = True
) -> dict:
    if gold_relations is None:
        gold_relations = [["A", "B", "BEFORE"]]
    return {
        "gold_relations": gold_relations,
        "verification": {
            "is_valid": is_valid,
            "trace_grounded": True,
            "violation_counts": {},
            "formula_violation_counts": {},
            "first_violation_step": None,
        },
        "score": {
            "direct": {"correct": correct, "pred_total": 1, "gold_total": 1},
        },
    }


def test_extract_correctness_positive_when_correct_gt_zero() -> None:
    record = _make_record(correct=2)
    assert _extract_correctness(record) == 1.0


def test_extract_correctness_zero_when_no_correct() -> None:
    record = _make_record(correct=0)
    assert _extract_correctness(record) == 0.0


def test_extract_correctness_none_for_empty_gold() -> None:
    record = _make_record(correct=1, gold_relations=[])
    assert _extract_correctness(record) is None


def test_extract_correctness_none_for_absent_gold() -> None:
    record = {"score": {"direct": {"correct": 1}}}
    assert _extract_correctness(record) is None


# ---------------------------------------------------------------------------
# _extract_verifier_signals
# ---------------------------------------------------------------------------


def test_extract_signals_binary_flags() -> None:
    record = _make_record(is_valid=True)
    sigs = _extract_verifier_signals(record)
    assert sigs["is_valid"] == 1.0
    assert sigs["trace_grounded"] == 1.0


def test_extract_signals_violation_count_summed() -> None:
    record = {
        "verification": {
            "is_valid": False,
            "trace_grounded": False,
            "violation_counts": {"cycle": 2, "contradiction": 1},
            "formula_violation_counts": {},
            "first_violation_step": 3,
        }
    }
    sigs = _extract_verifier_signals(record)
    assert sigs["violation_count"] == 3.0
    assert sigs["first_violation_step"] == 3.0
    assert sigs["is_valid"] == 0.0


def test_extract_signals_nan_when_no_violation() -> None:
    record = _make_record()
    sigs = _extract_verifier_signals(record)
    assert math.isnan(sigs["first_violation_step"])


def test_extract_signals_ltl_counts_split() -> None:
    record = {
        "verification": {
            "is_valid": False,
            "trace_grounded": True,
            "violation_counts": {},
            "formula_violation_counts": {
                "ltl_unsupported_final_commitment": 2,
                "ltl_trace_inversion": 1,
                "ltl_contradiction": 1,
                "ltl_temporal_inconsistency": 1,
                "ltl_hallucinated_node": 3,
            },
            "first_violation_step": 1,
        }
    }
    sigs = _extract_verifier_signals(record)
    assert sigs["ltl_genuine_violation_count"] == 3.0
    assert sigs["ltl_corroboration_count"] == 5.0


# ---------------------------------------------------------------------------
# _spearman_safe
# ---------------------------------------------------------------------------


def test_spearman_safe_known_perfect_correlation() -> None:
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [1.0, 2.0, 3.0, 4.0, 5.0]
    rho, p = _spearman_safe(xs, ys)
    assert abs(rho - 1.0) < 1e-6
    assert p < 0.05


def test_spearman_safe_known_anti_correlation() -> None:
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [5.0, 4.0, 3.0, 2.0, 1.0]
    rho, p = _spearman_safe(xs, ys)
    assert abs(rho - (-1.0)) < 1e-6


def test_spearman_safe_nan_pairs_dropped() -> None:
    xs = [float("nan"), 1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    rho, p = _spearman_safe(xs, ys)
    # NaN pair dropped; remaining 5 pairs are perfectly correlated
    assert abs(rho - 1.0) < 1e-6


def test_spearman_safe_returns_nan_for_n_lt_5() -> None:
    xs = [1.0, 2.0, 3.0]
    ys = [1.0, 2.0, 3.0]
    rho, p = _spearman_safe(xs, ys)
    assert math.isnan(rho)
    assert math.isnan(p)


def test_spearman_safe_returns_nan_for_empty() -> None:
    rho, p = _spearman_safe([], [])
    assert math.isnan(rho)
    assert math.isnan(p)


def test_spearman_safe_returns_nan_without_warning_for_constant_input() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rho, p = _spearman_safe([0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 1.0, 0.0])

    assert caught == []
    assert math.isnan(rho)
    assert math.isnan(p)


# ---------------------------------------------------------------------------
# _pointbiserial_safe
# ---------------------------------------------------------------------------


def test_pointbiserial_returns_none_for_n_lt_5() -> None:
    r, p = _pointbiserial_safe([0.0, 1.0, 0.0], [1.0, 0.0, 1.0])
    assert r is None
    assert p is None


def test_pointbiserial_returns_values_for_sufficient_data() -> None:
    xs = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    ys = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    r, p = _pointbiserial_safe(xs, ys)
    assert r is not None
    assert p is not None
    assert abs(r - 1.0) < 1e-6


def test_pointbiserial_returns_none_without_warning_for_constant_input() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r, p = _pointbiserial_safe([1.0, 1.0, 1.0, 1.0, 1.0], [0.0, 1.0, 0.0, 1.0, 0.0])

    assert caught == []
    assert r is None
    assert p is None


# ---------------------------------------------------------------------------
# analyse_run integration
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, records: list) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for rec in records:
            handle.write(json.dumps(rec) + "\n")


def _make_prediction_record(
    *, task_id: str, correct: int, is_valid: bool, violation_count: int = 0
) -> dict:
    return {
        "id": task_id,
        "gold_relations": [["A", "B", "BEFORE"]],
        "verification": {
            "is_valid": is_valid,
            "trace_grounded": is_valid,
            "violation_counts": {"cycle": violation_count} if violation_count else {},
            "formula_violation_counts": {},
            "first_violation_step": 1 if violation_count else None,
        },
        "score": {
            "direct": {"correct": correct, "pred_total": 1, "gold_total": 1},
        },
    }


def test_analyse_run_returns_six_signals(tmp_path: Path) -> None:
    records = [
        _make_prediction_record(task_id=f"t{i}", correct=i % 2, is_valid=bool(i % 2))
        for i in range(10)
    ]
    preds_path = tmp_path / "predictions.jsonl"
    _write_jsonl(preds_path, records)

    results = analyse_run(preds_path)

    assert len(results) == 6
    signal_names = {r.signal for r in results}
    assert signal_names == {
        "is_valid",
        "trace_grounded",
        "violation_count",
        "first_violation_step",
        "ltl_genuine_violation_count",
        "ltl_corroboration_count",
    }


def test_analyse_run_excludes_empty_gold(tmp_path: Path) -> None:
    records = [
        _make_prediction_record(task_id="with_gold", correct=1, is_valid=True),
        {
            "id": "no_gold",
            "gold_relations": [],
            "verification": {
                "is_valid": True,
                "trace_grounded": True,
                "violation_counts": {},
                "formula_violation_counts": {},
                "first_violation_step": None,
            },
            "score": {"direct": {"correct": 0, "pred_total": 0, "gold_total": 0}},
        },
    ] * 5  # pad to n >= 5 for non-nan results
    preds_path = tmp_path / "predictions.jsonl"
    _write_jsonl(preds_path, records)

    results = analyse_run(preds_path)

    # n should only count gold-bearing tasks
    is_valid_result = next(r for r in results if r.signal == "is_valid")
    assert is_valid_result.n == 5


def test_analyse_run_graceful_for_few_tasks(tmp_path: Path) -> None:
    records = [
        _make_prediction_record(task_id="t1", correct=1, is_valid=True),
        _make_prediction_record(task_id="t2", correct=0, is_valid=False),
    ]
    preds_path = tmp_path / "predictions.jsonl"
    _write_jsonl(preds_path, records)

    results = analyse_run(preds_path)

    for result in results:
        assert math.isnan(result.spearman_rho)
        assert math.isnan(result.spearman_p)


def test_analyse_run_spearman_for_known_sequence(tmp_path: Path) -> None:
    # is_valid perfectly predicts correctness across 10 tasks
    records = [
        _make_prediction_record(task_id=f"t{i}", correct=i % 2, is_valid=bool(i % 2))
        for i in range(10)
    ]
    preds_path = tmp_path / "predictions.jsonl"
    _write_jsonl(preds_path, records)

    results = analyse_run(preds_path)
    is_valid_result = next(r for r in results if r.signal == "is_valid")

    assert abs(is_valid_result.spearman_rho - 1.0) < 1e-6
    assert is_valid_result.point_biserial_r is not None
    assert abs(is_valid_result.point_biserial_r - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# batch_analyse
# ---------------------------------------------------------------------------


def test_batch_analyse_flat_list(tmp_path: Path) -> None:
    records = [
        _make_prediction_record(task_id=f"t{i}", correct=i % 2, is_valid=bool(i % 2))
        for i in range(10)
    ]
    preds_path = tmp_path / "predictions.jsonl"
    _write_jsonl(preds_path, records)

    rows = batch_analyse([(preds_path, "model_A", "synthetic")])

    assert len(rows) == 6
    assert all(r["model_label"] == "model_A" for r in rows)
    assert all(r["dataset"] == "synthetic" for r in rows)
    signals = {r["signal"] for r in rows}
    assert signals == {
        "is_valid",
        "trace_grounded",
        "violation_count",
        "first_violation_step",
        "ltl_genuine_violation_count",
        "ltl_corroboration_count",
    }
