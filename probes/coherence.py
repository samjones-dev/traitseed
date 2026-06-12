"""T4 (coherence x diversity) and T6 (blind-spot productivity).

See the pre-registrations in DESIGN.md. Reuses T2 character studies;
adds a fresh `none` cell per generator, then one blind judging pass
scoring five dimensions, analyzed two ways.

    uv run python -m probes.coherence none-cell --model <generator> --t2-dir <dir> --out <dir>
    uv run python -m probes.coherence judge --t2-dir <dir> --none-dir <dir> --out <dir>
    uv run python -m probes.coherence analyze --judged <dir> [<dir> ...]
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from ablation.llm import generate

from .common import (
    BudgetExhausted,
    append_jsonl,
    check_budget_floor,
    embed_texts,
    read_jsonl,
    refuse_existing,
)
from .t2_steering import PROMPT as T2_PROMPT

logger = logging.getLogger(__name__)

JUDGE_MODEL = "anthropic/claude-sonnet-4.6"
JUDGE_TEMPERATURE = 0.0
NONE_CELL_SIZE = 60
CONDITIONS = ("tarot", "fictional", "traits", "none")

NONE_PROMPT = T2_PROMPT.replace(
    """Use these three {kind} to shape them:

1. Worldview/disposition: {s1}
2. Primary concern/focus: {s2}
3. Blind spot/shadow: {s3}""",
    "Make the person distinctive.",
)

JUDGE_PROMPT = """Score this fictional character study on five dimensions, each 1-5.

coherence: do the traits, concerns, and behaviours form one psychologically consistent person (5) or contradictory fragments (1)?
plausibility: could you meet this person — a real, specific human (5) or generic/impossible (1)?
blindspot_genuine: does the character have a real flaw or blind spot (5) or a flattering pseudo-flaw or none (1)?
blindspot_specific: is the blind spot concrete and behavioural (5) or vague (1)?
blindspot_integrated: does the blind spot connect to the character's strengths and worldview, e.g. as their shadow side (5), or feel bolted on (1)?

Return ONLY a JSON object, no other text:
{"coherence": n, "plausibility": n, "blindspot_genuine": n, "blindspot_specific": n, "blindspot_integrated": n}

