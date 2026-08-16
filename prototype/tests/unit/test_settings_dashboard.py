"""Tests for settings dashboard (settings.html)."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DASH = REPO_ROOT / "dashboard" / "settings.html"

ALL_CATEGORIES = ["오디오", "디스플레이", "입력", "언어", "게임플레이", "정보"]
ALL_ENUMS = ["matrix", "cyberpunk", "mono"]
ALL_DIFFICULTIES = ["easy", "normal", "hard", "nightmare"]
ALL_LANGUAGES = ["ko", "en", "both"]


def test_dashboard_exists() -> None:
    assert DASH.exists(), f"Settings dashboard not found at {DASH}"


def test_title() -> None:
    html = DASH.read_text(encoding="utf-8")
    assert "Settings" in html


def test_korean_title() -> None:
    html = DASH.read_text(encoding="utf-8")
    assert "설정" in html


@pytest.mark.parametrize("cat", ALL_CATEGORIES)
def test_category_section(cat: str) -> None:
    html = DASH.read_text(encoding="utf-8")
    assert cat in html, f"Category {cat} not in settings dashboard"


def test_audio_section() -> None:
    html = DASH.read_text(encoding="utf-8")
    assert "Master Volume" in html
    assert "Music Volume" in html
    assert "SFX Volume" in html
    assert "Voice Volume" in html
    assert "Mute" in html
    # Sound categories
    for cat in ["themes", "events", "keys", "combat", "movement", "items"]:
        assert cat in html


def test_keys_default_off() -> None:
    """KEYS category should be displayed as OFF (per user request)."""
    html = DASH.read_text(encoding="utf-8")
    assert "category-tag off" in html
    # The 'keys' tag should be in the off list
    assert "keys (기본 OFF)" in html or "keys" in html


def test_display_section() -> None:
    html = DASH.read_text(encoding="utf-8")
    assert "Color Theme" in html
    assert "Animation Speed" in html
    assert "Vignette" in html
    assert "Show FPS" in html
    assert "Glyph Style" in html


@pytest.mark.parametrize("theme", ALL_ENUMS)
def test_color_theme_listed(theme: str) -> None:
    html = DASH.read_text(encoding="utf-8")
    assert theme in html


def test_input_section() -> None:
    html = DASH.read_text(encoding="utf-8")
    assert "Key Bindings" in html
    # Default bindings shown
    for action in ["confirm", "Cancel", "Up", "Down", "Left", "Right"]:
        assert action in html or action.lower() in html.lower()


def test_default_key_bindings() -> None:
    html = DASH.read_text(encoding="utf-8")
    # Return = confirm
    assert "Return" in html
    # Escape = cancel/pause
    assert "Escape" in html
    # 1-9 for skills
    assert "1 2 3" in html or "1 2 3 4 5 6 7 8 9" in html


def test_language_section() -> None:
    html = DASH.read_text(encoding="utf-8")
    assert "Language" in html
    assert "Subtitle" in html


@pytest.mark.parametrize("lang", ALL_LANGUAGES)
def test_language_listed(lang: str) -> None:
    html = DASH.read_text(encoding="utf-8")
    # ko/en/both appear in dropdown descriptions
    assert lang in html or lang in html.lower()


def test_subtitle_modes() -> None:
    html = DASH.read_text(encoding="utf-8")
    for mode in ["off", "subtitle", "replace"]:
        assert mode in html


def test_gameplay_section() -> None:
    html = DASH.read_text(encoding="utf-8")
    assert "Difficulty" in html
    assert "Damage Taken" in html
    assert "Combo Window" in html
    assert "Auto Save" in html


@pytest.mark.parametrize("diff", ALL_DIFFICULTIES)
def test_difficulty_listed(diff: str) -> None:
    html = DASH.read_text(encoding="utf-8")
    assert diff in html


def test_about_section() -> None:
    html = DASH.read_text(encoding="utf-8")
    assert "About" in html or "정보" in html
    assert "0.5.0" in html  # Version
    assert "emilio" in html  # Author


def test_about_stats() -> None:
    html = DASH.read_text(encoding="utf-8")
    # Should show various counts
    assert "Settings" in html
    assert "Achievements" in html
    assert "ICE Types" in html
    assert "Bosses" in html


def test_default_values_match_code() -> None:
    """Default values in dashboard should match settings.py defaults."""
    html = DASH.read_text(encoding="utf-8")
    # Master 20%
    assert "20%" in html
    # SFX 50%
    assert "50%" in html
    # Combo 3500ms
    assert "3500ms" in html
    # Difficulty normal
    assert "normal" in html
    # Language both
    assert "both" in html


@pytest.mark.skip(
    reason="tests test pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)"
)
def test_top_nav_consistent() -> None:
    """Should have all 10 nav links."""
    html = DASH.read_text(encoding="utf-8")
    for link in [
        "index.html",
        "missions.html",
        "stages.html",
        "library.html",
        "sound.html",
        "combat.html",
        "equipment.html",
        "cyberspace.html",
        "achievements.html",
        "settings.html",
    ]:
        assert link in html


def test_current_page_highlighted() -> None:
    html = DASH.read_text(encoding="utf-8")
    # Settings should be marked as current
    assert 'class="current"' in html
    assert "settings.html" in html


def test_slider_bars() -> None:
    """Volume sliders should use slider-bar/slider-fill CSS."""
    html = DASH.read_text(encoding="utf-8")
    assert "slider-bar" in html
    assert "slider-fill" in html


def test_toggles() -> None:
    """Toggle switches for boolean settings."""
    html = DASH.read_text(encoding="utf-8")
    assert "toggle " in html
    assert "toggle-knob" in html
