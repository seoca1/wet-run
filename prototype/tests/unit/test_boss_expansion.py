"""Tests for Boss Expansion (ADR-0180)."""

from __future__ import annotations

import dataclasses

import pytest

from roguelike_sprawl.combat.boss_expansion import (
    BLACK_BARON_PROFILE,
    BOSS_EXPANSION_REGISTRY,
    LOA_BARON_PROFILE,
    NEUROMANCER_PROFILE,
    BossProfile,
    boss_exists,
    get_all_bosses,
    get_boss_by_tier,
    get_boss_count,
    get_boss_ids,
    get_boss_max_hp,
    get_boss_phase_count,
    get_boss_profile,
)


def test_registry_has_3_bosses() -> None:
    assert get_boss_count() == 3


def test_get_boss_profile_existing() -> None:
    boss = get_boss_profile("neuromancer")
    assert boss is not None
    assert boss.name == "Neuromancer"


def test_get_boss_profile_nonexistent() -> None:
    assert get_boss_profile("nonexistent") is None


def test_get_all_bosses() -> None:
    bosses = get_all_bosses()
    assert len(bosses) == 3
    assert all(isinstance(b, BossProfile) for b in bosses)


def test_get_boss_by_tier() -> None:
    for tier in range(3, 6):
        boss = get_boss_by_tier(tier)
        assert boss is not None
        assert boss.tier == tier


def test_get_boss_by_tier_nonexistent() -> None:
    assert get_boss_by_tier(99) is None


def test_get_boss_ids() -> None:
    ids = get_boss_ids()
    assert "neuromancer" in ids
    assert "loa_baron" in ids
    assert "black_baron" in ids


def test_boss_exists() -> None:
    assert boss_exists("neuromancer")
    assert not boss_exists("nonexistent")


def test_get_boss_phase_count() -> None:
    assert get_boss_phase_count("neuromancer") == 6
    assert get_boss_phase_count("loa_baron") == 4
    assert get_boss_phase_count("black_baron") == 4


def test_get_boss_phase_count_nonexistent() -> None:
    assert get_boss_phase_count("nonexistent") == 0


def test_get_boss_max_hp() -> None:
    assert get_boss_max_hp("neuromancer") == 400
    assert get_boss_max_hp("loa_baron") == 300
    assert get_boss_max_hp("black_baron") == 250
    assert get_boss_max_hp("nonexistent") == 0


def test_boss_immutable() -> None:
    boss = get_boss_profile("neuromancer")
    assert boss is not None
    try:
        boss.name = "Modified"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_phase_immutable() -> None:
    boss = get_boss_profile("neuromancer")
    assert boss is not None
    phase = boss.phases[0]
    try:
        phase.damage_multiplier = 99.0  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_boss_phases_are_sorted_by_threshold() -> None:
    for boss in get_all_bosses():
        thresholds = [p.hp_threshold for p in boss.phases]
        assert thresholds == sorted(thresholds, reverse=True)


def test_boss_phase_damage_multiplier_increases() -> None:
    for boss in get_all_bosses():
        for i in range(len(boss.phases) - 1):
            assert boss.phases[i].damage_multiplier <= boss.phases[i + 1].damage_multiplier


def test_all_bosses_have_descriptions() -> None:
    for boss in get_all_bosses():
        assert boss.description != ""


def test_total_bosses_match_registry() -> None:
    assert get_boss_count() == len(BOSS_EXPANSION_REGISTRY)
    assert get_boss_count() == len(get_all_bosses())


def test_neuromancer_is_highest_tier() -> None:
    neuromancer = get_boss_profile("neuromancer")
    assert neuromancer is not None
    assert neuromancer.tier == 5
    assert neuromancer.hp_base == 400


def test_tier_progression() -> None:
    tiers = [b.tier for b in get_all_bosses()]
    assert sorted(tiers) == [3, 4, 5]


def test_all_boss_have_color() -> None:
    for boss in get_all_bosses():
        for phase in boss.phases:
            assert len(phase.color) == 3
            assert all(0 <= c <= 255 for c in phase.color)


def test_build_boss_combatant_neuromancer() -> None:
    from roguelike_sprawl.combat.boss_expansion import build_boss_combatant

    c = build_boss_combatant(NEUROMANCER_PROFILE)
    assert c.id == "neuromancer"
    assert c.name == "Neuromancer"
    assert c.hp == 400
    assert c.max_hp == 400
    assert c.auto_attack_damage == 18
    assert c.team == "enemy"
    assert c.ice_kind == "boss_neuromancer"


def test_build_boss_combatant_loa_baron() -> None:
    from roguelike_sprawl.combat.boss_expansion import build_boss_combatant

    c = build_boss_combatant(LOA_BARON_PROFILE)
    assert c.id == "loa_baron"
    assert c.hp == 300
    assert c.auto_attack_damage == 14
    assert c.ice_kind == "boss_loa_baron"


def test_build_boss_combatant_black_baron() -> None:
    from roguelike_sprawl.combat.boss_expansion import build_boss_combatant

    c = build_boss_combatant(BLACK_BARON_PROFILE)
    assert c.id == "black_baron"
    assert c.hp == 250
    assert c.auto_attack_damage == 12
    assert c.ice_kind == "boss_black_baron"


def test_build_boss_combatant_grade_scaling() -> None:
    from roguelike_sprawl.combat.boss_expansion import build_boss_combatant

    c_grade_1 = build_boss_combatant(NEUROMANCER_PROFILE, player_grade=1)
    c_grade_5 = build_boss_combatant(NEUROMANCER_PROFILE, player_grade=5)
    assert c_grade_5.hp > c_grade_1.hp
    assert c_grade_5.auto_attack_damage > c_grade_1.auto_attack_damage


def test_build_boss_combatant_no_grade() -> None:
    from roguelike_sprawl.combat.boss_expansion import build_boss_combatant

    c = build_boss_combatant(NEUROMANCER_PROFILE)
    assert c.hp == 400
    assert c.auto_attack_damage == 18


def test_build_boss_combatant_all_three_bosses() -> None:
    from roguelike_sprawl.combat.boss_expansion import BOSS_EXPANSION_REGISTRY, build_boss_combatant

    for boss_id, profile in BOSS_EXPANSION_REGISTRY.items():
        c = build_boss_combatant(profile)
        assert c.id == boss_id
        assert c.hp > 0
        assert c.auto_attack_damage > 0
        assert c.team == "enemy"
