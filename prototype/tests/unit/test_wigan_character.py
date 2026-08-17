"""Tests for the Wigan (5th) character integration (Phase 7.1).

The Wigan character is a Vodou construct persona — half-dead cowboy
Wigan Ludgate, half-loa Zavijava — introduced 2026-07-04. It has:
  - 8 scenes in data/scenes/wigan/ (4 base + 4 ending)
  - Added to GN menu as 5th character option
  - Added to char_to_dir mapping (wigan → wigan directory)
  - Has ending descriptions for A/B/C
"""

from __future__ import annotations

from pathlib import Path

from wet_run.engine.chapter_view import chapter_for_character
from wet_run.engine.graphic_novel_view import (
    GN_MENU_WIGAN,
    _character_label,
    available_endings,
    get_gn_menu_key,
    get_gn_menu_options,
    list_scenes_for_character,
    load_scene_chain,
)

SCENES_DIR = Path(__file__).resolve().parents[2] / "data" / "scenes"
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class TestWiganScenesExist:
    def test_wigan_scenes_dir_exists(self) -> None:
        wigan_dir = SCENES_DIR / "wigan"
        assert wigan_dir.exists(), "data/scenes/wigan/ should exist for Phase 7.1"

    def test_wigan_has_nine_scenes(self) -> None:
        """Wigan character has 4 base + 4 ending = 8 scenes."""
        stems = list_scenes_for_character(SCENES_DIR, "wigan")
        assert len(stems) == 9, f"Expected 8 wigan scene files, got {len(stems)}: {stems}"

    def test_wigan_scenes_load_ending_a(self) -> None:
        """4 ending A scenes for Wigan."""
        chain = load_scene_chain(SCENES_DIR, "wigan", ending="A", max_order=8)
        assert len(chain) == 4
        for s in chain:
            assert s.character == "wigan"
            assert s.ending == "A"

    def test_wigan_scenes_load_ending_b(self) -> None:
        """2 ending B scenes for Wigan (offering + dissolve)."""
        chain = load_scene_chain(SCENES_DIR, "wigan", ending="B")
        assert len(chain) == 2
        for s in chain:
            assert s.character == "wigan"
            assert s.ending == "B"


class TestWiganMenuOption:
    def test_wigan_constant_defined(self) -> None:
        assert GN_MENU_WIGAN == "wigan"

    def test_wigan_in_menu_options_without_save(self) -> None:
        """10 total options: prologue + 7 chars + suit + wigan + sally + back (Phase 9 added 3jane)."""
        from wet_run.i18n import Translator

        t = Translator("en")
        options = get_gn_menu_options(t, has_save=False)
        keys = [k for k, _ in options]
        # 10 menu keys + 1 empty BACK key
        assert len(options) == 11
        # Wigan is the 6th option (index 5) when no save
        assert keys[5] == "6"

    def test_wigan_in_menu_options_with_save(self) -> None:
        from wet_run.i18n import Translator

        t = Translator("en")
        options = get_gn_menu_options(t, has_save=True)
        keys = [k for k, _ in options]
        # CONTINUE + 9 menu keys + BACK = 11 options
        assert len(options) == 12
        # Wigan is the 6th menu key (index 6) with save
        assert keys[6] == "7"

    def test_get_menu_key_wigan_index(self) -> None:
        """Wigan = index 5 (no save) or index 6 (with save)."""
        assert get_gn_menu_key(has_save=False, selected_index=5) == GN_MENU_WIGAN
        assert get_gn_menu_key(has_save=True, selected_index=6) == GN_MENU_WIGAN


class TestWiganCharacterLabel:
    def test_label_en(self) -> None:
        label = _character_label("wigan", "en")
        assert "Wigan" in label
        assert "Vodou" in label or "Construct" in label

    def test_label_ko(self) -> None:
        label = _character_label("wigan", "ko")
        assert "위건" in label
        assert "부두" in label


class TestWiganEndings:
    def test_three_endings_available(self) -> None:
        """Wigan has 3 endings (A/B/C)."""
        endings = available_endings("wigan")
        assert endings == ["A", "B", "C"]


class TestWiganChapter:
    def test_chapter_for_wigan_loads(self) -> None:
        chapter = chapter_for_character("wigan", DATA_DIR)
        assert chapter.id == "chapter_wigan"
        assert chapter.character == "wigan"
        assert chapter.excerpt_en
        assert chapter.excerpt_ko
        # Wigan-specific theme
        assert chapter.theme == "loa_network"


class TestPrologueWithWigan:
    def test_prologue_includes_wigan(self) -> None:
        from wet_run.engine.graphic_novel_view import load_prologue_chain

        chain = load_prologue_chain(SCENES_DIR, seed=42)
        wigan_scenes = [s for s in chain if s.character == "wigan"]
        assert len(wigan_scenes) == 4

    def test_prologue_has_6_characters(self) -> None:
        from wet_run.engine.graphic_novel_view import load_prologue_chain

        chain = load_prologue_chain(SCENES_DIR, seed=42)
        chars = {s.character for s in chain}
        assert chars.issuperset({"novice", "veteran", "heretic", "suit", "wigan", "angie"})
