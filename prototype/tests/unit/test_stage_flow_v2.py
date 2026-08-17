"""Tests for improved stage flow system.

Covers:
- New stages: JACK_OUT, REWARD, DEBRIEF, DEATH_RESTART
- Per-mission flows (first_jack, watchdog_patrol, ice_run)
- Stage validation logic
- RunState progress tracking
- Stage event bus
"""

from __future__ import annotations

from wet_run.run import (
    DEFAULT_FLOW,
    Stage,
    StageEvent,
    StageEventBus,
    StageEventKind,
    advance_stage,
    get_mission_flow,
    get_mission_stage_count,
    get_next_stage_in_flow,
    get_progress_text,
    start_run,
    validate_stage_transition,
)
from wet_run.run.events import get_event_bus, reset_event_bus


class TestNewStages:
    """Verify new stage types exist and are properly configured."""

    def test_jack_out_stage_exists(self) -> None:
        assert Stage.JACK_OUT in DEFAULT_FLOW
        info = DEFAULT_FLOW[Stage.JACK_OUT]
        assert info.title == "Jack Out"
        assert info.next_stage is Stage.REWARD

    def test_reward_stage_exists(self) -> None:
        assert Stage.REWARD in DEFAULT_FLOW
        info = DEFAULT_FLOW[Stage.REWARD]
        assert info.title == "Mission Rewards"
        assert info.next_stage is Stage.COMPLETE

    def test_debrief_stage_exists(self) -> None:
        assert Stage.DEBRIEF in DEFAULT_FLOW
        info = DEFAULT_FLOW[Stage.DEBRIEF]
        assert info.title == "Debrief"

    def test_death_restart_stage_exists(self) -> None:
        assert Stage.DEATH_RESTART in DEFAULT_FLOW
        info = DEFAULT_FLOW[Stage.DEATH_RESTART]
        assert info.title == "Restart"
        assert info.next_stage is Stage.PENDING

    def test_jack_out_has_ascii_art(self) -> None:
        info = DEFAULT_FLOW[Stage.JACK_OUT]
        assert info.ascii_art
        assert any("JACKING OUT" in line for line in info.ascii_art)

    def test_reward_has_ascii_art(self) -> None:
        info = DEFAULT_FLOW[Stage.REWARD]
        assert info.ascii_art
        assert any("MISSION COMPLETE" in line for line in info.ascii_art)


class TestPerMissionFlows:
    """Each mission has its own stage sequence."""

    def test_first_jack_has_extract(self) -> None:
        flow = get_mission_flow("first_jack")
        stages = [info.stage for info in flow]
        assert Stage.EXTRACT_DATA in stages
        assert Stage.MEET_NPC in stages
        assert Stage.DEFEAT_ICE in stages
        assert Stage.JACK_OUT in stages
        assert Stage.REWARD in stages
        assert Stage.COMPLETE in stages

    def test_watchdog_patrol_skips_extract(self) -> None:
        flow = get_mission_flow("watchdog_patrol")
        stages = [info.stage for info in flow]
        assert Stage.EXTRACT_DATA not in stages, "Watchdog Patrol is pure combat"
        assert Stage.MEET_NPC in stages
        assert Stage.DEFEAT_ICE in stages
        assert Stage.JACK_OUT in stages
        assert Stage.REWARD in stages

    def test_ice_run_has_extract(self) -> None:
        flow = get_mission_flow("ice_run")
        stages = [info.stage for info in flow]
        assert Stage.EXTRACT_DATA in stages
        assert Stage.DEFEAT_ICE in stages

    def test_first_jack_order(self) -> None:
        flow = get_mission_flow("first_jack")
        order = [info.stage for info in flow]
        assert order.index(Stage.MEET_NPC) < order.index(Stage.EXTRACT_DATA)
        assert order.index(Stage.EXTRACT_DATA) < order.index(Stage.DEFEAT_ICE)
        assert order.index(Stage.DEFEAT_ICE) < order.index(Stage.JACK_OUT)
        assert order.index(Stage.JACK_OUT) < order.index(Stage.REWARD)
        assert order.index(Stage.REWARD) < order.index(Stage.COMPLETE)

    def test_unknown_mission_falls_back_to_first_jack(self) -> None:
        flow = get_mission_flow("nonexistent_mission")
        expected = get_mission_flow("first_jack")
        assert flow == expected

    def test_mission_stage_count(self) -> None:
        # CONTENT_EXPANSION Phase B: +BRIEFING +TRAVEL → 8 stages
        # (watchdog adds BYPASS_SECURITY → 8 also).
        assert get_mission_stage_count("first_jack") == 8
        assert get_mission_stage_count("watchdog_patrol") == 8
        assert get_mission_stage_count("ice_run") == 8


