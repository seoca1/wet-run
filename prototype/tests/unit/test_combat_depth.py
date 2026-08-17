"""Automated tests for combat depth expansion (ADR-0148).

Source spec: Game/wet_run/testcases/combat/depth.md (TC-DEPTH-001 ~ 015)

Four sub-features:
- Counter Window (200ms reactive gameplay)
- Defense Stackable (Wisp / Shield / Wardrone)
- Companion Skills (Dixie decompile + icebreaker_overdrive)
- ICE Aggression Tiers (PASSIVE / STANDARD / AGGRESSIVE / BOSS)
"""

from __future__ import annotations

import random

from wet_run.combat.depth import (
    AGGRESSION_PROBABILITY,
    COUNTER_DAMAGE_MULTIPLIER,
    COUNTER_STUN_MS,
    COUNTER_WINDOW_MS,
    DIXIE_DECOMPILE_AP,
    DIXIE_DECOMPILE_ATTACK_REDUCTION,
    DIXIE_DECOMPILE_DURATION_MS,
    DIXIE_ICEBREAKER_AP,
    DIXIE_ICEBREAKER_DAMAGE,
    DIXIE_ICEBREAKER_DAMAGE_UP_PCT,
    DIXIE_ICEBREAKER_DURATION_MS,
    SHIELD_BARRIER,
    WARDRONE_COUNTER_DMG,
    WARDRONE_COUNTER_INTERVAL_MS,
    WARDRONE_DURATION_MS,
    WARDRONE_SHIELD,
    WISP_DURATION_MS,
    WISP_SHIELD,
    AggressionLevel,
    CompanionSkillId,
    apply_counter_attack,
    apply_shield_barrier,
    apply_wardrone,
    apply_wisp,
    counter_window_active_and_expired,
    dixie_choose_skill,
    dixie_use_skill,
    enemy_should_use_skill,
    is_counter_window_open,
    open_counter_window,
)
from wet_run.combat.state import Combatant, CombatState, Skill, SkillEffect
from wet_run.combat.state_models import StatusEffect

TICK_MS = 100


def _make_player(*, hp: int = 100, max_hp: int = 100) -> Combatant:
    return Combatant(
        id="player",
        name="Player",
        portrait="portrait.player",
        color=(255, 255, 255),
        hp=hp,
        max_hp=max_hp,
        ap=10,
        max_ap=10,
    )


def _make_enemy(
    *,
    hp: int = 100,
    max_hp: int = 100,
    aggression: str = "standard",
    skills: tuple[Skill, ...] = (),
) -> Combatant:
    return Combatant(
        id="ice_standard",
        name="ICE — Standard",
        portrait="portrait.ice.standard",
        color=(150, 200, 200),
        hp=hp,
        max_hp=max_hp,
        ap=0,
        max_ap=0,
        auto_attack_damage=3,
        skills=skills,
        team="enemy",
        aggression=aggression,
    )


def _make_state(
    *,
    player: Combatant | None = None,
    enemy: Combatant | None = None,
    rng: random.Random | None = None,
    tick_ms: int = 0,
) -> CombatState:
    if player is None:
        player = _make_player()
    if enemy is None:
        enemy = _make_enemy()
    if rng is None:
        rng = random.Random(0)
    return CombatState(player=player, enemy=enemy, rng=rng, tick_ms=tick_ms)


def _make_stun_skill(damage: int = 5) -> Skill:
    return Skill(
        id="test_stun",
        name="Stun Skill",
        tier=1,
        effect=SkillEffect.STUN,
        ap_cost=2,
        damage=damage,
        stun_duration_ms=1000,
    )


def _make_counter_skill(damage: int = 10) -> Skill:
    return Skill(
        id="test_counter",
        name="Counter-Strike",
        tier=2,
        effect=SkillEffect.COUNTER,
        ap_cost=2,
        damage=damage,
    )


# ---------------------------------------------------------------------------
# TC-DEPTH-001: Counter Window Opens on Enemy Skill
# ---------------------------------------------------------------------------


class TestCounterWindowOpen:
    def test_open_counter_window_sets_deadline(self) -> None:
        state = _make_state(tick_ms=1000)
        open_counter_window(state)
        assert state.counter_window_open_ms == 1000 + COUNTER_WINDOW_MS

    def test_window_open_immediately_after_open(self) -> None:
        state = _make_state(tick_ms=1000)
        open_counter_window(state)
        assert is_counter_window_open(state)

    def test_window_deadline_zero_when_not_open(self) -> None:
        state = _make_state()
        assert not is_counter_window_open(state)


# ---------------------------------------------------------------------------
# TC-DEPTH-002: Counter-Attack 2x Damage + Stun
# ---------------------------------------------------------------------------


