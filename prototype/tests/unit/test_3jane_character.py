"""Tests for 3Jane (8th) character integration (Phase 9).

3Jane Tessier-Ashpool is the T-A family heir from Neuromancer,
introduced 2026-07-04. She has:
  - 8 scenes in data/scenes/3jane/ (4 base + 4 ending)
  - Added to GN menu as 8th character option
  - Added to char_to_dir mapping (3jane → 3jane)
  - Has ending descriptions for A/B/C
"""

from __future__ import annotations

from pathlib import Path

from wet_run.engine.chapter_view import chapter_for_character
from wet_run.engine.graphic_novel_view import (
    GN_MENU_3JANE,
    _character_label,
    available_endings,
    get_gn_menu_key,
    get_gn_menu_options,
    list_scenes_for_character,
    load_scene_chain,
)

SCENES_DIR = Path(__file__).resolve().parents[2] / "data" / "scenes"
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class Test3JaneScenesExist:
    def test_3jane_scenes_dir_exists(self) -> None:
        d = SCENES_DIR / "3jane"
        assert d.exists(), "data/scenes/3jane/ should exist for Phase 9"

    def test_3jane_has_nine_scenes(self) -> None:
        stems = list_scenes_for_character(SCENES_DIR, "3jane")
        assert len(stems) == 9, f"Expected 8 scenes, got {len(stems)}: {stems}"

    def test_3jane_scenes_load_ending_a(self) -> None:
        chain = load_scene_chain(SCENES_DIR, "3jane", ending="A", max_order=8)
        assert len(chain) == 4
        for s in chain:
            assert s.character == "3jane"
            assert s.ending == "A"

    def test_3jane_scenes_load_ending_b(self) -> None:
        chain = load_scene_chain(SCENES_DIR, "3jane", ending="B")
        assert len(chain) == 2
        for s in chain:
            assert s.character == "3jane"
            assert s.ending == "B"

    def test_3jane_scenes_load_ending_c(self) -> None:
        chain = load_scene_chain(SCENES_DIR, "3jane", ending="C")
        assert len(chain) == 2
        for s in chain:
            assert s.character == "3jane"
            assert s.ending == "C"


class Test3JaneMenuOption:
    def test_3jane_constant_defined(self) -> None:
        assert GN_MENU_3JANE == "3jane"

    def test_3jane_in_menu_options_without_save(self) -> None:
        from wet_run.i18n import Translator

        t = Translator("en")
        options = get_gn_menu_options(t, has_save=False)
        keys = [k for k, _ in options]
        # 10 menu keys + 1 empty BACK key
        assert len(options) == 11
        # 3Jane is the 9th option (index 8) when no save
        assert keys[8] == "9"

    def test_3jane_in_menu_options_with_save(self) -> None:
        from wet_run.i18n import Translator

        t = Translator("en")
        options = get_gn_menu_options(t, has_save=True)
        keys = [k for k, _ in options]
        # CONTINUE + 10 menu keys + BACK = 12 options
        assert len(options) == 12
        # 3Jane is the 9th menu key (index 9) with save
        assert keys[9] == "A"

    def test_get_menu_key_3jane_index(self) -> None:
        assert get_gn_menu_key(has_save=False, selected_index=8) == GN_MENU_3JANE


class Test3JaneCharacterLabel:
    def test_label_en(self) -> None:
        label = _character_label("3jane", "en")
        assert "3Jane" in label
        assert "Family" in label or "Heir" in label

    def test_label_ko(self) -> None:
        label = _character_label("3jane", "ko")
        assert "3Jane" in label
        assert "가족" in label or "후계자" in label


class Test3JaneEndings:
    def test_three_endings_available(self) -> None:
        endings = available_endings("3jane")
        assert endings == ["A", "B", "C"]


class Test3JaneChapter:
    def test_chapter_for_3jane_loads(self) -> None:
        chapter = chapter_for_character("3jane", DATA_DIR)
        assert chapter.id == "chapter_3jane"
        assert chapter.character == "3jane"
        assert chapter.excerpt_en
        assert chapter.excerpt_ko
        assert chapter.theme == "tessier_ashpool_lab"


class TestPrologueWith3Jane:
    def test_prologue_includes_3jane(self) -> None:
        from wet_run.engine.graphic_novel_view import load_prologue_chain

        chain = load_prologue_chain(SCENES_DIR, seed=42)
        jane_scenes = [s for s in chain if s.character == "3jane"]
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
            }
        )
