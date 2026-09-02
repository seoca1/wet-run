#!/usr/bin/env python3
"""Unified data export script for wet_run-web migration.

Exports all game data from Python prototype to Web format:
- effects.json (canonical VFX schema)
- missions.json (mission definitions)
- programs.json (player programs)
- ice_types.json (ICE enemy types)
- strings.json (i18n strings)

Usage:
    cd wet_run-web
    python3 scripts/export_all.py
    python3 scripts/export_all.py --dry-run
    python3 scripts/export_all.py --only missions,programs
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_DATA = REPO_ROOT.parent / "prototype" / "data"
WEB_DATA = Path(__file__).resolve().parents[1] / "src" / "data"

# Export configuration
EXPORTS = {
    "effects": {
        "src": PROTOTYPE_DATA / "effects.json",
        "dst": WEB_DATA / "effects.json",
        "type": "json",
    },
    "missions": {
        "src": PROTOTYPE_DATA / "missions" / "missions.json",
        "dst": WEB_DATA / "missions.json",
        "type": "json",
    },
    "programs": {
        "src": PROTOTYPE_DATA / "programs" / "programs.json",
        "dst": WEB_DATA / "programs.json",
        "type": "json",
    },
    "ice_types": {
        "src": PROTOTYPE_DATA / "combat" / "ice_types.json",
        "dst": WEB_DATA / "ice_types.json",
        "type": "json",
    },
    "strings_en": {
        "src": PROTOTYPE_DATA / "i18n" / "en.json",
        "dst": WEB_DATA / "strings.json",
        "type": "json",
    },
}

# Fields to exclude from Web export (Python-only fields)
EXCLUDE_FIELDS = {
    "is_canonical_cast",
    "story",
    "random_weight",
    "is_chain_mission",
    "chain_id",
    "chain_order",
}


def filter_mission(mission: dict) -> dict:
    """Remove Python-only fields from mission data."""
    return {k: v for k, v in mission.items() if k not in EXCLUDE_FIELDS}


def export_json(src: Path, dst: Path, mission_filter: bool = False) -> bool:
    """Export a JSON file, optionally filtering mission data."""
    if not src.exists():
        print(f"  [SKIP] Source not found: {src}")
        return False

    with src.open() as f:
        data = json.load(f)

    if mission_filter:
        data = {k: filter_mission(v) for k, v in data.items()}

    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return True


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    only_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--only="):
            only_filter = set(arg.split("=", 1)[1].split(","))

    print(f"[export_all] REPO_ROOT: {REPO_ROOT}")
    print(f"[export_all] PROTOTYPE_DATA: {PROTOTYPE_DATA}")
    print(f"[export_all] WEB_DATA: {WEB_DATA}")
    print()

    exported = 0
    skipped = 0

    for name, config in EXPORTS.items():
        if only_filter and name not in only_filter:
            continue

        src = config["src"]
        dst = config["dst"]

        if dry_run:
            exists = src.exists()
            print(f"  {'[OK]' if exists else '[MISSING]'} {name}: {src}")
            if exists:
                exported += 1
            else:
                skipped += 1
            continue

        mission_filter = (name == "missions")
        if export_json(src, dst, mission_filter):
            print(f"  [EXPORTED] {name}: {dst}")
            exported += 1
        else:
            skipped += 1

    print()
    if dry_run:
        print(f"[export_all] dry-run: {exported} would export, {skipped} skipped")
    else:
        print(f"[export_all] Done: {exported} exported, {skipped} skipped")

    return 0


if __name__ == "__main__":
    sys.exit(main())