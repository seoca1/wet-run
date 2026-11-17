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
LEDGER = os.path.join(ROOT, "docs", "design", "story", "briefing-ledger.json")
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
SUMMARY_KO_RE = re.compile(r"^plot_summary:\s*\n\s*en:.*\n\s*ko:\s*(.*)$", re.M)
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


# The importer only reads `**/en/*.md`. The ledger below also surveys the other
# language directories, because a twin can carry a summary the `en` file lost
# (2026-11-17: `watchdog_patrol`'s `en` summary is missing its middle clause and
# its `ko` twin has the whole sentence). Those are reported, not used — the
# choice is the owner's, and changing it changes the game's text.
SCAN_LANG = "en"


def survey() -> dict[str, dict[str, list[dict]]]:
    """Every candidate summary per mission id, from every language directory.

    Returns `{mission_id: {"considered": [...], "other": [...]}}`, where each
    entry is `{file, chars, declared, body, bodyKo}` and `considered` are the
    ones the importer's own scan would see. `bodyKo` is the Korean summary of the
    SAME story, which is what makes it a translation of the briefing rather than
    a summary of something else.
    """
    out: dict[str, dict[str, list[dict]]] = defaultdict(
        lambda: {"considered": [], "other": []}
    )
    pattern = os.path.join(FICTION, "**", "*.md")
    for path in glob.glob(pattern, recursive=True):
        text = open(path, errors="ignore").read()
        mid = ID_RE.search(text)
        summ = SUMMARY_RE.search(text)
        if not mid or not summ:
            continue
        body = clean(summ.group(1))
        ko_match = SUMMARY_KO_RE.search(text)
        body_ko = clean(ko_match.group(1)) if ko_match else ""
        declared = INTEG_RE.search(text)
        entry = {
            "file": os.path.relpath(path, FICTION),
            "chars": len(body),
            "declared": bool(declared and declared.group(1) == mid.group(1)),
            "body": body,
            "bodyKo": body_ko or None,
            "readable": len(body) >= 40 and not has_slop(body),
        }
        bucket = (
            "considered"
            if os.sep + SCAN_LANG + os.sep in path
            else "other"
        )
        out[mid.group(1)][bucket].append(entry)
    return out


def collect() -> dict[str, dict]:
    """mission_id -> {"en": brief, "ko": brief|None, "file": source}.

    Prefers the story that declares the mission in `game_integration`, then the
    shortest readable summary. The Korean brief comes from the SAME file: a
    translation of this story, never a different story's summary of the same
    mission id (2026-11-17 — `aleph_fragment` has six files claiming it).
    """
    surveyed = survey()
    out: dict[str, dict] = {}
    for mid, buckets in surveyed.items():
        options = [
            (1 if c["declared"] else 0, -c["chars"], c)
            for c in buckets["considered"]
            if c["readable"]
        ]
        # Prefer a declared match, then the shortest readable summary.
        options.sort(key=lambda o: (o[0], o[1]), reverse=True)
        for _, _, cand in options:
            chosen = brief(cand["body"])
            if chosen:
                out[mid] = {
                    "en": chosen,
                    "ko": brief(cand["bodyKo"]) if cand["bodyKo"] else None,
                    "file": cand["file"],
                }
                break
    return out


