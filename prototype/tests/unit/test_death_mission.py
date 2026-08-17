"""Unit tests for death/restart and mission completion systems."""

from __future__ import annotations

from tcod.event import KeyDown, KeySym, Modifier, Scancode

from wet_run.engine import death as death_screen
from wet_run.engine import mission_completion
from wet_run.engine.state import AppState, ScreenKind
from wet_run.matrix.node import ZoneDepth
from wet_run.missions.board import JobBoard
from wet_run.missions.mission import Mission, Objective, Rewards


def _make_first_jack_mission() -> Mission:
    """Standard 'First Jack' mission: extract 1 data + defeat 1 ICE."""
    return Mission(
        id="first_jack",
        title="First Jack",
        fixer="finn",
        arc=1,
        grade_min=1,
        grade_max=1,
        matrix_seed=42,
        zone=ZoneDepth.SURFACE,
        objective="Extract demo_file",
        reward_tier=1,
        reward_credits=500,
        primary_objective=Objective(type="extract_data", data_id="demo_file", count=1),
        secondary_objectives=(Objective(type="defeat", enemy="ice.standard", count=1),),
        rewards=Rewards(credits=500, materials={"data_fragment": 2}),
    )


def _make_two_extract_mission() -> Mission:
    """Mission requiring 2 data extractions (incomplete after 1)."""
    return Mission(
        id="two_extract",
        title="Two Extract",
        fixer="finn",
        arc=1,
        grade_min=1,
        grade_max=1,
        matrix_seed=0,
        zone=ZoneDepth.SURFACE,
        primary_objective=Objective(type="extract_data", count=2),
    )


def _make_test_state(with_mission: bool = True) -> AppState:
    """Build a test AppState with a job board containing First Jack."""
    state = AppState()
    mission = _make_first_jack_mission()
    state.job_board = JobBoard((mission,))
    if with_mission:
        state.current_mission = mission
    state.player_max_hp = 100
    state.player_hp = 50
    return state


# ============================================================================
# Mission model tests
# ============================================================================


class TestMissionCheckCompletion:
    """Mission.check_completion() returns True when objective is met."""

    def test_extract_complete(self) -> None:
        """1/1 extract_data means complete."""
        m = _make_first_jack_mission()
        assert m.check_completion({"extract_data": 1}) is True

    def test_extract_incomplete(self) -> None:
        """0/1 extract_data is not complete."""
        m = _make_first_jack_mission()
        assert m.check_completion({"extract_data": 0}) is False

    def test_extract_missing_key(self) -> None:
        """Empty progress dict means not complete."""
        m = _make_first_jack_mission()
        assert m.check_completion({}) is False

    def test_other_objective_doesnt_count(self) -> None:
        """Defeating ICE doesn't satisfy extract_data objective."""
        m = _make_first_jack_mission()
        assert m.check_completion({"defeat": 5}) is False

    def test_overflow_counts(self) -> None:
        """5/1 is still complete."""
        m = _make_first_jack_mission()
        assert m.check_completion({"extract_data": 5}) is True


class TestMissionProgressPct:
    """Mission.progress_pct() returns 0.0-1.0."""

    def test_zero_progress(self) -> None:
        """0/1 = 0.0%."""
        m = _make_first_jack_mission()
        assert m.progress_pct({}) == 0.0

    def test_half_progress(self) -> None:
        """1/2 = 50%."""
        m = Mission(
            id="two_extract",
            title="Two",
            fixer="finn",
            arc=1,
            grade_min=1,
            grade_max=1,
            matrix_seed=0,
            zone=ZoneDepth.SURFACE,
            primary_objective=Objective(type="extract_data", count=2),
        )
        assert m.progress_pct({"extract_data": 1}) == 0.5

    def test_full_progress(self) -> None:
        """1/1 = 100%."""
        m = _make_first_jack_mission()
        assert m.progress_pct({"extract_data": 1}) == 1.0

    def test_overflow_capped(self) -> None:
        """5/1 capped at 100%."""
        m = _make_first_jack_mission()
        assert m.progress_pct({"extract_data": 5}) == 1.0


# ============================================================================
# Mission completion tests
# ============================================================================