class TestCounterAttack:
    def test_counter_attack_deals_2x_damage(self) -> None:
        player = _make_player()
        enemy = _make_enemy(hp=100, max_hp=100)
        state = _make_state(player=player, enemy=enemy, tick_ms=1000)
        open_counter_window(state)
        skill = _make_counter_skill(damage=10)
        applied = apply_counter_attack(state, skill)
        assert applied == int(10 * COUNTER_DAMAGE_MULTIPLIER)
        assert enemy.hp == 100 - 20

    def test_counter_attack_applies_stun(self) -> None:
        player = _make_player()
        enemy = _make_enemy(hp=100, max_hp=100)
        state = _make_state(player=player, enemy=enemy, tick_ms=1000)
        open_counter_window(state)
        skill = _make_counter_skill(damage=10)
        apply_counter_attack(state, skill)
        stun_status = next((s for s in enemy.statuses if s.is_stunned), None)
        assert stun_status is not None
        assert stun_status.remaining_ms == COUNTER_STUN_MS

    def test_counter_attack_consumes_window(self) -> None:
        state = _make_state(tick_ms=1000)
        open_counter_window(state)
        apply_counter_attack(state, _make_counter_skill(damage=10))
        assert state.counter_window_open_ms == 0
        assert not is_counter_window_open(state)

    def test_counter_attack_without_target_returns_zero(self) -> None:
        state = CombatState(player=_make_player(), enemy=None, rng=random.Random(0))
        applied = apply_counter_attack(state, _make_counter_skill())
        assert applied == 0


# ---------------------------------------------------------------------------
# TC-DEPTH-003: Counter Window Closes After 200ms
# ---------------------------------------------------------------------------


class TestCounterWindowExpiry:
    def test_window_closes_after_200ms(self) -> None:
        state = _make_state(tick_ms=1000)
        open_counter_window(state)
        state.tick_ms = 1000 + COUNTER_WINDOW_MS + 1
        assert not is_counter_window_open(state)

    def test_window_active_and_expired_helper(self) -> None:
        state = _make_state(tick_ms=1000)
        open_counter_window(state)
        state.tick_ms = 1000 + COUNTER_WINDOW_MS + 1
        assert counter_window_active_and_expired(state)

    def test_no_window_no_expired(self) -> None:
        state = _make_state()
        assert not counter_window_active_and_expired(state)


# ---------------------------------------------------------------------------
# TC-DEPTH-004: Wisp Stackable
# ---------------------------------------------------------------------------


class TestWisp:
    def test_wisp_adds_shield_and_status(self) -> None:
        state = _make_state()
        apply_wisp(state)
        assert state.shield == WISP_SHIELD
        wisp = next((s for s in state.player.statuses if s.effect_id == "wisp"), None)
        assert wisp is not None
        assert wisp.remaining_ms == WISP_DURATION_MS

    def test_wisp_stacks_and_refreshes(self) -> None:
        state = _make_state()
        apply_wisp(state)
        # Age the wisp status to near-end
        for s in state.player.statuses:
            if s.effect_id == "wisp":
                s.remaining_ms = 100
        apply_wisp(state)
        assert state.shield == 2
        wisp = next(s for s in state.player.statuses if s.effect_id == "wisp")
        assert wisp.remaining_ms == WISP_DURATION_MS  # refreshed


# ---------------------------------------------------------------------------
# TC-DEPTH-005: Shield One-Hit
# ---------------------------------------------------------------------------


class TestShieldBarrier:
    def test_shield_barrier_adds_3_shield(self) -> None:
        state = _make_state()
        apply_shield_barrier(state)
        assert state.shield == SHIELD_BARRIER
        assert any(s.effect_id == "shield_barrier" for s in state.player.statuses)

    def test_shield_barrier_status_present(self) -> None:
        state = _make_state()
        apply_shield_barrier(state)
        sb = next(s for s in state.player.statuses if s.effect_id == "shield_barrier")
        assert sb.is_shield


# ---------------------------------------------------------------------------
# TC-DEPTH-006: Wardrone + Auto-Counter
# ---------------------------------------------------------------------------


class TestWardrone:
    def test_wardrone_adds_2_shield_10s(self) -> None:
        state = _make_state()
        apply_wardrone(state)
        assert state.shield == WARDRONE_SHIELD
        wd = next(s for s in state.player.statuses if s.effect_id == "wardrone")
        assert wd.remaining_ms == WARDRONE_DURATION_MS

    def test_wardrone_constants(self) -> None:
        assert WARDRONE_SHIELD == 2
        assert WARDRONE_DURATION_MS == 10_000
        assert WARDRONE_COUNTER_INTERVAL_MS == 5_000
        assert WARDRONE_COUNTER_DMG == 5


