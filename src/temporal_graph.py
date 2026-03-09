from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Iterable, List, Sequence, Set, Tuple, Union

import networkx as nx

Relation = str
Edge = Tuple[str, str, Relation]  # (source_event, target_event, relation)
EdgeLike = Union[Edge, Sequence[str]]  # accepts ("A", "B", "BEFORE") or ["A", "B", "BEFORE"]

ALLOWED_RELATIONS: Final[frozenset[str]] = frozenset(
    {"BEFORE", "AFTER", "SIMULTANEOUS", "UNKNOWN"}
)


def canonicalise_relation(value: str) -> str:
    """
    Normalise and validate a relation label.

    Raises:
        ValueError: if the relation is empty or unsupported.
    """
    rel = str(value).strip().upper()
    if not rel:
        raise ValueError("Relation must be a non-empty string.")
    if rel not in ALLOWED_RELATIONS:
        raise ValueError(
            f"Unsupported relation label: {value!r}. "
            f"Allowed relations: {sorted(ALLOWED_RELATIONS)}"
        )
    return rel


def _to_edge(edge_like: EdgeLike) -> Edge:
    """
    Convert edge-like input into a canonical Edge tuple.

    Accepts:
      - tuple[str, str, str]
      - list[str] / other sequence[str] of length 3

    Returns:
        A canonical (source, target, RELATION) tuple.

    Raises:
        ValueError: if the input is malformed or the relation is invalid.
    """
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


