from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, Sequence, Tuple, List

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


@dataclass(frozen=True)
class ModelPrediction:
    answer: str
    events: List[str]
    relations: List[Edge]
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)
    raw_output: Optional[str] = None


@dataclass(frozen=True)
class ParsedPrediction:
    task_id: str
    answer: str
    pred_events: List[str]
    pred_edges: List[Edge]
    reasoning_steps: List[ReasoningStep]
    raw_output: Optional[str] = None