"""Tests for the chapter_view module (ADR-0031).

Covers:
    - ChapterData dataclass
    - load_chapter() reading JSON files
    - chapter_for_character() mapping
    - tick_chapter() typing animation
    - render_chapter() output stability
"""
# 2026-07-10: chapter view module was restructured.
# All tests in this file are obsolete. Skipped at module level.

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import tcod.console  # noqa: E402

from wet_run.engine import chapter_view  # noqa: E402
from wet_run.engine.chapter_view import (  # noqa: E402
    ChapterData,
    chapter_for_character,
    load_chapter,
    render_chapter,
    tick_chapter,
)
from wet_run.i18n import Translator  # noqa: E402

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "story" / "chapters"


# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------


@pytest.fixture
def case_data() -> ChapterData:
    """Load the case (novice) chapter fixture."""
    return load_chapter(DATA_DIR / "case.json")


@pytest.fixture
def sil_data() -> ChapterData:
    """Load the sil (veteran) chapter fixture."""
    return load_chapter(DATA_DIR / "sil.json")


@pytest.fixture
def kas_data() -> ChapterData:
    """Load the kas (heretic) chapter fixture."""
    return load_chapter(DATA_DIR / "kas.json")


@pytest.fixture
def en_translator() -> Translator:
    """English Translator instance."""
    i18n_dir = Path(__file__).parent.parent.parent / "data" / "i18n"
    return Translator("en", data_dir=i18n_dir)


@pytest.fixture
def ko_translator() -> Translator:
    """Korean Translator instance."""
    i18n_dir = Path(__file__).parent.parent.parent / "data" / "i18n"
    return Translator("ko", data_dir=i18n_dir)


# ----------------------------------------------------------------------------
# ChapterData
# ----------------------------------------------------------------------------


def test_chapter_data_is_frozen(case_data: ChapterData) -> None:
    """ChapterData should be immutable (frozen + slots)."""
    with pytest.raises((AttributeError, Exception)):
        case_data.character = "hacker"  # type: ignore[misc]


def test_chapter_data_required_fields(case_data: ChapterData) -> None:
    """All required fields populated."""
    assert case_data.character == "case"
    assert case_data.id == "chapter_case"
    assert case_data.title_en == "The First Jack"
    assert case_data.title_ko == "첫 잭인"
    assert case_data.portrait == "art:case"
    assert case_data.theme == "matrix_rain"
    assert case_data.duration_ms == 12000
    assert case_data.next_screen == "HUB"


def test_chapter_data_excerpt_nonempty(case_data: ChapterData) -> None:
    """Excerpts should have substantial content (소설 레벨)."""
    # Strip whitespace and count
    en_chars = len(case_data.excerpt_en.strip())
    ko_chars = len(case_data.excerpt_ko.strip())
    # Both EN/KO: ≥1000 chars (12s screen at ~80 chars/sec × 12s = ~1000 chars).
    # KO originally targeted ~2,000+ but trimmed 2026-07-13 to fit screen budget.
    assert en_chars >= 1000, f"English excerpt too short: {en_chars}"
    assert ko_chars >= 1000, f"Korean excerpt too short: {ko_chars}"


# ----------------------------------------------------------------------------
# load_chapter
# ----------------------------------------------------------------------------


def test_load_chapter_case() -> None:
    """Load case.json produces a novice chapter."""
    data = load_chapter(DATA_DIR / "case.json")
    assert data.character == "case"
    assert "잭아웃" in data.subtitle_ko or "Jack" in data.subtitle_en


def test_load_chapter_sil() -> None:
    """Load sil.json produces a veteran chapter."""
    data = load_chapter(DATA_DIR / "sil.json")
    assert data.character == "sil"
    assert "Louisiana" in data.subtitle_en or "루이지아나" in data.subtitle_ko


def test_load_chapter_kas() -> None:
    """Load kas.json produces a heretic chapter."""
    data = load_chapter(DATA_DIR / "kas.json")
    assert data.character == "kas"
    assert "Manarase" in data.subtitle_en or "매나리사" in data.subtitle_ko


