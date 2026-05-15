from __future__ import annotations

import math

from src.analysis.axis_correlation import (
    _pearson,
    axis_correlation_prose,
    compute_axis_correlation,
    extract_flags,
)


# ---------------------------------------------------------------------------
# _pearson helpers
# ---------------------------------------------------------------------------


def test_pearson_identical_sequences_is_one() -> None:
    xs = [1, 0, 1, 0]
    assert abs(_pearson(xs, xs) - 1.0) < 1e-9  # type: ignore[arg-type]


def test_pearson_opposite_sequences_is_minus_one() -> None:
    xs = [1, 0, 1, 0]
    ys = [0, 1, 0, 1]
    assert abs(_pearson(xs, ys) - (-1.0)) < 1e-9  # type: ignore[arg-type]


def test_pearson_constant_sequence_is_none() -> None:
    # When one variable is constant, correlation is undefined
    assert _pearson([1, 1, 1, 1], [0, 1, 0, 1]) is None  # type: ignore[arg-type]


def test_pearson_too_short_is_none() -> None:
    assert _pearson([1], [0]) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# compute_axis_correlation
# ---------------------------------------------------------------------------


def _make_flags(
    *,
    parse_success: list[bool],
    verifier_valid: list[bool],
    trace_grounded: list[bool],
) -> list[dict[str, bool]]:
    return [
        {"parse_success": p, "verifier_valid": v, "trace_grounded": t}
        for p, v, t in zip(parse_success, verifier_valid, trace_grounded)
    ]


def test_fully_correlated_pair_gives_pearson_one() -> None:
    # verifier_valid == trace_grounded throughout
    flags = _make_flags(
        parse_success=[True, True, True, True],
        verifier_valid=[True, True, False, False],
        trace_grounded=[True, True, False, False],
    )

    result = compute_axis_correlation(flags)

    r = result.pearson[("verifier_valid", "trace_grounded")]
    assert abs(r - 1.0) < 1e-9


def test_anti_correlated_pair_gives_pearson_minus_one() -> None:
    flags = _make_flags(
        parse_success=[True, True, True, True],
        verifier_valid=[True, False, True, False],
        trace_grounded=[False, True, False, True],
    )

    result = compute_axis_correlation(flags)

    r = result.pearson[("verifier_valid", "trace_grounded")]
    assert abs(r - (-1.0)) < 1e-9


def test_constant_parse_success_gives_nan() -> None:
    # All tasks parsed → parse_success is constant → correlation with others = NaN
    flags = _make_flags(
        parse_success=[True, True, True, True],
        verifier_valid=[True, False, True, False],
        trace_grounded=[True, True, False, False],
    )

    result = compute_axis_correlation(flags)

    assert math.isnan(result.pearson[("parse_success", "verifier_valid")])
    assert math.isnan(result.pearson[("parse_success", "trace_grounded")])


def test_agreement_count_correct() -> None:
    flags = _make_flags(
        parse_success=[True, True, True, True],
        verifier_valid=[True, True, False, False],
        trace_grounded=[True, True, False, False],  # always agrees with verifier_valid
    )

    result = compute_axis_correlation(flags)

    assert result.agreement[("verifier_valid", "trace_grounded")] == 4


def test_n_equals_total_tasks() -> None:
    flags = _make_flags(
        parse_success=[True, True, False],
        verifier_valid=[True, False, False],
        trace_grounded=[True, False, False],
    )
    result = compute_axis_correlation(flags)
    assert result.n == 3


# ---------------------------------------------------------------------------
# extract_flags
# ---------------------------------------------------------------------------


def test_extract_flags_parsed_row() -> None:
    predictions = [
        {
            "verification": {
                "is_valid": True,
                "trace_grounded": False,
            }
        }
    ]
    flags = extract_flags(predictions, [])

    assert flags == [
        {"parse_success": True, "verifier_valid": True, "trace_grounded": False}
    ]


def test_extract_flags_failure_row_all_false() -> None:
    flags = extract_flags([], [{"id": "fail_001"}])

    assert flags == [
        {"parse_success": False, "verifier_valid": False, "trace_grounded": False}
    ]


# ---------------------------------------------------------------------------
# axis_correlation_prose
# ---------------------------------------------------------------------------


def test_prose_reports_collinear_pair() -> None:
    flags = _make_flags(
        parse_success=[True, True, True, True],
        verifier_valid=[True, True, False, False],
        trace_grounded=[
            True,
            True,
            False,
            False,
        ],  # fully correlated with verifier_valid
    )
    result = compute_axis_correlation(flags)
    prose = axis_correlation_prose(result)

    assert "Collinear" in prose
    assert "verifier_valid" in prose
    assert "trace_grounded" in prose


def test_prose_empty_when_no_valid_pairs() -> None:
    # Only 1 task — too short for Pearson
    flags = _make_flags(
        parse_success=[True],
        verifier_valid=[True],
        trace_grounded=[True],
    )
    result = compute_axis_correlation(flags)
    prose = axis_correlation_prose(result)

    assert prose == ""