class TestStageValidation:
    """Stage transitions are validated against mission flow."""

    def test_first_jack_valid_transition_meet_to_extract(self) -> None:
        assert validate_stage_transition(Stage.MEET_NPC, Stage.EXTRACT_DATA, "first_jack")

    def test_first_jack_valid_transition_extract_to_defeat(self) -> None:
        assert validate_stage_transition(Stage.EXTRACT_DATA, Stage.DEFEAT_ICE, "first_jack")

    def test_first_jack_valid_transition_defeat_to_jackout(self) -> None:
        assert validate_stage_transition(Stage.DEFEAT_ICE, Stage.JACK_OUT, "first_jack")

    def test_first_jack_valid_transition_jackout_to_reward(self) -> None:
        assert validate_stage_transition(Stage.JACK_OUT, Stage.REWARD, "first_jack")

    def test_first_jack_valid_transition_reward_to_complete(self) -> None:
        assert validate_stage_transition(Stage.REWARD, Stage.COMPLETE, "first_jack")

    def test_invalid_transition_skip_to_complete(self) -> None:
        """Cannot skip from MEET_NPC directly to COMPLETE in first_jack."""
        assert not validate_stage_transition(Stage.MEET_NPC, Stage.COMPLETE, "first_jack")

    def test_failed_reachable_from_any_in_progress(self) -> None:
        for stage in (Stage.MEET_NPC, Stage.EXTRACT_DATA, Stage.DEFEAT_ICE, Stage.JACK_OUT):
            assert validate_stage_transition(stage, Stage.FAILED, "first_jack")

    def test_failed_not_reachable_from_pending(self) -> None:
        assert not validate_stage_transition(Stage.PENDING, Stage.FAILED, "first_jack")

    def test_failed_not_reachable_from_complete(self) -> None:
        assert not validate_stage_transition(Stage.COMPLETE, Stage.FAILED, "first_jack")

    def test_get_next_stage_in_flow(self) -> None:
        assert get_next_stage_in_flow(Stage.MEET_NPC, "first_jack") is Stage.EXTRACT_DATA
        assert get_next_stage_in_flow(Stage.EXTRACT_DATA, "first_jack") is Stage.DEFEAT_ICE
        assert get_next_stage_in_flow(Stage.COMPLETE, "first_jack") is None

    def test_get_next_stage_unknown_mission(self) -> None:
        """Unknown mission falls back to first_jack flow."""
        assert get_next_stage_in_flow(Stage.MEET_NPC, "unknown") is Stage.EXTRACT_DATA


class TestRunStateProgress:
    """RunState tracks progress through mission stages."""

    def test_initial_state_zero_progress(self) -> None:
        run = start_run("first_jack")
        assert run.stages_completed() == 0
        assert run.stages_total() == 8
        assert run.progress_fraction() == 0.0

    def test_progress_increases_with_advance(self) -> None:
        run = start_run("first_jack")
        run.mark_advance()  # BRIEFING -> TRAVEL
        assert run.stages_completed() == 1
        # In progress on TRAVEL (stage 2 of 8)
        assert run.current_stage is Stage.TRAVEL

    def test_full_run_to_complete(self) -> None:
        run = start_run("first_jack")
        # 8 stages: BRIEFING -> TRAVEL -> MEET_NPC -> EXTRACT_DATA ->
        # DEFEAT_ICE -> JACK_OUT -> REWARD -> COMPLETE
        # 7 mark_advance() calls to traverse all 7 transitions
        for _ in range(7):
            run.mark_advance()
        assert run.current_stage is Stage.COMPLETE
        assert run.stages_completed() == 7
        # Progress: 7 completed out of 8 stages = 7/8
        assert abs(run.progress_fraction() - 7 / 8) < 0.01

    def test_progress_text(self) -> None:
        run = start_run("first_jack")
        run.mark_advance()  # now on TRAVEL (stage 2 of 8)
        run.mark_advance()  # now on MEET_NPC (stage 3 of 8)
        run.mark_advance()  # now on EXTRACT_DATA (stage 4 of 8)
        text = get_progress_text(run)
        assert "Stage 4/8" in text
        assert "Extract the Data" in text

    def test_run_mission_id(self) -> None:
        run = start_run("watchdog_patrol")
        assert run.mission_id == "watchdog_patrol"
        assert run.stages_total() == 8

    def test_advance_stage_helper(self) -> None:
        run = start_run("first_jack")
        new_stage = advance_stage(run)
        assert new_stage is Stage.TRAVEL
        assert run.current_stage is Stage.TRAVEL

    def test_watchdog_skips_extract_on_advance(self) -> None:
        """Watchdog: MEET_NPC -> BYPASS_SECURITY -> DEFEAT_ICE (skip EXTRACT_DATA)."""
        run = start_run("watchdog_patrol")
        # BRIEFING -> TRAVEL -> MEET_NPC -> BYPASS_SECURITY (skip EXTRACT_DATA)
        for _ in range(3):
            run.mark_advance()
        assert run.current_stage is Stage.BYPASS_SECURITY, (
            "Should reach BYPASS_SECURITY (skipping EXTRACT_DATA)"
        )


