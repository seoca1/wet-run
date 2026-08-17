"""Tests for post-combat screens: JACK_OUT, REWARD, DEBRIEF.

Verifies:
- enter_jack_out / advance_to_reward
- enter_reward / return_to_hub_from_reward
- enter_debrief / advance_from_debrief
- Input handlers (ENTER advances, Q quits, ESC quits)
- Reward award logic
- State transitions (run_state + screen)
"""

from __future__ import annotations

import time

import tcod.event

from wet_run.engine import debrief_view, jack_out_view, reward_view
from wet_run.engine.state import AppState, ScreenKind
from wet_run.matrix.node import ZoneDepth
from wet_run.missions.mission import Mission, Rewards
from wet_run.run import Stage, start_run


def _make_mission(rewards: Rewards | None = None) -> Mission:
    """Helper to create a minimal valid Mission for tests."""
    return Mission(
        id="test_mission",
        title="Test Mission",
        fixer="finn",
        arc=1,
        grade_min=1,
        grade_max=1,
        matrix_seed=42,
        zone=ZoneDepth.SURFACE,
        rewards=rewards,
    )


def _state() -> AppState:
    """Fresh AppState with active run."""
    s = AppState()
    s.inventory = {}
    s.credits = 0
    s.run_state = start_run("first_jack")
    s.run_state.current_stage = Stage.JACK_OUT
    return s


# --- Jack Out ---


class TestJackOutEnter:
    """enter_jack_out transitions to JACK_OUT screen."""

    def test_sets_screen(self) -> None:
        state = _state()
        state.screen = ScreenKind.MATRIX
        jack_out_view.enter_jack_out(state)
        assert state.screen is ScreenKind.JACK_OUT

    def test_sets_animation_state(self) -> None:
        state = _state()
        before = time.monotonic()
        jack_out_view.enter_jack_out(state)
        assert state.jack_out_started_at >= before
        assert state.jack_out_frame_index == 0

    def test_appends_status_message(self) -> None:
        state = _state()
        before_count = len(state.status_messages)
        jack_out_view.enter_jack_out(state)
        assert len(state.status_messages) > before_count
        assert any("Jacking out" in m for m in state.status_messages)


class TestJackOutAdvance:
    """advance_to_reward moves from JACK_OUT to REWARD."""

    def test_advances_run_state(self) -> None:
        state = _state()
        assert state.run_state.current_stage is Stage.JACK_OUT
        jack_out_view.advance_to_reward(state)
        assert state.run_state.current_stage is Stage.REWARD

    def test_swaps_to_reward_screen(self) -> None:
        state = _state()
        jack_out_view.advance_to_reward(state)
        assert state.screen is ScreenKind.REWARD

    def test_no_op_if_not_jack_out(self) -> None:
        state = _state()
        state.run_state.current_stage = Stage.MEET_NPC
        state.screen = ScreenKind.MATRIX
        jack_out_view.advance_to_reward(state)
        assert state.run_state.current_stage is Stage.MEET_NPC
        assert state.screen is ScreenKind.MATRIX

    def test_no_op_if_no_run_state(self) -> None:
        state = AppState()
        state.run_state = None
        # Should not crash
        jack_out_view.advance_to_reward(state)


class TestJackOutInput:
    """handle_jack_out_input dispatches key events."""

    def test_enter_advances_when_animation_done(self) -> None:
        state = _state()
        # Pretend animation finished
        state.jack_out_started_at = time.monotonic() - 10.0
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)
        result = jack_out_view.handle_jack_out_input(event, state)
        assert result is True
        assert state.run_state.current_stage is Stage.REWARD

    def test_enter_blocked_during_animation(self) -> None:
        state = _state()
        # Animation just started
        state.jack_out_started_at = time.monotonic()
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)
        jack_out_view.handle_jack_out_input(event, state)
        # Should not advance
        assert state.run_state.current_stage is Stage.JACK_OUT

    def test_q_quits(self) -> None:
        state = _state()
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.Q, mod=0, scancode=0)
        result = jack_out_view.handle_jack_out_input(event, state)
        assert result is False

    def test_escape_quits(self) -> None:
        state = _state()
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.ESCAPE, mod=0, scancode=0)
        result = jack_out_view.handle_jack_out_input(event, state)
        assert result is False

    def test_other_keys_ignored(self) -> None:
        state = _state()
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.A, mod=0, scancode=0)
        result = jack_out_view.handle_jack_out_input(event, state)
        assert result is True


# --- Reward ---


