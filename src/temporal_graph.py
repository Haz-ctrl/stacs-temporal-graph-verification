from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple, Set
import networkx as nx

Relation = str
Edge = Tuple[str, str, Relation]  # (source_event, target_event, relation)

@dataclass
class TemporalGraph:
    """
    Minimal temporal graph wrapper around a directed graph.

    Nodes: event strings (must match task events exactly)
    Edges: directed relations, e.g. A --BEFORE--> B

    Notes:
    - Uses networkx.DiGraph (simple directed graph).
    - Edge attribute: relation=<Relation>
    """
    g: nx.DiGraph = field(default_factory=nx.DiGraph)

    def add_event(self, event: str) -> None:
        """Add an event node to the graph."""
        if not isinstance(event, str) or not event.strip():
            raise ValueError("Event must be a non-empty string.")
        self.g.add_node(event)

    def add_events(self, events: Iterable[str]) -> None:
        """Add multiple events."""
        for e in events:
            self.add_event(e)

    def add_relation(self, source: str, target: str, relation: Relation) -> None:
        """
        Add a directed relation edge source -> target with attribute 'relation'.

        Example: add_relation("A", "B", "BEFORE")
        """
        if source not in self.g:
            self.add_event(source)
        if target not in self.g:
            self.add_event(target)

        rel = str(relation).strip().upper()
        if not rel:
            raise ValueError("Relation must be a non-empty string.")

        self.g.add_edge(source, target, relation=rel)

    def add_edges(self, edges: Iterable[Edge]) -> None:
        """Add multiple relation edges."""
        for a, b, rel in edges:
            self.add_relation(a, b, rel)

    def nodes(self) -> List[str]:
        """Return nodes as a list."""
        return list(self.g.nodes)

    def edges(self) -> List[Edge]:
        """Return edges as (src, dst, relation) tuples."""
        out: List[Edge] = []
        for u, v, data in self.g.edges(data=True):
            out.append((u, v, str(data.get("relation", "")).upper()))
        return out

    def relations_set(self) -> Set[Tuple[str, str, str]]:
        """Convenience: set of (src, dst, relation) for fast lookups."""
        return set(self.edges())

    def is_acyclic(self) -> bool:
        """True if the directed graph is acyclic."""
        return nx.is_directed_acyclic_graph(self.g)

    def find_cycles(self) -> List[List[str]]:
        """
        Return a list of cycles (each cycle is a list of node strings).
        Empty list means no cycles.
        """
        try:
            cycles = list(nx.simple_cycles(self.g))
            return cycles
        except Exception:
            # In case of unexpected networkx issues, fail safe
            return []

    def has_direct_contradiction(self, relation: Relation = "BEFORE") -> bool:
        """
        Detect direct contradictions of the form:
          A --REL--> B and B --REL--> A
        Default relation is BEFORE.
        """
        rel = str(relation).strip().upper()
        if not rel:
            raise ValueError("Relation must be a non-empty string.")

        # Check for symmetric edge pair with same relation
        for a, b, r in self.edges():
            if r != rel:
                continue
            if self.g.has_edge(b, a):
                r2 = str(self.g.edges[b, a].get("relation", "")).upper()
                if r2 == rel:
                    return True
        return False

    def direct_contradictions(self, relation: Relation = "BEFORE") -> List[Tuple[str, str]]:
        """
        Return list of (A, B) pairs such that:
          A --REL--> B and B --REL--> A
        """
        rel = str(relation).strip().upper()
        if not rel:
            raise ValueError("Relation must be a non-empty string.")

        seen: Set[Tuple[str, str]] = set()
        contradictions: List[Tuple[str, str]] = []

        for a, b, r in self.edges():
            if r != rel:
                continue
            if self.g.has_edge(b, a):
                r2 = str(self.g.edges[b, a].get("relation", "")).upper()
                if r2 == rel:
                    pair = tuple(sorted((a, b)))
                    if pair not in seen:
                        seen.add(pair)
                        contradictions.append((pair[0], pair[1]))

        return contradictions

    def unknown_nodes(self, allowed_events: Iterable[str]) -> List[str]:
        """
        Return nodes in the graph that are not in allowed_events.
        Used for hallucination checks.
        """
        allowed = set(allowed_events)
        return [n for n in self.g.nodes if n not in allowed]