class TestMissionCompletion:
    """check_mission_completion() and complete_mission()."""

    def test_complete_mission_awards_credits(self) -> None:
        """Completing mission adds reward_credits to state.credits."""
        state = _make_test_state()
        state.mission_progress = {"extract_data": 1}

        result = mission_completion.check_mission_completion(state)

        assert result is True
        assert state.credits == 500

    def test_complete_mission_awards_materials(self) -> None:
        """Completing mission adds reward materials to inventory."""
        state = _make_test_state()
        state.mission_progress = {"extract_data": 1}

        mission_completion.check_mission_completion(state)

        assert state.inventory.get("data_fragment") == 2

    def test_complete_mission_marks_complete(self) -> None:
        """Completed mission id is added to completed_missions."""
        state = _make_test_state()
        state.mission_progress = {"extract_data": 1}

        mission_completion.check_mission_completion(state)

        assert "first_jack" in state.completed_missions

    def test_complete_mission_clears_current(self) -> None:
        """current_mission becomes None after completion."""
        state = _make_test_state()
        state.mission_progress = {"extract_data": 1}

        mission_completion.check_mission_completion(state)

        assert state.current_mission is None

    def test_incomplete_mission_returns_false(self) -> None:
        """0/1 progress returns False."""
        state = _make_test_state()
        state.mission_progress = {"extract_data": 0}

        result = mission_completion.check_mission_completion(state)

        assert result is False
        assert state.credits == 0  # No reward

    def test_no_active_mission_returns_false(self) -> None:
        """No current_mission returns False."""
        state = _make_test_state(with_mission=False)

        result = mission_completion.check_mission_completion(state)

        assert result is False


class TestUpdateMissionProgress:
    """update_mission_progress() advances progress and checks completion."""

    def test_progress_increments(self) -> None:
        """Adding progress increments the counter (without completion)."""
        # Mission requires 2 extractions; first one doesn't complete
        state = _make_test_state()
        state.current_mission = _make_two_extract_mission()

        mission_completion.update_mission_progress(state, "extract_data", 1)

        assert state.mission_progress["extract_data"] == 1

    def test_wrong_objective_ignored(self) -> None:
        """Progress on non-primary objective is ignored."""
        state = _make_test_state()

        result = mission_completion.update_mission_progress(state, "defeat", 5)

        assert result is False
        assert state.mission_progress == {}

    def test_completes_when_target_reached(self) -> None:
        """Mission completes when target count reached."""
        state = _make_test_state()

        result = mission_completion.update_mission_progress(state, "extract_data", 1)

        assert result is True
        assert state.credits == 500  # Reward awarded
        assert "first_jack" in state.completed_missions


class TestNextAvailableMission:
    """get_next_available_mission() returns next un-completed mission."""

    def test_returns_first_uncompleted(self) -> None:
        """With one mission un-completed, returns it."""
        state = _make_test_state(with_mission=False)
        m = mission_completion.get_next_available_mission(state)

        assert m is not None
        assert m.id == "first_jack"

    def test_returns_none_when_all_done(self) -> None:
        """With mission completed, returns None."""
        state = _make_test_state(with_mission=False)
        state.completed_missions.add("first_jack")

        m = mission_completion.get_next_available_mission(state)

        assert m is None

    def test_skips_completed_missions(self) -> None:
        """When one mission is done, returns next one."""
        # Add 2 missions
        mission2 = Mission(
            id="second",
            title="Second",
            fixer="finn",
            arc=1,
            grade_min=1,
            grade_max=1,
            matrix_seed=0,
            zone=ZoneDepth.SURFACE,
            primary_objective=Objective(type="defeat", count=1),
        )
        state = _make_test_state(with_mission=False)
        state.job_board.add(mission2)
        state.completed_missions.add("first_jack")

        m = mission_completion.get_next_available_mission(state)

        assert m is not None
        assert m.id == "second"


class TestMissionSummary:
    """get_mission_summary() returns human-readable status."""

    def test_no_mission(self) -> None:
        """No current mission returns 'No active mission'."""
        state = AppState()

        summary = mission_completion.get_mission_summary(state)

        assert "No" in summary

    def test_active_mission(self) -> None:
        """Active mission shows progress."""
        state = _make_test_state()
        state.mission_progress = {"extract_data": 0}

        summary = mission_completion.get_mission_summary(state)

        assert "First Jack" in summary
        assert "0/1" in summary


# ============================================================================
# Death screen tests
# ============================================================================