class TestRewardEnter:
    """enter_reward transitions to REWARD and awards credits/materials."""

    def test_awards_credits(self) -> None:
        state = _state()
        state.current_mission = _make_mission(
            rewards=Rewards(credits=500, materials={"data_fragment": 2})
        )
        state.credits = 100
        reward_view.enter_reward(state)
        assert state.credits == 600
        assert any("+500 credits" in m for m in state.status_messages)

    def test_awards_materials(self) -> None:
        state = _state()
        state.current_mission = _make_mission(
            rewards=Rewards(credits=0, materials={"ice_shard": 3, "data_fragment": 1})
        )
        state.inventory = {}
        reward_view.enter_reward(state)
        assert state.inventory.get("ice_shard") == 3
        assert state.inventory.get("data_fragment") == 1
        assert any("+3x ice_shard" in m for m in state.status_messages)

    def test_no_mission_no_rewards(self) -> None:
        state = _state()
        state.current_mission = None
        state.credits = 100
        reward_view.enter_reward(state)
        assert state.credits == 100

    def test_mission_without_rewards(self) -> None:
        state = _state()
        state.current_mission = _make_mission(rewards=None)
        state.credits = 100
        reward_view.enter_reward(state)
        assert state.credits == 100

    def test_sets_screen(self) -> None:
        state = _state()
        reward_view.enter_reward(state)
        assert state.screen is ScreenKind.REWARD


class TestRewardReturnToHub:
    """return_to_hub_from_reward advances state and returns to Hub."""

    def test_advances_to_complete(self) -> None:
        state = _state()
        state.current_mission = _make_mission()
        reward_view.enter_reward(state)
        reward_view.return_to_hub_from_reward(state)
        # After return_to_hub, run_state is reset to BRIEFING for next
        # run (CONTENT_EXPANSION Phase B; was MEET_NPC).
        assert state.run_state.current_stage is Stage.BRIEFING
        # But mission is marked completed
        assert "test_mission" in state.completed_missions

    def test_marks_mission_completed(self) -> None:
        state = _state()
        state.current_mission = _make_mission()
        reward_view.return_to_hub_from_reward(state)
        assert "test_mission" in state.completed_missions

    def test_clears_matrix_state(self) -> None:
        state = _state()

        # Use a real mock-like object — MagicMock is overkill
        class FakeMatrix:
            pass

        state.matrix = FakeMatrix()
        state.current_node_id = "x1"
        state.cyberspace_layouts = {"x": 1}
        reward_view.return_to_hub_from_reward(state)
        assert state.matrix is None
        assert state.current_node_id is None
        assert state.cyberspace_layouts is None

    def test_resets_mission(self) -> None:
        state = _state()
        state.current_mission = _make_mission()
        state.mission_progress = {"extract_data": 1}
        reward_view.return_to_hub_from_reward(state)
        assert state.current_mission is None
        assert state.mission_progress == {}

    def test_switches_to_hub(self) -> None:
        state = _state()
        reward_view.return_to_hub_from_reward(state)
        assert state.screen is ScreenKind.HUB


class TestRewardInput:
    """handle_reward_input dispatches key events."""

    def test_enter_returns_to_hub(self) -> None:
        state = _state()
        state.current_mission = _make_mission()
        reward_view.enter_reward(state)
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)
        result = reward_view.handle_reward_input(event, state)
        assert result is True
        assert state.screen is ScreenKind.HUB

    def test_q_quits(self) -> None:
        state = _state()
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.Q, mod=0, scancode=0)
        result = reward_view.handle_reward_input(event, state)
        assert result is False

    def test_escape_quits(self) -> None:
        state = _state()
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.ESCAPE, mod=0, scancode=0)
        result = reward_view.handle_reward_input(event, state)
        assert result is False

    def test_space_also_advances(self) -> None:
        state = _state()
        state.current_mission = _make_mission()
        reward_view.enter_reward(state)
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.SPACE, mod=0, scancode=0)
        reward_view.handle_reward_input(event, state)
        assert state.screen is ScreenKind.HUB


# --- Debrief ---


class TestDebriefEnter:
    """enter_debrief transitions to DEBRIEF screen."""

    def test_sets_screen(self) -> None:
        state = AppState()
        debrief_view.enter_debrief(state, character="novice")
        assert state.screen is ScreenKind.DEBRIEF

    def test_sets_character(self) -> None:
        state = AppState()
        debrief_view.enter_debrief(state, character="veteran")
        assert state.debrief_character == "veteran"

    def test_index_starts_at_zero(self) -> None:
        state = AppState()
        debrief_view.enter_debrief(state)
        assert state.debrief_index == 0

    def test_unknown_character_falls_back(self) -> None:
        state = AppState()
        debrief_view.enter_debrief(state, character="unknown")
        assert state.debrief_character == "unknown"