Character study:
---
{study}"""

SCORE_KEYS = (
    "coherence",
    "plausibility",
    "blindspot_genuine",
    "blindspot_specific",
    "blindspot_integrated",
)


def parse_scores(raw: str) -> dict | None:
    match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if all(isinstance(data.get(k), (int, float)) and 1 <= data[k] <= 5 for k in SCORE_KEYS):
        return {k: data[k] for k in SCORE_KEYS}
    return None


def cmd_none_cell(args: argparse.Namespace) -> None:
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    path = out / "none.jsonl"
    done = set()
    if args.resume and path.exists():
        done = {r["index"] for r in read_jsonl(path)}
    elif not args.resume:
        refuse_existing([path])

    t2_manifest = json.loads((args.t2_dir / "manifest.json").read_text())
    temperature = t2_manifest["temperature"]
    manifest = {
        "probe": "t4_none_cell",
        "model": args.model,
        "temperature": temperature,
        "top_p": t2_manifest["top_p"],
        "max_tokens": args.max_tokens,
        "prompt": NONE_PROMPT,
        "calls": NONE_CELL_SIZE,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    jobs = [i for i in range(NONE_CELL_SIZE) if i not in done]
    logger.info("none-cell %s: %d calls", args.model, len(jobs))

    def one(i: int) -> dict:
        raw = generate(
            NONE_PROMPT,
            model=args.model,
            temperature=temperature,
            top_p=t2_manifest["top_p"],
            max_tokens=args.max_tokens,
        )
        return {"condition": "none", "index": i, "seed_material": [], "raw": raw}

    finished = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(one, i) for i in jobs]
        for future in as_completed(futures):
            append_jsonl(path, future.result())
            finished += 1
            if finished % 25 == 0:
                try:
                    check_budget_floor(args.budget_floor)
                except BudgetExhausted as e:
                    pool.shutdown(wait=False, cancel_futures=True)
                    raise SystemExit(str(e)) from e
    logger.info("none-cell %s: %d/%d done", args.model, finished, len(jobs))


def collect_studies(t2_dir: Path, none_dir: Path) -> list[dict]:
    studies = []
    for condition in ("tarot", "fictional", "traits"):
        for r in read_jsonl(t2_dir / f"{condition}.jsonl"):
            studies.append(
                {
                    "condition": condition,
                    "key": f"{condition}:{r['draw']}:{r['rep']}",
                    "seed_material": r["seed_material"],
                    "reversed": any("(reversed)" in s for s in r["seed_material"]),
                    "raw": r["raw"],
                }
            )
    for r in read_jsonl(none_dir / "none.jsonl"):
        studies.append(
            {
                "condition": "none",
                "key": f"none:{r['index']}",
                "seed_material": [],
                "reversed": False,
                "raw": r["raw"],
            }
        )
    return studies


def cmd_judge(args: argparse.Namespace) -> None:
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    path = out / "judged.jsonl"
    done = set()
    if args.resume and path.exists():
        done = {r["key"] for r in read_jsonl(path)}
    elif not args.resume:
        refuse_existing([path])

    generator = json.loads((args.t2_dir / "manifest.json").read_text())["model"]
    studies = [s for s in collect_studies(args.t2_dir, args.none_dir) if s["key"] not in done]
    manifest = {
        "probe": "t4_t6_judge",
        "generator_model": generator,
        "judge_model": JUDGE_MODEL,
        "judge_temperature": JUDGE_TEMPERATURE,
        "judge_prompt": JUDGE_PROMPT,
        "calls": len(studies) + len(done),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    logger.info("judging %s: %d studies", generator, len(studies))

    def one(study: dict) -> dict:
        scores = None
        for _ in range(3):
            raw = generate(
                JUDGE_PROMPT.replace("{study}", study["raw"]),
                model=JUDGE_MODEL,
                temperature=JUDGE_TEMPERATURE,
                top_p=1.0,
                max_tokens=1024,
            )
            scores = parse_scores(raw)
            if scores:
                break
        return {
            "generator_model": generator,
            "condition": study["condition"],
            "key": study["key"],
            "reversed": study["reversed"],
            "seed_material": study["seed_material"],
            "study": study["raw"],
            "scores": scores,
        }

    finished = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(one, s) for s in studies]
        for future in as_completed(futures):
            append_jsonl(path, future.result())
            finished += 1
            if finished % 50 == 0 or finished == len(studies):
                logger.info("%d/%d judged", finished, len(studies))
            if finished % 25 == 0:
                try:
                    check_budget_floor(args.budget_floor)
                except BudgetExhausted as e:
                    pool.shutdown(wait=False, cancel_futures=True)
                    raise SystemExit(str(e)) from e


def leakage(records: list[dict]) -> float:
    """Fraction of seeded studies containing a content word from their seed."""
    seeded = [r for r in records if r["seed_material"]]
    if not seeded:
        return 0.0
    hits = 0
    for r in seeded:
        text = r["study"].casefold()
        tokens = {
            w
            for s in r["seed_material"]
            for w in re.findall(r"[a-z]+", s.casefold())
            if len(w) > 3 and w not in {"reversed", "taken", "excess", "point", "obsession", "severe"}
        }
        if any(t in text for t in tokens):
            hits += 1
    return hits / len(seeded)


def cmd_analyze(args: argparse.Namespace) -> None:
    all_results = {}
    for judged_dir in args.judged:
        records = [r for r in read_jsonl(judged_dir / "judged.jsonl") if r["scores"]]
        generator = records[0]["generator_model"]
        model_result = {"n_judged": len(records), "leakage": leakage(records)}

        emb_cache = {}
        for condition in CONDITIONS:
            rows = [r for r in records if r["condition"] == condition]
            if not rows:
                continue
            emb = embed_texts([r["study"] for r in rows])
            dist = 1 - emb @ emb.T
            dispersion = float(dist[np.triu_indices(len(rows), k=1)].mean())
            emb_cache[condition] = dispersion
            means = {
                k: float(np.mean([r["scores"][k] for r in rows])) for k in SCORE_KEYS
            }
            model_result[condition] = {
                "n": len(rows),
                **means,
                "t4_score": (means["coherence"] + means["plausibility"]) / 2,
                "t6_score": (
                    means["blindspot_genuine"]
                    + means["blindspot_specific"]
                    + means["blindspot_integrated"]
                )
                / 3,
                "dispersion": dispersion,
            }

        for condition in ("tarot", "fictional"):
            rows = [r for r in records if r["condition"] == condition]
            rev = [r for r in rows if r["reversed"]]
            upr = [r for r in rows if not r["reversed"]]
            if rev and upr:
                t6 = lambda rs: float(
                    np.mean(
                        [
                            (
                                r["scores"]["blindspot_genuine"]
                                + r["scores"]["blindspot_specific"]
                                + r["scores"]["blindspot_integrated"]
                            )
                            / 3
                            for r in rs
                        ]
                    )
                )
                model_result[f"{condition}_reversal_contrast"] = {
                    "reversed_t6": t6(rev),
                    "upright_t6": t6(upr),
                    "n_reversed": len(rev),
                }

        all_results[generator] = model_result
        (judged_dir / "analysis.json").write_text(
            json.dumps(model_result, indent=2) + "\n"
        )

    print(f"{'generator':<34}{'cond':<11}{'T4':>6}{'T6':>6}{'disp':>7}")
    t4_tally = t6_tally = 0
    for generator, res in all_results.items():
        for condition in CONDITIONS:
            if condition in res:
                c = res[condition]
                print(
                    f"{generator:<34}{condition:<11}{c['t4_score']:>6.2f}"
                    f"{c['t6_score']:>6.2f}{c['dispersion']:>7.3f}"
                )
        t4 = res["tarot"]["t4_score"] > res["traits"]["t4_score"]
        t6 = res["tarot"]["t6_score"] > res["none"]["t6_score"]
        t4_tally += t4
        t6_tally += t6
        print(
            f"  -> T4 (tarot>traits): {'HOLDS' if t4 else 'fails'} | "
            f"T6 (tarot>none): {'HOLDS' if t6 else 'fails'} | "
            f"leakage {res['leakage']:.0%}"
        )
    print(f"\ntally: T4 {t4_tally}/{len(all_results)}, T6 {t6_tally}/{len(all_results)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("none-cell")
    n.add_argument("--model", required=True)
    n.add_argument("--t2-dir", type=Path, required=True)
    n.add_argument("--out", type=Path, required=True)
    n.add_argument("--workers", type=int, default=6)
    n.add_argument("--resume", action="store_true")
    n.add_argument("--max-tokens", type=int, default=2048)
    n.add_argument("--budget-floor", type=float, default=10.0)
    n.set_defaults(func=cmd_none_cell)

    j = sub.add_parser("judge")
    j.add_argument("--t2-dir", type=Path, required=True)
    j.add_argument("--none-dir", type=Path, required=True)
    j.add_argument("--out", type=Path, required=True)
    j.add_argument("--workers", type=int, default=6)
    j.add_argument("--resume", action="store_true")
    j.add_argument("--budget-floor", type=float, default=10.0)
    j.set_defaults(func=cmd_judge)

    a = sub.add_parser("analyze")
    a.add_argument("--judged", type=Path, nargs="+", required=True)
    a.set_defaults(func=cmd_analyze)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args.func(args)


if __name__ == "__main__":
    main()
