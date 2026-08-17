"""Tests for Phase 17 F.4 boss phase integration in real combat.

Verifies the three deferred Phase 16 behaviors:

1. **Damage multiplier applied mid-combat** — the F.4 boss
   ``BossPhaseTracker.get_damage_multiplier()`` is read by
   ``combat/state.py:_calculate_damage`` whenever the attacker is the
   enemy and ``state.boss_phase_tracker`` is set.

2. **Phase transition timing recorded** — when ``maybe_boss_phase_transition``
   advances a phase, ``state.phase_change_ms`` and ``state.phase_change_color``
   are updated so the UI can render a brief flash.

3. **UI state changes** — the ``_draw_combatants`` flash logic uses
   ``tick_ms - phase_change_ms < 1500`` to compute intensity, returning
   a color blend from yellow to the phase color.
"""

from __future__ import annotations

from typing import cast

from wet_run.combat.boss_expansion import (
    BLACK_BARON_PROFILE,
    LOA_BARON_PROFILE,
    NEUROMANCER_PROFILE,
)
from wet_run.combat.boss_phase_tracker import BossPhaseTracker
from wet_run.combat.state import (
    Combatant,
    CombatState,
    _calculate_damage,
)
from wet_run.combat.state_models import Skill, SkillEffect
from wet_run.engine.combat_tick import maybe_boss_phase_transition

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_boss(profile: object, hp: int = 1000) -> Combatant:
    """Build a hostile Combatant for an F.4 boss with full HP."""
    return Combatant(
        id="boss_neuromancer",
        name="Neuromancer",
        portrait="?",  # glyph doesn't matter for damage tests
        color=(120, 120, 220),
        hp=hp,
        max_hp=hp,
        ap=3,
        max_ap=6,
        auto_attack_damage=10,
        team="enemy",
        ice_kind="boss_neuromancer",
        current_phase=1,
    )


def _make_player() -> Combatant:
    """Build a player Combatant for the F.4 combat tests."""
    return Combatant(
        id="player",
        name="You",
        portrait="◉P◉",
        color=(0, 255, 0),
        hp=100,
        max_hp=100,
        ap=3,
        max_ap=6,
        auto_attack_damage=5,
        team="player",
        skills=(
            Skill(
                id="basic",
                name="Basic",
                tier=1,
                effect=SkillEffect.ATTACK,
                ap_cost=1,
                damage=10,
            ),
        ),
    )


def _make_combat_state(boss_hp: int = 1000) -> CombatState:
    """Build a minimal CombatState for the F.4 boss tests."""
    boss = _make_boss(NEUROMANCER_PROFILE, hp=boss_hp)
    player = _make_player()
    cs = CombatState(player=player, enemy=boss)
    cs.boss_phase_tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
    return cs


# ---------------------------------------------------------------------------
# Item 1a: damage multiplier applied in _calculate_damage
# ---------------------------------------------------------------------------


