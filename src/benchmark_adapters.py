from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from src.schemas import TemporalRelation


@dataclass(frozen=True)
class TempEvalEvent:
    event_id: str
    text: str


@dataclass(frozen=True)
class TempEvalRelation:
    source: str
    target: str
    relation: str


def _require_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Field '{field_name}' must be a non-empty string.")
    return value.strip()


def _parse_events(raw_events: Any) -> List[TempEvalEvent]:
    if not isinstance(raw_events, list) or not raw_events:
        raise ValueError("'events' must be a non-empty list.")
    events: List[TempEvalEvent] = []
    seen_ids: set[str] = set()
    seen_texts: set[str] = set()
    for idx, raw_event in enumerate(raw_events):
        if not isinstance(raw_event, dict):
            raise ValueError(f"Event at index {idx} must be an object.")
        event_id = _require_string(raw_event.get("id"), field_name=f"events[{idx}].id")
        text = _require_string(raw_event.get("text"), field_name=f"events[{idx}].text")
        if event_id in seen_ids:
            raise ValueError(f"Duplicate TempEval event id: {event_id!r}")
        if text in seen_texts:
            raise ValueError(f"Duplicate TempEval event text: {text!r}")
        seen_ids.add(event_id)
        seen_texts.add(text)
        events.append(TempEvalEvent(event_id=event_id, text=text))
    return events


def _parse_relations(raw_relations: Any, event_ids: Iterable[str]) -> List[TempEvalRelation]:
    if not isinstance(raw_relations, list):
        raise ValueError("'relations' must be a list.")
    allowed_ids = set(event_ids)
    relations: List[TempEvalRelation] = []
    for idx, raw_relation in enumerate(raw_relations):
        if not isinstance(raw_relation, dict):
            raise ValueError(f"Relation at index {idx} must be an object.")
        source = _require_string(raw_relation.get("source"), field_name=f"relations[{idx}].source")
        target = _require_string(raw_relation.get("target"), field_name=f"relations[{idx}].target")
        relation = TemporalRelation.canonicalise(
            _require_string(raw_relation.get("relation"), field_name=f"relations[{idx}].relation")
        ).value
        if source not in allowed_ids or target not in allowed_ids:
            raise ValueError(
                f"Relation at index {idx} references unknown event ids: {(source, target)!r}"
            )
        relations.append(TempEvalRelation(source=source, target=target, relation=relation))
    return relations


def convert_tempeval_style_record(
    record: Dict[str, Any],
    *,
    category: str = "tempeval_relation",
) -> Dict[str, Any]:
    task_id = _require_string(record.get("id"), field_name="id")
    passage = _require_string(record.get("passage"), field_name="passage")
    events = _parse_events(record.get("events"))
    event_by_id = {event.event_id: event.text for event in events}
    relations = _parse_relations(record.get("relations", []), event_by_id.keys())

    event_texts = [event.text for event in events]
    gold_relations = [
        [event_by_id[relation.source], event_by_id[relation.target], relation.relation]
        for relation in relations
    ]

    event_inventory = "\n".join(f"- {event.text}" for event in events)
    question = (
        "Passage:\n"
        f"{passage}\n\n"
        "Determine the temporal relations between the following events:\n"
        f"{event_inventory}"
    )

    return {
        "id": task_id,
        "category": category,
        "question": question,
        "events": event_texts,
        "gold_relations": gold_relations,
        "expected_valid": True,
        "expected_consistent": True,
        "metadata": {
            "source_format": "tempeval_style",
            "passage": passage,
            "event_id_map": {event.event_id: event.text for event in events},
        },
    }
