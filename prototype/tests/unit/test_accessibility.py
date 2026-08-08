"""Tests for Accessibility System (ADR-0183)."""

from __future__ import annotations

import dataclasses

import pytest

from roguelike_sprawl.combat.accessibility import (
    TEXT_SIZES,
    AccessibilityConfig,
    get_color_palette,
    get_colorblind_modes,
    get_default_accessibility,
    get_text_size_factor,
    get_text_sizes,
    is_colorblind_mode,
    is_text_size,
    remap_key,
    set_colorblind_mode,
    set_text_size,
)


def test_get_default_accessibility() -> None:
    config = get_default_accessibility()
    assert config.colorblind_mode == "none"
    assert config.text_size == "medium"
    assert config.input_remapping == {}


def test_set_colorblind_mode() -> None:
    config = get_default_accessibility()
    config = set_colorblind_mode(config, "deuteranopia")
    assert config.colorblind_mode == "deuteranopia"


def test_set_colorblind_mode_invalid() -> None:
    config = get_default_accessibility()
    with pytest.raises(ValueError, match="Invalid"):
        set_colorblind_mode(config, "invalid")


def test_set_text_size() -> None:
    config = get_default_accessibility()
    config = set_text_size(config, "large")
    assert config.text_size == "large"


def test_set_text_size_invalid() -> None:
    config = get_default_accessibility()
    with pytest.raises(ValueError, match="Invalid"):
        set_text_size(config, "huge")


def test_remap_key() -> None:
    config = get_default_accessibility()
    config = remap_key(config, "pause", "p")
    assert config.input_remapping["pause"] == "p"


def test_remap_multiple_keys() -> None:
    config = get_default_accessibility()
    config = remap_key(config, "pause", "p")
    config = remap_key(config, "attack", "space")
    assert config.input_remapping["pause"] == "p"
    assert config.input_remapping["attack"] == "space"


def test_get_color_palette_none() -> None:
    assert get_color_palette("none") == {}


def test_get_color_palette_deuteranopia() -> None:
    palette = get_color_palette("deuteranopia")
    assert "red" in palette
    assert "green" in palette


def test_get_color_palette_protanopia() -> None:
    palette = get_color_palette("protanopia")
    assert "red" in palette


def test_get_color_palette_tritanopia() -> None:
    palette = get_color_palette("tritanopia")
    assert "blue" in palette


def test_get_text_size_factor() -> None:
    assert get_text_size_factor("small") < 1.0
    assert get_text_size_factor("medium") == 1.0
    assert get_text_size_factor("large") > 1.0


def test_get_text_size_factor_unknown() -> None:
    assert get_text_size_factor("unknown") == 1.0


def test_is_colorblind_mode() -> None:
    assert is_colorblind_mode("deuteranopia")
    assert is_colorblind_mode("protanopia")
    assert is_colorblind_mode("tritanopia")
    assert is_colorblind_mode("none")
    assert not is_colorblind_mode("invalid")


def test_is_text_size() -> None:
    assert is_text_size("small")
    assert is_text_size("medium")
    assert is_text_size("large")
    assert not is_text_size("huge")


def test_get_colorblind_modes() -> None:
    modes = get_colorblind_modes()
    assert "none" in modes
    assert "deuteranopia" in modes
    assert "protanopia" in modes
    assert "tritanopia" in modes


def test_get_text_sizes() -> None:
    sizes = get_text_sizes()
    assert "small" in sizes
    assert "medium" in sizes
    assert "large" in sizes


def test_config_immutable() -> None:
    config = get_default_accessibility()
    try:
        config.colorblind_mode = "modified"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_colorblind_palettes_have_colors() -> None:
    for mode in ("deuteranopia", "protanopia", "tritanopia"):
        palette = get_color_palette(mode)
        assert len(palette) > 0
        for color_name, rgb in palette.items():
            assert len(rgb) == 3
            assert all(0 <= c <= 255 for c in rgb)


def test_text_size_factor_progression() -> None:
    factors = [get_text_size_factor(s) for s in TEXT_SIZES]
    assert factors == sorted(factors)


def test_remap_preserves_other_fields() -> None:
    config = AccessibilityConfig(
        colorblind_mode="deuteranopia",
        text_size="large",
        input_remapping={},
    )
    config2 = remap_key(config, "skill_1", "q")
    assert config2.colorblind_mode == "deuteranopia"
    assert config2.text_size == "large"
    assert config2.input_remapping["skill_1"] == "q"
