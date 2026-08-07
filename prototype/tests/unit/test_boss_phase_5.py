"""Tests for Boss Phase 5 Last Stand (ADR-0162)."""

from __future__ import annotations

from roguelike_sprawl.combat.boss import BOSS_PROFILES
from roguelike_sprawl.combat.bosses import BossPhase, should_trigger_phase_5
from roguelike_sprawl.combat.bosses_cinematic import (
    boss_phase_5_sequence,
    spawn_boss_phase5,
)
from roguelike_sprawl.combat.effects import CombatEffects
from roguelike_sprawl.combat.state import Combatant


def make_boss(hp: int = 100, max_hp: int = 1000) -> Combatant:
    return Combatant(
        id="boss",
        name="TestBoss",
        portrait="B",
        color=(255, 0, 0),
        team="enemy",
        hp=hp,
        max_hp=max_hp,
        ap=5,
        max_ap=5,
    )


def test_should_trigger_phase_5_low_hp_phase_4() -> None:
    boss = make_boss(hp=50, max_hp=1000)
    phase = BossPhase(
        index=4,
        name="Last Stand",
        hp_threshold_pct=10,
        phase5_super_skill="super",
        phase5_dialogue="test",
    )
    assert should_trigger_phase_5(boss, phase)


def test_should_not_trigger_phase_5_high_hp_phase_4() -> None:
    boss = make_boss(hp=500, max_hp=1000)
    phase = BossPhase(
        index=4,
        name="Last Stand",
        hp_threshold_pct=10,
        phase5_super_skill="super",
        phase5_dialogue="test",
    )
    assert not should_trigger_phase_5(boss, phase)


def test_should_not_trigger_phase_5_phase_3() -> None:
    boss = make_boss(hp=50, max_hp=1000)
    phase = BossPhase(
        index=3,
        name="Phase 3",
        hp_threshold_pct=33,
        phase5_super_skill="super",
        phase5_dialogue="test",
    )
    assert not should_trigger_phase_5(boss, phase)


def test_should_not_trigger_phase_5_no_super_skill() -> None:
    boss = make_boss(hp=50, max_hp=1000)
    phase = BossPhase(
        index=4,
        name="Last Stand",
        hp_threshold_pct=10,
        phase5_super_skill=None,
        phase5_dialogue="test",
    )
    assert not should_trigger_phase_5(boss, phase)


def test_wintermute_profile_has_phase_5() -> None:
    from roguelike_sprawl.combat.effects import IceType

    profile = BOSS_PROFILES[IceType.WINTERMUTE]
    assert profile.max_phases >= 4
    phase_4 = profile.phases[3]
    assert phase_4.phase5_super_skill is not None
    assert phase_4.phase5_dialogue != ""


def test_ta_construct_profile_has_phase_5() -> None:
    from roguelike_sprawl.combat.effects import IceType

    profile = BOSS_PROFILES[IceType.TA_CONSTRUCT_PRIME]
    assert profile.max_phases >= 4
    phase_4 = profile.phases[3]
    assert phase_4.phase5_super_skill is not None
    assert phase_4.phase5_dialogue != ""


def test_phase_5_super_skill_is_heavy() -> None:
    from roguelike_sprawl.combat.effects import IceType

    profile = BOSS_PROFILES[IceType.WINTERMUTE]
    phase_4 = profile.phases[3]
    skill = phase_4.phase5_super_skill
    assert skill is not None
    assert hasattr(skill, "damage")
    assert skill.damage >= 30


def test_phase_5_damage_multiplier_at_least_3() -> None:
    from roguelike_sprawl.combat.effects import IceType

    for profile in [BOSS_PROFILES[IceType.WINTERMUTE], BOSS_PROFILES[IceType.TA_CONSTRUCT_PRIME]]:
        phase_4 = profile.phases[3]
        assert phase_4.phase5_damage_multiplier >= 3.0


def test_boss_phase_5_sequence_includes_dialogue() -> None:
    from roguelike_sprawl.combat.effects import IceType

    profile = BOSS_PROFILES[IceType.WINTERMUTE]
    phase_4 = profile.phases[3]
    seq = boss_phase_5_sequence(profile, phase_4)
    assert seq.name.startswith("boss_phase5_")
    all_text = " ".join(p[0] for p in seq.phases)
    assert phase_4.phase5_dialogue in all_text


def test_boss_phase_5_sequence_includes_super_skill_name() -> None:
    from roguelike_sprawl.combat.effects import IceType

    profile = BOSS_PROFILES[IceType.TA_CONSTRUCT_PRIME]
    phase_4 = profile.phases[3]
    seq = boss_phase_5_sequence(profile, phase_4)
    all_text = " ".join(p[0] for p in seq.phases)
    skill = phase_4.phase5_super_skill
    assert skill is not None
    assert skill.name in all_text


def test_spawn_boss_phase5_sets_cinematic() -> None:
    from roguelike_sprawl.combat.effects import IceType

    profile = BOSS_PROFILES[IceType.WINTERMUTE]
    phase_4 = profile.phases[3]
    fx = CombatEffects()
    spawn_boss_phase5(fx, profile, phase_4)
    assert fx.cinematic is not None
    assert fx.shake.intensity > 0
    assert fx.slow_motion_ms > 0


def test_boss_phase_5_super_skill_id_unique() -> None:
    from roguelike_sprawl.combat.effects import IceType

    wm = BOSS_PROFILES[IceType.WINTERMUTE].phases[3].phase5_super_skill
    ta = BOSS_PROFILES[IceType.TA_CONSTRUCT_PRIME].phases[3].phase5_super_skill
    assert wm is not None
    assert ta is not None
    assert wm.id != ta.id
