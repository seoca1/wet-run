#!/usr/bin/env python3
"""Export wet_run Python game data to static JSON for the web MVP.

Reads from Game/wet_run/prototype/data/, writes to Game/wet_run-web/src/data/.

Per ADR-0199, MVP only exports the data needed for:
- 1 playable mission (first_jack.json)
- Programs (programs.json)
- ICE types (ice_types.json subset)
- English i18n strings

Tier 2 will expand to all missions + full i18n.

Usage:
    cd /Users/emilio/projects/Projects/Game/wet_run-web
    python3 scripts/export_web_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WET_RUN_DATA = REPO_ROOT / "prototype" / "data"
WEB_DATA = Path(__file__).resolve().parents[1] / "src" / "data"

# Tier 2a (2026-08-25): 5 curated missions for the browser MVP.
# Curated for: tier 1-2 difficulty, narrative flow, fixer variety.
MVP_MISSION_IDS: tuple[str, ...] = (
    "first_jack",          # Tier 1 — tutorial entry
    "watchdog_patrol",     # Tier 1 — same fixer, escalation
    "ono_sendai_repair",   # Tier 2 — different verb (repair vs extract)
    "construct_market",    # Tier 2 — same zone (surface)
    "ghost_signal_origin", # Tier 2 — different fixer (sally), arc6 aftermath
)


def _load_json(path: Path) -> dict | list:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  wrote {path} ({path.stat().st_size} bytes)")


def export_mvp_missions() -> None:
    """Export curated Tier 2a missions (5 total) for the browser MVP."""
    missions = _load_json(WET_RUN_DATA / "missions" / "missions.json")
    missing = [mid for mid in MVP_MISSION_IDS if mid not in missions]
    if missing:
        available = sorted(missions.keys())[:5]
        print(
            f"ERROR: missing missions {missing}. First 5 available: {available}",
            file=sys.stderr,
        )
        sys.exit(1)
    mvp = {mid: missions[mid] for mid in MVP_MISSION_IDS}
    _write_json(WEB_DATA / "missions.json", mvp)
    print(f"  mission count: {len(mvp)}")


def export_programs() -> None:
    """Export programs.json for the MVP."""
    programs = _load_json(WET_RUN_DATA / "programs" / "programs.json")
    _write_json(WEB_DATA / "programs.json", programs)


def export_ice_types() -> None:
    """Export ICE types JSON for the MVP."""
    ice_types = _load_json(WET_RUN_DATA / "combat" / "ice_types.json")
    _write_json(WEB_DATA / "ice_types.json", ice_types)


def export_strings() -> None:
    """Export English i18n strings for the MVP (subset)."""
    en = _load_json(WET_RUN_DATA / "i18n" / "en.json")
    # MVP needs: menu, hub, combat, matrix, status, help, settings
    sections = {
        k: v
        for k, v in en.items()
        if k in {"menu", "hub", "combat", "matrix", "status", "help", "settings"}
    }
    _write_json(WEB_DATA / "strings.json", sections)


def main() -> int:
    print("=== wetrun-web data export ===\n")
    print(f"Source: {WET_RUN_DATA}")
    print(f"Target: {WEB_DATA}\n")
    print(f"Exporting Tier 2a subset ({len(MVP_MISSION_IDS)} missions + programs + ICE types + strings):")
    export_mvp_missions()
    export_programs()
    export_ice_types()
    export_strings()
    print("\n✅ Export complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
