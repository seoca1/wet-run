"""Auto-Play Tempo Layering (ADR-0140 §Proposal 8).

Configurable pacing for graphic novel auto-play. Three modes adjust
the dialogue advancement rate via a multiplier applied to elapsed time.

Mapping:
- SLOW   = 0.7x multiplier (durations feel 1.43x longer)
- NORMAL = 1.0x multiplier (default pacing)
- FAST   = 1.5x multiplier (durations feel 0.67x shorter)

Implementation: the multiplier is applied to the elapsed_ms delta in
main_loop._advance_graphic_novel. Higher multiplier = faster auto-play.
"""

from __future__ import annotations

from enum import StrEnum


class TempoMode(StrEnum):
    """Auto-play tempo modes (ADR-0140 P2.8)."""

    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


# Multipliers (applied to elapsed_ms delta).
TEMPO_MULTIPLIERS: dict[TempoMode, float] = {
    TempoMode.SLOW: 0.7,
    TempoMode.NORMAL: 1.0,
    TempoMode.FAST: 1.5,
}

DEFAULT_TEMPO_MODE: TempoMode = TempoMode.NORMAL


def get_tempo_multiplier(mode: TempoMode | str) -> float:
    """Return the elapsed_ms multiplier for a tempo mode.

    Args:
        mode: TempoMode enum or string value.

    Returns:
        Multiplier (0.7, 1.0, or 1.5). Defaults to 1.0 if unknown.
    """
    if isinstance(mode, str):
        try:
            mode = TempoMode(mode)
        except ValueError:
            return 1.0
    return TEMPO_MULTIPLIERS.get(mode, 1.0)


def cycle_tempo_mode(current: TempoMode) -> TempoMode:
    """Cycle to the next tempo mode (SLOW → NORMAL → FAST → SLOW)."""
    cycle = [TempoMode.SLOW, TempoMode.NORMAL, TempoMode.FAST]
    idx = cycle.index(current) if current in cycle else 1
    return cycle[(idx + 1) % 3]


__all__ = [
    "TempoMode",
    "TEMPO_MULTIPLIERS",
    "DEFAULT_TEMPO_MODE",
    "get_tempo_multiplier",
    "cycle_tempo_mode",
]
