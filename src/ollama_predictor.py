from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
import json

from src.ollama_client import OllamaClient, _extract_first_json_object

Edge = Tuple[str, str, str]  # (eventA, eventB, relation)

PROMPT_TEMPLATE = """You extract temporal relations between events.

Question:
{question}

Events (use these exact strings only):
{events_block}

Return ONLY JSON in this exact schema (no markdown):
{{
  "edges": [
    ["<eventA>", "<eventB>", "BEFORE"]
  ]
}}

Rules:
- Use only the event strings exactly as given in Events.
- Only output relation "BEFORE".
- If unsure, return {{"edges": []}}.
- Do not infer ordering unless explicitly or logically entailed.
"""

@dataclass
class OllamaPredictor:
    model: str
    client: OllamaClient
    temperature: float = 0.0
    seed: Optional[int] = 42

    def predict_edges(self, task: Dict[str, Any]) -> List[Edge]:
        events_block = "\n".join([f"- {e}" for e in task["events"]])
        prompt = PROMPT_TEMPLATE.format(question=task["question"], events_block=events_block)

        raw = self.client.generate(self.model, prompt, temperature=self.temperature, seed=self.seed)
        obj = json.loads(_extract_first_json_object(raw))

        edges: List[Edge] = []
        for triple in obj.get("edges", []):
            if isinstance(triple, list) and len(triple) == 3:
                a, b, rel = triple
                edges.append((str(a), str(b), str(rel)))
        return edges

    def metadata(self) -> Dict[str, Any]:
        return {
            "provider": "ollama",
            "model": self.model,
            "base_url": self.client.base_url,
            "temperature": self.temperature,
            "seed": self.seed,
            "tags_snapshot": self.client.tags_snapshot(),
        }