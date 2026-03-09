from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable

from src.constraints import Violation


VIOLATION_TO_CATEGORY: Dict[str, str] = {
    "cycle": "structural",
    "contradiction": "structural",
    "temporal_inconsistency": "structural",
    "hallucinated_node": "grounding",
    "missing_edge": "prediction",
    "spurious_edge": "prediction",
    "overcommitment": "prediction",
    "duplicate_edge": "format",
    "unsupported_reasoning_step": "reasoning_trace",
}


@dataclass(frozen=True)
class TaxonomySummary:
    by_violation_type: Dict[str, int]
    by_category: Dict[str, int]


def map_violation_to_category(violation_type: str) -> str:
    """
    Map a low-level violation type to a higher-level taxonomy category.
    Unknown types are grouped under 'other'.
    """
    return VIOLATION_TO_CATEGORY.get(violation_type, "other")


def summarise_violations(violations: Iterable[Violation]) -> TaxonomySummary:
    """
    Aggregate a collection of violations both by raw type and by category.
    """
    type_counter: Counter[str] = Counter()
    category_counter: Counter[str] = Counter()

    for violation in violations:
        type_counter[violation.type] += 1
        category_counter[map_violation_to_category(violation.type)] += 1

    return TaxonomySummary(
        by_violation_type=dict(type_counter),
        by_category=dict(category_counter),
    )