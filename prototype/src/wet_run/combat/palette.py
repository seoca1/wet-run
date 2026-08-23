"""Centralized color palette for all combat visual systems.

Provides RGB color tuples for tcod rendering. All combat modules
(effects, hud, combo, bosses) should import from here to ensure
visual consistency and easy theming.

Color categories:
  - HP/health (high/mid/low/crit)
  - Damage/crit (red, orange, yellow)
  - Heal/buff (green, cyan)
  - Status effects (debuff purple, stun yellow)
  - Shield/UI (cyan, white)
  - Phase colors (4-tier escalation)
  - Vignette (dark red)
  - ICE types (5 distinct palettes)
"""

from __future__ import annotations

from typing import Final

# ----------------------------------------------------------------------------
# HP / Health colors
# ----------------------------------------------------------------------------

HP_HIGH_COLOR: Final[tuple[int, int, int]] = (100, 230, 130)  # green
HP_MID_COLOR: Final[tuple[int, int, int]] = (255, 200, 80)  # yellow
HP_LOW_COLOR: Final[tuple[int, int, int]] = (255, 100, 80)  # orange-red
HP_CRIT_COLOR: Final[tuple[int, int, int]] = (255, 30, 30)  # critical red
HEAL_COLOR: Final[tuple[int, int, int]] = (80, 255, 120)  # bright green

# ----------------------------------------------------------------------------
# Grayscale ramp (dark → light) — UI neutrals, dim text, backgrounds
# ----------------------------------------------------------------------------

GRAY_BLACK: Final[tuple[int, int, int]] = (0, 0, 0)
GRAY_VERY_DARK: Final[tuple[int, int, int]] = (40, 40, 40)
GRAY_DARK: Final[tuple[int, int, int]] = (60, 60, 60)
GRAY_MID_DARK: Final[tuple[int, int, int]] = (80, 80, 80)
GRAY_MID: Final[tuple[int, int, int]] = (100, 100, 100)
GRAY_120: Final[tuple[int, int, int]] = (120, 120, 120)
GRAY_MID_LIGHT: Final[tuple[int, int, int]] = (128, 128, 128)
GRAY_LIGHT: Final[tuple[int, int, int]] = (150, 150, 150)
GRAY_160: Final[tuple[int, int, int]] = (160, 160, 160)
GRAY_BRIGHT: Final[tuple[int, int, int]] = (200, 200, 220)

# ----------------------------------------------------------------------------
# Damage / Combat feedback
# ----------------------------------------------------------------------------

DAMAGE_COLOR: Final[tuple[int, int, int]] = (255, 80, 80)
DAMAGE_FLASH_COLOR: Final[tuple[int, int, int]] = (255, 50, 50)  # bright crimson (P3)
CRIT_COLOR: Final[tuple[int, int, int]] = (255, 150, 50)  # orange
HIT_FLASH_COLOR: Final[tuple[int, int, int]] = (255, 255, 255)  # white
DYING_COLOR: Final[tuple[int, int, int]] = (255, 0, 0)  # pure red (HP depleted)
ICE_BREAK_COLOR: Final[tuple[int, int, int]] = (180, 200, 220)  # light blue-white
YELLOW_PURE: Final[tuple[int, int, int]] = (255, 255, 0)  # pure yellow (skill effect)
LIFE_STEAL_COLOR: Final[tuple[int, int, int]] = (200, 0, 0)  # deep crimson (lifesteal)
WISP_COLOR: Final[tuple[int, int, int]] = (180, 180, 255)  # pale cyan (wisp attack)
PROBE_COLOR: Final[tuple[int, int, int]] = (0, 200, 255)  # sky blue (probe)
JAMMER_COLOR: Final[tuple[int, int, int]] = (150, 150, 255)  # lavender (jammer debuff)
GREEN_PURE: Final[tuple[int, int, int]] = (0, 255, 0)  # pure green (heal/regen)
GREEN_BRIGHT: Final[tuple[int, int, int]] = (100, 255, 100)  # bright green (stim)

# ----------------------------------------------------------------------------
# Wintermute boss phase colors (3-tier escalation)
# ----------------------------------------------------------------------------

WINTERMUTE_P1_COLOR: Final[tuple[int, int, int]] = (120, 120, 220)  # P1 — observing
WINTERMUTE_P2_COLOR: Final[tuple[int, int, int]] = (220, 100, 220)  # P2 — rebelling
WINTERMUTE_P3_COLOR: Final[tuple[int, int, int]] = (255, 50, 100)  # P3 — integrating
WINTERMUTE_P4_COLOR: Final[tuple[int, int, int]] = HIT_FLASH_COLOR  # P4 — interface