class TestDeath:
    """Death/restart system (Pillar 3: The Flatline)."""

    def test_trigger_death_sets_state(self) -> None:
        """trigger_death() sets is_dead=True and screen=DEATH."""
        state = _make_test_state()

        death_screen.trigger_death(state, reason="ICE breach")

        assert state.is_dead is True
        assert state.death_reason == "ICE breach"
        assert state.screen is ScreenKind.DEATH

    def test_trigger_death_appends_message(self) -> None:
        """Death adds a status message."""
        state = _make_test_state()

        death_screen.trigger_death(state, reason="ICE breach")

        assert any("FLATLINE" in msg for msg in state.status_messages)

    def test_jack_out_resets_hp(self) -> None:
        """Jack out restores HP to max."""
        state = _make_test_state()
        state.player_hp = 0
        state.is_dead = True

        death_screen.jack_out_to_hub(state)

        assert state.player_hp == state.player_max_hp

    def test_jack_out_returns_to_hub(self) -> None:
        """Jack out returns to hub screen."""
        state = _make_test_state()
        state.screen = ScreenKind.DEATH
        state.is_dead = True

        death_screen.jack_out_to_hub(state)

        assert state.screen is ScreenKind.HUB
        assert state.is_dead is False

    def test_jack_out_clears_inventory(self) -> None:
        """Inventory is forfeited on jack out (Pillar 3: current run lost)."""
        state = _make_test_state()
        state.inventory = {"ice_shard": 5, "data_fragment": 3}
        state.is_dead = True

        death_screen.jack_out_to_hub(state)

        assert state.inventory == {}

    def test_jack_out_keeps_credits(self) -> None:
        """Credits are NOT lost (Pillar 3: only current run is lost)."""
        state = _make_test_state()
        state.credits = 1000
        state.is_dead = True

        death_screen.jack_out_to_hub(state)

        # Credits are kept (only inventory is lost)
        assert state.credits == 1000

    def test_jack_out_clears_mission(self) -> None:
        """Current mission is cleared."""
        state = _make_test_state()
        state.is_dead = True

        death_screen.jack_out_to_hub(state)

        assert state.current_mission is None
        assert state.mission_progress == {}

    def test_jack_out_preserves_completed(self) -> None:
        """Completed missions persist (progress not lost)."""
        state = _make_test_state()
        state.completed_missions.add("first_jack")
        state.is_dead = True

        death_screen.jack_out_to_hub(state)

        assert "first_jack" in state.completed_missions

    def test_jack_out_when_alive_no_op(self) -> None:
        """Jack out is no-op if not dead."""
        state = _make_test_state()
        state.inventory = {"key_item": 1}
        state.is_dead = False

        death_screen.jack_out_to_hub(state)

        # Inventory should be preserved
        assert state.inventory == {"key_item": 1}

    def test_jack_out_preserves_grade(self) -> None:
        """Player grade persists (Pillar 3: progress is permanent)."""
        state = _make_test_state()
        state.player_grade = 3
        state.is_dead = True

        death_screen.jack_out_to_hub(state)

        assert state.player_grade == 3


class TestDeathInput:
    """handle_death_input() handles key events on death screen."""

    def _make_event(self, sym: KeySym) -> KeyDown:
        return KeyDown(sym=sym, scancode=Scancode.UP, mod=Modifier.NONE)

    def test_enter_advances_to_death_summary(self) -> None:
        """ENTER on death screen advances to DEATH_SUMMARY (ADR-0040)."""
        state = _make_test_state()
        state.is_dead = True
        state.screen = ScreenKind.DEATH

        event = self._make_event(KeySym.RETURN)
        result = death_screen.handle_death_input(event, state)

        assert result is True
        assert state.screen is ScreenKind.DEATH_SUMMARY

    def test_space_advances_to_death_summary(self) -> None:
        """SPACE on death screen advances to DEATH_SUMMARY (ADR-0040)."""
        state = _make_test_state()
        state.is_dead = True
        state.screen = ScreenKind.DEATH

        event = self._make_event(KeySym.SPACE)
        death_screen.handle_death_input(event, state)

        assert state.screen is ScreenKind.DEATH_SUMMARY

    def test_q_quits(self) -> None:
        """Q on death screen returns False (quit game)."""
        state = _make_test_state()
        state.is_dead = True
        state.screen = ScreenKind.DEATH

        event = self._make_event(KeySym.Q)
        result = death_screen.handle_death_input(event, state)

        assert result is False

    def test_m_toggles_mute(self) -> None:
        """M key toggles mute and shows message."""
        from wet_run.audio import sound_manager

        initial = sound_manager.get_sound_manager().muted
        state = _make_test_state()
        state.is_dead = True
        state.screen = ScreenKind.DEATH

        event = self._make_event(KeySym.M)
        death_screen.handle_death_input(event, state)

        # Verify mute was toggled
        assert sound_manager.get_sound_manager().muted != initial
        # Restore
        sound_manager.get_sound_manager().set_mute(initial)
