from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Protocol, Sequence, Set, Tuple

from src.temporal_graph import TemporalGraph, EdgeLike, _to_edge

Edge3 = Tuple[str, str, str]


def _edge_set(relations: Iterable[EdgeLike]) -> Set[Edge3]:
    """
    Convert edge-like triples into a set of canonical (a, b, REL) tuples.
    Normalises relation labels via _to_edge.
    """
    out: Set[Edge3] = set()
    for relation in relations:
        out.add(_to_edge(relation))
    return out


@dataclass
class Violation:
    """A structured record describing a constraint failure."""
    type: str
    message: str
    details: Dict[str, Any]


class Constraint(Protocol):
    """Interface for all constraints."""
    name: str

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
        **kwargs: Any,
    ) -> List[Violation]:
        ...


@dataclass
class AcyclicityConstraint:
    name: str = "acyclicity"

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
        **kwargs: Any,
    ) -> List[Violation]:
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
    relation: str = "BEFORE"
    name: str = "no_direct_contradictions"

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
        **kwargs: Any,
    ) -> List[Violation]:
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
class TemporalConsistencyConstraint:
    """
    Detect global inconsistency using graph reachability.

    Example:
        A BEFORE B, B BEFORE C, C BEFORE A
    may imply mutually inconsistent temporal orderings even when the issue
    is not framed purely as a direct symmetric contradiction.
    """
    relation: str = "BEFORE"
    name: str = "temporal_consistency"

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
        **kwargs: Any,
    ) -> List[Violation]:
        inconsistencies = graph.temporal_inconsistencies(self.relation)
        if not inconsistencies:
            return []
        return [
            Violation(
                type="temporal_inconsistency",
                message="Temporal graph contains globally inconsistent ordering constraints.",
                details={"relation": self.relation, "pairs": inconsistencies},
            )
        ]


@dataclass
class NoHallucinatedNodesConstraint:
    name: str = "no_hallucinated_nodes"

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
        **kwargs: Any,
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
                details={"unknown_nodes": unknown},
            )
        ]


@dataclass
class OvercommitmentConstraint:
    """
    If gold_relations is empty but the model predicts at least one edge,
    mark as overcommitment.
    """
    name: str = "overcommitment"

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
        **kwargs: Any,
    ) -> List[Violation]:
        gold_list = list(gold_relations or [])
        pred_list = list(pred_edges or [])

        if len(gold_list) == 0 and len(pred_list) > 0:
            return [
                Violation(
                    type="overcommitment",
                    message="Predicted temporal relations despite gold specifying no entailed relations (ambiguous/unknown).",
                    details={"num_pred_edges": len(pred_list)},
                )
            ]
        return []


@dataclass
class MissingEdgeConstraint:
    name: str = "missing_edge"

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
        **kwargs: Any,
    ) -> List[Violation]:
        gold_list = list(gold_relations or [])
        pred_list = list(pred_edges or [])
        if not gold_list:
            return []

        gold_set = _edge_set(gold_list)
        pred_set = _edge_set(pred_list)

        missing = sorted(gold_set - pred_set)
        if not missing:
            return []
        return [
            Violation(
                type="missing_edge",
                message="One or more gold temporal relations were not predicted.",
                details={"missing": missing},
            )
        ]


@dataclass
class SpuriousEdgeConstraint:
    name: str = "spurious_edge"

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
        **kwargs: Any,
    ) -> List[Violation]:
        gold_list = list(gold_relations or [])
        pred_list = list(pred_edges or [])
        if not gold_list:
            return []

        gold_set = _edge_set(gold_list)
        pred_set = _edge_set(pred_list)

        spurious = sorted(pred_set - gold_set)
        if not spurious:
            return []
        return [
            Violation(
                type="spurious_edge",
                message="One or more predicted temporal relations are not present in gold.",
                details={"spurious": spurious},
            )
        ]


@dataclass
class DuplicateEdgeConstraint:
    """
    Detect duplicate predicted edge triples before graph insertion collapses them.
    """
    name: str = "duplicate_edge"

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
        **kwargs: Any,
    ) -> List[Violation]:
        pred_list = [_to_edge(edge) for edge in (pred_edges or [])]
        unique = set(pred_list)

        if len(pred_list) == len(unique):
            return []

        return [
            Violation(
                type="duplicate_edge",
                message="Predicted output contains duplicate relation triples.",
                details={
                    "num_edges": len(pred_list),
                    "num_unique_edges": len(unique),
                },
            )
        ]


@dataclass
class ReasoningSupportConstraint:
    """
    Check that edges cited in reasoning steps are present in the final predicted relations.

    This is a deliberately simple first trace-verification rule:
    if a reasoning step claims support for an edge, that edge should appear
    in the final predicted relation set.
    """
    name: str = "reasoning_support"

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
        **kwargs: Any,
    ) -> List[Violation]:
        if not reasoning_steps:
            return []

        pred_set = _edge_set(pred_edges or [])
        unsupported: List[Dict[str, Any]] = []

        for step in reasoning_steps:
            step_id = getattr(step, "step_id", None)
            supports = getattr(step, "supports", [])

            for edge in supports:
                canonical_edge = _to_edge(edge)
                if canonical_edge not in pred_set:
                    unsupported.append(
                        {
                            "step_id": step_id,
                            "edge": canonical_edge,
                        }
                    )

        if not unsupported:
            return []

        return [
            Violation(
                type="unsupported_reasoning_step",
                message="One or more reasoning steps cite relations not present in final predicted relations.",
                details={"unsupported_supports": unsupported},
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
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
        reasoning_steps: Optional[Sequence[Any]] = None,
    ) -> List[Violation]:
        violations: List[Violation] = []
        for constraint in self.constraints:
            violations.extend(
                constraint.check(
                    graph,
                    allowed_events=allowed_events,
                    gold_relations=gold_relations,
                    pred_edges=pred_edges,
                    reasoning_steps=reasoning_steps,
                )
            )
        return violations


def default_verifier() -> Verifier:
    return Verifier(
        constraints=[
            AcyclicityConstraint(),
            NoDirectContradictionsConstraint(relation="BEFORE"),
            TemporalConsistencyConstraint(relation="BEFORE"),
            NoHallucinatedNodesConstraint(),
            OvercommitmentConstraint(),
            MissingEdgeConstraint(),
            SpuriousEdgeConstraint(),
            DuplicateEdgeConstraint(),
            ReasoningSupportConstraint(),
        ]
    )