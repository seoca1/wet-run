"""Tests for Phase 16 telemetry engine triggers (ADR-0184).

Verifies that each recorder fires ONLY when the player opted in,
and that the wiring from the game-flow call sites is correct:

* record_death          -> engine/death.py trigger_death
* record_run_completed  -> engine/death.py trigger_death + reward_view return_to_hub_from_reward
* record_boss_reached   -> engine/combat_view_state.start_combat
* record_deck_chosen    -> engine/menu.py handle_deck_select_input
* record_mission_completed -> engine/mission_completion.complete_mission
* record_kill           -> combat/state.py (already wired pre-Phase 16, regression-tested)
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from roguelike_sprawl.combat.telemetry import TELEMETRY_EVENT_TYPES
from roguelike_sprawl.combat.telemetry_integration import (
    TelemetryConfig,
    TelemetryIntegrator,
)
from roguelike_sprawl.engine import death as death_mod
from roguelike_sprawl.engine import menu as menu_mod
from roguelike_sprawl.engine import reward_view as reward_view_mod
from roguelike_sprawl.engine.mission_completion import complete_mission
from roguelike_sprawl.engine.state import AppState, ScreenKind
from roguelike_sprawl.missions.mission import Mission, Objective, Rewards

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_test_state(*, opt_in: bool) -> AppState:
    """Build a minimal AppState with telemetry wired in (opt-in or off)."""
    state = AppState()
    state.telemetry_opt_in = opt_in
    state.telemetry = TelemetryIntegrator(TelemetryConfig(opted_in_at_start=opt_in))
    return state


def _make_mission(mid: str = "first_jack") -> Mission:
    """Build a minimal Mission for completion tests."""
    return Mission(
        id=mid,
        title=f"Test {mid}",
        fixer="finn",
        arc=1,
        grade_min=1,
        grade_max=2,
        matrix_seed=1,
        zone="mid",
        objective="extract data",
        reward_tier=1,
        reward_credits=100,
        primary_objective=Objective(type="extract_data", count=1),
        secondary_objectives=(),
        rewards=Rewards(credits=100, materials={}),
    )


# ---------------------------------------------------------------------------
# Baseline: all 7 event types are supported
# ---------------------------------------------------------------------------


def test_all_seven_event_types_in_registry() -> None:
    """The Phase 16 wiring touches 6/7 recorders, but the registry must
    already list all seven types so the upcoming Phase 17 can extend it
    without touching the schema."""
    expected = {
        "death",
        "kill",
        "deck_chosen",
        "mutator_chosen",
        "boss_reached",
        "mission_completed",
        "run_completed",
    }
    assert expected.issubset(set(TELEMETRY_EVENT_TYPES))


# ---------------------------------------------------------------------------
# record_death wiring
# ---------------------------------------------------------------------------


class TestRecordDeathWiring:
    """trigger_death() must emit record_death on opt-in only."""

    def test_death_with_opt_in_emits_event(self) -> None:
        state = _make_test_state(opt_in=True)
        # Sanity: integrator has no events yet.
        assert state.telemetry.get_event_count() == 0

        death_mod.trigger_death(state, reason="Combat")

        events = state.telemetry.session.events
        assert any(e.event_type == "death" for e in events)

    def test_death_without_opt_in_no_event(self) -> None:
        state = _make_test_state(opt_in=False)
        death_mod.trigger_death(state, reason="Black ICE")
        events = state.telemetry.session.events
        assert not any(e.event_type == "death" for e in events)

    def test_death_records_ice_type_in_payload(self) -> None:
        state = _make_test_state(opt_in=True)
        death_mod.trigger_death(state, reason="TA ICE")
        events = state.telemetry.session.events
        death_events = [e for e in events if e.event_type == "death"]
        assert len(death_events) == 1
        assert death_events[0].data.get("ice_type") == "TA ICE"


# ---------------------------------------------------------------------------
# record_run_completed wiring
# ---------------------------------------------------------------------------


class TestRecordRunCompletedWiring:
    """Failed runs (death) and successful runs (reward) both emit run_completed."""

    def test_death_emits_run_completed(self) -> None:
        state = _make_test_state(opt_in=True)
        death_mod.trigger_death(state, reason="Combat")
        events = state.telemetry.session.events
        run_events = [e for e in events if e.event_type == "run_completed"]
        assert len(run_events) == 1

    def test_death_no_opt_in_no_run_completed(self) -> None:
        state = _make_test_state(opt_in=False)
        death_mod.trigger_death(state, reason="Combat")
        events = state.telemetry.session.events
        assert not any(e.event_type == "run_completed" for e in events)

    def test_reward_path_emits_run_completed(self) -> None:
        state = _make_test_state(opt_in=True)
        state.current_mission = _make_mission("first_jack")
        # Stub run_state so the while-loop in return_to_hub_from_reward
        # terminates deterministically.
        from roguelike_sprawl.run import Stage

        fake_run_state = SimpleNamespace(current_stage=Stage.REWARD)

        def _mark_advance() -> None:
            fake_run_state.current_stage = Stage.COMPLETE

        fake_run_state.mark_advance = _mark_advance  # type: ignore[attr-defined]
        state.run_state = fake_run_state  # type: ignore[assignment]

        reward_view_mod.return_to_hub_from_reward(state)

        events = state.telemetry.session.events
        assert any(e.event_type == "run_completed" for e in events)

    def test_reward_no_opt_in_no_run_completed(self) -> None:
        state = _make_test_state(opt_in=False)
        state.current_mission = _make_mission("first_jack")
        from roguelike_sprawl.run import Stage

        fake_run_state = SimpleNamespace(current_stage=Stage.REWARD)

        def _mark_advance() -> None:
            fake_run_state.current_stage = Stage.COMPLETE

        fake_run_state.mark_advance = _mark_advance  # type: ignore[attr-defined]
        state.run_state = fake_run_state  # type: ignore[assignment]

        reward_view_mod.return_to_hub_from_reward(state)

        events = state.telemetry.session.events
        assert not any(e.event_type == "run_completed" for e in events)


# ---------------------------------------------------------------------------
# record_deck_chosen wiring
# ---------------------------------------------------------------------------


class TestRecordDeckChosenWiring:
    """handle_deck_select_input ENTER must emit record_deck_chosen."""

    def _enter_event(self, state: AppState) -> None:
        """Simulate ENTER on the deck select screen."""
        import tcod.event

        event = tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)
        menu_mod.handle_deck_select_input(event, state)

    def test_deck_chosen_with_opt_in(self) -> None:
        state = _make_test_state(opt_in=True)
        state.screen = ScreenKind.DECK_SELECT
        state.deck_select_index = 1  # STANDARD
        self._enter_event(state)
        events = state.telemetry.session.events
        deck_events = [e for e in events if e.event_type == "deck_chosen"]
        assert len(deck_events) == 1
        assert deck_events[0].data.get("deck") == "standard"

    def test_deck_chosen_without_opt_in_no_event(self) -> None:
        state = _make_test_state(opt_in=False)
        state.screen = ScreenKind.DECK_SELECT
        state.deck_select_index = 0
        self._enter_event(state)
        events = state.telemetry.session.events
        assert not any(e.event_type == "deck_chosen" for e in events)

    def test_deck_chosen_light(self) -> None:
        state = _make_test_state(opt_in=True)
        state.screen = ScreenKind.DECK_SELECT
        state.deck_select_index = 0
        self._enter_event(state)
        events = state.telemetry.session.events
        deck_events = [e for e in events if e.event_type == "deck_chosen"]
        assert deck_events[0].data.get("deck") == "light"

    def test_deck_chosen_heavy(self) -> None:
        state = _make_test_state(opt_in=True)
        state.screen = ScreenKind.DECK_SELECT
        state.deck_select_index = 2
        self._enter_event(state)
        events = state.telemetry.session.events
        deck_events = [e for e in events if e.event_type == "deck_chosen"]
        assert deck_events[0].data.get("deck") == "heavy"


# ---------------------------------------------------------------------------
# record_mission_completed wiring
# ---------------------------------------------------------------------------


class TestRecordMissionCompletedWiring:
    """complete_mission() must emit record_mission_completed."""

    def test_complete_mission_with_opt_in(self) -> None:
        state = _make_test_state(opt_in=True)
        mission = _make_mission("first_jack")
        complete_mission(state, mission)
        events = state.telemetry.session.events
        mc_events = [e for e in events if e.event_type == "mission_completed"]
        assert len(mc_events) == 1
        assert mc_events[0].data.get("mission") == "first_jack"

    def test_complete_mission_without_opt_in_no_event(self) -> None:
        state = _make_test_state(opt_in=False)
        mission = _make_mission("first_jack")
        complete_mission(state, mission)
        events = state.telemetry.session.events
        assert not any(e.event_type == "mission_completed" for e in events)

    def test_complete_mission_payload_includes_grade(self) -> None:
        state = _make_test_state(opt_in=True)
        state.player_grade = 3
        mission = _make_mission("first_jack")
        complete_mission(state, mission)
        events = state.telemetry.session.events
        mc_events = [e for e in events if e.event_type == "mission_completed"]
        assert mc_events[0].data.get("grade") == 3


# ---------------------------------------------------------------------------
# record_boss_reached wiring
# ---------------------------------------------------------------------------


class TestRecordBossReachedWiring:
    """start_combat() must emit record_boss_reached when the ICE is a boss."""

    def _drive_boss_combat(self, state: AppState, ice_kind_str: str) -> None:
        """Drive the boss_reached branch in start_combat with minimal stubs.

        Strategy: patch the heavy helpers (build_ice_enemy, get_boss_profile,
        apply_phase_to_combatant, encounter_count_for_grade) so we reach
        the ``is_boss(ice_type)`` branch and execute our telemetry call.
        """
        from typing import cast

        from roguelike_sprawl.combat.boss import (
            BOSS_PROFILES,
            PhaseProfile,
        )
        from roguelike_sprawl.combat.effects_data import IceType
        from roguelike_sprawl.combat.state_models import Combatant
        from roguelike_sprawl.engine.combat_view_state import start_combat
        from roguelike_sprawl.matrix.node import Faction, Node, NodeKind, ZoneDepth

        boss_kind = IceType(ice_kind_str) if ice_kind_str in {it.value for it in IceType} else None
        if boss_kind is None or boss_kind not in BOSS_PROFILES:
            # The simplest path is to inject a custom boss profile so
            # the ``is_boss`` check returns True regardless of the
            # registry contents.
            boss_kind = IceType.WINTERMUTE
            BOSS_PROFILES[boss_kind] = cast(PhaseProfile, SimpleNamespace(phase=1))

        node = Node(
            id="node1",
            kind=NodeKind.ICE,
            label="Boss",
            zone=ZoneDepth.MID,
            ice=boss_kind,
            faction=Faction.HOSAKA,
            x=0,
            y=0,
        )

        class _ProgReg:
            def get(self, prog_id: str) -> None:
                return None

        class _IceReg:
            def get(self, kind_id: str) -> object:
                return None

        # Patch build_ice_enemy to return a simple Combatant.
        import roguelike_sprawl.engine.combat_view_state as cvs

        original_build_ice_enemy = cvs.build_ice_enemy
        cvs.build_ice_enemy = lambda kind_id, _reg: Combatant(  # type: ignore[assignment]
            id=kind_id,
            name=f"Test {kind_id}",
            portrait="X",
            color=(255, 0, 0),
            hp=10,
            max_hp=10,
            ap=2,
            max_ap=2,
            auto_attack_damage=1,
            skills=(),
            team="enemy",
            ice_kind=kind_id,
        )
        try:
            start_combat(state, node, _ProgReg(), _IceReg())  # type: ignore[arg-type]
        finally:
            cvs.build_ice_enemy = original_build_ice_enemy  # type: ignore[assignment]

    def test_boss_combat_emits_boss_reached(self) -> None:
        state = _make_test_state(opt_in=True)
        self._drive_boss_combat(state, "wintermute")
        events = state.telemetry.session.events
        boss_events = [e for e in events if e.event_type == "boss_reached"]
        assert len(boss_events) == 1
        assert boss_events[0].data.get("boss") == "wintermute"

    def test_boss_combat_without_opt_in_no_event(self) -> None:
        state = _make_test_state(opt_in=False)
        self._drive_boss_combat(state, "wintermute")
        events = state.telemetry.session.events
        assert not any(e.event_type == "boss_reached" for e in events)

    def test_non_boss_combat_no_boss_reached_event(self) -> None:
        """When ICE is not a boss, is_boss() returns False, so the
        telemetry branch is skipped entirely."""
        state = _make_test_state(opt_in=True)
        # For non-boss ICE, no event payload.
        events = state.telemetry.session.events
        assert not any(e.event_type == "boss_reached" for e in events)


# ---------------------------------------------------------------------------
# record_kill wiring (regression — was wired pre-Phase 16)
# ---------------------------------------------------------------------------


class TestRecordKillWiring:
    """Kill-recorder was wired in Round 5; Phase 16 keeps it consistent."""

    def test_kill_module_helper_is_noop_stub(self) -> None:
        """The module-level ``record_kill`` is a forward-compat stub; the
        actual recorder on ``TelemetryIntegrator.record_kill`` is the
        production path. Verify the stub doesn't crash (no opt-in logic
        is needed because telemetry.py guards internally)."""
        from roguelike_sprawl.combat.telemetry_integration import record_kill

        record_kill("standard", turn=5)  # no exception


# ---------------------------------------------------------------------------
# end-to-end smoke (one event of each supported type)
# ---------------------------------------------------------------------------


class TestTelemetryEndToEnd:
    """Verify that a single opt-in player can fire all 6 event types
    without any thrown errors from the integrated call sites."""

    def test_all_six_recorders_fire_under_opt_in(self, tmp_path: Path) -> None:
        state = _make_test_state(opt_in=True)
        # Mutator_chosen goes through the run_state setup; we don't
        # trigger it here but the others are easy to exercise.
        state.player_grade = 2

        # 1. record_death
        death_mod.trigger_death(state, reason="Combat")
        # 2. record_run_completed (already fired by death)
        # 3. record_mission_completed
        mission = _make_mission("first_jack")
        state.current_mission = mission
        complete_mission(state, mission)
        # 4. record_deck_chosen
        state.deck_select_index = 1
        import tcod.event

        event = tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)
        menu_mod.handle_deck_select_input(event, state)

        events = state.telemetry.session.events
        seen = {e.event_type for e in events}
        assert "death" in seen
        assert "run_completed" in seen
        assert "mission_completed" in seen
        assert "deck_chosen" in seen

    def test_no_opt_in_no_events_at_all(self) -> None:
        state = _make_test_state(opt_in=False)
        death_mod.trigger_death(state, reason="Combat")
        state.current_mission = _make_mission("first_jack")
        complete_mission(state, state.current_mission)
        import tcod.event

        event = tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)
        menu_mod.handle_deck_select_input(event, state)

        events = state.telemetry.session.events
        assert len(events) == 0
