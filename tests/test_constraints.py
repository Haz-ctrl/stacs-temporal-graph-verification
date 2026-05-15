from __future__ import annotations

from src.constraints import default_temporal_specification, default_verifier
from src.schemas import ReasoningStep
from src.temporal_graph import TemporalGraph


def _types(result) -> set[str]:
    return {violation.type for violation in result.violations}


# ---------------------------------------------------------------------------
# Specification metadata
# ---------------------------------------------------------------------------


def test_default_specification_exposes_named_invariants() -> None:
    specification = default_temporal_specification()

    assert specification.name == "default_temporal_spec"
    assert [invariant.name for invariant in specification.invariants] == [
        "duplicate_edge",
        "no_hallucinated_nodes",
        "reasoning_grounding",
        "antisymmetry",
        "simultaneity_consistency",
        "acyclicity",
        "temporal_consistency",
        "reasoning_support",
    ]
    assert [formula.name for formula in specification.formulas] == [
        "ltl_no_contradiction",
        "ltl_no_temporal_inconsistency",
        "ltl_no_hallucinated_nodes",
    ]


# ---------------------------------------------------------------------------
# Graph-level verification
# ---------------------------------------------------------------------------


def test_cycle_violation() -> None:
    allowed = ["A", "B", "C"]
    pred_edges = [["A", "B", "BEFORE"], ["B", "C", "BEFORE"], ["C", "A", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    result = default_verifier().verify(
        tg, allowed_events=allowed, pred_edges=pred_edges
    )
    assert result.is_valid is False
    assert result.graph_valid is False
    assert "cycle" in _types(result)


def test_direct_contradiction_violation() -> None:
    allowed = ["A", "B"]
    pred_edges = [["A", "B", "BEFORE"], ["B", "A", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    result = default_verifier().verify(
        tg, allowed_events=allowed, pred_edges=pred_edges
    )
    assert "contradiction" in _types(result)
    assert "ltl_contradiction" in {
        violation.type for violation in result.formula_violations
    }
    assert result.first_violation_step == 0


def test_simultaneous_order_conflict_violation() -> None:
    allowed = ["A", "B"]
    pred_edges = [["A", "B", "SIMULTANEOUS"], ["A", "B", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    result = default_verifier().verify(
        tg, allowed_events=allowed, pred_edges=pred_edges
    )
    assert "simultaneous_order_conflict" in _types(result)


def test_temporal_inconsistency_violation() -> None:
    allowed = ["A", "B", "C"]
    pred_edges = [["A", "B", "BEFORE"], ["B", "C", "BEFORE"], ["C", "A", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    result = default_verifier().verify(
        tg, allowed_events=allowed, pred_edges=pred_edges
    )
    assert "temporal_inconsistency" in _types(result)


def test_hallucinated_node_violation() -> None:
    allowed = ["A", "B"]
    pred_edges = [["A", "B", "BEFORE"], ["A", "C", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(["A", "B", "C"])
    tg.add_edges(pred_edges)

    result = default_verifier().verify(
        tg, allowed_events=allowed, pred_edges=pred_edges
    )
    assert "hallucinated_node" in _types(result)
    assert "ltl_hallucinated_node" in {
        violation.type for violation in result.formula_violations
    }


def test_intrinsic_validity_is_independent_from_gold_match() -> None:
    allowed = ["A", "B", "C"]
    pred_edges = [["A", "B", "BEFORE"], ["A", "C", "BEFORE"], ["B", "C", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    result = default_verifier().verify(
        tg, allowed_events=allowed, pred_edges=pred_edges
    )
    assert result.is_valid is True
    assert result.graph_valid is True
    assert result.violations == []


def test_duplicate_edge_violation() -> None:
    allowed = ["A", "B"]
    pred_edges = [["A", "B", "BEFORE"], ["A", "B", "BEFORE"]]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    result = default_verifier().verify(
        tg, allowed_events=allowed, pred_edges=pred_edges
    )
    assert "duplicate_edge" in _types(result)


# ---------------------------------------------------------------------------
# Reasoning-step grounding
# ---------------------------------------------------------------------------


def test_reasoning_support_violation_when_step_support_missing_from_predictions() -> (
    None
):
    allowed = ["A", "B", "C"]
    pred_edges = [["A", "B", "BEFORE"]]
    reasoning_steps = [
        ReasoningStep(
            step_id=1,
            text="From the prompt, A happened before B, and B happened before C.",
            supports=[("A", "B", "BEFORE"), ("B", "C", "BEFORE")],
        )
    ]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    result = default_verifier().verify(
        tg,
        allowed_events=allowed,
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
    )
    assert result.graph_valid is True
    assert result.trace_grounded is False
    assert result.is_valid is True
    assert "unsupported_reasoning_step" in _types(result)
    violation = next(
        v for v in result.violations if v.type == "unsupported_reasoning_step"
    )
    assert violation.counterexample is not None
    assert violation.counterexample.step_ids == [1]


def test_reasoning_support_accepts_closure_implied_supports() -> None:
    allowed = ["A", "B", "C"]
    pred_edges = [["A", "B", "BEFORE"], ["B", "C", "BEFORE"]]
    reasoning_steps = [
        ReasoningStep(
            step_id=2,
            text="A happened before B, B happened before C, and therefore A happened before C.",
            supports=[
                ("A", "B", "BEFORE"),
                ("B", "C", "BEFORE"),
                ("A", "C", "BEFORE"),
            ],
        )
    ]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    result = default_verifier().verify(
        tg,
        allowed_events=allowed,
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
    )

    assert result.graph_valid is True
    assert result.trace_grounded is True
    assert "unsupported_reasoning_step" not in _types(result)


def test_reasoning_grounding_violation_when_support_references_unknown_event() -> None:
    allowed = ["A", "B"]
    pred_edges = [["A", "B", "BEFORE"]]
    reasoning_steps = [
        ReasoningStep(
            step_id=3,
            text="Ghost happened before B.",
            supports=[("Ghost", "B", "BEFORE")],
        )
    ]

    tg = TemporalGraph()
    tg.add_events(["A", "B", "Ghost"])
    tg.add_edges(pred_edges)

    result = default_verifier().verify(
        tg,
        allowed_events=allowed,
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
    )
    assert "unsupported_reasoning_reference" in _types(result)


def test_reasoning_support_no_violation_when_supports_match_predictions() -> None:
    allowed = ["A", "B", "C"]
    pred_edges = [["A", "B", "BEFORE"], ["B", "C", "BEFORE"]]
    reasoning_steps = [
        ReasoningStep(
            step_id=1,
            text="The prompt states A happened before B.",
            supports=[("A", "B", "BEFORE")],
        ),
        ReasoningStep(
            step_id=2,
            text="The prompt states B happened before C.",
            supports=[("B", "C", "BEFORE")],
        ),
    ]

    tg = TemporalGraph()
    tg.add_events(allowed)
    tg.add_edges(pred_edges)

    result = default_verifier().verify(
        tg,
        allowed_events=allowed,
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
    )
    assert result.is_valid is True
    assert "unsupported_reasoning_step" not in _types(result)
    assert result.formula_violations == []
