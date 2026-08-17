"""Tests for ADR-0048 + ADR-0049: GN ending menu (A/B/C) + Save 1.1.0→1.2.0.

Covers:
    - render_graphic_novel_ending_menu: 3 options, character header
    - handle_graphic_novel_ending_menu_input: N1→A, N2→B, N3/ESC→back
    - get_gn_ending_menu_options: 3 options including BACK
    - GNProgress.ending field: default "A", from_dict accepts "B"
    - GNProgress v1.0.0 migration (no `ending` key) → default "A"
    - GNProgress v1.2.0 with `ending` A/B/C → preserved
    - GN_SAVE_VERSION bumped to "1.2.0" (1.1.0 → 1.2.0 added "C", ADR-0049)
    - make_progress accepts ending parameter
    - State transition: GRAPHIC_NOVEL_MENU → GRAPHIC_NOVEL_ENDING_MENU → GRAPHIC_NOVEL
    - gn_ending_choice state field defaults to "A"
    - i18n: Korean + English option labels
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import tcod.console  # noqa: E402

from wet_run.engine.graphic_novel_save import (  # noqa: E402
    GN_SAVE_VERSION,
    GNProgress,
    load_gn_progress,
    make_progress,
    save_gn_progress,
)
from wet_run.engine.graphic_novel_view import (  # noqa: E402
    GN_ENDING_A,
    GN_ENDING_B,
    GN_ENDING_BACK,
    get_gn_ending_menu_options,
    render_graphic_novel_ending_menu,
)
from wet_run.engine.menu import (  # noqa: E402
    handle_graphic_novel_ending_menu_input,
)
from wet_run.engine.state import AppState  # noqa: E402
from wet_run.i18n import Translator  # noqa: E402

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def translator_en() -> Translator:
    return Translator("en", data_dir=Path(__file__).parent.parent.parent / "data" / "i18n")


@pytest.fixture
def translator_ko() -> Translator:
    return Translator("ko", data_dir=Path(__file__).parent.parent.parent / "data" / "i18n")


def _key(sym: object) -> tcod.event.KeyDown:  # noqa: F821
    """Build a real KeyDown event with the given symbol."""
    from tcod.event import KeyDown

    return KeyDown(sym=sym, scancode=0, mod=0, repeat=0)


# ============================================================================
# 1. State field
# ============================================================================


class TestStateField:
    def test_gn_ending_choice_default_is_a(self) -> None:
        state = AppState()
        assert state.gn_ending_choice == "A"

    def test_gn_ending_choice_can_be_set(self) -> None:
        state = AppState()
        state.gn_ending_choice = "B"
        assert state.gn_ending_choice == "B"


# ============================================================================
# 2. GN_SAVE_VERSION bump
# ============================================================================


class TestSaveVersion:
    def test_version_is_1_2_0(self) -> None:
        assert GN_SAVE_VERSION == "1.2.0"

    def test_version_format(self) -> None:
        parts = GN_SAVE_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


# ============================================================================
# 3. GNProgress ending field
# ============================================================================


class TestGNProgressEnding:
    def test_default_ending_is_a(self) -> None:
        p = make_progress(
            mode="novice",
            scene_index=0,
            dialogue_index=0,
            elapsed_in_dialogue_ms=0.0,
            character_id="novice",
            chain_length=4,
        )
        assert p.ending == "A"

    def test_make_progress_with_ending_a(self) -> None:
        p = make_progress(
            mode="novice",
            scene_index=0,
            dialogue_index=0,
            elapsed_in_dialogue_ms=0.0,
            character_id="novice",
            chain_length=4,
            ending="A",
        )
        assert p.ending == "A"

    def test_make_progress_with_ending_b(self) -> None:
        p = make_progress(
            mode="novice",
            scene_index=1,
            dialogue_index=2,
            elapsed_in_dialogue_ms=500.0,
            character_id="novice",
            chain_length=4,
            ending="B",
        )
        assert p.ending == "B"

    def test_to_dict_includes_ending(self) -> None:
        p = make_progress(
            mode="veteran",
            scene_index=0,
            dialogue_index=0,
            elapsed_in_dialogue_ms=0.0,
            character_id="veteran",
            chain_length=4,
            ending="B",
        )
        d = p.to_dict()
        assert d["ending"] == "B"

    def test_from_dict_with_ending_b(self) -> None:
        data = {
            "mode": "novice",
            "scene_index": 2,
            "dialogue_index": 1,
            "elapsed_in_dialogue_ms": 100.0,
            "character_id": "novice",
            "chain_length": 4,
            "saved_at": "2026-06-21T12:00:00Z",
            "ending": "B",
            "session_id": "abc123",
        }
        p = GNProgress.from_dict(data)
        assert p.ending == "B"

    def test_from_dict_missing_ending_defaults_to_a(self) -> None:
        """ADR-0048: backward-compat — v1.0.0 saves have no `ending` key."""
        data = {
            "mode": "novice",
            "scene_index": 2,
            "dialogue_index": 1,
            "elapsed_in_dialogue_ms": 100.0,
            "character_id": "novice",
            "chain_length": 4,
            "saved_at": "2026-06-21T12:00:00Z",
            "session_id": "abc123",
        }
        p = GNProgress.from_dict(data)
        assert p.ending == "A"

    def test_from_dict_invalid_ending_defaults_to_a(self) -> None:
        """Forward-compat: unknown values fall back to A."""
        data = {
            "mode": "novice",
            "scene_index": 0,
            "dialogue_index": 0,
            "elapsed_in_dialogue_ms": 0.0,
            "character_id": "novice",
            "chain_length": 4,
            "saved_at": "2026-06-21T12:00:00Z",
            "ending": "Z",  # future ending not yet supported
            "session_id": "abc",
        }
        p = GNProgress.from_dict(data)
        assert p.ending == "A"

    def test_round_trip_preserves_ending(self) -> None:
        original = make_progress(
            mode="heretic",
            scene_index=3,
            dialogue_index=5,
            elapsed_in_dialogue_ms=1500.0,
            character_id="heretic",
            chain_length=4,
            ending="B",
        )
        restored = GNProgress.from_dict(original.to_dict())
        assert restored.ending == original.ending
        assert restored.mode == original.mode
        assert restored.scene_index == original.scene_index


# ============================================================================
# 4. Save migration (file-level)
# ============================================================================


class TestSaveMigration:
    def test_save_creates_with_ending_b(self, tmp_path: Path) -> None:
        save_path = tmp_path / "gn_progress.json"
        progress = make_progress(
            mode="novice",
            scene_index=1,
            dialogue_index=0,
            elapsed_in_dialogue_ms=200.0,
            character_id="novice",
            chain_length=4,
            ending="B",
        )
        save_gn_progress(progress, save_path)
        assert save_path.exists()
        payload = json.loads(save_path.read_text(encoding="utf-8"))
        assert payload["version"] == "1.2.0"
        assert payload["progress"]["ending"] == "B"

    def test_load_v1_0_0_save_defaults_to_a(self, tmp_path: Path) -> None:
        """Simulate a v1.0.0 save (no `ending` key) — must still load."""
        save_path = tmp_path / "gn_progress.json"
        payload = {
            "version": "1.2.0",  # current version (file is "fresh")
            "saved_at": "2026-06-21T00:00:00Z",
            "progress": {
                "mode": "novice",
                "scene_index": 0,
                "dialogue_index": 0,
                "elapsed_in_dialogue_ms": 0.0,
                "character_id": "novice",
                "chain_length": 4,
                "saved_at": "2026-06-21T00:00:00Z",
                "session_id": "legacy01",
                # NO `ending` key (simulates v1.0.0 migration path)
            },
        }
        save_path.write_text(json.dumps(payload), encoding="utf-8")
        loaded = load_gn_progress(save_path)
        assert loaded.ending == "A"
        assert loaded.mode == "novice"

    def test_load_v1_1_0_save_preserves_b(self, tmp_path: Path) -> None:
        save_path = tmp_path / "gn_progress.json"
        progress = make_progress(
            mode="veteran",
            scene_index=2,
            dialogue_index=1,
            elapsed_in_dialogue_ms=300.0,
            character_id="veteran",
            chain_length=4,
            ending="B",
        )
        save_gn_progress(progress, save_path)
        loaded = load_gn_progress(save_path)
        assert loaded.ending == "B"
        assert loaded.scene_index == 2


# ============================================================================
# 5. get_gn_ending_menu_options
# ============================================================================


class TestGetEndingMenuOptions:
    def test_returns_four_options(self, translator_en: Translator) -> None:
        opts = get_gn_ending_menu_options(translator_en, "novice")
        assert len(opts) == 4  # A, B, C, BACK (ADR-0049)

    def test_option_keys_for_english(self, translator_en: Translator) -> None:
        opts = get_gn_ending_menu_options(translator_en, "novice")
        keys = [k for k, _ in opts]
        assert keys[0] == "1"
        assert keys[1] == "2"
        assert keys[2] == "3"  # C (ADR-0049)
        assert keys[3] == ""  # BACK has no key

    def test_english_labels_contain_ending(self, translator_en: Translator) -> None:
        opts = get_gn_ending_menu_options(translator_en, "novice")
        a_label = opts[0][1]
        b_label = opts[1][1]
        assert "ENDING A" in a_label
        assert "ENDING B" in b_label

    def test_korean_labels_contain_ending(self, translator_ko: Translator) -> None:
        opts = get_gn_ending_menu_options(translator_ko, "novice")
        a_label = opts[0][1]
        b_label = opts[1][1]
        assert "엔딩 A" in a_label
        assert "엔딩 B" in b_label

    def test_all_three_characters(self, translator_en: Translator) -> None:
        for char in ("novice", "veteran", "heretic"):
            opts = get_gn_ending_menu_options(translator_en, char)
            assert len(opts) == 4  # A/B/C + BACK

    def test_back_option_present(self, translator_en: Translator) -> None:
        opts = get_gn_ending_menu_options(translator_en, "heretic")
        # BACK is the last option (after A/B/C)
        back_label = opts[-1][1]
        assert "BACK" in back_label.upper()


# ============================================================================
# 6. handle_graphic_novel_ending_menu_input
# ============================================================================


class TestEndingMenuInput:
    def test_n1_returns_a(self) -> None:
        from tcod.event import KeySym

        state = AppState()
        state.gn_mode = "novice"
        result = handle_graphic_novel_ending_menu_input(_key(KeySym.N1), state)
        assert result == "A"

    def test_n2_returns_b(self) -> None:
        from tcod.event import KeySym

        state = AppState()
        state.gn_mode = "novice"
        result = handle_graphic_novel_ending_menu_input(_key(KeySym.N2), state)
        assert result == "B"

    def test_n4_returns_back(self) -> None:
        from tcod.event import KeySym

        state = AppState()
        state.gn_mode = "novice"
        result = handle_graphic_novel_ending_menu_input(_key(KeySym.N4), state)
        assert result == "back"

    def test_escape_returns_back(self) -> None:
        from tcod.event import KeySym

        result = handle_graphic_novel_ending_menu_input(_key(KeySym.ESCAPE), AppState())
        assert result == "back"

    def test_q_returns_back(self) -> None:
        from tcod.event import KeySym

        result = handle_graphic_novel_ending_menu_input(_key(KeySym.Q), AppState())
        assert result == "back"

    def test_unmapped_returns_empty(self) -> None:
        from tcod.event import KeySym

        result = handle_graphic_novel_ending_menu_input(_key(KeySym.A), AppState())
        assert result == ""


# ============================================================================
# 7. render_graphic_novel_ending_menu
# ============================================================================


class TestRenderEndingMenu:
    def test_render_does_not_raise(self, translator_en: Translator) -> None:
        console = tcod.console.Console(80, 30, order="F")
        render_graphic_novel_ending_menu(console, translator_en, "novice", selected_index=0)

    def test_render_korean_does_not_raise(self, translator_ko: Translator) -> None:
        console = tcod.console.Console(80, 30, order="F")
        render_graphic_novel_ending_menu(console, translator_ko, "heretic", selected_index=1)

    def test_render_includes_character_label(self, translator_en: Translator) -> None:
        console = tcod.console.Console(80, 30, order="F")
        render_graphic_novel_ending_menu(console, translator_en, "veteran", selected_index=0)
        # Check console has the character label
        text_lines = []
        for y in range(console.height):
            row = []
            for x in range(console.width):
                ch = int(console.ch[x, y])
                row.append(chr(ch) if 0 < ch < 0x110000 else " ")
            text_lines.append("".join(row))
        full_text = "\n".join(text_lines)
        assert "Sil" in full_text or "Veteran" in full_text

    def test_render_four_options(self, translator_en: Translator) -> None:
        console = tcod.console.Console(80, 30, order="F")
        render_graphic_novel_ending_menu(console, translator_en, "novice", selected_index=0)
        text_lines = []
        for y in range(console.height):
            row = []
            for x in range(console.width):
                ch = int(console.ch[x, y])
                row.append(chr(ch) if 0 < ch < 0x110000 else " ")
            text_lines.append("".join(row))
        full_text = "\n".join(text_lines)
        assert "ENDING A" in full_text
        assert "ENDING B" in full_text
        assert "BACK" in full_text


# ============================================================================
# 8. GN ending constants
# ============================================================================


class TestEndingConstants:
    def test_ending_a_constant(self) -> None:
        assert GN_ENDING_A == "A"

    def test_ending_b_constant(self) -> None:
        assert GN_ENDING_B == "B"

    def test_back_constant(self) -> None:
        assert GN_ENDING_BACK == "back"


# ============================================================================
# 9. Screen kind exists
# ============================================================================


class TestScreenKind:
    def test_ending_menu_screen_exists(self) -> None:
        from wet_run.engine.state import ScreenKind

        assert hasattr(ScreenKind, "GRAPHIC_NOVEL_ENDING_MENU")
        assert ScreenKind.GRAPHIC_NOVEL_ENDING_MENU.value == "graphic_novel_ending_menu"
