"""T7L — lattice controls. See pre-registration in DESIGN.md.

Generates T2-protocol character studies seeded from persisted control
lattices (degraded / gpt41 / human), judges them with the same blind
pass as T4/T6, and ranks all six conditions per generator.

    uv run python -m probes.lattice_controls generate --model <gen> --out <dir>
    uv run python -m probes.lattice_controls judge --records <dir> --out <dir>
    uv run python -m probes.lattice_controls analyze --judged <dir>... --t46 <dir>...
"""

from __future__ import annotations

import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from random import Random

import numpy as np

from ablation.llm import generate

from .coherence import JUDGE_MODEL, JUDGE_PROMPT, JUDGE_TEMPERATURE, SCORE_KEYS, parse_scores
from .common import (
    BudgetExhausted,
    append_jsonl,
    check_budget_floor,
    embed_texts,
    read_jsonl,
    refuse_existing,
)
from .t2_steering import KIND, PROMPT, TEMPERATURE, TOP_P

logger = logging.getLogger(__name__)

LATTICE_DIR = Path("probes/lattices")
CONDITIONS = ("degraded", "lattice2", "human")
LATTICE_FILES = {"degraded": "degraded.json", "lattice2": "gpt41.json", "human": "human.json"}

INTENSITY_PROBABILITY = 0.3
INTENSITY_SUFFIX = {
    "dispositions": "taken to excess",
    "concerns": "to the point of obsession",
    "blind_spots": "severe",
}
DRAWS = 10
REPS = 6


def draw_from_lattice(lattice: dict, rng: Random) -> list[str]:
    """One item per position with intensity flags, mirroring traits.py."""
    out = []
    for position in ("dispositions", "concerns", "blind_spots"):
        item = rng.choice(lattice[position])
        if rng.random() < INTENSITY_PROBABILITY:
            item = f"{item} ({INTENSITY_SUFFIX[position]})"
        out.append(item)
    return out


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
    else:
        refuse_existing(list(paths.values()))

    lattices = {
        c: json.loads((LATTICE_DIR / f).read_text()) for c, f in LATTICE_FILES.items()
    }
    draws = {
        c: [
            draw_from_lattice(lattices[c], Random(f"{args.seed}:{c}:{d}"))
            for d in range(DRAWS)
        ]
        for c in CONDITIONS
    }
    all_jobs = [
        (c, d, rep) for c in CONDITIONS for d in range(DRAWS) for rep in range(REPS)
    ]
    jobs = [j for j in all_jobs if j not in done_keys]

    manifest = {
        "probe": "t7l_lattice_controls",
        "model": args.model,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "master_seed": args.seed,
        "max_tokens": args.max_tokens,
        "draws": draws,
        "calls": len(all_jobs),
    }
    if not (args.resume and (out / "manifest.json").exists()):
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    logger.info("T7L %s: %d calls", args.model, len(jobs))

    def one(condition: str, d: int, rep: int) -> dict:
        s = draws[condition][d]
        prompt = PROMPT.format(kind=KIND["traits"], s1=s[0], s2=s[1], s3=s[2])
        raw = generate(
            prompt,
            model=args.model,
            temperature=TEMPERATURE,
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

    finished = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(one, *job) for job in jobs]
        for future in as_completed(futures):
            record = future.result()
            append_jsonl(paths[record["condition"]], record)
            finished += 1
            if finished % 20 == 0 or finished == len(jobs):
                logger.info("%d/%d done", finished, len(jobs))
            if finished % 25 == 0:
                try:
                    check_budget_floor(args.budget_floor)
                except BudgetExhausted as e:
                    pool.shutdown(wait=False, cancel_futures=True)
                    raise SystemExit(str(e)) from e


def cmd_judge(args: argparse.Namespace) -> None:
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    path = out / "judged.jsonl"
    done = set()
    if args.resume and path.exists():
        done = {r["key"] for r in read_jsonl(path)}
    elif not args.resume:
        refuse_existing([path])

    generator = json.loads((args.records / "manifest.json").read_text())["model"]
    studies = []
    for condition in CONDITIONS:
        for r in read_jsonl(args.records / f"{condition}.jsonl"):
            key = f"{condition}:{r['draw']}:{r['rep']}"
            if key not in done:
                studies.append({**r, "key": key})
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "probe": "t7l_judge",
                "generator_model": generator,
                "judge_model": JUDGE_MODEL,
                "calls": len(studies) + len(done),
            },
            indent=2,
        )
        + "\n"
    )
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


