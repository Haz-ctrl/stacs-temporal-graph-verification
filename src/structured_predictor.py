from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.ollama_client import OllamaClient, _extract_first_json_object
from src.prediction_schema import ParsedPrediction, parse_model_prediction_json
from src.schemas import TemporalTask


STRUCTURED_PROMPT_TEMPLATE = """You are solving a temporal reasoning task.

Return ONLY valid JSON in this exact schema:
{{
  "answer": "string",
  "events": ["string"],
  "relations": [["Event A", "Event B", "BEFORE"]],
  "reasoning_steps": [
    {{
      "step_id": 1,
      "text": "string",
      "supports": [["Event A", "Event B", "BEFORE"]]
    }}
  ]
}}

Rules:
- Use only the provided event names exactly as written.
- Allowed relation labels are: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
- Do not include markdown fences.
- Do not include explanatory text outside the JSON.
- If uncertain, still return valid JSON.
- 'supports' must be a list when present.
- Keep reasoning_steps concise and grounded in the task.

Question:
{question}

Allowed events:
{events_block}
"""


@dataclass
class StructuredOllamaPredictor:
    model: str
    client: OllamaClient
    temperature: float = 0.0
    seed: Optional[int] = 42

    def build_prompt(self, task: TemporalTask) -> str:
        events_block = "\n".join(f"- {event}" for event in task.events)
        return STRUCTURED_PROMPT_TEMPLATE.format(
            question=task.question,
            events_block=events_block,
        )

    def predict(self, task: TemporalTask) -> ParsedPrediction:
        prompt = self.build_prompt(task)
        raw = self.client.generate(
            self.model,
            prompt,
            temperature=self.temperature,
            seed=self.seed,
        )
        json_text = _extract_first_json_object(raw)
        return parse_model_prediction_json(json_text, task_id=task.id)

    def metadata(self) -> Dict[str, Any]:
        return {
            "provider": "ollama",
            "model": self.model,
            "base_url": self.client.base_url,
            "temperature": self.temperature,
            "seed": self.seed,
            "tags_snapshot": self.client.tags_snapshot(),
            "prediction_mode": "structured_json",
        }