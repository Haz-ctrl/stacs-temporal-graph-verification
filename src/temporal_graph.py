from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Dict, Iterable, List, Sequence, Set, Tuple, Union

import networkx as nx

from src.schemas import TemporalRelation

Relation = str
Edge = Tuple[str, str, Relation]
EdgeLike = Union[Edge, Sequence[str]]

ALLOWED_RELATIONS: Final[frozenset[str]] = frozenset(
    relation.value for relation in TemporalRelation
)


def canonicalise_relation(value: str) -> str:
    return TemporalRelation.canonicalise(value).value


def _to_edge(edge_like: EdgeLike) -> Edge:
    if not isinstance(edge_like, (list, tuple)) or len(edge_like) != 3:
        raise ValueError(f"Invalid edge format (expected 3 items): {edge_like!r}")

    source_raw, target_raw, relation_raw = edge_like
    source = str(source_raw)
    target = str(target_raw)
    relation = canonicalise_relation(str(relation_raw))

    if not source.strip():
        raise ValueError("Edge source must be a non-empty string.")
    if not target.strip():
        raise ValueError("Edge target must be a non-empty string.")

    return (source, target, relation)


class _DisjointSet:
    def __init__(self, items: Iterable[str]) -> None:
        self._parent: Dict[str, str] = {item: item for item in items}

    def find(self, item: str) -> str:
        parent = self._parent[item]
        if parent != item:
            self._parent[item] = self.find(parent)
        return self._parent[item]

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self._parent[right_root] = left_root


