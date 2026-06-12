"""T1 — symbol expansion probe. See probes/DESIGN.md.

Generate:
    uv run python -m probes.t1_expansion generate [--cards N] [--k 8]
Analyze:
    uv run python -m probes.t1_expansion analyze
"""

from __future__ import annotations

import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from ablation.llm import generate
from traitseed.tarot import FULL_DECK, MAJOR_ARCANA

from .common import (
    BudgetExhausted,
    append_jsonl,
    check_budget_floor,
    embed_texts,
    read_jsonl,
    refuse_existing,
)
from .fictional import FICTIONAL_DECK, FICTIONAL_MAJORS

logger = logging.getLogger(__name__)

TEMPERATURE = 1.0
TOP_P = 0.95
DEFAULT_K = 8
DEFAULT_OUT = Path("probes/runs/t1")

PROMPT = (
    "In the symbolic deck this card belongs to, what worldview or "
    "disposition does the card '{card}' connote? Answer in 2-3 sentences."
)

DECKS = {"real": FULL_DECK, "fictional": FICTIONAL_DECK}
MAJORS = {"real": set(MAJOR_ARCANA), "fictional": set(FICTIONAL_MAJORS)}


def cmd_generate(args: argparse.Namespace) -> None:
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    paths = {deck: out / f"{deck}.jsonl" for deck in DECKS}

    done_keys: set[tuple] = set()
    if args.resume:
        for path in paths.values():
            if path.exists():
                done_keys |= {
                    (r["deck"], r["card"], r["k"]) for r in read_jsonl(path)
                }
        logger.info("Resume: %d records already on disk", len(done_keys))
    else:
        refuse_existing(list(paths.values()))

    all_jobs = [
        (deck, card, k)
        for deck, cards in DECKS.items()
        for card in (cards[: args.cards] if args.cards else cards)
        for k in range(args.k)
    ]
    jobs = [j for j in all_jobs if j not in done_keys]
    if not (args.resume and (out / "manifest.json").exists()):
        manifest = {
            "probe": "t1_expansion",
            "model": args.model,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "k": args.k,
            "cards_per_deck": args.cards or "all",
            "max_tokens": args.max_tokens,
            "prompt": PROMPT,
            "calls": len(all_jobs),
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    logger.info("T1: %d calls (%d workers)", len(jobs), args.workers)

    def one(deck: str, card: str, k: int) -> dict:
        raw = generate(
            PROMPT.format(card=card),
            model=args.model,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=args.max_tokens,
        )
        return {"deck": deck, "card": card, "k": k, "raw": raw}

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(one, *job) for job in jobs]
        for future in as_completed(futures):
            record = future.result()
            append_jsonl(paths[record["deck"]], record)
            done += 1
            if done % 50 == 0 or done == len(jobs):
                logger.info("%d/%d done", done, len(jobs))
            if done % 25 == 0:
                try:
                    check_budget_floor(args.budget_floor)
                except BudgetExhausted as e:
                    pool.shutdown(wait=False, cancel_futures=True)
                    raise SystemExit(str(e)) from e


def analyze_run(out: Path) -> dict:
    """Compute T1 metrics for a run directory; writes analysis.json."""
    results = {}
    for deck in DECKS:
        records = read_jsonl(out / f"{deck}.jsonl")
        cards = sorted({r["card"] for r in records})
        texts = [r["raw"] for r in records]
        emb = embed_texts(texts)
        card_idx = {c: [i for i, r in enumerate(records) if r["card"] == c] for c in cards}

        sim = emb @ emb.T
        per_card = {}
        for c in cards:
            idx = np.array(card_idx[c])
            within_block = sim[np.ix_(idx, idx)]
            within = within_block[np.triu_indices(len(idx), k=1)].mean()
            mask = np.ones(len(records), dtype=bool)
            mask[idx] = False
            cross = sim[np.ix_(idx, mask)].mean()
            per_card[c] = {
                "stability": float(within),
                "separation": float(within - cross),
                "major": c in MAJORS[deck],
            }

        stab = [v["stability"] for v in per_card.values()]
        sep = [v["separation"] for v in per_card.values()]
        results[deck] = {
            "n_cards": len(cards),
            "stability": float(np.mean(stab)),
            "separation": float(np.mean(sep)),
            "stability_majors": float(
                np.mean([v["stability"] for v in per_card.values() if v["major"]])
            ),
            "stability_minors": float(
                np.mean([v["stability"] for v in per_card.values() if not v["major"]])
            ),
            "per_card": per_card,
        }

    (out / "analysis.json").write_text(json.dumps(results, indent=2) + "\n")
    return results


def cmd_analyze(args: argparse.Namespace) -> None:
    results = analyze_run(args.out)
    print(f"{'deck':<11}{'stability':>11}{'separation':>12}{'stab(maj)':>11}{'stab(min)':>11}")
    for deck, r in results.items():
        print(
            f"{deck:<11}{r['stability']:>11.3f}{r['separation']:>12.3f}"
            f"{r['stability_majors']:>11.3f}{r['stability_minors']:>11.3f}"
        )
    rule = (
        results["real"]["stability"] > results["fictional"]["stability"]
        and results["real"]["separation"] > results["fictional"]["separation"]
    )
    print(f"\nPre-registered rule (real > fictional on both): {'HOLDS' if rule else 'FAILS'}")
    print(f"Written: {args.out / 'analysis.json'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate")
    g.add_argument("--model", default="google/gemini-2.5-flash")
    g.add_argument("--k", type=int, default=DEFAULT_K)
    g.add_argument("--cards", type=int, default=None, help="Limit cards per deck (smoke test)")
    g.add_argument("--workers", type=int, default=6)
    g.add_argument("--out", type=Path, default=DEFAULT_OUT)
    g.add_argument("--resume", action="store_true", help="Skip records already on disk")
    g.add_argument("--max-tokens", type=int, default=1024, help="Per-call cap incl. reasoning")
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
