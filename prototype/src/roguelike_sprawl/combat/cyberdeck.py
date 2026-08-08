"""Cyberdeck Customization (ADR-0172).

Player pre-run loadout: 8 program slots. Programs are TOOLS (Pillar 4),
not stat boosts. Deck composition is a meaningful choice.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_DECK_SLOTS = 8
MAX_DECK_NAME_LENGTH = 32


@dataclass(frozen=True, slots=True)
class Cyberdeck:
    """Player's pre-run loadout: up to 8 program slots."""

    name: str
    program_ids: tuple[str, ...] = ()
    passive_bonus: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.name) > MAX_DECK_NAME_LENGTH:
            raise ValueError(
                f"Deck name too long: {len(self.name)} > {MAX_DECK_NAME_LENGTH}"
            )


def create_deck(name: str, program_ids: list[str] | None = None) -> Cyberdeck:
    """Create a new cyberdeck with the given name and program list."""
    if program_ids is None:
        program_ids = []
    return Cyberdeck(name=name, program_ids=tuple(program_ids))


def validate_deck(deck: Cyberdeck, max_slots: int = DEFAULT_DECK_SLOTS) -> bool:
    """Return True if deck is valid (has unique programs and fits in slots)."""
    if len(deck.program_ids) > max_slots:
        return False
    if len(set(deck.program_ids)) != len(deck.program_ids):
        return False
    return True


def add_program_to_deck(deck: Cyberdeck, program_id: str, max_slots: int = DEFAULT_DECK_SLOTS) -> Cyberdeck:
    """Add a program to the deck. Returns a new deck (frozen)."""
    if program_id in deck.program_ids:
        raise ValueError(f"Program {program_id} already in deck")
    if len(deck.program_ids) >= max_slots:
        raise ValueError(f"Deck full ({max_slots} slots)")
    new_ids = deck.program_ids + (program_id,)
    return Cyberdeck(
        name=deck.name,
        program_ids=new_ids,
        passive_bonus=dict(deck.passive_bonus),
    )


def remove_program_from_deck(deck: Cyberdeck, program_id: str) -> Cyberdeck:
    """Remove a program from the deck. Returns a new deck."""
    if program_id not in deck.program_ids:
        raise ValueError(f"Program {program_id} not in deck")
    new_ids = tuple(p for p in deck.program_ids if p != program_id)
    return Cyberdeck(
        name=deck.name,
        program_ids=new_ids,
        passive_bonus=dict(deck.passive_bonus),
    )


def get_deck_program_count(deck: Cyberdeck) -> int:
    """Return the number of programs in the deck."""
    return len(deck.program_ids)


def get_deck_slots_remaining(deck: Cyberdeck, max_slots: int = DEFAULT_DECK_SLOTS) -> int:
    """Return the number of empty slots."""
    return max_slots - len(deck.program_ids)


def has_program(deck: Cyberdeck, program_id: str) -> bool:
    """Return True if the deck contains the given program."""
    return program_id in deck.program_ids


__all__ = [
    "DEFAULT_DECK_SLOTS",
    "MAX_DECK_NAME_LENGTH",
    "Cyberdeck",
    "add_program_to_deck",
    "create_deck",
    "get_deck_program_count",
    "get_deck_slots_remaining",
    "has_program",
    "remove_program_from_deck",
    "validate_deck",
]
