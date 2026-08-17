"""tools/build_dashboard.py — Single source of truth for dashboard stats.

Reads canonical game data and writes a small set of JSON files
under ``dashboard/data/`` that the static dashboard HTML pages can
``fetch()`` at runtime.  Run from the repo root::

    python3 tools/build_dashboard.py
    # or (uses the prototype venv for any Python-side parsing)
    prototype/.venv/bin/python tools/build_dashboard.py

Outputs (overwritten in place):

    dashboard/data/combat_stats.json   — ICE, effects, programs, mode, PPL/ZDR
    dashboard/data/library_stats.json  — catalog size, hook kinds, layers, tests
    dashboard/data/mission_stats.json  — arcs, chapters, characters, missions
    dashboard/data/journey_stats.json  — novice/veteran/heretic totals
    dashboard/data/design_system.json   — 5 pillars, anti-patterns, PPL/ZDR, tiers, world hierarchy
    dashboard/data/faction_stats.json   — 5 factions, reputation tiers, mechanics
    dashboard/data/data_index.json     — index of all available JSON files

The generator is intentionally pure-stdlib so it works under both
system Python and the prototype venv.  It only reads files that
already exist; missing files are reported and skipped, not failed.

This script does NOT regenerate the static dashboard HTML pages
themselves.  Each page has one or more ``<div data-stat="...">``
siblings and a tiny inline ``<script>fetch(...)</script>`` that
populates them at load time.  See dashboard/README.md for the full
page ↔ source map.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DASHBOARD_DATA = REPO / "dashboard" / "data"


# ---------------------------------------------------------------------------
# Loaders — each returns a dict suitable for JSON serialization.
# ---------------------------------------------------------------------------


def load_combat_stats(repo: Path) -> dict[str, object]:
    """Pull ICE types, skill effects, programs, and the RT-MS / PPL / ZDR labels."""
    out: dict[str, object] = {
        "ice_types_total": 0,
        "ice_types_grades": 0,
        "ice_grades_list": [],
        "skill_effects_total": 14,
        "skill_effect_animations_total": 0,
        "programs_total": 9,
        "combat_mode": "RT-MS",
        "ppl_version": "v1",
        "zdr_version": "v1",
        "_generated_at": "",
    }
    p = repo / "prototype" / "data" / "combat" / "ice_types.json"
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        if isinstance(data, dict):
            out["ice_types_total"] = len(data)
            out["ice_grades_list"] = list(data.keys())

    ep = repo / "prototype" / "src" / "wet_run" / "combat" / "effects.py"
    if ep.exists():
        src = ep.read_text(encoding="utf-8")
        funcs = re.findall(r"^def\s+\w+_animation\b", src, re.M)
        out["skill_effect_animations_total"] = len(funcs)
        m = re.search(r"SKILL_EFFECT_ANIMATIONS\s*=\s*\{([^}]+)\}", src, re.S)
        if m:
            keys = re.findall(r"SkillEffect\.(\w+)", m.group(1))
            if keys:
                out["skill_effects_total"] = len(keys)

    for cand in [
        repo / "prototype" / "data" / "programs.json",
        repo / "prototype" / "data" / "programs" / "programs.json",
    ]:
        if cand.exists():
            try:
                d = json.loads(cand.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                d = {}
            if isinstance(d, dict):
                out["programs_total"] = len(d)
            break
    return out


def load_library_stats(repo: Path) -> dict[str, object]:
    """Pull Derivative Library catalog + manifest counts (short stories + novelettes).

    Short stories and novelettes are counted and catalogued separately.
    """
    out: dict[str, object] = {
        "short_stories_en": 0,
        "short_stories_ko": 0,
        "novelettes_en": 0,
        "novelettes_ko": 0,
        "hook_kinds": 6,
        "hook_kind_names": [
            "narrative",
            "excerpt",
            "event",
            "combat",
            "item",
            "cinematic",
        ],
        "layers": 4,
        "tests_passing": 39,
        "code_lines_approx": 900,
        "_generated_at": "",
    }

    def _scan_dir(
        dir_path: Path,
    ) -> tuple[set[str], dict[str, dict[str, str]], dict[str, str], dict[str, str]]:
        """Scan a derivative subdirectory for EN/KO pairs.

        Returns (stems, titles, derivative_types, game_mission_ids).
        derivative_types maps stem -> 'short_story' or 'novelette' (from frontmatter).
        game_mission_ids maps stem -> mission id when the story is referenced by
        wet_run's missions.json (cross-project link, ADR-0042 + Phase α).
        """
        if not dir_path.exists():
            return set(), {}, {}, {}
        md_files = [f for f in dir_path.glob("*.md") if not f.name.endswith(".tone-prompt.md")]
        stems: set[str] = set()
        per_stem_titles: dict[str, dict[str, str]] = {}
        derivative_types: dict[str, str] = {}
        game_mission_ids: dict[str, str] = {}
        for f in md_files:
            name = f.name
            is_ko = name.endswith(".ko.md")
            stem = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", name)
            if is_ko:
                stem = stem[: -len(".ko.md")]
            else:
                stem = stem[: -len(".md")]
            stems.add(stem)
            title = stem.replace("_", " ").title()
            dtype = "short_story"
            gmi: str | None = None
            try:
                text = f.read_text(encoding="utf-8")
                lines = text.splitlines()
                head = lines[:200]
                fm_text = ""
                if head and head[0] == "---":
                    fm_lines = []
                    for line in head[1:]:
                        if line == "---":
                            break
                        fm_lines.append(line)
                    fm_text = "\n".join(fm_lines)
                fm_match = re.search(r"derivative_type:\s*(\S+)", fm_text)
                if fm_match:
                    dtype = fm_match.group(1).strip().strip('"')
                gmi_match = re.search(r"^game_mission_id:\s*(\S+)", fm_text, re.MULTILINE)
                if gmi_match:
                    gmi = gmi_match.group(1).strip().strip('"')
                for line in text.splitlines()[1:]:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
            except OSError:
                pass
            slot = per_stem_titles.setdefault(stem, {})
            slot["ko" if is_ko else "en"] = title
            derivative_types[stem] = dtype
            if gmi is not None and not is_ko:
                game_mission_ids[stem] = gmi
        return stems, per_stem_titles, derivative_types, game_mission_ids

    base = repo.parent / "Fiction" / "derivative" / "sprawl-trilogy"
    short_dir = base / "short-stories"
    novel_dir = base / "novelettes"

    # Fallback paths
    if not short_dir.exists():
        for cand in [
            repo / "Fiction" / "derivative" / "sprawl-trilogy" / "short-stories",
            Path("/Users/emilio/projects/Projects/Fiction")
            / "derivative"
            / "sprawl-trilogy"
            / "short-stories",
        ]:
            if cand.exists():
                short_dir = cand
                break
    if not novel_dir.exists():
        for cand in [
            repo / "Fiction" / "derivative" / "sprawl-trilogy" / "novelettes",
            Path("/Users/emilio/projects/Projects/Fiction")
            / "derivative"
            / "sprawl-trilogy"
            / "novelettes",
        ]:
            if cand.exists():
                novel_dir = cand
                break

    short_en_dir = short_dir / "en"
    short_ko_dir = short_dir / "ko"
    novel_en_dir = novel_dir / "en"
    novel_ko_dir = novel_dir / "ko"

    short_stems, short_titles, short_dtypes, short_gmis = _scan_dir(short_en_dir)
    short_ko_stems, short_ko_titles, short_ko_dtypes, _ = _scan_dir(short_ko_dir)
    short_stems |= short_ko_stems
    short_titles.update(short_ko_titles)
    short_dtypes.update(short_ko_dtypes)
    novel_stems, novel_titles, novel_dtypes, novel_gmis = _scan_dir(novel_en_dir)
    novel_ko_stems, novel_ko_titles, novel_ko_dtypes, _ = _scan_dir(novel_ko_dir)
    novel_stems |= novel_ko_stems
    novel_titles.update(novel_ko_titles)
    novel_dtypes.update(novel_ko_dtypes)

    all_dtypes = {**short_dtypes, **novel_dtypes}
    all_gmis = {**short_gmis, **novel_gmis}

    en_stems = set()
    ko_stems = set()
    for d in (short_en_dir, novel_en_dir):
        if d.exists():
            for f in d.glob("*.md"):
                stem = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", f.name)
                stem = re.sub(r"\.md$", "", stem)
                en_stems.add(stem)
    for d in (short_ko_dir, novel_ko_dir):
        if d.exists():
            for f in d.glob("*.md"):
                stem = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", f.name)
                stem = re.sub(r"\.ko\.md$", "", stem)
                ko_stems.add(stem)

    # Count by derivative_type (from frontmatter), not directory
    novel_en = sum(1 for s in en_stems if all_dtypes.get(s) == "novelette")
    novel_ko = sum(1 for s in ko_stems if all_dtypes.get(s) == "novelette")
    short_en = sum(1 for s in en_stems if all_dtypes.get(s) == "short_story")
    short_ko = sum(1 for s in ko_stems if all_dtypes.get(s) == "short_story")

    out["short_stories_en"] = short_en
    out["short_stories_ko"] = short_ko
    out["novelettes_en"] = novel_en
    out["novelettes_ko"] = novel_ko

    # Combined catalog — use frontmatter type
    all_stems = short_stems | novel_stems
    all_titles = {**short_titles, **novel_titles}
    all_gmis_dict = all_gmis
    out["stories_with_mission_link"] = len(all_gmis_dict)
    out["catalog_entries"] = len(all_stems)
    out["catalog_entries_list"] = [
        {
            "stem": s,
            "type": all_dtypes.get(s, "short_story"),
            "title_en": all_titles.get(s, {}).get("en", s.replace("_", " ").title()),
            "title_ko": all_titles.get(s, {}).get("ko", ""),
            "game_mission_id": all_gmis.get(s),
        }
        for s in sorted(all_stems)
    ]
    return out


def load_mission_stats(repo: Path) -> dict[str, object]:
    """Pull mission / chapter / character / event / reaction counts.

    Wires metadata → novel → story events → stages into the
    dashboard so the HTML stat-pills stay in lockstep with the
    actual disk state.

    Stat keys (each consumed by ``dashboard/missions.html``):
      - missions: int — total missions in missions.json
      - stories / html_files / en_files / ko_files / complete_pairs:
        short-stories catalogue
      - arcs / chapters: character arc JSONs
      - characters: list[str] — main jockeys
      - aftermath_events: int — Phase 6+ content (12)
      - reactions: int — NPC reactions (25)
      - reaction_characters: list[str] — characters with reactions (6)
      - event_triggers: list[str] — all EventTrigger enum values (9)
      - total_rewards: int — total StoryReward items across events
      - hub_visit_events: int — events with hub_visited trigger
    """
    out: dict[str, object] = {
        "missions": 0,
        "stories": 0,
        "html_files": 0,
        "en_files": 0,
        "ko_files": 0,
        "en_only": 0,
        "ko_only": 0,
        "complete_pairs": 0,
        "quotes": 0,
        "references": 0,
        "arcs": 0,
        "chapters": 0,
        "characters": [],
        "aftermath_events": 0,
        "reactions": 0,
        "reaction_characters": [],
        "event_triggers": [],
        "total_rewards": 0,
        "hub_visit_events": 0,
        "_generated_at": "",
    }
    mp = repo / "prototype" / "data" / "missions" / "missions.json"
    if mp.exists():
        try:
            d = json.loads(mp.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                out["missions"] = len(d)
        except json.JSONDecodeError:
            pass

    # Phase 6+: aftermath events, reactions, rewards.
    ap = repo / "prototype" / "data" / "story" / "aftermath.json"
    if ap.exists():
        try:
            am = json.loads(ap.read_text(encoding="utf-8"))
            if isinstance(am, dict):
                out["aftermath_events"] = len(am)
                out["total_rewards"] = sum(
                    len(v.get("rewards", [])) for v in am.values() if isinstance(v, dict)
                )
                out["hub_visit_events"] = sum(
                    1
                    for v in am.values()
                    if isinstance(v, dict) and v.get("trigger") == "hub_visited"
                )
        except json.JSONDecodeError:
            pass

    rp = repo / "prototype" / "data" / "story" / "reactions.json"
    if rp.exists():
        try:
            rj = json.loads(rp.read_text(encoding="utf-8"))
            if isinstance(rj, dict):
                out["reactions"] = len(rj)
                out["reaction_characters"] = sorted(
                    {
                        v.get("character", "")
                        for v in rj.values()
                        if isinstance(v, dict) and v.get("character")
                    }
                )
        except json.JSONDecodeError:
            pass

    # Discover all EventTrigger values from the enum source.
    out["event_triggers"] = _collect_event_trigger_names(repo)

    short = repo.parent / "Fiction" / "derivative" / "sprawl-trilogy" / "short-stories"
    if not short.exists():
        for cand in [
            repo / "Fiction" / "derivative" / "sprawl-trilogy" / "short-stories",
            Path("/Users/emilio/projects/Projects/Fiction")
            / "derivative"
            / "sprawl-trilogy"
            / "short-stories",
        ]:
            if cand.exists():
                short = cand
                break
    if short.exists():
        md_files = list(short.glob("*.md"))
        en_files = [f for f in md_files if ".ko." not in f.name]
        ko_files = [f for f in md_files if ".ko." in f.name]
        stems_en: set[str] = set()
        for f in en_files:
            s = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", f.name)
            s = re.sub(r"\.md$", "", s)
            stems_en.add(s)
        stems_ko: set[str] = set()
        for f in ko_files:
            s = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", f.name)
            s = re.sub(r"\.ko\.md$", "", s)
            stems_ko.add(s)
        out["stories"] = len(stems_en | stems_ko)
        out["html_files"] = len(md_files)
        out["en_files"] = len(en_files)
        out["ko_files"] = len(ko_files)
        out["en_only"] = len(stems_en - stems_ko)
        out["ko_only"] = len(stems_ko - stems_en)
        out["complete_pairs"] = len(stems_en & stems_ko)
        out["quotes"] = out["complete_pairs"]
        out["references"] = out["complete_pairs"]
    for c in _character_ids_from_facts(repo):
        p = repo / "prototype" / "data" / "story" / "chapters" / f"{c}.json"
        if not p.exists():
            p = repo / "prototype" / "data" / "chapters" / f"{c}.json"
        if p.exists():
            out["arcs"] += 1
            out["chapters"] += 1
    out["characters"] = [c.capitalize() for c in _character_ids_from_facts(repo)]
    return out


def _character_ids_from_facts(repo: Path) -> tuple[str, ...]:
    """Return the character ids from game_facts.json (single source of truth).

    Phase 14 expanded the cast from 4 main jockeys to 27 named characters;
    this function replaces the hardcoded ``("case", "sil", "kas", "suit")``
    tuple that previously capped the character counter.
    """
    facts_path = repo / "prototype" / "data" / "game_facts.json"
    if not facts_path.exists():
        return ("case", "sil", "kas", "suit")
    try:
        facts = json.loads(facts_path.read_text(encoding="utf-8"))
        ids = facts.get("character_ids", [])
        return tuple(ids) if ids else ("case", "sil", "kas", "suit")
    except (json.JSONDecodeError, OSError):
        return ("case", "sil", "kas", "suit")


def _collect_event_trigger_names(repo: Path) -> list[str]:
    """Extract all EventTrigger enum values from the event_story module.

    Reads the source file rather than importing (avoids the entire
    game's import chain during this build step). Falls back to a
    hard-coded list if the source can't be found / parsed.
    """
    import re as _re

    fallback = [
        "npc_choice",
        "npc_greeting",
        "combat_end",
        "node_enter",
        "story_milestone",
        "chapter_complete",
        "vendor_unlocked",
        "hub_visited",
        "dialogue_completed",
    ]
    src = repo / "prototype" / "src" / "wet_run" / "engine" / "event_story.py"
    if not src.exists():
        return fallback
    try:
        text = src.read_text(encoding="utf-8")
    except OSError:
        return fallback
    # Match the EventTrigger class body and pull `NAME = "value"` lines.
    class_re = _re.compile(
        r"^class\s+EventTrigger\b.*?:\s*$(.*?)(?=^class\s|\Z)",
        _re.MULTILINE | _re.DOTALL,
    )
    member_re = _re.compile(r"^\s{4}(\w+)\s*=\s*['\"]([^'\"]+)['\"]", _re.MULTILINE)
    match = class_re.search(text)
    if not match:
        return fallback
    return [v for _, v in member_re.findall(match.group(1))] or fallback


def load_event_dialogues_stats(repo: Path) -> dict[str, object]:
    """Count NPCs / dialogues / lines / choices in event_dialogues.json.

    Drives the event-viewer stat pills in ``dashboard/story.html``.
    """
    out: dict[str, object] = {
        "npcs": 0,
        "dialogues": 0,
        "lines": 0,
        "choices": 0,
        "characters": [],
        "_generated_at": "",
    }
    p = repo / "design" / "story" / "event_dialogues.json"
    if not p.exists():
        return out
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return out
    if not isinstance(data, dict):
        return out

    npcs = data.get("npcs", {})
    if isinstance(npcs, dict):
        out["npcs"] = len(npcs)
        out["characters"] = sorted(npcs.keys())

    dialogues = data.get("dialogues", {})
    if isinstance(dialogues, dict):
        out["dialogues"] = len(dialogues)
        for d in dialogues.values():
            if not isinstance(d, dict):
                continue
            out["lines"] += len(d.get("lines", []) or [])
            out["choices"] += sum(
                len(line.get("choices", []) or [])
                for line in (d.get("lines", []) or [])
                if isinstance(line, dict)
            )
    elif isinstance(dialogues, list):
        # Legacy: dialogues as list of dicts.
        out["dialogues"] = len(dialogues)
        for d in dialogues:
            if not isinstance(d, dict):
                continue
            out["lines"] += len(d.get("lines", []) or [])
            out["choices"] += sum(
                len(line.get("choices", []) or [])
                for line in (d.get("lines", []) or [])
                if isinstance(line, dict)
            )
    return out


def load_stages_stats(repo: Path) -> dict[str, object]:
    """Count stages / transitions / chapter-states from the run module.

    Mirrors ``dashboard/stages.html`` so the dashboard always reflects
    the real state of the run state machine.
    """
    out: dict[str, object] = {
        "stages": 0,
        "stage_enum": 0,
        "transitions": 0,
        "missions": 0,
        "chapter_states": 0,
        "objectives": 0,
        "_generated_at": "",
    }

    # Stage enum count
    src = repo / "prototype" / "src" / "wet_run" / "run" / "state.py"
    if src.exists():
        try:
            text = src.read_text(encoding="utf-8")
        except OSError:
            text = ""
        # Use a regex-based parser that's robust to comments and
        # arbitrary whitespace.
        import re as _re

        pattern = _re.compile(
            r"^class\s+(\w+).*?:\s*$(.*?)(?=^class\s|\Z)",
            _re.MULTILINE | _re.DOTALL,
        )
        member_re = _re.compile(r"^\s{4}(\w+)\s*=\s*['\"]([^'\"]+)['\"]", _re.MULTILINE)

        for match in pattern.finditer(text):
            class_name = match.group(1)
            body = match.group(2)
            members = member_re.findall(body)
            if class_name == "Stage":
                out["stages"] = len(members)
                out["stage_enum"] = len(members)
            elif class_name == "ChapterState":
                out["chapter_states"] = len(members)
            elif class_name == "ObjectiveKind":
                out["objectives"] = len(members)

    # Transitions: count `STAGE_TRANSITIONS` literal (fallback: derive
    # from Stage-flow JSON if it exists).
    missions_p = repo / "prototype" / "data" / "missions" / "missions.json"
    if missions_p.exists():
        try:
            d = json.loads(missions_p.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                out["missions"] = len(d)
        except json.JSONDecodeError:
            pass
    out["transitions"] = out["stages"]  # rough 1:1 estimate

    return out


def load_run_stats(repo: Path) -> dict[str, object]:
    """Walk prototype/src/run/state.py for Stage / ChapterState / Phase enums.

    The Stage enum lists every in-game stage (10 entries: PENDING /
    MEET_NPC / EXTRACT_DATA / DEFEAT_ICE / JACK_OUT / REWARD /
    DEBRIEF / COMPLETE / DEATH_RESTART / FAILED), of which
    stage_structure.json only enumerates 9 (DEBRIEF is marked
    optional in the source).  Pulling the enum straight from
    state.py keeps the dashboard honest when the implementation
    grows new phases.
    """
    out: dict[str, object] = {
        "stage_enum_count": 0,
        "stage_enum_names": [],
        "stage_optional": [],
        "chapter_state_enum_count": 0,
        "chapter_state_enum_names": [],
        "objective_kind_enum_count": 0,
        "objective_kind_enum_names": [],
        "source": "",
        "_generated_at": "",
    }
    p = repo / "prototype" / "src" / "wet_run" / "run" / "state.py"
    if not p.exists():
        return out
    out["source"] = str(p.relative_to(repo))
    src = p.read_text(encoding="utf-8")

    def _enum_block(name: str) -> list[str]:
        m = re.search(
            rf"^class\s+{name}\s*\(\s*StrEnum\s*\):.*?(?=^\nclass\s+\w+|\Z)",
            src,
            re.M | re.S,
        )
        if not m:
            return []
        block = m.group(0)
        return re.findall(r"^\s+([A-Z][A-Z0-9_]*)\s*=\s*\"[a-z0-9_]+\"", block, re.M)

    out["stage_enum_names"] = _enum_block("Stage")
    out["stage_enum_count"] = len(out["stage_enum_names"])  # type: ignore[assignment]
    # Per docstring: DEBRIEF is optional.  Mark any literal that the
    # docstring says is optional / conditional.
    optional = []
    for name in out["stage_enum_names"]:  # type: ignore[union-attr]
        # Match 'Foo (optional)' or '(debatable)' / '(conditional)'.
        m = re.search(
            rf"^\s+{name}\s*=\s*\"[a-z_]+\"\s*#\s*(optional|conditional|debatable)",
            src,
            re.M,
        )
        if m:
            optional.append(name)
    out["stage_optional"] = optional

    out["chapter_state_enum_names"] = _enum_block("ChapterState")
    out["chapter_state_enum_count"] = len(out["chapter_state_enum_names"])  # type: ignore[assignment]
    out["objective_kind_enum_names"] = _enum_block("ObjectiveKind")
    out["objective_kind_enum_count"] = len(out["objective_kind_enum_names"])  # type: ignore[assignment]
    return out


def load_character_stats(repo: Path) -> dict[str, object]:
    """Pull canonical character data from design/story/characters.md + CHARACTER_PATHS.md.

    Two-source merge:
    - characters.md (3 canonical: case/sil/kas) — detailed attributes
      from '| **<key>** | <val> |' rows under '## N. <name> (<EN>) — Novice/Veteran/Heretic'
    - CHARACTER_PATHS.md (all 9) — archetype/POV/motivation/tone/deck
      from the §1.1 table: '| `id` | 이름 | 아키타입 | 시점 | 동기 | 톤 | Deck Tier |'

    Merge: the 3 canonical characters get full attributes (detailed + brief).
    The 6 extension characters (suit/wigan/angie/sally/3jane/neuromancer) get
    only the brief row from CHARACTER_PATHS.md.
    """
    out: dict[str, object] = {
        "characters": [],
        "source": "",
        "sources": [],
        "_generated_at": "",
    }
    brief_entries = _load_brief_character_entries(repo, out)
    detailed_entries = _load_detailed_character_entries(repo, out)
    final_chars: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for char_id, det in detailed_entries.items():
        merged = dict(det)
        if char_id in brief_entries:
            brief_attrs = dict(brief_entries[char_id]["attributes"])  # type: ignore[arg-type]
            for k, v in brief_attrs.items():
                if k not in merged["attributes"]:  # type: ignore[operator]
                    merged["attributes"][k] = v  # type: ignore[index]
        merged["id"] = char_id
        final_chars.append(merged)
        seen_ids.add(char_id)
    for char_id, brief in brief_entries.items():
        if char_id in seen_ids:
            continue
        final_chars.append(brief)
    out["characters"] = final_chars
    out["source"] = " + ".join(out["sources"]) if out["sources"] else "none"
    out["total_characters"] = len(final_chars)
    return out


def _load_brief_character_entries(
    repo: Path, out: dict[str, object]
) -> dict[str, dict[str, object]]:
    """Parse CHARACTER_PATHS.md §1.1 table — archetype/POV/motivation/tone/deck for 9 chars."""
    brief_entries: dict[str, dict[str, object]] = {}
    cp_path = repo / "design" / "CHARACTER_PATHS.md"
    if not cp_path.exists():
        return brief_entries
    out["sources"].append(str(cp_path.relative_to(repo)))
    text = cp_path.read_text(encoding="utf-8")
    section = _extract_section_text(text, "1.1 캐릭터 구성")
    if section is None:
        return brief_entries
    row_re = re.compile(
        r"^\|\s*`(?P<id>[^`]+)`\s*\|"
        r"\s*(?P<name_ko>[^|]+?)\s*\|"
        r"\s*(?P<archetype>[^|]+?)\s*\|"
        r"\s*(?P<pov>[^|]+?)\s*\|"
        r"\s*(?P<motivation>[^|]+?)\s*\|"
        r"\s*(?P<tone>[^|]+?)\s*\|"
        r"\s*(?P<deck>[^|]+?)\s*\|\s*$",
        re.M,
    )
    arc_key_map = {
        "Novice": "novice",
        "Veteran": "veteran",
        "Heretic": "heretic",
        "Corporate": "suit",
        "Vodou Construct": "wigan",
        "Loa Receiver": "angie",
        "Market Operator": "sally",
        "Family Heir": "3jane",
        "Merged AI": "neuromancer",
    }
    for m in row_re.finditer(section):
        char_id = m.group("id").strip()
        archetype = m.group("archetype").strip()
        arc = arc_key_map.get(archetype, char_id)
        brief_entries[char_id] = {
            "id": char_id,
            "name_ko": m.group("name_ko").strip(),
            "name_en": "3Jane" if char_id == "3jane" else char_id.capitalize(),
            "arc": arc,
            "arc_label": archetype,
            "attributes": {
                "시점": m.group("pov").strip(),
                "동기": m.group("motivation").strip(),
                "톤": m.group("tone").strip(),
                "데크": m.group("deck").strip(),
                "아키타입": archetype,
            },
        }
    return brief_entries


def _extract_section_text(text: str, heading_keyword: str) -> str | None:
    """Extract text from '### <keyword>...' until the next '###' heading or EOF."""
    pattern = re.compile(
        r"^###\s+" + re.escape(heading_keyword) + r".*?(?=^###\s+|\Z)",
        re.M | re.S,
    )
    m = pattern.search(text)
    return m.group(0) if m else None


def _load_detailed_character_entries(
    repo: Path, out: dict[str, object]
) -> dict[str, dict[str, object]]:
    """Parse characters.md — detailed attributes for case/sil/kas."""
    detailed_entries: dict[str, dict[str, object]] = {}
    md_path = repo / "design" / "story" / "characters.md"
    if not md_path.exists():
        return detailed_entries
    out["sources"].append(str(md_path.relative_to(repo)))
    text = md_path.read_text(encoding="utf-8")
    section_re = re.compile(
        r"^##\s+\d+\.\s+([^\n]+?)\s*\(([^)]+)\)\s*[—-]\s*(Novice|Veteran|Heretic)",
        re.M,
    )
    matches = list(section_re.finditer(text))
    arc_to_key = {"Novice": "novice", "Veteran": "veteran", "Heretic": "heretic"}
    name_to_id = {
        "Case": "novice",
        "Sil": "veteran",
        "Kas": "heretic",
        "케이": "novice",
        "실": "veteran",
        "카스": "heretic",
    }
    row_re = re.compile(
        r"\s*\|\s*\*\*(?P<k>[^*]+)\*\*\s*\|\s*(?P<v>[^|]+?)\s*\|\s*$",
    )
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        name_ko = m.group(1).strip()
        name_en = m.group(2).strip()
        char_id = name_to_id.get(name_en) or name_to_id.get(name_ko)
        if not char_id:
            continue
        attributes: dict[str, object] = {}
        for line in body.splitlines():
            row = row_re.match(line)
            if not row:
                continue
            key = row.group("k").strip().lower().replace(" ", "_")
            val = row.group("v").strip().strip("*")
            attributes[key] = val
        detailed_entries[char_id] = {
            "name_ko": name_ko,
            "name_en": name_en,
            "arc": arc_to_key[m.group(3)],
            "arc_label": m.group(3),
            "attributes": attributes,
        }
    return detailed_entries


def load_index_stats(repo: Path) -> dict[str, object]:
    """Top-level sidebar / Project Status cards on dashboard/index.html."""
    out: dict[str, object] = {
        "tests_total": 0,
        "tests_passing": True,
        "story_lines_total": 0,
        "npcs_unique": 0,
        "stages_per_run": 9,
        "transitions": 8,
        "missions": 0,
        "_generated_at": "",
    }
    # Use pytest --collect-only when available for an accurate count.
    tests_dir = repo / "prototype" / "tests"
    if tests_dir.exists():
        # Cheap, fast, cross-platform: spawn the prototype venv's pytest.
        import subprocess

        venv_py = repo / "prototype" / ".venv" / "bin" / "python"
        if not venv_py.exists():
            venv_py = repo / "prototype" / ".venv" / "Scripts" / "python.exe"  # type: ignore[assignment]  # noqa
        if venv_py.exists():
            try:
                res = subprocess.run(
                    [str(venv_py), "-m", "pytest", str(tests_dir), "--collect-only", "-q"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                m = re.search(r"(\d+)\s+tests?\s+collected", res.stdout)
                if m:
                    out["tests_total"] = int(m.group(1))
                    out["tests_passing"] = "passed" in res.stdout.lower()
            except (OSError, subprocess.SubprocessError):
                pass
    if out["tests_total"] == 0 and tests_dir.exists():
        # Fallback: count def test_* across all test files (less accurate
        # but never zero).
        for f in tests_dir.rglob("test_*.py"):
            src = f.read_text(encoding="utf-8")
            out["tests_total"] += len(re.findall(r"^\s*def test_\w+", src, re.M))

    pro = repo / "design" / "story" / "prologue_data.json"
    if pro.exists():
        try:
            d = json.loads(pro.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            d = {}
        if isinstance(d, dict):
            for sc in d.get("scenes", []):
                if isinstance(sc, dict):
                    out["story_lines_total"] += len(sc.get("lines", []) or [])
            for ends in (d.get("endings") or {}).values():
                if isinstance(ends, list):
                    for e in ends:
                        if isinstance(e, dict):
                            out["story_lines_total"] += len(e.get("lines", []) or [])

    evt = repo / "design" / "story" / "event_dialogues.json"
    if evt.exists():
        try:
            d = json.loads(evt.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            d = {}
        if isinstance(d, dict) and isinstance(d.get("npcs"), dict):
            out["npcs_unique"] = len(d["npcs"])

    # Missions: prefer the live missions.json (canonical source) over
    # the legacy stage_structure.json snapshot. Fall back to the snapshot
    # only when the live file is missing.
    missions_p = repo / "prototype" / "data" / "missions" / "missions.json"
    if missions_p.exists():
        try:
            d = json.loads(missions_p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            d = {}
        if isinstance(d, dict):
            out["missions"] = len(d)
    if out["missions"] == 0:
        stg = repo / "design" / "systems" / "stage_structure.json"
        if stg.exists():
            try:
                d = json.loads(stg.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                d = {}
            if isinstance(d, dict):
                out["stages_per_run"] = len(d.get("stages", []) or [])
                out["transitions"] = len(d.get("transitions", []) or [])
                out["missions"] = len(d.get("missions", []) or [])
    return out


def load_cyberspace_stats(repo: Path) -> dict[str, object]:
    """Walk worlds.json + matrix/node.py to keep cyberspace cards honest."""
    out: dict[str, object] = {
        "worlds": 0,
        "sectors": 0,
        "servers": 0,
        "node_kinds": 0,
        "zone_depths": 0,
        "world_names": [],
        "_generated_at": "",
    }
    p = repo / "prototype" / "data" / "cyberspace" / "worlds.json"
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            d = {}
        if isinstance(d, dict):
            worlds = d.get("worlds", {})
            if isinstance(worlds, dict):
                out["worlds"] = len(worlds)
                out["world_names"] = [
                    w.get("name", k) for k, w in worlds.items() if isinstance(w, dict)
                ]
                out["sectors"] = sum(
                    len(w.get("sectors", {})) for w in worlds.values() if isinstance(w, dict)
                )
                out["servers"] = sum(
                    len(s.get("servers", []))
                    for w in worlds.values()
                    if isinstance(w, dict)
                    for s in w.get("sectors", {}).values()
                    if isinstance(s, dict)
                )
    nk = repo / "prototype" / "src" / "wet_run" / "matrix" / "node.py"
    if nk.exists():
        src = nk.read_text(encoding="utf-8")
        out["node_kinds"] = len(re.findall(r"^\s+([A-Z_]+)\s*=\s*\"[a-z_]+\"\s*$", src, re.M))
        for cls_name in ("class NodeKind", "class ZoneDepth"):
            m = re.search(
                rf"{cls_name}\(StrEnum\):.*?(?=\n\nclass |\Z)",
                src,
                re.S,
            )
            if m:
                count = len(re.findall(r"^\s+([A-Z_]+)\s*=\s*\"[a-z_]+\"", m.group(0), re.M))
                if cls_name == "class NodeKind":
                    out["node_kinds"] = count
                else:
                    out["zone_depths"] = count
    return out


def load_journey_stats(repo: Path) -> dict[str, object]:
    """Per-character journey totals (novice / veteran / heretic).

    Pulls final credits / missions / grade / deck-progression from
    the journey markdown files when present; otherwise falls back to
    the original hand-crafted defaults (20,050 / 27,500 / 20,100 cr).
    """
    out: dict[str, object] = {
        "novice": {
            "credits": 20050,
            "missions": 0,
            "deaths": 0,
            "final_grade": 0,
            "deck_progression": "",
        },
        "veteran": {
            "credits": 27500,
            "missions": 0,
            "deaths": 0,
            "final_grade": 0,
            "deck_progression": "",
        },
        "heretic": {
            "credits": 20100,
            "missions": 0,
            "deaths": 0,
            "final_grade": 0,
            "deck_progression": "",
        },
        "_generated_at": "",
    }
    path = repo / "dashboard" / "stories" / "journey"
    char_map = {"novice": "novice.md", "veteran": "veteran.md", "heretic": "heretic.md"}
    for char_key, filename in char_map.items():
        p = path / filename
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8")
        slot = out[char_key]
        m = re.search(r"총 누적 credits\s*\|\s*\*\*([0-9,]+)\*\*", src)
        if m:
            slot["credits"] = int(m.group(1).replace(",", ""))
        m = re.search(r"총 완료 미션\s*\|\s*\*\*(\d+)/(\d+)\*\*", src)
        if m:
            slot["missions"] = int(m.group(2))
        m = re.search(r"최종 등급\s*\|\s*\*?(\d+)\*?", src)
        if m:
            slot["final_grade"] = int(m.group(1))
        m = re.search(r"핸드폰 등급 추정\s*\|\s*([^\n]+)", src)
        if m:
            slot["deck_progression"] = m.group(1).strip().strip("**").strip()
    return out


def load_faction_stats(repo: Path) -> dict[str, object]:
    """Extract faction system data from source.

    Sources:
    - matrix/node.py: Faction enum (5 factions)
    - run/reputation.py: tier thresholds and mechanics
    """
    out: dict[str, object] = {
        "factions": [],
        "tier_thresholds": [],
        "max_delta_per_event": 25,
        "_generated_at": "",
    }

    # Faction enum from matrix/node.py
    nk = repo / "prototype" / "src" / "wet_run" / "matrix" / "node.py"
    if nk.exists():
        try:
            src = nk.read_text(encoding="utf-8")
            m = re.search(
                r"class\s+Faction\s*\([^)]+\):.*?(?=^class\s|\Z)",
                src,
                re.S | re.M,
            )
            if m:
                faction_re = re.compile(
                    r"^\s+([A-Z_][A-Z0-9_]*)\s*=\s*\"([a-z_]+)\"",
                    re.M,
                )
                for name, val in faction_re.findall(m.group(0)):
                    out["factions"].append({"name": name, "id": val})
        except OSError:
            pass

    # Tier thresholds and mechanics from run/reputation.py
    rp = repo / "prototype" / "src" / "wet_run" / "run" / "reputation.py"
    if rp.exists():
        try:
            src = rp.read_text(encoding="utf-8")
            # Tier thresholds
            m = re.search(
                r"TIER_THRESHOLDS\s*:\s*list\[tuple\[int,\s*str\]\]\s*=\s*\[(.*?)\]",
                src,
                re.S,
            )
            if m:
                tier_re = re.compile(r"\(\s*(-?\d+)\s*,\s*\"([A-Z_]+)\"\s*\)")
                for threshold, label in tier_re.findall(m.group(1)):
                    out["tier_thresholds"].append(
                        {
                            "threshold": int(threshold),
                            "label": label,
                        }
                    )
            m2 = re.search(r"MAX_DELTA_PER_EVENT\s*=\s*(\d+)", src)
            if m2:
                out["max_delta_per_event"] = int(m2.group(1))
        except OSError:
            pass

    return out


def load_design_system(repo: Path) -> dict[str, object]:
    """Build design_system.json from canonical game data + design docs.

    Aggregates:
    - 5 Design Pillars (from design/pillars.md)
    - Anti-patterns list
    - PPL/ZDR difficulty system
    - Tier system (T1-T6, 9 programs)
    - Mission distributions (by pillar / arc / zone / grade range)
    - World hierarchy (2 worlds / 4 sectors / 6 servers)
    - Alarm system (6 levels)
    """
    out: dict[str, object] = {
        "design_pillars": [
            {
                "id": 1,
                "name": "The Run",
                "tagline_ko": "한 번의 침투, 명확한 끝",
                "tagline_en": "One run, one job, one clear ending",
                "color": "#66ffcc",
                "mechanics_ko": ["job 단위 진행", "PPL/ZDR 난이도 명시", "Story Events"],
                "anti_these_ko": ["무한 진행 모드", "일일 미션", "강제 진입"],
            },
            {
                "id": 2,
                "name": "The Matrix",
                "tagline_ko": "사이버스페이스가 유일한 시각적 공간",
                "tagline_en": "Cyberspace is the only visual space",
                "color": "#00ccff",
                "mechanics_ko": [
                    "meatspace 절대 시각화 안함",
                    "ASCII portrait는 cyberspace 안의 존재만",
                ],
                "anti_these_ko": ["meatspace 메인 게임", "현실 세계 직접 묘사"],
            },
            {
                "id": 3,
                "name": "The Flatline",
                "tagline_ko": "죽음에 진짜 무게",
                "tagline_en": "Death has real weight",
                "color": "#ff5555",
                "mechanics_ko": ["평시 캐릭터 Loss", "리스폰 없음", "메타 진행은 공격적이지 않음"],
                "anti_these_ko": ["리스폰/부활", "가벼운 죽음 페널티", "death = positive"],
            },
            {
                "id": 4,
                "name": "The Build",
                "tagline_ko": "런 사이 진행은 더 좋은 도구로",
                "tagline_en": "Between runs, better tools",
                "color": "#ffaa55",
                "mechanics_ko": [
                    "레벨업 = 아이템/장비 티어 (T1-T6)",
                    "combat 강도는 program tier에 비례",
                ],
                "anti_these_ko": ["스탯 누적", "XP/레벨 시스템", "지속적 난이도 하락"],
            },
            {
                "id": 5,
                "name": "The Style",
                "tagline_ko": "사이버펑크 미학 — 네온, 크롬, 가죽",
                "tagline_en": "Cyberpunk aesthetics — neon, chrome, leather",
                "color": "#9b59b6",
                "mechanics_ko": ["깁슨 톤 정확히", "거칠고 비관적", "mediated world"],
                "anti_these_ko": ["미니멀/유토피아 미래", "Cyberpunk 2077 톤", "화려한 비주얼"],
            },
        ],
        "anti_patterns": [
            {"id": "AP-1", "name": "Loot Grind", "desc_ko": "무한히 강한 적 = 무한히 좋은 loot"},
            {"id": "AP-2", "name": "Multiplayer/Social", "desc_ko": "1인칭 솔로 경험"},
            {"id": "AP-3", "name": "Skins/Cosmetics", "desc_ko": "시각적 다양성보다 의미"},
            {"id": "AP-4", "name": "Daily Login", "desc_ko": "게임이 사용자 시간을 빼앗지 않음"},
            {"id": "AP-5", "name": "Infinite Scaling", "desc_ko": "적이 계속 강해지는 시스템"},
            {"id": "AP-6", "name": "Prestige", "desc_ko": "반복 플레이를 위한 인위적 시스템"},
            {"id": "AP-7", "name": "Mobile/F2P", "desc_ko": "PC/Mac 솔로 게임"},
        ],
        "core_loop": {
            "macro_ko": "Hub → Run(매트릭스 진입) → Extraction/Death → Result → Hub",
            "stages": [
                "PENDING",
                "BRIEFING",
                "TRAVEL",
                "MEET_NPC",
                "EXTRACT_DATA",
                "BYPASS_SECURITY",
                "DEFEAT_ICE",
                "JACK_OUT",
                "REWARD",
                "DEBRIEF",
                "COMPLETE",
                "DEATH_RESTART",
                "FAILED",
                "SALVATION_EPILOGUE",
            ],
            "micro_ko": "Navigation → Node 발견 → Decision → Action → Combat(RT-MS) → State Update",
            "alarm_levels": [0, 1, 2, 3, 4, 5],
            "combat": {
                "name": "RT-MS (Real-Time Missile Storm)",
                "desc_ko": "실시간 자동 공격 + 메뉴 스킬",
                "tick_rate": "1 attack / 2초, 양쪽 동시",
                "skill_count": 14,
                "skill_effect_animations": 15,
                "ice_types": 41,
                "programs_count": 9,
            },
        },
        "difficulty_system": {
            "ppl_zdr": {
                "desc_ko": "전투 전/중 위험 명시화 시스템",
                "ppl_desc_ko": "Player Power Level — 자키의 현재 힘 (데크/프로그램 티어 합산)",
                "zdr_desc_ko": "Zone Difficulty Rating — 현재 zone의 위험",
                "status": [
                    {"name": "SAFE", "ratio": "PPL > ZDR*1.5", "color": "#66ffcc"},
                    {"name": "MATCH", "ratio": "ZDR*0.8 < PPL <= ZDR*1.5", "color": "#00ccff"},
                    {"name": "TOUGH", "ratio": "ZDR*0.5 < PPL <= ZDR*0.8", "color": "#ffaa55"},
                    {"name": "DEADLY", "ratio": "ZDR*0.25 < PPL <= ZDR*0.5", "color": "#ff5555"},
                    {"name": "FUTILE", "ratio": "PPL <= ZDR*0.25", "color": "#ff0000"},
                ],
            },
            "grade_progression": {"grades": [1, 2, 3, 4, 5, 6], "max_tier": 6},
        },
        "tier_system": {
            "max_tier": 6,
            "programs_count": 9,
            "program_tiers": {},
        },
        "mission_distribution": {
            "by_pillar": {},
            "by_arc": {},
            "by_zone": {},
            "by_grade_range": {},
        },
        "world_hierarchy": {
            "worlds": [],
            "world_count": 0,
            "sector_count": 0,
            "server_count": 0,
            "zone_depths": 0,
        },
        "alarm_system": {
            "levels": [
                {"level": 0, "name_ko": "평온", "ice_ko": "없음", "risk_ko": "없음"},
                {"level": 1, "name_ko": "인지", "ice_ko": "기본 배치", "risk_ko": "낮음"},
                {"level": 2, "name_ko": "정찰", "ice_ko": "watchdog", "risk_ko": "중간"},
                {"level": 3, "name_ko": "추적", "ice_ko": "hellhound", "risk_ko": "높음"},
                {
                    "level": 4,
                    "name_ko": "黑色ICE",
                    "ice_ko": "black ICE, trace 진행",
                    "risk_ko": "매우 높음",
                },
                {
                    "level": 5,
                    "name_ko": "trace 완료",
                    "ice_ko": "flatline 임박",
                    "risk_ko": "치명적",
                },
            ],
        },
        "_source_files": [
            "design/pillars.md",
            "design/core_loop.md",
            "prototype/data/missions/missions.json",
            "prototype/data/programs/programs.json",
            "prototype/data/cyberspace/worlds.json",
        ],
    }

    # Tier system from programs
    prog_paths = [
        repo / "prototype" / "data" / "programs.json",
        repo / "prototype" / "data" / "programs" / "programs.json",
    ]
    for pp in prog_paths:
        if pp.exists():
            try:
                pd = json.loads(pp.read_text(encoding="utf-8"))
                if isinstance(pd, dict):
                    tier_map: dict[int, list[str]] = {}
                    for pname, pinfo in pd.items():
                        if isinstance(pinfo, dict):
                            t = pinfo.get("tier", 0)
                            tier_map.setdefault(t, []).append(pname)
                    out["tier_system"]["program_tiers"] = {
                        f"T{k}": v for k, v in sorted(tier_map.items())
                    }
            except (json.JSONDecodeError, OSError):
                pass
            break

    # Mission distributions
    mp = repo / "prototype" / "data" / "missions" / "missions.json"
    if mp.exists():
        try:
            md = json.loads(mp.read_text(encoding="utf-8"))
            if isinstance(md, dict):
                by_pillar: dict[str, int] = {}
                by_arc: dict[int, int] = {}
                by_zone: dict[str, int] = {}
                by_grade: dict[str, int] = {}
                for _k, v in md.items():
                    if not isinstance(v, dict):
                        continue
                    story = v.get("story", {})
                    pillar = (
                        story.get("pillar", "unknown") if isinstance(story, dict) else "unknown"
                    )
                    arc = v.get("arc", 0)
                    zone = v.get("zone", "unknown")
                    g_min = v.get("grade_min", 0)
                    g_max = v.get("grade_max", 0)
                    by_pillar[pillar] = by_pillar.get(pillar, 0) + 1
                    by_arc[arc] = by_arc.get(arc, 0) + 1
                    by_zone[zone] = by_zone.get(zone, 0) + 1
                    gk = f"grade_{g_min}-{g_max}"
                    by_grade[gk] = by_grade.get(gk, 0) + 1
                out["mission_distribution"]["by_pillar"] = by_pillar
                out["mission_distribution"]["by_arc"] = {
                    str(k): v for k, v in sorted(by_arc.items())
                }
                out["mission_distribution"]["by_zone"] = dict(sorted(by_zone.items()))
                out["mission_distribution"]["by_grade_range"] = dict(sorted(by_grade.items()))
        except (json.JSONDecodeError, OSError):
            pass

    # World hierarchy
    wp = repo / "prototype" / "data" / "cyberspace" / "worlds.json"
    if wp.exists():
        try:
            wd = json.loads(wp.read_text(encoding="utf-8"))
            if isinstance(wd, dict):
                worlds = wd.get("worlds", {})
                if isinstance(worlds, dict):
                    out["world_hierarchy"]["world_count"] = len(worlds)
                    out["world_hierarchy"]["world_names"] = [
                        w.get("name", k) for k, w in worlds.items() if isinstance(w, dict)
                    ]
                    world_list: list[dict[str, object]] = []
                    sector_count = 0
                    server_count = 0
                    for wid, winfo in worlds.items():
                        if not isinstance(winfo, dict):
                            continue
                        sectors = winfo.get("sectors", {})
                        if not isinstance(sectors, dict):
                            continue
                        sector_list: list[dict[str, object]] = []
                        for sid, sinfo in sectors.items():
                            if not isinstance(sinfo, dict):
                                continue
                            servers = sinfo.get("servers", [])
                            sector_list.append(
                                {
                                    "id": sid,
                                    "name": sinfo.get("name", sid),
                                    "server_count": len(servers),
                                }
                            )
                            server_count += len(servers)
                            sector_count += 1
                        world_list.append(
                            {
                                "id": wid,
                                "name": winfo.get("name", wid),
                                "sectors": sector_list,
                            }
                        )
                    out["world_hierarchy"]["worlds"] = world_list
                    out["world_hierarchy"]["sector_count"] = sector_count
                    out["world_hierarchy"]["server_count"] = server_count
        except (json.JSONDecodeError, OSError):
            pass

    # Zone depths from matrix/node.py
    nk = repo / "prototype" / "src" / "wet_run" / "matrix" / "node.py"
    if nk.exists():
        try:
            src = nk.read_text(encoding="utf-8")
            m = re.search(
                r"class\s+ZoneDepth\s*\(\s*StrEnum\s*\):.*?(?=\n\nclass |\Z)",
                src,
                re.S,
            )
            if m:
                cnt = len(re.findall(r"^\s+[A-Z_]+\s*=\s*\"[a-z_]+\"", m.group(0), re.M))
                out["world_hierarchy"]["zone_depths"] = cnt
        except OSError:
            pass

    return out


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _stamp(d: dict[str, object]) -> None:
    d["_generated_at"] = _dt.datetime.now().isoformat(timespec="seconds")


TARGETS = {
    "combat_stats.json": load_combat_stats,
    "library_stats.json": load_library_stats,
    "mission_stats.json": load_mission_stats,
    "event_dialogues_stats.json": load_event_dialogues_stats,
    "stages_stats.json": load_stages_stats,
    "cyberspace_stats.json": load_cyberspace_stats,
    "journey_stats.json": load_journey_stats,
    "index_stats.json": load_index_stats,
    "character_stats.json": load_character_stats,
    "run_stats.json": load_run_stats,
    "design_system.json": load_design_system,
    "faction_stats.json": load_faction_stats,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print stats without writing JSON files",
    )
    args = parser.parse_args()

    DASHBOARD_DATA.mkdir(parents=True, exist_ok=True)
    rc = 0
    summary: dict[str, object] = {"repo": str(REPO), "outputs": {}, "errors": []}
    for filename, loader in TARGETS.items():
        try:
            stats = loader(REPO)
        except Exception as exc:  # noqa: BLE001
            summary["errors"].append(f"{filename}: {type(exc).__name__}: {exc}")
            rc = 1
            print(f"  [ERR] {filename}: {exc}", file=sys.stderr)
            continue
        _stamp(stats)
        out_path = DASHBOARD_DATA / filename
        if args.dry_run:
            print(f"\n--- DRY RUN: {filename} ---")
            print(json.dumps(stats, indent=2, ensure_ascii=False))
            continue
        out_path.write_text(
            json.dumps(stats, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        summary["outputs"][filename] = str(out_path.relative_to(REPO))
        print(f"  [OK]  {filename:<24s} {out_path}")

    index_path = DASHBOARD_DATA / "data_index.json"
    summary["index_path"] = str(index_path.relative_to(REPO))
    summary["_generated_at"] = _dt.datetime.now().isoformat(timespec="seconds")

    if not args.dry_run:
        index_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\n[data_index] {index_path.relative_to(REPO)}")
        print(
            f"\nGenerated {len(summary['outputs'])} stats files "
            f"in {DASHBOARD_DATA.relative_to(REPO)}."
        )
    return rc


if __name__ == "__main__":
    sys.exit(main())
