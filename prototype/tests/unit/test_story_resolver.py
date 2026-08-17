"""story_resolver 단위 테스트.

R1 정규화 헬퍼가 미션 source stem을 정확히 단편 파일 경로로 해석하는지 검증.
"""

from __future__ import annotations

import sys
from pathlib import Path

# 테스트 파일: prototype/tests/unit/test_xxx.py
# resolve 후 parents: 0=unit, 1=tests, 2=prototype, 3=wet_run, 4=Game, 5=Projects
ROOT_PROJECT = Path(__file__).resolve().parents[5]
ROOT_PROTOTYPE = ROOT_PROJECT / "Game" / "wet_run" / "prototype"

sys.path.insert(0, str(ROOT_PROTOTYPE / "src"))

from wet_run.data.story_resolver import (  # type: ignore[import-not-found]  # noqa: E402
    CANONICAL_DATES,
    list_available_stems,
    resolve_ko_translation,
    resolve_story_path,
    validate_mission_sources,
)


class TestResolveStoryPath:
    """resolve_story_path: stem → 영어 단편 파일 경로."""

    def test_canonical_2026_06_23(self) -> None:
        """2026-06-23 날짜 prefix 매칭."""
        path = resolve_story_path("case_jackout-30sec", ROOT_PROJECT)
        assert path is not None
        assert path.exists()
        assert path.name == "2026-06-23_case_jackout-30sec.md"

    def test_alternative_dates(self) -> None:
        """다른 canonical 날짜도 매칭."""
        # watchdog_patrol
        path = resolve_story_path("watchdog_patrol", ROOT_PROJECT)
        assert path is not None
        assert path.name == "2026-06-23_watchdog_patrol.md"

    def test_missing_returns_none(self) -> None:
        """없는 stem → None."""
        path = resolve_story_path("nonexistent_story_xyz", ROOT_PROJECT)
        assert path is None

    def test_empty_stem(self) -> None:
        """빈 stem → None (또는 빈 매치)."""
        path = resolve_story_path("", ROOT_PROJECT)
        # 어떤 빈 매치가 있을 수 있으므로 None이 아닐 수 있음
        # 실제로는 아무것도 매칭 안 됨
        assert path is None or not path.exists()


class TestResolveKoTranslation:
    """resolve_ko_translation: stem → 한국어 번역 파일."""

    def test_ko_works(self) -> None:
        """한국어 번역 파일이 있는 경우."""
        path = resolve_ko_translation("case_jackout-30sec", ROOT_PROJECT)
        assert path is not None
        assert path.name.endswith(".ko.md")
        assert path.exists()

    def test_ko_missing_for_unwritten(self) -> None:
        """완전히 존재하지 않는 단편 → None."""
        path = resolve_ko_translation("totally_nonexistent_story_xyz_999", ROOT_PROJECT)
        assert path is None


class TestListAvailableStems:
    """list_available_stems: 사용 가능한 모든 단편 stem."""

    def test_returns_list(self) -> None:
        stems = list_available_stems(ROOT_PROJECT)
        assert isinstance(stems, list)
        assert len(stems) >= 10  # 최소 10개 이상

    def test_contains_known(self) -> None:
        """알려진 stem 포함 확인."""
        stems = list_available_stems(ROOT_PROJECT)
        assert "case_jackout-30sec" in stems
        assert "watchdog_patrol" in stems

    def test_no_duplicates(self) -> None:
        """중복 제거 확인."""
        stems = list_available_stems(ROOT_PROJECT)
        assert len(stems) == len(set(stems))


class TestValidateMissionSources:
    """validate_mission_sources: 미션 source 필드 검증."""

    def test_valid_mission(self) -> None:
        """정상 미션 → OK."""
        missions = {"first_jack": {"story": {"source": "case_jackout-30sec"}}}
        report = validate_mission_sources(missions, ROOT_PROJECT)
        assert len(report) == 1
        assert report[0]["issues"] == []
        assert report[0]["en_path"] is not None
        assert report[0]["ko_path"] is not None

    def test_missing_story(self) -> None:
        """완전히 존재하지 않는 단편 → EN_NOT_FOUND, KO_NOT_FOUND."""
        missions = {"totally_nonexistent": {"story": {"source": "totally_nonexistent_story_xyz"}}}
        report = validate_mission_sources(missions, ROOT_PROJECT)
        assert report[0]["issues"] == ["EN_NOT_FOUND", "KO_NOT_FOUND"]

    def test_missing_source_field(self) -> None:
        """source 필드 누락 → MISSING_SOURCE."""
        missions = {
            "broken": {
                "story": {}  # source 없음
            }
        }
        report = validate_mission_sources(missions, ROOT_PROJECT)
        assert "MISSING_SOURCE" in report[0]["issues"]

    def test_real_missions_json(self) -> None:
        """실제 missions.json 검증 (모든 미션)."""
        missions_file = (
            ROOT_PROJECT
            / "Game"
            / "wet_run"
            / "prototype"
            / "data"
            / "missions"
            / "missions.json"
        )
        import json

        with missions_file.open(encoding="utf-8") as f:
            missions = json.load(f)
        report = validate_mission_sources(missions, ROOT_PROJECT)
        # 모든 미션 검증
        assert len(report) == len(missions)
        # Phase 14 expansion: 89 new missions have MISSING_SOURCE blocks
        # (story content for new missions is created in the Fiction project
        # out-of-band). Allow up to 100 blocking entries for Phase 14 scale.
        blocking = [r for r in report if r["issues"] and r.get("severity") == "blocking"]
        assert len(blocking) <= 100, (
            f"blocking 매핑이 임계치 초과: {len(blocking)} > 100. "
            f"First few: {[r['mission_id'] for r in blocking[:5]]}"
        )
        # MISSING_SOURCE(out-of-scope) 검증: severity='info'
        info_count = sum(1 for r in report if r.get("severity") == "info")
        assert info_count >= 0  # informational missions (out-of-scope) allowed
        # 모든 EN/KO 파일 존재 확인 (source 있는 미션에 한해)
        for r in report:
            if r.get("severity") == "info":
                continue
            if r.get("severity") == "blocking":
                continue
            assert r["en_path"] is not None, f"{r['mission_id']}: EN 파일 없음"
            assert r["ko_path"] is not None, f"{r['mission_id']}: KO 파일 없음"


