"""Tests for Salvation Phase engine (Phase 9).

Salvation Phase is entered after Chapter 5 completion:
- SALVATION_INTRO: select 1 of 9 character epilogues
- SALVATION_EPILOGUE: play epilogue scene
- SALVATION_DONE: choose ENDING_A/B/C
- FINAL: return to Hub
"""

from __future__ import annotations

from pathlib import Path

import pytest

from wet_run.engine.salvation import (
    SALVATION_ENDINGS,
    SALVATION_EPILOGUES,
    SalvationSelection,
    format_salvation_ending_menu,
    format_salvation_menu,
    get_epilogue_ending,
    get_epilogue_paths,
    get_epilogue_scene_id,
    list_available_epilogues,
    validate_epilogue_selection,
)


class TestSalvationEpilogues:
    """SALVATION_EPILOGUES dict structure."""

    def test_all_nine_characters_defined(self) -> None:
        assert len(SALVATION_EPILOGUES) == 9

    def test_all_keys_are_character_ids(self) -> None:
        expected = {"case", "sil", "kas", "suit", "wigan", "angie", "sally", "3jane", "neuromancer"}
        assert set(SALVATION_EPILOGUES.keys()) == expected

    def test_all_entries_have_required_fields(self) -> None:
        required = {"name_en", "name_ko", "scene_id", "ending", "tagline_en", "tagline_ko"}
        for char_id, entry in SALVATION_EPILOGUES.items():
            missing = required - set(entry.keys())
            assert not missing, f"{char_id} missing fields: {missing}"

    def test_all_scene_ids_end_with_epilogue(self) -> None:
        for char_id, entry in SALVATION_EPILOGUES.items():
            assert entry["scene_id"].endswith("_epilogue"), (
                f"{char_id} scene_id should end with _epilogue: {entry['scene_id']}"
            )

    def test_all_endings_are_valid(self) -> None:
        for char_id, entry in SALVATION_EPILOGUES.items():
            assert entry["ending"] in SALVATION_ENDINGS, (
                f"{char_id} ending {entry['ending']} not in {SALVATION_ENDINGS}"
            )


class TestSalvationEndings:
    """SALVATION_ENDINGS list."""

    def test_three_endings(self) -> None:
        assert SALVATION_ENDINGS == ["A", "B", "C"]


class TestListAvailableEpilogues:
    """list_available_epilogues function."""

    def test_default_english(self) -> None:
        result = list_available_epilogues()
        assert len(result) == 9
        # First entry should be case
        assert result[0][0] == "case"
        # All entries have non-empty labels
        for char_id, label in result:
            assert len(label) > 0

    def test_korean_labels(self) -> None:
        result = list_available_epilogues(lang="ko")
        for char_id, label in result:
            # Korean labels: case=케이, sil=실, etc.
            assert char_id in SALVATION_EPILOGUES


class TestGetEpilogueSceneId:
    """get_epilogue_scene_id function."""

    def test_known_character(self) -> None:
        assert get_epilogue_scene_id("case") == "scene_case_epilogue"
        assert get_epilogue_scene_id("sally") == "scene_sally_epilogue"
        assert get_epilogue_scene_id("neuromancer") == "scene_neuromancer_epilogue"

    def test_unknown_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            get_epilogue_scene_id("nonexistent")


class TestGetEpilogueEnding:
    """get_epilogue_ending function."""

    def test_known_character(self) -> None:
        assert get_epilogue_ending("kas") == "C"
        assert get_epilogue_ending("suit") == "B"
        assert get_epilogue_ending("case") == "A"

    def test_unknown_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            get_epilogue_ending("nonexistent")


class TestFormatSalvationMenu:
    """format_salvation_menu function."""

    def test_english_contains_all_characters(self) -> None:
        menu = format_salvation_menu("en")
        for char_id in SALVATION_EPILOGUES:
            assert (
                char_id.upper() in menu.upper() or SALVATION_EPILOGUES[char_id]["name_en"] in menu
            )

    def test_korean_contains_korean_names(self) -> None:
        menu = format_salvation_menu("ko")
        assert "케이" in menu  # Case Korean
        assert "샐리" in menu  # Sally Korean

    def test_ends_with_prompt(self) -> None:
        menu = format_salvation_menu("en")
        assert "Select" in menu


