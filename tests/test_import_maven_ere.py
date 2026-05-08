"""Tests for scripts/import_maven_ere.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.import_maven_ere import (
    _map_relation,
    convert_maven_ere_temporal_split,
    convert_maven_ere_test_candidates,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_map_relation_supported_only_by_default() -> None:
    assert _map_relation("BEFORE", coarsen_overlap=False) == "BEFORE"
    assert _map_relation("SIMULTANEOUS", coarsen_overlap=False) == "SIMULTANEOUS"
    assert _map_relation("OVERLAP", coarsen_overlap=False) is None
    assert _map_relation("CONTAINS", coarsen_overlap=False) is None


def test_map_relation_can_coarsen_overlap() -> None:
    assert _map_relation("OVERLAP", coarsen_overlap=True) == "SIMULTANEOUS"


def test_convert_valid_split_keeps_supported_relations(tmp_path: Path) -> None:
    input_path = tmp_path / "valid.jsonl"
    _write_jsonl(
        input_path,
        [
            {
                "id": "doc-1",
                "title": "Example",
                "tokens": [["A", "began", "."], ["B", "ended", "."]],
                "sentences": ["A began.", "B ended."],
                "events": [
                    {
                        "id": "EVENT_A",
                        "type": "Start",
                        "mention": [{"id": "m1", "trigger_word": "began", "sent_id": 0, "offset": [1, 2]}],
                    },
                    {
                        "id": "EVENT_B",
                        "type": "End",
                        "mention": [{"id": "m2", "trigger_word": "ended", "sent_id": 1, "offset": [1, 2]}],
                    },
                ],
                "TIMEX": [{"id": "TIME_1", "mention": "today", "type": "DATE", "sent_id": 0, "offset": [0, 1]}],
                "temporal_relations": {
                    "BEFORE": [["EVENT_A", "EVENT_B"], ["EVENT_B", "EVENT_A"]],
                    "CONTAINS": [["TIME_1", "EVENT_B"]],
                },
                "causal_relations": {"CAUSE": [], "PRECONDITION": []},
                "subevent_relations": [],
            }
        ],
    )

    tasks, stats = convert_maven_ere_temporal_split(
        input_path,
        split="valid",
        category="maven_ere_temporal",
        context_radius=1,
        coarsen_overlap=False,
        max_tasks=0,
        seed=42,
    )

    assert len(tasks) == 2
    assert stats["sampled_counts"] == {"BEFORE": 2}
    assert stats["skipped_relation_counts"] == {"CONTAINS": 1}
    assert all(task["gold_relations"][0][2] == "BEFORE" for task in tasks)
    assert all(task["metadata"]["document_id"] == "doc-1" for task in tasks)


def test_convert_valid_split_can_coarsen_overlap(tmp_path: Path) -> None:
    input_path = tmp_path / "valid.jsonl"
    _write_jsonl(
        input_path,
        [
            {
                "id": "doc-1",
                "title": "Example",
                "tokens": [["A", "met", "B", "."]],
                "sentences": ["A met B."],
                "events": [
                    {
                        "id": "EVENT_A",
                        "type": "Meet",
                        "mention": [{"id": "m1", "trigger_word": "met", "sent_id": 0, "offset": [1, 2]}],
                    },
                    {
                        "id": "EVENT_B",
                        "type": "Meet",
                        "mention": [{"id": "m2", "trigger_word": "met", "sent_id": 0, "offset": [1, 2]}],
                    },
                ],
                "TIMEX": [],
                "temporal_relations": {"OVERLAP": [["EVENT_A", "EVENT_B"]]},
                "causal_relations": {"CAUSE": [], "PRECONDITION": []},
                "subevent_relations": [],
            }
        ],
    )

    tasks, stats = convert_maven_ere_temporal_split(
        input_path,
        split="valid",
        category="maven_ere_temporal",
        context_radius=0,
        coarsen_overlap=True,
        max_tasks=0,
        seed=42,
    )

    assert len(tasks) == 1
    assert tasks[0]["gold_relations"] == [[tasks[0]["events"][0], tasks[0]["events"][1], "SIMULTANEOUS"]]
    assert stats["sampled_counts"] == {"SIMULTANEOUS": 1}


def test_convert_test_candidates_generates_unlabeled_pairs(tmp_path: Path) -> None:
    input_path = tmp_path / "test.jsonl"
    _write_jsonl(
        input_path,
        [
            {
                "id": "doc-2",
                "title": "Test doc",
                "tokens": [["A", "began", "."], ["It", "ended", "today", "."]],
                "sentences": ["A began.", "It ended today."],
                "event_mentions": [
                    {"id": "m1", "trigger_word": "began", "sent_id": 0, "offset": [1, 2], "type": "Start", "type_id": 1},
                    {"id": "m2", "trigger_word": "ended", "sent_id": 1, "offset": [1, 2], "type": "End", "type_id": 2},
                ],
                "TIMEX": [{"id": "TIME_1", "mention": "today", "type": "DATE", "sent_id": 1, "offset": [2, 3]}],
            }
        ],
    )

    tasks, stats = convert_maven_ere_test_candidates(
        input_path,
        split="test",
        category="maven_ere_temporal_test",
        context_radius=0,
        include_timex=True,
        sentence_window=-1,
        max_tasks=0,
    )

    assert len(tasks) == 6
    assert stats["num_tasks"] == 6
    assert all(task["gold_relations"] == [] for task in tasks)
    assert all(task["metadata"]["original_relation"] == "UNLABELED" for task in tasks)


def test_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/import_maven_ere.py", "--help"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.returncode == 0