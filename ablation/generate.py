"""Run the ablation: generate persona panels under each condition.

Usage:
    uv run python -m ablation.generate --n 30 --seed 42

Every call is an independent context. Per-slot RNGs are derived from the
master seed, so the same seed reproduces the same draws regardless of
worker scheduling. Artefacts land in ablation/runs/<run_id>/.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from random import Random
from typing import Any

import yaml

from .conditions import CONDITIONS, build_prompt
from .llm import generate

logger = logging.getLogger(__name__)

# Held constant across conditions (see DESIGN.md).
TEMPERATURE = 1.2
TOP_P = 0.95
PARSE_ATTEMPTS = 3  # initial call + up to 2 retries on unparseable output

QUESTION = """How can we best prepare for integrating AI into the education system? What traps, pitfalls, and goldmines could we run into?

Consider the perspectives of students, teachers, administrators, policymakers, and technology providers. Address both near-term implementation challenges and longer-term systemic implications."""

QUESTION_ID = "ai_education_q1"

REQUIRED_FIELDS = ("name", "institution", "persona", "perspective")


def parse_yaml_response(content: str) -> dict[str, Any] | None:
    """Extract and parse the YAML block from a model response."""
    match = re.search(r"```ya?ml\s*(.*?)```", content, re.DOTALL)
    if match:
        yaml_content = match.group(1)
    else:
        # Unclosed fence: responses that hit the token cap lose the
        # closing ``` — strip the opening fence and parse to the end.
        unclosed = re.search(r"```ya?ml\s*(.*)", content, re.DOTALL)
        yaml_content = unclosed.group(1) if unclosed else content
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError:
        return None
    if isinstance(data, dict) and all(data.get(f) for f in REQUIRED_FIELDS):
        return data
    return None


def generate_one(
    condition: str, index: int, master_seed: int, model: str, max_retries: int
) -> dict[str, Any]:
    """Generate one persona record. Deterministic seed material per slot.

    Never raises: a call that exhausts its retries is recorded with an
    error so one bad slot cannot kill the run.
    """
    rng = Random(f"{master_seed}:{condition}:{index}")
    seeded = build_prompt(condition, QUESTION, rng)

    raw = ""
    persona = None
    attempts = 0
    error = None
    for attempts in range(1, PARSE_ATTEMPTS + 1):
        try:
            raw = generate(
                seeded.prompt,
                model=model,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                max_retries=max_retries,
            )
        except RuntimeError as e:
            error = str(e)
            logger.error("%s[%d]: %s", condition, index, e)
            break
        persona = parse_yaml_response(raw)
        if persona is not None:
            break
        logger.warning(
            "%s[%d]: unparseable output (attempt %d/%d)",
            condition,
            index,
            attempts,
            PARSE_ATTEMPTS,
        )

    return {
        "condition": condition,
        "index": index,
        "seed_material": seeded.seed_material,
        "attempts": attempts,
        "raw": raw,
        "persona": persona,
        "error": error,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=30, help="Personas per condition")
    parser.add_argument("--model", default="google/gemini-2.5-flash")
    parser.add_argument("--seed", type=int, default=42, help="Master RNG seed")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--max-retries", type=int, default=4, help="LLM retry budget")
    parser.add_argument("--conditions", nargs="+", default=list(CONDITIONS))
    parser.add_argument("--out", type=Path, default=Path("ablation/runs"))
    parser.add_argument("--run-id", default=None, help="Override run directory name")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    model_short = args.model.split("/")[-1]
    run_id = args.run_id or f"{model_short}-seed{args.seed}-n{args.n}"
    run_dir = args.out / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    existing = [p for c in args.conditions if (p := run_dir / f"{c}.jsonl").exists()]
    if existing:
        raise SystemExit(
            f"Refusing to append to existing run files: {existing}. "
            "Use a different --run-id or remove them first."
        )

    # Manifest first: provenance must exist even if the run dies partway.
    manifest = {
        "run_id": run_id,
        "model": args.model,
        "master_seed": args.seed,
        "n_per_condition": args.n,
        "conditions": list(args.conditions),
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "parse_attempts": PARSE_ATTEMPTS,
        "question_id": QUESTION_ID,
        "question": QUESTION,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    jobs = [(c, i) for c in args.conditions for i in range(args.n)]
    logger.info("Run %s: %d calls (%d workers)", run_id, len(jobs), args.workers)

    # Stream each record to disk as it completes so partial runs persist.
    write_lock = threading.Lock()
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(generate_one, c, i, args.seed, args.model, args.max_retries)
            for c, i in jobs
        ]
        for future in as_completed(futures):
            record = future.result()
            with write_lock:
                path = run_dir / f"{record['condition']}.jsonl"
                with path.open("a") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                done += 1
            logger.info(
                "%d/%d done: %s[%d]%s",
                done,
                len(jobs),
                record["condition"],
                record["index"],
                "" if record["persona"] else " (FAILED)",
            )

    for condition in args.conditions:
        rows = (run_dir / f"{condition}.jsonl").read_text().splitlines()
        parsed = sum(1 for row in rows if json.loads(row)["persona"])
        logger.info("%s: %d/%d parsed", condition, parsed, len(rows))


if __name__ == "__main__":
    main()