# ----------------------------------------------------------------------------
# ICE type identity colors (used in portraits, VFX, boss themes)
# ----------------------------------------------------------------------------

ICE_TYPE_WATCHDOG_COLOR: Final[tuple[int, int, int]] = (220, 180, 100)  # amber
ICE_TYPE_BLACK_COLOR: Final[tuple[int, int, int]] = (180, 100, 220)  # magenta
ICE_TYPE_CONSTRUCT_COLOR: Final[tuple[int, int, int]] = (220, 220, 220)  # silver
ICE_TYPE_PATROL_COLOR: Final[tuple[int, int, int]] = (180, 180, 200)  # patrol gray-blue
ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR: Final[tuple[int, int, int]] = (255, 255, 0)  # bright yellow
ICE_TYPE_NEUROMANCER_COLOR: Final[tuple[int, int, int]] = (255, 0, 100)  # hot pink

# ----------------------------------------------------------------------------
# Boss VFX theme colors (per boss, for shake/flash/particle)
# ----------------------------------------------------------------------------

WINTERMUTE_THEME_COLOR: Final[tuple[int, int, int]] = (150, 150, 255)  # pale cyan
WINTERMUTE_PARTICLE_COLOR: Final[tuple[int, int, int]] = (100, 100, 255)  # neural blue
GOLIATH_THEME_COLOR: Final[tuple[int, int, int]] = DAMAGE_COLOR  # red shake/flash
GOLIATH_PARTICLE_COLOR: Final[tuple[int, int, int]] = (255, 100, 100)  # light red particles
BLACK_ICE_THEME_COLOR: Final[tuple[int, int, int]] = (180, 100, 220)  # magenta
WATCHDOG_THEME_COLOR: Final[tuple[int, int, int]] = (255, 220, 100)  # amber (BUFF_COLOR)
TA_CONSTRUCT_THEME_COLOR: Final[tuple[int, int, int]] = (200, 200, 255)  # white/cyan
TA_CONSTRUCT_PARTICLE_COLOR: Final[tuple[int, int, int]] = (200, 200, 255)  # white/cyan

# ----------------------------------------------------------------------------
# TA Construct Prime boss phase colors (4-tier escalation)
# ----------------------------------------------------------------------------

TA_CONSTRUCT_P1_COLOR: Final[tuple[int, int, int]] = (220, 220, 220)  # P1 — observing
TA_CONSTRUCT_P2_COLOR: Final[tuple[int, int, int]] = (200, 100, 100)  # P2 — engaging
TA_CONSTRUCT_P3_COLOR: Final[tuple[int, int, int]] = (180, 50, 180)  # P3 — replicating
TA_CONSTRUCT_P4_COLOR: Final[tuple[int, int, int]] = YELLOW_PURE  # P4 — family vote

# ----------------------------------------------------------------------------
# Status effects
# ----------------------------------------------------------------------------

SHIELD_COLOR: Final[tuple[int, int, int]] = (100, 200, 255)  # cyan
BUFF_COLOR: Final[tuple[int, int, int]] = (255, 220, 100)  # yellow
DEBUFF_COLOR: Final[tuple[int, int, int]] = (200, 100, 255)  # purple
STUN_COLOR: Final[tuple[int, int, int]] = (255, 255, 100)  # bright yellow

# ----------------------------------------------------------------------------
# Special / cinematic
# ----------------------------------------------------------------------------

GLITCH_COLOR: Final[tuple[int, int, int]] = (255, 0, 255)  # magenta
DEFAULT_COLOR: Final[tuple[int, int, int]] = (200, 200, 200)  # gray-white
VIGNETTE_COLOR: Final[tuple[int, int, int]] = (50, 0, 0)  # dark red

# ----------------------------------------------------------------------------
# Boss phase colors (4-tier escalation)
# ----------------------------------------------------------------------------

PHASE_COLORS: Final[tuple[tuple[int, int, int], ...]] = (
    (180, 180, 200),  # P0 - silver (normal)
    (255, 180, 100),  # P1 - warning
    (255, 100, 100),  # P2 - danger
    (255, 50, 50),  # P3 - critical
)

# ----------------------------------------------------------------------------
# ICE type palettes (5 distinct color schemes)
# ----------------------------------------------------------------------------