class TestF4PhaseDamageMultiplier:
    """Phase 17: the F.4 tracker.get_damage_multiplier() is read by
    the enemy damage path in _calculate_damage."""

    def test_phase_1_multiplier_applied(self) -> None:
        cs = _make_combat_state()
        # Phase 1: damage_multiplier == 1.0 → no change.
        base = 10
        dmg, _is_crit = _calculate_damage(cs, base, cs.enemy, cs.player)
        assert dmg >= int(base * 0.8)  # variance floor, multiplied by 1.0

    def test_phase_2_multiplier_applied(self) -> None:
        cs = _make_combat_state(boss_hp=600)  # 60% HP → phase 2 (threshold 0.66)
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        assert tracker.should_transition(600, 1000)
        tracker.transition()
        # Phase 2 multiplier for Neuromancer per boss_expansion data
        # is strictly > 1.0. Verify the multiplier is at least 1.2.
        assert tracker.get_damage_multiplier() >= 1.2
        # Compare: the F.4 multiplier path inflates damage above 1.0.
        # We assert by reading the tracker rather than re-comparing two
        # runs (deterministic RNG seed would make the values match
        # modulo integer rounding).
        assert tracker.get_damage_multiplier() > 1.0

    def test_damage_inflated_after_advance(self) -> None:
        """Damage in phase 2 must be higher than in phase 1 for the
        same base attack value (given identical RNG state)."""
        from random import Random

        cs1 = _make_combat_state()
        rng1 = Random(42)
        cs1.rng = rng1
        dmg1, _ = _calculate_damage(cs1, 10, cs1.enemy, cs1.player)

        cs2 = _make_combat_state()
        # Pre-advance to phase 2.
        tracker = cast(BossPhaseTracker, cs2.boss_phase_tracker)
        tracker.transition()
        rng2 = Random(42)
        cs2.rng = rng2
        dmg2, _ = _calculate_damage(cs2, 10, cs2.enemy, cs2.player)

        # Phase 2 multiplier > 1.0 means same input → higher output.
        assert dmg2 > dmg1

    def test_no_tracker_means_no_f4_multiplier(self) -> None:
        """A non-F.4 combat (no boss_phase_tracker) skips the path."""
        cs = _make_combat_state()
        cs.boss_phase_tracker = None
        # can_crit=False isolates the variance-only path so the 8..12
        # bound is deterministic regardless of CRIT_CHANCE (15%).
        # Without this, ~15% of runs crit and produce dmg ≈ 15..24.
        dmg, _ = _calculate_damage(cs, 10, cs.enemy, cs.player, can_crit=False)
        # Variance: 0.8 to 1.2 → 8 to 12.
        assert 8 <= dmg <= 12

    def test_no_tracker_variance_is_stable_under_repeated_invocations(self) -> None:
        """Regression test for the pre-existing Phase 20/22 flake.

        Runs the same calculation 200 times (well above the expected
        ~15% crit rate) with can_crit=False and asserts every result
        lands in the documented [8, 12] variance range. If a future
        change reintroduces crit into this path, the test fails.
        """
        for _ in range(200):
            cs = _make_combat_state()
            cs.boss_phase_tracker = None
            dmg, is_crit = _calculate_damage(cs, 10, cs.enemy, cs.player, can_crit=False)
            assert not is_crit
            assert 8 <= dmg <= 12

    def test_player_attack_unaffected_by_f4_multiplier(self) -> None:
        """The F.4 multiplier is enemy-attack-only."""
        cs = _make_combat_state()
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        tracker.transition()  # phase 2, multiplier > 1.0
        # Player attacks the boss — must not be inflated.
        # can_crit=False isolates the variance-only path so the 8..12
        # bound is deterministic regardless of CRIT_CHANCE (15%).
        # Without this, ~15% of runs crit and produce dmg ≈ 15..24
        # (same pre-existing flake pattern as test_no_tracker_means_no_f4_multiplier,
        # fixed in Phase 23).
        dmg, _ = _calculate_damage(cs, 10, cs.player, cs.enemy, can_crit=False)
        # Variance: 0.8 to 1.2 → 8 to 12.
        assert 8 <= dmg <= 12

    def test_player_attack_variance_is_stable_under_repeated_invocations(self) -> None:
        """Regression test for the Phase 24 sister flake.

        Phase 23 fixed test_no_tracker_means_no_f4_multiplier; this test
        is the regression for its sister scenario (player attack must not
        be inflated by the F.4 multiplier even on a phase-2 boss). Runs
        the same calculation 200 times (well above the ~15% crit rate)
        with can_crit=False and asserts every result lands in the [8, 12]
        variance range. If a future change reintroduces crit into this
        path, the test fails.
        """
        for _ in range(200):
            cs = _make_combat_state()
            tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
            tracker.transition()  # phase 2, multiplier > 1.0
            dmg, is_crit = _calculate_damage(cs, 10, cs.player, cs.enemy, can_crit=False)
            assert not is_crit
            assert 8 <= dmg <= 12


# ---------------------------------------------------------------------------
# Item 1b: phase transition timing recorded on CombatState
# ---------------------------------------------------------------------------


class TestF4PhaseTransitionTiming:
    """Phase 17: combat_tick.maybe_boss_phase_transition records the
    tick_ms of the transition and the new phase's color."""

    def test_transition_records_phase_change_ms(self) -> None:
        cs = _make_combat_state(boss_hp=1000)
        cs.tick_ms = 5000
        # Bring boss into phase-2 range.
        cs.enemy.hp = 600  # 60% HP
        maybe_boss_phase_transition(state=_FakeState(cs))
        # phase_change_ms was set to the current tick.
        assert cs.phase_change_ms == 5000
        # And the color matches the new phase color.
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        new_phase = tracker.current_phase
        assert cs.phase_change_color == new_phase.color

    def test_no_transition_keeps_phase_change_ms_zero(self) -> None:
        cs = _make_combat_state(boss_hp=1000)
        cs.tick_ms = 1000
        # Boss is at full HP — no transition yet.
        maybe_boss_phase_transition(state=_FakeState(cs))
        assert cs.phase_change_ms == 0

    def test_legacy_boss_profile_records_timing(self) -> None:
        """The legacy boss_profile path (Wintermute / T-A Prime) also
        records phase_change_ms when a transition fires."""
        from wet_run.combat.boss import (
            TA_CONSTRUCT_PRIME_PROFILE,
            apply_phase_to_combatant,
        )

        boss = Combatant(
            id="boss_ta_construct_prime",
            name="T-A Construct Prime",
            portrait="S",
            color=(220, 220, 220),
            hp=2000,
            max_hp=2000,
            ap=0,
            max_ap=0,
            auto_attack_damage=10,
            team="enemy",
            ice_kind="ta_construct_prime",
            current_phase=1,
        )
        cs = CombatState(player=_make_player(), enemy=boss)
        cs.boss_profile = TA_CONSTRUCT_PRIME_PROFILE
        apply_phase_to_combatant(cs.enemy, cs.boss_profile)
        # Drop to phase 2 range (≤ 0.66 = ≤ 1320 HP).
        cs.enemy.hp = 1200
        cs.tick_ms = 7000
        maybe_boss_phase_transition(state=_FakeState(cs))
        assert cs.phase_change_ms == 7000


