from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence

from src.temporal_graph import TemporalGraph


@dataclass
class Violation:
    """
    A structured record describing a constraint failure.
    """
    type: str
    message: str
    details: Dict[str, Any]


class Constraint(Protocol):
    """Interface for all constraints."""
    name: str

    def check(self, graph: TemporalGraph, *, allowed_events: Optional[Sequence[str]] = None) -> List[Violation]:
        ...


@dataclass
class AcyclicityConstraint:
    name: str = "acyclicity"

    def check(self, graph: TemporalGraph, *, allowed_events: Optional[Sequence[str]] = None) -> List[Violation]:
        if graph.is_acyclic():
            return []
        cycles = graph.find_cycles()
        return [
            Violation(
                type="cycle",
                message="Temporal graph contains at least one directed cycle.",
                details={"cycles": cycles},
            )
        ]


@dataclass
class NoDirectContradictionsConstraint:
    """
    Detects direct contradictions of the form:
      A --REL--> B and B --REL--> A
    Default is BEFORE.
    """
    relation: str = "BEFORE"
    name: str = "no_direct_contradictions"

    def check(self, graph: TemporalGraph, *, allowed_events: Optional[Sequence[str]] = None) -> List[Violation]:
        contradictions = graph.direct_contradictions(self.relation)
        if not contradictions:
            return []
        return [
            Violation(
                type="contradiction",
                message=f"Temporal graph contains direct contradictory '{self.relation}' relations.",
                details={"relation": self.relation, "pairs": contradictions},
            )
        ]


@dataclass
class NoHallucinatedNodesConstraint:
    """
    Ensures every node in the graph is drawn from the task's allowed events.
    """
    name: str = "no_hallucinated_nodes"

    def check(self, graph: TemporalGraph, *, allowed_events: Optional[Sequence[str]] = None) -> List[Violation]:
        if allowed_events is None:
            raise ValueError("NoHallucinatedNodesConstraint requires allowed_events to be provided.")
        unknown = graph.unknown_nodes(allowed_events)
        if not unknown:
            return []
        return [
            Violation(
                type="hallucinated_node",
                message="Graph contains node(s) not present in the allowed event list.",
                details={"unknown_nodes": unknown},
            )
        ]


@dataclass
class Verifier:
    """
    Runs a list of constraints against a TemporalGraph and returns violations.
    """
    constraints: List[Constraint]

    def verify(self, graph: TemporalGraph, *, allowed_events: Optional[Sequence[str]] = None) -> List[Violation]:
        violations: List[Violation] = []
        for c in self.constraints:
            violations.extend(c.check(graph, allowed_events=allowed_events))
        return violations


def default_verifier() -> Verifier:
    return Verifier(
        constraints=[
            AcyclicityConstraint(),
            NoDirectContradictionsConstraint(relation="BEFORE"),
            NoHallucinatedNodesConstraint(),
        ]
    )