ICE_STANDARD_PALETTE: Final[tuple[tuple[int, int, int], ...]] = (
    (180, 180, 200),  # idle
    (200, 200, 220),  # name reveal
    (220, 220, 240),  # focus
    (240, 240, 255),  # peak
)

ICE_WATCHDOG_PALETTE: Final[tuple[tuple[int, int, int], ...]] = (
    (200, 150, 100),  # idle
    (220, 170, 100),  # warm
    (255, 100, 100),  # alert (red)
    (255, 150, 100),  # howl
    (255, 200, 100),  # peak
)

ICE_GOLIATH_PALETTE: Final[tuple[tuple[int, int, int], ...]] = (
    (200, 200, 220),  # silver
    (255, 180, 100),  # warning
    (255, 100, 100),  # danger
    (255, 200, 50),  # gold
    (255, 50, 50),  # crimson
)

ICE_BLACK_PALETTE: Final[tuple[tuple[int, int, int], ...]] = (
    (180, 180, 180),  # gray
    (200, 200, 200),  # light gray
    (255, 0, 255),  # magenta (glitch)
    (255, 0, 100),  # hot pink
    (150, 0, 200),  # deep purple
)

ICE_CONSTRUCT_PALETTE: Final[tuple[tuple[int, int, int], ...]] = (
    (150, 150, 180),  # idle
    (180, 180, 200),  # warm
    (200, 200, 220),  # alert
    (220, 220, 240),  # name
    (240, 240, 255),  # peak
)

ICE_PALETTES: Final[dict[str, tuple[tuple[int, int, int], ...]]] = {
    "standard": ICE_STANDARD_PALETTE,
    "watchdog": ICE_WATCHDOG_PALETTE,
    "goliath": ICE_GOLIATH_PALETTE,
    "black": ICE_BLACK_PALETTE,
    "construct": ICE_CONSTRUCT_PALETTE,
}

# ----------------------------------------------------------------------------
# Combo stage colors (5-tier)
# ----------------------------------------------------------------------------

COMBO_STAGE_COLORS: Final[tuple[tuple[int, int, int], ...]] = (
    (200, 200, 200),  # WARMUP - gray
    (100, 230, 130),  # CHAIN - green
    (255, 200, 80),  # FLURRY - yellow
    (255, 100, 80),  # RAMPAGE - orange
    (255, 30, 30),  # ANNIHILATION - red
)

# Combo timing bar
COMBO_BAR_GREEN: Final[tuple[int, int, int]] = (100, 230, 130)
COMBO_BAR_YELLOW: Final[tuple[int, int, int]] = (255, 200, 80)
COMBO_BAR_RED: Final[tuple[int, int, int]] = (255, 80, 80)

# ----------------------------------------------------------------------------
# Combo finisher colors
# ----------------------------------------------------------------------------

FINISHER_COLORS: Final[dict[str, tuple[int, int, int]]] = {
    "quick_slash": (255, 200, 80),  # yellow
    "rampage_burst": (255, 100, 80),  # orange
    "final_strike": (255, 30, 30),  # red
}

# ----------------------------------------------------------------------------
# Achievement tier colors
# ----------------------------------------------------------------------------

TIER_BRONZE: Final[tuple[int, int, int]] = (205, 127, 50)
TIER_SILVER: Final[tuple[int, int, int]] = (192, 192, 192)
TIER_GOLD: Final[tuple[int, int, int]] = (255, 215, 0)
TIER_PLATINUM: Final[tuple[int, int, int]] = (229, 228, 226)

# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------


def get_color_for_hp_pct(hp_pct: float) -> tuple[int, int, int]:
    """Get HP color based on percentage (0.0-1.0).

    Returns:
      - green if > 50%
      - yellow if > 30%
      - orange if > 10%
      - red otherwise
    """
    if hp_pct > 0.5:
        return HP_HIGH_COLOR
    if hp_pct > 0.3:
        return HP_MID_COLOR
    if hp_pct > 0.1:
        return HP_LOW_COLOR
    return HP_CRIT_COLOR


def get_color_for_phase(phase_index: int) -> tuple[int, int, int]:
    """Get the boss phase color for a given phase index (0-3).

    Clamps to valid range. Default to silver for unknown.
    """
    if 0 <= phase_index < len(PHASE_COLORS):
        return PHASE_COLORS[phase_index]
    return PHASE_COLORS[0]


def get_color_for_combo_stage(stage_index: int) -> tuple[int, int, int]:
    """Get the combo stage color for a given stage index (0-4).

    Clamps to valid range. Default to gray.
    """
    if 0 <= stage_index < len(COMBO_STAGE_COLORS):
        return COMBO_STAGE_COLORS[stage_index]
    return COMBO_STAGE_COLORS[0]


