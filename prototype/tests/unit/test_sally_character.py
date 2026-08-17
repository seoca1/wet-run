"""Tests for Sally (7th) character integration (Phase 8).

Sally Shears is the cold A.I. market operator from Count Zero,
introduced 2026-07-04. She has:
  - 8 scenes in data/scenes/sally/ (4 base + 4 ending)
  - Added to GN menu as 7th character option
  - Added to char_to_dir mapping (sally → sally)
  - Has ending descriptions for A/B/C
"""

from __future__ import annotations

from pathlib import Path

from wet_run.engine.chapter_view import chapter_for_character
from wet_run.engine.graphic_novel_view import (
    GN_MENU_SALLY,
    _character_label,
    available_endings,
    get_gn_menu_key,
    get_gn_menu_options,
    list_scenes_for_character,
    load_scene_chain,
)

SCENES_DIR = Path(__file__).resolve().parents[2] / "data" / "scenes"
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class TestSallyScenesExist:
    def test_sally_scenes_dir_exists(self) -> None:
        sally_dir = SCENES_DIR / "sally"
        assert sally_dir.exists(), "data/scenes/sally/ should exist for Phase 8"

    def test_sally_has_nine_scenes(self) -> None:
        stems = list_scenes_for_character(SCENES_DIR, "sally")
        assert len(stems) == 9, f"Expected 8 sally scene files, got {len(stems)}: {stems}"

    def test_sally_scenes_load_ending_a(self) -> None:
        chain = load_scene_chain(SCENES_DIR, "sally", ending="A", max_order=8)
        assert len(chain) == 4
        for s in chain:
            assert s.character == "sally"
            assert s.ending == "A"

    def test_sally_scenes_load_ending_b(self) -> None:
        chain = load_scene_chain(SCENES_DIR, "sally", ending="B")
        assert len(chain) == 2
        for s in chain:
            assert s.character == "sally"
            assert s.ending == "B"


class TestSallyMenuOption:
    def test_sally_constant_defined(self) -> None:
        assert GN_MENU_SALLY == "sally"

    def test_sally_in_menu_options_without_save(self) -> None:
        from wet_run.i18n import Translator

        t = Translator("en")
        options = get_gn_menu_options(t, has_save=False)
        keys = [k for k, _ in options]
        # 10 menu keys + 1 empty BACK key
        assert len(options) == 11
        # Sally is the 8th option (index 7) when no save
        assert keys[7] == "8"

    def test_sally_in_menu_options_with_save(self) -> None:
        from wet_run.i18n import Translator

        t = Translator("en")
        options = get_gn_menu_options(t, has_save=True)
        keys = [k for k, _ in options]
        # CONTINUE + 9 menu keys + BACK = 11 options
        assert len(options) == 12
        # Sally is the 8th menu key (index 8) with save
        assert keys[8] == "9"

    def test_get_menu_key_sally_index(self) -> None:
        """Sally = index 7 (no save) or index 8 (with save)."""
        # without save: 0=prologue, 1=novice, ..., 7=sally, 8=BACK
        assert get_gn_menu_key(has_save=False, selected_index=7) == GN_MENU_SALLY
        # with save: 0=continue, 1=prologue, ..., 8=sally, 9=BACK
        assert get_gn_menu_key(has_save=True, selected_index=8) == GN_MENU_SALLY


class TestSallyCharacterLabel:
    def test_label_en(self) -> None:
        label = _character_label("sally", "en")
        assert "Sally" in label
        assert "Market" in label

    def test_label_ko(self) -> None:
        label = _character_label("sally", "ko")
        assert "샐리" in label
        assert "시장" in label


class TestSallyEndings:
    def test_three_endings_available(self) -> None:
        endings = available_endings("sally")
        assert endings == ["A", "B", "C"]


class TestSallyChapter:
    def test_chapter_for_sally_loads(self) -> None:
        chapter = chapter_for_character("sally", DATA_DIR)
        assert chapter.id == "chapter_sally"
        assert chapter.character == "sally"
        assert chapter.excerpt_en
        assert chapter.excerpt_ko
        assert chapter.theme == "industrial_market"


class TestPrologueWithSally:
    def test_prologue_includes_sally(self) -> None:
        from wet_run.engine.graphic_novel_view import load_prologue_chain

        chain = load_prologue_chain(SCENES_DIR, seed=42)
        sally_scenes = [s for s in chain if s.character == "sally"]
        assert len(sally_scenes) == 4

    def test_prologue_has_7_characters(self) -> None:
        from wet_run.engine.graphic_novel_view import load_prologue_chain

        chain = load_prologue_chain(SCENES_DIR, seed=42)
        chars = {s.character for s in chain}
        assert chars.issuperset({"novice", "veteran", "heretic", "suit", "wigan", "angie", "sally"})
