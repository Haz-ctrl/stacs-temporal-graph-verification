from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import json
import requests

def _extract_first_json_object(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    if start == -1:
        raise ValueError(f"Could not find JSON object in model output:\n{text}")

    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
            continue
        if char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    raise ValueError(f"Could not find balanced JSON object in model output:\n{text}")


@dataclass
class OllamaClient:
    base_url: str = "http://localhost:11434"
    timeout_s: int = 120

    def generate(self, model: str, prompt: str, *, temperature: float = 0.0, seed: Optional[int] = 42) -> str:
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if seed is not None:
            payload["options"]["seed"] = seed

        r = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout_s)
        r.raise_for_status()
        return (r.json().get("response") or "").strip()

    def tags_snapshot(self) -> Dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:
            return {"error": "could_not_fetch_tags"}
