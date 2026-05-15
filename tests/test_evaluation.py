from __future__ import annotations

from src.evaluation import (
    PRFResult,
    canonical_edge_set,
    closure_prf,
    compute_prf,
    direct_edge_prf,
    normalise_pred_labels,
    score_prediction,
)
from src.schemas import ReasoningStep


# ---------------------------------------------------------------------------
# Edge canonicalisation and PRF helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Direct-edge scoring
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Closure scoring
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Prediction-level scoring
# ---------------------------------------------------------------------------


def test_score_prediction_reports_closure_equivalent_extra_edge_without_invalidating() -> (
    None
):
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


# ---------------------------------------------------------------------------
# Symmetric relation scoring
# ---------------------------------------------------------------------------


def test_direct_edge_prf_after_is_symmetric_with_reversed_before() -> None:
    """AFTER(A, B) and BEFORE(B, A) are semantically identical; direct F1 must be 1.0."""
    gold = [("A [ei1]", "B [ei2]", "AFTER")]
    pred = [("B [ei2]", "A [ei1]", "BEFORE")]

    result = direct_edge_prf(gold, pred)

    assert result.f1 == 1.0
    assert result.precision == 1.0
    assert result.recall == 1.0


def test_direct_edge_prf_after_wrong_direction_scores_zero() -> None:
    """AFTER(A, B) and BEFORE(A, B) are contradictory; direct F1 must be 0.0."""
    gold = [("A [ei1]", "B [ei2]", "AFTER")]
    pred = [("A [ei1]", "B [ei2]", "BEFORE")]

    result = direct_edge_prf(gold, pred)

    assert result.f1 == 0.0


def test_direct_edge_prf_before_symmetric_with_reversed_after() -> None:
    """BEFORE(A, B) and AFTER(B, A) are semantically identical; direct F1 must be 1.0."""
    gold = [("A [ei1]", "B [ei2]", "BEFORE")]
    pred = [("B [ei2]", "A [ei1]", "AFTER")]

    result = direct_edge_prf(gold, pred)

    assert result.f1 == 1.0


def test_direct_edge_prf_simultaneous_is_symmetric() -> None:
    """SIMULTANEOUS(A, B) and SIMULTANEOUS(B, A) are semantically identical."""
    gold = [("A [ei1]", "B [ei2]", "SIMULTANEOUS")]
    pred = [("B [ei2]", "A [ei1]", "SIMULTANEOUS")]

    result = direct_edge_prf(gold, pred)

    assert result.f1 == 1.0
    assert result.precision == 1.0
    assert result.recall == 1.0


def test_score_prediction_direct_diagnostics_use_symmetric_edges() -> None:
    """Equivalent AFTER/BEFORE orientations must not be reported missing/spurious."""
    score = score_prediction(
        allowed_events=["A [ei1]", "B [ei2]"],
        gold_edges=[("A [ei1]", "B [ei2]", "AFTER")],
        pred_edges=[("B [ei2]", "A [ei1]", "BEFORE")],
    )

    assert score.direct.f1 == 1.0
    assert score.missing_direct_edges == []
    assert score.spurious_direct_edges == []


# ---------------------------------------------------------------------------
# Prediction label normalisation
# ---------------------------------------------------------------------------


def test_normalise_pred_labels_remaps_stripped_trigger_word() -> None:
    """Model emits bare trigger word; should be remapped to canonical label."""
    task_events = ["started [ei3]", "ended [ei6]"]
    pred_events = ["started", "ended"]
    pred_edges = [("started", "ended", "BEFORE")]
    reasoning_steps: list[ReasoningStep] = []

    norm_events, norm_edges, norm_steps = normalise_pred_labels(
        pred_events=pred_events,
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
        task_events=task_events,
    )

    assert norm_events == ["started [ei3]", "ended [ei6]"]
    assert norm_edges == [("started [ei3]", "ended [ei6]", "BEFORE")]
    assert norm_steps == []


def test_normalise_pred_labels_remaps_case_mismatch() -> None:
    """Model emits wrong capitalisation in [eiN] label; should be remapped."""
    task_events = ["bailed [ei6]", "havoc [ei4]"]
    pred_events = ["bAILED [ei6]", "havoc [ei4]"]
    pred_edges = [("bAILED [ei6]", "havoc [ei4]", "BEFORE")]
    reasoning_steps: list[ReasoningStep] = []

    norm_events, norm_edges, _ = normalise_pred_labels(
        pred_events=pred_events,
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
        task_events=task_events,
    )

    assert norm_events == ["bailed [ei6]", "havoc [ei4]"]
    assert norm_edges == [("bailed [ei6]", "havoc [ei4]", "BEFORE")]


def test_normalise_pred_labels_leaves_genuine_hallucination_unchanged() -> None:
    """A node that has no match in task_events should not be remapped."""
    task_events = ["started [ei3]", "ended [ei6]"]
    pred_events = ["started", "invented_event_not_in_task"]
    pred_edges = [("started", "invented_event_not_in_task", "BEFORE")]
    reasoning_steps: list[ReasoningStep] = []

    norm_events, norm_edges, _ = normalise_pred_labels(
        pred_events=pred_events,
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
        task_events=task_events,
    )

    assert norm_events[0] == "started [ei3]"
    assert norm_events[1] == "invented_event_not_in_task"
    assert norm_edges == [("started [ei3]", "invented_event_not_in_task", "BEFORE")]


def test_normalise_pred_labels_remaps_reasoning_step_supports() -> None:
    """Remapping must be applied to support edges inside reasoning steps."""
    task_events = ["started [ei3]", "ended [ei6]"]
    pred_events = ["started", "ended"]
    pred_edges = [("started", "ended", "BEFORE")]
    step = ReasoningStep(
        step_id=1,
        text="started happened before ended",
        supports=[("started", "ended", "BEFORE")],
    )

    _, _, norm_steps = normalise_pred_labels(
        pred_events=pred_events,
        pred_edges=pred_edges,
        reasoning_steps=[step],
        task_events=task_events,
    )

    assert len(norm_steps) == 1
    assert norm_steps[0].supports == [("started [ei3]", "ended [ei6]", "BEFORE")]


def test_normalise_pred_labels_no_op_when_labels_already_canonical() -> None:
    """When pred labels already match task events exactly, nothing changes."""
    task_events = ["started [ei3]", "ended [ei6]"]
    pred_events = ["started [ei3]", "ended [ei6]"]
    pred_edges = [("started [ei3]", "ended [ei6]", "BEFORE")]

    norm_events, norm_edges, _ = normalise_pred_labels(
        pred_events=pred_events,
        pred_edges=pred_edges,
        reasoning_steps=[],
        task_events=task_events,
    )

    assert norm_events == task_events
    assert norm_edges == pred_edges


def test_normalise_pred_labels_ambiguous_trigger_is_not_remapped() -> None:
    """Two events sharing the same trigger word -> trigger-only lookup omitted."""
    task_events = ["said [ei9]", "said [ei20]"]
    pred_events = ["said"]
    pred_edges: list = []

    norm_events, _, _ = normalise_pred_labels(
        pred_events=pred_events,
        pred_edges=pred_edges,
        reasoning_steps=[],
        task_events=task_events,
    )

    assert norm_events == ["said"]