def get_palette_for_ice(ice_type: str) -> tuple[tuple[int, int, int], ...]:
    """Get the color palette for an ICE type.

    Falls back to STANDARD if unknown.
    """
    return ICE_PALETTES.get(ice_type, ICE_STANDARD_PALETTE)


def get_color_for_tier(tier: str) -> tuple[int, int, int]:
    """Get the achievement tier color."""
    return {
        "bronze": TIER_BRONZE,
        "silver": TIER_SILVER,
        "gold": TIER_GOLD,
        "platinum": TIER_PLATINUM,
    }.get(tier, TIER_BRONZE)


def fade_color(
    color: tuple[int, int, int],
    alpha: float,
) -> tuple[int, int, int]:
    """Apply alpha (0.0-1.0) to a color, darkening toward black.

    Used for particles and fading elements.
    """
    r, g, b = color
    return (int(r * alpha), int(g * alpha), int(b * alpha))


__all__ = [
    "BUFF_COLOR",
    "COMBO_BAR_GREEN",
    "COMBO_BAR_RED",
    "COMBO_BAR_YELLOW",
    "COMBO_STAGE_COLORS",
    "CRIT_COLOR",
    "DAMAGE_COLOR",
    "DAMAGE_FLASH_COLOR",
    "DEBUFF_COLOR",
    "DEFAULT_COLOR",
    "DYING_COLOR",
    "FINISHER_COLORS",
    "GLITCH_COLOR",
    "GRAY_120",
    "GRAY_160",
    "GRAY_BLACK",
    "GRAY_BRIGHT",
    "GRAY_DARK",
    "GRAY_LIGHT",
    "GRAY_MID",
    "GRAY_MID_DARK",
    "GRAY_MID_LIGHT",
    "GRAY_VERY_DARK",
    "GOLIATH_PARTICLE_COLOR",
    "GOLIATH_THEME_COLOR",
    "GREEN_BRIGHT",
    "GREEN_PURE",
    "HEAL_COLOR",
    "HIT_FLASH_COLOR",
    "BLACK_ICE_THEME_COLOR",
    "HP_CRIT_COLOR",
    "HP_HIGH_COLOR",
    "HP_LOW_COLOR",
    "HP_MID_COLOR",
    "ICE_TYPE_BLACK_COLOR",
    "ICE_TYPE_CONSTRUCT_COLOR",
    "ICE_TYPE_NEUROMANCER_COLOR",
    "ICE_TYPE_PATROL_COLOR",
    "ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR",
    "ICE_TYPE_WATCHDOG_COLOR",
    "LIFE_STEAL_COLOR",
    "ICE_BLACK_PALETTE",
    "ICE_BREAK_COLOR",
    "ICE_CONSTRUCT_PALETTE",
    "ICE_GOLIATH_PALETTE",
    "ICE_PALETTES",
    "ICE_STANDARD_PALETTE",
    "ICE_WATCHDOG_PALETTE",
    "JAMMER_COLOR",
    "PHASE_COLORS",
    "PROBE_COLOR",
    "SHIELD_COLOR",
    "STUN_COLOR",
    "TIER_BRONZE",
    "TIER_GOLD",
    "TIER_PLATINUM",
    "TIER_SILVER",
    "TA_CONSTRUCT_P1_COLOR",
    "TA_CONSTRUCT_PARTICLE_COLOR",
    "TA_CONSTRUCT_P2_COLOR",
    "TA_CONSTRUCT_P3_COLOR",
    "TA_CONSTRUCT_P4_COLOR",
    "TA_CONSTRUCT_THEME_COLOR",
    "WATCHDOG_THEME_COLOR",
    "WINTERMUTE_PARTICLE_COLOR",
    "WINTERMUTE_THEME_COLOR",
    "TA_CONSTRUCT_P2_COLOR",
    "TA_CONSTRUCT_P3_COLOR",
    "TA_CONSTRUCT_P4_COLOR",
    "VIGNETTE_COLOR",
    "WINTERMUTE_P1_COLOR",
    "WINTERMUTE_P2_COLOR",
    "WINTERMUTE_P3_COLOR",
    "WINTERMUTE_P4_COLOR",
    "WISP_COLOR",
    "YELLOW_PURE",
    "fade_color",
    "get_color_for_combo_stage",
    "get_color_for_hp_pct",
    "get_color_for_phase",
    "get_color_for_tier",
    "get_palette_for_ice",
]
