"""Finisher Combos (ADR-0181).

Player-triggered finisher moves at combo thresholds.
At combo >= threshold, player can trigger a devastating move.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FinisherCombo:
    """A player-triggered finisher combo."""

    id: str
    name: str
    combo_threshold: int
    damage_multiplier: float
    effect_type: str
    cooldown_ms: int


FINISHER_REGISTRY: dict[str, FinisherCombo] = {
    "burst": FinisherCombo(
        id="burst",
        name="BURST",
        combo_threshold=5,
        damage_multiplier=2.0,
        effect_type="burst",
        cooldown_ms=3000,
    ),
    "pierce": FinisherCombo(
        id="pierce",
        name="PIERCE",
        combo_threshold=8,
        damage_multiplier=1.5,
        effect_type="pierce",
        cooldown_ms=4000,
    ),
    "silence": FinisherCombo(
        id="silence",
        name="SILENCE",
        combo_threshold=12,
        damage_multiplier=1.0,
        effect_type="silence",
        cooldown_ms=5000,
    ),
    "burn": FinisherCombo(
        id="burn",
        name="BURN",
        combo_threshold=15,
        damage_multiplier=2.5,
        effect_type="burn",
        cooldown_ms=6000,
    ),
}


def get_finisher(combo_id: str) -> FinisherCombo | None:
    """Return finisher by id."""
    return FINISHER_REGISTRY.get(combo_id)


def list_finishers() -> tuple[FinisherCombo, ...]:
    """Return all finishers."""
    return tuple(FINISHER_REGISTRY.values())


def get_finisher_count() -> int:
    """Return the number of finishers."""
    return len(FINISHER_REGISTRY)


def get_highest_combo_finisher(combo_count: int) -> FinisherCombo | None:
    """Return the highest-tier finisher available at this combo count."""
    for finisher in sorted(
        FINISHER_REGISTRY.values(),
        key=lambda f: f.combo_threshold,
        reverse=True,
    ):
        if combo_count >= finisher.combo_threshold:
            return finisher
    return None


def list_available_finishers(combo_count: int) -> tuple[FinisherCombo, ...]:
    """Return all finishers available at this combo count."""
    return tuple(
        f for f in FINISHER_REGISTRY.values() if combo_count >= f.combo_threshold
    )


def can_trigger_finisher(
    combo_count: int,
    finisher_id: str,
    last_trigger_ms: int,
    current_ms: int,
) -> bool:
    """Return True if a finisher can be triggered."""
    finisher = get_finisher(finisher_id)
    if finisher is None:
        return False
    if combo_count < finisher.combo_threshold:
        return False
    if current_ms - last_trigger_ms < finisher.cooldown_ms:
        return False
    return True


def get_finisher_remaining_cooldown(
    finisher_id: str,
    last_trigger_ms: int,
    current_ms: int,
) -> int:
    """Return the remaining cooldown in ms (0 if ready)."""
    finisher = get_finisher(finisher_id)
    if finisher is None:
        return 0
    elapsed = current_ms - last_trigger_ms
    return max(0, finisher.cooldown_ms - elapsed)


def get_finisher_ids() -> tuple[str, ...]:
    """Return all finisher ids."""
    return tuple(FINISHER_REGISTRY.keys())


def has_finisher(finisher_id: str) -> bool:
    """Return True if finisher exists."""
    return finisher_id in FINISHER_REGISTRY


__all__ = [
    "FINISHER_REGISTRY",
    "FinisherCombo",
    "can_trigger_finisher",
    "get_finisher",
    "get_finisher_count",
    "get_finisher_ids",
    "get_finisher_remaining_cooldown",
    "get_highest_combo_finisher",
    "has_finisher",
    "list_available_finishers",
    "list_finishers",
]
