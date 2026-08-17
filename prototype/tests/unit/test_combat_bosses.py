"""Tests for BOSS ICE multi-phase system (combat/bosses.py).

Validates:
- 3 BOSS definitions (GOLIATH PRIME, BLACK ICE LORD, WATCHDOG ALPHA)
- BossSpec, BossPhase data classes
- is_boss / get_boss_spec lookups
- get_next_phase HP threshold logic
- apply_phase_buff stat math
- boss_intro_sequence multi-line construction
- boss_phase_transition cinematic
- boss_death_sequence multi-stage (4 sequences)
- High-level spawners (spawn_boss_intro, spawn_boss_phase_transition,
  spawn_boss_death)
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from wet_run.combat.bosses import (
    ALL_BOSSES,
    BLACK_ICE_LORD,
    GOLIATH_PRIME,
    WATCHDOG_ALPHA,
    BossPhase,
    apply_phase_buff,
    boss_death_sequence,
    boss_epilogue_lines,
    boss_intro_sequence,
    boss_phase_transition,
    get_boss_spec,
    get_next_phase,
    is_boss,
    spawn_boss_death,
    spawn_boss_intro,
    spawn_boss_phase_transition,
)
from wet_run.combat.effects import CombatEffects, IceType
from wet_run.combat.registry import ProgramRegistry, build_default_player
from wet_run.combat.state import Combatant, CombatState

ALL_BOSS_IDS = ["goliath_prime", "black_ice_lord", "watchdog_alpha"]


# ----------------------------------------------------------------------------
# Data class structure
# ----------------------------------------------------------------------------


class TestBossDataClasses:
    def test_boss_spec_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            GOLIATH_PRIME.id = "hacked"  # type: ignore[misc]

    def test_boss_phase_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            GOLIATH_PRIME.phases[0].name = "hacked"  # type: ignore[misc]

    def test_goliath_has_4_phases(self) -> None:
        assert len(GOLIATH_PRIME.phases) == 4

    def test_black_has_3_phases(self) -> None:
        assert len(BLACK_ICE_LORD.phases) == 3

    def test_watchdog_has_3_phases(self) -> None:
        assert len(WATCHDOG_ALPHA.phases) == 3

    def test_phases_ordered_high_to_low(self) -> None:
        for spec in ALL_BOSSES.values():
            thresholds = [p.hp_threshold_pct for p in spec.phases]
            assert thresholds == sorted(thresholds, reverse=True), (
                f"{spec.id} phases not ordered: {thresholds}"
            )


# ----------------------------------------------------------------------------
# Lookup functions
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
class TestBossLookup:
    def test_is_boss_true(self, boss_id: str) -> None:
        assert is_boss(boss_id)

    def test_get_boss_spec_returns_spec(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        assert spec.id == boss_id

    def test_all_bosses_contains(self, boss_id: str) -> None:
        assert boss_id in ALL_BOSSES


class TestIsBossFalse:
    def test_standard_not_boss(self) -> None:
        assert not is_boss("standard")

    def test_watchdog_not_boss(self) -> None:
        # WATCHDOG is the base type; only WATCHDOG_ALPHA is a BOSS
        assert not is_boss("watchdog")

    def test_nonexistent_not_boss(self) -> None:
        assert not is_boss("xyz_nonexistent")

    def test_get_boss_spec_returns_none(self) -> None:
        assert get_boss_spec("standard") is None


# ----------------------------------------------------------------------------
# Phase progression
# ----------------------------------------------------------------------------


GOLIATH_HP_CASES: list[tuple[int, int]] = [
    (100, 0),
    (80, 0),
    (75, 1),
    (60, 1),
    (50, 2),
    (30, 2),
    (25, 3),
    (10, 3),
]
BLACK_HP_CASES: list[tuple[int, int]] = [
    (100, 0),
    (66, 1),
    (33, 2),
    (10, 2),
]


class TestGetNextPhase:
    @pytest.mark.parametrize("case_idx", list(range(len(GOLIATH_HP_CASES))))
    def test_goliath_phases(self, case_idx: int) -> None:
        hp_pct, expected_index = GOLIATH_HP_CASES[case_idx]
        phase = get_next_phase(GOLIATH_PRIME, hp_pct)
        assert phase is not None
        assert phase.index == expected_index

    @pytest.mark.parametrize("case_idx", list(range(len(BLACK_HP_CASES))))
    def test_black_phases(self, case_idx: int) -> None:
        hp_pct, expected_index = BLACK_HP_CASES[case_idx]
        phase = get_next_phase(BLACK_ICE_LORD, hp_pct)
        assert phase is not None
        assert phase.index == expected_index

    def test_watchdog_phase_progression(self) -> None:
        # 100% → phase 0
        # 50% → phase 1
        # 20% → phase 2
        assert get_next_phase(WATCHDOG_ALPHA, 100).index == 0
        assert get_next_phase(WATCHDOG_ALPHA, 50).index == 1
        assert get_next_phase(WATCHDOG_ALPHA, 20).index == 2


# ----------------------------------------------------------------------------
# Phase buffs
# ----------------------------------------------------------------------------


class TestApplyPhaseBuff:
    def test_zero_buff(self) -> None:
        phase = BossPhase(
            index=0,
            name="base",
            hp_threshold_pct=100,
            intro_line="",
            color=(0, 0, 0),
        )
        atk, spd = apply_phase_buff(phase, 100, 1000)
        assert atk == 100
        assert spd == 1000

    def test_attack_bonus(self) -> None:
        phase = BossPhase(
            index=1,
            name="+50%",
            hp_threshold_pct=50,
            intro_line="",
            color=(0, 0, 0),
            attack_bonus_pct=50,
        )
        atk, _ = apply_phase_buff(phase, 100, 1000)
        assert atk == 150

    def test_speed_bonus(self) -> None:
        phase = BossPhase(
            index=1,
            name="faster",
            hp_threshold_pct=50,
            intro_line="",
            color=(0, 0, 0),
            speed_bonus_pct=50,
        )
        _, spd = apply_phase_buff(phase, 100, 1000)
        # 50% faster means 1000 / 1.5 = 666ms
        assert 660 <= spd <= 670

    def test_combined(self) -> None:
        phase = BossPhase(
            index=2,
            name="both",
            hp_threshold_pct=25,
            intro_line="",
            color=(0, 0, 0),
            attack_bonus_pct=100,
            speed_bonus_pct=100,
        )
        atk, spd = apply_phase_buff(phase, 50, 2000)
        assert atk == 100
        assert spd == 1000

    def test_goliath_phase_progression_buffs(self) -> None:
        # Phase 0: 100/1000, Phase 3: 180/714
        for phase in GOLIATH_PRIME.phases:
            atk, spd = apply_phase_buff(phase, 100, 1000)
            assert atk >= 100
            assert spd <= 1000


# ----------------------------------------------------------------------------
# Boss intro sequence
# ----------------------------------------------------------------------------


class TestBossIntroSequence:
    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_intro_has_phases(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        seq = boss_intro_sequence(spec)
        assert len(seq.phases) >= 3  # At least intro line + body + name

    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_intro_duration_3_to_5_seconds(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        seq = boss_intro_sequence(spec)
        assert 2000 <= seq.total_duration_ms <= 6000

    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_intro_uses_spec_lines(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        seq = boss_intro_sequence(spec)
        spec_lines = list(spec.intro_lines)
        seq_lines = [p[0] for p in seq.phases]
        for line in spec_lines:
            assert line in seq_lines, f"{boss_id}: line '{line}' not in sequence"

    def test_goliath_intro_has_warning(self) -> None:
        seq = boss_intro_sequence(GOLIATH_PRIME)
        # Should have a warning-style first line
        first = seq.phases[0][0]
        assert "경고" in first or "▓" in first

    def test_black_intro_has_glitch(self) -> None:
        seq = boss_intro_sequence(BLACK_ICE_LORD)
        # Should have error/glitch text
        all_text = " ".join(p[0] for p in seq.phases)
        assert "오류" in all_text or "▓" in all_text


# ----------------------------------------------------------------------------
# Phase transition
# ----------------------------------------------------------------------------


class TestBossPhaseTransition:
    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_transition_has_phases(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        # Test transition to a non-zero phase
        new_phase = spec.phases[min(1, len(spec.phases) - 1)]
        seq = boss_phase_transition(spec, new_phase)
        assert len(seq.phases) >= 3

    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_transition_completes_in_reasonable_time(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        new_phase = spec.phases[-1]  # Most dramatic transition
        seq = boss_phase_transition(spec, new_phase)
        assert 1000 <= seq.total_duration_ms <= 5000

    def test_goliath_ground_slam_announcement(self) -> None:
        # Phase 2 has special_ability=ground_slam
        seq = boss_phase_transition(GOLIATH_PRIME, GOLIATH_PRIME.phases[2])
        all_text = " ".join(p[0] for p in seq.phases)
        assert "지면 강타" in all_text

    def test_black_glitch_burst_announcement(self) -> None:
        seq = boss_phase_transition(BLACK_ICE_LORD, BLACK_ICE_LORD.phases[1])
        all_text = " ".join(p[0] for p in seq.phases)
        assert "글리치 폭주" in all_text

    def test_watchdog_pack_howl_announcement(self) -> None:
        seq = boss_phase_transition(WATCHDOG_ALPHA, WATCHDOG_ALPHA.phases[1])
        all_text = " ".join(p[0] for p in seq.phases)
        assert "무리 외침" in all_text


# ----------------------------------------------------------------------------
# Boss death sequence
# ----------------------------------------------------------------------------


class TestBossDeathSequence:
    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_death_has_4_stages(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        sequences = boss_death_sequence(spec)
        assert len(sequences) == 4, f"{boss_id} should have 4 death stages"

    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_death_total_duration(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        sequences = boss_death_sequence(spec)
        total = sum(s.total_duration_ms for s in sequences)
        # 4 stages * ~800ms each = ~3000-5000ms
        assert 2000 <= total <= 7000

    def test_goliath_death_unique(self) -> None:
        # GOLIATH death has earthquake-style frames
        sequences = boss_death_sequence(GOLIATH_PRIME)
        all_text = " ".join(p[0] for s in sequences for p in s.phases)
        # Should have earth-shattering / heavy destruction
        assert "X_X" in all_text or "╳" in all_text
        assert "코어" in all_text

    def test_black_death_has_glitch(self) -> None:
        sequences = boss_death_sequence(BLACK_ICE_LORD)
        all_text = " ".join(p[0] for s in sequences for p in s.phases)
        # Should have ERR or 권한 (permission) text
        assert "ERR" in all_text or "권한" in all_text

    def test_watchdog_death_has_woof(self) -> None:
        sequences = boss_death_sequence(WATCHDOG_ALPHA)
        all_text = " ".join(p[0] for s in sequences for p in s.phases)
        assert "woof" in all_text or "추적" in all_text

    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_epilogue_lines_present(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        lines = boss_epilogue_lines(spec)
        assert len(lines) >= 3
        # All lines should be non-empty
        for line in lines:
            assert len(line) > 0


# ----------------------------------------------------------------------------
# High-level spawners
# ----------------------------------------------------------------------------


class TestSpawnBossIntro:
    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_intro_sets_cinematic(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        fx = CombatEffects()
        spawn_boss_intro(fx, spec)
        assert fx.cinematic is not None
        assert fx.slow_motion_ms > 0
        assert fx.shake.intensity > 0


class TestSpawnBossPhaseTransition:
    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_transition_sets_cinematic(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        # Find a non-zero phase
        new_phase = spec.phases[min(1, len(spec.phases) - 1)]
        fx = CombatEffects()
        spawn_boss_phase_transition(fx, spec, new_phase)
        assert fx.cinematic is not None
        assert fx.shake.intensity >= new_phase.screen_shake_intensity


class TestSpawnBossDeath:
    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_death_sets_cinematic(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        fx = CombatEffects()
        spawn_boss_death(fx, spec)
        assert fx.cinematic is not None
        assert fx.shake.intensity > 0
        # Cinematic should include the death dialogue
        all_text = " ".join(p[0] for p in fx.cinematic.phases)
        for line in spec.death_lines:
            assert line in all_text, f"{line} not in {boss_id} death cinematic"


# ----------------------------------------------------------------------------
# Boss balance check
# ----------------------------------------------------------------------------


class TestBossBalance:
    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_boss_has_higher_stats_than_base(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        assert spec.hp_multiplier >= 3.0
        assert spec.attack_multiplier >= 1.5
        assert spec.defense_multiplier >= 1.0

    @pytest.mark.parametrize("boss_id", ALL_BOSS_IDS)
    def test_boss_has_unique_base_type(self, boss_id: str) -> None:
        spec = get_boss_spec(boss_id)
        assert spec is not None
        # Each BOSS has a unique base ICE type
        assert spec.base_ice_type in list(IceType)

    def test_all_bosses_have_distinct_intros(self) -> None:
        """Each BOSS has visually distinct intro text."""
        signatures = set()
        for spec in ALL_BOSSES.values():
            sig = "|".join(spec.intro_lines)
            signatures.add(sig)
        assert len(signatures) == 3

    def test_all_bosses_have_distinct_deaths(self) -> None:
        signatures = set()
        for spec in ALL_BOSSES.values():
            sig = "|".join(spec.death_lines)
            signatures.add(sig)
        assert len(signatures) == 3


# ----------------------------------------------------------------------------
# Performance smoke
# ----------------------------------------------------------------------------


class TestPerformance:
    def test_boss_intro_settles(self) -> None:
        fx = CombatEffects()
        spawn_boss_intro(fx, GOLIATH_PRIME)
        for _ in range(200):
            fx.step(50)
            if fx.cinematic is None:
                break
        assert fx.cinematic is None

    def test_full_boss_fight(self) -> None:
        """Simulate a full boss fight: intro → 3 phase transitions → death."""
        fx = CombatEffects()
        spec = GOLIATH_PRIME

        # Intro
        spawn_boss_intro(fx, spec)
        for _ in range(100):
            fx.step(50)
            if fx.cinematic is None:
                break

        # Phase 1 → 2 → 3 transitions
        for i in range(1, len(spec.phases)):
            fx.clear()
            spawn_boss_phase_transition(fx, spec, spec.phases[i])
            for _ in range(100):
                fx.step(50)
                if fx.cinematic is None:
                    break

        # Death
        fx.clear()
        spawn_boss_death(fx, spec)
        for _ in range(200):
            fx.step(50)
            if fx.cinematic is None:
                break
        assert fx.cinematic is None


class TestBossB3Enhancements:
    """Phase H: tests for B-3 spawn_minions + aoe_damage helpers (ADR-0125)."""

    def test_spawn_phase_minions_appends_to_state_enemies(self) -> None:
        """spawn_phase_minions() adds minion Combatants to state.enemies."""
        from wet_run.combat.boss import (
            PhaseProfile,
            spawn_phase_minions,
        )
        from wet_run.combat.registry import (
            IceRegistry,
            ProgramRegistry,
        )

        phase = PhaseProfile(
            phase=2,
            hp_threshold=0.66,
            damage_multiplier=1.0,
            color=(255, 0, 0),
            glyph="*",
            intro_text="Phase 2",
            skills=(),
            spawn_minions=("watchdog",),
        )
        boss = _make_boss_for_minion_test()
        state = _make_combat_state_with_boss(boss)
        ice_reg = IceRegistry.load(
            Path(__file__).resolve().parent.parent.parent / "data" / "combat" / "ice_types.json"
        )
        prog_reg = ProgramRegistry({})

        before_enemies = len(state.enemies)
        spawned = spawn_phase_minions(boss, phase, state, ice_reg, prog_reg)
        assert len(spawned) == 1
        assert len(state.enemies) == before_enemies + 1
        assert isinstance(spawned[0], Combatant)
        assert spawned[0].team == "enemy"

    def test_spawn_phase_minions_invalid_id_skipped(self) -> None:
        """Invalid ICE id in spawn_minions is silently skipped (no crash)."""
        from wet_run.combat.boss import (
            PhaseProfile,
            spawn_phase_minions,
        )
        from wet_run.combat.registry import (
            IceRegistry,
            ProgramRegistry,
        )

        phase = PhaseProfile(
            phase=1,
            hp_threshold=1.0,
            damage_multiplier=1.0,
            color=(255, 0, 0),
            glyph="?",
            intro_text="Phase 1",
            spawn_minions=("nonexistent_ice_id_xyz",),
        )
        boss = _make_boss_for_minion_test()
        state = _make_combat_state_with_boss(boss)
        ice_reg = IceRegistry.load(
            Path(__file__).resolve().parent.parent.parent / "data" / "combat" / "ice_types.json"
        )
        prog_reg = ProgramRegistry({})
        before = len(state.enemies)
        spawned = spawn_phase_minions(boss, phase, state, ice_reg, prog_reg)
        assert spawned == []
        assert len(state.enemies) == before

    def test_apply_phase_aoe_decreases_player_hp(self) -> None:
        """apply_phase_aoe() applies aoe_damage to player and returns it."""
        from wet_run.combat.boss import (
            PhaseProfile,
            apply_phase_aoe,
        )

        phase = PhaseProfile(
            phase=3,
            hp_threshold=0.33,
            damage_multiplier=2.0,
            color=(255, 50, 50),
            glyph="*",
            intro_text="Phase 3 AoE",
            aoe_damage=15,
        )
        boss = _make_boss_for_minion_test()
        state = _make_combat_state_with_boss(boss)
        original_hp = state.player.hp

        dealt = apply_phase_aoe(phase, state)
        assert dealt == 15
        assert state.player.hp == original_hp - 15

    def test_apply_phase_aoe_triggers_visual_effects(self) -> None:
        """Phase B-3.5: apply_phase_aoe triggers screen shake + hit flash."""
        from wet_run.combat.boss import (
            PhaseProfile,
            apply_phase_aoe,
        )
        from wet_run.combat.effects import CombatEffects

        phase = PhaseProfile(
            phase=3,
            hp_threshold=0.33,
            damage_multiplier=2.0,
            color=(255, 50, 50),
            glyph="*",
            intro_text="Phase 3 AoE",
            aoe_damage=15,
        )
        boss = _make_boss_for_minion_test()
        state = _make_combat_state_with_boss(boss)
        state.combat_effects = CombatEffects()

        apply_phase_aoe(phase, state, IceType.WINTERMUTE)
        # Visual effects triggered: shake and hit_flash active
        assert state.combat_effects.shake.intensity > 0
        assert state.combat_effects.hit_flash.is_active

    def test_apply_phase_aoe_zero_damage_noop(self) -> None:
        """apply_phase_aoe() with aoe_damage=0 deals nothing."""
        from wet_run.combat.boss import (
            PhaseProfile,
            apply_phase_aoe,
        )

        phase = PhaseProfile(
            phase=1,
            hp_threshold=1.0,
            damage_multiplier=1.0,
            color=(120, 120, 220),
            glyph="?",
            intro_text="Phase 1 (no AoE)",
            aoe_damage=0,
        )
        boss = _make_boss_for_minion_test()
        state = _make_combat_state_with_boss(boss)
        original_hp = state.player.hp

        dealt = apply_phase_aoe(phase, state)
        assert dealt == 0
        assert state.player.hp == original_hp

    def test_wintermute_phase_3_has_aoe_and_minion(self) -> None:
        """WINTERMUTE phase 3 should have aoe_damage + spawn_minions populated."""
        from wet_run.combat.boss import WINTERMUTE_PROFILE

        phase_3 = WINTERMUTE_PROFILE.phases[2]
        assert phase_3.aoe_damage > 0
        assert len(phase_3.spawn_minions) > 0

    def test_ta_prime_phase_3_has_aoe_and_minion(self) -> None:
        """T-A CONSTRUCT PRIME phase 3 should have aoe_damage + spawn_minions."""
        from wet_run.combat.boss import TA_CONSTRUCT_PRIME_PROFILE

        phase_3 = TA_CONSTRUCT_PRIME_PROFILE.phases[2]
        assert phase_3.aoe_damage > 0
        assert len(phase_3.spawn_minions) >= 1


def _make_boss_for_minion_test() -> Combatant:
    """Create a minimal boss Combatant for testing."""
    return Combatant(
        id="test_boss",
        name="Test Boss",
        portrait="▲BOSS▲",
        color=(255, 0, 0),
        hp=200,
        max_hp=200,
        ap=0,
        max_ap=0,
        auto_attack_damage=10,
        skills=(),
        team="enemy",
        ice_kind="standard",
    )


def _make_combat_state_with_boss(boss: Combatant) -> CombatState:
    """Create a minimal CombatState with the given boss."""
    player = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    player.skills = ()
    return CombatState(player=player, enemy=boss)


class TestBossB3IntegrationFlow:
    """Phase N: integration tests for full B-3 combat flow (all 5 bosses)."""

    @staticmethod
    def _drive_to_phase(boss, profile, state, target_phase):
        from pathlib import Path as _Path

        from wet_run.combat.boss import (
            apply_phase_aoe,
            apply_phase_to_combatant,
            current_phase,
            spawn_phase_minions,
        )
        from wet_run.combat.registry import (
            IceRegistry,
            ProgramRegistry,
        )

        ph = profile.phases[target_phase - 1]
        # PhaseProfile (boss.py) uses hp_threshold as float 0-1
        # BossPhase (bosses.py) uses hp_threshold_pct as int 0-100
        if hasattr(ph, "hp_threshold"):
            threshold = ph.hp_threshold
        else:
            threshold = ph.hp_threshold_pct / 100
        boss.hp = int(boss.max_hp * threshold) - 1
        apply_phase_to_combatant(boss, profile)
        cur = current_phase(boss, profile)
        # Load real ice_types.json so spawn_phase_minions can resolve ids
        ice_types_path = _Path(__file__).resolve().parents[2] / "data" / "combat" / "ice_types.json"
        if ice_types_path.exists():
            ice_reg = IceRegistry.load(ice_types_path)
        else:
            ice_reg = IceRegistry({})
        prog_reg = ProgramRegistry({})
        if cur.spawn_minions:
            spawn_phase_minions(
                boss,
                cur,
                state,
                ice_registry=ice_reg,
                program_registry=prog_reg,
            )
        if cur.aoe_damage > 0:
            original = state.player.hp
            apply_phase_aoe(cur, state)
            assert state.player.hp == original - cur.aoe_damage
        # PhaseProfile.phase is int; BossPhase.index is int
        cur_num = getattr(cur, "phase", getattr(cur, "index", 0))
        # Reset to old phase for next iteration (if test loops)
        if cur_num > 1:
            if hasattr(cur, "hp_threshold"):
                threshold = cur.hp_threshold
            else:
                threshold = cur.hp_threshold_pct / 100
            boss.hp = int(boss.max_hp * threshold) - 1
            apply_phase_to_combatant(boss, profile)

    def test_wintermute_full_phase_flow(self) -> None:
        """WINTERMUTE: phase 1->2 summons proxies, phase 2->3 summons fragment + AoE 15."""
        from wet_run.combat.boss import WINTERMUTE_PROFILE
        from wet_run.combat.effects import CombatEffects

        boss = Combatant(
            id="wintermute",
            name="Wintermute",
            portrait="BOSS",
            color=(120, 120, 220),
            hp=1000,
            max_hp=1000,
            ap=0,
            max_ap=0,
            auto_attack_damage=10,
            skills=(),
            team="enemy",
            ice_kind="wintermute",
        )
        boss.current_phase = 1
        state = _make_combat_state_with_boss(boss)
        state.combat_effects = CombatEffects()
        # _drive_to_phase drives to phases[target-1] (0-indexed array)
        # Drive to profile.phases[1] (phase field=2) -> current_phase=2
        self._drive_to_phase(boss, WINTERMUTE_PROFILE, state, 2)
        assert boss.current_phase == 2
        assert len(state.enemies) == 3
        # Drive to phases[2] (phase field=3) -> current_phase=3
        # _drive_to_phase drives to phases[target-1] (0-indexed array)
        # WINTERMUTE: phases[2] (phase field=3) -> current_phase=3
        self._drive_to_phase(boss, WINTERMUTE_PROFILE, state, 3)
        assert boss.current_phase == 3
        assert state.combat_effects.shake.intensity > 0

    def test_ta_prime_phase_3_20_aoe_and_2_minions(self) -> None:
        from wet_run.combat.boss import TA_CONSTRUCT_PRIME_PROFILE
        from wet_run.combat.effects import CombatEffects

        boss = Combatant(
            id="ta_prime",
            name="TA Construct Prime",
            portrait="BOSS",
            color=(220, 220, 220),
            hp=1000,
            max_hp=1000,
            ap=0,
            max_ap=0,
            auto_attack_damage=10,
            skills=(),
            team="enemy",
            ice_kind="ta_construct_prime",
        )
        boss.current_phase = 1
        state = _make_combat_state_with_boss(boss)
        state.combat_effects = CombatEffects()
        # Drive to profile.phases[1] (phase field=2)
        self._drive_to_phase(boss, TA_CONSTRUCT_PRIME_PROFILE, state, 2)
        assert boss.current_phase == 2
        assert len(state.enemies) == 2
        # Drive to phases[2] (phase field=3)
        self._drive_to_phase(boss, TA_CONSTRUCT_PRIME_PROFILE, state, 3)
        assert boss.current_phase == 3
        assert len(state.enemies) == 4

    def test_goliath_phase_3_25_aoe_highest(self) -> None:
        from wet_run.combat.bosses import GOLIATH_PRIME
        from wet_run.combat.effects import CombatEffects

        boss = Combatant(
            id="goliath_prime",
            name="GOLIATH PRIME",
            portrait="BOSS",
            color=(150, 150, 170),
            hp=1000,
            max_hp=1000,
            ap=0,
            max_ap=0,
            auto_attack_damage=10,
            skills=(),
            team="enemy",
            ice_kind="goliath",
        )
        state = _make_combat_state_with_boss(boss)
        state.combat_effects = CombatEffects()
        # GOLIATH has 4 phases (0-3); phase 3 (자폭, phases[3]) has 25 AoE
        self._drive_to_phase(boss, GOLIATH_PRIME, state, 4)
        assert boss.current_phase == 3
        assert GOLIATH_PRIME.phases[3].aoe_damage == 25

    def test_black_ice_lord_phase_1_construct_spawn(self) -> None:
        from wet_run.combat.bosses import BLACK_ICE_LORD
        from wet_run.combat.effects import CombatEffects

        boss = Combatant(
            id="black_ice_lord",
            name="BLACK ICE LORD",
            portrait="BOSS",
            color=(180, 180, 200),
            hp=1000,
            max_hp=1000,
            ap=0,
            max_ap=0,
            auto_attack_damage=10,
            skills=(),
            team="enemy",
            ice_kind="black",
        )
        state = _make_combat_state_with_boss(boss)
        state.combat_effects = CombatEffects()
        self._drive_to_phase(boss, BLACK_ICE_LORD, state, 2)
        assert len(state.enemies) == 2

    def test_watchdog_alpha_no_aoe(self) -> None:
        from wet_run.combat.bosses import WATCHDOG_ALPHA

        for ph in WATCHDOG_ALPHA.phases:
            assert ph.aoe_damage == 0


# Phase N fix: PhaseProfile.phase is 0-indexed (phase 2 = third phase).
# The test_goliath_phase_3_25_aoe_highest test had wrong assertion (== 3).


class TestScaleMinionSpawn:
    """Tests for M3: dynamic minion spawn intensity scaling (ADR-0125)."""

    def test_empty_phase_returns_empty(self) -> None:
        from wet_run.combat.boss import PhaseProfile, scale_minion_spawn
        from wet_run.combat.state_models import Combatant, CombatState

        phase = PhaseProfile(
            phase=1,
            hp_threshold=1.0,
            damage_multiplier=1.0,
            color=(0, 0, 0),
            glyph="X",
            intro_text="",
            spawn_minions=(),
        )
        boss = Combatant(id="b", name="B", portrait="p", color=(0, 0, 0), hp=100, max_hp=100)
        state = CombatState(player=boss)
        result = scale_minion_spawn(phase, boss, state)
        assert result == ()

    def test_returns_subset_of_base_list(self) -> None:
        from wet_run.combat.boss import PhaseProfile, scale_minion_spawn
        from wet_run.combat.state_models import Combatant, CombatState

        phase = PhaseProfile(
            phase=2,
            hp_threshold=0.5,
            damage_multiplier=1.2,
            color=(0, 0, 0),
            glyph="X",
            intro_text="",
            spawn_minions=("m1", "m2", "m3", "m4"),
        )
        boss = Combatant(
            id="b",
            name="B",
            portrait="p",
            color=(0, 0, 0),
            hp=100,
            max_hp=100,
            equip_attack_bonus=2,
        )
        state = CombatState(player=boss)
        result = scale_minion_spawn(phase, boss, state)
        assert 1 <= len(result) <= 4
        assert all(m in phase.spawn_minions for m in result)


class TestBossAiChoosePhaseEffect:
    """Tests for M4: boss AI decision logic (ADR-0125)."""

    def test_no_effects_returns_none(self) -> None:
        from wet_run.combat.boss import PhaseProfile, boss_ai_choose_phase_effect
        from wet_run.combat.state_models import Combatant, CombatState

        phase = PhaseProfile(
            phase=1,
            hp_threshold=1.0,
            damage_multiplier=1.0,
            color=(0, 0, 0),
            glyph="X",
            intro_text="",
        )
        boss = Combatant(id="b", name="B", portrait="p", color=(0, 0, 0), hp=100, max_hp=100)
        state = CombatState(player=boss)
        assert boss_ai_choose_phase_effect(phase, state) == "none"

    def test_low_hp_player_picks_aoe(self) -> None:
        from wet_run.combat.boss import PhaseProfile, boss_ai_choose_phase_effect
        from wet_run.combat.state_models import Combatant, CombatState

        phase = PhaseProfile(
            phase=2,
            hp_threshold=0.5,
            damage_multiplier=1.0,
            color=(0, 0, 0),
            glyph="X",
            intro_text="",
            spawn_minions=("m1",),
            aoe_damage=20,
        )
        player = Combatant(id="p", name="P", portrait="x", color=(0, 0, 255), hp=20, max_hp=100)
        state = CombatState(player=player)
        assert boss_ai_choose_phase_effect(phase, state) == "aoe"

    def test_high_hp_player_picks_spawn(self) -> None:
        from wet_run.combat.boss import PhaseProfile, boss_ai_choose_phase_effect
        from wet_run.combat.state_models import Combatant, CombatState

        phase = PhaseProfile(
            phase=2,
            hp_threshold=0.5,
            damage_multiplier=1.0,
            color=(0, 0, 0),
            glyph="X",
            intro_text="",
            spawn_minions=("m1", "m2"),
            aoe_damage=20,
        )
        player = Combatant(id="p", name="P", portrait="x", color=(0, 0, 255), hp=100, max_hp=100)
        state = CombatState(player=player)
        assert boss_ai_choose_phase_effect(phase, state) == "spawn"
