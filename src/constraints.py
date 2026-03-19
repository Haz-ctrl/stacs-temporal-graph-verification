from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Protocol, Sequence, Set, Tuple

from src.results import Counterexample, VerificationResult, Violation
from src.temporal_graph import EdgeLike, TemporalGraph, _to_edge

Edge3 = Tuple[str, str, str]


def _edge_set(relations: Iterable[EdgeLike]) -> Set[Edge3]:
    return {_to_edge(relation) for relation in relations}


class Constraint(Protocol):
    name: str
    layer: str
    description: str

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        ...


@dataclass(frozen=True)
class AcyclicityConstraint:
    name: str = "acyclicity"
    layer: str = "intrinsic_temporal"
    description: str = "Ordering edges must not induce a directed cycle."

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        if graph.is_acyclic():
            return []
        cycles = graph.find_cycles()
        return [
            Violation(
                type="cycle",
                message="Temporal graph contains at least one directed cycle.",
                layer=self.layer,
                constraint=self.name,
                details={"cycles": cycles},
                counterexample=Counterexample(
                    relation_edges=[],
                    notes=["Detected cycle in normalised ordering graph."],
                ),
            )
        ]


@dataclass(frozen=True)
class NoDirectContradictionsConstraint:
    name: str = "antisymmetry"
    layer: str = "intrinsic_temporal"
    description: str = "No event pair may be asserted in both temporal directions."

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        contradictions = graph.direct_contradictions("BEFORE")
        if not contradictions:
            return []
        return [
            Violation(
                type="contradiction",
                message="Temporal graph contains directly contradictory ordering relations.",
                layer=self.layer,
                constraint=self.name,
                details={"pairs": contradictions},
                counterexample=Counterexample(
                    relation_edges=[],
                    notes=["Contradictory direct order pair detected after AFTER normalisation."],
                ),
            )
        ]


@dataclass(frozen=True)
class SimultaneityConsistencyConstraint:
    name: str = "simultaneity_consistency"
    layer: str = "intrinsic_temporal"
    description: str = "SIMULTANEOUS groups must not also contain ordering edges."

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        conflicts = graph.simultaneous_order_conflicts()
        if not conflicts:
            return []
        return [
            Violation(
                type="simultaneous_order_conflict",
                message="A SIMULTANEOUS group also contains an ordering relation.",
                layer=self.layer,
                constraint=self.name,
                details={"pairs": conflicts},
                counterexample=Counterexample(
                    relation_edges=[],
                    notes=["Ordering inside a simultaneous equivalence class is inconsistent."],
                ),
            )
        ]


@dataclass(frozen=True)
class TemporalConsistencyConstraint:
    name: str = "temporal_consistency"
    layer: str = "intrinsic_temporal"
    description: str = "Ordering closure must remain globally consistent."

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        inconsistencies = graph.temporal_inconsistencies("BEFORE")
        if not inconsistencies:
            return []
        return [
            Violation(
                type="temporal_inconsistency",
                message="Temporal graph contains globally inconsistent ordering constraints.",
                layer=self.layer,
                constraint=self.name,
                details={"pairs": inconsistencies},
                counterexample=Counterexample(
                    relation_edges=[],
                    notes=["Bidirectional reachability detected in the ordering closure."],
                ),
            )
        ]


@dataclass(frozen=True)
class NoHallucinatedNodesConstraint:
    name: str = "no_hallucinated_nodes"
    layer: str = "grounding"
    description: str = "Predicted events must be drawn from the task event inventory."

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        if allowed_events is None:
            raise ValueError("NoHallucinatedNodesConstraint requires allowed_events to be provided.")
        unknown = graph.unknown_nodes(allowed_events)
        if not unknown:
            return []
        return [
            Violation(
                type="hallucinated_node",
                message="Graph contains node(s) not present in the allowed event list.",
                layer=self.layer,
                constraint=self.name,
                details={"unknown_nodes": unknown},
                counterexample=Counterexample(notes=["Prediction introduced unsupported event nodes."]),
            )
        ]


