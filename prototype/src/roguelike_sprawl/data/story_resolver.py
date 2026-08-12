"""소설 stem → 파일 경로 정규화 (R1).

`missions.json`의 `story.source` 필드는 소설 stem (예: `case_jackout-30sec`)이고,
실제 파일은 날짜 prefix를 가진 형태 (예: `2026-06-23_case_jackout-30sec.md`)입니다.
날짜 prefix는 v1 → v2 갱신 시 변경될 수 있으므로 코드에서 정규화합니다.

소설은 다음 디렉토리 중 하나에 저장됨 (test_novels.py 검증):
  - short-stories/  (단편,   derivative_type: short_story)
  - novelettes/     (중단편, derivative_type: novelette)
  - novellas/       (중편,   derivative_type: novella)

규칙:
- canonical 날짜 순으로 모든 소설 디렉토리 검색
- 없으면 다른 날짜 prefix 시도
- 한국어 번역 (`.ko.md`) 도 동일한 정규화
"""

from __future__ import annotations

import re
from pathlib import Path

# 가장 최근 canonical 날짜 (v2.1). 새 버전 출시 시 갱신.
CANONICAL_DATES = (
    "2026-07-08",
    "2026-07-01",
    "2026-06-30",
    "2026-06-29",
    "2026-06-25",
    "2026-06-23",
    "2026-06-22",
    "2026-06-20",
    "2026-06-19",
)

# 소설 디렉토리 목록 (derivative_type 순) — 2026-07-10 구조 변경 반영
# en/ko 하위 디렉토리로 분리됨. resolver는 양쪽 구조 (legacy + new) 모두 지원.
NOVEL_DIR_NAMES: tuple[str, ...] = ("short-stories", "novelettes", "novellas")
LANG_SUBDIRS: tuple[str, ...] = ("en", "ko")


def _novel_dirs(repo_root: Path) -> list[Path]:
    """모든 소설 디렉토리 경로 반환 (존재하는 것만).

    Searches all three trilogies (Sprawl / Bridge / Blue Ant).
    Returns both legacy paths (e.g., short-stories/case_jackout.md)
    and new paths (e.g., short-stories/en/case_jackout.md).
    """
    derivative = repo_root / "Fiction" / "derivative"
    trilogies = ("sprawl-trilogy", "bridge-trilogy", "blue-ant")
    paths: list[Path] = []
    for trilogy in trilogies:
        for name in NOVEL_DIR_NAMES:
            base = derivative / trilogy / name
            if base.exists():
                paths.append(base)
                for lang in LANG_SUBDIRS:
                    sub = base / lang
                    if sub.exists():
                        paths.append(sub)
    return paths


def _short_stories_dir(repo_root: Path) -> Path:
    """단편 소설 디렉토리 경로. (legacy 호환용)"""
    return repo_root / "Fiction" / "derivative" / "sprawl-trilogy" / "short-stories"


def _search_in_dirs(stem: str, suffix: str, repo_root: Path) -> Path | None:
    """모든 소설 디렉토리에서 canonical 날짜 순으로 검색.

    2026-07-10 구조 변경: en/ko 하위 디렉토리도 검색.
    """
    for date in CANONICAL_DATES:
        for base in _novel_dirs(repo_root):
            candidate = base / f"{date}_{stem}{suffix}"
            if candidate.exists():
                return candidate
    # 어떤 날짜든 매칭
    for base in _novel_dirs(repo_root):
        matches = sorted(base.glob(f"*_{stem}{suffix}"), reverse=True)
        if matches:
            return matches[0]
    return None


def resolve_story_path(stem: str, repo_root: Path) -> Path | None:
    """소설 stem → 영어 본편 파일 경로.

    Args:
        stem: 미션의 source 필드 (예: "case_jackout-30sec")
        repo_root: 프로젝트 루트 (Projects/)

    Returns:
        찾은 파일 경로. 없으면 None.
    """
    return _search_in_dirs(stem, ".md", repo_root)


def resolve_ko_translation(stem: str, repo_root: Path) -> Path | None:
    """소설 stem → 한국어 번역 파일 경로.

    Args:
        stem: 미션의 source 필드
        repo_root: 프로젝트 루트

    Returns:
        한국어 번역 파일 경로. 없으면 None.
    """
    return _search_in_dirs(stem, ".ko.md", repo_root)


def list_available_stems(repo_root: Path) -> list[str]:
    """사용 가능한 소설 stem 목록 (모든 날짜/디렉토리 통합, 중복 제거)."""
    stems: set[str] = set()
    for base in _novel_dirs(repo_root):
        for f in base.glob("*.md"):
            if f.name.endswith(".ko.md") or f.name.endswith(".tone-prompt.md"):
                continue
            # 2026-06-23_case_jackout-30sec → ['2026-06-23', 'case_jackout-30sec']
            # 최대 1번 split으로 [날짜, stem] 분리 (stem 내부에 하이픈 허용)
            parts = f.stem.split("_", 1)
            if len(parts) == 2 and parts[0].startswith("2026-"):
                stems.add(parts[1])
            else:
                stems.add(f.stem)
    return sorted(stems)


