"""
Adapter for the Test of Time benchmark (Fatemi et al., arXiv:2406.09170).

Converts ToT source records to the project's TemporalTask schema so they can
be run through run_llm_baseline.py without modification. Malformed records are
logged and skipped; the script never raises on bad input.

Source format per record:
    {
      "id": "...",
      "question": "...",
      "answer": "A",
      "choices": ["...", "..."],
      "events": [{"name": "...", "date": "..."}, ...],
      "relations": [{"source": "...", "target": "...", "relation": "BEFORE"}, ...],
      "graph_type": "chain",
      "depth": 1,
      "category": "easy"
    }
All fields are best-effort; any may be absent.

Output JSONL is readable by src/dataset.py:load_jsonl without modification.

CLI:
    python scripts/import_test_of_time.py \
        --input path/to/test_of_time.jsonl \
        --output data/tot_eval.jsonl \
        [--max-items N] \
        [--categories tot_easy tot_hard]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Relation label mapping (ToT → project canonical)
# ---------------------------------------------------------------------------

_RELATION_MAP: Dict[str, str] = {
    "BEFORE": "BEFORE",
    "IBEFORE": "BEFORE",
    "PRECEDES": "BEFORE",
    "STARTS": "BEFORE",
    "AFTER": "AFTER",
    "IAFTER": "AFTER",
    "FOLLOWS": "AFTER",
    "FINISHES": "AFTER",
    "SIMULTANEOUS": "SIMULTANEOUS",
    "IDENTITY": "SIMULTANEOUS",
    "EQUALS": "SIMULTANEOUS",
}

# ---------------------------------------------------------------------------
# Category mapping
# ---------------------------------------------------------------------------

_CATEGORY_MAP: Dict[str, str] = {
    "easy": "tot_easy",
    "hard": "tot_hard",
}

# Answer letters A–Z map to choice index 0–25.
_ANSWER_INDEX: Dict[str, int] = {chr(ord("A") + i): i for i in range(26)}


def _map_relation(label: str) -> str:
    """Map a ToT relation label to the project canonical label."""
    return _RELATION_MAP.get(label.strip().upper(), "UNKNOWN")


def _map_category(raw: str, *, graph_type: str = "", depth: int = 0) -> str:
    """Map a ToT category string to the project category label."""
    canonical = _CATEGORY_MAP.get(str(raw).strip().lower(), "")
    if canonical:
        return canonical
    # Infer from graph_type + depth when category field is absent or unrecognised.
    if graph_type in ("chain", "linear") and depth <= 2:
        return "tot_easy"
    return "tot_hard"


def _infer_category(record: Dict[str, Any]) -> str:
    raw = record.get("category", "")
    graph_type = str(record.get("graph_type", ""))
    depth = int(record.get("depth", 0))
    return _map_category(raw, graph_type=graph_type, depth=depth)


def _event_names(events_raw: Any) -> List[str]:
    """Extract event name strings from the events list."""
    if not isinstance(events_raw, list):
        raise ValueError("'events' must be a list.")
    names: List[str] = []
    for idx, ev in enumerate(events_raw):
        if isinstance(ev, dict):
            name = ev.get("name") or ev.get("text") or ev.get("id")
            if not name or not str(name).strip():
                raise ValueError(f"Event at index {idx} has no usable name.")
            names.append(str(name).strip())
        elif isinstance(ev, str) and ev.strip():
            names.append(ev.strip())
        else:
            raise ValueError(f"Event at index {idx} is not a usable type: {type(ev)}")
    return names


def _parse_relations(
    relations_raw: Any,
    event_names: List[str],
) -> List[Tuple[str, str, str]]:
    """Parse relations into canonical (source, target, label) triples."""
    if not isinstance(relations_raw, list):
        raise ValueError("'relations' must be a list.")
    event_set = set(event_names)
    triples: List[Tuple[str, str, str]] = []
    for idx, rel in enumerate(relations_raw):
        if not isinstance(rel, dict):
            raise ValueError(f"Relation at index {idx} must be an object.")
        source = str(rel.get("source", "")).strip()
        target = str(rel.get("target", "")).strip()
        label = _map_relation(str(rel.get("relation", "UNKNOWN")))
        if not source or source not in event_set:
            raise ValueError(f"Relation {idx} has unknown source: {source!r}")
        if not target or target not in event_set:
            raise ValueError(f"Relation {idx} has unknown target: {target!r}")
        triples.append((source, target, label))
    return triples


def _derive_gold_from_answer(
    record: Dict[str, Any],
    event_names: List[str],
) -> Optional[List[Tuple[str, str, str]]]:
    """
    Derive a single gold relation from the answer field when relations are absent
    and there are exactly two events.

    Returns None when the answer cannot be mapped to a known relation.
    """
    if len(event_names) != 2:
        return None
    answer = str(record.get("answer", "")).strip().upper()
    choices = record.get("choices", [])
    if not answer or not isinstance(choices, list):
        return None
    idx = _ANSWER_INDEX.get(answer)
    if idx is None or idx >= len(choices):
        return None
    choice_label = str(choices[idx]).strip().upper()
    mapped = _map_relation(choice_label)
    if mapped == "UNKNOWN" and choice_label not in _RELATION_MAP:
        return None
    return [(event_names[0], event_names[1], mapped)]


def convert_tot_record(
    record: Dict[str, Any],
    *,
    allowed_categories: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Convert a single ToT record to the project's TemporalTask dict format.

    Raises:
        ValueError: If the record is structurally invalid.
    """
    task_id = str(record.get("id", "")).strip()
    if not task_id:
        raise ValueError("Record has no 'id' field.")

    question = str(record.get("question", "")).strip()

    events_raw = record.get("events")
    if events_raw is None:
        raise ValueError(f"Task {task_id}: missing 'events' field.")
    event_names = _event_names(events_raw)
    if not event_names:
        raise ValueError(f"Task {task_id}: 'events' list is empty.")

    relations_raw = record.get("relations")
    if relations_raw is not None:
        gold_triples = _parse_relations(relations_raw, event_names)
    else:
        gold_triples_opt = _derive_gold_from_answer(record, event_names)
        gold_triples = gold_triples_opt if gold_triples_opt is not None else []

    category = _infer_category(record)
    if allowed_categories and category not in allowed_categories:
        raise ValueError(
            f"Task {task_id}: category {category!r} not in allowed set {allowed_categories}."
        )

    expected_valid = category == "tot_easy"

    if not question:
        choices_raw = record.get("choices", [])
        choices_text = " / ".join(str(c) for c in choices_raw) if choices_raw else ""
        event_lines = "\n".join(f"- {e}" for e in event_names)
        question = (
            f"Determine the temporal relations between the following events:\n"
            f"{event_lines}"
        )
        if choices_text:
            question += f"\n\nChoices: {choices_text}"

    return {
        "id": task_id,
        "category": category,
        "question": question,
        "events": event_names,
        "gold_relations": [[s, t, r] for s, t, r in gold_triples],
        "expected_valid": expected_valid,
        "expected_consistent": expected_valid,
        "metadata": {
            "source_format": "test_of_time",
            "original_category": record.get("category"),
            "graph_type": record.get("graph_type"),
            "depth": record.get("depth"),
            "answer": record.get("answer"),
            "choices": record.get("choices"),
        },
    }


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for i, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {i}: {exc}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"Line {i}: expected JSON object, got {type(obj).__name__}.")
            rows.append(obj)
    return rows


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Test of Time benchmark records to project TemporalTask JSONL."
    )
    parser.add_argument("--input", required=True, help="Path to ToT source JSONL.")
    parser.add_argument("--output", required=True, help="Path for canonical output JSONL.")
    parser.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="Maximum number of records to convert (0 = all).",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=[],
        help="Restrict output to these category labels (e.g. tot_easy tot_hard).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    allowed_categories: Optional[List[str]] = args.categories or None

    source_records = _load_jsonl(input_path)
    if args.max_items > 0:
        source_records = source_records[: args.max_items]

    converted: List[Dict[str, Any]] = []
    n_skipped = 0
    category_counts: Dict[str, int] = {}

    for record in source_records:
        try:
            task = convert_tot_record(record, allowed_categories=allowed_categories)
        except (ValueError, TypeError, KeyError) as exc:
            record_id = record.get("id", "<unknown>")
            logger.warning("Skipping record %r: %s", record_id, exc)
            n_skipped += 1
            continue
        converted.append(task)
        cat = task["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    _write_jsonl(output_path, converted)

    summary = {
        "n_input": len(source_records),
        "n_converted": len(converted),
        "n_skipped": n_skipped,
        "category_counts": category_counts,
    }
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
