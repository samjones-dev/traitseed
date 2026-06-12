"""Minimal OpenRouter chat client with retries."""

from __future__ import annotations

import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


def generate(
    prompt: str,
    model: str,
    temperature: float,
    top_p: float,
    max_retries: int = 4,
    timeout: float = 120.0,
    max_tokens: int | None = None,
) -> str:
    """Send one chat completion and return the content string.

    Retries on transient HTTP errors with exponential backoff.
    Raises on exhausted retries or missing API key.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "top_p": top_p,
    }
    if max_tokens is not None:
        # Bounds spend per call. Reasoning models bill thinking tokens
        # as output; this cap includes them on OpenRouter.
        payload["max_tokens"] = max_tokens
    headers = {"Authorization": f"Bearer {api_key}"}

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = httpx.post(
                OPENROUTER_URL, json=payload, headers=headers, timeout=timeout
            )
            if response.status_code in RETRYABLE_STATUS:
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response,
                )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if not content:
                raise ValueError("Empty completion content")
            return content
        except (httpx.HTTPError, ValueError, KeyError) as e:
            last_error = e
            wait = 2**attempt
            logger.warning(
                "LLM call failed (attempt %d/%d): %s — retrying in %ds",
                attempt + 1,
                max_retries,
                e,
                wait,
            )
            time.sleep(wait)

    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_error}")
