from __future__ import annotations

from src.constraints import default_verifier
from src.schemas import ReasoningStep
from src.temporal_graph import TemporalGraph


def _verify(pred_edges, reasoning_steps):
    allowed = ["a", "b"]
    graph = TemporalGraph()
    graph.add_events(allowed)
    graph.add_edges(pred_edges)
    return default_verifier().verify(
        graph,
        allowed_events=allowed,
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
    )


def _formula_types(result) -> set[str]:
    return {violation.type for violation in result.formula_violations}


# ---------------------------------------------------------------------------
# Unsupported final commitments
# ---------------------------------------------------------------------------


def test_unsupported_final_commitment_fires_when_no_step_supports_edge() -> None:
    result = _verify(
        [("a", "b", "BEFORE")],
        [
            ReasoningStep(
                step_id=1, text="No temporal support.", supports=[], confidence=None
            )
        ],
    )

    assert "ltl_unsupported_final_commitment" in _formula_types(result)


def test_unsupported_final_commitment_clear_when_step_supports_edge() -> None:
    result = _verify(
        [("a", "b", "BEFORE")],
        [
            ReasoningStep(
                step_id=1,
                text="a happened before b.",
                supports=[("a", "b", "BEFORE")],
                confidence=None,
            )
        ],
    )

    assert "ltl_unsupported_final_commitment" not in _formula_types(result)


def test_unsupported_final_commitment_accepts_after_support_for_before_edge() -> None:
    result = _verify(
        [("b", "a", "BEFORE")],
        [
            ReasoningStep(
                step_id=1,
                text="a happened after b.",
                supports=[("a", "b", "AFTER")],
                confidence=None,
            )
        ],
    )

    assert "ltl_unsupported_final_commitment" not in _formula_types(result)


def test_unsupported_final_commitment_accepts_before_support_for_after_edge() -> None:
    result = _verify(
        [("a", "b", "AFTER")],
        [
            ReasoningStep(
                step_id=1,
                text="b happened before a.",
                supports=[("b", "a", "BEFORE")],
                confidence=None,
            )
        ],
    )

    assert "ltl_unsupported_final_commitment" not in _formula_types(result)


def test_unsupported_final_commitment_accepts_reversed_simultaneous_support() -> None:
    result = _verify(
        [("a", "b", "SIMULTANEOUS")],
        [
            ReasoningStep(
                step_id=1,
                text="b and a are simultaneous.",
                supports=[("b", "a", "SIMULTANEOUS")],
                confidence=None,
            )
        ],
    )

    assert "ltl_unsupported_final_commitment" not in _formula_types(result)


def test_unknown_edges_exempt_from_unsupported_commitment() -> None:
    result = _verify(
        [("a", "b", "UNKNOWN")],
        [
            ReasoningStep(
                step_id=1, text="Unknown relation.", supports=[], confidence=None
            )
        ],
    )

    assert "ltl_unsupported_final_commitment" not in _formula_types(result)


# ---------------------------------------------------------------------------
# Trace inversion
# ---------------------------------------------------------------------------


def test_trace_inversion_fires_when_opposing_supports_in_trace() -> None:
    result = _verify(
        [],
        [
            ReasoningStep(
                step_id=1,
                text="a happened before b.",
                supports=[("a", "b", "BEFORE")],
                confidence=None,
            ),
            ReasoningStep(
                step_id=2,
                text="b happened before a.",
                supports=[("b", "a", "BEFORE")],
                confidence=None,
            ),
        ],
    )

    assert "ltl_trace_inversion" in _formula_types(result)


def test_trace_inversion_fires_for_semantic_after_reversal() -> None:
    result = _verify(
        [],
        [
            ReasoningStep(
                step_id=1,
                text="a happened before b.",
                supports=[("a", "b", "BEFORE")],
                confidence=None,
            ),
            ReasoningStep(
                step_id=2,
                text="a happened after b.",
                supports=[("a", "b", "AFTER")],
                confidence=None,
            ),
        ],
    )

    assert "ltl_trace_inversion" in _formula_types(result)


def test_trace_inversion_clear_when_consistent_supports() -> None:
    result = _verify(
        [("a", "b", "BEFORE")],
        [
            ReasoningStep(
                step_id=1,
                text="a happened before b.",
                supports=[("a", "b", "BEFORE")],
                confidence=None,
            ),
            ReasoningStep(
                step_id=2,
                text="a still happened before b.",
                supports=[("a", "b", "BEFORE")],
                confidence=None,
            ),
        ],
    )

    assert "ltl_trace_inversion" not in _formula_types(result)


def test_trace_inversion_skipped_when_no_reasoning_steps() -> None:
    result = _verify([("a", "b", "BEFORE")], [])

    assert "ltl_trace_inversion" not in _formula_types(result)
