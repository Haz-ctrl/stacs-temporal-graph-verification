from __future__ import annotations

import pytest

from src.prediction_schema import PredictionParseError, parse_model_prediction_json


def test_parse_model_prediction_json_valid_minimal_payload() -> None:
    raw = """
    {
      "answer": "A happened before B.",
      "events": ["A", "B"],
      "relations": [["A", "B", "BEFORE"]],
      "reasoning_steps": []
    }
    """

    parsed = parse_model_prediction_json(raw, task_id="t001")

    assert parsed.task_id == "t001"
    assert parsed.answer == "A happened before B."
    assert parsed.pred_events == ["A", "B"]
    assert parsed.pred_edges == [("A", "B", "BEFORE")]
    assert parsed.reasoning_steps == []
    assert parsed.raw_output == raw


def test_parse_model_prediction_json_valid_with_reasoning_steps() -> None:
    raw = """
    {
      "answer": "A happened before C.",
      "events": ["A", "B", "C"],
      "relations": [
        ["A", "B", "BEFORE"],
        ["B", "C", "BEFORE"]
      ],
      "reasoning_steps": [
        {
          "step_id": 1,
          "text": "The prompt states A happened before B.",
          "supports": [["A", "B", "BEFORE"]]
        },
        {
          "step_id": 2,
          "text": "The prompt states B happened before C.",
          "supports": [["B", "C", "BEFORE"]]
        }
      ]
    }
    """

    parsed = parse_model_prediction_json(raw, task_id="t002")

    assert parsed.task_id == "t002"
    assert parsed.answer == "A happened before C."
    assert parsed.pred_events == ["A", "B", "C"]
    assert parsed.pred_edges == [
        ("A", "B", "BEFORE"),
        ("B", "C", "BEFORE"),
    ]
    assert len(parsed.reasoning_steps) == 2
    assert parsed.reasoning_steps[0].step_id == 1
    assert parsed.reasoning_steps[0].text == "The prompt states A happened before B."
    assert parsed.reasoning_steps[0].supports == [("A", "B", "BEFORE")]
    assert parsed.reasoning_steps[1].step_id == 2


def test_parse_model_prediction_json_accepts_reasoning_step_aliases() -> None:
    raw = """
    {
      "answer": "UNKNOWN",
      "events": ["A", "B"],
      "relations": [["A", "B", "UNKNOWN"]],
      "reasoning_steps": [
        {
          "step": 1,
          "description": "The text does not link A and B.",
          "support": [["A", "B", "UNKNOWN"]]
        }
      ]
    }
    """

    parsed = parse_model_prediction_json(raw, task_id="t002_alias")

    assert parsed.reasoning_steps[0].step_id == 1
    assert parsed.reasoning_steps[0].text == "The text does not link A and B."
    assert parsed.reasoning_steps[0].supports == [("A", "B", "UNKNOWN")]


def test_parse_model_prediction_json_accepts_optional_confidence_fields() -> None:
    raw = """
    {
      "answer": "A happened before B.",
      "answer_confidence": 0.8,
      "events": ["A", "B"],
      "relations": [["A", "B", "BEFORE"]],
      "reasoning_steps": [
        {
          "step_id": 1,
          "text": "The question states A happened before B.",
          "supports": [["A", "B", "BEFORE"]],
          "confidence": 0.6
        }
      ]
    }
    """

    parsed = parse_model_prediction_json(raw, task_id="t002b")

    assert parsed.answer_confidence == 0.8
    assert parsed.reasoning_steps[0].confidence == 0.6


def test_parse_model_prediction_json_rejects_invalid_json() -> None:
    raw = """{ invalid json }"""

    with pytest.raises(PredictionParseError, match="Invalid JSON") as exc_info:
        parse_model_prediction_json(raw, task_id="t003")
    assert exc_info.value.category == "invalid_json"


def test_parse_model_prediction_json_rejects_non_object_top_level() -> None:
    raw = """["not", "an", "object"]"""

    with pytest.raises(PredictionParseError, match="Top-level model output must be a JSON object"):
        parse_model_prediction_json(raw, task_id="t004")


def test_parse_model_prediction_json_requires_answer_string() -> None:
    raw = """
    {
      "answer": 123,
      "events": ["A", "B"],
      "relations": []
    }
    """

    with pytest.raises(PredictionParseError, match="Expected string field 'answer'"):
        parse_model_prediction_json(raw, task_id="t005")


def test_parse_model_prediction_json_requires_events_list_of_strings() -> None:
    raw = """
    {
      "answer": "test",
      "events": ["A", 2],
      "relations": []
    }
    """

    with pytest.raises(PredictionParseError, match="'events' must be a list of strings"):
        parse_model_prediction_json(raw, task_id="t006")


