#!/usr/bin/env python3
"""Back-fill ``game_integration`` blocks in Fiction short stories.

v0.4 of Roguelike Sprawl opened a novel pipeline (ADR-0061) that ties
every mission in ``data/missions/missions.json`` to a Fiction short
story via the mission's ``story.source`` field.  The richer Fiction
files carry a ``game_integration`` frontmatter block that names the
mission explicitly (``mission_id``, ``arc``, ``character_ref``).

Two early classes of stories didn't get that block:

1. v0.4's novel pipeline was added *after* many short stories were
   already merged; their frontmatter predates the convention.
2. New 2026-07-01 stories (``hosaka_core``, ``maas_heist`` …) had the
   block baked in by template.

This one-shot tool reads every EN short story in
``Fiction/derivative/sprawl-trilogy/short-stories/``, looks up the
mission that owns it via the canonical source→mission_id table, and
writes/updates the ``game_integration`` field in-place.  It's a
migrate script: run once, commit the diff, never run again.

Usage::

    PROJECT=Game/roguelike_sprawl python scripts/backfill_game_integration.py

The script is intentionally **idempotent** — running it twice yields
the same content.  Add a CI guard in
``tests/integration/test_novel_pipeline_e2e.py`` (already added) to
catch regressions where a Fiction file loses the block.

Fiction repository policy: this tool operates in-place on a
filesystem-level target, so call it from a checkout of the Fiction
repo.  It won't damage files that already have a complete block.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FICTION_DIR = Path(
    "/Users/emilio/projects/Projects/Fiction/derivative/sprawl-trilogy/short-stories"
)
MISSIONS_JSON = (
    Path(__file__).resolve().parents[1]
    / "prototype"
    / "data" / "missions" / "missions.json"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fiction-dir",
        default=str(FICTION_DIR),
        help="Directory of Fiction short stories (.md)",
    )
    parser.add_argument(
        "--missions-json",
        default=str(MISSIONS_JSON),
        help="Path to prototype/data/missions/missions.json",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would change without writing",
    )
    args = parser.parse_args()

    fiction = Path(args.fiction_dir)
    missions_path = Path(args.missions_json)
    if not fiction.exists():
        print(f"✗ Fiction dir not found: {fiction}", file=sys.stderr)
        return 2
    if not missions_path.exists():
        print(f"✗ missions.json not found: {missions_path}", file=sys.stderr)
        return 2

    import json

    missions_data = json.loads(missions_path.read_text(encoding="utf-8"))
    src_to_mission: dict[str, str] = {
        m["story"]["source"]: mid
        for mid, m in missions_data.items()
        if isinstance(m, dict) and "story" in m
    }

    # Patterns for the YAML frontmatter block.
    fm_start = re.compile(r"^---\s*$", re.MULTILINE)
    fm_end = re.compile(r"^---\s*$", re.MULTILINE)
    date_prefix = re.compile(r"^(\d{4}-\d{2}-\d{2})_")

    updated = 0
    skipped = 0
    untouched = 0

    for path in sorted(fiction.glob("*.md")):
        if path.stem.endswith(".ko") or path.stem.endswith(".tone-prompt"):
            continue
        stem = date_prefix.sub("", path.stem)
        mission_id = src_to_mission.get(stem)
        if not mission_id:
            skipped += 1
            continue

        mission = missions_data[mission_id]
        text = path.read_text(encoding="utf-8")
        new_block = _render_block(mission_id, mission)

        # Find first frontmatter block and replace its game_integration
        # subsection.  If a complete block already exists verbatim, we
        # leave the file untouched.
        m_starts = list(fm_start.finditer(text))
        if len(m_starts) < 2:
            # No frontmatter — skip (single-file Fiction stories often
            # skip frontmatter).
            untouched += 1
            continue

        block_start, block_end = m_starts[0].end(), m_starts[1].start()
        block = text[block_start:block_end]

        if "game_integration:" in block and re.search(
            r"^\s*mission_id:\s*['\"]?" + re.escape(mission_id) + r"['\"]?",
            block,
            re.MULTILINE,
        ):
            untouched += 1
            continue

        new_text = _replace_or_inject_gi(text, m_starts, new_block)
        if new_text == text:
            untouched += 1
            continue

        if args.dry_run:
            print(f"[dry-run] would update: {path.name}")
        else:
            path.write_text(new_text, encoding="utf-8")
            print(f"updated: {path.name}")
        updated += 1

    print(f"\nUpdated: {updated}  Untouched: {untouched}  Skipped: {skipped}")
    return 0


def _render_block(mission_id: str, mission: dict) -> str:
    """Render the canonical ``game_integration`` block for a mission."""
    story = mission["story"]
    return (
        "game_integration:\n"
        f"  mission_id: \"{mission_id}\"\n"
        f"  arc: {story['arc']}\n"
        f"  character_ref: \"{story['character_ref']}\"\n"
        f"  pillar: \"{story['pillar']}\"\n"
    )


def _replace_or_inject_gi(text: str, m_starts: list, new_block: str) -> str:
    """Replace existing ``game_integration:`` block or append before the
    closing ``---`` of the frontmatter.

    We approximate indentation by prefixing each line with 2 spaces.
    """
    block_start = m_starts[0].end()
    block_end = m_starts[1].start()

    # If there's a game_integration: line, replace its whole block.
    pattern = re.compile(
        r"^( *)game_integration:.*?(?=^---|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    fm_text = text[block_start:block_end]
    if pattern.search(fm_text):
        indented = "\n".join("  " + line for line in new_block.split("\n") if line)
        new_fm = pattern.sub(indented, fm_text)
        if new_fm.endswith("\n"):
            new_fm = new_fm.rstrip("\n") + "\n"
        return text[:block_start] + new_fm + text[block_end:]

    # Otherwise, inject before the closing ``---``.
    injection = (
        "\n" + "\n".join("  " + line for line in new_block.split("\n") if line) + "\n"
    )
    new_fm = fm_text.rstrip("\n") + injection
    return text[:block_start] + new_fm + text[block_end:]


if __name__ == "__main__":
    sys.exit(main())