from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from src.ollama_client import OllamaClient
from src.schemas import TemporalTask
from src.structured_predictor import StructuredOllamaPredictor


@dataclass
class FakeOllamaClient:
    base_url: str = "http://localhost:11434"

    def generate(self, model: str, prompt: str, temperature: float, seed: int | None) -> str:
        return """
        {
          "answer": "A happened before B.",
          "events": ["A", "B"],
          "relations": [["A", "B", "BEFORE"]],
          "reasoning_steps": [
            {
              "step_id": 1,
              "text": "The task states A happened before B.",
              "supports": [["A", "B", "BEFORE"]]
            }
          ]
        }
        """

    def tags_snapshot(self) -> list[str]:
        return ["fake-model:latest"]


def test_build_prompt_includes_question_and_events() -> None:
    task = TemporalTask(
        id="t001",
        question="Did A happen before B?",
        events=["A", "B"],
        gold_relations=[("A", "B", "BEFORE")],
        category="demo",
        expected_valid=True,
        expected_consistent=True,
    )

    predictor = StructuredOllamaPredictor(
        model="fake-model",
        client=cast(OllamaClient, FakeOllamaClient()),
    )

    prompt = predictor.build_prompt(task)

    assert "Did A happen before B?" in prompt
    assert "- A" in prompt
    assert "- B" in prompt
    assert "Return ONLY valid JSON" in prompt


def test_predict_returns_parsed_prediction() -> None:
    task = TemporalTask(
        id="t001",
        question="Did A happen before B?",
        events=["A", "B"],
        gold_relations=[("A", "B", "BEFORE")],
        category="demo",
        expected_valid=True,
        expected_consistent=True,
    )

    predictor = StructuredOllamaPredictor(
        model="fake-model",
        client=cast(OllamaClient, FakeOllamaClient()),
    )

    prediction = predictor.predict(task)

    assert prediction.task_id == "t001"
    assert prediction.answer == "A happened before B."
    assert prediction.pred_events == ["A", "B"]
    assert prediction.pred_edges == [("A", "B", "BEFORE")]
    assert len(prediction.reasoning_steps) == 1
    assert prediction.reasoning_steps[0].step_id == 1
    assert prediction.raw_output is not None
    assert '"answer": "A happened before B."' in prediction.raw_output