def _condition_stats(rows: list[dict]) -> dict:
    emb = embed_texts([r["study"] for r in rows])
    dist = 1 - emb @ emb.T
    means = {k: float(np.mean([r["scores"][k] for r in rows])) for k in SCORE_KEYS}
    return {
        "n": len(rows),
        "t4_score": (means["coherence"] + means["plausibility"]) / 2,
        "t6_score": (
            means["blindspot_genuine"]
            + means["blindspot_specific"]
            + means["blindspot_integrated"]
        )
        / 3,
        "dispersion": float(dist[np.triu_indices(len(rows), k=1)].mean()),
    }


def cmd_analyze(args: argparse.Namespace) -> None:
    print(f"{'generator':<34}{'condition':<11}{'T4':>6}{'T6':>6}{'disp':>7}")
    r1 = r2 = 0
    n_models = 0
    for judged_dir, t46_dir in zip(args.judged, args.t46):
        records = [r for r in read_jsonl(judged_dir / "judged.jsonl") if r["scores"]]
        generator = records[0]["generator_model"]
        n_models += 1

        stats = {}
        for condition in CONDITIONS:
            rows = [r for r in records if r["condition"] == condition]
            stats[condition] = _condition_stats(rows)

        # Comparators from the T4/T6 pass (same generators, prompt, judge).
        t46 = json.loads((t46_dir / "analysis.json").read_text())
        for comparator in ("tarot", "traits", "none"):
            stats[comparator] = {
                "n": t46[comparator]["n"],
                "t4_score": t46[comparator]["t4_score"],
                "t6_score": t46[comparator]["t6_score"],
                "dispersion": t46[comparator]["dispersion"],
            }

        (judged_dir / "analysis.json").write_text(json.dumps(stats, indent=2) + "\n")
        for condition, s in sorted(
            stats.items(), key=lambda kv: -kv[1]["t4_score"]
        ):
            print(
                f"{generator:<34}{condition:<11}{s['t4_score']:>6.2f}"
                f"{s['t6_score']:>6.2f}{s['dispersion']:>7.3f}"
            )
        holds_r1 = stats["degraded"]["t4_score"] < stats["traits"]["t4_score"]
        holds_r2 = stats["lattice2"]["t4_score"] > stats["none"]["t4_score"]
        r1 += holds_r1
        r2 += holds_r2
        print(
            f"  -> R1 curation matters (degraded<traits): {'HOLDS' if holds_r1 else 'fails'}"
            f" | R2 author-robust (lattice2>none): {'HOLDS' if holds_r2 else 'fails'}"
        )
    print(f"\ntally: R1 {r1}/{n_models}, R2 {r2}/{n_models}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate")
    g.add_argument("--model", required=True)
    g.add_argument("--seed", type=int, default=42)
    g.add_argument("--out", type=Path, required=True)
    g.add_argument("--workers", type=int, default=6)
    g.add_argument("--resume", action="store_true")
    g.add_argument("--max-tokens", type=int, default=2048)
    g.add_argument("--budget-floor", type=float, default=10.0)
    g.set_defaults(func=cmd_generate)

    j = sub.add_parser("judge")
    j.add_argument("--records", type=Path, required=True)
    j.add_argument("--out", type=Path, required=True)
    j.add_argument("--workers", type=int, default=6)
    j.add_argument("--resume", action="store_true")
    j.add_argument("--budget-floor", type=float, default=10.0)
    j.set_defaults(func=cmd_judge)

    a = sub.add_parser("analyze")
    a.add_argument("--judged", type=Path, nargs="+", required=True)
    a.add_argument("--t46", type=Path, nargs="+", required=True, help="Matching t46-judged dirs for comparator rows")
    a.set_defaults(func=cmd_analyze)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args.func(args)


if __name__ == "__main__":
    main()
