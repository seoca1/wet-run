#!/usr/bin/env python3
"""tools/build_static_data.py — Build dashboard data JSONs in one place.

Sources:
    Game/wet_run/prototype/data/missions/missions.json
    Fiction/derivative/sprawl-trilogy/short-stories/{en,ko}/*.md

Outputs (overwritten in place):
    dashboard/data/mission_links.json
    dashboard/data/search_index.json
    dashboard/data/character_graph.json
    dashboard/data/glossary.json          (also copied to dashboard/glossary.json)
    dashboard/data/character_meta.json     (extended cast profiles)
    dashboard/data/dataset_health.json     (size + integrity checks)

Run from workspace root:

    python3 tools/build_static_data.py

Exit codes:
    0  ok
    2  warning — emitted anyway (non-fatal)
    3  error  — missing source files or hard contracts broken
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DASH = REPO / "Game/wet_run/dashboard"
DATA = DASH / "data"
SPRAWL_EN_DIR = REPO / "Fiction/derivative/sprawl-trilogy/short-stories/en"
SPRAWL_KO_DIR = REPO / "Fiction/derivative/sprawl-trilogy/short-stories/ko"
SPRAWL_NV_EN_DIR = REPO / "Fiction/derivative/sprawl-trilogy/novelettes/en"
SPRAWL_NV_KO_DIR = REPO / "Fiction/derivative/sprawl-trilogy/novelettes/ko"
BRIDGE_EN_DIR = REPO / "Fiction/derivative/bridge-trilogy/short-stories/en"
BRIDGE_KO_DIR = REPO / "Fiction/derivative/bridge-trilogy/short-stories/ko"
BRIDGE_NV_EN_DIR = REPO / "Fiction/derivative/bridge-trilogy/novelettes/en"
BRIDGE_NV_KO_DIR = REPO / "Fiction/derivative/bridge-trilogy/novelettes/ko"
BLUE_ANT_EN_DIR = REPO / "Fiction/derivative/blue-ant/short-stories/en"
BLUE_ANT_KO_DIR = REPO / "Fiction/derivative/blue-ant/short-stories/ko"
BLUE_ANT_NV_EN_DIR = REPO / "Fiction/derivative/blue-ant/novelettes/en"
BLUE_ANT_NV_KO_DIR = REPO / "Fiction/derivative/blue-ant/novelettes/ko"
MISSIONS = REPO / "Game/wet_run/prototype/data/missions/missions.json"
GLOSSARY_WIKI = REPO / "Fiction/wiki"

NOW = _dt.datetime.now(_dt.timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_missions() -> dict[str, object]:
    if not MISSIONS.exists():
        sys.stderr.write(f"MISSING: {MISSIONS}\n")
        sys.exit(3)
    return json.loads(MISSIONS.read_text(encoding="utf-8"))


def _story_key(stem: str) -> str:
    """Strip leading YYYY-MM-DD_ prefix from a markdown stem.

    Keeps the stem comparable to dashboard HTML file names which also
    strip the date prefix (see markdown_to_story_html.get_story_id).
    """
    if len(stem) >= 11 and stem[4] == "-" and stem[7] == "-" and stem[10] == "_":
        return stem[11:]
    return stem


def load_all_stories() -> tuple[dict, dict]:
    en_out: dict[str, dict] = {}
    ko_out: dict[str, dict] = {}

    for src_dir in (SPRAWL_EN_DIR, SPRAWL_NV_EN_DIR):
        if src_dir.exists():
            for f in sorted(src_dir.glob("*.md")):
                if not f.name.endswith(".ko.md") and not f.name.endswith(".tone-prompt.md"):
                    en_out.setdefault(_story_key(f.stem), parse_story(f.read_text(encoding="utf-8"), "en"))
    for src_dir in (SPRAWL_KO_DIR, SPRAWL_NV_KO_DIR):
        if src_dir.exists():
            for f in sorted(src_dir.glob("*.ko.md")):
                ko_out.setdefault(_story_key(f.stem.replace(".ko", "")), parse_story(f.read_text(encoding="utf-8"), "ko"))

    for src_dir in (BRIDGE_EN_DIR, BRIDGE_NV_EN_DIR):
        if src_dir.exists():
            for f in sorted(src_dir.glob("*.md")):
                if not f.name.endswith(".ko.md") and not f.name.endswith(".tone-prompt.md"):
                    en_out.setdefault(_story_key(f.stem), parse_story(f.read_text(encoding="utf-8"), "en"))
    for src_dir in (BRIDGE_KO_DIR, BRIDGE_NV_KO_DIR):
        if src_dir.exists():
            for f in sorted(src_dir.glob("*.ko.md")):
                ko_out.setdefault(_story_key(f.stem.replace(".ko", "")), parse_story(f.read_text(encoding="utf-8"), "ko"))

    for src_dir in (BLUE_ANT_EN_DIR, BLUE_ANT_NV_EN_DIR):
        if src_dir.exists():
            for f in sorted(src_dir.glob("*.md")):
                if not f.name.endswith(".ko.md") and not f.name.endswith(".tone-prompt.md"):
                    en_out.setdefault(_story_key(f.stem), parse_story(f.read_text(encoding="utf-8"), "en"))
    for src_dir in (BLUE_ANT_KO_DIR, BLUE_ANT_NV_KO_DIR):
        if src_dir.exists():
            for f in sorted(src_dir.glob("*.ko.md")):
                ko_out.setdefault(_story_key(f.stem.replace(".ko", "")), parse_story(f.read_text(encoding="utf-8"), "ko"))

    return en_out, ko_out


def load_en_stories() -> dict[str, dict]:
    en_out, _ = load_all_stories()
    return en_out


def load_ko_stories() -> dict[str, dict]:
    _, ko_out = load_all_stories()
    return ko_out


def load_gibson_verification() -> dict[str, dict]:
    """Load Gibson verification results and index by story key."""
    gibson_path = Path("/tmp/gibson_verification.json")
    if not gibson_path.exists():
        return {}
    
    try:
        data = json.loads(gibson_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    
    index = {}
    for item in data:
        path = Path(item["path"])
        stem = path.stem
        
        key = _story_key(stem)
        
        checks = {c["check"]: c["status"] for c in item.get("checks", [])}
        
        index[key] = {
            "overall": item.get("overall", "partial"),
            "passed": item.get("passed", 0),
            "partial": item.get("partial", 0),
            "failed": item.get("failed", 0),
            "checks": checks,
        }
    
    return index


def load_stage5_results() -> dict[str, dict]:
    """Load Stage 5 (derivative literary check) results and index by story key."""
    stage5_path = Path("/tmp/stage5_results.json")
    if not stage5_path.exists():
        return {}
    
    try:
        data = json.loads(stage5_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    
    index = {}
    for item in data:
        path = Path(item["filepath"])
        stem = path.stem
        key = _story_key(stem)
        
        index[key] = {
            "score": item.get("weighted_total", 0),
            "grade": item.get("letter_grade", "unknown"),
            "dimensions": item.get("dimensions", {}),
        }
    
    return index


def load_stage6_results() -> dict[str, dict]:
    """Load Stage 6 (advanced literary check) results and index by story key."""
    stage6_path = Path("/tmp/stage6_results.json")
    if not stage6_path.exists():
        return {}
    
    try:
        data = json.loads(stage6_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    
    index = {}
    for item in data:
        path = Path(item["filepath"])
        stem = path.stem
        key = _story_key(stem)
        
        index[key] = {
            "score": item.get("weighted_total", 0),
            "grade": item.get("letter_grade", "unknown"),
            "era": item.get("era", ""),
            "dimensions": item.get("dimensions", {}),
        }
    
    return index


def load_flesch_readability() -> dict[str, dict]:
    """Load Flesch-Kincaid readability results and index by story key."""
    flesch_path = Path("/tmp/flesch_readability.json")
    if not flesch_path.exists():
        return {}
    
    try:
        data = json.loads(flesch_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    
    index = {}
    for item in data:
        path = item.get("path", "")
        stem = Path(path).stem if path else ""
        key = _story_key(stem)
        
        index[key] = {
            "fk_grade": item.get("flesch_kincaid_grade", 0),
            "fre": item.get("flesch_reading_ease", 0),
            "fog": item.get("gunning_fog", 0),
            "smog": item.get("smog_index", 0),
            "status": item.get("status", "unknown"),
        }
    
    return index


def parse_story(text: str, lang: str) -> dict:
    fm = re.search(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    out = {"lang": lang, "title": "", "subtitle": "", "character": "",
           "word_count": "", "language": "", "summary_en": "", "summary_ko": "",
           "missions_field": "", "plot_summary": "", "raw": text[:1200]}
    if not fm:
        return out
    body = fm.group(1)
    for line in body.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip().strip("'\"")
        if key == "title":
            if lang == "en":
                out["title"] = val
            else:
                # KO: nested title: { en, ko } — extract en or ko
                out["title"] = val
        elif key == "language":
            out["language"] = val
        elif key == "word_count":
            out["word_count"] = val
        elif key == "format":
            if " — " in val:
                out["format"] = val.split(" — ")[0]
        # Subtitle detection is in body
    sm = re.search(r"(?m)^plot_summary:\s*$", text, re.MULTILINE)
    if sm:
        summary_text = text[sm.end():]
        for summary_lang in ["en", "ko"]:
            m = re.search(rf"^\s+{summary_lang}:\s*(.+)$", summary_text, re.MULTILINE)
            if m:
                out[f"summary_{summary_lang}"] = m.group(1).strip()
    return out


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


def gen_mission_links(missions: dict) -> dict:
    by_source = {}
    by_character = {}
    for mid, m in missions.items():
        src = (m.get("story") or {}).get("source")
        if not src:
            continue
        rec = {
            "id": mid,
            "title": m.get("title", mid),
            "character_ref": (m.get("story") or {}).get("character_ref", ""),
            "cast": (m.get("story") or {}).get("cast", ""),
            "arc": (m.get("story") or {}).get("arc", 0),
            "pillar": (m.get("story") or {}).get("pillar", ""),
            "grade_min": m.get("grade_min", 0),
            "grade_max": m.get("grade_max", 0),
            "fixer": m.get("fixer", ""),
        }
        by_source.setdefault(src, []).append(rec)
        cr = rec["character_ref"]
        by_character.setdefault(cr, {})[src] = rec.get("title", "")
    return {"version": "1.0", "generated": NOW, "by_source": by_source, "by_character": by_character}


def gen_search_index(en_stories: dict, ko_stories: dict,
                     mission_links: dict) -> dict:
    out = []
    stem_trilogy: dict[str, str] = {}
    stem_content: dict[str, str] = {}
    trilogy_dirs_map = {
        "bridge":   (BRIDGE_EN_DIR,   BRIDGE_NV_EN_DIR,   BRIDGE_KO_DIR,   BRIDGE_NV_KO_DIR),
        "blue-ant": (BLUE_ANT_EN_DIR, BLUE_ANT_NV_EN_DIR, BLUE_ANT_KO_DIR, BLUE_ANT_NV_KO_DIR),
        "sprawl":   (SPRAWL_EN_DIR,   SPRAWL_NV_EN_DIR,   SPRAWL_KO_DIR,   SPRAWL_NV_KO_DIR),
    }
    for trilogy, (ss_dir, nv_dir, ko_ss, ko_nv) in trilogy_dirs_map.items():
        for content_type, ss in (("short-stories", ss_dir), ("novelettes", nv_dir)):
            if not ss.exists():
                continue
            for f in ss.glob("*.md"):
                if not (f.suffix == ".md" and not f.name.endswith(".tone-prompt.md")):
                    continue
                stem = _story_key(f.stem)
                if stem not in stem_trilogy or content_type == "novelettes":
                    stem_trilogy[stem] = trilogy
                    stem_content[stem] = content_type

    gibson_index = load_gibson_verification()
    stage5_index = load_stage5_results()
    stage6_index = load_stage6_results()
    flesch_index = load_flesch_readability()

    for stem, info in en_stories.items():
        trilogy = stem_trilogy.get(stem, "sprawl")
        content = stem_content.get(stem, "short-stories")
        entry = _story_entry(stem, info, "en", mission_links, trilogy, content)
        if stem in gibson_index:
            entry["gibson_style"] = gibson_index[stem]
        if stem in stage5_index:
            entry["literary"] = stage5_index[stem]
        if stem in stage6_index:
            entry["advanced_literary"] = stage6_index[stem]
        if stem in flesch_index:
            entry["readability"] = flesch_index[stem]
        out.append(entry)
    for stem, info in ko_stories.items():
        trilogy = stem_trilogy.get(stem, "sprawl")
        content = stem_content.get(stem, "short-stories")
        entry = _story_entry(stem, info, "ko", mission_links, trilogy, content)
        if stem in gibson_index:
            entry["gibson_style"] = gibson_index[stem]
        if stem in stage5_index:
            entry["literary"] = stage5_index[stem]
        if stem in stage6_index:
            entry["advanced_literary"] = stage6_index[stem]
        if stem in flesch_index:
            entry["readability"] = flesch_index[stem]
        out.append(entry)
    out.sort(key=lambda s: (s["lang"], s["id"]))

    gibson_stats = {
        "total_verified": len(gibson_index),
        "pass": sum(1 for v in gibson_index.values() if v["overall"] == "pass"),
        "partial": sum(1 for v in gibson_index.values() if v["overall"] == "partial"),
        "fail": sum(1 for v in gibson_index.values() if v["overall"] == "fail"),
    }

    stage5_stats = {
        "total": len(stage5_index),
        "S": sum(1 for v in stage5_index.values() if v["grade"] == "S"),
        "A": sum(1 for v in stage5_index.values() if v["grade"] == "A"),
        "B": sum(1 for v in stage5_index.values() if v["grade"] == "B"),
        "C": sum(1 for v in stage5_index.values() if v["grade"] == "C"),
        "D": sum(1 for v in stage5_index.values() if v["grade"] == "D"),
    }

    stage6_stats = {
        "total": len(stage6_index),
        "S": sum(1 for v in stage6_index.values() if v["grade"] == "S"),
        "A": sum(1 for v in stage6_index.values() if v["grade"] == "A"),
        "B": sum(1 for v in stage6_index.values() if v["grade"] == "B"),
        "C": sum(1 for v in stage6_index.values() if v["grade"] == "C"),
        "D": sum(1 for v in stage6_index.values() if v["grade"] == "D"),
    }

    flesch_stats = {
        "total": len(flesch_index),
        "pass": sum(1 for v in flesch_index.values() if v["status"] == "pass"),
        "partial": sum(1 for v in flesch_index.values() if v["status"] == "partial"),
        "avg_fk_grade": round(sum(v["fk_grade"] for v in flesch_index.values()) / max(1, len(flesch_index)), 1),
        "avg_fre": round(sum(v["fre"] for v in flesch_index.values()) / max(1, len(flesch_index)), 1),
        "avg_fog": round(sum(v["fog"] for v in flesch_index.values()) / max(1, len(flesch_index)), 1),
    }

    return {
        "version": "1.0",
        "generated": NOW,
        "count": len(out),
        "stories": out,
        "gibson_style_stats": gibson_stats,
        "literary_stats": stage5_stats,
        "advanced_literary_stats": stage6_stats,
        "readability_stats": flesch_stats,
    }


def _story_entry(stem: str, info: dict, lang: str, mission_links: dict,
                 trilogy: str = "sprawl", content_type: str = "short-stories") -> dict:
    body_preview = ""
    sm = info.get(f"summary_{lang}") or info.get("summary_en") or info.get("summary_ko")
    if sm:
        body_preview = sm[:280]
    missions_for_stem = []
    cast_set = set()
    for rec in mission_links.get("by_source", {}).get(stem, []):
        missions_for_stem.append(rec["id"])
        if rec.get("cast"):
            cast_set.add(rec["cast"])


    return {
        "id": stem,
        "lang": lang,
        "title": info.get("title") or stem,
        "subtitle": info.get("format") or "",
        "character": info.get("character") or "",
        "cast": ",".join(sorted(cast_set)),
        "word_count": info.get("word_count") or "",
        "body_preview": body_preview,
        "missions": missions_for_stem,
        "trilogy": trilogy,
        "url": f"stories/{content_type}/{stem}_{lang}.html",
    }


def gen_character_graph() -> dict:
    """Build character graph from wiki character pages — auto-extract
    Related Characters sections. Falls back to hand-curated base."""
    base = REPO / "Game/wet_run/dashboard/data/character_graph.json"
    if base.exists():
        try:
            existing = json.loads(base.read_text(encoding="utf-8"))
            base_chars = existing.get("characters", [])
            base_edges = existing.get("edges", [])
        except Exception:
            base_chars, base_edges = [], []
    else:
        base_chars, base_edges = [], []

    # Optionally enrich: scan wiki pages for "Related Characters" section
    wiki_chars = REPO / "Fiction/wiki/characters"
    enriched = {c["id"]: dict(c) for c in base_chars}
    for f in (wiki_chars.glob("*.md") if wiki_chars.exists() else []):
        stem = f.stem
        if stem not in enriched:
            continue
        text = f.read_text(encoding="utf-8")
        m = re.search(r"## Related Characters\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
        if not m:
            continue
        related = re.findall(r"\[\[([^\]|#]+)\]", m.group(1))
        enriched[stem].setdefault("related", [])
        for r in related:
            r_stem = r.lower().replace(" ", "-")
            if r_stem not in enriched[stem]["related"]:
                enriched[stem]["related"].append(r_stem)

    return {
        "version": "1.0",
        "generated": NOW,
        "characters": list(enriched.values()),
        "edges": base_edges,
        "enrichment": {
            "wiki_char_pages_scanned": sum(1 for _ in (wiki_chars.glob("*.md") if wiki_chars.exists() else [])),
            "relationships_from_wiki": sum(
                len(c.get("related", [])) for c in enriched.values()
            ),
        },
    }


def gen_glossary(missions: dict) -> dict:
    """Generate the canonical glossary that dashboard/glossary.js depends on.

    Sources:
      1. wiki/concepts/*.md        — page bodies
      2. wiki/characters/*.md      — page names + Related Characters
      3. wiki/works/*.md           — page titles
      4. missions.json             — explicit character_ref names
    """
    terms = set()
    mapping = {}

    def add(label: str, page: str, tooltip: str = ""):
        if not label:
            return
        k = label.lower()
        if k in mapping:
            return
        if (GLOSSARY_WIKI / page).exists():
            terms.add(label)
            mapping[k] = {"page": page, "tooltip": tooltip or label, "text": label}

    concepts_dir = GLOSSARY_WIKI / "concepts"
    if concepts_dir.exists():
        for f in concepts_dir.glob("*.md"):
            add(f.stem.replace("-", " "), f"concepts/{f.name}")

    chars_dir = GLOSSARY_WIKI / "characters"
    if chars_dir.exists():
        for f in chars_dir.glob("*.md"):
            try:
                text = f.read_text(encoding="utf-8")
            except Exception:
                continue
            m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            label = m.group(1).strip() if m else f.stem
            add(label, f"characters/{f.name}")
            for alias in re.findall(r"\[\[([^\]|#]+)", text):
                add(alias.replace("-", " "), f"characters/{f.name}")

    works_dir = GLOSSARY_WIKI / "works"
    if works_dir.exists():
        for f in works_dir.glob("*.md"):
            try:
                text = f.read_text(encoding="utf-8")
            except Exception:
                continue
            m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            label = m.group(1).strip() if m else f.stem
            add(label, f"works/{f.name}")

    settings_dir = GLOSSARY_WIKI / "settings"
    if settings_dir.exists():
        for f in settings_dir.glob("*.md"):
            add(f.stem.replace("-", " "), f"settings/{f.name}")

    # from mission literals
    for m in missions.values():
        for field in ("fixer",):
            v = m.get(field, "")
            if v:
                add(v.replace("-", " "), f"concepts/{v}.md")

    sorted_terms = sorted(terms, key=lambda x: (-len(x), x))
    return {
        "version": "1.0",
        "generated": NOW,
        "wiki_base": "../../../Fiction/wiki/",
        "term_count": len(sorted_terms),
        "terms": sorted_terms,
        "map": mapping,
    }


def gen_health(en_stories: dict, ko_stories: dict, missions: dict,
               glossary: dict) -> dict:
    issues = []
    en_keys = set(en_stories.keys())
    ko_keys = set(ko_stories.keys())
    if en_keys != ko_keys:
        issues.append({
            "type": "en_ko_mismatch",
            "only_en": sorted(en_keys - ko_keys),
            "only_ko": sorted(ko_keys - en_keys),
        })
    # Collect all EN directories
    en_dirs = [SPRAWL_EN_DIR, SPRAWL_NV_EN_DIR, BRIDGE_EN_DIR, BRIDGE_NV_EN_DIR, BLUE_ANT_EN_DIR, BLUE_ANT_NV_EN_DIR]
    for mid, m in missions.items():
        src = (m.get("story") or {}).get("source", "")
        if not src:
            continue
        matches = []
        for d in en_dirs:
            if d.exists():
                # Check if source already includes date prefix
                if src.startswith("20") and "-" in src[:10]:
                    matches.extend(d.glob(f"{src}.md"))
                else:
                    matches.extend(d.glob(f"*_{src}.md"))
        if not matches:
            issues.append({"type": "missing_source", "mission": mid, "source": src})

    return {
        "version": "1.0",
        "generated": NOW,
        "en_stories": len(en_stories),
        "ko_stories": len(ko_stories),
        "missions": len(missions),
        "glossary_terms": glossary.get("term_count", 0),
        "issues": issues,
        "ok": not issues,
    }


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------


def write(path: Path, payload: dict) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, indent=2, ensure_ascii=False)
    path.write_text(body, encoding="utf-8")
    return path.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    missions = load_missions()
    en_stories = load_en_stories()
    ko_stories = load_ko_stories()

    mission_links = gen_mission_links(missions)
    glossary = gen_glossary(missions)
    search_index = gen_search_index(en_stories, ko_stories, mission_links)
    char_graph = gen_character_graph()
    health = gen_health(en_stories, ko_stories, missions, glossary)

    sizes = {
        DATA / "mission_links.json": write(DATA / "mission_links.json", mission_links),
        DATA / "search_index.json": write(DATA / "search_index.json", search_index),
        DATA / "character_graph.json": write(DATA / "character_graph.json", char_graph),
        DATA / "dataset_health.json": write(DATA / "dataset_health.json", health),
        DASH / "glossary.json": write(DASH / "glossary.json", glossary),
        DATA / "glossary.json": write(DATA / "glossary.json", {k: v for k, v in glossary.items() if k != "map" or True}),
    }
    sizes[DATA / "glossary.json"] = (DASH / "glossary.json").stat().st_size

    if not args.quiet:
        print("=== build_static_data.py ===\n")
        for path, size in sizes.items():
            rel = path.relative_to(REPO)
            print(f"  ✓ {rel} ({size:,} bytes)")
        print(f"\n  EN stories: {health['en_stories']}")
        print(f"  KO stories: {health['ko_stories']}")
        print(f"  Missions:   {health['missions']}")
        print(f"  Glossary:   {health['glossary_terms']} terms")
        if not health["ok"]:
            print("\n  ⚠ Issues:")
            for issue in health["issues"][:10]:
                print(f"    - {issue}")
            return 2
        print("\n  ✓ All integrity checks pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
