from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, List, Optional, Sequence, Tuple

from src.schemas import Edge, ReasoningStep
from src.temporal_graph import _to_edge, canonicalise_relation


@dataclass(frozen=True)
class TemporalState:
    index: int
    label: str
    step_id: Optional[int]
    is_final_state: bool
    text: str
    support_edges: Tuple[Edge, ...]
    active_edges: Tuple[Edge, ...]
    mentioned_events: Tuple[str, ...]
    violation_types: Tuple[str, ...] = ()
    introduced_violation_types: Tuple[str, ...] = ()


@dataclass(frozen=True)
class TemporalTrace:
    states: Tuple[TemporalState, ...]

    def __len__(self) -> int:
        return len(self.states)

    def state(self, index: int) -> TemporalState:
        return self.states[index]

    def predicate_holds(self, index: int, predicate: str, args: Sequence[str]) -> bool:
        state = self.state(index)
        name = predicate.strip().lower()

        if name in {"before", "after", "simultaneous", "unknown"}:
            if len(args) != 2:
                return False
            relation = canonicalise_relation(name)
            return (args[0], args[1], relation) in state.active_edges

        if name == "supports":
            if len(args) != 3:
                return False
            try:
                edge = _to_edge(args)
            except ValueError:
                return False
            return edge in state.support_edges

        if name == "mentions_event":
            if len(args) != 1:
                return False
            return args[0] in state.mentioned_events

        if name == "has_violation":
            if len(args) != 1:
                return False
            return args[0] in state.violation_types

        if name == "introduced_violation":
            if len(args) != 1:
                return False
            return args[0] in state.introduced_violation_types

        if name == "is_final_state":
            return state.is_final_state

        return False

    def with_violations(self, violation_types_by_state: Sequence[Iterable[str]]) -> "TemporalTrace":
        states: List[TemporalState] = []
        seen: set[str] = set()
        for state, violation_types in zip(self.states, violation_types_by_state):
            ordered = tuple(sorted(set(violation_types)))
            introduced = tuple(sorted(set(ordered) - seen))
            seen.update(ordered)
            states.append(
                replace(
                    state,
                    violation_types=ordered,
                    introduced_violation_types=introduced,
                )
            )
        return TemporalTrace(states=tuple(states))


def _mentioned_events_from_step(
    *,
    allowed_events: Sequence[str],
    text: str,
    supports: Iterable[Edge],
) -> Tuple[str, ...]:
    mentioned = set()
    for event in allowed_events:
        if event in text:
            mentioned.add(event)
    for source, target, _ in supports:
        mentioned.add(source)
        mentioned.add(target)
    return tuple(sorted(mentioned))


def build_temporal_trace(
    *,
    allowed_events: Sequence[str],
    pred_edges: Iterable[Edge],
    reasoning_steps: Sequence[ReasoningStep],
) -> TemporalTrace:
    states: List[TemporalState] = []
    cumulative_supports: List[Edge] = []

    for index, step in enumerate(reasoning_steps):
        supports = tuple(_to_edge(edge) for edge in step.supports)
        cumulative_supports.extend(supports)
        states.append(
            TemporalState(
                index=index,
                label=f"step_{step.step_id}",
                step_id=step.step_id,
                is_final_state=False,
                text=step.text,
                support_edges=supports,
                active_edges=tuple(dict.fromkeys(cumulative_supports)),
                mentioned_events=_mentioned_events_from_step(
                    allowed_events=allowed_events,
                    text=step.text,
                    supports=supports,
                ),
            )
        )

    final_edges = tuple(_to_edge(edge) for edge in pred_edges)
    states.append(
        TemporalState(
            index=len(states),
            label="final_prediction",
            step_id=None,
            is_final_state=True,
            text="Final predicted relations",
            support_edges=(),
            active_edges=final_edges,
            mentioned_events=tuple(
                sorted({event for source, target, _ in final_edges for event in (source, target)})
            ),
        )
    )

    return TemporalTrace(states=tuple(states))