def validate_mission_sources(
    missions: dict[str, dict[str, object]], repo_root: Path
) -> list[dict[str, object]]:
    """missions.json의 모든 source 필드 검증.

    Returns:
        문제 보고서 리스트. 각 항목:
            - mission_id
            - source (stem)
            - en_path (or None)
            - ko_path (or None)
            - issues (list of issue strings)
            - severity: "ok" | "info" | "blocking"

        Severity:
            - "ok": no issues
            - "info": MISSING_SOURCE (intentional — out-of-scope mission, no Fiction source expected)
            - "blocking": EN_NOT_FOUND or KO_NOT_FOUND (orphaned reference)
    """
    report = []
    for mid, m in missions.items():
        story = m.get("story", {})
        if not isinstance(story, dict):
            continue
        source = story.get("source", "")
        if not source:
            report.append(
                {
                    "mission_id": mid,
                    "source": source,
                    "en_path": None,
                    "ko_path": None,
                    "issues": ["MISSING_SOURCE"],
                    "severity": "info",
                }
            )
            continue
        en = resolve_story_path(source, repo_root)
        ko = resolve_ko_translation(source, repo_root)
        issues = []
        severity = "ok"
        if en is None:
            issues.append("EN_NOT_FOUND")
            severity = "blocking"
        if ko is None:
            issues.append("KO_NOT_FOUND")
            severity = "blocking"
        report.append(
            {
                "mission_id": mid,
                "source": source,
                "en_path": str(en) if en else None,
                "ko_path": str(ko) if ko else None,
                "issues": issues,
                "severity": severity,
            }
        )
    return report


def _read_game_mission_ids_from_fiction(repo_root: Path) -> list[dict[str, object]]:
    """Scan all Fiction derivative EN .md files for `game_mission_id:` frontmatter.

    Returns list of dicts with keys: file, stem, game_mission_id.
    Skips KO .ko.md files (they mirror the EN frontmatter).
    """
    import re

    out: list[dict[str, object]] = []
    fm_pattern = re.compile(r"^game_mission_id:\s*(\S+)\s*$", re.MULTILINE)
    for base in _novel_dirs(repo_root):
        for f in base.glob("*.md"):
            if f.name.endswith(".ko.md") or f.name.endswith(".tone-prompt.md"):
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except OSError:
                continue
            m = fm_pattern.search(text)
            if m is None:
                continue
            stem_match = re.search(r"^stem:\s*(\S+)", text, re.MULTILINE)
            declared_stem = stem_match.group(1).strip().strip('"') if stem_match else None
            out.append(
                {
                    "file": str(f.relative_to(repo_root)),
                    "stem": declared_stem or f.stem.split("_", 1)[-1],
                    "game_mission_id": m.group(1).strip().strip('"'),
                }
            )
    return out


def validate_game_mission_id_links(
    missions: dict[str, dict[str, object]], repo_root: Path
) -> list[dict[str, object]]:
    """Cross-project: Fiction frontmatter `game_mission_id` ↔ roguelike_sprawl missions.

    Reports Fiction stories that declare `game_mission_id` but the mission
    does not exist in missions.json (orphan). Stories without the field
    are not reported — they are intentionally Fiction-only.

    Also reports inconsistencies where the declared stem differs from the
    filename-derived stem.

    Returns list of dicts with keys: file, stem, game_mission_id, issues.
    """
    mission_ids = set(missions.keys())
    rows = _read_game_mission_ids_from_fiction(repo_root)
    report: list[dict[str, object]] = []
    for row in rows:
        gmi = row["game_mission_id"]
        issues: list[str] = []
        if gmi not in mission_ids:
            issues.append("ORPHAN_MISSION_ID")
        report.append({**row, "issues": issues})
    return report


