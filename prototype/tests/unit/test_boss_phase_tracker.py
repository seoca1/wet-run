"""Tests for Boss Phase Transitions Integration (F.4, Round 6)."""

from __future__ import annotations

import pytest

from roguelike_sprawl.combat.boss_expansion import (
    BLACK_BARON_PROFILE,
    LOA_BARON_PROFILE,
    NEUROMANCER_PROFILE,
)
from roguelike_sprawl.combat.boss_phase_tracker import (
    BossPhaseTracker,
    PhaseProgress,
    get_all_f4_boss_ids,
    get_black_baron_tracker,
    get_damage_multiplier_for_phase,
    get_loa_baron_tracker,
    get_neuromancer_tracker,
    get_next_phase,
    get_phase_count_for_boss,
    get_phase_info,
    get_remaining_phases,
    get_tracker_for_boss,
    should_trigger_phase_transition,
)


class TestBossPhaseTrackerBasics:
    """BossPhaseTracker basic operations."""

    def test_create_tracker_neuromancer(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        assert tracker.boss == NEUROMANCER_PROFILE
        assert tracker.current_phase_index == 0
        assert tracker.total_phases == 6

    def test_create_tracker_loa_baron(self) -> None:
        tracker = BossPhaseTracker(LOA_BARON_PROFILE)
        assert tracker.total_phases == 4

    def test_create_tracker_black_baron(self) -> None:
        tracker = BossPhaseTracker(BLACK_BARON_PROFILE)
        assert tracker.total_phases == 4

    def test_current_phase_neuromancer(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        assert tracker.current_phase.phase == 1
        assert tracker.current_phase.hp_threshold == 1.0

    def test_current_phase_loa_baron(self) -> None:
        tracker = BossPhaseTracker(LOA_BARON_PROFILE)
        assert tracker.current_phase.phase == 1


class TestBossPhaseTransition:
    """Boss phase transition logic."""

    def test_should_transition_neuromancer_phase_1(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        assert tracker.should_transition(80, 400) is True
        assert tracker.should_transition(400, 400) is False

    def test_should_transition_neuromancer_phase_2(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        tracker.transition()
        assert tracker.current_phase.phase == 2
        assert tracker.should_transition(40, 400) is True
        assert tracker.should_transition(280, 400) is False

    def test_should_transition_last_phase(self) -> None:
        tracker = BossPhaseTracker(LOA_BARON_PROFILE)
        for _ in range(3):
            tracker.transition()
        assert tracker.is_last_phase is True
        assert tracker.should_transition(1, 100) is False

    def test_transition_advances(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        assert tracker.current_phase.phase == 1
        new_phase = tracker.transition()
        assert new_phase is not None
        assert new_phase.phase == 2
        assert tracker.current_phase.phase == 2

    def test_transition_to_last(self) -> None:
        tracker = BossPhaseTracker(LOA_BARON_PROFILE)
        for _ in range(3):
            tracker.transition()
        result = tracker.transition()
        assert result is None
        assert tracker.is_last_phase is True

    def test_reset(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        tracker.transition()
        tracker.transition()
        assert tracker.current_phase.phase == 3
        tracker.reset()
        assert tracker.current_phase.phase == 1


class TestBossPhaseProgress:
    """BossPhaseProgress information."""

    def test_get_progress_initial(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        progress = tracker.get_progress(400, 400)
        assert progress.boss_id == "neuromancer"
        assert progress.phase_index == 0
        assert progress.hp_fraction == 1.0
        assert progress.is_last_phase is False

    def test_get_progress_damaged(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        progress = tracker.get_progress(200, 400)
        assert progress.hp_fraction == 0.5

    def test_get_progress_zero_hp(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        progress = tracker.get_progress(0, 400)
        assert progress.hp_fraction == 0.0

    def test_get_progress_last_phase(self) -> None:
        tracker = BossPhaseTracker(LOA_BARON_PROFILE)
        for _ in range(3):
            tracker.transition()
        progress = tracker.get_progress(50, 100)
        assert progress.is_last_phase is True

    def test_is_transition_boundary(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        progress = tracker.get_progress(400, 400)
        assert progress.is_transition_boundary() is False
        progress2 = tracker.get_progress(80, 400)
        assert progress2.is_transition_boundary() is True


class TestBossPhaseQueries:
    """Boss phase query functions."""

    def test_get_all_f4_boss_ids(self) -> None:
        ids = get_all_f4_boss_ids()
        assert "neuromancer" in ids
        assert "loa_baron" in ids
        assert "black_baron" in ids

    def test_get_tracker_for_boss_neuromancer(self) -> None:
        tracker = get_tracker_for_boss("neuromancer")
        assert tracker is not None
        assert tracker.boss == NEUROMANCER_PROFILE

    def test_get_tracker_for_boss_loa_baron(self) -> None:
        tracker = get_tracker_for_boss("loa_baron")
        assert tracker is not None

    def test_get_tracker_for_boss_black_baron(self) -> None:
        tracker = get_tracker_for_boss("black_baron")
        assert tracker is not None

    def test_get_tracker_for_boss_nonexistent(self) -> None:
        assert get_tracker_for_boss("nonexistent") is None

    def test_get_neuromancer_tracker(self) -> None:
        tracker = get_neuromancer_tracker()
        assert tracker.boss == NEUROMANCER_PROFILE

    def test_get_loa_baron_tracker(self) -> None:
        tracker = get_loa_baron_tracker()
        assert tracker.boss == LOA_BARON_PROFILE

    def test_get_black_baron_tracker(self) -> None:
        tracker = get_black_baron_tracker()
        assert tracker.boss == BLACK_BARON_PROFILE


class TestBossPhaseHelpers:
    """Boss phase helper functions."""

    def test_get_phase_count_for_boss(self) -> None:
        assert get_phase_count_for_boss("neuromancer") == 6
        assert get_phase_count_for_boss("loa_baron") == 4
        assert get_phase_count_for_boss("black_baron") == 4
        assert get_phase_count_for_boss("nonexistent") == 0

    def test_get_phase_info(self) -> None:
        phase = get_phase_info("neuromancer", 0)
        assert phase is not None
        assert phase.phase == 1

    def test_get_phase_info_out_of_range(self) -> None:
        assert get_phase_info("neuromancer", 99) is None
        assert get_phase_info("neuromancer", -1) is None

    def test_get_phase_info_nonexistent(self) -> None:
        assert get_phase_info("nonexistent", 0) is None

    def test_get_next_phase(self) -> None:
        next_phase = get_next_phase("neuromancer", 0)
        assert next_phase is not None
        assert next_phase.phase == 2

    def test_get_next_phase_at_last(self) -> None:
        next_phase = get_next_phase("neuromancer", 5)
        assert next_phase is None

    def test_get_next_phase_nonexistent(self) -> None:
        assert get_next_phase("nonexistent", 0) is None

    def test_should_trigger_phase_transition(self) -> None:
        assert should_trigger_phase_transition("neuromancer", 80, 400, 0) is True
        assert should_trigger_phase_transition("neuromancer", 400, 400, 0) is False

    def test_should_trigger_phase_transition_at_last(self) -> None:
        assert should_trigger_phase_transition("neuromancer", 1, 400, 5) is False

    def test_should_trigger_phase_transition_nonexistent(self) -> None:
        assert should_trigger_phase_transition("nonexistent", 1, 100, 0) is False

    def test_get_damage_multiplier_for_phase(self) -> None:
        assert get_damage_multiplier_for_phase("neuromancer", 0) == 1.0
        assert get_damage_multiplier_for_phase("neuromancer", 5) == 3.0

    def test_get_damage_multiplier_for_phase_nonexistent(self) -> None:
        assert get_damage_multiplier_for_phase("nonexistent", 0) == 1.0

    def test_get_remaining_phases(self) -> None:
        assert get_remaining_phases("neuromancer", 0) == 5
        assert get_remaining_phases("neuromancer", 5) == 0
        assert get_remaining_phases("neuromancer", 3) == 2

    def test_get_remaining_phases_nonexistent(self) -> None:
        assert get_remaining_phases("nonexistent", 0) == 0


class TestBossPhaseTrackerMethods:
    """BossPhaseTracker method coverage."""

    def test_get_phase(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        phase = tracker.get_phase(2)
        assert phase.phase == 3

    def test_get_phase_out_of_range(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        with pytest.raises(IndexError):
            tracker.get_phase(99)

    def test_get_damage_multiplier(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        assert tracker.get_damage_multiplier() == 1.0
        tracker.transition()
        assert tracker.get_damage_multiplier() == 1.3

    def test_get_glyph(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        assert tracker.get_glyph() == "*"

    def test_get_color(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        assert tracker.get_color() == (255, 0, 100)

    def test_get_intro_text(self) -> None:
        tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        assert "NEUROMANCER" in tracker.get_intro_text()


class TestPhaseProgressDataclass:
    """PhaseProgress dataclass."""

    def test_create_phase_progress(self) -> None:
        progress = PhaseProgress(
            boss_id="test",
            phase_index=1,
            hp_threshold=0.5,
            hp_fraction=0.3,
            progress_in_phase=0.6,
            is_last_phase=False,
        )
        assert progress.boss_id == "test"
        assert progress.phase_index == 1
        assert progress.is_last_phase is False

    def test_is_transition_boundary_true(self) -> None:
        progress = PhaseProgress(
            boss_id="test",
            phase_index=0,
            hp_threshold=0.5,
            hp_fraction=0.3,
            progress_in_phase=0.6,
            is_last_phase=False,
        )
        assert progress.is_transition_boundary() is True

    def test_is_transition_boundary_false(self) -> None:
        progress = PhaseProgress(
            boss_id="test",
            phase_index=0,
            hp_threshold=0.5,
            hp_fraction=0.8,
            progress_in_phase=0.6,
            is_last_phase=False,
        )
        assert progress.is_transition_boundary() is False
