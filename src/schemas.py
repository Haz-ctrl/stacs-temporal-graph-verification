from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Optional, Tuple, List


class TemporalRelation(str, Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    SIMULTANEOUS = "SIMULTANEOUS"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def canonicalise(cls, value: str) -> "TemporalRelation":
        rel = str(value).strip().upper()
        if not rel:
            raise ValueError("Relation must be a non-empty string.")
        try:
            return cls(rel)
        except ValueError as exc:
            allowed = sorted(member.value for member in cls)
            raise ValueError(
                f"Unsupported relation label: {value!r}. Allowed relations: {allowed}"
            ) from exc

    def reverses_order(self) -> bool:
        return self is TemporalRelation.AFTER

    def contributes_to_order(self) -> bool:
        return self in {TemporalRelation.BEFORE, TemporalRelation.AFTER}

    def is_equivalence(self) -> bool:
        return self is TemporalRelation.SIMULTANEOUS

    def is_abstention(self) -> bool:
        return self is TemporalRelation.UNKNOWN


RelationLabel = Literal["BEFORE", "AFTER", "SIMULTANEOUS", "UNKNOWN"]
CanonicalRelationLabel = Literal["BEFORE", "AFTER", "SIMULTANEOUS", "UNKNOWN"]

Edge = Tuple[str, str, str]


@dataclass(frozen=True)
class TemporalTask:
    id: str
    question: str
    events: List[str]
    gold_relations: List[Edge]
    category: str = ""
    expected_valid: bool = True
    expected_consistent: bool = True


@dataclass(frozen=True)
class ReasoningStep:
    step_id: int
    text: str
    supports: List[Edge] = field(default_factory=list)
    confidence: Optional[float] = None


@dataclass(frozen=True)
class ModelPrediction:
    answer: str
    events: List[str]
    relations: List[Edge]
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)
    answer_confidence: Optional[float] = None
    raw_output: Optional[str] = None


@dataclass(frozen=True)
class ParsedPrediction:
    task_id: str
    answer: str
    pred_events: List[str]
    pred_edges: List[Edge]
    reasoning_steps: List[ReasoningStep]
    answer_confidence: Optional[float] = None
    json_repaired: bool = False
    raw_output: Optional[str] = None
