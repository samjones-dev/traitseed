"""Re-parse failed records in a run from their persisted raw output.

Usage:
    uv run python -m ablation.reparse ablation/runs/<run_id>

Post-processing only: no API calls, raw text and attempt counts are
untouched. Applies the current parse_yaml_response to records whose
persona is null and rewrites the JSONL in place.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generate import parse_yaml_response


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()

    for path in sorted(args.run_dir.glob("*.jsonl")):
        records = [json.loads(line) for line in path.read_text().splitlines()]
        recovered = 0
        for record in records:
            if record["persona"] is None and record["raw"]:
                record["persona"] = parse_yaml_response(record["raw"])
                if record["persona"] is not None:
                    recovered += 1
        with path.open("w") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        parsed = sum(1 for r in records if r["persona"])
        print(f"{path.stem}: recovered {recovered}, now {parsed}/{len(records)} parsed")


if __name__ == "__main__":
    main()
