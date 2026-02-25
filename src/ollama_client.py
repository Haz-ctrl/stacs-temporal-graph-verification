from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import json
import re
import requests

def _extract_first_json_object(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError(f"Could not find JSON object in model output:\n{text}")
    return m.group(0)


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