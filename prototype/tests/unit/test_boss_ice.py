"""Tests for ADR-0050: Boss ICE multi-phase system.

Covers:
    - IceType.WINTERMUTE and IceType.TA_CONSTRUCT_PRIME values
    - Combatant.current_phase default = 1 (non-bosses unchanged)
    - PhaseProfile + BossProfile dataclasses (frozen, slots)
    - BOSS_PROFILES dict maps both new types
    - is_boss() / get_boss_profile() helpers
    - current_phase(): HP threshold → phase mapping
    - phase_transition(): detects phase change
    - phase_damage(): damage × multiplier per phase
    - phase_skills(): skill pool swap per phase
    - phase_color() / phase_glyph(): HUD rendering helpers
    - apply_phase_to_combatant(): mutates skills + color + current_phase
    - Cinematic sequences: wintermute/ta_intro + phase transitions
    - Wintermute has 3 phases with damage 1.0x/1.5x/2.0x
    - TA Construct Prime has 3 phases with damage 0.7x/1.2x/1.8x
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.combat.boss import (  # noqa: E402
    BOSS_PROFILES,
    TA_CONSTRUCT_PRIME_PROFILE,
    WINTERMUTE_PROFILE,
    apply_phase_to_combatant,
    current_phase,
    get_boss_profile,
    is_boss,
    phase_color,
    phase_damage,
    phase_glyph,
    phase_skills,
    phase_transition,
)
from wet_run.combat.effects import (  # noqa: E402
    CinematicSequence,
    IceType,
    boss_phase_transition_sequence,
    ice_death_sequence,
    ice_intro_sequence,
)
from wet_run.combat.state import Combatant  # noqa: E402

# ============================================================================
# Helpers
# ============================================================================


def _make_combatant(
    name: str = "Test",
    *,
    hp: int = 100,
    max_hp: int = 100,
    auto_attack_damage: int = 10,
    ice_type: IceType = IceType.WINTERMUTE,
    current_phase: int = 1,
) -> Combatant:
    """Build a Combatant with the given HP for phase testing."""
    return Combatant(
        id="test_boss",
        name=name,
        portrait="art:wintermute",
        color=(120, 120, 220),
        hp=hp,
        max_hp=max_hp,
        auto_attack_damage=auto_attack_damage,
        current_phase=current_phase,
    )


# ============================================================================
# 1. IceType enum
# ============================================================================


class TestIceTypeBosses:
    def test_wintermute_in_enum(self) -> None:
        assert IceType.WINTERMUTE == "wintermute"

    def test_ta_construct_prime_in_enum(self) -> None:
        assert IceType.TA_CONSTRUCT_PRIME == "ta_construct_prime"

    def test_total_ice_types_seven(self) -> None:
        # 5 original + 2 bosses
        assert len(list(IceType)) == 7


# ============================================================================
# 2. Combatant field
# ============================================================================


class TestCombatantCurrentPhase:
    def test_default_current_phase_is_one(self) -> None:
        c = Combatant(id="x", name="x", portrait="x", color=(0, 0, 0), hp=10, max_hp=10)
        assert c.current_phase == 1

    def test_can_set_current_phase(self) -> None:
        c = _make_combatant(current_phase=2)
        assert c.current_phase == 2


# ============================================================================
# 3. Boss profiles
# ============================================================================


class TestBossProfiles:
    def test_wintermute_profile_exists(self) -> None:
        assert WINTERMUTE_PROFILE.ice_type == IceType.WINTERMUTE
        assert WINTERMUTE_PROFILE.max_phases == 4

    def test_ta_profile_exists(self) -> None:
        assert TA_CONSTRUCT_PRIME_PROFILE.ice_type == IceType.TA_CONSTRUCT_PRIME
        assert TA_CONSTRUCT_PRIME_PROFILE.max_phases == 4

    def test_wintermute_damage_multipliers(self) -> None:
        mults = [p.damage_multiplier for p in WINTERMUTE_PROFILE.phases]
        assert mults == [1.0, 1.5, 2.0, 3.0]

    def test_ta_damage_multipliers(self) -> None:
        mults = [p.damage_multiplier for p in TA_CONSTRUCT_PRIME_PROFILE.phases]
        assert mults == [0.7, 1.2, 1.8, 3.0]

    def test_wintermute_thresholds(self) -> None:
        thresholds = [p.hp_threshold for p in WINTERMUTE_PROFILE.phases]
        assert thresholds == [1.0, 0.66, 0.33, 0.10]

    def test_boss_profiles_dict_has_both(self) -> None:
        assert IceType.WINTERMUTE in BOSS_PROFILES
        assert IceType.TA_CONSTRUCT_PRIME in BOSS_PROFILES


class TestIsBoss:
    def test_wintermute_is_boss(self) -> None:
        assert is_boss(IceType.WINTERMUTE) is True

    def test_ta_construct_prime_is_boss(self) -> None:
        assert is_boss(IceType.TA_CONSTRUCT_PRIME) is True

    def test_standard_is_not_boss(self) -> None:
        assert is_boss(IceType.STANDARD) is False

    def test_construct_is_not_boss(self) -> None:
        assert is_boss(IceType.CONSTRUCT) is False


class TestGetBossProfile:
    def test_returns_wintermute(self) -> None:
        assert get_boss_profile(IceType.WINTERMUTE) is WINTERMUTE_PROFILE

    def test_returns_ta(self) -> None:
        assert get_boss_profile(IceType.TA_CONSTRUCT_PRIME) is TA_CONSTRUCT_PRIME_PROFILE

    def test_returns_none_for_non_boss(self) -> None:
        assert get_boss_profile(IceType.STANDARD) is None


# ============================================================================
# 4. Phase logic
# ============================================================================


class TestCurrentPhase:
    def test_full_hp_is_phase_1(self) -> None:
        boss = _make_combatant(hp=100, max_hp=100)
        phase = current_phase(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 1

    def test_just_below_phase_2_threshold_is_phase_2(self) -> None:
        # Phase 2 threshold = 0.66, so HP/max_hp must be <= 0.66
        boss = _make_combatant(hp=65, max_hp=100)
        phase = current_phase(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 2

    def test_just_above_phase_2_threshold_is_phase_1(self) -> None:
        # HP 67/100 = 0.67 > 0.66 → still phase 1
        boss = _make_combatant(hp=67, max_hp=100)
        phase = current_phase(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 1

    def test_just_below_phase_3_threshold_is_phase_3(self) -> None:
        # Phase 3 threshold = 0.33
        boss = _make_combatant(hp=32, max_hp=100)
        phase = current_phase(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 3

    def test_zero_hp_is_phase_4(self) -> None:
        boss = _make_combatant(hp=0, max_hp=100)
        phase = current_phase(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 4

    def test_zero_max_hp_returns_last_phase(self) -> None:
        # Defensive: avoid division by zero
        boss = _make_combatant(hp=0, max_hp=0)
        phase = current_phase(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 4

    def test_exactly_at_phase_2_threshold(self) -> None:
        # HP 66/100 = 0.66 exactly → phase 2 (≤ threshold)
        boss = _make_combatant(hp=66, max_hp=100)
        phase = current_phase(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 2

    def test_exactly_at_phase_3_threshold(self) -> None:
        # HP 33/100 = 0.33 exactly → phase 3 (≤ threshold)
        boss = _make_combatant(hp=33, max_hp=100)
        phase = current_phase(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 3

    def test_negative_hp_is_phase_4(self) -> None:
        # hp=-10, max_hp=100 → hp_ratio = -0.1 ≤ all thresholds
        boss = _make_combatant(hp=-10, max_hp=100)
        phase = current_phase(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 4

    def test_negative_max_hp_is_phase_4(self) -> None:
        # hp=0, max_hp=-100 → hp_ratio = -0.0 (negative zero), ≤ all thresholds
        boss = _make_combatant(hp=0, max_hp=-100)
        phase = current_phase(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 4

    def test_hp_exceeds_max_hp_stays_phase_1(self) -> None:
        # hp=101, max_hp=100 → hp_ratio = 1.01 > 1.0 (phase 1 threshold)
        boss = _make_combatant(hp=101, max_hp=100)
        phase = current_phase(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 1


class TestPhaseTransition:
    def test_no_transition_when_phase_matches(self) -> None:
        boss = _make_combatant(hp=100, current_phase=1)
        assert phase_transition(boss, WINTERMUTE_PROFILE) is None

    def test_transition_phase_1_to_2(self) -> None:
        boss = _make_combatant(hp=50, max_hp=100, current_phase=1)
        new = phase_transition(boss, WINTERMUTE_PROFILE)
        assert new is not None
        assert new.phase == 2

    def test_transition_phase_2_to_3(self) -> None:
        boss = _make_combatant(hp=20, max_hp=100, current_phase=2)
        new = phase_transition(boss, WINTERMUTE_PROFILE)
        assert new is not None
        assert new.phase == 3

    def test_no_transition_when_already_max(self) -> None:
        boss = _make_combatant(hp=0, current_phase=4)
        assert phase_transition(boss, WINTERMUTE_PROFILE) is None

    def test_skip_transition_phase_1_to_3(self) -> None:
        # Stale phase: boss was manually set to phase 1 but HP now phase 3
        boss = _make_combatant(hp=20, max_hp=100, current_phase=1)
        new = phase_transition(boss, WINTERMUTE_PROFILE)
        assert new is not None
        assert new.phase == 3

    def test_reverse_transition_phase_3_to_1(self) -> None:
        # Healing: boss HP recovered from phase 3 to phase 1
        boss = _make_combatant(hp=100, max_hp=100, current_phase=3)
        new = phase_transition(boss, WINTERMUTE_PROFILE)
        assert new is not None
        assert new.phase == 1


class TestPhaseDamage:
    def test_phase_1_damage(self) -> None:
        boss = _make_combatant(hp=100, max_hp=100, auto_attack_damage=10)
        assert phase_damage(boss, WINTERMUTE_PROFILE) == 10

    def test_phase_2_damage_1_5x(self) -> None:
        boss = _make_combatant(hp=50, max_hp=100, auto_attack_damage=10)
        assert phase_damage(boss, WINTERMUTE_PROFILE) == 15

    def test_phase_3_damage_2x(self) -> None:
        boss = _make_combatant(hp=20, max_hp=100, auto_attack_damage=10)
        assert phase_damage(boss, WINTERMUTE_PROFILE) == 20

    def test_ta_phase_1_damage_0_7x(self) -> None:
        boss = _make_combatant(
            hp=100, max_hp=100, auto_attack_damage=10, ice_type=IceType.TA_CONSTRUCT_PRIME
        )
        assert phase_damage(boss, TA_CONSTRUCT_PRIME_PROFILE) == 7


class TestPhaseSkills:
    def test_phase_1_has_probe(self) -> None:
        boss = _make_combatant(hp=100, max_hp=100)
        skills = phase_skills(boss, WINTERMUTE_PROFILE)
        assert any(s.id == "wintermute_probe" for s in skills)

    def test_phase_2_has_corrode_and_adapt(self) -> None:
        boss = _make_combatant(hp=50, max_hp=100)
        skills = phase_skills(boss, WINTERMUTE_PROFILE)
        ids = {s.id for s in skills}
        assert "wintermute_burn" in ids
        assert "wintermute_buff" in ids

    def test_phase_3_has_spike_and_fracture(self) -> None:
        boss = _make_combatant(hp=20, max_hp=100)
        skills = phase_skills(boss, WINTERMUTE_PROFILE)
        ids = {s.id for s in skills}
        assert "wintermute_pierce" in ids
        assert "wintermute_multi" in ids


class TestPhaseColorAndGlyph:
    def test_phase_1_color(self) -> None:
        boss = _make_combatant(hp=100)
        assert phase_color(boss, WINTERMUTE_PROFILE) == (120, 120, 220)

    def test_phase_3_color_is_red(self) -> None:
        boss = _make_combatant(hp=20)
        assert phase_color(boss, WINTERMUTE_PROFILE) == (255, 50, 100)

    def test_phase_1_glyph(self) -> None:
        boss = _make_combatant(hp=100)
        assert phase_glyph(boss, WINTERMUTE_PROFILE) == "?"


class TestApplyPhaseToCombatant:
    def test_applies_phase_1(self) -> None:
        boss = _make_combatant(hp=100)
        phase = apply_phase_to_combatant(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 1
        assert boss.current_phase == 1
        assert boss.color == (120, 120, 220)

    def test_applies_phase_2(self) -> None:
        boss = _make_combatant(hp=50)
        phase = apply_phase_to_combatant(boss, WINTERMUTE_PROFILE)
        assert phase.phase == 2
        assert boss.current_phase == 2
        assert any(s.id == "wintermute_burn" for s in boss.skills)


# ============================================================================
# 5. Cinematic sequences
# ============================================================================


class TestCinematics:
    def test_wintermute_intro_returns_unique_sequence(self) -> None:
        seq = ice_intro_sequence(IceType.WINTERMUTE, "Wintermute")
        assert isinstance(seq, CinematicSequence)
        assert "wintermute" in seq.name
        # Has the "PHASE 1/3" marker
        assert any("PHASE 1/3" in p[0] for p in seq.phases)

    def test_ta_intro_returns_unique_sequence(self) -> None:
        seq = ice_intro_sequence(IceType.TA_CONSTRUCT_PRIME, "T-A Prime")
        assert "ta_construct_prime" in seq.name
        assert any("PHASE 1/3" in p[0] for p in seq.phases)

    def test_wintermute_has_distinct_intro(self) -> None:
        # Not the same as construct
        seq_w = ice_intro_sequence(IceType.WINTERMUTE, "X")
        seq_c = ice_intro_sequence(IceType.CONSTRUCT, "X")
        assert seq_w.name != seq_c.name

    def test_ta_has_distinct_intro_from_construct(self) -> None:
        seq_t = ice_intro_sequence(IceType.TA_CONSTRUCT_PRIME, "X")
        seq_c = ice_intro_sequence(IceType.CONSTRUCT, "X")
        assert seq_t.name != seq_c.name

    def test_wintermute_death_sequence(self) -> None:
        seq = ice_death_sequence(IceType.WINTERMUTE)
        assert "wintermute" in seq.name

    def test_ta_death_sequence(self) -> None:
        seq = ice_death_sequence(IceType.TA_CONSTRUCT_PRIME)
        assert "ta_construct_prime" in seq.name


class TestPhaseTransitionCinematic:
    def test_wintermute_phase_2_transition(self) -> None:
        seq = boss_phase_transition_sequence(IceType.WINTERMUTE, phase=2)
        assert "wintermute" in seq.name
        assert any("PHASE 2/3" in p[0] for p in seq.phases)

    def test_wintermute_phase_3_transition(self) -> None:
        seq = boss_phase_transition_sequence(IceType.WINTERMUTE, phase=3)
        assert any("PHASE 3/3" in p[0] for p in seq.phases)

    def test_ta_phase_2_transition(self) -> None:
        seq = boss_phase_transition_sequence(IceType.TA_CONSTRUCT_PRIME, phase=2)
        assert "ta_construct_prime" in seq.name
        assert any("PHASE 2/3" in p[0] for p in seq.phases)

    def test_ta_phase_3_transition(self) -> None:
        seq = boss_phase_transition_sequence(IceType.TA_CONSTRUCT_PRIME, phase=3)
        assert any("PHASE 3/3" in p[0] for p in seq.phases)


# ============================================================================
# 6. Phase profile dataclass immutability
# ============================================================================


class TestPhaseProfileFrozen:
    def test_phase_profile_is_frozen(self) -> None:
        p = WINTERMUTE_PROFILE.phases[0]
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            p.damage_multiplier = 99.0  # type: ignore[misc]

    def test_boss_profile_is_frozen(self) -> None:
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            WINTERMUTE_PROFILE.name = "Other"  # type: ignore[misc]