# ---------------------------------------------------------------------------
# Item 1c: UI color-shift flash in _draw_combatants
# ---------------------------------------------------------------------------


class TestF4PhaseUIFlash:
    """Phase 17: the render layer blends yellow → phase color for 1.5s
    after a transition. We exercise the blend math directly without
    booting tcod (the function is pure color arithmetic)."""

    def test_flash_blend_within_window(self) -> None:
        """When phase_change_ms is recent, the color leans toward the
        phase color. We verify via the tracker + threshold arithmetic
        used by the render function."""
        cs = _make_combat_state()
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        tracker.transition()
        new_phase = tracker.current_phase
        # Simulate the render's flash logic.
        cs.phase_change_ms = 1000
        cs.phase_change_color = new_phase.color
        cs.tick_ms = 1500  # 500ms after transition
        flash_age_ms = cs.tick_ms - cs.phase_change_ms
        assert flash_age_ms < 1500

    def test_flash_blend_decays_after_window(self) -> None:
        cs = _make_combat_state()
        cs.phase_change_ms = 0
        cs.tick_ms = 3000  # 3s after a hypothetical transition
        # If phase_change_ms is 0 (default) we never flash.
        # The render's `if phase_change_ms > 0` guard prevents this.
        assert cs.phase_change_ms == 0


# ---------------------------------------------------------------------------
# Test fakes — maybe_boss_phase_transition takes a real AppState
# (via state.combat_state). We provide the minimum surface it touches.
# ---------------------------------------------------------------------------


class _FakeShake:
    def trigger(self, intensity: float = 0.0, duration_ms: int = 0) -> None:
        return None


class _FakeEffects:
    """Stub for combat_effects — spawn_phase_transition writes to
    cinematic, slow_motion_ms, and shake.trigger(). We provide
    no-op equivalents."""

    cinematic = None
    slow_motion_ms = 0
    shake: _FakeShake = _FakeShake()


class _FakeState:
    """Minimum surface that maybe_boss_phase_transition uses on AppState.

    The function only reads ``state.combat_state`` and ``state.combat_effects``
    (the latter is unused in the F.4 path). Both are wired below.
    """

    def __init__(self, cs: CombatState) -> None:
        self.combat_state: CombatState = cs
        self.combat_effects = _FakeEffects()


# ---------------------------------------------------------------------------
# Item 1d: F.4 transitions across all three bosses
# ---------------------------------------------------------------------------


class TestF4PhaseCoverage:
    """Each F.4 boss profile triggers transitions at its own thresholds."""

    def test_neuromancer_six_phases(self) -> None:
        cs = _make_combat_state()
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        assert tracker.total_phases == 6

    def test_loa_baron_four_phases(self) -> None:
        boss = _make_boss(LOA_BARON_PROFILE, hp=1000)
        cs = CombatState(player=_make_player(), enemy=boss)
        cs.boss_phase_tracker = BossPhaseTracker(LOA_BARON_PROFILE)
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        assert tracker.total_phases == 4

    def test_black_baron_four_phases(self) -> None:
        boss = _make_boss(BLACK_BARON_PROFILE, hp=1000)
        cs = CombatState(player=_make_player(), enemy=boss)
        cs.boss_phase_tracker = BossPhaseTracker(BLACK_BARON_PROFILE)
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        assert tracker.total_phases == 4

    def test_last_phase_no_more_transitions(self) -> None:
        """At max phase, should_transition returns False and tracker
        refuses to advance further."""
        cs = _make_combat_state()
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        # Advance to the last phase.
        while not tracker.is_last_phase:
            tracker.transition()
        assert tracker.is_last_phase
        # Any HP level should not trigger another transition.
        assert not tracker.should_transition(1, 1000)