def ledger(briefings: dict[str, str], game_ids: list[str]) -> dict:
    """What the import decided, and what it could have decided.

    This is the intermediate file the pipeline did not have: the game data says
    only what a mission's briefing IS, so a choice between candidates — or a
    candidate the scan never saw — is invisible. 51 fiction mission ids have
    disagreeing candidates; 14 of them are missions the game ships.
    """
    surveyed = survey()
    missions: dict[str, dict] = {}
    for mid in game_ids:
        buckets = surveyed.get(mid, {"considered": [], "other": []})
        entry = briefings.get(mid) or {}
        chosen = entry.get("en")
        chosen_ko = entry.get("ko")
        distinct = {c["body"] for c in buckets["considered"] if c["readable"]}
        missions[mid] = {
            "briefing": chosen,
            # ADR-0316: the Korean brief is the SAME story's summary, so the two
            # say the same thing in two languages. None when the story has no
            # Korean yet — which is most of them, and the source work fills it.
            "briefingKo": chosen_ko,
            "chosenFrom": entry.get("file"),
            "considered": buckets["considered"],
            "notScanned": buckets["other"],
            "disagrees": len(distinct) > 1,
            # A twin in another language directory can carry a summary the
            # scanned one lost. `watchdog_patrol` is the case: its `en` summary
            # is missing a clause and its `ko` twin has the whole sentence.
            "twinDiffers": any(
                c["body"] != chosen and c["readable"] for c in buckets["other"]
            ),
            "note": (
                "the en candidates disagree — one of them is not the whole job"
                if len(distinct) > 1
                else None
            ),
        }
    orphans = sorted(mid for mid in surveyed if mid not in game_ids)
    return {
        "generatedBy": "scripts/tools/import_briefings.py",
        "source": os.path.relpath(FICTION, ROOT),
        "scanLanguage": SCAN_LANG,
        "fictionMissionIds": len(surveyed),
        "gameMissions": len(game_ids),
        "orphanMissionIds": orphans,
        "missions": missions,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify the ledger and the game data still agree; write nothing",
    )
    args = ap.parse_args()

    if not os.path.isdir(FICTION):
        print(f"Fiction derivative directory not found: {FICTION}", file=sys.stderr)
        return 2

    briefings = collect()
    missions = json.load(open(MISSIONS, encoding="utf-8"))
    sprawl_ids = [
        mid
        for mid, m in missions.items()
        if (m.get("source_universe") or "sprawl") == "sprawl"
    ]

    if args.check:
        return check(briefings, missions, sprawl_ids)

    written = 0
    skipped_far_grid = 0
    missing: list[str] = []
    for mid, mission in missions.items():
        if (mission.get("source_universe") or "sprawl") != "sprawl":
            skipped_far_grid += 1
            continue
        entry = briefings.get(mid)
        if not entry:
            missing.append(mid)
            continue
        text = entry["en"]
        text_ko = entry.get("ko")
        if mission.get("briefing") == text and mission.get("briefing_ko") == text_ko:
            continue
        if not args.dry_run:
            mission["briefing"] = text
            # The importer owns both fields, so a Korean brief the source no
            # longer has is removed rather than left to go stale.
            if text_ko:
                mission["briefing_ko"] = text_ko
            else:
                mission.pop("briefing_ko", None)
        written += 1

    if not args.dry_run and written:
        with open(MISSIONS, "w", encoding="utf-8") as fh:
            json.dump(missions, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

    # The ledger is the intermediate file: it records what each mission's
    # briefing came from and which candidates were passed over, so a choice the
    # importer makes cannot be invisible (see `ledger`).
    record = ledger(briefings, sprawl_ids)
    if not args.dry_run:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

    disagree = [m for m, v in record["missions"].items() if v["disagrees"]]
    twins = [m for m, v in record["missions"].items() if v["twinDiffers"]]
    print(f"summaries found: {len(briefings)}")
    print(f"briefings {'would be ' if args.dry_run else ''}written: {written}")
    print(f"far-grid missions left alone: {skipped_far_grid}")
    print(f"sprawl missions still without a briefing: {len(missing)}")
    if missing:
        print("  " + ", ".join(sorted(missing)[:12]))
    print(f"ledger: {os.path.relpath(LEDGER, ROOT)}")
    print(
        f"missions whose candidates disagree: {len(disagree)}"
        + (" -> " + ", ".join(sorted(disagree)[:8]) if disagree else "")
    )
    with_ko = sum(1 for v in record["missions"].values() if v["briefingKo"])
    print(f"briefings with a Korean twin: {with_ko}/{len(record['missions'])}")
    print(
        f"missions whose summary differs in another language: {len(twins)}"
        + (" -> " + ", ".join(sorted(twins)[:8]) if twins else "")
    )
    print(f"fiction mission ids the game does not ship: {len(record['orphanMissionIds'])}")
    return 0


def check(
    briefings: dict[str, str],
    missions: dict,
    sprawl_ids: list[str],
) -> int:
    """The gate: the ledger must describe the game data that is on disk.

    A stale ledger is worse than none — it would report a decision that is no
    longer true — so this fails rather than warns, the same way the narrative
    ledger refuses to keep a wired dialogue on its unwired list.
    """
    if not os.path.isfile(LEDGER):
        print(f"ledger missing: {os.path.relpath(LEDGER, ROOT)}", file=sys.stderr)
        return 1
    record = json.load(open(LEDGER, encoding="utf-8"))
    problems: list[str] = []
    for mid in sprawl_ids:
        entry = record["missions"].get(mid, {})
        for field, key in (("briefing", "en"), ("briefing_ko", "ko")):
            on_disk = missions[mid].get(field)
            in_ledger = entry.get("briefingKo") if field == "briefing_ko" else entry.get("briefing")
            if on_disk != in_ledger:
                problems.append(
                    f"{mid}.{field}: game has {on_disk!r}, ledger has {in_ledger!r}"
                )
            derived = (briefings.get(mid) or {}).get(key)
            if derived != on_disk:
                problems.append(
                    f"{mid}.{field}: the import would write {derived!r}, the game has {on_disk!r}"
                )
    for mid, entry in record["missions"].items():
        if entry["briefing"] is not None and entry["chosenFrom"] is None:
            problems.append(f"{mid}: the ledger names no source file")
    if problems:
        print("briefing ledger is out of date:", file=sys.stderr)
        for line in problems[:12]:
            print(f"  {line}", file=sys.stderr)
        return 1
    print(
        f"OK: {len(sprawl_ids)} sprawl briefings match the ledger"
        f" ({sum(1 for v in record['missions'].values() if v['disagrees'])} with disagreeing candidates)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