@dataclass
class TemporalGraph:
    _nodes: List[str] = field(default_factory=list)
    _node_set: Set[str] = field(default_factory=set)
    _edges: List[Edge] = field(default_factory=list)
    _edge_set: Set[Edge] = field(default_factory=set)

    def add_event(self, event: str) -> None:
        if not isinstance(event, str) or not event.strip():
            raise ValueError("Event must be a non-empty string.")
        if event not in self._node_set:
            self._node_set.add(event)
            self._nodes.append(event)

    def add_events(self, events: Iterable[str]) -> None:
        for event in events:
            self.add_event(event)

    def add_relation(self, source: str, target: str, relation: Relation) -> None:
        edge = _to_edge((source, target, relation))
        self.add_event(edge[0])
        self.add_event(edge[1])
        if edge not in self._edge_set:
            self._edge_set.add(edge)
            self._edges.append(edge)

    def add_edges(self, edges: Iterable[EdgeLike]) -> None:
        for edge_like in edges:
            source, target, relation = _to_edge(edge_like)
            self.add_relation(source, target, relation)

    def nodes(self) -> List[str]:
        return list(self._nodes)

    def edges(self) -> List[Edge]:
        return list(self._edges)

    def relations_set(self) -> Set[Edge]:
        return set(self._edge_set)

    def edges_for_relation(self, relation: str) -> List[Edge]:
        rel = canonicalise_relation(relation)
        return [edge for edge in self._edges if edge[2] == rel]

    def pairs_for_relation(self, relation: str = "BEFORE") -> Set[Tuple[str, str]]:
        rel = canonicalise_relation(relation)
        return {
            (source, target)
            for (source, target, edge_rel) in self._edges
            if edge_rel == rel
        }

    def _simultaneous_sets(self) -> Tuple[_DisjointSet, Dict[str, List[str]]]:
        ds = _DisjointSet(self._nodes)
        for source, target, relation in self._edges:
            if TemporalRelation.canonicalise(relation).is_equivalence():
                ds.union(source, target)
        groups: Dict[str, List[str]] = {}
        for node in self._nodes:
            root = ds.find(node)
            groups.setdefault(root, []).append(node)
        for members in groups.values():
            members.sort()
        return ds, groups

    def simultaneous_groups(self) -> List[List[str]]:
        _, groups = self._simultaneous_sets()
        return sorted(groups.values(), key=lambda members: (members[0], len(members)))

    def simultaneous_pair_set(self) -> Set[Tuple[str, str]]:
        _, groups = self._simultaneous_sets()
        pairs: Set[Tuple[str, str]] = set()
        for members in groups.values():
            if len(members) < 2:
                continue
            for source in members:
                for target in members:
                    if source != target:
                        pairs.add((source, target))
        return pairs

    def direct_order_pairs(self) -> Set[Tuple[str, str]]:
        order_pairs: Set[Tuple[str, str]] = set()
        for source, target, relation in self._edges:
            rel = TemporalRelation.canonicalise(relation)
            if rel is TemporalRelation.BEFORE:
                order_pairs.add((source, target))
            elif rel is TemporalRelation.AFTER:
                order_pairs.add((target, source))
        return order_pairs

    def _collapsed_ordering_graph(self) -> Tuple[nx.DiGraph, Dict[str, List[str]]]:
        ds, groups = self._simultaneous_sets()
        graph = nx.DiGraph()
        for root in groups:
            graph.add_node(root)

        for source, target in self.direct_order_pairs():
            source_root = ds.find(source)
            target_root = ds.find(target)
            graph.add_edge(source_root, target_root)

        return graph, groups

    def ordering_pairs(self) -> Set[Tuple[str, str]]:
        graph, groups = self._collapsed_ordering_graph()
        closure = nx.transitive_closure(graph)
        pairs: Set[Tuple[str, str]] = set()

        for source_root, target_root in closure.edges():
            if source_root == target_root:
                continue
            for source in groups[source_root]:
                for target in groups[target_root]:
                    if source != target:
                        pairs.add((source, target))

        return pairs

    def transitive_closure_pairs(self) -> Set[Tuple[str, str]]:
        return self.ordering_pairs()

    def implied_before_pairs(self) -> Set[Tuple[str, str]]:
        return self.ordering_pairs()

    def is_acyclic(self) -> bool:
        graph, _ = self._collapsed_ordering_graph()
        if any(source == target for (source, target) in graph.edges()):
            return False
        return nx.is_directed_acyclic_graph(graph)

    def find_cycles(self) -> List[List[str]]:
        graph, groups = self._collapsed_ordering_graph()
        cycles: List[List[str]] = []
        try:
            for cycle in nx.simple_cycles(graph):
                if not cycle:
                    continue
                cycles.append([groups[node][0] for node in cycle])
        except nx.NetworkXException:
            return []
        return cycles

    def has_direct_contradiction(self, relation: Relation = "BEFORE") -> bool:
        return len(self.direct_contradictions(relation)) > 0

    def direct_contradictions(
        self, relation: Relation = "BEFORE"
    ) -> List[Tuple[str, str]]:
        rel = TemporalRelation.canonicalise(relation)
        if rel is not TemporalRelation.BEFORE:
            raise ValueError("direct_contradictions currently supports BEFORE only.")

        contradictions: Set[Tuple[str, str]] = set()
        pairs = self.direct_order_pairs()
        for source, target in pairs:
            if (target, source) in pairs:
                contradictions.add(
                    (source, target) if source <= target else (target, source)
                )
        return sorted(contradictions)

    def simultaneous_order_conflicts(self) -> List[Tuple[str, str]]:
        ds, _ = self._simultaneous_sets()
        conflicts: Set[Tuple[str, str]] = set()
        for source, target in self.direct_order_pairs():
            if ds.find(source) == ds.find(target):
                conflicts.add(
                    (source, target) if source <= target else (target, source)
                )
        return sorted(conflicts)

    def temporal_inconsistencies(
        self, relation: Relation = "BEFORE"
    ) -> List[Tuple[str, str]]:
        rel = TemporalRelation.canonicalise(relation)
        if rel is not TemporalRelation.BEFORE:
            raise ValueError("temporal_inconsistencies currently supports BEFORE only.")

        inconsistencies: Set[Tuple[str, str]] = set(self.simultaneous_order_conflicts())
        closure = self.ordering_pairs()
        for source, target in closure:
            if (target, source) in closure:
                inconsistencies.add(
                    (source, target) if source <= target else (target, source)
                )
        return sorted(inconsistencies)

    def unknown_nodes(self, allowed_events: Iterable[str]) -> List[str]:
        allowed = set(allowed_events)
        unknown = [node for node in self._nodes if node not in allowed]
        unknown.sort()
        return unknown

    def entails_edge(self, edge_like: EdgeLike) -> bool:
        source, target, relation = _to_edge(edge_like)
        rel = TemporalRelation.canonicalise(relation)
        if rel is TemporalRelation.BEFORE:
            return (source, target) in self.ordering_pairs()
        if rel is TemporalRelation.AFTER:
            return (target, source) in self.ordering_pairs()
        if rel is TemporalRelation.SIMULTANEOUS:
            return (source, target) in self.simultaneous_pair_set()
        return (source, target, rel.value) in self._edge_set
