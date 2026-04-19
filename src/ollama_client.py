from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import json
import time
import requests


class OllamaTransportError(RuntimeError):
    def __init__(self, message: str, *, category: str) -> None:
        super().__init__(message)
        self.category = category


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
    max_retries: int = 1
    retry_backoff_s: float = 2.0

    def generate(self, model: str, prompt: str, *, temperature: float = 0.0, seed: Optional[int] = 42) -> str:
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if seed is not None:
            payload["options"]["seed"] = seed
        last_error: Exception | None = None
        attempts = max(self.max_retries, 1)

        for attempt in range(1, attempts + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout_s,
                )
                response.raise_for_status()
                return (response.json().get("response") or "").strip()
            except requests.exceptions.Timeout as exc:
                last_error = exc
                if attempt == attempts:
                    raise OllamaTransportError(
                        f"Ollama request timed out after {attempts} attempt(s): {exc}",
                        category="transport_timeout",
                    ) from exc
            except requests.exceptions.RequestException as exc:
                last_error = exc
                if attempt == attempts:
                    raise OllamaTransportError(
                        f"Ollama transport request failed after {attempts} attempt(s): {exc}",
                        category="transport_error",
                    ) from exc

            if attempt < attempts:
                time.sleep(self.retry_backoff_s * attempt)

        raise OllamaTransportError(
            f"Ollama transport request failed after {attempts} attempt(s): {last_error}",
            category="transport_error",
        )

    def tags_snapshot(self) -> Dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:
            return {"error": "could_not_fetch_tags"}
