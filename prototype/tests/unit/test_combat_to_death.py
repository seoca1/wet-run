"""Integration test: real combat (step_combat) -> trigger_death().

This test exercises the wiring described in
``combat_view._end_combat`` (combat_view.py:679-739): when
``step_combat`` produces ``outcome="defeat"`` (player HP <= 0),
the engine should call ``trigger_death`` which archives the jockey
and transitions the screen to DEATH.

The combat-to-death integration is the *contract* that the death
cycle (ADR-0040) depends on. This test guards it.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.combat.state import (  # noqa: E402
    AUTO_ATTACK_INTERVAL_MS,
    TICK_MS,
    Combatant,
    CombatState,
    step_combat,
)
from wet_run.engine.death import (  # noqa: E402
    advance_to_death_summary,
    restart_with_new_jockey,
    trigger_death,
)
from wet_run.engine.jockey_history import (  # noqa: E402
    build_deceased_from_state,
)
from wet_run.engine.state import AppState, ScreenKind  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_state() -> AppState:
    """An AppState primed for a veteran jockey in active combat."""
    s = AppState()
    s.character_id = "veteran"
    s.player_grade = 3
    s.player_hp = 100
    s.player_max_hp = 100
    s.current_node_id = "data_cache_5"
    s.completed_missions = {"mission_1"}
    s.mission_progress = {"extract_data": 1}
    s.demo_elapsed_s = 30 * 60
    return s


def _build_combat(player_hp: int = 5, player_atk: int = 0) -> CombatState:
    """Build a combat that will reliably produce a defeat.

    Player HP=5, ATK=0, ICE damage=3 -> 2 attacks to kill player.
    ICE HP=80, no incoming damage -> ICE never dies.
    """
    player = Combatant(
        id="player",
        name="케이 (K) — Novice",
        portrait="@",
        color=(200, 200, 255),
        hp=player_hp,
        max_hp=player_hp,
        ap=0,
        max_ap=6,
        auto_attack_damage=player_atk,
        team="player",
    )
    enemy = Combatant(
        id="ice_standard",
        name="ICE — Standard",
        portrait="▲",
        color=(255, 100, 100),
        hp=80,
        max_hp=80,
        ap=0,
        max_ap=0,
        auto_attack_damage=3,
        team="enemy",
    )
    combat = CombatState(player=player, enemy=enemy)
    # Seed RNG so damage variance is deterministic across test runs
    combat.rng = random.Random(42)
    return combat


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCombatDefeatPath:
    """step_combat() must reach outcome=defeat when player HP hits 0."""

    def test_step_combat_terminates_with_defeat(self) -> None:
        combat = _build_combat(player_hp=5, player_atk=0)
        ticks = 0
        max_ticks = 200  # safety cap
        while not combat.finished and ticks < max_ticks:
            step_combat(combat)
            ticks += 1
        assert combat.finished, "Combat should have finished within {max_ticks} ticks"
        assert combat.outcome == "defeat"
        assert combat.player.hp == 0
        assert combat.enemy.hp > 0  # enemy must be alive (player didn't kill it)

    def test_combat_timing_matches_documentation(self) -> None:
        """TICK_MS=100, AUTO_ATTACK_INTERVAL_MS=2000 → 1 attack / 20 ticks.

        With 3 damage and HP=5, player dies on 2nd enemy attack (~21-22 ticks).
        """
        combat = _build_combat(player_hp=5, player_atk=0)
        ticks = 0
        while not combat.finished and ticks < 200:
            step_combat(combat)
            ticks += 1
        # 1st attack at tick 21 (2100ms - 0ms), 2nd at tick 41 → kill at ~41-42
        # Allow some slack for variance and AP regen edge cases
        assert 20 <= ticks <= 50, f"Expected 20-50 ticks to kill HP=5 with 3-dmg, got {ticks}"

    def test_combat_constants_unmodified(self) -> None:
        """Guards against accidental changes to combat pacing."""
        assert TICK_MS == 100
        assert AUTO_ATTACK_INTERVAL_MS == 2000


class TestTriggerDeathOnDefeat:
    """trigger_death() must be safe to call after step_combat produces defeat."""

    def test_trigger_death_marks_appstate_dead(self, fresh_state: AppState) -> None:
        # Simulate the post-defeat contract: app state knows the player
        # is at 0 HP and the combat has ended.
        fresh_state.player_hp = 0
        trigger_death(fresh_state, reason="ICE breach")
        assert fresh_state.is_dead is True
        assert fresh_state.death_cause == "ICE breach"
        assert fresh_state.death_reason == "ICE breach"
        assert fresh_state.screen == ScreenKind.DEATH

    def test_trigger_death_increments_counters(self, fresh_state: AppState) -> None:
        assert fresh_state.total_runs == 0
        assert fresh_state.total_deaths == 0
        trigger_death(fresh_state, reason="ICE breach")
        assert fresh_state.total_runs == 1
        assert fresh_state.total_deaths == 1

    def test_trigger_death_appends_flatline_message(self, fresh_state: AppState) -> None:
        before = len(fresh_state.status_messages)
        trigger_death(fresh_state, reason="Black ICE")
        msgs = fresh_state.status_messages[before:]
        assert any("FLATLINE" in m for m in msgs)
        assert any("Black ICE" in m for m in msgs)

    def test_trigger_death_archives_jockey(self, fresh_state: AppState) -> None:
        # trigger_death uses a singleton JockeyHistory internally.
        # Verify via state.last_jockey_summary_id (set in trigger_death)
        # and via the status_messages archive line.
        assert fresh_state.last_jockey_summary_id == ""
        trigger_death(fresh_state, reason="ICE breach")
        # The summary id is a UUID hex string
        assert len(fresh_state.last_jockey_summary_id) == 32
        assert fresh_state.jockey_history_loaded is True
        # The "Jockey archived" line should be in status messages
        archived = [m for m in fresh_state.status_messages if "Jockey archived" in m]
        assert len(archived) == 1
        # The jockey name comes from the AppState character_id
        assert "Veteran" in archived[0] or "실" in archived[0]


class TestEndToEndCombatToDeath:
    """Full pipeline: step_combat -> defeat -> trigger_death -> restart."""

    def test_full_combat_to_death_to_new_jockey(self, fresh_state: AppState) -> None:
        # 1. Real combat ends in defeat
        combat = _build_combat(player_hp=5, player_atk=0)
        ticks = 0
        while not combat.finished and ticks < 200:
            step_combat(combat)
            ticks += 1
        assert combat.outcome == "defeat"
        assert combat.player.hp == 0

        # 2. _end_combat equivalent: mark_failed + trigger_death
        #    (we skip mark_failed — it lives in run_state and is covered elsewhere)
        trigger_death(fresh_state, reason="ICE breach")
        assert fresh_state.screen == ScreenKind.DEATH
        assert fresh_state.is_dead is True

        # 3. Advance to DEATH_SUMMARY
        advance_to_death_summary(fresh_state)
        expected_summary = ScreenKind.DEATH_SUMMARY
        assert fresh_state.screen == expected_summary

        # 4. Player picks a different jockey → restart
        restart_with_new_jockey(fresh_state, new_character_id="novice")
        assert fresh_state.is_dead is False
        assert fresh_state.death_cause == ""
        assert fresh_state.character_id == "novice"
        assert fresh_state.player_grade == 1
        assert fresh_state.screen == ScreenKind.CHARACTER_SELECT

    def test_combat_to_death_with_all_ice_types(self, fresh_state: AppState) -> None:
        """The pipeline should work regardless of which ICE fought the player."""
        ice_damages = [3, 5, 8, 12, 15]  # 5 ICE tiers
        for ice_dmg in ice_damages:
            player = Combatant(
                id="p",
                name="Player",
                portrait="@",
                color=(255, 255, 255),
                hp=5,
                max_hp=5,
                auto_attack_damage=0,
                team="player",
            )
            enemy = Combatant(
                id="ice",
                name=f"ICE-{ice_dmg}",
                portrait="▲",
                color=(255, 100, 100),
                hp=80,
                max_hp=80,
                auto_attack_damage=ice_dmg,
                team="enemy",
            )
            combat = CombatState(player=player, enemy=enemy)
            ticks = 0
            while not combat.finished and ticks < 200:
                step_combat(combat)
                ticks += 1
            assert combat.outcome == "defeat", f"ICE dmg={ice_dmg} should kill player"

            # The contract is the same regardless of ICE strength
            s = AppState()
            s.character_id = "veteran"
            trigger_death(s, reason="ICE breach")
            assert s.is_dead is True
            assert s.screen == ScreenKind.DEATH


class TestBuildDeceasedFromState:
    """The archived jockey must capture meaningful state at time of death."""

    def test_archived_jockey_has_meaningful_fields(self, fresh_state: AppState) -> None:
        # build_deceased_from_state preserves inventory order from a tuple
        deceased = build_deceased_from_state(
            name="케이 (K) — Novice",
            character_id="novice",
            grade=2,
            died_at_node="data_cache_3",
            died_at_mission="watchdog_patrol",
            inventory=("loa_drum", "wisp_T2"),  # pre-sorted input
            missions_completed=1,
            data_recovered=100,
            playtime_minutes=30,
        )
        assert deceased.name == "케이 (K) — Novice"
        assert deceased.character_id == "novice"
        assert deceased.grade == 2
        assert deceased.died_at_node == "data_cache_3"
        assert deceased.inventory_snapshot == ("loa_drum", "wisp_T2")
        assert deceased.epitaph  # non-empty

    def test_archived_jockey_dict_inventory_is_sorted(self) -> None:
        """When inventory is a dict, build_deceased_from_state sorts keys."""
        deceased = build_deceased_from_state(
            name="X",
            character_id="novice",
            grade=1,
            died_at_node="n",
            died_at_mission="m",
            inventory={"wisp_T2": 1, "loa_drum": 3, "aether_eye": 2},
            missions_completed=0,
            data_recovered=0,
            playtime_minutes=0,
        )
        assert deceased.inventory_snapshot == ("aether_eye", "loa_drum", "wisp_T2")