def test_parse_model_prediction_json_requires_relations_to_be_list() -> None:
    raw = """
    {
      "answer": "test",
      "events": ["A", "B"],
      "relations": "not-a-list"
    }
    """

    with pytest.raises(PredictionParseError, match="'relations' must be a list"):
        parse_model_prediction_json(raw, task_id="t007")


def test_parse_model_prediction_json_rejects_malformed_relation_triple() -> None:
    raw = """
    {
      "answer": "test",
      "events": ["A", "B"],
      "relations": [["A", "B"]]
    }
    """

    with pytest.raises(PredictionParseError, match="Invalid edge in 'relations'") as exc_info:
        parse_model_prediction_json(raw, task_id="t008")
    assert exc_info.value.category == "invalid_edge_support"


def test_parse_model_prediction_json_rejects_invalid_relation_label() -> None:
    raw = """
    {
      "answer": "test",
      "events": ["A", "B"],
      "relations": [["A", "B", "DURING"]]
    }
    """

    with pytest.raises(PredictionParseError, match="Invalid edge in 'relations'"):
        parse_model_prediction_json(raw, task_id="t009")


def test_parse_model_prediction_json_requires_reasoning_steps_list() -> None:
    raw = """
    {
      "answer": "test",
      "events": ["A", "B"],
      "relations": [],
      "reasoning_steps": "not-a-list"
    }
    """

    with pytest.raises(PredictionParseError, match="'reasoning_steps' must be a list"):
        parse_model_prediction_json(raw, task_id="t010")


def test_parse_model_prediction_json_accepts_digit_string_step_id() -> None:
    raw = """
    {
      "answer": "test",
      "events": ["A", "B"],
      "relations": [],
      "reasoning_steps": [
        {
          "step_id": "1",
          "text": "A before B",
          "supports": [["A", "B", "BEFORE"]]
        }
      ]
    }
    """

    parsed = parse_model_prediction_json(raw, task_id="t011")
    assert parsed.reasoning_steps[0].step_id == 1


def test_parse_model_prediction_json_rejects_non_numeric_reasoning_step_id() -> None:
    raw = """
    {
      "answer": "test",
      "events": ["A", "B"],
      "relations": [],
      "reasoning_steps": [
        {
          "step_id": "first",
          "text": "A before B",
          "supports": [["A", "B", "BEFORE"]]
        }
      ]
    }
    """

    with pytest.raises(PredictionParseError, match="must include integer 'step_id'"):
        parse_model_prediction_json(raw, task_id="t011b")


def test_parse_model_prediction_json_rejects_reasoning_step_without_text_string() -> None:
    raw = """
    {
      "answer": "test",
      "events": ["A", "B"],
      "relations": [],
      "reasoning_steps": [
        {
          "step_id": 1,
          "text": 99,
          "supports": []
        }
      ]
    }
    """

    with pytest.raises(PredictionParseError, match="must include string 'text'"):
        parse_model_prediction_json(raw, task_id="t012")


def test_parse_model_prediction_json_rejects_invalid_support_edge() -> None:
    raw = """
    {
      "answer": "test",
      "events": ["A", "B"],
      "relations": [],
      "reasoning_steps": [
        {
          "step_id": 1,
          "text": "A before B",
          "supports": [["A", "B", "DURING"]]
        }
      ]
    }
    """

    with pytest.raises(PredictionParseError, match="Invalid edge in 'supports'") as exc_info:
        parse_model_prediction_json(raw, task_id="t013")
    assert exc_info.value.category == "invalid_edge_support"


def test_parse_model_prediction_json_repairs_missing_comma_once() -> None:
    raw = """
    {
      "answer": "A happened before B."
      "events": ["A", "B"],
      "relations": [["A", "B", "BEFORE"]],
      "reasoning_steps": []
    }
    """

    parsed = parse_model_prediction_json(raw, task_id="t013b")

    assert parsed.answer == "A happened before B."
    assert parsed.pred_edges == [("A", "B", "BEFORE")]
    assert parsed.json_repaired is True


def test_parse_model_prediction_json_rejects_out_of_range_answer_confidence() -> None:
    raw = """
    {
      "answer": "test",
      "answer_confidence": 1.2,
      "events": ["A", "B"],
      "relations": []
    }
    """

    with pytest.raises(PredictionParseError, match="'answer_confidence' must be in \\[0.0, 1.0\\]"):
        parse_model_prediction_json(raw, task_id="t014")


def test_parse_model_prediction_json_rejects_boolean_step_confidence() -> None:
    raw = """
    {
      "answer": "test",
      "events": ["A", "B"],
      "relations": [],
      "reasoning_steps": [
        {
          "step_id": 1,
          "text": "A before B",
          "supports": [],
          "confidence": true
        }
      ]
    }
    """

    with pytest.raises(PredictionParseError, match="'confidence' must be a number when present"):
        parse_model_prediction_json(raw, task_id="t015")