class TestDebriefAdvance:
    """advance_from_debrief moves to next stage."""

    def test_advances_run_state(self) -> None:
        state = AppState()
        state.run_state = start_run("first_jack")
        state.run_state.current_stage = Stage.DEBRIEF
        debrief_view.enter_debrief(state)
        debrief_view.advance_from_debrief(state)
        assert state.run_state.current_stage is Stage.COMPLETE

    def test_clears_matrix(self) -> None:
        state = AppState()
        state.run_state = start_run("first_jack")
        state.run_state.current_stage = Stage.DEBRIEF

        class FakeMatrix:
            pass

        state.matrix = FakeMatrix()
        state.current_node_id = "x"
        state.cyberspace_layouts = {"x": 1}
        state.in_server_browser = False
        debrief_view.enter_debrief(state)
        debrief_view.advance_from_debrief(state)
        assert state.matrix is None
        assert state.cyberspace_layouts is None
        assert state.in_server_browser is True

    def test_switches_to_hub(self) -> None:
        state = AppState()
        state.run_state = start_run("first_jack")
        state.run_state.current_stage = Stage.DEBRIEF
        debrief_view.enter_debrief(state)
        debrief_view.advance_from_debrief(state)
        assert state.screen is ScreenKind.HUB

    def test_no_op_if_not_debrief(self) -> None:
        state = AppState()
        state.run_state = start_run("first_jack")
        state.run_state.current_stage = Stage.MEET_NPC
        state.screen = ScreenKind.MATRIX
        debrief_view.advance_from_debrief(state)
        assert state.run_state.current_stage is Stage.MEET_NPC
        assert state.screen is ScreenKind.MATRIX


class TestDebriefInput:
    """handle_debrief_input dispatches key events."""

    def test_any_key_advances(self) -> None:
        state = AppState()
        state.run_state = start_run("first_jack")
        state.run_state.current_stage = Stage.DEBRIEF
        debrief_view.enter_debrief(state)
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.SPACE, mod=0, scancode=0)
        result = debrief_view.handle_debrief_input(event, state)
        assert result is True
        assert state.screen is ScreenKind.HUB

    def test_q_quits(self) -> None:
        state = AppState()
        state.run_state = start_run("first_jack")
        state.run_state.current_stage = Stage.DEBRIEF
        debrief_view.enter_debrief(state)
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.Q, mod=0, scancode=0)
        result = debrief_view.handle_debrief_input(event, state)
        assert result is False


# --- End-to-End ---


class TestJackOutToRewardFlow:
    """End-to-end: JACK_OUT → REWARD → Hub flow."""

    def test_full_flow(self) -> None:
        state = AppState()
        state.inventory = {}
        state.credits = 0
        state.run_state = start_run("first_jack")
        # CONTENT_EXPANSION Phase B: simulate being mid-run at DEFEAT_ICE
        # (start at BRIEFING then advance to DEFEAT_ICE: 4 advances).
        for _ in range(4):
            state.run_state.mark_advance()
        assert state.run_state.current_stage is Stage.DEFEAT_ICE

        # Set mission BEFORE the flow so rewards can be awarded
        state.current_mission = _make_mission(
            rewards=Rewards(credits=300, materials={"data_fragment": 1})
        )

        # 1. DEFEAT_ICE victory → mark_advance → JACK_OUT
        state.run_state.mark_advance()
        assert state.run_state.current_stage is Stage.JACK_OUT

        # 2. Enter JACK_OUT screen
        jack_out_view.enter_jack_out(state)
        assert state.screen is ScreenKind.JACK_OUT

        # 3. Skip animation, dismiss
        state.jack_out_started_at = time.monotonic() - 10.0
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)
        jack_out_view.handle_jack_out_input(event, state)

        # 4. Should be on REWARD screen with credits awarded
        assert state.run_state.current_stage is Stage.REWARD
        assert state.screen is ScreenKind.REWARD
        assert state.credits == 300  # Awarded on entering REWARD

        # 5. Press ENTER to return to hub
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)
        reward_view.handle_reward_input(event, state)

        # 6. Should be back at Hub
        # Note: return_to_hub_from_reward resets run_state to fresh BRIEFING
        # (Phase B; was MEET_NPC) for the next run; check mission completion.
        assert state.screen is ScreenKind.HUB
        assert state.credits == 300
        assert "test_mission" in state.completed_missions
        # CONTENT_EXPANSION Phase B: return_to_hub now resets to BRIEFING
        assert state.run_state.current_stage is Stage.BRIEFING
