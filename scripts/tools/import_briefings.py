#!/usr/bin/env python3
"""Import mission briefings from the derivative fiction (ADR-0316).

The Sprawl missions carry no in-game story text: the narrative lives in
`Fiction/derivative/`, where 166 sprawl stories declare a `game_mission_id`
and a clean one-paragraph `plot_summary`. This tool lifts that summary into
`web/src/data/missions.json` as `briefing`, so the mission a player picks can
say what it is about.

Rules:
  - Only Sprawl missions are touched. Far Grid missions already have their own
    briefing (ADR-0213 Wave 2) and are left alone.
  - The summary is cleaned (surrounding quotes, doubled apostrophes, collapsed
    whitespace) and truncated at a word boundary — a briefing is one line, not
    a paragraph.
  - Idempotent: running it twice changes nothing.
  - Slop is checked: the Fiction audit found injected filler in story BODIES.
    `plot_summary` was verified clean (0 hits across 168 summaries), but this
    tool refuses a summary that contains a known slop marker.

Usage:
    python3 scripts/tools/import_briefings.py [--dry-run]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MISSIONS = os.path.join(ROOT, "web", "src", "data", "missions.json")
FICTION = os.path.abspath(os.path.join(ROOT, "..", "..", "Fiction", "derivative"))

# A briefing is the job in a sentence or two — and it has to be a WHOLE
# sentence. The first version cut at 150 characters, which ended mid-clause with
# an ellipsis ("…a secret that could bring down a mid-level…") and then handed
# that to the screen as the fixer's words. Truncated text read as broken, and
# marking it with "…" only said so. Complete sentences only, no truncation
# marker, and a fragment is refused rather than papered over.
MAX_LEN = 240

# Below this a "briefing" says nothing ("A."). The floor also matches the one
# `collect` puts on a source summary, so a candidate that only shrinks into
# nonsense is refused rather than written.
MIN_LEN = 40

SENTENCE_RE = re.compile(r"[^.!?]+[.!?]+[\"')\]]*")
SENTENCE_END = (".", "!", "?", '"', "'")

SLOP_MARKERS = (
    "i noticed",
    "the texture of",
    "was undeniable",
    "holographic display filtered",
    "i could hear",
)

# A doubled word ("the the matrix") is a slop-removal scar: the sentence around
# the injected filler was stitched back together badly.
DOUBLED_WORD_RE = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)

SUMMARY_RE = re.compile(r"^plot_summary:\s*\n\s*en:\s*(.+)$", re.M)
ID_RE = re.compile(r"^game_mission_id:\s*([a-z_0-9-]+)\s*$", re.M)
INTEG_RE = re.compile(r"^game_integration:\s*\n(?:\s+.*\n)*?\s+mission_id:\s*([a-z_0-9-]+)", re.M)


def clean(text: str) -> str:
    t = text.strip()
    # YAML may wrap the value in single or double quotes; the content escapes
    # an apostrophe by doubling it. The wrapper is not always a matched pair
    # once a body has been rewritten, so strip whatever quotes are on the ends
    # — a summary never legitimately opens with one.
    t = t.strip("\"'")
    t = t.replace("''", "'").replace('\\"', '"').replace("\\'", "'")
    # Repair a slop-removal scar rather than discarding the summary: when the
    # injected filler was cut out, the join sometimes left a doubled word
    # ("the the matrix").
    t = DOUBLED_WORD_RE.sub(r"\1", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def brief(text: str) -> str | None:
    """The leading whole sentence(s) of `text`, up to `MAX_LEN`.

    `None` when there is no complete sentence inside the budget — a fragment
    like "… The shard's" has nothing to say, and saying half of it says less.
    """
    sentences = [s.strip() for s in SENTENCE_RE.findall(text)]
    if not sentences:
        return None
    out = sentences[0]
    for sentence in sentences[1:]:
        if len(out) + 1 + len(sentence) > MAX_LEN:
            break
        out = f"{out} {sentence}"
    if len(out) > MAX_LEN or len(out) < MIN_LEN or not out.endswith(SENTENCE_END):
        return None
    return out


def has_slop(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in SLOP_MARKERS)


def collect() -> dict[str, str]:
    """mission_id -> cleaned summary, preferring the story that declares the
    mission in `game_integration` and is short enough to read as a briefing."""
    candidates: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    pattern = os.path.join(FICTION, "**", "en", "*.md")
    for path in glob.glob(pattern, recursive=True):
        text = open(path, errors="ignore").read()
        mid = ID_RE.search(text)
        summ = SUMMARY_RE.search(text)
        if not mid or not summ:
            continue
        body = clean(summ.group(1))
        if len(body) < 40 or has_slop(body):
            continue
        declared = INTEG_RE.search(text)
        declared_match = 1 if declared and declared.group(1) == mid.group(1) else 0
        # Prefer a declared match, then the shortest readable summary.
        candidates[mid.group(1)].append((declared_match, -len(body), body))

    out: dict[str, str] = {}
    for mid, options in candidates.items():
        options.sort(reverse=True)
        for _, _, body in options:
            chosen = brief(body)
            if chosen:
                out[mid] = chosen
                break
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(FICTION):
        print(f"Fiction derivative directory not found: {FICTION}", file=sys.stderr)
        return 2

    briefings = collect()
    missions = json.load(open(MISSIONS, encoding="utf-8"))

    written = 0
    skipped_far_grid = 0
    missing: list[str] = []
    for mid, mission in missions.items():
        if (mission.get("source_universe") or "sprawl") != "sprawl":
            skipped_far_grid += 1
            continue
        text = briefings.get(mid)
        if not text:
            missing.append(mid)
            continue
        if mission.get("briefing") == text:
            continue
        if not args.dry_run:
            mission["briefing"] = text
        written += 1

    if not args.dry_run and written:
        with open(MISSIONS, "w", encoding="utf-8") as fh:
            json.dump(missions, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

    print(f"summaries found: {len(briefings)}")
    print(f"briefings {'would be ' if args.dry_run else ''}written: {written}")
    print(f"far-grid missions left alone: {skipped_far_grid}")
    print(f"sprawl missions still without a briefing: {len(missing)}")
    if missing:
        print("  " + ", ".join(sorted(missing)[:12]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
