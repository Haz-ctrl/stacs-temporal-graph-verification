from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Literal, Optional, Sequence, Set, Tuple

from src.temporal_graph import TemporalGraph, Edge, EdgeLike, _to_edge

Relation = Literal["BEFORE"]
Category = Literal[
    "linear_chain",
    "transitive_reasoning",
    "ambiguous",
    "contradiction",
    "long_chain",
]


@dataclass
class ValidationIssue:
    task_id: str
    severity: Literal["error", "warning"]
    code: str
    message: str
    details: Dict[str, Any]


@dataclass
class ValidationReport:
    num_tasks: int
    num_errors: int
    num_warnings: int
    issues: List[ValidationIssue]
    category_counts: Dict[str, int]

    def ok(self) -> bool:
        return self.num_errors == 0


def _is_str_list(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(v, str) for v in x)


def _coerce_edges(edges_like: Any) -> Optional[List[Edge]]:
    """
    Accepts edges in JSON form: List[List[str]] or List[Tuple[str,str,str]].
    Returns canonical List[Edge] or None if not coercible.
    """
    if not isinstance(edges_like, list):
        return None
    out: List[Edge] = []
    for e in edges_like:
        try:
            out.append(_to_edge(e))  # handles list/tuple edge-like
        except Exception:
            return None
    return out


def _edge_set(edges: Iterable[Edge]) -> Set[Edge]:
    return set(edges)


def _transitive_closure_edges_from_chain(events: Sequence[str]) -> Set[Edge]:
    """
    For an ordered list of events [e0,e1,...,en-1], return full closure set:
    ei BEFORE ej for all i<j.
    """
    out: Set[Edge] = set()
    n = len(events)
    for i in range(n):
        for j in range(i + 1, n):
            out.add((events[i], events[j], "BEFORE"))
    return out


