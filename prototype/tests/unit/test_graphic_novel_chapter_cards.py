"""Tests for chapter title card and scene transition (ADR-0042).

Covers:
    - _to_roman: roman numeral conversion (1-12)
    - _character_label: localized character labels
    - render_chapter_card: layout, ornaments, fade-in transition
    - render_blank_transition: fade-out pause
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import tcod.console  # noqa: E402

from wet_run.engine.graphic_novel_view import (  # noqa: E402
    SceneData,
    _character_label,
    _to_roman,
    render_blank_transition,
    render_chapter_card,
)

# ============================================================================
# Roman numerals
# ============================================================================


class TestRomanNumerals:
    @pytest.mark.parametrize(
        ("n", "expected"),
        [
            (1, "I"),
            (2, "II"),
            (3, "III"),
            (4, "IV"),
            (5, "V"),
            (6, "VI"),
            (7, "VII"),
            (8, "VIII"),
            (9, "IX"),
            (10, "X"),
            (11, "XI"),
            (12, "XII"),
        ],
    )
    def test_roman_1_to_12(self, n: int, expected: str) -> None:
        assert _to_roman(n) == expected

    def test_roman_13_falls_back_to_arabic(self) -> None:
        assert _to_roman(13) == "13"

    def test_roman_zero_falls_back_to_arabic(self) -> None:
        assert _to_roman(0) == "0"


# ============================================================================
# Character labels
# ============================================================================


class TestCharacterLabel:
    @pytest.mark.parametrize(
        ("char_id", "lang", "expected"),
        [
            ("novice", "en", "Case (K) — Novice"),
            ("veteran", "en", "Marly (Sil) — Veteran"),
            ("heretic", "en", "Kumiko (Kas) — Heretic"),
            ("novice", "ko", "케이 (K) — Novice"),
            ("veteran", "ko", "실 (Sil) — Veteran"),
            ("heretic", "ko", "카스 (Kas) — Heretic"),
        ],
    )
    def test_character_label(self, char_id: str, lang: str, expected: str) -> None:
        assert _character_label(char_id, lang) == expected

    def test_unknown_character_returns_id(self) -> None:
        assert _character_label("unknown_char", "en") == "unknown_char"


# ============================================================================
# render_chapter_card
# ============================================================================


def _make_scene(title: str = "TEST SCENE", character: str = "novice") -> SceneData:
    return SceneData(
        id="test_scene",
        character=character,
        order=1,
        title_en=title,
        title_ko="테스트",
        background_id="",
        portrait_left=None,
        portrait_right=None,
        dialogue=(),
        next_scene=None,
    )


def _read_console(console: tcod.console.Console, y: int) -> str:
    return "".join(chr(int(console.ch[x, y])) for x in range(console.width)).rstrip()


def _read_all_console(console: tcod.console.Console) -> str:
    return "\n".join(_read_console(console, y) for y in range(console.height))


class TestChapterCardLayout:
    def test_shows_chapter_number_in_roman(self) -> None:
        console = tcod.console.Console(80, 50, order="F")
        scene = _make_scene(title="CHATTO'S 24/7", character="novice")
        render_chapter_card(
            console,
            scene,
            0,
            4,
            transition_ms=2000,
            transition_duration_ms=600,
            lang="en",
            is_last_scene=False,
        )
        full = _read_all_console(console)
        assert "CHAPTER I" in full

    def test_shows_scene_title(self) -> None:
        console = tcod.console.Console(80, 50, order="F")
        scene = _make_scene(title="CHATTO'S 24/7", character="novice")
        render_chapter_card(
            console,
            scene,
            0,
            4,
            transition_ms=2000,
            transition_duration_ms=600,
            lang="en",
            is_last_scene=False,
        )
        full = _read_all_console(console)
        assert "CHATTO'S 24/7" in full

    def test_shows_character_label(self) -> None:
        console = tcod.console.Console(80, 50, order="F")
        scene = _make_scene(title="LOUISIANA 11", character="veteran")
        render_chapter_card(
            console,
            scene,
            0,
            4,
            transition_ms=2000,
            transition_duration_ms=600,
            lang="en",
            is_last_scene=False,
        )
        full = _read_all_console(console)
        assert "Marly (Sil) — Veteran" in full

    def test_shows_scene_n_of_total(self) -> None:
        console = tcod.console.Console(80, 50, order="F")
        scene = _make_scene()
        render_chapter_card(
            console,
            scene,
            2,
            4,
            transition_ms=2000,
            transition_duration_ms=600,
            lang="en",
            is_last_scene=False,
        )
        full = _read_all_console(console)
        assert "Scene 3 of 4" in full

    def test_roman_numerals_for_each_chapter(self) -> None:
        """Each scene index should produce a different roman numeral."""
        for i, expected_roman in enumerate(["I", "II", "III", "IV"]):
            console = tcod.console.Console(80, 50, order="F")
            scene = _make_scene()
            render_chapter_card(
                console,
                scene,
                i,
                4,
                transition_ms=2000,
                transition_duration_ms=600,
                lang="en",
                is_last_scene=False,
            )
            assert f"CHAPTER {expected_roman}" in _read_all_console(console), (
                f"Scene {i} should show CHAPTER {expected_roman}"
            )

    def test_finale_for_last_scene(self) -> None:
        """Last scene (≥3) should show FINALE instead of CHAPTER N."""
        console = tcod.console.Console(80, 50, order="F")
        scene = _make_scene(title="THE WHEEL", character="heretic")
        render_chapter_card(
            console,
            scene,
            3,
            4,
            transition_ms=2000,
            transition_duration_ms=600,
            lang="en",
            is_last_scene=True,
        )
        full = _read_all_console(console)
        assert "FINALE" in full
        assert "CHAPTER IV" not in full

    def test_korean_label_format(self) -> None:
        console = tcod.console.Console(80, 50, order="F")
        scene = _make_scene(title="LOUISIANA 11", character="veteran")
        render_chapter_card(
            console,
            scene,
            0,
            4,
            transition_ms=2000,
            transition_duration_ms=600,
            lang="ko",
            is_last_scene=False,
        )
        full = _read_all_console(console)
        assert "씬 1 / 4" in full
        assert "실 (Sil) — Veteran" in full

    def test_has_top_and_bottom_borders(self) -> None:
        """The card should have ornamental borders."""
        console = tcod.console.Console(80, 50, order="F")
        scene = _make_scene()
        render_chapter_card(
            console,
            scene,
            0,
            4,
            transition_ms=2000,
            transition_duration_ms=600,
            lang="en",
            is_last_scene=False,
        )
        full = _read_all_console(console)
        # Top/bottom borders
        assert "═" * 70 in full

    def test_has_ornament_header(self) -> None:
        console = tcod.console.Console(80, 50, order="F")
        scene = _make_scene()
        render_chapter_card(
            console,
            scene,
            0,
            4,
            transition_ms=2000,
            transition_duration_ms=600,
            lang="en",
            is_last_scene=False,
        )
        full = _read_all_console(console)
        # Header should have ornamental dots
        assert "·  CHAPTER I  ·" in full


class TestChapterCardFade:
    def test_full_fade_uses_strong_borders(self) -> None:
        """After fade-in completes, ═ borders should be visible."""
        console = tcod.console.Console(80, 50, order="F")
        scene = _make_scene()
        render_chapter_card(
            console,
            scene,
            0,
            4,
            transition_ms=2000,
            transition_duration_ms=600,
            lang="en",
            is_last_scene=False,
        )
        full = _read_all_console(console)
        # After fade complete (transition_ms > transition_duration_ms)
        assert "═" in full  # Full-strength borders

    def test_no_fade_dim_borders(self) -> None:
        """At very low fade, borders should be dimmer (▒ or ▓)."""
        console = tcod.console.Console(80, 50, order="F")
        scene = _make_scene()
        # At 10% fade-in: borders should be very dim
        render_chapter_card(
            console,
            scene,
            0,
            4,
            transition_ms=60,
            transition_duration_ms=600,
            lang="en",
            is_last_scene=False,
        )
        full = _read_all_console(console)
        # ▒ or ▓ should be present (dim chars)
        assert "▒" in full or "▓" in full

    def test_zero_fade_uses_heavy_dim(self) -> None:
        """At 0% fade, borders should be very dim (▒)."""
        console = tcod.console.Console(80, 50, order="F")
        scene = _make_scene()
        render_chapter_card(
            console,
            scene,
            0,
            4,
            transition_ms=0,
            transition_duration_ms=600,
            lang="en",
            is_last_scene=False,
        )
        full = _read_all_console(console)
        # At 0% (dim_level=0): heavy dim = ▒
        assert "▒" in full


class TestChapterCardEmptyArgs:
    def test_works_with_zero_total(self) -> None:
        """Edge case: scene_total=0 should still render without crashing."""
        console = tcod.console.Console(80, 50, order="F")
        scene = _make_scene()
        render_chapter_card(
            console,
            scene,
            0,
            0,
            transition_ms=2000,
            transition_duration_ms=600,
            lang="en",
            is_last_scene=True,
        )
        # Should not crash; just renders with FINALE (since total < 3 is False)
        # Actually total=0 with is_last=True would show FINALE due to `total >= 3` check
        # Let's verify no exception
        full = _read_all_console(console)
        assert "FINALE" in full or "CHAPTER I" in full


# ============================================================================
# render_blank_transition
# ============================================================================


class TestBlankTransition:
    def test_early_fade_shows_dim_chars(self) -> None:
        """In the first half of transition, dim chars are visible."""
        console = tcod.console.Console(80, 50, order="F")
        render_blank_transition(console, transition_ms=200, transition_duration_ms=800)
        full = _read_all_console(console)
        # Should have at least one dim block char
        has_dim = any(c in full for c in "░▒▓")
        assert has_dim

    def test_late_fade_shows_clear(self) -> None:
        """In the second half of transition, screen should be blank."""
        console = tcod.console.Console(80, 50, order="F")
        render_blank_transition(console, transition_ms=600, transition_duration_ms=800)
        full = _read_all_console(console)
        # After 50%, no dim chars should be visible (cleared)
        # Note: tcod.console.clear() sets all to 0 (which becomes " " in dump)
        assert full.strip() == ""

    def test_zero_duration_no_op(self) -> None:
        """Zero transition duration should not crash and not render anything."""
        console = tcod.console.Console(80, 50, order="F")
        render_blank_transition(console, transition_ms=0, transition_duration_ms=0)
        # Should not crash
        full = _read_all_console(console)
        assert full.strip() == ""
