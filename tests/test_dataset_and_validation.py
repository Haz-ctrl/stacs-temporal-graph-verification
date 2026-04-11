from __future__ import annotations

from src.benchmark_adapters import convert_tempeval_style_record
from src.dataset import load_jsonl, parse_temporal_task
from src.dataset_validation import validate_tasks


def test_parse_temporal_task_rejects_boolean_coercion() -> None:
    task = {
        "id": "t001",
        "category": "linear_chain",
        "question": "A happened before B.",
        "events": ["A", "B"],
        "gold_relations": [["A", "B", "BEFORE"]],
        "expected_valid": "true",
        "expected_consistent": True,
    }

    try:
        parse_temporal_task(task)
    except ValueError as exc:
        assert "expected_valid" in str(exc)
    else:
        raise AssertionError("parse_temporal_task should reject non-bool expected_valid")


def test_sample_tasks_validate_cleanly() -> None:
    tasks = load_jsonl("data/sample_tasks.jsonl")
    report = validate_tasks(tasks, strict=False, require_expected_fields=False)

    assert report.num_errors == 0


def test_generic_validation_accepts_diagnostic_relations() -> None:
    tasks = load_jsonl("data/diagnostic_eval.jsonl")

    report = validate_tasks(tasks, strict=False, require_expected_fields=False, profile="generic")

    assert report.num_errors == 0


def test_tempeval_style_record_converts_to_canonical_task() -> None:
    record = {
        "id": "te3_x",
        "passage": "Maya arrived before Noah boarded.",
        "events": [
            {"id": "e1", "text": "Maya arrived"},
            {"id": "e2", "text": "Noah boarded"},
        ],
        "relations": [{"source": "e1", "target": "e2", "relation": "BEFORE"}],
    }

    task = convert_tempeval_style_record(record)

    assert task["id"] == "te3_x"
    assert task["category"] == "tempeval_relation"
    assert task["events"] == ["Maya arrived", "Noah boarded"]
    assert task["gold_relations"] == [["Maya arrived", "Noah boarded", "BEFORE"]]
