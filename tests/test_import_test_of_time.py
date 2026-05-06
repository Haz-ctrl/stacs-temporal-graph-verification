"""Tests for scripts/import_test_of_time.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.import_test_of_time import (
    _derive_gold_from_answer,
    _event_names,
    _infer_category,
    _map_relation,
    convert_tot_record,
)


# ---------------------------------------------------------------------------
# _map_relation
# ---------------------------------------------------------------------------


def test_map_relation_before() -> None:
    assert _map_relation("BEFORE") == "BEFORE"


def test_map_relation_after() -> None:
    assert _map_relation("AFTER") == "AFTER"


def test_map_relation_ibefore_maps_to_before() -> None:
    assert _map_relation("IBEFORE") == "BEFORE"


def test_map_relation_precedes_maps_to_before() -> None:
    assert _map_relation("PRECEDES") == "BEFORE"


def test_map_relation_starts_maps_to_before() -> None:
    assert _map_relation("STARTS") == "BEFORE"


def test_map_relation_iafter_maps_to_after() -> None:
    assert _map_relation("IAFTER") == "AFTER"


def test_map_relation_follows_maps_to_after() -> None:
    assert _map_relation("FOLLOWS") == "AFTER"


def test_map_relation_finishes_maps_to_after() -> None:
    assert _map_relation("FINISHES") == "AFTER"


def test_map_relation_simultaneous() -> None:
    assert _map_relation("SIMULTANEOUS") == "SIMULTANEOUS"


def test_map_relation_identity_maps_to_simultaneous() -> None:
    assert _map_relation("IDENTITY") == "SIMULTANEOUS"


def test_map_relation_equals_maps_to_simultaneous() -> None:
    assert _map_relation("EQUALS") == "SIMULTANEOUS"


def test_map_relation_unknown_for_unrecognised() -> None:
    assert _map_relation("VAGUE") == "UNKNOWN"
    assert _map_relation("") == "UNKNOWN"


# ---------------------------------------------------------------------------
# _infer_category
# ---------------------------------------------------------------------------


def test_infer_category_easy() -> None:
    assert _infer_category({"category": "easy"}) == "tot_easy"


def test_infer_category_hard() -> None:
    assert _infer_category({"category": "hard"}) == "tot_hard"


def test_infer_category_from_graph_type_chain_depth_1() -> None:
    assert _infer_category({"graph_type": "chain", "depth": 1}) == "tot_easy"


def test_infer_category_from_graph_type_complex() -> None:
    assert _infer_category({"graph_type": "dag", "depth": 5}) == "tot_hard"


def test_infer_category_absent_defaults_to_hard() -> None:
    # No category, no graph_type — fallback to hard
    assert _infer_category({}) == "tot_hard"


# ---------------------------------------------------------------------------
# _event_names
# ---------------------------------------------------------------------------


def test_event_names_from_dict_list() -> None:
    events = [{"name": "Alice born", "date": "1990"}, {"name": "Bob born", "date": "1985"}]
    assert _event_names(events) == ["Alice born", "Bob born"]


def test_event_names_from_string_list() -> None:
    assert _event_names(["A", "B", "C"]) == ["A", "B", "C"]


def test_event_names_raises_on_non_list() -> None:
    with pytest.raises(ValueError):
        _event_names({"name": "X"})


def test_event_names_raises_on_missing_name() -> None:
    with pytest.raises(ValueError):
        _event_names([{"date": "1990"}])


# ---------------------------------------------------------------------------
# _derive_gold_from_answer
# ---------------------------------------------------------------------------


def test_derive_gold_from_answer_before() -> None:
    record = {"answer": "A", "choices": ["BEFORE", "AFTER"]}
    events = ["Event X", "Event Y"]
    result = _derive_gold_from_answer(record, events)
    assert result == [("Event X", "Event Y", "BEFORE")]


def test_derive_gold_from_answer_after() -> None:
    record = {"answer": "B", "choices": ["BEFORE", "AFTER"]}
    events = ["X", "Y"]
    result = _derive_gold_from_answer(record, events)
    assert result == [("X", "Y", "AFTER")]


def test_derive_gold_returns_none_for_wrong_event_count() -> None:
    record = {"answer": "A", "choices": ["BEFORE"]}
    events = ["X", "Y", "Z"]
    assert _derive_gold_from_answer(record, events) is None


def test_derive_gold_returns_none_for_out_of_bounds_answer() -> None:
    record = {"answer": "C", "choices": ["BEFORE", "AFTER"]}
    events = ["X", "Y"]
    assert _derive_gold_from_answer(record, events) is None


# ---------------------------------------------------------------------------
# convert_tot_record — well-formed input
# ---------------------------------------------------------------------------


_WELL_FORMED = {
    "id": "tot_001",
    "question": "When did these events happen?",
    "answer": "A",
    "choices": ["BEFORE", "AFTER"],
    "events": [{"name": "Meeting", "date": "2020-01"}, {"name": "Report", "date": "2020-03"}],
    "relations": [{"source": "Meeting", "target": "Report", "relation": "BEFORE"}],
    "graph_type": "chain",
    "depth": 1,
    "category": "easy",
}


def test_convert_well_formed_record() -> None:
    task = convert_tot_record(_WELL_FORMED)

    assert task["id"] == "tot_001"
    assert task["category"] == "tot_easy"
    assert task["expected_valid"] is True
    assert task["expected_consistent"] is True
    assert task["events"] == ["Meeting", "Report"]
    assert task["gold_relations"] == [["Meeting", "Report", "BEFORE"]]
    assert "question" in task
    assert task["metadata"]["source_format"] == "test_of_time"


def test_convert_hard_category_sets_expected_valid_false() -> None:
    record = dict(_WELL_FORMED)
    record["category"] = "hard"
    task = convert_tot_record(record)
    assert task["category"] == "tot_hard"
    assert task["expected_valid"] is False


def test_convert_derives_gold_when_relations_absent() -> None:
    record = {
        "id": "tot_002",
        "answer": "A",
        "choices": ["BEFORE", "AFTER"],
        "events": [{"name": "E1"}, {"name": "E2"}],
        "graph_type": "chain",
        "depth": 1,
        "category": "easy",
    }
    task = convert_tot_record(record)
    assert task["gold_relations"] == [["E1", "E2", "BEFORE"]]


def test_convert_category_filter_raises_for_excluded() -> None:
    with pytest.raises(ValueError, match="category"):
        convert_tot_record(_WELL_FORMED, allowed_categories=["tot_hard"])


# ---------------------------------------------------------------------------
# convert_tot_record — malformed input
# ---------------------------------------------------------------------------


def test_convert_raises_on_missing_id() -> None:
    record = dict(_WELL_FORMED)
    del record["id"]
    with pytest.raises(ValueError):
        convert_tot_record(record)


def test_convert_raises_on_missing_events() -> None:
    record = dict(_WELL_FORMED)
    del record["events"]
    with pytest.raises(ValueError):
        convert_tot_record(record)


def test_convert_raises_on_unknown_relation_source() -> None:
    record = dict(_WELL_FORMED)
    record["relations"] = [{"source": "Ghost", "target": "Report", "relation": "BEFORE"}]
    with pytest.raises(ValueError):
        convert_tot_record(record)


# ---------------------------------------------------------------------------
# Graceful skip integration (simulates the main() loop behaviour)
# ---------------------------------------------------------------------------


def test_graceful_skip_on_malformed_record() -> None:
    """The convert function raises; callers should catch and skip."""
    bad_record = {"question": "X"}  # no id, no events
    with pytest.raises((ValueError, TypeError)):
        convert_tot_record(bad_record)


def test_cli_help(tmp_path: Path) -> None:
    """Verify the CLI parses --help without error."""
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "scripts/import_test_of_time.py", "--help"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.returncode == 0
    assert "--input" in result.stdout