@dataclass(frozen=True)
class DuplicateEdgeConstraint:
    name: str = "duplicate_edge"
    layer: str = "format"
    description: str = "Predicted edge triples should not repeat."

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        pred_list = [_to_edge(edge) for edge in (pred_edges or [])]
        unique = set(pred_list)
        if len(pred_list) == len(unique):
            return []
        return [
            Violation(
                type="duplicate_edge",
                message="Predicted output contains duplicate relation triples.",
                layer=self.layer,
                constraint=self.name,
                details={"num_edges": len(pred_list), "num_unique_edges": len(unique)},
                counterexample=Counterexample(relation_edges=pred_list),
            )
        ]


@dataclass(frozen=True)
class ReasoningSupportConstraint:
    name: str = "reasoning_support"
    layer: str = "trace"
    description: str = "Reasoning supports should be grounded in final predicted relations."

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        if not reasoning_steps:
            return []

        pred_set = _edge_set(pred_edges or [])
        unsupported: List[dict[str, Any]] = []
        step_ids: Set[int] = set()

        for step in reasoning_steps:
            step_id = getattr(step, "step_id", None)
            supports = getattr(step, "supports", [])
            for edge in supports:
                canonical_edge = _to_edge(edge)
                if canonical_edge not in pred_set:
                    unsupported.append({"step_id": step_id, "edge": canonical_edge})
                    if isinstance(step_id, int):
                        step_ids.add(step_id)

        if not unsupported:
            return []

        return [
            Violation(
                type="unsupported_reasoning_step",
                message="One or more reasoning steps cite relations not present in final predicted relations.",
                layer=self.layer,
                constraint=self.name,
                details={"unsupported_supports": unsupported},
                counterexample=Counterexample(
                    relation_edges=[item["edge"] for item in unsupported],
                    step_ids=sorted(step_ids),
                ),
            )
        ]


@dataclass(frozen=True)
class ReasoningGroundingConstraint:
    name: str = "reasoning_grounding"
    layer: str = "grounding"
    description: str = "Reasoning supports should only reference allowed events."

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        if allowed_events is None or not reasoning_steps:
            return []

        allowed_set = set(allowed_events)
        unsupported_refs: List[dict[str, Any]] = []
        step_ids: Set[int] = set()

        for step in reasoning_steps:
            step_id = getattr(step, "step_id", None)
            supports = getattr(step, "supports", [])
            for edge in supports:
                source, target, relation = _to_edge(edge)
                if source not in allowed_set or target not in allowed_set:
                    unsupported_refs.append(
                        {"step_id": step_id, "edge": (source, target, relation)}
                    )
                    if isinstance(step_id, int):
                        step_ids.add(step_id)

        if not unsupported_refs:
            return []

        return [
            Violation(
                type="unsupported_reasoning_reference",
                message="A reasoning step references event names outside the task event set.",
                layer=self.layer,
                constraint=self.name,
                details={"unsupported_references": unsupported_refs},
                counterexample=Counterexample(
                    relation_edges=[item["edge"] for item in unsupported_refs],
                    step_ids=sorted(step_ids),
                ),
            )
        ]


@dataclass
class Verifier:
    constraints: List[Constraint]

    def verify(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> VerificationResult:
        violations: List[Violation] = []
        for constraint in self.constraints:
            violations.extend(
                constraint.check(
                    graph,
                    allowed_events=allowed_events,
                    pred_edges=pred_edges,
                    reasoning_steps=reasoning_steps,
                )
            )

        violation_counts = dict(Counter(violation.type for violation in violations))
        layer_counts = dict(Counter(violation.layer for violation in violations))
        return VerificationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            violation_counts=violation_counts,
            layer_counts=layer_counts,
        )


def default_verifier() -> Verifier:
    return Verifier(
        constraints=[
            DuplicateEdgeConstraint(),
            NoHallucinatedNodesConstraint(),
            ReasoningGroundingConstraint(),
            NoDirectContradictionsConstraint(),
            SimultaneityConsistencyConstraint(),
            AcyclicityConstraint(),
            TemporalConsistencyConstraint(),
            ReasoningSupportConstraint(),
        ]
    )
