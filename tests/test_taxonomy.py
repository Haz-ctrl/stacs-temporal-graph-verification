from __future__ import annotations

from src.results import Violation
from src.taxonomy import (
    VIOLATION_TO_CATEGORY,
    map_violation_to_category,
    summarise_violations,
)


def test_violation_to_category_contains_expected_mappings() -> None:
    assert VIOLATION_TO_CATEGORY["cycle"] == "structural"
    assert VIOLATION_TO_CATEGORY["hallucinated_node"] == "grounding"
    assert VIOLATION_TO_CATEGORY["duplicate_edge"] == "format"
    assert VIOLATION_TO_CATEGORY["unsupported_reasoning_step"] == "reasoning_trace"
    assert VIOLATION_TO_CATEGORY["unsupported_reasoning_reference"] == "grounding"


def test_map_violation_to_category_returns_expected_category() -> None:
    assert map_violation_to_category("cycle") == "structural"
    assert map_violation_to_category("contradiction") == "structural"
    assert map_violation_to_category("hallucinated_node") == "grounding"
    assert map_violation_to_category("duplicate_edge") == "format"
    assert map_violation_to_category("unsupported_reasoning_step") == "reasoning_trace"
    assert map_violation_to_category("unsupported_reasoning_reference") == "grounding"


def test_map_violation_to_category_unknown_type_maps_to_other() -> None:
    assert map_violation_to_category("some_future_violation") == "other"


def test_summarise_violations_counts_by_type_and_category() -> None:
    violations = [
        Violation(type="cycle", message="cycle", layer="intrinsic_temporal", constraint="acyclicity", details={}),
        Violation(type="contradiction", message="contradiction", layer="intrinsic_temporal", constraint="antisymmetry", details={}),
        Violation(type="hallucinated_node", message="hallucinated", layer="grounding", constraint="no_hallucinated_nodes", details={}),
        Violation(type="duplicate_edge", message="duplicate", layer="format", constraint="duplicate_edge", details={}),
        Violation(type="unsupported_reasoning_step", message="unsupported", layer="trace", constraint="reasoning_support", details={}),
        Violation(type="unsupported_reasoning_reference", message="unsupported", layer="grounding", constraint="reasoning_grounding", details={}),
        Violation(type="some_future_violation", message="unknown", layer="other", constraint="future", details={}),
    ]

    summary = summarise_violations(violations)

    assert summary.by_violation_type == {
        "cycle": 1,
        "contradiction": 1,
        "hallucinated_node": 1,
        "duplicate_edge": 1,
        "unsupported_reasoning_step": 1,
        "unsupported_reasoning_reference": 1,
        "some_future_violation": 1,
    }

    assert summary.by_category == {
        "structural": 2,
        "grounding": 2,
        "format": 1,
        "reasoning_trace": 1,
        "other": 1,
    }


def test_summarise_violations_empty_input() -> None:
    summary = summarise_violations([])

    assert summary.by_violation_type == {}
    assert summary.by_category == {}
