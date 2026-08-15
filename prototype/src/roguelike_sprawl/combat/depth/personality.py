"""ICE Personality Archetypes (ADR-0161).

4 distinct behavioral patterns that complement aggression tier:
- AGGRESSIVE: max offense, +5% crit chance
- DEFENSIVE: prefer shield/buff when HP < 50%
- STEALTH: alarm generation × 0.5, prefer silence/slow
- SUPPORT: target allies, prefer heal/buff

Personality is *orthogonal* to aggression — a BOSS-tier ICE can be
DEFENSIVE personality, making it a "tank" raid boss.
"""

from __future__ import annotations

from enum import StrEnum

from ..state_models import Combatant, CombatState, Skill, SkillEffect


class PersonalityLevel(StrEnum):
    """ICE personality archetype (ADR-0161)."""

    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    STEALTH = "stealth"
    SUPPORT = "support"


# Per-personality skill preferences (in priority order)
PERSONALITY_SKILL_PREFERENCE: dict[str, tuple[SkillEffect, ...]] = {
    "aggressive": (
        SkillEffect.PIERCE,
        SkillEffect.HEAVY_ATTACK,
        SkillEffect.MULTI_HIT,
        SkillEffect.ATTACK,
        SkillEffect.DOT,
    ),
    "defensive": (
        SkillEffect.SHIELD,
        SkillEffect.BUFF,
        SkillEffect.HEAL,
        SkillEffect.STUN,
        SkillEffect.ATTACK,
    ),
    "stealth": (
        SkillEffect.SILENCE,
        SkillEffect.SLOW,
        SkillEffect.DEBUFF,
        SkillEffect.MULTI_HIT,
        SkillEffect.ATTACK,
    ),
    "support": (
        SkillEffect.HEAL,
        SkillEffect.BUFF,
        SkillEffect.SHIELD,
        SkillEffect.DEBUFF,
        SkillEffect.ATTACK,
    ),
}

DEFENSIVE_HP_THRESHOLD = 0.5
AGGRESSIVE_CRIT_BONUS = 0.05
STEALTH_ALARM_MULTIPLIER = 0.5


def _combatant_personality(combatant: Combatant) -> PersonalityLevel:
    """Resolve a combatant's personality attribute to a PersonalityLevel.

    Coerces raw string values (e.g. from JSON data) into the enum and
    falls back to AGGRESSIVE when the attribute is missing, malformed,
    or holds an unrecognized value. This guarantees downstream
    personality checks always receive a valid enum member.
    """
    raw = getattr(combatant, "personality", None)
    if raw is None:
        return PersonalityLevel.AGGRESSIVE
    if isinstance(raw, PersonalityLevel):
        return raw
    try:
        return PersonalityLevel(str(raw))
    except ValueError:
        return PersonalityLevel.AGGRESSIVE


def should_defensive_act(combatant: Combatant) -> bool:
    """Return True if combatant is DEFENSIVE and HP < 50%."""
    if _combatant_personality(combatant) != PersonalityLevel.DEFENSIVE:
        return False
    if combatant.max_hp <= 0:
        return False
    return combatant.hp / combatant.max_hp < DEFENSIVE_HP_THRESHOLD


def get_alarm_multiplier(combatant: Combatant) -> float:
    """Return the alarm generation multiplier for combatant.

    STEALTH personality halves alarm generation; others are 1.0.
    """
    if _combatant_personality(combatant) == PersonalityLevel.STEALTH:
        return STEALTH_ALARM_MULTIPLIER
    return 1.0


def get_crit_bonus(combatant: Combatant) -> float:
    """Return the crit bonus for combatant (AGGRESSIVE: +5%)."""
    if _combatant_personality(combatant) == PersonalityLevel.AGGRESSIVE:
        return AGGRESSIVE_CRIT_BONUS
    return 0.0


def should_target_ally(combatant: Combatant, state: CombatState) -> bool:
    """Return True if combatant should target an ally (SUPPORT + wounded ally)."""
    if _combatant_personality(combatant) != PersonalityLevel.SUPPORT:
        return False
    for other in state.enemies:
        if other is combatant:
            continue
        if other.team != combatant.team:
            continue
        if other.hp <= 0:
            continue
        if other.max_hp > 0 and other.hp / other.max_hp < 0.7:
            return True
    return False


def select_skill_by_personality(
    combatant: Combatant,
    available_skills: tuple[Skill, ...],
    state: CombatState,
) -> Skill | None:
    """Select the best skill for combatant based on personality archetype.

    Returns the first available skill matching the personality's
    preference order, or None if no match.
    """
    if not available_skills:
        return None

    personality = _combatant_personality(combatant)
    preference = PERSONALITY_SKILL_PREFERENCE[personality.value]

    by_effect: dict[SkillEffect, Skill] = {}
    for skill in available_skills:
        if skill.effect not in by_effect:
            by_effect[skill.effect] = skill

    for preferred_effect in preference:
        if preferred_effect in by_effect:
            return by_effect[preferred_effect]

    return available_skills[0]


__all__ = [
    "AGGRESSIVE_CRIT_BONUS",
    "DEFENSIVE_HP_THRESHOLD",
    "PERSONALITY_SKILL_PREFERENCE",
    "PersonalityLevel",
    "STEALTH_ALARM_MULTIPLIER",
    "get_alarm_multiplier",
    "get_crit_bonus",
    "select_skill_by_personality",
    "should_defensive_act",
    "should_target_ally",
]
