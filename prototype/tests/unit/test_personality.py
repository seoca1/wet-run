"""Tests for ICE Personality Archetypes (ADR-0161)."""

from __future__ import annotations

import random

from roguelike_sprawl.combat.depth.personality import (
    PersonalityLevel,
    get_alarm_multiplier,
    get_crit_bonus,
    select_skill_by_personality,
    should_defensive_act,
    should_target_ally,
)
from roguelike_sprawl.combat.state import Combatant, CombatState, Skill, SkillEffect


def make_ice(
    personality: str = "aggressive",
    hp: int = 100,
    max_hp: int = 100,
    name: str = "ice",
) -> Combatant:
    return Combatant(
        id="e",
        name=name,
        portrait="X",
        color=(255, 0, 0),
        team="enemy",
        hp=hp,
        max_hp=max_hp,
        ap=5,
        max_ap=5,
        personality=personality,
    )


def make_state(ice: Combatant) -> CombatState:
    rng = random.Random(42)
    return CombatState(
        player=Combatant(
            id="p",
            name="player",
            portrait="@",
            color=(255, 255, 255),
            team="player",
            hp=100,
            max_hp=100,
            ap=5,
            max_ap=5,
        ),
        enemies=(ice,),
        rng=rng,
    )


def make_skill(effect: SkillEffect, id: str = "test") -> Skill:
    return Skill(
        id=id,
        name="Test",
        tier=1,
        effect=effect,
        ap_cost=1,
        effect_color=(255, 255, 255),
        effect_glyph="?",
    )


def test_aggressive_personality_boosts_crit() -> None:
    ice = make_ice("aggressive")
    assert get_crit_bonus(ice) == 0.05


def test_stealth_personality_halves_alarm() -> None:
    ice = make_ice("stealth")
    assert get_alarm_multiplier(ice) == 0.5


def test_defensive_personality_full_alarm() -> None:
    ice = make_ice("defensive")
    assert get_alarm_multiplier(ice) == 1.0


def test_support_personality_full_alarm() -> None:
    ice = make_ice("support")
    assert get_alarm_multiplier(ice) == 1.0


def test_defensive_should_act_when_low_hp() -> None:
    ice = make_ice("defensive", hp=40, max_hp=100)
    assert should_defensive_act(ice)


def test_defensive_should_not_act_when_high_hp() -> None:
    ice = make_ice("defensive", hp=80, max_hp=100)
    assert not should_defensive_act(ice)


def test_aggressive_should_not_defensive_act() -> None:
    ice = make_ice("aggressive", hp=10, max_hp=100)
    assert not should_defensive_act(ice)


def test_support_targets_ally_when_wounded() -> None:
    ice = make_ice("support")
    ally = make_ice("support", hp=30, max_hp=100, name="ally")
    state = CombatState(
        player=Combatant(
            id="p",
            name="player",
            portrait="@",
            color=(255, 255, 255),
            team="player",
            hp=100,
            max_hp=100,
        ),
        enemies=(ice, ally),
        rng=random.Random(42),
    )
    assert should_target_ally(ice, state)


def test_support_does_not_target_when_all_healthy() -> None:
    ice = make_ice("support")
    ally = make_ice("support", hp=100, max_hp=100, name="ally")
    state = CombatState(
        player=Combatant(
            id="p",
            name="player",
            portrait="@",
            color=(255, 255, 255),
            team="player",
            hp=100,
            max_hp=100,
        ),
        enemies=(ice, ally),
        rng=random.Random(42),
    )
    assert not should_target_ally(ice, state)


def test_aggressive_does_not_target_ally() -> None:
    ice = make_ice("aggressive")
    ally = make_ice("aggressive", hp=10, max_hp=100, name="ally")
    state = CombatState(
        player=Combatant(
            id="p",
            name="player",
            portrait="@",
            color=(255, 255, 255),
            team="player",
            hp=100,
            max_hp=100,
        ),
        enemies=(ice, ally),
        rng=random.Random(42),
    )
    assert not should_target_ally(ice, state)


def test_aggressive_selects_pierce_first() -> None:
    ice = make_ice("aggressive")
    skills = (make_skill(SkillEffect.ATTACK), make_skill(SkillEffect.PIERCE, "pierce"))
    state = make_state(ice)
    selected = select_skill_by_personality(ice, skills, state)
    assert selected is not None
    assert selected.effect == SkillEffect.PIERCE


def test_defensive_selects_shield_first() -> None:
    ice = make_ice("defensive")
    skills = (make_skill(SkillEffect.ATTACK), make_skill(SkillEffect.SHIELD, "shield"))
    state = make_state(ice)
    selected = select_skill_by_personality(ice, skills, state)
    assert selected is not None
    assert selected.effect == SkillEffect.SHIELD


def test_stealth_selects_silence_first() -> None:
    ice = make_ice("stealth")
    skills = (make_skill(SkillEffect.ATTACK), make_skill(SkillEffect.SILENCE, "silence"))
    state = make_state(ice)
    selected = select_skill_by_personality(ice, skills, state)
    assert selected is not None
    assert selected.effect == SkillEffect.SILENCE


def test_support_selects_heal_first() -> None:
    ice = make_ice("support")
    skills = (make_skill(SkillEffect.ATTACK), make_skill(SkillEffect.HEAL, "heal"))
    state = make_state(ice)
    selected = select_skill_by_personality(ice, skills, state)
    assert selected is not None
    assert selected.effect == SkillEffect.HEAL


def test_select_skill_returns_none_when_empty() -> None:
    ice = make_ice("aggressive")
    state = make_state(ice)
    assert select_skill_by_personality(ice, (), state) is None


def test_select_skill_falls_back_to_first_available() -> None:
    ice = make_ice("aggressive")
    skills = (make_skill(SkillEffect.DETECT),)
    state = make_state(ice)
    selected = select_skill_by_personality(ice, skills, state)
    assert selected is not None


def test_personality_level_str_enum() -> None:
    assert PersonalityLevel.AGGRESSIVE.value == "aggressive"
    assert PersonalityLevel.DEFENSIVE.value == "defensive"
    assert PersonalityLevel.STEALTH.value == "stealth"
    assert PersonalityLevel.SUPPORT.value == "support"


def test_defensive_full_hp_no_action() -> None:
    ice = make_ice("defensive", hp=100, max_hp=100)
    assert not should_defensive_act(ice)


def test_stealth_alarm_is_halved() -> None:
    ice = make_ice("stealth")
    mult = get_alarm_multiplier(ice)
    assert mult == 0.5


def test_aggressive_crit_bonus_personal() -> None:
    ice = make_ice("aggressive")
    assert get_crit_bonus(ice) > 0
    ice_default = make_ice("defensive")
    assert get_crit_bonus(ice_default) == 0.0