class TestRunStateLifecycle:
    """RunState lifecycle: reset, terminal states, transitions."""

    def test_reset_clears_state(self) -> None:
        run = start_run("first_jack")
        run.mark_advance()
        run.mark_advance()
        run.mark_failed()
        run.reset("ice_run")
        # CONTENT_EXPANSION Phase B: reset() now starts at BRIEFING
        assert run.current_stage is Stage.BRIEFING
        assert run.completed_stages == ()
        assert run.mission_id == "ice_run"
        assert run.pending_advance is False

    def test_is_complete_at_complete(self) -> None:
        run = start_run("first_jack")
        # 8 stages → 7 mark_advance() to reach COMPLETE
        for _ in range(7):
            run.mark_advance()
        assert run.is_complete()
        assert not run.is_in_progress()
        assert not run.is_in_cyberspace()

    def test_is_complete_at_failed(self) -> None:
        run = start_run("first_jack")
        run.mark_failed()
        assert run.is_complete()

    def test_is_in_cyberspace_for_matrix_stages(self) -> None:
        run = start_run("first_jack")
        for stage in (Stage.MEET_NPC, Stage.EXTRACT_DATA, Stage.DEFEAT_ICE):
            run.current_stage = stage
            assert run.is_in_cyberspace()

    def test_not_in_cyberspace_for_non_matrix_stages(self) -> None:
        run = start_run("first_jack")
        for stage in (Stage.JACK_OUT, Stage.REWARD, Stage.PENDING, Stage.COMPLETE):
            run.current_stage = stage
            assert not run.is_in_cyberspace()

    def test_mark_failed_after_complete_is_noop(self) -> None:
        run = start_run("first_jack")
        for _ in range(7):
            run.mark_advance()
        assert run.current_stage is Stage.COMPLETE
        before = run.completed_stages
        run.mark_failed()
        assert run.current_stage is Stage.COMPLETE
        assert run.completed_stages == before

    def test_mark_advance_documents_intentional_non_idempotency(self) -> None:
        """mark_advance() is NOT idempotent by design.

        Calling twice advances twice (records the same stage twice in
        completed_stages). Call sites must gate the call with check
        helpers (e.g. is_complete). This test documents the behavior
        so regressions are caught if it changes accidentally.
        """
        run = start_run("first_jack")
        # Start: BRIEFING (initial)
        assert run.current_stage is Stage.BRIEFING
        # First mark_advance: BRIEFING → TRAVEL
        run.mark_advance()
        assert run.current_stage is Stage.TRAVEL
        first_advance_count = len(run.completed_stages)
        # Double-call (bug scenario): advances again from TRAVEL
        run.mark_advance()
        # Confirms non-idempotent behavior: stage recorded twice
        assert len(run.completed_stages) == first_advance_count + 1
        # Site must guard with check before calling

    def test_death_restart_transition(self) -> None:
        run = start_run("first_jack")
        run.mark_failed()
        run.mark_death_restart()
        assert run.current_stage is Stage.DEATH_RESTART
        assert run.pending_advance is True

    def test_advance_to_jack_out(self) -> None:
        run = start_run("first_jack")
        # BRIEFING -> TRAVEL -> MEET_NPC -> EXTRACT_DATA -> DEFEAT_ICE -> JACK_OUT
        for _ in range(5):
            run.mark_advance()
        assert run.current_stage is Stage.JACK_OUT

    def test_advance_to_reward_after_jackout(self) -> None:
        run = start_run("first_jack")
        # ... -> JACK_OUT (5 advances from BRIEFING)
        for _ in range(5):
            run.mark_advance()
        # JACK_OUT -> REWARD
        run.mark_advance()
        assert run.current_stage is Stage.REWARD


