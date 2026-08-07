"""Tests for Status Effects System (ADR-0160)."""

from __future__ import annotations

import random

from roguelike_sprawl.combat.state import Combatant, CombatState, Skill, SkillEffect
from roguelike_sprawl.combat.state_models import StatusEffect
from roguelike_sprawl.combat.status_effects import (
    apply_silence,
    apply_slow,
    apply_vulnerable,
    get_slow_multiplier,
    get_vulnerability_multiplier,
    is_silenced,
)


def make_player(hp: int = 100, max_ap: int = 5) -> Combatant:
    return Combatant(
        id="p",
        name="player",
        portrait="@",
        color=(255, 255, 255),
        team="player",
        hp=hp,
        max_hp=hp,
        ap=max_ap,
        max_ap=max_ap,
    )


def make_state(hp: int = 100) -> CombatState:
    rng = random.Random(42)
    state = CombatState(
        player=make_player(hp=hp),
        enemies=(),
        rng=rng,
    )
    return state


def test_apply_slow_adds_status() -> None:
    state = make_state()
    target = state.player
    apply_slow(state, target, slow_pct=30, duration_ms=3000)
    assert len(target.statuses) == 1
    assert target.statuses[0].effect_id == "slow"
    assert target.statuses[0].slow_pct == 30
    assert target.statuses[0].remaining_ms == 3000


def test_apply_silence_marks_is_silenced() -> None:
    state = make_state()
    target = state.player
    apply_silence(state, target, duration_ms=2000)
    assert is_silenced(target)
    assert target.statuses[0].effect_id == "silence"


def test_apply_vulnerable_adds_status() -> None:
    state = make_state()
    target = state.player
    apply_vulnerable(state, target, vuln_pct=20, duration_ms=4000)
    assert len(target.statuses) == 1
    assert target.statuses[0].effect_id == "vulnerable"
    assert target.statuses[0].vulnerability_pct == 20


def test_get_slow_multiplier_no_slow() -> None:
    state = make_state()
    assert get_slow_multiplier(state.player) == 1.0


def test_get_slow_multiplier_single_30_pct() -> None:
    state = make_state()
    apply_slow(state, state.player, slow_pct=30, duration_ms=1000)
    assert abs(get_slow_multiplier(state.player) - 0.7) < 0.001


def test_get_slow_multiplier_composes() -> None:
    state = make_state()
    apply_slow(state, state.player, slow_pct=30, duration_ms=1000)
    apply_slow(state, state.player, slow_pct=20, duration_ms=1000)
    mult = get_slow_multiplier(state.player)
    assert abs(mult - 0.7 * 0.8) < 0.001


def test_get_vulnerability_multiplier_no_vuln() -> None:
    state = make_state()
    assert get_vulnerability_multiplier(state.player) == 1.0


def test_get_vulnerability_multiplier_single_20_pct() -> None:
    state = make_state()
    apply_vulnerable(state, state.player, vuln_pct=20, duration_ms=1000)
    assert abs(get_vulnerability_multiplier(state.player) - 1.2) < 0.001


def test_get_vulnerability_multiplier_composes() -> None:
    state = make_state()
    apply_vulnerable(state, state.player, vuln_pct=20, duration_ms=1000)
    apply_vulnerable(state, state.player, vuln_pct=10, duration_ms=1000)
    mult = get_vulnerability_multiplier(state.player)
    assert abs(mult - 1.2 * 1.1) < 0.001


def test_is_silenced_no_silence() -> None:
    state = make_state()
    assert not is_silenced(state.player)


def test_is_silenced_after_silence() -> None:
    state = make_state()
    apply_silence(state, state.player, duration_ms=1000)
    assert is_silenced(state.player)


def test_is_silenced_returns_true_when_silence_status_expires() -> None:
    state = make_state()
    status = StatusEffect(
        effect_id="silence",
        remaining_ms=0,
        is_silenced=True,
    )
    state.player.statuses.append(status)
    assert not is_silenced(state.player)


def test_silence_blocks_use_skill() -> None:
    from roguelike_sprawl.combat.state import use_skill

    state = make_state()
    state.player.skills = [
        Skill(
            id="probe",
            name="Probe",
            tier=1,
            effect=SkillEffect.DETECT,
            ap_cost=1,
            effect_color=(255, 255, 255),
            effect_glyph="?",
        )
    ]
    apply_silence(state, state.player, duration_ms=2000)
    assert use_skill(state, state.player.skills[0]) is False


def test_vulnerability_applies_to_damage() -> None:
    from roguelike_sprawl.combat.state import _calculate_damage

    base_damage = 20

    state1 = make_state()
    attacker1 = state1.player
    defender1 = Combatant(
        id="e1",
        name="ice1",
        portrait="X",
        color=(255, 0, 0),
        team="enemy",
        hp=100,
        max_hp=100,
        ap=1,
        max_ap=1,
    )
    dmg_normal, _ = _calculate_damage(state1, base_damage, attacker1, defender1)

    state2 = make_state()
    attacker2 = state2.player
    defender2 = Combatant(
        id="e2",
        name="ice2",
        portrait="X",
        color=(255, 0, 0),
        team="enemy",
        hp=100,
        max_hp=100,
        ap=1,
        max_ap=1,
    )
    apply_vulnerable(state2, defender2, vuln_pct=100, duration_ms=1000)
    dmg_higher, _ = _calculate_damage(state2, base_damage, attacker2, defender2)

    assert dmg_higher > dmg_normal


def test_slow_does_not_affect_damage_calc() -> None:
    from roguelike_sprawl.combat.state import _calculate_damage

    state = make_state()
    attacker = state.player
    defender = Combatant(
        id="e",
        name="ice",
        portrait="X",
        color=(255, 0, 0),
        team="enemy",
        hp=100,
        max_hp=100,
        ap=1,
        max_ap=1,
    )
    apply_slow(state, defender, slow_pct=80, duration_ms=1000)
    dmg_with_slow, _ = _calculate_damage(state, 20, attacker, defender)
    assert dmg_with_slow >= 1


def test_status_effect_decays_in_tick() -> None:
    from roguelike_sprawl.combat.state_transitions import _tick_status_effects

    state = make_state()
    apply_slow(state, state.player, slow_pct=30, duration_ms=100)
    assert len(state.player.statuses) == 1
    state.tick_ms = 100
    _ = _tick_status_effects(state, state.player)
    assert len(state.player.statuses) == 0


def test_silence_does_not_silenced_when_silence_field_false() -> None:
    state = make_state()
    state.player.statuses.append(
        StatusEffect(
            effect_id="silence",
            remaining_ms=1000,
            is_silenced=False,
        )
    )
    assert not is_silenced(state.player)


def test_vulnerability_with_zero_pct_is_neutral() -> None:
    state = make_state()
    apply_vulnerable(state, state.player, vuln_pct=0, duration_ms=1000)
    assert get_vulnerability_multiplier(state.player) == 1.0


def test_slow_with_zero_pct_is_neutral() -> None:
    state = make_state()
    apply_slow(state, state.player, slow_pct=0, duration_ms=1000)
    assert get_slow_multiplier(state.player) == 1.0