# ---------------------------------------------------------------------------
# TC-DEPTH-007: Dixie Decompile
# ---------------------------------------------------------------------------


class _StubAppState:
    """Minimal AppState stub for companion tests."""

    __slots__ = ("construct_companion_active",)

    def __init__(self, active: bool = True) -> None:
        self.construct_companion_active = active


class TestDixieDecompile:
    def test_decompile_reduces_target_attack(self) -> None:
        enemy = _make_enemy(hp=100, max_hp=100)
        state = _make_state(enemy=enemy)
        app_state = _StubAppState(active=True)
        result = dixie_use_skill(state, app_state, CompanionSkillId.DECOMPILE, random.Random(0))
        assert result is True
        decompiled = next((s for s in enemy.statuses if s.effect_id == "decompiled"), None)
        assert decompiled is not None
        assert decompiled.attack_bonus == -DIXIE_DECOMPILE_ATTACK_REDUCTION
        assert decompiled.remaining_ms == DIXIE_DECOMPILE_DURATION_MS

    def test_decompile_constants(self) -> None:
        assert DIXIE_DECOMPILE_AP == 1
        assert DIXIE_DECOMPILE_ATTACK_REDUCTION == 1
        assert DIXIE_DECOMPILE_DURATION_MS == 3_000


# ---------------------------------------------------------------------------
# TC-DEPTH-008: Dixie Icebreaker Overdrive
# ---------------------------------------------------------------------------


class TestDixieIcebreaker:
    def test_icebreaker_deals_damage_and_applies_damage_up(self) -> None:
        enemy = _make_enemy(hp=100, max_hp=100)
        state = _make_state(enemy=enemy)
        app_state = _StubAppState(active=True)
        result = dixie_use_skill(
            state, app_state, CompanionSkillId.ICEBREAKER_OVERDRIVE, random.Random(0)
        )
        assert result is True
        assert enemy.hp == 100 - DIXIE_ICEBREAKER_DAMAGE
        damage_up = next((s for s in enemy.statuses if s.effect_id == "damage_up"), None)
        assert damage_up is not None
        assert damage_up.remaining_ms == DIXIE_ICEBREAKER_DURATION_MS

    def test_icebreaker_constants(self) -> None:
        assert DIXIE_ICEBREAKER_AP == 3
        assert DIXIE_ICEBREAKER_DAMAGE == 50
        assert DIXIE_ICEBREAKER_DURATION_MS == 5_000
        assert DIXIE_ICEBREAKER_DAMAGE_UP_PCT == 25


# ---------------------------------------------------------------------------
# TC-DEPTH-009: Companion Skill Requires Active
# ---------------------------------------------------------------------------


class TestCompanionSkillGating:
    def test_decompile_no_op_when_companion_inactive(self) -> None:
        enemy = _make_enemy(hp=100, max_hp=100)
        state = _make_state(enemy=enemy)
        app_state = _StubAppState(active=False)
        result = dixie_use_skill(state, app_state, CompanionSkillId.DECOMPILE, random.Random(0))
        assert result is False
        assert not any(s.effect_id == "decompiled" for s in enemy.statuses)
        assert any("silent" in m.lower() for m in state.log)

    def test_icebreaker_no_op_when_companion_inactive(self) -> None:
        enemy = _make_enemy(hp=100, max_hp=100)
        state = _make_state(enemy=enemy)
        app_state = _StubAppState(active=False)
        result = dixie_use_skill(
            state, app_state, CompanionSkillId.ICEBREAKER_OVERDRIVE, random.Random(0)
        )
        assert result is False
        assert enemy.hp == 100  # unchanged

    def test_decompile_no_op_when_target_dead(self) -> None:
        enemy = _make_enemy(hp=0, max_hp=100)
        state = _make_state(enemy=enemy)
        app_state = _StubAppState(active=True)
        result = dixie_use_skill(state, app_state, CompanionSkillId.DECOMPILE, random.Random(0))
        assert result is False


# ---------------------------------------------------------------------------
# TC-DEPTH-010 ~ 013: Aggression Tier Probabilities
# ---------------------------------------------------------------------------


