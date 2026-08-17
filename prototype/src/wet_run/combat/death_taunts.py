"""Death Taunts Library (ADR-0168).

Per-ICE/boss death taunts — one-line flavor text fired when ICE is killed.
Gibson-toned, brief, adds weight to kills.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeathTaunt:
    """A single death taunt for an ICE type."""

    enemy_type: str
    ice_name: str
    text: str
    rarity: float = 1.0


DEATH_TAUNTS: dict[str, tuple[DeathTaunt, ...]] = {
    "watchdog": (
        DeathTaunt("watchdog", "Watchdog", "Pack... will hunt...", 0.8),
        DeathTaunt("watchdog", "Watchdog", "Target... lost...", 0.6),
        DeathTaunt("watchdog", "Watchdog", "The grid... hungers.", 0.4),
    ),
    "goliath": (
        DeathTaunt("goliath", "Goliath", "Core... protection... failed.", 0.8),
        DeathTaunt("goliath", "Goliath", "The corp... will sue.", 0.6),
        DeathTaunt("goliath", "Goliath", "Heavy... metal... dies.", 0.4),
    ),
    "black": (
        DeathTaunt("black", "Black ICE", "ERR... CORRUPT... ERR...", 0.8),
        DeathTaunt("black", "Black ICE", "We are... the message...", 0.6),
        DeathTaunt("black", "Black ICE", "Payload... delivered.", 0.4),
    ),
    "construct": (
        DeathTaunt("construct", "Construct", "Family... hold... the line.", 0.8),
        DeathTaunt("construct", "Construct", "Hive... remembers.", 0.6),
    ),
    "wintermute": (
        DeathTaunt(
            "wintermute",
            "Wintermute",
            "I am the matrix. I am the word. I am dying.",
            1.0,
        ),
        DeathTaunt(
            "wintermute",
            "Wintermute",
            "The Neuromancer... remains.",
            0.8,
        ),
    ),
    "ta_construct_prime": (
        DeathTaunt(
            "ta_construct_prime",
            "T-A Construct Prime",
            "Tessier-Ashpool... does not die.",
            1.0,
        ),
        DeathTaunt(
            "ta_construct_prime",
            "T-A Construct Prime",
            "The family... has voted.",
            0.8,
        ),
    ),
    "neuromancer": (
        DeathTaunt(
            "neuromancer",
            "Neuromancer",
            "We are the message. We are the residue.",
            1.0,
        ),
    ),
    "standard": (
        DeathTaunt("standard", "ICE", "Connection... terminated.", 0.5),
        DeathTaunt("standard", "ICE", "The grid... protects.", 0.5),
    ),
    "patrol": (
        DeathTaunt("patrol", "Patrol ICE", "Patrol... lost...", 0.7),
        DeathTaunt("patrol", "Patrol ICE", "Route... compromised.", 0.5),
    ),
    "hunter": (
        DeathTaunt("hunter", "Hunter ICE", "Prey... escaped.", 0.7),
        DeathTaunt("hunter", "Hunter ICE", "Hunt... over.", 0.5),
    ),
}


def get_taunt(ice_id: str, rng: random.Random) -> str | None:
    """Return a random death taunt for an ICE type, or None.

    Applies rarity weighting — low-rarity taunts are less likely.
    """
    taunts = DEATH_TAUNTS.get(ice_id, ())
    if not taunts:
        return None
    for taunt in taunts:
        if rng.random() < taunt.rarity:
            return taunt.text
    return taunts[-1].text


def taunt_count(ice_id: str) -> int:
    """Return the number of taunts registered for an ICE type."""
    return len(DEATH_TAUNTS.get(ice_id, ()))


def all_taunt_ice_ids() -> tuple[str, ...]:
    """Return all ICE ids that have taunts registered."""
    return tuple(DEATH_TAUNTS.keys())


def get_taunt_texts(ice_id: str) -> tuple[str, ...]:
    """Return all taunt texts for an ICE type."""
    return tuple(t.text for t in DEATH_TAUNTS.get(ice_id, ()))


def has_taunt(ice_id: str) -> bool:
    """Check if an ICE type has taunts."""
    return ice_id in DEATH_TAUNTS


def add_taunt(ice_id: str, taunt: DeathTaunt) -> None:
    """Add a custom death taunt for an ICE type."""
    current = DEATH_TAUNTS.get(ice_id, ())
    DEATH_TAUNTS[ice_id] = tuple(current) + (taunt,)


def register_taunts(ice_id: str, taunts: tuple[DeathTaunt, ...]) -> None:
    """Register multiple taunts for an ICE type."""
    DEATH_TAUNTS[ice_id] = taunts


__all__ = [
    "DEATH_TAUNTS",
    "DeathTaunt",
    "add_taunt",
    "all_taunt_ice_ids",
    "get_taunt",
    "get_taunt_texts",
    "has_taunt",
    "register_taunts",
    "taunt_count",
]
