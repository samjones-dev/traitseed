"""T2 — fixed-seed steering probe. See probes/DESIGN.md.

Generate:
    uv run python -m probes.t2_steering generate [--draws 10] [--reps 6]
Analyze:
    uv run python -m probes.t2_steering analyze
"""

from __future__ import annotations

import argparse
import itertools
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from random import Random

import numpy as np

from ablation.llm import generate
from ablation.traits import draw_traits
from traitseed.tarot import draw_three

from .common import (
    BudgetExhausted,
    append_jsonl,
    check_budget_floor,
    embed_texts,
    read_jsonl,
    refuse_existing,
)
from .fictional import draw_fictional

logger = logging.getLogger(__name__)

TEMPERATURE = 1.2
TOP_P = 0.95
DEFAULT_OUT = Path("probes/runs/t2")
CONDITIONS = ("tarot", "fictional", "traits")

PROMPT = """Create a character study of one fictional person — 150-250 words of flowing prose describing their worldview, what they care about most, and their blind spot.

Use these three {kind} to shape them:

1. Worldview/disposition: {s1}
2. Primary concern/focus: {s2}
3. Blind spot/shadow: {s3}

Write the character study directly, without preamble."""

KIND = {"tarot": "tarot cards", "fictional": "cards", "traits": "traits"}


def seed_material(condition: str, rng: Random) -> list[str]:
    if condition == "tarot":
        return draw_three(rng=rng).to_list()
    if condition == "fictional":
        return draw_fictional(rng=rng).to_list()
    if condition == "traits":
        return draw_traits(rng).to_list()
    raise ValueError(condition)


def cmd_generate(args: argparse.Namespace) -> None:
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    paths = {c: out / f"{c}.jsonl" for c in CONDITIONS}

    done_keys: set[tuple] = set()
    if args.resume:
        for path in paths.values():
            if path.exists():
                done_keys |= {
                    (r["condition"], r["draw"], r["rep"]) for r in read_jsonl(path)
                }
        logger.info("Resume: %d records already on disk", len(done_keys))
    else:
        refuse_existing(list(paths.values()))

    draws = {
        c: [
            seed_material(c, Random(f"{args.seed}:{c}:{d}"))
            for d in range(args.draws)
        ]
        for c in CONDITIONS
    }
    all_jobs = [
        (c, d, rep)
        for c in CONDITIONS
        for d in range(args.draws)
        for rep in range(args.reps)
    ]
    jobs = [j for j in all_jobs if j not in done_keys]
    manifest = {
        "probe": "t2_steering",
        "model": args.model,
        "temperature": args.temperature,
        "top_p": TOP_P,
        "master_seed": args.seed,
        "draws_per_condition": args.draws,
        "reps_per_draw": args.reps,
        "prompt": PROMPT,
        "draws": draws,
        "calls": len(all_jobs),
        "max_tokens": args.max_tokens,
    }
    if not (args.resume and (out / "manifest.json").exists()):
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    logger.info("T2: %d calls (%d workers)", len(jobs), args.workers)

    def one(condition: str, d: int, rep: int) -> dict:
        s = draws[condition][d]
        prompt = PROMPT.format(kind=KIND[condition], s1=s[0], s2=s[1], s3=s[2])
        raw = generate(
            prompt,
            model=args.model,
            temperature=args.temperature,
            top_p=TOP_P,
            max_tokens=args.max_tokens,
        )
        return {
            "condition": condition,
            "draw": d,
            "rep": rep,
            "seed_material": s,
            "raw": raw,
        }

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(one, *job) for job in jobs]
        for future in as_completed(futures):
            record = future.result()
            append_jsonl(paths[record["condition"]], record)
            done += 1
            if done % 20 == 0 or done == len(jobs):
                logger.info("%d/%d done", done, len(jobs))
            if done % 25 == 0:
                try:
                    check_budget_floor(args.budget_floor)
                except BudgetExhausted as e:
                    pool.shutdown(wait=False, cancel_futures=True)
                    raise SystemExit(str(e)) from e


def analyze_run(out: Path) -> dict:
    """Compute T2 metrics for a run directory; writes analysis.json."""
    results = {}
    for condition in CONDITIONS:
        records = read_jsonl(out / f"{condition}.jsonl")
        emb = embed_texts([r["raw"] for r in records])
        dist = 1 - emb @ emb.T
        draws = sorted({r["draw"] for r in records})
        idx = {d: [i for i, r in enumerate(records) if r["draw"] == d] for d in draws}

        within = []
        for d in draws:
            block = dist[np.ix_(idx[d], idx[d])]
            within.extend(block[np.triu_indices(len(idx[d]), k=1)].tolist())
        across = []
        for a, b in itertools.combinations(draws, 2):
            across.extend(dist[np.ix_(idx[a], idx[b])].flatten().tolist())

        results[condition] = {
            "n": len(records),
            "within_draw_distance": float(np.mean(within)),
            "across_draw_distance": float(np.mean(across)),
            "steering_ratio": float(np.mean(across) / np.mean(within)),
        }

    (out / "analysis.json").write_text(json.dumps(results, indent=2) + "\n")
    return results


def cmd_analyze(args: argparse.Namespace) -> None:
    results = analyze_run(args.out)
    print(f"{'condition':<12}{'within':>9}{'across':>9}{'ratio':>8}")
    for c, r in results.items():
        print(
            f"{c:<12}{r['within_draw_distance']:>9.3f}"
            f"{r['across_draw_distance']:>9.3f}{r['steering_ratio']:>8.2f}"
        )
    rule = results["tarot"]["steering_ratio"] > results["fictional"]["steering_ratio"]
    print(f"\nPre-registered rule (tarot ratio > fictional ratio): {'HOLDS' if rule else 'FAILS'}")
    print(f"Written: {args.out / 'analysis.json'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate")
    g.add_argument("--model", default="google/gemini-2.5-flash")
    g.add_argument(
        "--temperature",
        type=float,
        default=TEMPERATURE,
        help="Override for providers that cap below 1.2 (Anthropic max is 1.0)",
    )
    g.add_argument("--seed", type=int, default=42)
    g.add_argument("--draws", type=int, default=10)
    g.add_argument("--reps", type=int, default=6)
    g.add_argument("--workers", type=int, default=6)
    g.add_argument("--out", type=Path, default=DEFAULT_OUT)
    g.add_argument("--resume", action="store_true", help="Skip records already on disk")
    g.add_argument("--max-tokens", type=int, default=2048, help="Per-call cap incl. reasoning")
    g.add_argument("--budget-floor", type=float, default=10.0, help="Abort below this credit ($)")
    g.set_defaults(func=cmd_generate)

    a = sub.add_parser("analyze")
    a.add_argument("--out", type=Path, default=DEFAULT_OUT)
    a.set_defaults(func=cmd_analyze)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args.func(args)


if __name__ == "__main__":
    main()
