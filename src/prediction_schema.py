from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from src.schemas import ParsedPrediction, ReasoningStep
from src.temporal_graph import Edge, _to_edge


class PredictionParseError(ValueError):
    """Raised when structured model output cannot be parsed safely."""

    def __init__(
        self,
        message: str,
        *,
        category: str = "schema_violation",
        raw_output: str | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.raw_output = raw_output


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


def _get_first_present(obj: Dict[str, Any], keys: List[str]) -> Any:
    for key in keys:
        if key in obj:
            return obj[key]
    return None


def _coerce_step_id(value: Any, *, index: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise PredictionParseError(
        f"reasoning step at index {index} must include integer 'step_id'."
    )


def _coerce_step_text(step_obj: Dict[str, Any], *, index: int) -> str:
    value = _get_first_present(step_obj, ["text", "description", "reasoning"])
    if not isinstance(value, str):
        raise PredictionParseError(
            f"reasoning step at index {index} must include string 'text'."
        )
    return value


def _parse_string_list(value: Any, *, field_name: str) -> List[str]:
    if not isinstance(value, list):
        raise PredictionParseError(f"'{field_name}' must be a list of strings.")
    if not all(isinstance(item, str) for item in value):
        raise PredictionParseError(f"'{field_name}' must be a list of strings.")
    return list(value)


def _parse_optional_confidence(value: Any, *, field_name: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise PredictionParseError(f"'{field_name}' must be a number when present.")
    confidence = float(value)
    if confidence < 0.0 or confidence > 1.0:
        raise PredictionParseError(f"'{field_name}' must be in [0.0, 1.0].")
    return confidence


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
                ,
                category="invalid_edge_support",
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

        step_id = _coerce_step_id(_get_first_present(step_obj, ["step_id", "step"]), index=idx)
        text = _coerce_step_text(step_obj, index=idx)
        supports = _parse_edge_list(
            _get_first_present(step_obj, ["supports", "support", "evidence"]) or [],
            field_name="supports",
        )

        steps.append(
            ReasoningStep(
                step_id=step_id,
                text=text,
                supports=supports,
                confidence=_parse_optional_confidence(
                    step_obj.get("confidence"),
                    field_name="confidence",
                ),
            )
        )

    return steps


def _repair_json_text(raw_text: str) -> str:
    repaired = raw_text
    repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)

    result_chars: List[str] = []
    in_string = False
    escape = False
    stack: List[str] = []
    previous_significant: str | None = None

    token_starters = set('"{[tfn-0123456789')
    value_enders = set('"}]0123456789')

    for char in repaired:
        if in_string:
            result_chars.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
                previous_significant = '"'
            continue

        if char.isspace():
            result_chars.append(char)
            continue

        if char == '"':
            if previous_significant in value_enders and previous_significant not in "{[,:":
                result_chars.append(",")
            result_chars.append(char)
            in_string = True
            continue

        if char in token_starters - {'"'}:
            if previous_significant in value_enders and previous_significant not in "{[,:":
                result_chars.append(",")
            result_chars.append(char)
            previous_significant = char
            if char == "{":
                stack.append("}")
            elif char == "[":
                stack.append("]")
            continue

        result_chars.append(char)
        if char == ":":
            previous_significant = ":"
        elif char == ",":
            previous_significant = ","
        elif char == "}" and stack and stack[-1] == "}":
            stack.pop()
            previous_significant = "}"
        elif char == "]" and stack and stack[-1] == "]":
            stack.pop()
            previous_significant = "]"
        else:
            previous_significant = char

    while stack:
        result_chars.append(stack.pop())

    return "".join(result_chars)


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
    repaired_successfully = False

    try:
        obj = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        repaired_text = _repair_json_text(raw_text)
        if repaired_text != raw_text:
            try:
                obj = json.loads(repaired_text)
                repaired_successfully = True
            except json.JSONDecodeError:
                raise PredictionParseError(
                    f"Invalid JSON: {exc.msg}",
                    category="invalid_json",
                ) from exc
        else:
            raise PredictionParseError(
                f"Invalid JSON: {exc.msg}",
                category="invalid_json",
            ) from exc

    top = _require_object(obj, context="Top-level model output")

    answer = _require_string_field(top, "answer")
    pred_events = _parse_string_list(top.get("events", []), field_name="events")
    pred_edges = _parse_edge_list(top.get("relations", []), field_name="relations")
    reasoning_steps = _parse_reasoning_steps(top.get("reasoning_steps", []))
    answer_confidence = _parse_optional_confidence(
        top.get("answer_confidence"),
        field_name="answer_confidence",
    )

    return ParsedPrediction(
        task_id=task_id,
        answer=answer,
        pred_events=pred_events,
        pred_edges=pred_edges,
        reasoning_steps=reasoning_steps,
        answer_confidence=answer_confidence,
        json_repaired=repaired_successfully,
        raw_output=raw_text,
    )
