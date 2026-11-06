#!/usr/bin/env python3
"""Offline curve tuner for ADR-0280.

Searches the per-grade ICE curve (`ENCOUNTER_HP_BY_GRADE` +
`ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` in `src/core/combat/ice_scaling.ts`) to hit
`GRADE_TARGETS` in `scripts/mission_survival.ts`, then writes the best schedule
back into the source.

Why offline rather than a flag in the game: the tuned numbers get committed, and
production code should carry the values, not a tuning seam. This script edits the
source between probes, which keeps the shipped module free of override hooks.

Grades are independent (a mission has one grade), so each grade is searched on
its own. The HP schedule must stay monotonic non-decreasing (ADR-0229), so the
search holds that as a hard constraint.

    python3 scripts/tune_curve.py            # search + write
    python3 scripts/tune_curve.py --dry-run  # search, report, do not write

!! CHECK THE OUTPUT BEFORE COMMITTING IT. This optimises mission survival
!! directly, and it will happily reach the mission targets by INVERTING the
!! per-encounter curve (measured: grade 4 at 7.2% per encounter while grade 6
!! sits at 99.3%). That breaks ADR-0229's monotonic non-increasing invariant
!! and reads as nonsense in play -- grade 4 ICE hitting harder than grade 6.
!! Always run `npm run balance` afterwards and confirm the per-grade rates are
!! still monotonic non-increasing. ADR-0280 records the full analysis.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCALING = ROOT / "src" / "core" / "combat" / "ice_scaling.ts"
SURVIVAL = ROOT / "scripts" / "mission_survival.ts"

TARGETS = {1: 100.0, 2: 95.0, 3: 80.0, 4: 50.0, 5: 25.0, 6: 10.0}

# Fixed input, not a search axis (see the comment in main()).
HP_SCHEDULE = [40, 45, 55, 90, 95, 110]
BONUS_GRID = [-75, -50, -25, 0, 20, 40, 60, 90, 120, 150, 180, 220, 260, 320, 400, 500]

HP_RE = re.compile(r"const ENCOUNTER_HP_BY_GRADE: ReadonlyArray<number> = \[\n([^\]]*)\];")
DMG_RE = re.compile(
    r"const ENCOUNTER_DMG_BONUS_PCT_BY_GRADE: ReadonlyArray<number> = \[\n([^\]]*)\];"
)


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


def measure(grade: int, seeds: int) -> float:
    """Mission completion rate for one grade."""
    out = subprocess.run(
        ["npx", "tsx", "scripts/mission_survival.ts", "--grade", str(grade),
         "--seeds", str(seeds)],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    ).stdout
    for line in out.splitlines():
        m = re.match(r"\s*(\d)\s+\d+\s+\d+\s+\d+\s+([\d.]+)%", line)
        if m and int(m.group(1)) == grade:
            return float(m.group(2))
    raise RuntimeError(f"could not parse grade {grade} from:\n{out}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--tol", type=float, default=5.0)
    args = ap.parse_args()

    hp, dmg = read_curve()
    print(f"start  hp={hp} dmg={dmg}")

    # The HP schedule is an input, not a search axis. In the ADR-0280 model
    # (one enemy phase per card) a fight's length is what decides whether the
    # runner survives it: a long fight means many hits. So HP stays low and
    # gently rising, and difficulty is carried by ICE damage. Letting the
    # search pick the cap instead makes it climb (a high cap needs a smaller
    # damage bonus to hit a target), which then blocks the grades above it.
    best_hp = list(HP_SCHEDULE)
    best_dmg = list(dmg)
    for grade in range(1, 7):
        idx = grade - 1
        target = TARGETS[grade]

        def probe(bonus: int) -> float:
            trial = list(best_dmg)
            trial[idx] = bonus
            write_curve(best_hp, trial)
            return measure(grade, args.seeds)

        best = (1e9, best_dmg[idx], 0)
        for bonus in BONUS_GRID:
            rate = probe(bonus)
            err = abs(rate - target)
            if err < best[0]:
                best = (err, bonus, rate)
        # Refine around the winner.
        for bonus in range(best[1] - 20, best[1] + 21, 5):
            if bonus in BONUS_GRID:
                continue
            rate = probe(bonus)
            err = abs(rate - target)
            if err < best[0]:
                best = (err, bonus, rate)
        best_dmg[idx] = best[1]
        write_curve(best_hp, best_dmg)
        flag = "" if best[0] <= args.tol else "  <-- SATURATED"
        print(
            f"g{grade}: target {target:>5.1f}  cap {best_hp[idx]:>3}  dmg {best[1]:>4}  "
            f"got {best[2]:>5.1f}%  err {best[0]:.1f}pp{flag}"
        )

    # Restore monotonic HP (ADR-0229) in case a later grade searched below an
    # earlier one.
    for i in range(1, 6):
        if best_hp[i] < best_hp[i - 1]:
            best_hp[i] = best_hp[i - 1]
    if args.dry_run:
        write_curve(hp, dmg)
        print(f"dry-run (source restored)  hp={best_hp} dmg={best_dmg}")
    else:
        write_curve(best_hp, best_dmg)
        print(f"written  hp={best_hp} dmg={best_dmg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
