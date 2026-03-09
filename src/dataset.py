from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.schemas import TemporalTask
from src.temporal_graph import Edge, _to_edge


def load_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    """
    Load a JSONL file (one object per line).
    """
    path = Path(path)
    items: List[Dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as handle:
        for i, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as err:
                raise ValueError(f"Invalid JSON on line {i} of {path}: {err}") from err

            if not isinstance(obj, dict):
                raise ValueError(f"Expected JSON object on line {i} of {path}, got {type(obj).__name__}.")
            items.append(obj)

    return items


def parse_temporal_task(obj: Dict[str, Any]) -> TemporalTask:
    """
    Convert a raw task dictionary into a typed TemporalTask.
    """
    task_id_raw = obj.get("id")
    question_raw = obj.get("question")
    events_raw = obj.get("events")
    gold_raw = obj.get("gold_relations", [])

    if not isinstance(task_id_raw, str) or not task_id_raw.strip():
        raise ValueError("Task field 'id' must be a non-empty string.")
    if not isinstance(question_raw, str):
        raise ValueError(f"Task {task_id_raw}: field 'question' must be a string.")
    if not isinstance(events_raw, list) or not all(isinstance(event, str) for event in events_raw):
        raise ValueError(f"Task {task_id_raw}: field 'events' must be a list of strings.")
    if not isinstance(gold_raw, list):
        raise ValueError(f"Task {task_id_raw}: field 'gold_relations' must be a list.")

    gold_edges: List[Edge] = [_to_edge(edge) for edge in gold_raw]

    return TemporalTask(
        id=task_id_raw,
        question=question_raw,
        events=list(events_raw),
        gold_relations=gold_edges,
        category=str(obj.get("category", "")),
        expected_valid=bool(obj.get("expected_valid", True)),
        expected_consistent=bool(obj.get("expected_consistent", True)),
    )


def load_temporal_tasks(path: str | Path) -> List[TemporalTask]:
    """
    Load and parse a JSONL dataset into typed TemporalTask objects.
    """
    return [parse_temporal_task(obj) for obj in load_jsonl(path)]