from __future__ import annotations

from pathlib import Path

from src.benchmark_adapters import (
    coarsen_tempeval3_relation,
    convert_tempeval3_tml_file,
    convert_tempeval_style_record,
)
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


def test_generic_validation_does_not_warn_on_external_categories() -> None:
    report = validate_tasks(
        [
            {
                "id": "te3_x",
                "category": "tempeval_relation",
                "question": "Passage:\nA happened before B.\n\n- A happened\n- B happened",
                "events": ["A happened", "B happened"],
                "gold_relations": [["A happened", "B happened", "BEFORE"]],
                "expected_valid": True,
                "expected_consistent": True,
            }
        ],
        strict=True,
        require_expected_fields=False,
        profile="generic",
    )

    assert report.num_errors == 0
    assert report.num_warnings == 0


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


def test_tempeval3_relation_coarsening_and_tml_conversion(tmp_path: Path) -> None:
    assert coarsen_tempeval3_relation("IBEFORE") == "BEFORE"
    assert coarsen_tempeval3_relation("IDENTITY") == "SIMULTANEOUS"
    assert coarsen_tempeval3_relation("INCLUDES") is None

    xml_path = tmp_path / "doc.tml"
    xml_path.write_text(
        """
<TimeML>
  <DOCID>doc_001</DOCID>
  <TITLE>Example</TITLE>
  <TEXT>Alpha <EVENT eid="e1" sent_idx="0">arrived</EVENT> first.
Beta <EVENT eid="e2" sent_idx="1">left</EVENT> later.</TEXT>
  <MAKEINSTANCE eiid="ei1" eid="e1" />
  <MAKEINSTANCE eiid="ei2" eid="e2" />
  <TLINK lid="l1" from="ei1" to="ei2" relType="IBEFORE" />
  <TLINK lid="l2" from="ei2" to="ei1" relType="INCLUDES" />
</TimeML>
        """.strip(),
        encoding="utf-8",
    )

    bundle = convert_tempeval3_tml_file(xml_path, split="test")

    assert bundle.stats["event_event_tlinks"] == 2
    assert bundle.stats["converted_tasks"] == 1
    assert bundle.tasks[0]["id"] == "te3_test_doc_001_l1"
    assert bundle.tasks[0]["gold_relations"] == [["arrived [ei1]", "left [ei2]", "BEFORE"]]
    assert "arrived [ei1]" in bundle.tasks[0]["question"]
