from __future__ import annotations

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