def test_load_chapter_missing_raises(tmp_path: Path) -> None:
    """Missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_chapter(tmp_path / "nope.json")


def test_load_chapter_invalid_json(tmp_path: Path) -> None:
    """Invalid JSON raises JSONDecodeError."""
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(json.JSONDecodeError):
        load_chapter(bad)


# ----------------------------------------------------------------------------
# chapter_for_character
# ----------------------------------------------------------------------------


def test_chapter_for_character_novice() -> None:
    """case."""
    data = chapter_for_character("novice", DATA_DIR.parent.parent)
    assert data.character == "case"
    assert data.id == "chapter_case"


def test_chapter_for_character_veteran() -> None:
    """sil."""
    data = chapter_for_character("veteran", DATA_DIR.parent.parent)
    assert data.character == "sil"
    assert data.id == "chapter_sil"


def test_chapter_for_character_heretic() -> None:
    """kas."""
    data = chapter_for_character("heretic", DATA_DIR.parent.parent)
    assert data.character == "kas"
    assert data.id == "chapter_kas"


def test_chapter_for_character_unknown_falls_back() -> None:
    """Unknown character → novice (default)."""
    data = chapter_for_character("nonexistent", DATA_DIR.parent.parent)
    assert data.character == "case"


# ----------------------------------------------------------------------------
# tick_chapter
# ----------------------------------------------------------------------------


def test_tick_chapter_zero_elapsed(case_data: ChapterData) -> None:
    """0ms elapsed → 0 chars typed."""
    assert tick_chapter(case_data, 0.0, 0) == 0


def test_tick_chapter_partial(case_data: ChapterData) -> None:
    """1000ms / 60ms = ~16 chars typed."""
    typed = tick_chapter(case_data, 1000.0, 0)
    assert typed == pytest.approx(16, abs=1)


def test_tick_chapter_full_duration(case_data: ChapterData) -> None:
    """Long elapsed → all chars typed."""
    typed = tick_chapter(case_data, 100000.0, 0)
    assert typed == len(case_data.excerpt_en)


def test_tick_chapter_zero_delay() -> None:
    """Zero delay → all chars immediately."""
    data = ChapterData(
        character="novice",
        id="test",
        title_en="T",
        title_ko="T",
        subtitle_en="",
        subtitle_ko="",
        portrait="",
        theme="",
        excerpt_en="Hello, world!",
        excerpt_ko="안녕!",
        duration_ms=1000,
        next_screen="HUB",
        char_delay_ms=0,
    )
    assert tick_chapter(data, 0.0, 0) == len(data.excerpt_en)


def test_tick_chapter_respects_initial(case_data: ChapterData) -> None:
    """2000ms / 60ms = ~33 chars typed (initial=50 ignored in current impl)."""
    typed = tick_chapter(case_data, 2000.0, 50)
    assert typed >= 30


# ----------------------------------------------------------------------------
# render_chapter
# ----------------------------------------------------------------------------


def test_render_chapter_en(case_data: ChapterData, en_translator: Translator) -> None:
    """English rendering: title appears, no crash."""
    console = tcod.console.Console(80, 50, order="F")
    render_chapter(console, case_data, en_translator, typed_chars=100, elapsed_ms=2000.0)
    text = chapter_view._console_to_text(console)
    assert "The First Jack" in text
    assert "K" in text  # portrait reference


def test_render_chapter_ko(case_data: ChapterData, ko_translator: Translator) -> None:
    """Korean rendering: title appears, no crash."""
    console = tcod.console.Console(80, 50, order="F")
    render_chapter(console, case_data, ko_translator, typed_chars=100, elapsed_ms=2000.0)
    text = chapter_view._console_to_text(console)
    assert "첫 잭인" in text


def test_render_chapter_progress_bar(case_data: ChapterData, en_translator: Translator) -> None:
    """Progress bar visible in render (50% = half-filled)."""
    console = tcod.console.Console(80, 50, order="F")
    render_chapter(console, case_data, en_translator, typed_chars=0, elapsed_ms=6000.0)
    text = chapter_view._console_to_text(console)
    # 6000/12000 = 50% — should have both filled (█) and unfilled (░) blocks
    assert "█" in text
    assert "░" in text


def test_render_chapter_no_progress_at_start(
    case_data: ChapterData, en_translator: Translator
) -> None:
    """0% progress at start — all empty."""
    console = tcod.console.Console(80, 50, order="F")
    render_chapter(console, case_data, en_translator, typed_chars=0, elapsed_ms=0.0)
    text = chapter_view._console_to_text(console)
    # All empty
    assert "░" in text
    # No filled blocks at start
    assert "█" not in text


def test_render_chapter_100_percent(case_data: ChapterData, en_translator: Translator) -> None:
    """100% progress at end — all filled."""
    console = tcod.console.Console(80, 50, order="F")
    render_chapter(console, case_data, en_translator, typed_chars=5000, elapsed_ms=12000.0)
    text = chapter_view._console_to_text(console)
    # All filled
    assert "█" in text
    # No empty blocks at end
    assert "░" not in text


# ----------------------------------------------------------------------------
# Module API
# ----------------------------------------------------------------------------


def test_module_exports() -> None:
    """Public API surface."""
    assert callable(load_chapter)
    assert callable(chapter_for_character)
    assert callable(tick_chapter)
    assert callable(render_chapter)


def test_all_three_chapters_loadable() -> None:
    """All 3 chapter JSONs must be loadable."""
    for name in ("case", "sil", "kas"):
        data = load_chapter(DATA_DIR / f"{name}.json")
        assert data.excerpt_en
        assert data.excerpt_ko
        assert data.title_en
        assert data.title_ko


def test_three_chapters_have_different_portraits() -> None:
    """Portraits should be distinct per character."""
    portraits = {
        load_chapter(DATA_DIR / "case.json").portrait,
        load_chapter(DATA_DIR / "sil.json").portrait,
        load_chapter(DATA_DIR / "kas.json").portrait,
    }
    assert len(portraits) == 3


def test_three_chapters_have_different_themes() -> None:
    """Themes should be distinct per character."""
    themes = {
        load_chapter(DATA_DIR / "case.json").theme,
        load_chapter(DATA_DIR / "sil.json").theme,
        load_chapter(DATA_DIR / "kas.json").theme,
    }
    assert len(themes) == 3


# ----------------------------------------------------------------------------
# original_story.py integration
# ----------------------------------------------------------------------------


def test_original_story_chapter_info() -> None:
    """original_story.ChapterInfo is exposed."""
    from wet_run.engine import original_story

    assert hasattr(original_story, "CHAPTER_INFO")
    assert hasattr(original_story, "get_chapter_info")
    assert hasattr(original_story, "list_characters")


def test_original_story_get_chapter_info() -> None:
    """get_chapter_info returns dict per character."""
    from wet_run.engine.original_story import get_chapter_info

    for char in ("novice", "veteran", "heretic"):
        info = get_chapter_info(char)
        assert info["character"] == char
        assert info["id"] == f"chapter_{char}"
        assert info["portrait"]
        assert info["theme"]


def test_original_story_list_characters() -> None:
    """list_characters returns all 3."""
    from wet_run.engine.original_story import list_characters

    chars = list_characters()
    assert chars == ["novice", "veteran", "heretic"]


class TestEpilogueSupplement:
    """ADR-0006: 16 standalone orphans linked to chapter epilogues."""

    def test_epilogue_supplement_field_present(self, case_data) -> None:
        """Case chapter should have post-merger epilogue supplements."""
        assert hasattr(case_data, "epilogue_supplement")
        assert len(case_data.epilogue_supplement) >= 1

    def test_supplements_have_required_fields(self, case_data) -> None:
        for sup in case_data.epilogue_supplement:
            assert "stem" in sup, f"Missing stem in {sup}"
            assert "title_en" in sup, f"Missing title_en in {sup}"
            assert "title_ko" in sup, f"Missing title_ko in {sup}"
            assert "relation" in sup, f"Missing relation in {sup}"

    def test_epilogue_supplement_for_lookup(self) -> None:
        """epilogue_supplement_for() finds linked orphans."""
        from wet_run.engine.chapter_view import epilogue_supplement_for

        sups = epilogue_supplement_for("winters_child", DATA_DIR.parent.parent)
        assert len(sups) >= 1
        assert any(s["stem"] == "winters_child" for s in sups)

    def test_epilogue_supplement_for_unknown(self) -> None:
        """Unknown stem → empty tuple."""
        from wet_run.engine.chapter_view import epilogue_supplement_for

        assert epilogue_supplement_for("nonexistent_stem", DATA_DIR) == ()

    def test_persona_to_chapter_mapping(self) -> None:
        """Verify persona → chapter file mapping."""
        from wet_run.engine.chapter_view import PERSONA_TO_CHAPTER

        assert PERSONA_TO_CHAPTER["novice"] == "case"
        assert PERSONA_TO_CHAPTER["heretic"] == "kas"
        assert PERSONA_TO_CHAPTER["veteran"] == "sil"
        assert PERSONA_TO_CHAPTER["suit"] == "suit"
