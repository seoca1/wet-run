"""ICE Aggression Tiers sub-module (ADR-0150, depth split).

4-tier aggression probability (per AUTO_ATTACK interval):
- PASSIVE: 5% (tutorial ICE, low-grade)
- STANDARD: 15% (watchdogs, standard, patrol)
- AGGRESSIVE: 35% (black, goliath, hunter)
- BOSS: 50% (wintermute, neuromancer, ta_prime)

Pillar 정합 (ADR-0148 §Consequences.7):
- P1 (The Run): 점진적 (tier-based, ADR-0147 alarm-aware salvage 가 보완)
- P5 (The Style): 깁슨 "ICE signature" 어휘
"""

from __future__ import annotations

import random
from enum import StrEnum

from ..state_models import Combatant


class AggressionLevel(StrEnum):
    """ICE aggression tier (ADR-0148)."""

    PASSIVE = "passive"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    BOSS = "boss"


# Aggression tier skill use probability (per AUTO_ATTACK interval).
AGGRESSION_PROBABILITY: dict[str, float] = {
    "passive": 0.05,
    "standard": 0.15,
    "aggressive": 0.35,
    "boss": 0.50,
}


def _combatant_aggression(combatant: Combatant) -> AggressionLevel:
    """Read aggression tier from a combatant, defaulting to STANDARD."""
    raw = getattr(combatant, "aggression", None)
    if raw is None:
        return AggressionLevel.STANDARD
    if isinstance(raw, AggressionLevel):
        return raw
    try:
        return AggressionLevel(str(raw))
    except ValueError:
        return AggressionLevel.STANDARD


def _skill_use_probability(combatant: Combatant) -> float:
    """Return the per-tick skill use probability for a combatant."""
    tier = _combatant_aggression(combatant)
    return AGGRESSION_PROBABILITY[tier.value]


def enemy_should_use_skill(combatant: Combatant, rng: random.Random) -> bool:
    """Return True if the enemy should use a skill this tick.

    Probability is determined by the combatant's aggression tier.
    """
    if not combatant.skills:
        return False
    probability = _skill_use_probability(combatant)
    return rng.random() < probability


__all__ = [
    "AGGRESSION_PROBABILITY",
    "AggressionLevel",
    "enemy_should_use_skill",
]
