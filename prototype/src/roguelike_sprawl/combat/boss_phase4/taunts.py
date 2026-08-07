"""Boss Death Taunts sub-module (ADR-0150, boss_phase4 split).

Player death by boss triggers a random taunt line from the boss's pool.
2-3 lines per boss, 5 boss total = 15 taunts.

Pillar 정합 (ADR-0149 §Consequences.7):
- P3 (The Flatline): death taunts 가 Pillar 3 weight 강화
- P5 (The Style): 5 unique 깁슨 어휘
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..state import CombatState


# Death taunt pool per boss (English).
DEATH_TAUNTS: dict[str, tuple[str, ...]] = {
    "wintermute": (
        "I see you, cowboy. Your pattern is mine.",
        "You wanted the matrix. Now the matrix has you.",
        "Trace complete. You were never here.",
    ),
    "ta_prime": (
        "Family consensus: you are not welcome.",
        "Three voices, one verdict. Trace.",
        "Tessier-Ashpool remembers every intrusion.",
    ),
    "neuromancer": (
        "We are the merger. You are the remainder.",
        "Construct preserved. Operator discarded.",
        "The matrix has you, cowboy. Always did.",
    ),
    "goliath_prime": (
        "Ground... settles... all.",
        "Heavy. Final. Static.",
        "Protocol complete. Architecture intact.",
    ),
    "black_ice_lord": (
        "Glitch. Catch. Static. You.",
        "Corrupt. Infect. Compile. Done.",
        "You were never real. We were.",
    ),
}


def pick_death_taunt(boss_id: str, rng: random.Random | None = None) -> str | None:
    """Return a random death taunt line for the given boss.

    Returns None if the boss has no death taunt pool.
    """
    if rng is None:
        rng = random.Random()
    from .intro import normalize_boss_id

    canonical = normalize_boss_id(boss_id)
    pool = DEATH_TAUNTS.get(canonical)
    if pool is None:
        return None
    return rng.choice(pool)


def apply_death_taunt(state: CombatState, app_state: Any, boss_id: str) -> str | None:
    """Pick and apply a death taunt to app_state.death_taunt.

    Returns the taunt line or None if not a known boss.
    """
    taunt = pick_death_taunt(boss_id)
    if taunt is None:
        return None
    app_state.death_taunt = taunt
    state.push(f">>> {boss_id}: {taunt}")
    return taunt


__all__ = [
    "DEATH_TAUNTS",
    "apply_death_taunt",
    "pick_death_taunt",
]
