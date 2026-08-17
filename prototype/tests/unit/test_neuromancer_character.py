"""Tests for Neuromancer (9th and final) character integration (Phase 9).

Neuromancer is the merged AI consciousness (Wintermute + Neuromancer),
introduced 2026-07-04. It has:
  - 8 scenes in data/scenes/neuromancer/ (4 base + 4 ending)
  - Added to GN menu as 9th character option
  - Added to char_to_dir mapping (neuromancer → neuromancer)
  - Has ending descriptions for A/B/C
"""

from __future__ import annotations

from pathlib import Path

from wet_run.engine.chapter_view import chapter_for_character
from wet_run.engine.graphic_novel_view import (
    GN_MENU_NEUROMANCER,
    _character_label,
    available_endings,
    get_gn_menu_key,
    list_scenes_for_character,
)

SCENES_DIR = Path(__file__).resolve().parents[2] / "data" / "scenes"
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class TestNeuromancerScenesExist:
    def test_neuromancer_scenes_dir_exists(self) -> None:
        d = SCENES_DIR / "neuromancer"
        assert d.exists(), "data/scenes/neuromancer/ should exist for Phase 9"

    def test_neuromancer_has_nine_scenes(self) -> None:
        stems = list_scenes_for_character(SCENES_DIR, "neuromancer")
        assert len(stems) == 9, f"Expected 8 scenes, got {len(stems)}: {stems}"


class TestNeuromancerMenuOption:
    def test_neuromancer_constant_defined(self) -> None:
        assert GN_MENU_NEUROMANCER == "neuromancer"

    def test_neuromancer_in_menu_options_without_save(self) -> None:
        from wet_run.i18n import Translator

        t = Translator("en")
        options = get_gn_menu_key.__globals__["get_gn_menu_options"](t, has_save=False)
        # 10 menu keys + 1 BACK = 11 total
        assert len(options) == 11
        # Neuromancer is the 10th option (index 9)
        assert options[9][0] == "A"  # 10th option key is "A" (after 0-9)

    def test_neuromancer_in_menu_options_with_save(self) -> None:
        from wet_run.i18n import Translator

        t = Translator("en")
        options = get_gn_menu_key.__globals__["get_gn_menu_options"](t, has_save=True)
        # CONTINUE + 10 menu keys + BACK = 12
        assert len(options) == 12

    def test_get_menu_key_neuromancer_index(self) -> None:
        """Neuromancer = index 9 (no save) or index 10 (with save)."""
        assert get_gn_menu_key(has_save=False, selected_index=9) == GN_MENU_NEUROMANCER


class TestNeuromancerCharacterLabel:
    def test_label_en(self) -> None:
        label = _character_label("neuromancer", "en")
        assert "Neuromancer" in label
        assert "Merged" in label or "AI" in label

    def test_label_ko(self) -> None:
        label = _character_label("neuromancer", "ko")
        assert "뉴로맨서" in label
        assert "합체" in label or "AI" in label


class TestNeuromancerEndings:
    def test_three_endings_available(self) -> None:
        endings = available_endings("neuromancer")
        assert endings == ["A", "B", "C"]


class TestNeuromancerChapter:
    def test_chapter_for_neuromancer_loads(self) -> None:
        chapter = chapter_for_character("neuromancer", DATA_DIR)
        assert chapter.id == "chapter_neuromancer"
        assert chapter.character == "neuromancer"
        assert chapter.excerpt_en
        assert chapter.excerpt_ko
        assert chapter.theme == "matrix_vast"


class TestPrologueWithNeuromancer:
    def test_prologue_includes_neuromancer(self) -> None:
        from wet_run.engine.graphic_novel_view import load_prologue_chain

        chain = load_prologue_chain(SCENES_DIR, seed=42)
        jane_scenes = [s for s in chain if s.character == "neuromancer"]
        assert len(jane_scenes) == 4

    def test_prologue_has_9_characters(self) -> None:
        from wet_run.engine.graphic_novel_view import load_prologue_chain

        chain = load_prologue_chain(SCENES_DIR, seed=42)
        chars = {s.character for s in chain}
        assert chars.issuperset(
            {
                "novice",
                "veteran",
                "heretic",
                "suit",
                "wigan",
                "angie",
                "sally",
                "3jane",
                "neuromancer",
            }
        )
