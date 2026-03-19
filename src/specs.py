from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional, Protocol, Sequence, Tuple

from src.ltl import Formula, formula_to_dict
from src.results import Counterexample, Violation
from src.temporal_graph import EdgeLike, TemporalGraph, _to_edge
from src.trace import TemporalTrace

Edge3 = Tuple[str, str, str]


@dataclass(frozen=True)
class InvariantSpec:
    name: str
    layer: str
    description: str


@dataclass(frozen=True)
class FormulaSpec:
    name: str
    description: str
    formula: Formula
    violation_type: str
    message: str

    def serialise(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "formula": formula_to_dict(self.formula),
            "violation_type": self.violation_type,
            "message": self.message,
        }


@dataclass(frozen=True)
class SpecContext:
    graph: TemporalGraph
    allowed_events: Optional[Sequence[str]] = None
    pred_edges: Tuple[Edge3, ...] = ()
    reasoning_steps: Tuple[Any, ...] = ()
    trace: Optional[TemporalTrace] = None


class Invariant(Protocol):
    spec: InvariantSpec

    def evaluate(self, context: SpecContext) -> List[Violation]:
        ...


@dataclass(frozen=True)
class TemporalSpecification:
    name: str
    invariants: Tuple[Invariant, ...] = field(default_factory=tuple)
    formulas: Tuple[FormulaSpec, ...] = field(default_factory=tuple)


class BaseInvariant:
    spec: InvariantSpec

    def evaluate(self, context: SpecContext) -> List[Violation]:
        raise NotImplementedError

    def violation(
        self,
        *,
        type: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
        relation_edges: Optional[Iterable[EdgeLike]] = None,
        step_ids: Optional[Iterable[int]] = None,
        notes: Optional[Iterable[str]] = None,
    ) -> Violation:
        counterexample: Counterexample | None = None
        if relation_edges is not None or step_ids is not None or notes is not None:
            counterexample = Counterexample(
                relation_edges=[_to_edge(edge) for edge in (relation_edges or [])],
                step_ids=sorted(set(step_ids or [])),
                notes=list(notes or []),
            )
        return Violation(
            type=type,
            message=message,
            layer=self.spec.layer,
            constraint=self.spec.name,
            spec_source="invariant",
            details=details or {},
            counterexample=counterexample,
        )
