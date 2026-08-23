"""ASCII Battle Portrait Evolution (ADR-0171).

ASCII portraits for ICE/bosses change based on combat state:
- HP thresholds (full/healthy/wounded/critical/dying)
- Status effects (burn glow, stun shake, slow trail, silence cross-out)
- Phase progression (boss portraits change color per phase)
"""

from __future__ import annotations

from dataclasses import dataclass

from .palette import (
    CRIT_COLOR,
    DAMAGE_COLOR,
    DEFAULT_COLOR,
    DYING_COLOR,
    ICE_TYPE_BLACK_COLOR,
    ICE_TYPE_CONSTRUCT_COLOR,
    ICE_TYPE_NEUROMANCER_COLOR,
    ICE_TYPE_PATROL_COLOR,
    ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
    ICE_TYPE_WATCHDOG_COLOR,
    TA_CONSTRUCT_P1_COLOR,
    TA_CONSTRUCT_P2_COLOR,
    TA_CONSTRUCT_P3_COLOR,
    TA_CONSTRUCT_P4_COLOR,
    WINTERMUTE_P1_COLOR,
    WINTERMUTE_P2_COLOR,
    WINTERMUTE_P3_COLOR,
    WINTERMUTE_P4_COLOR,
)


@dataclass(frozen=True, slots=True)
class BattlePortrait:
    """Visual portrait for a combatant."""

    base_glyph: str
    color: tuple[int, int, int]
    effect_overlay: str = ""
    suffix: str = ""


HP_THRESHOLDS: dict[str, float] = {
    "full": 0.95,
    "healthy": 0.7,
    "wounded": 0.4,
    "critical": 0.2,
    "dying": 0.0,
}

ICE_PORTRAITS: dict[str, str] = {
    "watchdog": "W",
    "goliath": "G",
    "black": "B",
    "construct": "C",
    "standard": "I",
    "patrol": "P",
    "hunter": "H",
    "wintermute": "?",
    "ta_construct_prime": "T",
    "neuromancer": "N",
}

ICE_COLORS: dict[str, tuple[int, int, int]] = {
    "watchdog": ICE_TYPE_WATCHDOG_COLOR,
    "goliath": DAMAGE_COLOR,
    "black": ICE_TYPE_BLACK_COLOR,
    "construct": ICE_TYPE_CONSTRUCT_COLOR,
    "standard": DEFAULT_COLOR,
    "patrol": ICE_TYPE_PATROL_COLOR,
    "hunter": CRIT_COLOR,
    "wintermute": WINTERMUTE_P1_COLOR,
    "ta_construct_prime": ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
    "neuromancer": ICE_TYPE_NEUROMANCER_COLOR,
}

BOSS_PHASE_COLORS: dict[str, dict[int, tuple[int, int, int]]] = {
    "wintermute": {
        1: WINTERMUTE_P1_COLOR,
        2: WINTERMUTE_P2_COLOR,
        3: WINTERMUTE_P3_COLOR,
        4: WINTERMUTE_P4_COLOR,
    },
    "ta_construct_prime": {
        1: TA_CONSTRUCT_P1_COLOR,
        2: TA_CONSTRUCT_P2_COLOR,
        3: TA_CONSTRUCT_P3_COLOR,
        4: TA_CONSTRUCT_P4_COLOR,
    },
}


def get_hp_threshold(ratio: float) -> str:
    """Return the HP threshold category for a given HP ratio."""
    if ratio >= HP_THRESHOLDS["full"]:
        return "full"
    if ratio >= HP_THRESHOLDS["healthy"]:
        return "healthy"
    if ratio >= HP_THRESHOLDS["wounded"]:
        return "wounded"
    if ratio >= HP_THRESHOLDS["critical"]:
        return "critical"
    return "dying"


def get_color_for_threshold(ice_type: str, threshold: str) -> tuple[int, int, int]:
    """Return the color for an ICE type at a given HP threshold."""
    base = ICE_COLORS.get(ice_type, DEFAULT_COLOR)
    if threshold == "full":
        return base
    if threshold == "healthy":
        return _darken(base, 0.8)
    if threshold == "wounded":
        return _darken(base, 0.6)
    if threshold == "critical":
        return _darken(base, 0.4)
    return DYING_COLOR


def _darken(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    """Darken a color by a factor."""
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


def get_status_overlay(status_effect_ids: tuple[str, ...]) -> str:
    """Compute the visual overlay for a set of active status effects."""
    overlays = []
    if "burn" in status_effect_ids:
        overlays.append("^")  # fire chars
    if "stun" in status_effect_ids:
        overlays.append("~")  # dazed
    if "slow" in status_effect_ids:
        overlays.append("...")  # ghostly trail
    if "silence" in status_effect_ids:
        overlays.append("X")  # muted cross-out
    if "vulnerable" in status_effect_ids:
        overlays.append("!")  # exploitable
    return "".join(overlays)


def get_glyph_for_threshold(ice_type: str, threshold: str) -> str:
    """Return the ASCII glyph for an ICE type at a given HP threshold."""
    base = ICE_PORTRAITS.get(ice_type, "?")
    if threshold == "dying":
        return base.lower()
    if threshold == "critical":
        return base + "*"
    return base


def get_portrait(
    ice_type: str,
    hp_ratio: float = 1.0,
    status_effect_ids: tuple[str, ...] = (),
    phase: int = 1,
) -> BattlePortrait:
    """Return a BattlePortrait for an ICE type with current combat state."""
    threshold = get_hp_threshold(hp_ratio)
    base_glyph = get_glyph_for_threshold(ice_type, threshold)
    if ice_type in BOSS_PHASE_COLORS:
        phase_colors = BOSS_PHASE_COLORS[ice_type]
        if phase in phase_colors:
            color = phase_colors[phase]
        else:
            color = phase_colors[max(phase_colors.keys())]
    else:
        color = get_color_for_threshold(ice_type, threshold)
    overlay = get_status_overlay(status_effect_ids)
    suffix = ""
    if overlay:
        suffix = f" [{overlay}]"
    return BattlePortrait(
        base_glyph=base_glyph,
        color=color,
        effect_overlay=overlay,
        suffix=suffix,
    )


def get_known_ice_types() -> tuple[str, ...]:
    """Return all known ICE types."""
    return tuple(ICE_PORTRAITS.keys())


def is_known_ice_type(ice_type: str) -> bool:
    """Check if an ICE type is known."""
    return ice_type in ICE_PORTRAITS


def get_phase_count(ice_type: str) -> int:
    """Return the number of phases for a boss ICE type."""
    if ice_type in BOSS_PHASE_COLORS:
        return len(BOSS_PHASE_COLORS[ice_type])
    return 0


__all__ = [
    "BOSS_PHASE_COLORS",
    "BattlePortrait",
    "HP_THRESHOLDS",
    "ICE_COLORS",
    "ICE_PORTRAITS",
    "get_color_for_threshold",
    "get_glyph_for_threshold",
    "get_hp_threshold",
    "get_known_ice_types",
    "get_phase_count",
    "get_portrait",
    "get_status_overlay",
    "is_known_ice_type",
]
