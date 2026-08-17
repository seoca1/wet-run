"""Deck Building (ADR-0178).

Three deck sizes with slot limits and trade-offs:
- LIGHT (6 slots): faster AP regen, shorter cooldowns
- STANDARD (8 slots): balanced
- HEAVY (10 slots): more options, slower AP regen
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeckSize:
    """A deck size configuration."""

    name: str
    slots: int
    ap_regen_bonus: float
    cooldown_modifier: float


DECK_SIZES: dict[str, DeckSize] = {
    "light": DeckSize(
        name="LIGHT",
        slots=6,
        ap_regen_bonus=0.5,
        cooldown_modifier=-0.10,
    ),
    "standard": DeckSize(
        name="STANDARD",
        slots=8,
        ap_regen_bonus=0.0,
        cooldown_modifier=0.0,
    ),
    "heavy": DeckSize(
        name="HEAVY",
        slots=10,
        ap_regen_bonus=-0.3,
        cooldown_modifier=0.15,
    ),
}


def get_deck_size(size: str) -> DeckSize | None:
    """Return deck size by name."""
    return DECK_SIZES.get(size.lower())


def get_deck_sizes() -> tuple[DeckSize, ...]:
    """Return all deck sizes."""
    return (DECK_SIZES["light"], DECK_SIZES["standard"], DECK_SIZES["heavy"])


def get_slot_limit(size: str) -> int:
    """Return the slot limit for a deck size."""
    deck = get_deck_size(size)
    if deck is None:
        return DECK_SIZES["standard"].slots
    return deck.slots


def get_ap_regen_bonus(size: str) -> float:
    """Return the AP regen bonus for a deck size."""
    deck = get_deck_size(size)
    if deck is None:
        return 0.0
    return deck.ap_regen_bonus


def get_cooldown_modifier(size: str) -> float:
    """Return the cooldown modifier for a deck size."""
    deck = get_deck_size(size)
    if deck is None:
        return 0.0
    return deck.cooldown_modifier


def get_deck_size_names() -> tuple[str, ...]:
    """Return the deck size names."""
    return tuple(DECK_SIZES.keys())


def is_valid_deck_size(size: str) -> bool:
    """Return True if the size is valid."""
    return size.lower() in DECK_SIZES


def get_default_deck_size() -> str:
    """Return the default deck size name."""
    return "standard"


__all__ = [
    "DECK_SIZES",
    "DeckSize",
    "get_ap_regen_bonus",
    "get_cooldown_modifier",
    "get_default_deck_size",
    "get_deck_size",
    "get_deck_size_names",
    "get_deck_sizes",
    "get_slot_limit",
    "is_valid_deck_size",
]