class TestFormatSalvationEndingMenu:
    """format_salvation_ending_menu function."""

    def test_english_shows_a_b_c(self) -> None:
        menu = format_salvation_ending_menu("en")
        assert "[A]" in menu
        assert "[B]" in menu
        assert "[C]" in menu

    def test_korean_shows_a_b_c(self) -> None:
        menu = format_salvation_ending_menu("ko")
        assert "[A]" in menu
        assert "[B]" in menu
        assert "[C]" in menu


class TestValidateEpilogueSelection:
    """validate_epilogue_selection function."""

    def test_valid_returns_scene_id(self) -> None:
        assert validate_epilogue_selection("case") == "scene_case_epilogue"

    def test_invalid_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid epilogue character"):
            validate_epilogue_selection("nonexistent")


class TestGetEpiloguePaths:
    """get_epilogue_paths function."""

    def test_returns_nine_paths(self, tmp_path: Path) -> None:
        # Create 9 character directories with epilogue files
        for char_id in SALVATION_EPILOGUES:
            char_dir = tmp_path / char_id
            char_dir.mkdir()
            (char_dir / f"scene_{char_id}_epilogue.json").write_text("{}")
        paths = get_epilogue_paths(tmp_path)
        assert len(paths) == 9

    def test_paths_use_scene_id_pattern(self, tmp_path: Path) -> None:
        paths = get_epilogue_paths(tmp_path)
        assert paths["case"] == tmp_path / "case" / "scene_case_epilogue.json"
        assert paths["neuromancer"] == tmp_path / "neuromancer" / "scene_neuromancer_epilogue.json"

    def test_paths_constructed_even_if_files_missing(self, tmp_path: Path) -> None:
        # Don't create any files, just construct paths
        paths = get_epilogue_paths(tmp_path)
        # All 9 paths should be returned regardless
        assert len(paths) == 9
        assert not paths["case"].exists()


class TestSalvationSelection:
    """SalvationSelection dataclass."""

    def test_create(self) -> None:
        s = SalvationSelection(character_id="case", ending="A", selected_at=1)
        assert s.character_id == "case"
        assert s.ending == "A"
        assert s.selected_at == 1

    def test_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        s = SalvationSelection(character_id="case", ending="A", selected_at=1)
        with pytest.raises(FrozenInstanceError):
            s.character_id = "sally"  # type: ignore[misc]


class TestSalvationRunner:
    """SalvationRunner state machine."""

    def test_initial_state(self) -> None:
        from wet_run.engine.salvation import (
            SALVATION_STATE_INTRO,
            SalvationRunner,
        )

        r = SalvationRunner()
        assert r.state == SALVATION_STATE_INTRO
        assert r.selection is None
        assert r.last_scene is None

    def test_choose_epilogue_transitions(self) -> None:
        from wet_run.engine.salvation import (
            SALVATION_STATE_EPILOGUE,
            SalvationRunner,
        )

        r = SalvationRunner()
        sel = r.choose_epilogue("case")
        assert sel.character_id == "case"
        assert sel.ending == "A"
        assert sel.selected_at == 1
        assert r.state == SALVATION_STATE_EPILOGUE
        assert r.selection is sel

    def test_choose_epilogue_invalid_raises(self) -> None:
        import pytest

        from wet_run.engine.salvation import SalvationRunner

        r = SalvationRunner()
        with pytest.raises(ValueError, match="Invalid epilogue character"):
            r.choose_epilogue("nonexistent")

    def test_set_state_validates(self) -> None:
        import pytest

        from wet_run.engine.salvation import SalvationRunner

        r = SalvationRunner()
        with pytest.raises(ValueError, match="Invalid Salvation state"):
            r.set_state("invalid")

    def test_load_epilogue_requires_choice(self) -> None:
        import pytest

        from wet_run.engine.salvation import SalvationRunner

        r = SalvationRunner()
        with pytest.raises(RuntimeError, match="No epilogue chosen"):
            r.load_epilogue(Path("data/scenes"))

    def test_load_epilogue_loads_scene(self) -> None:
        from wet_run.engine.salvation import SalvationRunner

        r = SalvationRunner()
        r.choose_epilogue("neuromancer")
        scene = r.load_epilogue(Path("data/scenes"))
        assert scene.character == "neuromancer"
        assert scene.order == 9
        assert r.last_scene is scene

    def test_complete_epilogue_transitions_to_done(self) -> None:
        from wet_run.engine.salvation import (
            SALVATION_STATE_DONE,
            SalvationRunner,
        )

        r = SalvationRunner()
        r.choose_epilogue("kas")
        r.complete_epilogue()
        assert r.state == SALVATION_STATE_DONE
        assert r.selection.selected_at == 2

    def test_complete_epilogue_requires_choice(self) -> None:
        import pytest

        from wet_run.engine.salvation import SalvationRunner

        r = SalvationRunner()
        with pytest.raises(RuntimeError, match="No epilogue chosen"):
            r.complete_epilogue()

    def test_choose_ending_invalid_raises(self) -> None:
        import pytest

        from wet_run.engine.salvation import SalvationRunner

        r = SalvationRunner()
        r.choose_epilogue("case")
        r.complete_epilogue()
        with pytest.raises(ValueError, match="Invalid ending"):
            r.choose_ending("D")

    def test_choose_ending_transitions_to_final(self) -> None:
        from wet_run.engine.salvation import (
            SALVATION_STATE_FINAL,
            SalvationRunner,
        )

        r = SalvationRunner()
        r.choose_epilogue("case")
        r.complete_epilogue()
        r.choose_ending("B")
        assert r.state == SALVATION_STATE_FINAL
        assert r.selection.ending == "B"
        assert r.selection.selected_at == 3

    def test_get_state_code_returns_current_state(self) -> None:
        from wet_run.engine.salvation import SalvationRunner

        r = SalvationRunner()
        assert r.get_state_code() == "salvation_intro"
        r.choose_epilogue("case")
        assert r.get_state_code() == "salvation_epilogue"
        r.complete_epilogue()
        assert r.get_state_code() == "salvation_done"
        r.choose_ending("A")
        assert r.get_state_code() == "final"

    def test_full_flow_ending_preserved_from_epilogue(self) -> None:
        """Choose epilogue, ending defaults to epilogue's tag, then override."""
        from wet_run.engine.salvation import SalvationRunner

        # Kas has ending C
        r = SalvationRunner()
        r.choose_epilogue("kas")
        assert r.selection.ending == "C"
        r.complete_epilogue()
        # Player overrides with A
        r.choose_ending("A")
        assert r.selection.ending == "A"


