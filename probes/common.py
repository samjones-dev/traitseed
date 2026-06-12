"""Shared IO and embedding helpers for the probes."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import numpy as np

_write_lock = threading.Lock()


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with _write_lock:
        with path.open("a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def embed_texts(texts: list[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    return model.encode(texts, normalize_embeddings=True)


def credits_remaining() -> float:
    """Remaining OpenRouter account credit in dollars."""
    import os

    import httpx

    response = httpx.get(
        "https://openrouter.ai/api/v1/credits",
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()["data"]
    return float(data["total_credits"]) - float(data["total_usage"])


class BudgetExhausted(RuntimeError):
    pass


def check_budget_floor(floor: float) -> None:
    """Raise BudgetExhausted when account credit drops below the floor."""
    remaining = credits_remaining()
    if remaining < floor:
        raise BudgetExhausted(
            f"Credit ${remaining:.2f} below floor ${floor:.2f} — aborting cleanly"
        )


def refuse_existing(paths: list[Path]) -> None:
    existing = [p for p in paths if p.exists()]
    if existing:
        raise SystemExit(
            f"Refusing to append to existing files: {existing}. "
            "Remove them or use a different output directory."
        )
