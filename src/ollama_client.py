from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


DEFAULT_OLLAMA_TIMEOUT_S = 300
DEFAULT_OLLAMA_MAX_RETRIES = 4
DEFAULT_OLLAMA_RETRY_BACKOFF_S = 5.0
DEFAULT_OLLAMA_CONNECT_TIMEOUT_S = 15


class OllamaTransportError(RuntimeError):
    """Raised when Ollama cannot return a usable generation response."""

    def __init__(self, message: str, *, category: str) -> None:
        super().__init__(message)
        self.category = category


@dataclass
class OllamaClient:
    """Minimal retrying client for Ollama's `/api/generate` endpoint."""

    base_url: str = "http://localhost:11434"
    timeout_s: int = DEFAULT_OLLAMA_TIMEOUT_S
    max_retries: int = DEFAULT_OLLAMA_MAX_RETRIES
    retry_backoff_s: float = DEFAULT_OLLAMA_RETRY_BACKOFF_S

    def generate(
        self,
        model: str,
        prompt: str,
        *,
        temperature: float = 0.0,
        seed: Optional[int] = 42,
    ) -> str:
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if seed is not None:
            payload["options"]["seed"] = seed
        last_error: Exception | None = None
        attempts = max(int(self.max_retries), 1)

        for attempt in range(1, attempts + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=(DEFAULT_OLLAMA_CONNECT_TIMEOUT_S, self.timeout_s),
                )
                response.raise_for_status()
                try:
                    body = response.json()
                except ValueError as exc:
                    raise OllamaTransportError(
                        f"Ollama returned a non-JSON response on attempt {attempt}: {exc}",
                        category="transport_error",
                    ) from exc
                return (body.get("response") or "").strip()
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
            except OllamaTransportError as exc:
                last_error = exc
                if attempt == attempts:
                    raise

            if attempt < attempts:
                backoff_s = self.retry_backoff_s * (2 ** (attempt - 1))
                time.sleep(backoff_s)

        raise OllamaTransportError(
            f"Ollama transport request failed after {attempts} attempt(s): {last_error}",
            category="transport_error",
        )

    def tags_snapshot(self) -> Dict[str, Any]:
        try:
            r = requests.get(
                f"{self.base_url}/api/tags",
                timeout=(DEFAULT_OLLAMA_CONNECT_TIMEOUT_S, 10),
            )
            r.raise_for_status()
            return r.json()
        except (requests.exceptions.RequestException, ValueError):
            return {"error": "could_not_fetch_tags"}
