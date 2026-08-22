#!/usr/bin/env python3
"""Refresh ``prototype/data/game_facts.json`` from canonical sources.

The single source of truth for the dashboard copy (mission count,
stage count, character count, ICE count, …) lives in
``prototype/data/missions/missions.json`` and the various source
modules.  The tests in
``prototype/tests/integration/test_dashboard_facts.py`` verify that
dashboard copy matches a separate ``game_facts.json`` snapshot.

When the underlying data changes — a new mission is added, a new
SkillEffect appears, a new ICE variant is registered, etc. — the
facts file becomes stale and a CI test fails with::

    AssertionError: game_facts.json is older than missions.json —
    run `python scripts/sync_dashboard_facts.py` to refresh

This script re-derives every fact from the canonical sources and
writes the snapshot.  It is **idempotent** and **safe to run at
any time**.  Run it once locally after a content change, then
commit the resulting ``game_facts.json``.

Usage::

    python scripts/sync_dashboard_facts.py            # write in place
    python scripts/sync_dashboard_facts.py --check    # exit 1 if stale
    python scripts/sync_dashboard_facts.py --diff     # show what would change

The ``--check`` mode is suitable for a pre-commit hook: it exits
non-zero when the facts file is out of date without modifying it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROTOTYPE = Path(__file__).resolve().parents[1] / "prototype"
REPO = PROTOTYPE.parent
MISSIONS_JSON = PROTOTYPE / "data" / "missions" / "missions.json"
FACTS_JSON = PROTOTYPE / "data" / "game_facts.json"
SRC = PROTOTYPE / "src" / "wet_run"
SOUNDS_DIR = PROTOTYPE / "data" / "sounds_test"
SCENES_DIR = PROTOTYPE / "data" / "scenes"
PROGRAMS_JSON = PROTOTYPE / "data" / "programs" / "programs.json"
CYBERSPACE_JSON = PROTOTYPE / "data" / "cyberspace" / "worlds.json"
STATE_PY = SRC / "run" / "state.py"
COMBAT_STATE_PY = SRC / "combat" / "state.py"
COMBAT_STATE_MODELS_PY = SRC / "combat" / "state_models.py"


def _count_missions() -> int:
    return len(json.loads(MISSIONS_JSON.read_text(encoding="utf-8")))


def _character_stats() -> tuple[int, list[str]]:
    data = json.loads(MISSIONS_JSON.read_text(encoding="utf-8"))
    chars = sorted({m["story"]["character_ref"] for m in data.values() if "story" in m})
    return len(chars), chars


def _arc_stats() -> tuple[list[int], dict[str, int]]:
    data = json.loads(MISSIONS_JSON.read_text(encoding="utf-8"))
    arcs = sorted({m["story"]["arc"] for m in data.values() if "story" in m})
    dist: dict[str, int] = {}
    for m in data.values():
        a = str(m["story"]["arc"])
        dist[a] = dist.get(a, 0) + 1
    return arcs, dist


def _count_stages() -> int:
    """Count Stage enum values in run/state.py (shim) or run/state/models.py."""
    STATE_MODELS_PY = STATE_PY.parent / "state" / "models.py"
    sources: list[Path] = [p for p in (STATE_PY, STATE_MODELS_PY) if p.exists()]
    if not sources:
        return 0
    for src in sources:
        text = src.read_text(encoding="utf-8")
        m = re.search(r"class Stage\(StrEnum\)[\s\S]+?(\nclass |\Z)", text)
        if m:
            return len(re.findall(r'=\s*"', m.group(0)))
    return 0


def _count_ice() -> int:
    from collections import Counter

    ice = json.loads((PROTOTYPE / "data" / "combat" / "ice_types.json").read_text(encoding="utf-8"))
    return len(ice)


def _count_sounds() -> int:
    if not SOUNDS_DIR.exists():
        return 0
    return sum(1 for f in SOUNDS_DIR.glob("*.wav"))


def _count_gn_scenes() -> tuple[dict[str, int], int]:
    if not SCENES_DIR.exists():
        return {}, 0
    by_char: dict[str, int] = {}
    for char_dir in sorted(SCENES_DIR.iterdir()):
        if not char_dir.is_dir():
            continue
        n = sum(1 for f in char_dir.glob("*.json") if not f.stem.endswith("_ko"))
        by_char[char_dir.name] = n
    return by_char, sum(by_char.values())


def _count_programs() -> int:
    return len(json.loads(PROGRAMS_JSON.read_text(encoding="utf-8")))


def _cyberspace_stats() -> tuple[int, int, int]:
    w = json.loads(CYBERSPACE_JSON.read_text(encoding="utf-8"))
    worlds = w["worlds"]
    n_worlds = len(worlds)
    n_sectors = sum(len(v) for v in worlds.values())
    n_servers = sum(len(v) for w_ in worlds.values() for v in w_.values())
    return n_worlds, n_sectors, n_servers


def _count_skill_effects() -> int:
    if not COMBAT_STATE_MODELS_PY.exists():
        return 0
    text = COMBAT_STATE_MODELS_PY.read_text(encoding="utf-8")
    m = re.search(r"class SkillEffect[\s\S]+?(\nclass |\Z)", text)
    if not m:
        return 0
    return len(re.findall(r'=\s*"', m.group(0)))


def _count_tests() -> int:
    """Approximate the number of test functions across the test tree."""
    n = 0
    for f in (PROTOTYPE / "tests").rglob("test_*.py"):
        n += len(re.findall(r"^\s*def\s+test_\w+", f.read_text(), re.MULTILINE))
    return n


def _collect_facts() -> dict:
    """Build the canonical facts dict from upstream sources."""
    n_chars, char_ids = _character_stats()
    arcs, dist = _arc_stats()
    gn_by_char, gn_total = _count_gn_scenes()
    n_worlds, n_sectors, n_servers = _cyberspace_stats()

    return {
        "mission_count": _count_missions(),
        "character_count": n_chars,
        "character_ids": char_ids,
        "arcs": arcs,
        "arc_distribution": dist,
        "ice_unique_count": _count_ice(),
        "stage_count": _count_stages(),
        "sound_wav_count": _count_sounds(),
        "gn_scenes_by_char": gn_by_char,
        "gn_scenes_total": gn_total,
        "program_count": _count_programs(),
        "ending_combinations": 9,  # A/B/C × 3 (case/sil/kas)
        "cyberspace_worlds": n_worlds,
        "cyberspace_sectors_per_world": n_sectors // n_worlds if n_worlds else 0,
        "cyberspace_sectors_total": n_sectors,
        "cyberspace_servers_total": n_servers,
        "skill_effect_count": _count_skill_effects(),
        "test_count_collected": _count_tests(),
        "_generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def _load_existing() -> dict | None:
    if not FACTS_JSON.exists():
        return None
    return json.loads(FACTS_JSON.read_text(encoding="utf-8"))


def _diff_facts(old: dict, new: dict) -> list[str]:
    """Return a list of human-readable diff lines (old → new)."""
    if old is None:
        return ["facts.json did not exist — would be created"]
    out: list[str] = []
    keys = sorted(set(old) | set(new))
    for k in keys:
        ov = old.get(k)
        nv = new.get(k)
        if ov != nv:
            out.append(f"  {k}: {ov!r} → {nv!r}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true",
        help="Exit non-zero if facts.json is out of date; do not write.",
    )
    parser.add_argument(
        "--diff", action="store_true",
        help="Print what would change; do not write.",
    )
    args = parser.parse_args()

    new = _collect_facts()
    old = _load_existing()

    if args.diff or args.check:
        diffs = _diff_facts(old, new)
        if not diffs:
            print("[sync_dashboard_facts] facts.json is up to date.")
            return 0
        print("[sync_dashboard_facts] facts.json is STALE:")
        for line in diffs:
            print(line)
        return 1 if args.check else 0

    # Write mode.
    FACTS_JSON.write_text(
        json.dumps(new, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    diffs = _diff_facts(old, new)
    if diffs:
        print(f"[sync_dashboard_facts] wrote {FACTS_JSON}")
        for line in diffs:
            print(line)
    else:
        print(f"[sync_dashboard_facts] no changes ({FACTS_JSON})")
    return 0


if __name__ == "__main__":
    sys.exit(main())