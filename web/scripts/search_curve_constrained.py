#!/usr/bin/env python3
"""Constrained curve search for ADR-0280 (the Manus review's first choice).

ADR-0280 §5 tuned mission completion directly and produced an INVERTED
per-encounter curve (g4 7.2% while g6 sat at 99.3%), which violates ADR-0229's
"per-encounter win rate must be monotonic non-increasing by grade". That attempt
did not constrain monotonicity, so the lever was never actually tested under the
invariant.

This searches the same 12 parameters (per-grade HP cap + damage bonus) with two
constraints enforced on every candidate:

  1. the HP caps stay monotonically non-decreasing (ADR-0229), and
  2. the measured per-encounter win rate stays monotonically non-increasing.

Objective: sum of |measured mission completion - target| across grades.

Every evaluation writes the candidate into `src/core/combat/ice_scaling.ts`,
runs `scripts/curve_probe.ts` (both metrics in one 1.4s pass) and restores or
keeps the curve. The final best curve is left in the source.

    python3 scripts/search_curve_constrained.py            # search + write
    python3 scripts/search_curve_constrained.py --dry-run   # search, restore
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCALING = ROOT / "src" / "core" / "combat" / "ice_scaling.ts"

TARGETS = {1: 100.0, 2: 95.0, 3: 80.0, 4: 50.0, 5: 25.0, 6: 10.0}

HP_RE = re.compile(r"const ENCOUNTER_HP_BY_GRADE: ReadonlyArray<number> = \[\n([^\]]*)\];")
DMG_RE = re.compile(r"const ENCOUNTER_DMG_BONUS_PCT_BY_GRADE: ReadonlyArray<number> = \[\n([^\]]*)\];")


def read_curve() -> tuple[list[int], list[int]]:
    text = SCALING.read_text()
    hp = [int(x) for x in re.findall(r"-?\d+", HP_RE.search(text).group(1))]
    dmg = [int(x) for x in re.findall(r"-?\d+", DMG_RE.search(text).group(1))]
    return hp, dmg


def write_curve(hp: list[int], dmg: list[int]) -> None:
    text = SCALING.read_text()
    text = HP_RE.sub(
        "const ENCOUNTER_HP_BY_GRADE: ReadonlyArray<number> = [\n  "
        + ", ".join(str(v) for v in hp)
        + ",\n];",
        text,
        count=1,
    )
    text = DMG_RE.sub(
        "const ENCOUNTER_DMG_BONUS_PCT_BY_GRADE: ReadonlyArray<number> = [\n  "
        + ", ".join(str(v) for v in dmg)
        + ",\n];",
        text,
        count=1,
    )
    SCALING.write_text(text)


def monotone_caps(hp: list[int]) -> list[int]:
    out = list(hp)
    for i in range(1, len(out)):
        if out[i] < out[i - 1]:
            out[i] = out[i - 1]
    return out


def evaluate(hp: list[int], dmg: list[int]) -> tuple[float, list[float], list[float]] | None:
    """Return (score, p, m) or None when a constraint is violated."""
    write_curve(hp, dmg)
    out = subprocess.run(
        ["npx", "tsx", "scripts/curve_probe.ts", "--csv", "--seeds", "8", "--runs", "40"],
        cwd=ROOT, capture_output=True, text=True, timeout=300,
    ).stdout
    p: dict[int, float] = {}
    m: dict[int, float] = {}
    for line in out.splitlines():
        parts = line.strip().split(",")
        if len(parts) != 4 or parts[0] == "grade":
            continue
        g = int(parts[0])
        p[g] = float(parts[2])
        m[g] = float(parts[3])
    if sorted(p) != [1, 2, 3, 4, 5, 6]:
        raise RuntimeError(f"probe did not report every grade:\n{out}")

    # Constraint (ADR-0229, pinned by tests/ice_scaling.test.ts): "the late
    # grades buy their contest from HP, not from damage" -- the damage bonus must
    # not rise from g4 to g5/g6. A search that uses the damage bonus as its main
    # knob will otherwise break it (g5 0 > g4 -20).
    if not (dmg[3] >= dmg[4] >= dmg[5]):
        return None

    # Constraint: per-encounter win rate monotonic non-increasing by grade.
    for g in range(2, 7):
        if p[g] > p[g - 1] + 0.05:  # 0.05 = probe noise allowance, ~2 runs
            return None

    score = sum(abs(m[g] - TARGETS[g]) for g in range(1, 7))
    return score, [p[g] for g in range(1, 7)], [m[g] for g in range(1, 7)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--passes", type=int, default=4)
    args = ap.parse_args()

    start_hp, start_dmg = read_curve()
    best_hp, best_dmg = list(start_hp), list(start_dmg)
    result = evaluate(best_hp, best_dmg)
    if result is None:
        print("starting curve violates the monotonicity constraint; aborting")
        return 1
    best_score, best_p, best_m = result
    print(f"start      score {best_score:6.1f}  p {best_p}  m {[round(v,1) for v in best_m]}")

    steps = {
        "hp": [10, 20, 35],
        "dmg": [20, 40, 80],
    }

    for p in range(args.passes):
        improved = False
        for i in range(12):
            is_hp = i < 6
            grid = steps["hp"] if is_hp else steps["dmg"]
            for delta in grid:
                for sign in (1, -1):
                    cand_hp = list(best_hp)
                    cand_dmg = list(best_dmg)
                    if is_hp:
                        cand_hp[i] = max(20, cand_hp[i] + sign * delta)
                        cand_hp = monotone_caps(cand_hp)
                    else:
                        cand_dmg[i - 6] = max(-90, min(500, cand_dmg[i - 6] + sign * delta))
                    res = evaluate(cand_hp, cand_dmg)
                    if res is None:
                        continue
                    score, ps, ms = res
                    if score < best_score - 0.5:
                        best_score, best_hp, best_dmg = score, cand_hp, cand_dmg
                        best_p, best_m = ps, ms
                        improved = True
        print(
            f"pass {p + 1}   score {best_score:6.1f}  hp {best_hp}  dmg {best_dmg}\n"
            f"           p {[round(v,1) for v in best_p]}  m {[round(v,1) for v in best_m]}"
        )
        if not improved:
            break

    if args.dry_run:
        write_curve(start_hp, start_dmg)
        print("dry-run: source restored")
    else:
        write_curve(best_hp, best_dmg)
        print("written to src/core/combat/ice_scaling.ts")
    return 0


if __name__ == "__main__":
    sys.exit(main())