"""Tests for the Suit (4th) character integration (Phase 6.1).

The Suit character is a 3인칭 corporate fixer/perspective introduced in
2026-07-04. It has:
  - 4 scenes in data/scenes/suit/ (one per suit short story)
  - Added to GN menu as 4th character option
  - Added to char_to_dir mapping (suit → suit directory)
  - Has ending descriptions for A/B/C
"""

from __future__ import annotations

from pathlib import Path

from wet_run.engine.chapter_view import chapter_for_character
from wet_run.engine.graphic_novel_view import (
    GN_MENU_SUIT,
    _character_label,
    available_endings,
    get_gn_menu_key,
    get_gn_menu_options,
    list_scenes_for_character,
    load_scene_chain,
)

SCENES_DIR = Path(__file__).resolve().parents[2] / "data" / "scenes"
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class TestSuitScenesExist:
    def test_suit_scenes_dir_exists(self) -> None:
        suit_dir = SCENES_DIR / "suit"
        assert suit_dir.exists(), "data/scenes/suit/ should exist for Phase 6.1"

    def test_suit_has_nine_scenes(self) -> None:
        """Suit character has 4 base scenes (one per suit short story).

        Plus 4 ending scenes (B and C) = 8 total files. The base
        list_scenes_for_character returns 8 stems but only 4 are
        used for ending A.
        """
        stems = list_scenes_for_character(SCENES_DIR, "suit")
        # 4 base + 4 ending = 8 files
        assert len(stems) == 9, f"Expected 8 suit scene files, got {len(stems)}: {stems}"

    def test_suit_scenes_load(self) -> None:
        """All 4 suit scenes must parse as valid SceneData."""
        chain = load_scene_chain(SCENES_DIR, "suit", ending="A")
        assert len(chain) == 4
        for s in chain:
            assert s.character == "suit"
            assert s.ending == "A"
            assert len(s.dialogue) >= 1


class TestSuitMenuOption:
    def test_suit_constant_defined(self) -> None:
        assert GN_MENU_SUIT == "suit"

    def test_suit_in_menu_options_without_save(self) -> None:
        """8 visible options: prologue + 6 chars + suit + back = 9 (Phase 8 added sally)."""
        from wet_run.i18n import Translator

        t = Translator("en")
        options = get_gn_menu_options(t, has_save=False)
        keys = [k for k, _ in options]
        # 10 menu keys + 1 empty BACK key
        assert len(options) == 11
        # Suit is the 5th option (index 4) when no save
        assert keys[4] == "5"

    def test_suit_in_menu_options_with_save(self) -> None:
        from wet_run.i18n import Translator

        t = Translator("en")
        options = get_gn_menu_options(t, has_save=True)
        keys = [k for k, _ in options]
        # CONTINUE + 9 menu keys + BACK = 11 options
        assert len(options) == 12
        # Suit is the 5th menu key (index 5) with save
        assert keys[5] == "6"

    def test_get_menu_key_suit_index(self) -> None:
        """Suit = index 4 (no save) or index 5 (with save)."""
        assert get_gn_menu_key(has_save=False, selected_index=4) == GN_MENU_SUIT
        assert get_gn_menu_key(has_save=True, selected_index=5) == GN_MENU_SUIT


class TestSuitCharacterLabel:
    def test_label_en(self) -> None:
        label = _character_label("suit", "en")
        assert "Suit" in label
        assert "Corporate" in label

    def test_label_ko(self) -> None:
        label = _character_label("suit", "ko")
        assert "스위트" in label
        assert "기업" in label


class TestSuitEndings:
    def test_three_endings_available(self) -> None:
        """Suit has 3 endings (A/B/C) per ADR-0048/0049."""
        endings = available_endings("suit")
        assert endings == ["A", "B", "C"]


class TestSuitChapter:
    def test_chapter_for_suit_loads(self) -> None:
        """chapter_for_character('suit') should load prototype/data/story/chapters/suit.json."""
        chapter = chapter_for_character("suit", DATA_DIR)
        assert chapter.id == "chapter_suit"
        assert chapter.character == "suit"
        # Should have excerpt
        assert chapter.excerpt_en
        assert chapter.excerpt_ko
        # Suit chapter should mention Armitage in the excerpt
        assert "Armitage" in chapter.excerpt_en or "Armitage" in chapter.excerpt_ko
        # Suit-specific fields
        assert chapter.portrait == "art:armitage"
        assert chapter.theme == "tessier_ashpool_lab"


class TestPrologueWithSuit:
    def test_prologue_includes_suit(self) -> None:
        """Prologue chain should include 4 suit scenes when ending='A'."""
        from wet_run.engine.graphic_novel_view import load_prologue_chain

        chain = load_prologue_chain(SCENES_DIR, seed=42)
        suit_scenes = [s for s in chain if s.character == "suit"]
        assert len(suit_scenes) == 4
