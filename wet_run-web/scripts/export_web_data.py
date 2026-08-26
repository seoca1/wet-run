#!/usr/bin/env python3
"""Export wet_run Python game data to static JSON for the web MVP.

Tier 2c (2026-08-26, ADR-0202): 15 curated missions + 12 ICE types.

Reads from Game/wet_run/prototype/data/, writes to Game/wet_run-web/src/data/.

Usage:
    cd /Users/emilio/projects/Projects/Game/wet_run/wet_run-web
    python3 scripts/export_web_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WET_RUN_DATA = REPO_ROOT / "prototype" / "data"
WEB_DATA = Path(__file__).resolve().parents[1] / "src" / "data"

TIER_2C_MISSION_IDS: tuple[str, ...] = (
    "first_jack",
    "watchdog_patrol",
    "ono_sendai_repair",
    "construct_market",
    "ghost_signal_origin",
    "razor_work",
    "soho_blackout",
    "delivery_to_finn",
    "ice_run",
    "armitage_infiltration",
    "flatline_call",
    "hosaka_corporate_infiltration",
    "idoru_wedding",
    "laney_node_signal_run",
    "first_contact",
)

TIER_2C_ICE_IDS: tuple[str, ...] = (
    "standard",
    "watchdog",
    "spider",
    "raven",
    "loa_priest",
    "ta_security_ice",
    "ice_feedback_loop",
    "black",
    "goliath",
    "loa_entity",
    "revelation",
    "ai_whisper",
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


def export_missions() -> None:
    missions = _load_json(WET_RUN_DATA / "missions" / "missions.json")
    missing = [mid for mid in TIER_2C_MISSION_IDS if mid not in missions]
    if missing:
        available = sorted(missions.keys())[:5]
        print(
            f"ERROR: missing missions {missing}. First 5 available: {available}",
            file=sys.stderr,
        )
        sys.exit(1)
    curated = {mid: missions[mid] for mid in TIER_2C_MISSION_IDS}
    _write_json(WEB_DATA / "missions.json", curated)
    print(f"  mission count: {len(curated)}")


def export_programs() -> None:
    programs = _load_json(WET_RUN_DATA / "programs" / "programs.json")
    _write_json(WEB_DATA / "programs.json", programs)


def export_ice_types() -> None:
    ice_types = _load_json(WET_RUN_DATA / "combat" / "ice_types.json")
    missing = [iid for iid in TIER_2C_ICE_IDS if iid not in ice_types]
    if missing:
        available = sorted(ice_types.keys())[:5]
        print(
            f"ERROR: missing ICE types {missing}. First 5 available: {available}",
            file=sys.stderr,
        )
        sys.exit(1)
    curated = {iid: ice_types[iid] for iid in TIER_2C_ICE_IDS}
    _write_json(WEB_DATA / "ice_types.json", curated)
    print(f"  ICE count: {len(curated)}")


def export_strings() -> None:
    en = _load_json(WET_RUN_DATA / "i18n" / "en.json")
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
    print(
        f"Exporting Tier 2c subset ({len(TIER_2C_MISSION_IDS)} missions, "
        f"{len(TIER_2C_ICE_IDS)} ICE types, programs, strings):"
    )
    export_missions()
    export_programs()
    export_ice_types()
    export_strings()
    print("\nExport complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())