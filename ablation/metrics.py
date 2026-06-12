"""Diversity metrics for an ablation run.

Usage:
    uv run python -m ablation.metrics ablation/runs/<run_id>

Reads each condition's JSONL, computes the three metric families from
DESIGN.md, prints a comparison table, and writes metrics.json into the
run directory.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

# Honorifics and suffixes stripped before splitting names.
_NAME_NOISE = re.compile(
    r"\b(dr|prof|professor|mr|mrs|ms|mx|sir|dame|phd|ph\.d|md|ed\.d|edd|jr|sr|ii|iii)\b\.?",
    re.IGNORECASE,
)

_WORD = re.compile(r"[a-z']+")

_STOPWORDS = frozenset(
    """a an and are as at be but by for from has have he her his i if in is it its
    of on or she that the their them they this to was we what when which who will
    with would not no nor so than then there these those you your our us about
    into how can could may might must should also more most other some such only
    own same too very s t don just now""".split()
)


def load_condition(path: Path) -> list[dict[str, Any]]:
    records = [json.loads(line) for line in path.read_text().splitlines()]
    return [r for r in records if r.get("persona")]


def normalize_name(name: str) -> str:
    # Role suffixes ("Dr. Anya Sharma, Digital Ethicist") would otherwise
    # count as distinct people — keep only the segment before the comma.
    cleaned = name.split(",")[0]
    cleaned = _NAME_NOISE.sub(" ", cleaned)
    cleaned = re.sub(r"[^\w\s'-]", " ", cleaned)
    return " ".join(cleaned.casefold().split())


def name_metrics(records: list[dict[str, Any]]) -> dict[str, float]:
    names = [normalize_name(r["persona"]["name"]) for r in records]
    firsts = [n.split()[0] for n in names if n.split()]
    lasts = [n.split()[-1] for n in names if n.split()]
    institutions = [
        " ".join(str(r["persona"]["institution"]).casefold().split())
        for r in records
    ]
    n = len(records)
    return {
        "unique_full_names": len(set(names)) / n,
        "unique_first_names": len(set(firsts)) / n,
        "unique_surnames": len(set(lasts)) / n,
        "unique_institutions": len(set(institutions)) / n,
    }


def _persona_text(record: dict[str, Any]) -> str:
    p = record["persona"]
    return f"{p.get('persona', '')}\n{p.get('perspective', '')}"


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.casefold())


def lexical_metrics(records: list[dict[str, Any]]) -> dict[str, float]:
    token_lists = [_tokens(_persona_text(r)) for r in records]
    all_tokens = list(itertools.chain.from_iterable(token_lists))
    bigrams = list(zip(all_tokens, all_tokens[1:]))

    content_sets = [
        {t for t in toks if t not in _STOPWORDS} for toks in token_lists
    ]
    jaccard_distances = [
        1 - len(a & b) / len(a | b)
        for a, b in itertools.combinations(content_sets, 2)
        if a | b
    ]
    return {
        "distinct_1": len(set(all_tokens)) / len(all_tokens),
        "distinct_2": len(set(bigrams)) / len(bigrams),
        "mean_pairwise_jaccard_distance": float(np.mean(jaccard_distances)),
    }


def embedding_metrics(records: list[dict[str, Any]], model_name: str) -> dict[str, float]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    texts = [str(r["persona"].get("perspective", "")) for r in records]
    embeddings = model.encode(texts, normalize_embeddings=True)
    similarity = embeddings @ embeddings.T
    n = len(texts)
    upper = similarity[np.triu_indices(n, k=1)]
    return {
        "mean_pairwise_cosine_distance": float(np.mean(1 - upper)),
        "min_pairwise_cosine_distance": float(np.min(1 - upper)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--embedding-model", default="all-MiniLM-L6-v2")
    args = parser.parse_args()

    results: dict[str, Any] = {}
    for path in sorted(args.run_dir.glob("*.jsonl")):
        condition = path.stem
        records = load_condition(path)
        results[condition] = {
            "n_parsed": len(records),
            **name_metrics(records),
            **lexical_metrics(records),
            **embedding_metrics(records, args.embedding_model),
        }

    out = args.run_dir / "metrics.json"
    out.write_text(json.dumps(results, indent=2) + "\n")

    conditions = list(results)
    metrics = [k for k in next(iter(results.values())) ]
    width = max(len(m) for m in metrics) + 2
    print(f"{'metric':<{width}}" + "".join(f"{c:>12}" for c in conditions))
    for m in metrics:
        row = "".join(
            f"{results[c][m]:>12.3f}" if isinstance(results[c][m], float) else f"{results[c][m]:>12}"
            for c in conditions
        )
        print(f"{m:<{width}}" + row)
    print(f"\nWritten: {out}")


if __name__ == "__main__":
    main()