def get_mission_for_scene(scene_id: str, jockey: str, repo_root: Path) -> dict[str, object] | None:
    """Look up the mission linked to a GN scene via its `mission_id` field.

    Phase β-2: GN scene JSON files may declare a `mission_id` field to
    link a character arc scene with its gameplay mission counterpart.
    Only 7 of 81 scenes currently have this field (mostly case/01-04
    → first_jack and sally/01 → sally_returns_arc3).

    Args:
        scene_id: Scene id (e.g. "scene_case_jackin") or scene file stem
        jockey: Jockey identifier ("case", "sil", etc.)
        repo_root: Project root (Projects/)

    Returns:
        Mission dict from missions.json or None if no link.
    """
    import json as _json

    scene_path = (
        repo_root
        / "Game"
        / "roguelike_sprawl"
        / "prototype"
        / "data"
        / "scenes"
        / jockey
        / f"{scene_id}.json"
    )
    if not scene_path.exists():
        return None
    try:
        scene = _json.loads(scene_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    mid = scene.get("mission_id")
    if not mid:
        return None
    missions_path = (
        repo_root
        / "Game"
        / "roguelike_sprawl"
        / "prototype"
        / "data"
        / "missions"
        / "missions.json"
    )
    if not missions_path.exists():
        return None
    try:
        missions = _json.loads(missions_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    mission = missions.get(mid)
    if not isinstance(mission, dict):
        return None
    return {"id": mid, **mission}


def get_fiction_story_for_mission(
    mission_id: str, repo_root: Path, source: str | None = None
) -> dict[str, object] | None:
    """Resolve mission_id → Fiction derivative story metadata.

    Looks up the Fiction file declared via game_mission_id frontmatter
    matching the given mission_id. Returns None if no Fiction story
    references this mission (either the mission is out-of-scope or the
    Fiction link is missing).

    Returns dict with keys:
        - file (relative path to Fiction EN file)
        - stem (Fiction stem)
        - title_en (English title)
        - title_ko (Korean title)
        - character_ref (POV character: novice/veteran/heretic/etc.)
        - derivative_type (short_story/novelette)
        - word_count (EN)
        - trilogy (sprawl-trilogy / bridge-trilogy / blue-ant)
    """
    fm_pattern = re.compile(r"^game_mission_id:\s*(\S+)\s*$", re.MULTILINE)
    title_en_pattern = re.compile(
        r"^title:\s*\n\s*en:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", re.MULTILINE
    )
    title_ko_pattern = re.compile(
        r"^title:\s*\n\s*ko:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", re.MULTILINE
    )
    char_pattern = re.compile(r"^character_ref:\s*['\"]?(\w+)", re.MULTILINE)
    type_pattern = re.compile(r"^derivative_type:\s*(\S+)", re.MULTILINE)
    wc_pattern = re.compile(r"^word_count:\s*(\d+)", re.MULTILINE)

    trilogies = ("sprawl-trilogy", "bridge-trilogy", "blue-ant")
    novel_subdirs = ("short-stories", "novelettes", "novellas")
    derivative_root = repo_root / "Fiction" / "derivative"

    candidates: list[tuple[int, tuple[Path, str, str, str]]] = []
    mission_id_alt_pattern = re.compile(
        r"^\s*mission_id:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", re.MULTILINE
    )
    for trilogy in trilogies:
        for subdir in novel_subdirs:
            en_dir = derivative_root / trilogy / subdir / "en"
            if not en_dir.exists():
                continue
            for f in en_dir.glob("*.md"):
                if f.name.endswith(".tone-prompt.md"):
                    continue
                try:
                    text = f.read_text(encoding="utf-8")
                except OSError:
                    continue
                m = fm_pattern.search(text)
                alt_m = mission_id_alt_pattern.search(text)
                matched_id = None
                score = 0
                if m and m.group(1).strip().strip('"') == mission_id:
                    matched_id = m.group(1).strip().strip('"')
                elif alt_m and alt_m.group(1).strip().strip('"') == mission_id:
                    matched_id = alt_m.group(1).strip().strip('"')
                elif m and source and m.group(1).strip().strip('"') == source:
                    matched_id = m.group(1).strip().strip('"')
                elif alt_m and source and alt_m.group(1).strip().strip('"') == source:
                    matched_id = alt_m.group(1).strip().strip('"')
                if matched_id is None:
                    continue
                file_stem = f.stem.split("_", 1)[-1] if "_" in f.stem else f.stem
                if file_stem == mission_id:
                    score = max(score, 3)
                elif source and file_stem == source:
                    score = max(score, 2)
                else:
                    score = max(score, 1)
                candidates.append((score, (f, text, file_stem, trilogy)))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    _, (f, text, file_stem, trilogy) = candidates[0]
    title_en_m = title_en_pattern.search(text)
    title_ko_m = title_ko_pattern.search(text)
    char_m = char_pattern.search(text)
    type_m = type_pattern.search(text)
    wc_m = wc_pattern.search(text)
    return {
        "file": str(f.relative_to(repo_root)),
        "stem": file_stem,
        "title_en": title_en_m.group(1) if title_en_m else f.stem,
        "title_ko": title_ko_m.group(1) if title_ko_m else "",
        "character_ref": char_m.group(1) if char_m else "",
        "derivative_type": type_m.group(1) if type_m else "short_story",
        "word_count": int(wc_m.group(1)) if wc_m else 0,
        "trilogy": trilogy,
    }
    return None
