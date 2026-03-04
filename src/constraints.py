from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Protocol, Sequence, Set, Tuple

from src.temporal_graph import TemporalGraph, EdgeLike, _to_edge

Edge3 = Tuple[str, str, str]


def _edge_set(relations: Iterable[EdgeLike]) -> Set[Edge3]:
    """
    Convert edge-like triples into a set of canonical (a, b, REL) tuples.
    Normalises relation to uppercase via _to_edge.
    """
    out: Set[Edge3] = set()
    for e in relations:
        a, b, r = _to_edge(e)
        out.add((a, b, r))
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
class NoHallucinatedNodesConstraint:
    name: str = "no_hallucinated_nodes"

    def check(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
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
class Verifier:
    constraints: List[Constraint]

    def verify(
        self,
        graph: TemporalGraph,
        *,
        allowed_events: Optional[Sequence[str]] = None,
        gold_relations: Optional[Iterable[EdgeLike]] = None,
        pred_edges: Optional[Iterable[EdgeLike]] = None,
    ) -> List[Violation]:
        violations: List[Violation] = []
        for c in self.constraints:
            violations.extend(
                c.check(
                    graph,
                    allowed_events=allowed_events,
                    gold_relations=gold_relations,
                    pred_edges=pred_edges,
                )
            )
        return violations


def default_verifier() -> Verifier:
    return Verifier(
        constraints=[
            AcyclicityConstraint(),
            NoDirectContradictionsConstraint(relation="BEFORE"),
            NoHallucinatedNodesConstraint(),
            OvercommitmentConstraint(),
            MissingEdgeConstraint(),
            SpuriousEdgeConstraint(),
        ]
    )