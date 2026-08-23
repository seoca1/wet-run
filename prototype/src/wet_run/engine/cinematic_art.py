"""Cinematic ASCII art portraits for the prologue and story scenes.

Provides large multi-line ASCII portraits for major characters and
locations. Used by the story_cinematic module to make the prologue
and briefings feel more cinematic.

Portraits are NOT meatspace representations (Pillar 2). They are
abstract cyberpunk symbols — "construct echoes", "data fragments",
"neural patterns" — that *suggest* a character or place without
showing their physical form.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..combat.palette import (
    CYAN_BRIGHT,
    CYAN_LIGHT,
    DEBUFF_COLOR,
    DEFAULT_COLOR,
    GREEN_PURE,
    ICE_TYPE_NEUROMANCER_COLOR,
    MAGENTA_BRIGHT,
    PURPLE_ICE,
    WINTERMUTE_P3_COLOR,
)


class ArtStyle(StrEnum):
    """Visual style for the ASCII art."""

    NEON = "neon"  # Bright cyan/magenta cyberpunk — default runner style.
    GLITCH = "glitch"  # Corrupted, distorted — damaged construct echo.
    SHADOW = "shadow"  # Dim, mysterious — pre-reveal scene.
    FIRE = "fire"  # Red/orange, intense — boss / combat climax.
    MATRIX = "matrix"  # Green, code-rain style — cyberspace node intro.
    GHOST = "ghost"  # Faded, ethereal — construct memory / Loa encounter.
    STATIC = "static"  # TV static / noise — jack-in / jack-out transition.


@dataclass(frozen=True, slots=True)
class AsciiArt:
    """A piece of ASCII art with associated color/style."""

    lines: tuple[str, ...]
    fg: tuple[int, int, int] = DEFAULT_COLOR
    bg: tuple[int, int, int] | None = None
    style: ArtStyle = ArtStyle.NEON

    @property
    def width(self) -> int:
        """Width of the widest line."""
        return max((len(line) for line in self.lines), default=0)

    @property
    def height(self) -> int:
        """Height in visual rows (one per line tuple)."""
        return len(self.lines)


# --- Major characters (construct echoes, not physical forms) ---

THE_FINN = AsciiArt(
    lines=(
        "  ╔══════════════╗  ",
        "  ║  ♠ ♠ ♠ ♠ ♠   ║  ",
        "  ║   SPADE 9   ║  ",
        "  ║  ♠ ♠ ♠ ♠ ♠   ║  ",
        "  ╚══════╦═══════╝  ",
        "       ╔═╩═╗        ",
        "      ╔╝   ╚╗       ",
        "     ╔╝ FINN ╚╗      ",
        "    ╔╝ THE    ╚╗     ",
        "    ╚═══════════╝    ",
    ),
    fg=PURPLE_ICE,  # Magenta
    style=ArtStyle.NEON,
)

DIXIE_FLATLINE = AsciiArt(
    lines=(
        "     ◊◊◊◊◊◊◊◊     ",
        "    ◊  D I X  ◊    ",
        "   ◊   ────    ◊   ",
        "   ◊  FLATLINE ◊   ",
        "   ◊   ────    ◊   ",
        "    ◊ construct ◊   ",
        "     ◊◊◊◊◊◊◊◊     ",
    ),
    fg=CYAN_LIGHT,  # Cyan
    style=ArtStyle.GHOST,
)

ARMITAGE = AsciiArt(
    lines=(
        "  ╔══════════════╗  ",
        "  ║  ╦ ╦ ╦ ╦ ╦  ║  ",
        "  ║  ╠═╣ ╠═╣ ║  ║  ",
        "  ║  ╩ ╩ ╩ ╩ ╩  ║  ",
        "  ╚══════════════╝  ",
        "      WILLIS         ",
        "     COLE            ",
    ),
    fg=(180, 180, 180),  # Gray
    style=ArtStyle.SHADOW,
)

MOLLY_MILLIONS = AsciiArt(
    lines=(
        "  ◆◆◆◆◆◆◆◆◆◆◆◆  ",
        "  ◆  M O L L  Y ◆  ",
        "  ◆   ──────    ◆  ",
        "  ◆  MILLIONS  ◆  ",
        "  ◆  ◣◢◣◢◣◢◣◢  ◆  ",
        "  ◆  razorgirl  ◆  ",
        "  ◆◆◆◆◆◆◆◆◆◆◆◆  ",
    ),
    fg=WINTERMUTE_P3_COLOR,  # Hot pink
    style=ArtStyle.NEON,
)

CASE = AsciiArt(
    lines=(
        "  ░░░░░░░░░░░░░░  ",
        "  ░   HENRY    ░  ",
        "  ░   DOROTHY  ░  ",
        "  ░   CASE     ░  ",
        "  ░            ░  ",
        "  ░ ex-console ░  ",
        "  ░░░░░░░░░░░░░░  ",
    ),
    fg=(100, 200, 100),  # Matrix green
    style=ArtStyle.MATRIX,
)

# --- Locations (cyberspace representations) ---

CHIBA_CITY = AsciiArt(
    lines=(
        "  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄  ",
        "  █              █  ",
        "  █  NEON LIGHTS █  ",
        "  █   ◢◣◢◣◢◣   █  ",
        "  █  ◤◥◤◥◤◥◤◥  █  ",
        "  █   the sprawl █  ",
        "  █  ▄▄▄▄▄▄▄▄▄▄ █  ",
        "  █  █  Chiba  █ █  ",
        "  █  ▀▀▀▀▀▀▀▀▀▀ █  ",
        "  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀  ",
    ),
    fg=MAGENTA_BRIGHT,  # Magenta neon
    style=ArtStyle.NEON,
)

CYBERSPACE = AsciiArt(
    lines=(
        "    ╲╱╲╱╲╱╲╱╲    ",
        "   ◆ grid   ◆   ",
        "  ◆   nodes  ◆  ",
        " ◆   ◢◣◢◣◢◣  ◆ ",
        " ◆  ▓▓▓▓▓▓▓▓  ◆ ",
        " ◆   ░▒▓█▓▒░   ◆ ",
        "  ◆  data flow ◆  ",
        "   ◆________◆   ",
        "    ╱╲╱╲╱╲╱╲    ",
    ),
    fg=CYAN_BRIGHT,  # Cyan
    style=ArtStyle.MATRIX,
)

MATRIX_RAIN = AsciiArt(
    lines=(
        " ░ █ ░ █ ░ █ ░ █ ",
        " █ ░ █ ░ █ ░ █ ░ ",
        " ░ █ ░ █ ░ █ ░ █ ",
        " █ ░ █ ░ █ ░ █ ░ ",
        " ░ █ ░ █ ░ █ ░ █ ",
        " █ ░ █ ░ █ ░ █ ░ ",
        " ░ █ ░ █ ░ █ ░ █ ",
        " █ ░ █ ░ █ ░ █ ░ ",
    ),
    fg=GREEN_PURE,  # Matrix green
    style=ArtStyle.MATRIX,
)

SENSE_NET = AsciiArt(
    lines=(
        "  ╔══════════════╗  ",
        "  ║  ◢◤◢◤◢◤    ║  ",
        "  ║  ────────   ║  ",
        "  ║  SENSE/NET  ║  ",
        "  ║  ────────   ║  ",
        "  ║  ◥◣◥◣◥◣    ║  ",
        "  ╚══════════════╝  ",
    ),
    fg=DEBUFF_COLOR,  # Purple
    style=ArtStyle.NEON,
)

FINN_OFFICE = AsciiArt(
    lines=(
        "  ┌──────────────┐  ",
        "  │ ▓▓▓▓▓▓▓▓▓▓▓▓ │  ",
        "  │ ▓ FINN'S  ▓ │  ",
        "  │ ▓ OFFICE  ▓ │  ",
        "  │ ▓▓▓▓▓▓▓▓▓▓▓▓ │  ",
        "  │   ◣◢◣◢      │  ",
        "  │  ◤◥◤◥◤◥     │  ",
        "  │ Chiba, Jpn  │  ",
        "  └──────────────┘  ",
    ),
    fg=(180, 130, 100),  # Dim brown
    style=ArtStyle.SHADOW,
)

# --- Generic / atmospheric ---

GLITCH_BURST = AsciiArt(
    lines=(
        " █▓▒░ ▄▀■ ░▒▓█ ",
        " ▓▒░ ▀▄▓█▓ ░▒▓ ",
        " ▒░ ▓▒░ ▀▄▓█▒░ ",
        " ░ ▒▓▒ ▀▄▓▒░ ▓ ",
        "   ░▒▓ ▀▄▒░▓▒   ",
    ),
    fg=ICE_TYPE_NEUROMANCER_COLOR,
    style=ArtStyle.GLITCH,
)

TV_STATIC = AsciiArt(
    lines=(
        " ░▒▓█▓▒ █▓▒░▓█▒ ",
        " ▒▓▒░ █▓▒░▓█▒ █ ",
        " ░▒▓▒░ ▓█▒░▓▒ █ ",
        " ▓▒░ █▓▒░▓█▒ █▓ ",
        " ░▒▓▒░▓█▒ █▓▒░▓ ",
    ),
    fg=(180, 180, 180),
    style=ArtStyle.STATIC,
)

# --- Portrait registry ---

PORTRAITS: dict[str, AsciiArt] = {
    "the_finn": THE_FINN,
    "finn": THE_FINN,
    "dixie": DIXIE_FLATLINE,
    "dixie_flatline": DIXIE_FLATLINE,
    "armitage": ARMITAGE,
    "willis_cole": ARMITAGE,
    "molly": MOLLY_MILLIONS,
    "molly_millions": MOLLY_MILLIONS,
    "case": CASE,
    "henry_case": CASE,
    "chiba": CHIBA_CITY,
    "chiba_city": CHIBA_CITY,
    "cyberspace": CYBERSPACE,
    "matrix_rain": MATRIX_RAIN,
    "sense_net": SENSE_NET,
    "finn_office": FINN_OFFICE,
    "glitch": GLITCH_BURST,
    "static": TV_STATIC,
}


def get_portrait(key: str) -> AsciiArt | None:
    """Get a portrait by key, or None if not found."""
    return PORTRAITS.get(key.lower().replace(" ", "_").replace("/", "_").replace("-", "_"))


def get_default_portrait() -> AsciiArt:
    """Get a default portrait for unknown keys."""
    return CYBERSPACE


# --- Story scene art mapping ---
# Maps scene IDs to their default art (used if a line doesn't override).

SCENE_ART: dict[str, str] = {
    "prologue_sprawl": "chiba",
    "prologue_chiba": "chiba",
    "prologue_matrix": "cyberspace",
    "briefing_finn_first_jack": "finn",
    "briefing_finn": "finn",
    "npc_dixie": "dixie",
    "npc_finn": "finn",
    "npc_molly": "molly",
    "npc_armitage": "armitage",
    "event_chiba_night": "chiba",
    "event_flatline": "glitch",
}


def get_scene_art(scene_id: str) -> AsciiArt:
    """Get the default art for a story scene."""
    key = SCENE_ART.get(scene_id, "cyberspace")
    return get_portrait(key) or get_default_portrait()


# --- Line-level art hints ---
# Lines can override the scene art by setting StoryLine.portrait = "key"
# If portrait starts with "art:" the rest is treated as an art key.


def resolve_line_art(line_portrait: str, scene_id: str) -> AsciiArt | None:
    """Resolve a line's portrait field into an AsciiArt.

    - Empty string: use scene art
    - "art:finn": use the named art
    - "♠F♠": legacy single-glyph, return None (caller uses inline glyph)
    """
    if not line_portrait:
        return get_scene_art(scene_id)
    if line_portrait.startswith("art:"):
        return get_portrait(line_portrait[4:]) or get_scene_art(scene_id)
    # Legacy single-glyph
    return None
