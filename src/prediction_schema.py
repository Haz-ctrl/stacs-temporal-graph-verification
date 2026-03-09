from __future__ import annotations

import json
from typing import Any, Dict, List

from src.schemas import ParsedPrediction, ReasoningStep
from src.temporal_graph import Edge, _to_edge


class PredictionParseError(ValueError):
    """Raised when structured model output cannot be parsed safely."""


def _require_object(value: Any, *, context: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise PredictionParseError(f"{context} must be a JSON object.")
    return value


def _require_string_field(obj: Dict[str, Any], key: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str):
        raise PredictionParseError(
            f"Expected string field '{key}', got {type(value).__name__}."
        )
    return value


def _parse_string_list(value: Any, *, field_name: str) -> List[str]:
    if not isinstance(value, list):
        raise PredictionParseError(f"'{field_name}' must be a list of strings.")
    if not all(isinstance(item, str) for item in value):
        raise PredictionParseError(f"'{field_name}' must be a list of strings.")
    return list(value)


def _parse_edge_list(value: Any, *, field_name: str) -> List[Edge]:
    if not isinstance(value, list):
        raise PredictionParseError(f"'{field_name}' must be a list.")
    edges: List[Edge] = []
    for item in value:
        try:
            edges.append(_to_edge(item))
        except ValueError as exc:
            raise PredictionParseError(
                f"Invalid edge in '{field_name}': {item!r}. {exc}"
            ) from exc
    return edges


def _parse_reasoning_steps(value: Any) -> List[ReasoningStep]:
    if value is None:
        return []

    if not isinstance(value, list):
        raise PredictionParseError("'reasoning_steps' must be a list.")

    steps: List[ReasoningStep] = []
    for idx, item in enumerate(value):
        step_obj = _require_object(item, context=f"reasoning step at index {idx}")

        step_id = step_obj.get("step_id")
        if not isinstance(step_id, int):
            raise PredictionParseError(
                f"reasoning step at index {idx} must include integer 'step_id'."
            )

        text = _require_string_field(step_obj, "text")
        supports = _parse_edge_list(step_obj.get("supports", []), field_name="supports")

        steps.append(
            ReasoningStep(
                step_id=step_id,
                text=text,
                supports=supports,
            )
        )

    return steps


def parse_model_prediction_json(raw_text: str, *, task_id: str) -> ParsedPrediction:
    """
    Parse strict structured model output into a typed ParsedPrediction.

    Expected schema:
    {
      "answer": "string",
      "events": ["string"],
      "relations": [["Event A", "Event B", "BEFORE"]],
      "reasoning_steps": [
        {
          "step_id": 1,
          "text": "string",
          "supports": [["Event A", "Event B", "BEFORE"]]
        }
      ]
    }
    """
    try:
        obj = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise PredictionParseError(f"Invalid JSON: {exc.msg}") from exc

    top = _require_object(obj, context="Top-level model output")

    answer = _require_string_field(top, "answer")
    pred_events = _parse_string_list(top.get("events", []), field_name="events")
    pred_edges = _parse_edge_list(top.get("relations", []), field_name="relations")
    reasoning_steps = _parse_reasoning_steps(top.get("reasoning_steps", []))

    return ParsedPrediction(
        task_id=task_id,
        answer=answer,
        pred_events=pred_events,
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
        raw_output=raw_text,
    )