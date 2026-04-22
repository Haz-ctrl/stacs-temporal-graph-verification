from __future__ import annotations

from src.run_summary import _aggregate_prf_from_rows, _closure_coverage, _committed_closure_prf


def _make_row(
    *,
    gold_total: int,
    pred_total: int,
    correct: int,
    has_gold_relations: bool = True,
) -> dict:
    """Build a minimal predictions.jsonl-style record for testing coverage helpers."""
    return {
        "gold_relations": [["A", "B", "BEFORE"]] if has_gold_relations else [],
        "expected_valid": True,
        "score": {
            "closure": {
                "correct": correct,
                "pred_total": pred_total,
                "gold_total": gold_total,
            }
        },
    }


# ---------------------------------------------------------------------------
# _closure_coverage
# ---------------------------------------------------------------------------


def test_closure_coverage_partial_commitment() -> None:
    # 3 gold-bearing tasks (gold_total>0): 2 committed, 1 UNKNOWN prediction
    rows = [
        _make_row(gold_total=1, pred_total=1, correct=1),
        _make_row(gold_total=1, pred_total=1, correct=1),
        _make_row(gold_total=1, pred_total=0, correct=0),  # UNKNOWN pred
    ]

    coverage = _closure_coverage(rows)

    assert coverage is not None
    assert abs(coverage - 2 / 3) < 1e-9


def test_closure_coverage_full_commitment() -> None:
    rows = [
        _make_row(gold_total=1, pred_total=1, correct=1),
        _make_row(gold_total=1, pred_total=1, correct=1),
    ]

    assert _closure_coverage(rows) == 1.0


def test_closure_coverage_zero_when_all_unknown() -> None:
    # Edge case: model commits to nothing on every gold-bearing task
    rows = [
        _make_row(gold_total=1, pred_total=0, correct=0),
        _make_row(gold_total=1, pred_total=0, correct=0),
    ]

    assert _closure_coverage(rows) == 0.0


def test_closure_coverage_none_when_no_gold_bearing() -> None:
    # All tasks have gold_total=0 (e.g. all SIMULTANEOUS gold, single-pair tasks)
    rows = [
        _make_row(gold_total=0, pred_total=1, correct=0),
    ]

    assert _closure_coverage(rows) is None


def test_closure_coverage_none_when_empty_input() -> None:
    assert _closure_coverage([]) is None


# ---------------------------------------------------------------------------
# _committed_closure_prf
# ---------------------------------------------------------------------------


def test_committed_closure_prf_perfect_on_committed_subset() -> None:
    # 2 committed tasks correct, 1 UNKNOWN pred task (excluded from committed calc)
    rows = [
        _make_row(gold_total=1, pred_total=1, correct=1),
        _make_row(gold_total=1, pred_total=1, correct=1),
        _make_row(gold_total=1, pred_total=0, correct=0),  # excluded
    ]

    result = _committed_closure_prf(rows)

    # Only the 2 committed tasks count: correct=2, pred=2, gold=2 → F1=1.0
    assert result["f1"] == 1.0
    assert result["correct"] == 2
    assert result["pred_total"] == 2
    assert result["gold_total"] == 2


def test_committed_closure_prf_zero_f1_when_no_committed_tasks() -> None:
    # Edge case: model commits to zero orderings across all gold-bearing tasks
    rows = [
        _make_row(gold_total=1, pred_total=0, correct=0),
        _make_row(gold_total=1, pred_total=0, correct=0),
    ]

    result = _committed_closure_prf(rows)

    # No committed rows → aggregate over empty list → f1=0.0 (both P and R are 0)
    assert result["f1"] == 0.0
    assert result["correct"] == 0
    assert result["pred_total"] == 0
    assert result["gold_total"] == 0


# ---------------------------------------------------------------------------
# Relationship between committed, full, and coverage
# ---------------------------------------------------------------------------


def test_full_f1_lower_than_committed_when_abstentions_present() -> None:
    # 2 correct committed + 1 UNKNOWN abstention (lowers full recall)
    rows = [
        _make_row(gold_total=1, pred_total=1, correct=1),
        _make_row(gold_total=1, pred_total=1, correct=1),
        _make_row(gold_total=1, pred_total=0, correct=0),
    ]

    committed = _committed_closure_prf(rows)
    # Full uses _aggregate_prf_from_rows on ALL rows (including the abstained one)
    full_agg = _aggregate_prf_from_rows(rows, metric_key="closure")

    # Committed F1 should be strictly higher (or equal) than full F1
    assert committed["f1"] >= full_agg["f1"]
    # Coverage is 2/3, less than 1.0
    assert _closure_coverage(rows) < 1.0