class TestStageEventBus:
    """Stage event bus for hooks."""

    def setup_method(self) -> None:
        reset_event_bus()

    def test_subscribe_and_emit(self) -> None:
        bus = StageEventBus()
        received: list[StageEvent] = []

        def handler(event: StageEvent) -> None:
            received.append(event)

        bus.subscribe(handler)
        run = start_run("first_jack")
        event = StageEvent(
            kind=StageEventKind.ENTER,
            run_state=run,
            from_stage=None,
            to_stage=Stage.MEET_NPC,
        )
        bus.emit(event)
        assert len(received) == 1
        assert received[0].kind is StageEventKind.ENTER

    def test_subscribe_by_kind(self) -> None:
        bus = StageEventBus()
        enter_count = [0]
        exit_count = [0]

        bus.subscribe_kind(
            StageEventKind.ENTER, lambda e: enter_count.__setitem__(0, enter_count[0] + 1)
        )
        bus.subscribe_kind(
            StageEventKind.EXIT, lambda e: exit_count.__setitem__(0, exit_count[0] + 1)
        )

        run = start_run("first_jack")
        bus.emit(StageEvent(StageEventKind.ENTER, run, None, Stage.MEET_NPC))
        bus.emit(StageEvent(StageEventKind.EXIT, run, Stage.MEET_NPC, Stage.EXTRACT_DATA))
        bus.emit(StageEvent(StageEventKind.ENTER, run, Stage.MEET_NPC, Stage.EXTRACT_DATA))

        assert enter_count[0] == 2
        assert exit_count[0] == 1

    def test_subscribe_by_stage(self) -> None:
        bus = StageEventBus()
        meet_npc_count = [0]

        bus.subscribe_stage(
            StageEventKind.ENTER,
            Stage.MEET_NPC,
            lambda e: meet_npc_count.__setitem__(0, meet_npc_count[0] + 1),
        )

        run = start_run("first_jack")
        bus.emit(StageEvent(StageEventKind.ENTER, run, None, Stage.MEET_NPC))
        bus.emit(StageEvent(StageEventKind.ENTER, run, Stage.MEET_NPC, Stage.EXTRACT_DATA))

        assert meet_npc_count[0] == 1

    def test_handler_exception_does_not_break_flow(self) -> None:
        bus = StageEventBus()
        after_called = [False]

        def bad_handler(event: StageEvent) -> None:
            raise RuntimeError("oops")

        def good_handler(event: StageEvent) -> None:
            after_called[0] = True

        bus.subscribe(bad_handler)
        bus.subscribe(good_handler)
        run = start_run("first_jack")
        bus.emit(StageEvent(StageEventKind.ENTER, run, None, Stage.MEET_NPC))
        assert after_called[0]

    def test_unsubscribe(self) -> None:
        bus = StageEventBus()
        count = [0]

        def h(event: StageEvent) -> None:
            count[0] += 1

        bus.subscribe(h)
        bus.unsubscribe(h)
        bus.emit(StageEvent(StageEventKind.ENTER, start_run(), None, Stage.MEET_NPC))
        assert count[0] == 0

    def test_clear_removes_all(self) -> None:
        bus = StageEventBus()
        bus.subscribe(lambda e: None)
        bus.subscribe_kind(StageEventKind.ENTER, lambda e: None)
        bus.subscribe_stage(StageEventKind.EXIT, Stage.MEET_NPC, lambda e: None)
        bus.clear()
        assert not bus._global_handlers
        assert not bus._kind_handlers
        assert not bus._stage_handlers

    def test_default_bus_singleton(self) -> None:
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2


class TestStageInfoMetadata:
    """StageInfo has rich metadata for UI/sound/narrative."""

    def test_combat_stage_has_on_enter(self) -> None:
        info = DEFAULT_FLOW[Stage.DEFEAT_ICE]
        assert info.on_enter
        assert "ICE" in info.on_enter

    def test_jack_out_has_ascii(self) -> None:
        info = DEFAULT_FLOW[Stage.JACK_OUT]
        assert info.ascii_art
        assert len(info.ascii_art) >= 3

    def test_all_stages_have_title_and_hint(self) -> None:
        for stage in Stage:
            info = DEFAULT_FLOW[stage]
            assert info.title, f"{stage} missing title"
            assert info.hint, f"{stage} missing hint"