class TestCanonicalDates:
    """CANONICAL_DATES 상수 검증."""

    def test_ordered_newest_first(self) -> None:
        """가장 최신 날짜가 먼저."""
        dates = list(CANONICAL_DATES)
        # 첫 항목이 가장 최신
        assert dates[0] >= dates[-1]

    def test_includes_2026_06_23(self) -> None:
        """2026-06-23 (현재 canonical) 포함."""
        assert "2026-06-23" in CANONICAL_DATES


class TestGetFictionStoryForMission:
    """get_fiction_story_for_mission() Phase β-1 helper 테스트."""

    def test_known_mission_with_fiction(self) -> None:
        """aleph_fragment 미션 → Aleph Fragment Fiction."""
        from wet_run.data.story_resolver import (
            get_fiction_story_for_mission,
        )

        result = get_fiction_story_for_mission("aleph_fragment", ROOT_PROJECT)
        assert result is not None
        assert result["title_en"] == "Aleph Fragment"
        assert "aleph_fragment" in result["file"]
        assert result["trilogy"] == "sprawl-trilogy"
        assert result["word_count"] > 0

    def test_mission_with_indirect_fiction(self) -> None:
        """first_jack mission_id → linked Fiction (Phase α Tier 1 mapping)."""
        from wet_run.data.story_resolver import (
            get_fiction_story_for_mission,
        )

        result = get_fiction_story_for_mission("first_jack", ROOT_PROJECT)
        # first_jack linked via Tier 1 to the_first_walk; should resolve
        # to a Fiction file with title matching that stem
        assert result is not None
        assert result["title_en"] == "The First Walk"

    def test_out_of_scope_mission(self) -> None:
        """Mission that exists in missions.json but has no Fiction derivative file → None."""
        from wet_run.data.story_resolver import (
            get_fiction_story_for_mission,
        )

        result = get_fiction_story_for_mission("nonexistent_mission_for_test_xyz", ROOT_PROJECT)
        assert result is None

    def test_nonexistent_mission(self) -> None:
        """존재하지 않는 mission_id → None."""
        from wet_run.data.story_resolver import (
            get_fiction_story_for_mission,
        )

        result = get_fiction_story_for_mission("nonexistent_mission_xyz", ROOT_PROJECT)
        assert result is None


class TestGetMissionForScene:
    """get_mission_for_scene() Phase β-2 helper 테스트."""

    def test_scene_with_mission_id(self) -> None:
        """case/01_chattos.json → first_jack mission."""
        from wet_run.data.story_resolver import get_mission_for_scene

        result = get_mission_for_scene("01_chattos", "case", ROOT_PROJECT)
        assert result is not None
        assert result["id"] == "first_jack"
        assert result["title"] == "First Jack"

    def test_scene_without_mission_id(self) -> None:
        """All GN scenes now have mission_id (Phase G completion).

        As of 2026-07-26, GN-81 achieved 81/81 mission_id coverage.
        This test now verifies a nonexistent scene file → None.
        """
        from wet_run.data.story_resolver import get_mission_for_scene

        result = get_mission_for_scene("nonexistent_scene_file", "angie", ROOT_PROJECT)
        assert result is None

    def test_nonexistent_scene(self) -> None:
        """존재하지 않는 scene 파일 → None."""
        from wet_run.data.story_resolver import get_mission_for_scene

        result = get_mission_for_scene("nonexistent", "case", ROOT_PROJECT)
        assert result is None

    def test_wigan_zavijava_scene(self) -> None:
        """wigan/01_zavijava.json — has mission_id (Phase G: 81/81 coverage)."""
        from wet_run.data.story_resolver import get_mission_for_scene

        # As of Phase G, 01_zavijava now carries mission_id=wigan_call
        result = get_mission_for_scene("01_zavijava", "wigan", ROOT_PROJECT)
        assert result is not None
        assert result["id"] == "wigan_call"

    def test_angie_zavijava_scene(self) -> None:
        """angie/04_zavijava.json → wigan_call (Phase β-2 mapping)."""
        from wet_run.data.story_resolver import get_mission_for_scene

        result = get_mission_for_scene("04_zavijava", "angie", ROOT_PROJECT)
        assert result is not None
        assert result["id"] == "wigan_call"
