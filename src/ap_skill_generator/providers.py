from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from .config import Settings
from .logging_utils import safe_exception_message

OFFLINE_MODEL_ID = "offline-default-stub"
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class LLMProvider(Protocol):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> tuple[dict, str]:
        """Return model JSON and model identifier."""

    def pop_token_usage(self) -> dict:
        """Return accumulated token usage for the current generation run."""


def offline_stub_response(*, user_prompt: str) -> tuple[dict, str]:
    """Deterministic JSON used when OPENAI_API_KEY is unset (local UI/tests without spend)."""
    if "Repair class:" in user_prompt:
        return (
            {
                "question": "[Offline test] What is the derivative of x^2 with respect to x?",
                "choices": ["A. x", "B. 2x", "C. 2", "D. x^2"],
            },
            OFFLINE_MODEL_ID,
        )
    if '"question": "...",' in user_prompt:
        if "Type: frq" in user_prompt:
            return (
                {
                    "question": (
                        "[Offline test] Explain how limits relate to continuity for a piecewise-defined function."
                    ),
                    "choices": [],
                },
                OFFLINE_MODEL_ID,
            )
        return (
            {
                "question": "What is the slope of y=2x+1?",
                "choices": ["A. 1", "B. 2", "C. -2", "D. 0"],
            },
            OFFLINE_MODEL_ID,
        )
    if '{"answer": "..."}' in user_prompt:
        if "Type: frq" in user_prompt:
            return (
                {"answer": "Apply limit laws to each piece and check agreement at boundary points."},
                OFFLINE_MODEL_ID,
            )
        return ({"answer": "B"}, OFFLINE_MODEL_ID)
    return (
        {
            "explanation": (
                "Slope is the coefficient of x in y=mx+b; here m=2, so the slope is 2 (choice B)."
            ),
        },
        OFFLINE_MODEL_ID,
    )


def _merge_usage(totals: dict, usage: dict) -> None:
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        totals[key] = totals.get(key, 0) + int(usage.get(key, 0) or 0)


@dataclass
class OpenAICompatibleProvider:
    settings: Settings
    _token_usage: dict = field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

    def reset_token_usage(self) -> None:
        self._token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def pop_token_usage(self) -> dict:
        usage = dict(self._token_usage)
        self.reset_token_usage()
        return usage

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> tuple[dict, str]:
        if not self.settings.openai_api_key.strip():
            return offline_stub_response(user_prompt=user_prompt)

        payload = {
            "model": self.settings.openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
        }
        url = f"{self.settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"}
        last_error: Exception | None = None
        attempts = max(1, self.settings.max_retries + 1)

        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=self.settings.timeout_seconds) as client:
                    response = client.post(url, headers=headers, json=payload)
                if response.status_code in _RETRYABLE_STATUS and attempt < attempts - 1:
                    time.sleep(min(2**attempt, 8))
                    continue
                response.raise_for_status()
                raw = response.json()
                usage = raw.get("usage") or {}
                _merge_usage(self._token_usage, usage)
                content = raw["choices"][0]["message"]["content"]
                model_id = raw.get("model", self.settings.openai_model)
                return json.loads(content), model_id
            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                if attempt < attempts - 1:
                    time.sleep(min(2**attempt, 8))
                    continue
                raise RuntimeError(safe_exception_message(exc)) from None

        if last_error:
            raise RuntimeError(safe_exception_message(last_error)) from None
        raise RuntimeError("LLM request failed without a captured error")