def validate_tasks(
    tasks: Sequence[Dict[str, Any]],
    *,
    strict: bool = True,
    require_expected_fields: bool = False,
) -> ValidationReport:
    """
    Validate dataset tasks for schema + logical/category coherence.

    strict:
      - if True, treat all schema/coherence problems as errors
      - if False, downgrade some checks to warnings

    require_expected_fields:
      - if True, require expected_valid and expected_consistent keys to exist
    """
    issues: List[ValidationIssue] = []
    category_counts: Dict[str, int] = {}
    seen_ids: Set[str] = set()

    def add_issue(
        task_id: str,
        severity: Literal["error", "warning"],
        code: str,
        message: str,
        **details: Any,
    ) -> None:
        issues.append(
            ValidationIssue(
                task_id=task_id,
                severity=severity,
                code=code,
                message=message,
                details=details,
            )
        )

    for i, task in enumerate(tasks, start=1):
        task_id = str(task.get("id", f"task_{i:03d}"))
        cat = task.get("category")

        if task_id in seen_ids:
            add_issue(task_id, "error", "duplicate_id", "Duplicate task id detected.")
        seen_ids.add(task_id)

        # Required keys
        required = ["id", "category", "question", "events", "gold_relations"]
        for k in required:
            if k not in task:
                add_issue(task_id, "error", "missing_field", f"Missing required field '{k}'.")
        if any(k not in task for k in required):
            continue

        # Field types
        if not isinstance(task["question"], str):
            add_issue(task_id, "error", "bad_type", "Field 'question' must be a string.")
        if not _is_str_list(task["events"]):
            add_issue(task_id, "error", "bad_type", "Field 'events' must be List[str].")
            continue

        events: List[str] = task["events"]
        if len(events) == 0:
            add_issue(task_id, "error", "empty_events", "Task has no events.")
            continue

        # expected fields (optional, but recommended)
        if require_expected_fields:
            if "expected_valid" not in task:
                add_issue(task_id, "error", "missing_field", "Missing expected_valid field.")
            if "expected_consistent" not in task:
                add_issue(task_id, "error", "missing_field", "Missing expected_consistent field.")
        else:
            # if present, validate their types
            if "expected_valid" in task and not isinstance(task["expected_valid"], bool):
                add_issue(task_id, "error", "bad_type", "expected_valid must be bool.")
            if "expected_consistent" in task and not isinstance(task["expected_consistent"], bool):
                add_issue(task_id, "error", "bad_type", "expected_consistent must be bool.")

        # category
        if not isinstance(cat, str):
            add_issue(task_id, "error", "bad_type", "Field 'category' must be a string.")
            continue
        category_counts[cat] = category_counts.get(cat, 0) + 1

        # events uniqueness
        if len(set(events)) != len(events):
            add_issue(task_id, "error", "duplicate_event", "Events list contains duplicates.")

        # gold edges
        gold_edges = _coerce_edges(task["gold_relations"])
        if gold_edges is None:
            add_issue(task_id, "error", "bad_edges", "gold_relations is not a valid list of edge triples.")
            continue

        # check that gold edges reference known events and relation set
        event_set = set(events)
        for (a, b, r) in gold_edges:
            if r != "BEFORE":
                add_issue(task_id, "error", "bad_relation", "Only 'BEFORE' is supported.", relation=r)
            if a not in event_set or b not in event_set:
                add_issue(
                    task_id,
                    "error",
                    "unknown_event_in_edge",
                    "Gold edge references event not present in events list.",
                    edge=[a, b, r],
                )
            if a == b:
                add_issue(task_id, "error", "self_edge", "Gold edge cannot be self-referential.", edge=[a, b, r])

        # question should contain each event string (helps prompting consistency)
        q = task["question"]
        for e in events:
            if e not in q:
                sev: Literal["error", "warning"] = "error" if strict else "warning"
                add_issue(
                    task_id,
                    sev,
                    "event_not_in_question",
                    "Event string not found verbatim in question text.",
                    event=e,
                )
                break

        # Build gold temporal graph (for acyclic/cycle checks)
        tg = TemporalGraph()
        tg.add_events(events)
        tg.add_edges(gold_edges)

        gold_set = _edge_set(gold_edges)

        if cat == "ambiguous":
            if len(gold_edges) != 0:
                add_issue(task_id, "error", "ambiguous_nonempty_gold", "Ambiguous tasks must have empty gold_relations.")

        elif cat in ("linear_chain", "long_chain"):
            # Must be exactly consecutive chain edges
            expected = _edge_set([(events[i], events[i + 1], "BEFORE") for i in range(len(events) - 1)])
            if gold_set != expected:
                add_issue(
                    task_id,
                    "error",
                    "chain_gold_mismatch",
                    "Chain tasks must have gold as consecutive edges only.",
                    expected=sorted(list(expected)),
                    got=sorted(list(gold_set)),
                )
            # Must be acyclic
            if not tg.is_acyclic():
                add_issue(task_id, "error", "chain_has_cycle", "Chain tasks must be acyclic.")

        elif cat == "transitive_reasoning":
            # gold should be full closure for the chain implied by event order
            expected = _transitive_closure_edges_from_chain(events)
            if gold_set != expected:
                add_issue(
                    task_id,
                    "error",
                    "transitive_gold_mismatch",
                    "Transitive tasks must have gold as full transitive closure.",
                    expected=sorted(list(expected))[:20],
                    got=sorted(list(gold_set))[:20],
                    note="Lists truncated; compare sets programmatically if needed.",
                )
            if not tg.is_acyclic():
                add_issue(task_id, "error", "transitive_has_cycle", "Transitive tasks must be acyclic.")

        elif cat == "contradiction":
            # Expect cyclic gold
            if tg.is_acyclic():
                add_issue(task_id, "error", "contradiction_acyclic", "Contradiction tasks should be cyclic.")
            # Require at least one direct contradiction pair A->B and B->A
            contradictions = tg.direct_contradictions("BEFORE")
            if len(contradictions) == 0:
                add_issue(
                    task_id,
                    "error",
                    "contradiction_missing_pair",
                    "Contradiction tasks must contain at least one direct contradictory pair.",
                )

        else:
            # Unknown category: allow but warn/error depending on strict.
            sev2: Literal["error", "warning"] = "warning" if not strict else "error"
            add_issue(task_id, sev2, "unknown_category", "Unknown category value.", category=cat)

    num_errors = sum(1 for it in issues if it.severity == "error")
    num_warnings = sum(1 for it in issues if it.severity == "warning")
    return ValidationReport(
        num_tasks=len(tasks),
        num_errors=num_errors,
        num_warnings=num_warnings,
        issues=issues,
        category_counts=category_counts,
    )