class TestFullRunFlow:
    """End-to-end: simulate a full run through all stages."""

    def test_first_jack_full_run(self) -> None:
        run = start_run("first_jack")
        # CONTENT_EXPANSION Phase B: 8 stages total, 7 advances to reach COMPLETE
        for _ in range(7):
            run.mark_advance()

        assert run.current_stage is Stage.COMPLETE
        # 7 transitions = 7 completed stages (COMPLETE itself isn't in completed)
        assert run.stages_completed() == 7
        assert Stage.BRIEFING in run.completed_stages
        assert Stage.TRAVEL in run.completed_stages
        assert Stage.MEET_NPC in run.completed_stages
        assert Stage.JACK_OUT in run.completed_stages
        assert Stage.REWARD in run.completed_stages

    def test_watchdog_patrol_shorter_flow(self) -> None:
        run = start_run("watchdog_patrol")
        # 8 stages (with BYPASS_SECURITY replacing EXTRACT_DATA)
        # 7 mark_advance() calls to reach COMPLETE
        for _ in range(7):
            run.mark_advance()
        assert run.current_stage is Stage.COMPLETE
        assert run.stages_completed() == 7
        assert Stage.EXTRACT_DATA not in run.completed_stages
        assert Stage.BYPASS_SECURITY in run.completed_stages

    def test_failure_mid_run(self) -> None:
        run = start_run("first_jack")
        run.mark_advance()  # MEET_NPC -> EXTRACT_DATA
        run.mark_failed()  # -> FAILED
        assert run.current_stage is Stage.FAILED
        assert run.is_complete()
        # DEATH_RESTART flow
        run.mark_death_restart()
        assert run.current_stage is Stage.DEATH_RESTART


class TestDataDrivenStageFlow:
    """Phase J: stage_flow declared in missions.json (C-1 implementation)."""

    def test_first_jack_flow_from_mission_data(self) -> None:
        """get_mission_flow() reads stage_flow from mission JSON."""
        import json
        from pathlib import Path

        from wet_run.run.state import get_mission_flow

        # Load missions.json
        missions_path = Path(__file__).resolve().parents[2] / "data" / "missions" / "missions.json"
        with missions_path.open() as f:
            data = json.load(f)

        flow = get_mission_flow("first_jack", data)
        stage_values = [s.stage.value for s in flow]
        assert "briefing" in stage_values
        assert "extract_data" in stage_values
        assert "defeat_ice" in stage_values
        assert "complete" in stage_values
        assert len(flow) == 8

    def test_watchdog_patrol_uses_bypass_security(self) -> None:
        """watchdog_patrol flow uses BYPASS_SECURITY (not EXTRACT_DATA)."""
        import json
        from pathlib import Path

        from wet_run.run.state import get_mission_flow

        missions_path = Path(__file__).resolve().parents[2] / "data" / "missions" / "missions.json"
        with missions_path.open() as f:
            data = json.load(f)

        flow = get_mission_flow("watchdog_patrol", data)
        stage_values = [s.stage.value for s in flow]
        assert "bypass_security" in stage_values
        assert "extract_data" not in stage_values

    def test_data_retrieval_uses_black_market(self) -> None:
        """data_retrieval flow uses BLACK_MARKET stage (special variant)."""
        import json
        from pathlib import Path

        from wet_run.run.state import get_mission_flow

        missions_path = Path(__file__).resolve().parents[2] / "data" / "missions" / "missions.json"
        with missions_path.open() as f:
            data = json.load(f)

        flow = get_mission_flow("data_retrieval", data)
        stage_values = [s.stage.value for s in flow]
        assert "black_market" in stage_values
        assert "extract_data" in stage_values

    def test_fallback_to_first_jack(self) -> None:
        """Mission without stage_flow falls back to first_jack's flow."""
        import json
        from pathlib import Path

        from wet_run.run.state import get_mission_flow

        missions_path = Path(__file__).resolve().parents[2] / "data" / "missions" / "missions.json"
        with missions_path.open() as f:
            data = json.load(f)

        # ice_run (different id, has stage_flow in JSON)
        flow = get_mission_flow("ice_run", data)
        stage_values = [s.stage.value for s in flow]
        # ice_run uses same flow as first_jack
        assert stage_values == [
            "briefing",
            "travel",
            "meet_npc",
            "extract_data",
            "defeat_ice",
            "jack_out",
            "reward",
            "complete",
        ]