@dataclass
class TemporalGraph:
    """
    Minimal temporal graph wrapper around a directed graph.

    Nodes:
        Event strings (must match task events exactly if used with grounding checks)

    Edges:
        Directed temporal relations, e.g. A --BEFORE--> B

    Notes:
        - Uses networkx.DiGraph (simple directed graph)
        - Edge attribute: relation=<Relation>
    """

    g: nx.DiGraph = field(default_factory=nx.DiGraph)

    def add_event(self, event: str) -> None:
        """
        Add a single event node to the graph.

        Raises:
            ValueError: if the event is not a non-empty string.
        """
        if not isinstance(event, str) or not event.strip():
            raise ValueError("Event must be a non-empty string.")
        self.g.add_node(event)

    def add_events(self, events: Iterable[str]) -> None:
        """Add multiple event nodes."""
        for event in events:
            self.add_event(event)

    def add_relation(self, source: str, target: str, relation: Relation) -> None:
        """
        Add a directed temporal relation edge source -> target.

        Example:
            add_relation("A", "B", "BEFORE")
        """
        if source not in self.g:
            self.add_event(source)
        if target not in self.g:
            self.add_event(target)

        rel = canonicalise_relation(relation)
        self.g.add_edge(source, target, relation=rel)

    def add_edges(self, edges: Iterable[EdgeLike]) -> None:
        """
        Add multiple relation edges from edge-like triples.
        """
        for edge_like in edges:
            source, target, relation = _to_edge(edge_like)
            self.add_relation(source, target, relation)

    def nodes(self) -> List[str]:
        """Return graph nodes as a list."""
        return list(self.g.nodes)

    def edges(self) -> List[Edge]:
        """Return graph edges as canonical (src, dst, relation) tuples."""
        out: List[Edge] = []
        for source, target, data in self.g.edges(data=True):
            relation = canonicalise_relation(str(data.get("relation", "")))
            out.append((source, target, relation))
        return out

    def edges_for_relation(self, relation: str) -> List[Edge]:
        """
        Return edges whose relation matches the given label.
        """
        rel = canonicalise_relation(relation)
        return [(u, v, r) for (u, v, r) in self.edges() if r == rel]

    def relations_set(self) -> Set[Edge]:
        """Return a set of canonical edges for fast lookup."""
        return set(self.edges())

    def is_acyclic(self) -> bool:
        """Return True if the directed graph is acyclic."""
        return nx.is_directed_acyclic_graph(self.g)

    def find_cycles(self) -> List[List[str]]:
        """
        Return a list of directed cycles.

        Each cycle is represented as a list of node strings.
        Returns an empty list if no cycles are present.
        """
        try:
            return list(nx.simple_cycles(self.g))
        except Exception:
            return []

    def transitive_closure_pairs(self) -> Set[Tuple[str, str]]:
        """
        Return the set of reachable ordered pairs (u, v) such that u != v.

        This is graph reachability over the current directed graph.
        """
        closure = nx.transitive_closure(self.g)
        return {(u, v) for (u, v) in closure.edges() if u != v}

    def implied_before_pairs(self) -> Set[Tuple[str, str]]:
        """
        Return the implied BEFORE reachability pairs.

        At present, this is the transitive closure over the directed graph.
        This assumes the graph is being used primarily for BEFORE-style edges.
        """
        return self.transitive_closure_pairs()

    def pairs_for_relation(self, relation: str = "BEFORE") -> Set[Tuple[str, str]]:
        """
        Return (u, v) pairs for edges whose relation matches the given label.
        """
        rel = canonicalise_relation(relation)
        out: Set[Tuple[str, str]] = set()
        for source, target, data in self.g.edges(data=True):
            edge_rel = canonicalise_relation(str(data.get("relation", "")))
            if edge_rel == rel:
                out.add((source, target))
        return out

    def has_direct_contradiction(self, relation: Relation = "BEFORE") -> bool:
        """
        Detect direct contradictions of the form:
            A --REL--> B and B --REL--> A

        Default relation is BEFORE.
        """
        rel = canonicalise_relation(relation)

        for source, target, edge_rel in self.edges():
            if edge_rel != rel:
                continue
            if self.g.has_edge(target, source):
                reverse_rel = canonicalise_relation(str(self.g.edges[target, source].get("relation", "")))
                if reverse_rel == rel:
                    return True

        return False

    def direct_contradictions(self, relation: Relation = "BEFORE") -> List[Tuple[str, str]]:
        """
        Return sorted unique contradictory node pairs for the given relation.
        """
        rel = canonicalise_relation(relation)

        seen: Set[Tuple[str, str]] = set()
        contradictions: List[Tuple[str, str]] = []

        for source, target, edge_rel in self.edges():
            if edge_rel != rel:
                continue
            if self.g.has_edge(target, source):
                reverse_rel = canonicalise_relation(str(self.g.edges[target, source].get("relation", "")))
                if reverse_rel == rel:
                    pair = (source, target) if source <= target else (target, source)
                    if pair not in seen:
                        seen.add(pair)
                        contradictions.append(pair)

        contradictions.sort()
        return contradictions

    def temporal_inconsistencies(self, relation: Relation = "BEFORE") -> List[Tuple[str, str]]:
        """
        Detect global temporal inconsistencies using transitive reachability.

        For now this only supports BEFORE. It flags pairs where both:
            A reaches B, and
            B reaches A

        which indicates a global ordering inconsistency.

        Returns:
            Sorted unique contradictory pairs.
        """
        rel = canonicalise_relation(relation)
        if rel != "BEFORE":
            raise ValueError("temporal_inconsistencies currently supports BEFORE only.")

        closure = self.transitive_closure_pairs()
        inconsistencies: List[Tuple[str, str]] = []
        seen: Set[Tuple[str, str]] = set()

        for source, target in closure:
            if source == target:
                continue
            if (target, source) in closure:
                pair = (source, target) if source <= target else (target, source)
                if pair not in seen:
                    seen.add(pair)
                    inconsistencies.append(pair)

        inconsistencies.sort()
        return inconsistencies

    def unknown_nodes(self, allowed_events: Iterable[str]) -> List[str]:
        """
        Return graph nodes that are not present in allowed_events.
        """
        allowed = set(allowed_events)
        unknown = [node for node in self.g.nodes if node not in allowed]
        unknown.sort()
        return unknown