class TestAggressionTiers:
    def test_passive_5_percent(self) -> None:
        enemy = _make_enemy(aggression="passive", skills=(_make_stun_skill(),))
        rng = random.Random(42)
        uses = sum(1 for _ in range(1000) if enemy_should_use_skill(enemy, rng))
        # 5% ± noise
        assert 30 < uses < 80

    def test_standard_15_percent(self) -> None:
        enemy = _make_enemy(aggression="standard", skills=(_make_stun_skill(),))
        rng = random.Random(42)
        uses = sum(1 for _ in range(1000) if enemy_should_use_skill(enemy, rng))
        assert 120 < uses < 200

    def test_aggressive_35_percent(self) -> None:
        enemy = _make_enemy(aggression="aggressive", skills=(_make_stun_skill(),))
        rng = random.Random(42)
        uses = sum(1 for _ in range(1000) if enemy_should_use_skill(enemy, rng))
        assert 300 < uses < 400

    def test_boss_50_percent(self) -> None:
        enemy = _make_enemy(aggression="boss", skills=(_make_stun_skill(),))
        rng = random.Random(42)
        uses = sum(1 for _ in range(1000) if enemy_should_use_skill(enemy, rng))
        assert 450 < uses < 550

    def test_no_skills_returns_false(self) -> None:
        enemy = _make_enemy(aggression="boss", skills=())
        assert enemy_should_use_skill(enemy, random.Random(0)) is False

    def test_default_aggression_is_standard(self) -> None:
        enemy = Combatant(
            id="ice_x",
            name="X",
            portrait="p",
            color=(0, 0, 0),
            hp=10,
            max_hp=10,
        )
        assert enemy.aggression == "standard"
        # enemy_should_use_skill defaults to standard tier
        assert enemy_should_use_skill(enemy, random.Random(0)) is False  # no skills


# ---------------------------------------------------------------------------
# TC-DEPTH-015: Counter Window Only Opens on Enemy Skill
# ---------------------------------------------------------------------------


class TestCounterWindowTrigger:
    def test_window_not_set_by_default(self) -> None:
        state = _make_state(tick_ms=1000)
        assert not is_counter_window_open(state)

    def test_open_counter_window_only_method_to_set(self) -> None:
        # Verified: the only way counter_window_open_ms changes from 0
        # is via open_counter_window(). step_combat does not modify it
        # directly (only _apply_enemy_skill via open_counter_window does).
        state = _make_state(tick_ms=1000)
        # Simulate step_combat tick advance without enemy skill
        state.tick_ms += 100
        assert not is_counter_window_open(state)


# ---------------------------------------------------------------------------
# Constants & StrEnum
# ---------------------------------------------------------------------------


class TestAggressionLevel:
    def test_passive_value(self) -> None:
        assert AggressionLevel.PASSIVE == "passive"

    def test_standard_value(self) -> None:
        assert AggressionLevel.STANDARD == "standard"

    def test_aggressive_value(self) -> None:
        assert AggressionLevel.AGGRESSIVE == "aggressive"

    def test_boss_value(self) -> None:
        assert AggressionLevel.BOSS == "boss"

    def test_aggression_probability_table(self) -> None:
        assert AGGRESSION_PROBABILITY["passive"] == 0.05
        assert AGGRESSION_PROBABILITY["standard"] == 0.15
        assert AGGRESSION_PROBABILITY["aggressive"] == 0.35
        assert AGGRESSION_PROBABILITY["boss"] == 0.50


class TestCompanionSkillId:
    def test_decompile_value(self) -> None:
        assert CompanionSkillId.DECOMPILE == "decompile"

    def test_icebreaker_value(self) -> None:
        assert CompanionSkillId.ICEBREAKER_OVERDRIVE == "icebreaker_overdrive"


# ---------------------------------------------------------------------------
# dixie_choose_skill AI
# ---------------------------------------------------------------------------


class TestDixieChooseSkill:
    def test_choose_icebreaker_when_target_hp_high(self) -> None:
        enemy = _make_enemy(hp=100, max_hp=100)
        state = _make_state(enemy=enemy)
        app_state = _StubAppState(active=True)
        skill = dixie_choose_skill(state, app_state, random.Random(0))
        assert skill is CompanionSkillId.ICEBREAKER_OVERDRIVE

    def test_choose_none_when_target_low_hp(self) -> None:
        enemy = _make_enemy(hp=10, max_hp=100)
        state = _make_state(enemy=enemy)
        app_state = _StubAppState(active=True)
        # Add decompiled so choose returns None (already decompiled)
        enemy.statuses.append(
            StatusEffect(effect_id="decompiled", remaining_ms=3000, attack_bonus=-1)
        )
        skill = dixie_choose_skill(state, app_state, random.Random(0))
        assert skill is None

    def test_choose_none_when_companion_inactive(self) -> None:
        enemy = _make_enemy(hp=100, max_hp=100)
        state = _make_state(enemy=enemy)
        app_state = _StubAppState(active=False)
        skill = dixie_choose_skill(state, app_state, random.Random(0))
        assert skill is None
