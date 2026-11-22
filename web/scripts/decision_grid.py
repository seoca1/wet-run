#!/usr/bin/env python3
"""Decision grid for ADR-0339 (g4 difficulty) x ADR-0341 (gear vs ICE) — 2026-11-22.

The two ADRs each list options, but their levers write to the SAME two arrays
(`ENCOUNTER_HP_BY_GRADE`, `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`) and every cell moves
the recorded goldens. Deciding them separately means re-recording `balance.golden`
and `gear.golden` twice, so this measures the cells first and lets the owner pick
one row instead of guessing twice.

Cells:

    g4 auto-attack bonus  (ADR-0339 lever)   x   g5/g6 encounter HP cap  (ADR-0341 lever)
    {0, 10, 20}                                    {95 (current), 115, 135}

`g4` is tuned by the damage bonus and `g5/g6` by the HP cap on purpose: that is
what each ADR argues is the only reachable lever, and it keeps the two effects
separable (a contract's grade is its start mission's grade).

Per cell it measures the three metrics the pass criteria need:

    1. campaign per-grade completion  -> is g3 >= g4? (ADR-0229 monotonicity)
    2. gear T6 per-grade completion   -> is g5/g6 inside ADR-0328's 65/70 band?
    3. gear T1<T2<T4<T6 at g5/g6      -> does better gear still mean more power?
    4. bare mission curve             -> how far does the recorded baseline move?

Convention follows `tune_curve.py` / `search_curve_constrained.py`: the numbers get
committed, so production code carries the values and the probe carries no override
hook. This script edits the source between cells and restores it in a `finally`,
and it refuses to start if the file already has uncommitted edits (so the restore
cannot clobber someone else's work).

    python3 scripts/decision_grid.py --dry-run     # report the plan, touch nothing
    python3 scripts/decision_grid.py              # run the grid, restore, print the table
    python3 scripts/decision_grid.py --seeds 64 --campaign-seeds 64   # final pass
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCALING = ROOT / "src" / "core" / "combat" / "ice_scaling.ts"
GRADE_NAMES = (1, 2, 3, 4, 5, 6)

HP_RE = re.compile(r"const ENCOUNTER_HP_BY_GRADE: ReadonlyArray<number> = \[([^\]]*)\];")
DMG_RE = re.compile(
    r"const ENCOUNTER_DMG_BONUS_PCT_BY_GRADE: ReadonlyArray<number> = \[([^\]]*)\];"
)

# ADR-0339 argued g4's auto-attack bonus is the lever. The first pass (g4 dmg
# 0/10/20 with g4 HP untouched) moved campaign g4 only 64.3 -> 65.0 -> 60.0 while
# g3 stayed at 50.0, i.e. the bonus is too coarse to close the inversion on its
# own. It stays here as a check, not as the main axis.
G4_DMG_AXIS = (0,)
# ADR-0341's lever, and the one ADR-0339 says is bounded by monotonicity: the
# encounter HP cap for the late grades. Applied to (g4, g5, g6) so both ADRs move
# together. `BOSS_HP_BY_GRADE` is a separate table (ADR-0290) and is NOT touched,
# so the climax keeps its budget.
CAP_PROFILES: tuple[tuple[str, tuple[int, int, int]], ...] = (
    ("P0 current", (95, 95, 95)),
    ("P2 g56=135", (115, 135, 135)),
    ("R g4=125", (125, 135, 135)),
    ("R g56=140", (125, 140, 140)),
    ("R g4=130", (130, 135, 135)),
    ("P3 +40", (135, 135, 135)),
)


def read_array(regex: re.Pattern[str]) -> list[int]:
    text = SCALING.read_text()
    match = regex.search(text)
    if match is None:
        sys.exit(f"cannot find the constant in {SCALING}")
    return [int(x) for x in re.findall(r"-?\d+", match.group(1))]


def write_arrays(hp: list[int], dmg: list[int]) -> None:
    text = SCALING.read_text()
    text = HP_RE.sub(
        "const ENCOUNTER_HP_BY_GRADE: ReadonlyArray<number> = ["
        + ", ".join(str(x) for x in hp)
        + "];",
        text,
    )
    text = DMG_RE.sub(
        "const ENCOUNTER_DMG_BONUS_PCT_BY_GRADE: ReadonlyArray<number> = ["
        + ", ".join(str(x) for x in dmg)
        + "];",
        text,
    )
    SCALING.write_text(text)


def run(args: list[str]) -> str:
    result = subprocess.run(
        args, cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout[-2000:])
        sys.stderr.write(result.stderr[-2000:])
        sys.exit(f"probe failed: {' '.join(args)}")
    return result.stdout


def parse_survival(out: str) -> dict[int, float]:
    """`mission_survival` per-grade table: `  4  10  40  21  52.5%  ...`."""
    rates: dict[int, float] = {}
    row = re.compile(r"^\s+(\d)\s+\d+\s+\d+\s+\d+\s+([\d.]+)%", re.MULTILINE)
    for grade, rate in row.findall(out):
        rates[int(grade)] = float(rate)
    if not rates:
        sys.exit("could not parse mission_survival output")
    return rates


def parse_campaign(out: str) -> dict[int, float]:
    """`by start grade (contract completion)` table."""
    block = out.split("by start grade (contract completion)")[-1]
    rates: dict[int, float] = {}
    row = re.compile(r"^\s+(\d)\s+\d+\s+\d+\s+([\d.]+)%", re.MULTILINE)
    for grade, rate in row.findall(block):
        rates[int(grade)] = float(rate)
    if not rates:
        sys.exit("could not parse campaign_survival output")
    return rates


def gear_mission() -> dict[str, list[float]]:
    data = json.loads(run(["npx", "tsx", "scripts/gear_curve_probe.ts", "--json"]))
    return {cell["set"]: cell["completionPct"] for cell in data["mission"]}


def gear_label(prefix: str, sets: dict[str, list[float]]) -> str:
    for name in sets:
        if name.startswith(prefix):
            return name
    sys.exit(f"gear set not found: {prefix}")


def fmt(values: list[float] | dict[int, float]) -> str:
    if isinstance(values, dict):
        values = [values[g] for g in GRADE_NAMES]
    return " ".join(f"{v:5.1f}" for v in values)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32, help="mission survival seeds")
    parser.add_argument("--campaign-seeds", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--csv", default="", help="write the cells to this CSV")
    parser.add_argument("--only", default="", help="run one cell by its label")
    args = parser.parse_args()

    original = SCALING.read_text()
    base_hp = read_array(HP_RE)
    base_dmg = read_array(DMG_RE)
    if len(base_hp) != 6 or len(base_dmg) != 6:
        sys.exit(f"expected 6 grades, got hp={base_hp} dmg={base_dmg}")

    dirty = subprocess.run(
        ["git", "diff", "--quiet", "--", str(SCALING)], cwd=ROOT, check=False
    )
    if dirty.returncode != 0:
        sys.exit(f"{SCALING} has uncommitted edits — commit or stash before a sweep")

    cells = list(itertools.product(G4_DMG_AXIS, CAP_PROFILES))
    if args.only:
        cells = [c for c in cells if c[1][0] == args.only]
        if not cells:
            sys.exit(f"no cell labelled {args.only!r}")
    print(
        f"decision grid — {len(cells)} cells x (survival {args.seeds} seeds + gear + "
        f"campaign {args.campaign_seeds} seeds)"
    )
    print(f"base hp={base_hp} dmg={base_dmg}")
    if args.dry_run:
        for dmg4, (label, caps) in cells:
            hp = [*base_hp[:3], *caps]
            dmg = [*base_dmg[:3], dmg4, *base_dmg[4:]]
            print(f"  g4 dmg {dmg4:+3d} · {label:18s} -> hp={hp} dmg={dmg}")
        return

    rows: list[dict[str, object]] = []
    try:
        for dmg4, (label, caps) in cells:
            hp = [*base_hp[:3], *caps]
            dmg = [*base_dmg[:3], dmg4, *base_dmg[4:]]
            write_arrays(hp, dmg)
            # Same policy as `gear_curve_probe` (and ADR-0339's reference run), so the
            # bare row and the T6 row are comparable: same runner skill, only gear differs.
            bare = parse_survival(
                run(
                    [
                        "npx",
                        "tsx",
                        "scripts/mission_survival.ts",
                        "--seeds",
                        str(args.seeds),
                        "--cards",
                        "best",
                        "--loot",
                        "value",
                    ]
                )
            )
            gear = gear_mission()
            campaign = parse_campaign(
                run(
                    [
                        "npx",
                        "tsx",
                        "scripts/campaign_survival.ts",
                        "--seeds",
                        str(args.campaign_seeds),
                    ]
                )
            )
            rows.append(
                {
                    "cap": label,
                    "g4_dmg": dmg4,
                    "bare": bare,
                    "campaign": campaign,
                    "t1": gear[gear_label("T1", gear)],
                    "t2": gear[gear_label("T2", gear)],
                    "t4": gear[gear_label("T4", gear)],
                    "t6": gear[gear_label("T6", gear)],
                }
            )
            print(f"  done g4 dmg {dmg4:+3d} · {label}", flush=True)
    finally:
        SCALING.write_text(original)
        restored = SCALING.read_text() == original
        print(f"source restored: {'yes' if restored else 'NO -- CHECK THE FILE'}")

    header = "cap                g4dmg | " + " ".join(f"   g{g}" for g in GRADE_NAMES)
    print()
    print("### bare mission (recorded baseline, cards best / loot value)")
    print(header)
    for row in rows:
        print(f"{row['cap']:18s} {row['g4_dmg']:+5d} | {fmt(row['bare'])}")  # type: ignore[arg-type]

    print()
    print("### gear T6 — ADR-0328 band is g5 65 / g6 70 (±8)")
    print(header)
    for row in rows:
        print(f"{row['cap']:18s} {row['g4_dmg']:+5d} | {fmt(row['t6'])}")  # type: ignore[arg-type]

    print()
    print("### campaign by start grade — pass criterion 1 is g3 >= g4")
    print(header)
    for row in rows:
        print(f"{row['cap']:18s} {row['g4_dmg']:+5d} | {fmt(row['campaign'])}")  # type: ignore[arg-type]

    print()
    print("### verdicts")
    print("cap                g4dmg | g3>=g4 | T6 in band | gear mono | bare g5,g6 vs 25,30")
    for row in rows:
        campaign: dict[int, float] = row["campaign"]  # type: ignore[assignment]
        bare: dict[int, float] = row["bare"]  # type: ignore[assignment]
        t1: list[float] = row["t1"]  # type: ignore[assignment]
        t2: list[float] = row["t2"]  # type: ignore[assignment]
        t4: list[float] = row["t4"]  # type: ignore[assignment]
        t6: list[float] = row["t6"]  # type: ignore[assignment]
        # Better gear must never make a late grade worse: T1 <= T2 <= T4 <= T6.
        mono = all(
            t1[g] <= t2[g] + 0.01 and t2[g] <= t4[g] + 0.01 and t4[g] <= t6[g] + 0.01
            for g in (4, 5)
        )
        in_band = 57 <= t6[4] <= 78 and 62 <= t6[5] <= 78
        print(
            f"{row['cap']:18s} {row['g4_dmg']:+5d} | "
            f"{'yes' if campaign[3] >= campaign[4] else 'NO '}     | "
            f"{'yes' if in_band else 'NO '}        | "
            f"{'yes' if mono else 'NO '}       | "
            f"{bare[5]:5.1f} / {bare[6]:5.1f}"
        )

    if args.csv:
        path = Path(args.csv)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "cap,g4_dmg,bare_g1..g6,t6_g1..g6,campaign_g1..g6\n"
            + "\n".join(
                ",".join(
                    [
                        row["cap"],  # type: ignore[list-item]
                        str(row["g4_dmg"]),
                        ";".join(f"{v:.1f}" for v in row["bare"]),  # type: ignore[union-attr]
                        ";".join(f"{v:.1f}" for v in row["t6"]),  # type: ignore[union-attr]
                        ";".join(f"{v:.1f}" for v in row["campaign"].values()),  # type: ignore[union-attr]
                    ]
                )
                for row in rows
            )
            + "\n"
        )
        print(f"\ncsv: {path}")


if __name__ == "__main__":
    main()