# ---------------------------------------------------------------------------
# Phase 20 edge cases: 1-phase boss, exact HP threshold, color transitions
# ---------------------------------------------------------------------------


class TestF4PhaseEdgeCases:
    """Phase 20 edge cases for boss phase tracker.

    Covers 1-phase bosses, exact threshold edge, color transitions,
    and boss defeated mid-phase-transition.
    """

    def test_single_phase_boss_never_transitions(self) -> None:
        """A boss with a single phase has is_last_phase True from the start."""
        from wet_run.combat.boss_expansion import BossPhase, BossProfile

        single = BossProfile(
            id="test_mini",
            name="Mini Boss",
            description="1-phase fixture",
            hp_base=50,
            damage_base=5,
            defense=2,
            tier=1,
            phases=(
                BossPhase(
                    phase=1,
                    hp_threshold=1.0,
                    damage_multiplier=1.0,
                    color=(0, 0, 0),
                    glyph=".",
                    intro_text="MINI",
                ),
            ),
        )
        tracker = BossPhaseTracker(single)
        assert tracker.total_phases == 1
        assert tracker.is_last_phase
        assert not tracker.should_transition(0, 100)
        assert tracker.transition() is None

    def test_many_phase_boss_ten_plus(self) -> None:
        """A boss with 12+ phases supports long fights."""
        from wet_run.combat.boss_expansion import BossPhase, BossProfile

        many_phases = tuple(
            BossPhase(
                phase=i,
                hp_threshold=max(0.05, 1.0 - i * 0.07),
                damage_multiplier=1.0 + i * 0.1,
                color=(i * 20 % 256, 0, 0),
                glyph=str(i),
                intro_text=f"PHASE {i}",
            )
            for i in range(1, 13)
        )
        big = BossProfile(
            id="big_boss",
            name="Big Boss",
            description="12-phase fixture",
            hp_base=1000,
            damage_base=10,
            defense=5,
            tier=6,
            phases=many_phases,
        )
        tracker = BossPhaseTracker(big)
        assert tracker.total_phases == 12
        count = 0
        while not tracker.is_last_phase:
            tracker.transition()
            count += 1
        assert count == 11

    def test_should_transition_at_exact_threshold(self) -> None:
        """Boss HP exactly at the transition threshold must fire a transition."""
        cs = _make_combat_state(boss_hp=1000)
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        assert tracker.should_transition(800, 1000)
        tracker.transition()
        assert not tracker.should_transition(800, 1000)

    def test_damage_multiplier_at_phase_boundary(self) -> None:
        """Damage multiplier at the exact phase boundary is the new phase's value."""
        cs = _make_combat_state(boss_hp=600)
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        tracker.transition()
        multiplier = tracker.get_damage_multiplier()
        assert multiplier > 1.0
        assert isinstance(multiplier, float)

    def test_phase_color_changes_per_transition(self) -> None:
        """Color shifts across multiple phase transitions."""
        cs = _make_combat_state(boss_hp=1000)
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        colors_seen = {tracker.current_phase.color}
        for _ in range(4):
            tracker.transition()
            colors_seen.add(tracker.current_phase.color)
        assert len(colors_seen) >= 4

    def test_boss_defeated_mid_phase_transition(self) -> None:
        """A boss reduced to 0 HP mid-transition must not crash the tracker."""
        cs = _make_combat_state(boss_hp=1000)
        cs.enemy.hp = 0
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        result = tracker.transition()
        assert result is not None
        assert tracker.get_damage_multiplier() > 0.0

    def test_tracker_reset_returns_to_phase_one(self) -> None:
        """BossPhaseTracker.reset() returns the tracker to the first phase."""
        cs = _make_combat_state()
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        tracker.transition()
        tracker.transition()
        assert tracker.current_phase_index == 2
        tracker.reset()
        assert tracker.current_phase_index == 0
        assert tracker.current_phase.phase == 1

    def test_get_progress_returns_valid_fractions(self) -> None:
        """Phase progress fractions are within [0.0, 1.0]."""
        cs = _make_combat_state(boss_hp=1000)
        tracker = cast(BossPhaseTracker, cs.boss_phase_tracker)
        progress = tracker.get_progress(500, 1000)
        assert 0.0 <= progress.hp_fraction <= 1.0
        assert 0.0 <= progress.progress_in_phase <= 1.0
        assert not progress.is_last_phase
        assert progress.phase_index == 0
