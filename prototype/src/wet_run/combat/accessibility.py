"""Accessibility System (ADR-0183).

3 accessibility modes:
- Colorblind: 3 modes (deuteranopia, protanopia, tritanopia)
- Text size: small / medium / large
- Input remapping: custom key bindings
"""

from __future__ import annotations

from dataclasses import dataclass, field

COLORBLIND_MODES: tuple[str, ...] = ("none", "deuteranopia", "protanopia", "tritanopia")
TEXT_SIZES: tuple[str, ...] = ("small", "medium", "large")

TEXT_SIZE_FACTORS: dict[str, float] = {
    "small": 0.85,
    "medium": 1.0,
    "large": 1.25,
}

COLORBLIND_PALETTES: dict[str, dict[str, tuple[int, int, int]]] = {
    "none": {},
    "deuteranopia": {
        "red": (200, 100, 50),
        "green": (80, 150, 80),
    },
    "protanopia": {
        "red": (180, 90, 40),
        "green": (90, 160, 80),
    },
    "tritanopia": {
        "blue": (80, 100, 200),
        "yellow": (180, 160, 50),
    },
}


@dataclass(frozen=True, slots=True)
class AccessibilityConfig:
    """Player accessibility preferences."""

    colorblind_mode: str = "none"
    text_size: str = "medium"
    input_remapping: dict[str, str] = field(default_factory=dict)


def get_default_accessibility() -> AccessibilityConfig:
    """Return the default accessibility configuration."""
    return AccessibilityConfig()


def set_colorblind_mode(config: AccessibilityConfig, mode: str) -> AccessibilityConfig:
    """Set the colorblind mode."""
    if mode not in COLORBLIND_MODES:
        raise ValueError(
            f"Invalid colorblind mode: {mode!r} (must be one of: {list(COLORBLIND_MODES)})"
        )
    return AccessibilityConfig(
        colorblind_mode=mode,
        text_size=config.text_size,
        input_remapping=dict(config.input_remapping),
    )


def set_text_size(config: AccessibilityConfig, size: str) -> AccessibilityConfig:
    """Set the text size."""
    if size not in TEXT_SIZES:
        raise ValueError(f"Invalid text size: {size!r} (must be one of: {list(TEXT_SIZES)})")
    return AccessibilityConfig(
        colorblind_mode=config.colorblind_mode,
        text_size=size,
        input_remapping=dict(config.input_remapping),
    )


def remap_key(config: AccessibilityConfig, action: str, key: str) -> AccessibilityConfig:
    """Set a custom key binding for an action."""
    new_remapping = dict(config.input_remapping)
    new_remapping[action] = key
    return AccessibilityConfig(
        colorblind_mode=config.colorblind_mode,
        text_size=config.text_size,
        input_remapping=new_remapping,
    )


def get_color_palette(mode: str) -> dict[str, tuple[int, int, int]]:
    """Return the colorblind palette for a mode."""
    return COLORBLIND_PALETTES.get(mode, {})


def get_text_size_factor(size: str) -> float:
    """Return the text size factor for a size."""
    return TEXT_SIZE_FACTORS.get(size, 1.0)


def is_colorblind_mode(mode: str) -> bool:
    """Return True if the mode is a valid colorblind mode."""
    return mode in COLORBLIND_MODES


def is_text_size(size: str) -> bool:
    """Return True if the size is a valid text size."""
    return size in TEXT_SIZES


def get_colorblind_modes() -> tuple[str, ...]:
    """Return all colorblind modes."""
    return COLORBLIND_MODES


def get_text_sizes() -> tuple[str, ...]:
    """Return all text sizes."""
    return TEXT_SIZES


__all__ = [
    "AccessibilityConfig",
    "COLORBLIND_MODES",
    "COLORBLIND_PALETTES",
    "TEXT_SIZES",
    "TEXT_SIZE_FACTORS",
    "get_color_palette",
    "get_colorblind_modes",
    "get_default_accessibility",
    "get_text_size_factor",
    "get_text_sizes",
    "is_colorblind_mode",
    "is_text_size",
    "remap_key",
    "set_colorblind_mode",
    "set_text_size",
]