class TestFormatEpilogueText:
    """format_epilogue_text TUI display helper."""

    def test_format_with_scene_data(self) -> None:
        from wet_run.engine.salvation import (
            SalvationRunner,
            format_epilogue_text,
        )

        r = SalvationRunner()
        r.choose_epilogue("case")
        r.load_epilogue(Path("data/scenes"))
        text = format_epilogue_text(r.last_scene, lang="en")
        assert "=== THE NEXT JACK ===" in text
        assert "[narrator]" in text
        assert "Ono-Sendai" in text

    def test_format_empty_dialogue(self) -> None:
        """When dialogue is empty, return placeholder."""

        # Create a fake scene with empty dialogue
        from wet_run.engine.graphic_novel_view import SceneData
        from wet_run.engine.salvation import format_epilogue_text

        scene = SceneData(
            id="fake",
            character="case",
            order=9,
            title_en="FAKE",
            title_ko="가짜",
            background_id="bg_chat_room",
            portrait_left=None,
            portrait_right=None,
            dialogue=(),
            next_scene=None,
        )
        text = format_epilogue_text(scene, lang="en")
        assert "Empty epilogue" in text

    def test_format_korean(self) -> None:
        from wet_run.engine.salvation import (
            SalvationRunner,
            format_epilogue_text,
        )

        r = SalvationRunner()
        r.choose_epilogue("neuromancer")
        r.load_epilogue(Path("data/scenes"))
        text = format_epilogue_text(r.last_scene, lang="ko")
        assert "완성" in text  # Korean title
        assert "완성이다" in text  # Korean dialogue text
        assert "매트릭스" in text  # 매트릭스


class TestSalvationStates:
    """Salvation state constants and validation."""

    def test_valid_states_frozenset(self) -> None:
        from wet_run.engine.salvation import (
            SALVATION_STATE_DONE,
            SALVATION_STATE_EPILOGUE,
            SALVATION_STATE_FINAL,
            SALVATION_STATE_INTRO,
            VALID_SALVATION_STATES,
        )

        assert SALVATION_STATE_INTRO in VALID_SALVATION_STATES
        assert SALVATION_STATE_EPILOGUE in VALID_SALVATION_STATES
        assert SALVATION_STATE_DONE in VALID_SALVATION_STATES
        assert SALVATION_STATE_FINAL in VALID_SALVATION_STATES
