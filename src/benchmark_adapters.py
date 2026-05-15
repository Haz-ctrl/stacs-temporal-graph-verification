from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import xml.etree.ElementTree as ET

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


TEMPEVAL3_RELATION_MAP = {
    "BEFORE": TemporalRelation.BEFORE.value,
    "IBEFORE": TemporalRelation.BEFORE.value,
    "AFTER": TemporalRelation.AFTER.value,
    "IAFTER": TemporalRelation.AFTER.value,
    "SIMULTANEOUS": TemporalRelation.SIMULTANEOUS.value,
    "IDENTITY": TemporalRelation.SIMULTANEOUS.value,
}


@dataclass(frozen=True)
class TempEvalTaskBundle:
    tasks: List[Dict[str, Any]]
    stats: Dict[str, Any]


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


def _parse_relations(
    raw_relations: Any, event_ids: Iterable[str]
) -> List[TempEvalRelation]:
    if not isinstance(raw_relations, list):
        raise ValueError("'relations' must be a list.")
    allowed_ids = set(event_ids)
    relations: List[TempEvalRelation] = []
    for idx, raw_relation in enumerate(raw_relations):
        if not isinstance(raw_relation, dict):
            raise ValueError(f"Relation at index {idx} must be an object.")
        source = _require_string(
            raw_relation.get("source"), field_name=f"relations[{idx}].source"
        )
        target = _require_string(
            raw_relation.get("target"), field_name=f"relations[{idx}].target"
        )
        relation = TemporalRelation.canonicalise(
            _require_string(
                raw_relation.get("relation"), field_name=f"relations[{idx}].relation"
            )
        ).value
        if source not in allowed_ids or target not in allowed_ids:
            raise ValueError(
                f"Relation at index {idx} references unknown event ids: {(source, target)!r}"
            )
        relations.append(
            TempEvalRelation(source=source, target=target, relation=relation)
        )
    return relations


def coarsen_tempeval3_relation(relation: str) -> Optional[str]:
    relation = _require_string(relation, field_name="relation").upper()
    return TEMPEVAL3_RELATION_MAP.get(relation)


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


def convert_tempeval3_tml_file(
    path: str | Path,
    *,
    split: str,
    category: str = "tempeval_relation",
) -> TempEvalTaskBundle:
    xml_path = Path(path)
    root = ET.parse(xml_path).getroot()

    title = (root.findtext("TITLE") or "").strip()
    text_node = root.find("TEXT")
    if text_node is None:
        raise ValueError(f"{xml_path} is missing a TEXT node.")
    full_text = "".join(text_node.itertext()).strip()
    sentences = [line.strip() for line in full_text.splitlines() if line.strip()]

    events_by_id: Dict[str, Dict[str, Any]] = {}
    for node in text_node.iter():
        if node.tag != "EVENT":
            continue
        eid = _require_string(node.attrib.get("eid"), field_name="EVENT.eid")
        sent_idx_raw = node.attrib.get("sent_idx")
        sent_idx = int(sent_idx_raw) if sent_idx_raw is not None else None
        events_by_id[eid] = {
            "text": _require_string(
                "".join(node.itertext()), field_name=f"EVENT[{eid}]"
            ),
            "sent_idx": sent_idx,
        }

    instances_by_id: Dict[str, Dict[str, Any]] = {}
    for node in root.findall("MAKEINSTANCE"):
        eiid = node.attrib.get("eiid")
        eid = node.attrib.get("eid")
        if eiid and eid and eid in events_by_id:
            instances_by_id[eiid] = {
                "eid": eid,
                "text": events_by_id[eid]["text"],
                "sent_idx": events_by_id[eid]["sent_idx"],
            }

    tasks: List[Dict[str, Any]] = []
    stats = {
        "document_id": (root.findtext("DOCID") or xml_path.stem).strip(),
        "split": split,
        "total_tlinks": 0,
        "event_event_tlinks": 0,
        "converted_tasks": 0,
        "skipped_unmapped_relations": 0,
        "skipped_missing_instances": 0,
    }

    for index, tlink in enumerate(root.findall("TLINK"), start=1):
        stats["total_tlinks"] += 1
        source_id = tlink.attrib.get("from")
        target_id = tlink.attrib.get("to")
        if source_id not in instances_by_id or target_id not in instances_by_id:
            continue
        stats["event_event_tlinks"] += 1

        source = instances_by_id[source_id]
        target = instances_by_id[target_id]
        relation_raw = _require_string(
            tlink.attrib.get("relType"), field_name="TLINK.relType"
        )
        relation = coarsen_tempeval3_relation(relation_raw)
        if relation is None:
            stats["skipped_unmapped_relations"] += 1
            continue

        if not source["text"] or not target["text"]:
            stats["skipped_missing_instances"] += 1
            continue

        source_label = f"{source['text']} [{source_id}]"
        target_label = f"{target['text']} [{target_id}]"
        sent_indices = [
            idx for idx in (source["sent_idx"], target["sent_idx"]) if idx is not None
        ]
        if sent_indices and sentences:
            start = max(0, min(sent_indices))
            end = min(len(sentences) - 1, max(sent_indices))
            passage = " ".join(sentences[start : end + 1]).strip()
        else:
            start = 0
            end = max(len(sentences) - 1, 0)
            passage = full_text

        prompt_lines = []
        if title:
            prompt_lines.extend(["Title:", title, ""])
        prompt_lines.extend(
            [
                "Passage:",
                passage,
                "",
                "Determine the temporal relation between the following event mentions.",
                f"- {source_label}",
                f"- {target_label}",
                "",
                "Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.",
            ]
        )
        task_id = f"te3_{split}_{stats['document_id']}_{tlink.attrib.get('lid', f'tlink_{index}')}"
        tasks.append(
            {
                "id": task_id,
                "category": category,
                "question": "\n".join(prompt_lines),
                "events": [source_label, target_label],
                "gold_relations": [[source_label, target_label, relation]],
                "expected_valid": True,
                "expected_consistent": True,
                "metadata": {
                    "source_format": "tempeval3_tml",
                    "document_id": stats["document_id"],
                    "split": split,
                    "title": title,
                    "tlink_id": tlink.attrib.get("lid", f"tlink_{index}"),
                    "original_relation": relation_raw,
                    "mapped_relation": relation,
                    "source_eiid": source_id,
                    "target_eiid": target_id,
                    "source_eid": source["eid"],
                    "target_eid": target["eid"],
                    "sentence_start": start,
                    "sentence_end": end,
                },
            }
        )

    stats["converted_tasks"] = len(tasks)
    return TempEvalTaskBundle(tasks=tasks, stats=stats)
