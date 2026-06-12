"""Cross-model grids for T1/T2 probe runs.

Usage:
    uv run python -m probes.aggregate

Walks probes/runs/, computes any missing analysis.json (skipping
incomplete generations), and prints the per-model verdict grids.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import t1_expansion, t2_steering

RUNS = Path("probes/runs")


def load(run_dir: Path, probe) -> dict | None:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text())
    expected = manifest.get("calls")
    actual = sum(
        len(p.read_text().splitlines()) for p in run_dir.glob("*.jsonl")
    )
    if expected and actual < expected:
        print(f"  (skipping {run_dir.name}: {actual}/{expected} calls)")
        return None
    analysis_path = run_dir / "analysis.json"
    if analysis_path.exists():
        analysis = json.loads(analysis_path.read_text())
    else:
        analysis = probe.analyze_run(run_dir)
    return {"model": manifest["model"], "analysis": analysis, "manifest": manifest}


def main() -> None:
    t1_rows, t2_rows = [], []
    for run_dir in sorted(RUNS.iterdir()):
        if not run_dir.is_dir():
            continue
        name = run_dir.name
        if name == "t1" or name.startswith("t1-"):
            if (row := load(run_dir, t1_expansion)) is not None:
                t1_rows.append(row)
        elif name == "t2" or name.startswith("t2-"):
            if (row := load(run_dir, t2_steering)) is not None:
                t2_rows.append(row)

    print("\nT1 — expansion (rule: real > fictional on stability AND separation)")
    print(f"{'model':<42}{'r.stab':>8}{'f.stab':>8}{'r.sep':>8}{'f.sep':>8}  rule")
    t1_holds = 0
    for row in t1_rows:
        a = row["analysis"]
        holds = (
            a["real"]["stability"] > a["fictional"]["stability"]
            and a["real"]["separation"] > a["fictional"]["separation"]
        )
        t1_holds += holds
        print(
            f"{row['model']:<42}"
            f"{a['real']['stability']:>8.3f}{a['fictional']['stability']:>8.3f}"
            f"{a['real']['separation']:>8.3f}{a['fictional']['separation']:>8.3f}"
            f"  {'HOLDS' if holds else 'fails'}"
        )
    print(f"tally: {t1_holds}/{len(t1_rows)} hold")

    print("\nT2 — steering ratio (rule: tarot > fictional)")
    print(f"{'model':<42}{'tarot':>7}{'fict':>7}{'traits':>7}  rule   best")
    t2_holds = 0
    for row in t2_rows:
        a = row["analysis"]
        r = {c: a[c]["steering_ratio"] for c in ("tarot", "fictional", "traits")}
        holds = r["tarot"] > r["fictional"]
        t2_holds += holds
        best = max(r, key=r.get)
        temp = row["manifest"].get("temperature")
        note = f" (T={temp})" if temp != 1.2 else ""
        print(
            f"{row['model']:<42}"
            f"{r['tarot']:>7.2f}{r['fictional']:>7.2f}{r['traits']:>7.2f}"
            f"  {'HOLDS' if holds else 'fails'}  {best}{note}"
        )
    print(f"tally: {t2_holds}/{len(t2_rows)} hold")


if __name__ == "__main__":
    main()
