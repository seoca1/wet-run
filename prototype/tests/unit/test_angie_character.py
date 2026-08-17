"""Tests for the Angie (6th) character integration (Phase 7.1).

The Angie character is a 12-year-old loa receiver — half Vodou, half
girl — introduced 2026-07-04. It has:
  - 8 scenes in data/scenes/angie/ (4 base + 4 ending)
  - Added to GN menu as 6th character option
  - Added to char_to_dir mapping (angie → angie directory)
  - Has ending descriptions for A/B/C
"""

from __future__ import annotations

from pathlib import Path

from wet_run.engine.chapter_view import chapter_for_character
from wet_run.engine.graphic_novel_view import (
    GN_MENU_ANGIE,
    _character_label,
    available_endings,
    get_gn_menu_key,
    get_gn_menu_options,
    list_scenes_for_character,
    load_scene_chain,
)

SCENES_DIR = Path(__file__).resolve().parents[2] / "data" / "scenes"
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class TestAngieScenesExist:
    def test_angie_scenes_dir_exists(self) -> None:
        angie_dir = SCENES_DIR / "angie"
        assert angie_dir.exists(), "data/scenes/angie/ should exist for Phase 7.1"

    def test_angie_has_nine_scenes(self) -> None:
        """Angie character has 4 base + 4 ending = 8 scenes."""
        stems = list_scenes_for_character(SCENES_DIR, "angie")
        assert len(stems) == 9, f"Expected 8 angie scene files, got {len(stems)}: {stems}"

    def test_angie_scenes_load_ending_a(self) -> None:
        """4 ending A scenes for Angie."""
        chain = load_scene_chain(SCENES_DIR, "angie", ending="A", max_order=8)
        assert len(chain) == 4
        for s in chain:
            assert s.character == "angie"
            assert s.ending == "A"

    def test_angie_scenes_load_ending_b(self) -> None:
        """2 ending B scenes for Angie (release + free)."""
        chain = load_scene_chain(SCENES_DIR, "angie", ending="B")
        assert len(chain) == 2
        for s in chain:
            assert s.character == "angie"
            assert s.ending == "B"


class TestAngieMenuOption:
    def test_angie_constant_defined(self) -> None:
        assert GN_MENU_ANGIE == "angie"

    def test_angie_in_menu_options_without_save(self) -> None:
        """9 total options: prologue + 6 chars + suit + wigan + angie + sally + back."""
        from wet_run.i18n import Translator

        t = Translator("en")
        options = get_gn_menu_options(t, has_save=False)
        keys = [k for k, _ in options]
        # 10 menu keys + 1 empty BACK key
        assert len(options) == 11
        # Angie is the 7th option (index 6) when no save
        assert keys[6] == "7"

    def test_angie_in_menu_options_with_save(self) -> None:
        from wet_run.i18n import Translator

        t = Translator("en")
        options = get_gn_menu_options(t, has_save=True)
        keys = [k for k, _ in options]
        # CONTINUE + 9 menu keys + BACK = 11 options
        assert len(options) == 12
        # Angie is the 7th menu key (index 7) with save
        assert keys[7] == "8"

    def test_get_menu_key_angie_index(self) -> None:
        """Angie = index 6 (no save) or index 7 (with save)."""
        assert get_gn_menu_key(has_save=False, selected_index=6) == GN_MENU_ANGIE
        assert get_gn_menu_key(has_save=True, selected_index=7) == GN_MENU_ANGIE


class TestAngieCharacterLabel:
    def test_label_en(self) -> None:
        label = _character_label("angie", "en")
        assert "Angie" in label
        assert "Loa" in label or "Receiver" in label

    def test_label_ko(self) -> None:
        label = _character_label("angie", "ko")
        assert "앤지" in label
        assert "로아" in label or "수신" in label


class TestAngieEndings:
    def test_three_endings_available(self) -> None:
        """Angie has 3 endings (A/B/C)."""
        endings = available_endings("angie")
        assert endings == ["A", "B", "C"]


class TestAngieChapter:
    def test_chapter_for_angie_loads(self) -> None:
        chapter = chapter_for_character("angie", DATA_DIR)
        assert chapter.id == "chapter_angie"
        assert chapter.character == "angie"
        assert chapter.excerpt_en
        assert chapter.excerpt_ko
        # Angie-specific theme
        assert chapter.theme == "broadcast_signal"


class TestPrologueWithAngie:
    def test_prologue_includes_angie(self) -> None:
        from wet_run.engine.graphic_novel_view import load_prologue_chain

        chain = load_prologue_chain(SCENES_DIR, seed=42)
        angie_scenes = [s for s in chain if s.character == "angie"]
        assert len(angie_scenes) == 4

    def test_prologue_has_6_characters(self) -> None:
        from wet_run.engine.graphic_novel_view import load_prologue_chain

        chain = load_prologue_chain(SCENES_DIR, seed=42)
        chars = {s.character for s in chain}
        assert chars.issuperset({"novice", "veteran", "heretic", "suit", "wigan", "angie"})
