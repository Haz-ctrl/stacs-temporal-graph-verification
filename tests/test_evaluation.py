from __future__ import annotations

from src.evaluation import (
    PRFResult,
    canonical_edge_set,
    closure_prf,
    compute_prf,
    direct_edge_prf,
    score_prediction,
)


def test_canonical_edge_set_normalises_relations() -> None:
    edges = [
        ("A", "B", "before"),
        ["B", "C", "AFTER"],
    ]

    result = canonical_edge_set(edges)

    assert result == {
        ("A", "B", "BEFORE"),
        ("B", "C", "AFTER"),
    }


def test_compute_prf_all_zero_when_no_predictions_and_no_gold() -> None:
    result = compute_prf(correct=0, pred_total=0, gold_total=0)

    assert result == PRFResult(
        precision=0.0,
        recall=0.0,
        f1=0.0,
        correct=0,
        pred_total=0,
        gold_total=0,
    )


def test_compute_prf_correct_values() -> None:
    result = compute_prf(correct=2, pred_total=4, gold_total=5)

    assert result.precision == 0.5
    assert result.recall == 0.4
    assert abs(result.f1 - (2.0 * 0.5 * 0.4 / (0.5 + 0.4))) < 1e-12
    assert result.correct == 2
    assert result.pred_total == 4
    assert result.gold_total == 5


def test_direct_edge_prf_exact_match_is_perfect() -> None:
    gold = [
        ("A", "B", "BEFORE"),
        ("B", "C", "BEFORE"),
    ]
    pred = [
        ("A", "B", "BEFORE"),
        ("B", "C", "BEFORE"),
    ]

    result = direct_edge_prf(gold, pred)

    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.f1 == 1.0
    assert result.correct == 2
    assert result.pred_total == 2
    assert result.gold_total == 2


def test_direct_edge_prf_partial_match() -> None:
    gold = [
        ("A", "B", "BEFORE"),
        ("B", "C", "BEFORE"),
    ]
    pred = [
        ("A", "B", "BEFORE"),
        ("A", "C", "BEFORE"),
    ]

    result = direct_edge_prf(gold, pred)

    assert result.correct == 1
    assert result.pred_total == 2
    assert result.gold_total == 2
    assert result.precision == 0.5
    assert result.recall == 0.5
    assert result.f1 == 0.5


def test_direct_edge_prf_no_predictions() -> None:
    gold = [
        ("A", "B", "BEFORE"),
    ]
    pred: list[tuple[str, str, str]] = []

    result = direct_edge_prf(gold, pred)

    assert result.correct == 0
    assert result.pred_total == 0
    assert result.gold_total == 1
    assert result.precision == 0.0
    assert result.recall == 0.0
    assert result.f1 == 0.0


def test_closure_prf_exact_match_is_perfect() -> None:
    allowed = ["A", "B", "C"]
    gold = [
        ("A", "B", "BEFORE"),
        ("B", "C", "BEFORE"),
    ]
    pred = [
        ("A", "B", "BEFORE"),
        ("B", "C", "BEFORE"),
    ]

    result = closure_prf(allowed, gold, pred)

    assert result.correct == 3
    assert result.pred_total == 3
    assert result.gold_total == 3
    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.f1 == 1.0


def test_closure_prf_rewards_equivalent_implied_structure() -> None:
    allowed = ["A", "B", "C"]
    gold = [
        ("A", "B", "BEFORE"),
        ("B", "C", "BEFORE"),
    ]
    pred = [
        ("A", "C", "BEFORE"),
        ("A", "B", "BEFORE"),
        ("B", "C", "BEFORE"),
    ]

    result = closure_prf(allowed, gold, pred)

    assert result.correct == 3
    assert result.pred_total == 3
    assert result.gold_total == 3
    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.f1 == 1.0


def test_closure_prf_partial_match() -> None:
    allowed = ["A", "B", "C"]
    gold = [
        ("A", "B", "BEFORE"),
        ("B", "C", "BEFORE"),
    ]
    pred = [
        ("A", "B", "BEFORE"),
    ]

    result = closure_prf(allowed, gold, pred)

    assert result.correct == 1
    assert result.pred_total == 1
    assert result.gold_total == 3
    assert result.precision == 1.0
    assert result.recall == (1 / 3)
    assert abs(result.f1 - 0.5) < 1e-12


def test_closure_prf_handles_empty_gold_and_predictions() -> None:
    allowed = ["A", "B"]
    gold: list[tuple[str, str, str]] = []
    pred: list[tuple[str, str, str]] = []

    result = closure_prf(allowed, gold, pred)

    assert result.correct == 0
    assert result.pred_total == 0
    assert result.gold_total == 0
    assert result.precision == 0.0
    assert result.recall == 0.0
    assert result.f1 == 0.0


def test_closure_prf_respects_after_directionality() -> None:
    allowed = ["A", "B"]
    gold = [("A", "B", "BEFORE")]
    pred = [("A", "B", "AFTER")]

    result = closure_prf(allowed, gold, pred)

    assert result.correct == 0
    assert result.pred_total == 1
    assert result.gold_total == 1
    assert result.precision == 0.0
    assert result.recall == 0.0
    assert result.f1 == 0.0


def test_score_prediction_reports_closure_equivalent_extra_edge_without_invalidating() -> None:
    allowed = ["A", "B", "C"]
    gold = [("A", "B", "BEFORE"), ("B", "C", "BEFORE")]
    pred = [("A", "B", "BEFORE"), ("B", "C", "BEFORE"), ("A", "C", "BEFORE")]

    score = score_prediction(allowed_events=allowed, gold_edges=gold, pred_edges=pred)

    assert score.direct.f1 < 1.0
    assert score.closure.f1 == 1.0
    assert score.preserves_ordering_closure is True
    assert score.spurious_direct_edges == [("A", "C", "BEFORE")]


def test_score_prediction_marks_overcommitment_on_gold_empty_prediction() -> None:
    score = score_prediction(
        allowed_events=["A", "B"],
        gold_edges=[],
        pred_edges=[("A", "B", "BEFORE")],
    )

    assert score.has_overcommitment is True
    assert score.abstained is False


def test_aggregate_prf_matches_compute_prf() -> None:
    from src.evaluation import aggregate_prf, compute_prf

    assert aggregate_prf(2, 4, 5) == compute_prf(2, 4, 5)
