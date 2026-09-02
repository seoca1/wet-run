#!/usr/bin/env python3
"""Export missions from Python prototype to Web format.

Reads:  prototype/data/missions/missions.json (canonical)
Writes: wet_run-web/src/data/missions.json (consumer)

Usage:
    python scripts/export_missions.py
    python scripts/export_missions.py --dry-run
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_MISSIONS = REPO_ROOT.parent / "prototype" / "data" / "missions" / "missions.json"
WEB_MISSIONS = REPO_ROOT / "src" / "data" / "missions.json"

# Fields to exclude from Web export (Python-only fields)
EXCLUDE_FIELDS = {
    "is_canonical_cast",  # Python-only metadata
    "story",  # Python-only narrative data (synopsis_en/ko, word_count)
    "random_weight",  # Python-only weighting
    "is_chain_mission",  # Phase 11 chain system (not in Web yet)
    "chain_id",
    "chain_order",
}


def filter_mission(mission: dict) -> dict:
    """Remove Python-only fields from mission data."""
    return {k: v for k, v in mission.items() if k not in EXCLUDE_FIELDS}


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    if not PYTHON_MISSIONS.exists():
        print(f"Error: Python missions not found: {PYTHON_MISSIONS}", file=sys.stderr)
        return 1

    with PYTHON_MISSIONS.open() as f:
        python_data = json.load(f)

    web_data = {}
    for mission_id, mission in python_data.items():
        web_data[mission_id] = filter_mission(mission)

    if dry_run:
        print(f"[dry-run] Would export {len(web_data)} missions to {WEB_MISSIONS}")
        print(f"  Sample IDs: {list(web_data.keys())[:5]}")
        return 0

    with WEB_MISSIONS.open("w") as f:
        json.dump(web_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"[export_missions] Exported {len(web_data)} missions to {WEB_MISSIONS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())