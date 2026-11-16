#!/usr/bin/env python3
"""Import the event dialogues into the app (ADR-0317 migration step 3b).

`docs/design/story/event_dialogues.json` (v0.2) holds the authored NPC beats —
the Finn, Dixie, the ICE tag-lines, the endings — with their derivative-fiction
sources. It has never been read by the code. This copies it into
`web/src/data/` so the game can speak it, and reports what cannot be reached.

Rules:
  - The design file stays the source of truth; this is a copy, not a rewrite.
  - Only the fields the game reads are kept (`id`, `npc`, `title_*`,
    `context_*`, `lines`), so a design-only field cannot silently become
    gameplay.
  - It reports dialogue ids whose trigger does not exist in the game yet
    (e.g. an `ice_<id>_intro` with no such ICE) instead of pretending.

Usage:
    python3 scripts/tools/import_event_dialogues.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SOURCE = os.path.join(ROOT, "docs", "design", "story", "event_dialogues.json")
TARGET = os.path.join(ROOT, "web", "src", "data", "event_dialogues.json")
ICE_CATALOG = os.path.join(ROOT, "web", "src", "data", "ice_types.json")

KEEP_DIALOGUE = ("id", "npc", "title_en", "title_ko", "context_en", "context_ko", "lines")
KEEP_LINE = ("speaker", "speaker_ko", "text_en", "text_ko")

# `ice_<id>_intro` is the one naming convention the game can resolve.
ICE_INTRO_RE = re.compile(r"^ice_(.+)_intro$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(SOURCE):
        print(f"event dialogues not found: {SOURCE}", file=sys.stderr)
        return 2
    src = json.load(open(SOURCE, encoding="utf-8"))
    dialogues = src.get("dialogues", {})

    out_dialogues = {}
    for did, d in dialogues.items():
        out_dialogues[did] = {
            k: d[k] for k in KEEP_DIALOGUE if k in d
        }
        out_dialogues[did]["lines"] = [
            {k: line[k] for k in KEEP_LINE if k in line} for line in d.get("lines", [])
        ]

    out = {
        "version": src.get("version", "0.2.0"),
        "title": src.get("title", "Sprawl Event Dialogues"),
        "npcs": src.get("npcs", {}),
        "dialogues": out_dialogues,
    }

    # What can the game actually reach today?
    ice = json.load(open(ICE_CATALOG, encoding="utf-8"))
    ice_ids = {k for k in ice if k != "skill_defs"}
    reachable: list[str] = []
    unreachable: list[str] = []
    for did in out_dialogues:
        m = ICE_INTRO_RE.match(did)
        if m:
            (reachable if m.group(1) in ice_ids else unreachable).append(did)

    if not args.dry_run:
        with open(TARGET, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

    print(f"dialogues {'would be ' if args.dry_run else ''}written: {len(out_dialogues)}")
    print(f"npcs: {len(out['npcs'])}")
    print(f"ice-taglines the catalog can reach: {reachable}")
    print(f"ice-taglines with no such ICE: {unreachable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
