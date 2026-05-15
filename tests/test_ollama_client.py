from __future__ import annotations

from unittest.mock import Mock, call, patch

import pytest
import requests

from src.ollama_client import OllamaClient, OllamaTransportError


# ---------------------------------------------------------------------------
# Retry handling
# ---------------------------------------------------------------------------


def test_generate_retries_timeout_then_succeeds() -> None:
    timeout = requests.exceptions.Timeout("read timed out")
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"response": "ok"}

    with patch(
        "src.ollama_client.requests.post", side_effect=[timeout, response]
    ) as post_mock:
        with patch("src.ollama_client.time.sleep") as sleep_mock:
            client = OllamaClient(timeout_s=180, max_retries=2, retry_backoff_s=3.0)
            result = client.generate("qwen3.5:9b", "prompt")

    assert result == "ok"
    assert post_mock.call_count == 2
    assert post_mock.call_args_list[0].kwargs["timeout"] == (15, 180)
    sleep_mock.assert_called_once_with(3.0)


def test_generate_raises_transport_timeout_after_exhaustion() -> None:
    timeout = requests.exceptions.Timeout("read timed out")

    with patch(
        "src.ollama_client.requests.post", side_effect=[timeout, timeout, timeout]
    ):
        with patch("src.ollama_client.time.sleep") as sleep_mock:
            client = OllamaClient(timeout_s=240, max_retries=3, retry_backoff_s=4.0)
            with pytest.raises(OllamaTransportError) as exc_info:
                client.generate("qwen3.5:9b", "prompt")

    assert exc_info.value.category == "transport_timeout"
    assert "3 attempt(s)" in str(exc_info.value)
    assert sleep_mock.call_args_list == [call(4.0), call(8.0)]


# ---------------------------------------------------------------------------
# Response decoding
# ---------------------------------------------------------------------------


def test_generate_retries_invalid_json_response() -> None:
    bad_response = Mock()
    bad_response.raise_for_status.return_value = None
    bad_response.json.side_effect = ValueError("bad json")

    good_response = Mock()
    good_response.raise_for_status.return_value = None
    good_response.json.return_value = {"response": "recovered"}

    with patch(
        "src.ollama_client.requests.post", side_effect=[bad_response, good_response]
    ):
        with patch("src.ollama_client.time.sleep") as sleep_mock:
            client = OllamaClient(timeout_s=180, max_retries=2, retry_backoff_s=2.5)
            result = client.generate("qwen3.5:9b", "prompt")

    assert result == "recovered"
    sleep_mock.assert_called_once_with(2.5)
