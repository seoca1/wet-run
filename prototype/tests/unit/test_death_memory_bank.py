"""Tests for the Death cycle → Construct Memory Bank hook (Phase 51+).

Verifies that when a jockey flatlines, a single MemoryFragment
is persisted to AppState.memory_bank with the right arc
(derived from the current mission, or 1 if no mission) and
a string that includes the death reason.
"""

from __future__ import annotations

import time

import pytest

from wet_run.engine.death import trigger_death
from wet_run.engine.state import AppState
from wet_run.matrix.node import ZoneDepth
from wet_run.missions.mission import Mission
from wet_run.run.memory_bank import MAX_FRAGMENTS


@pytest.fixture
def app_state() -> AppState:
    return AppState()


class TestDeathPersistsMemoryFragment:
    def test_single_fragment_after_first_death(self, app_state: AppState) -> None:
        trigger_death(app_state, reason="Combat breach")
        assert len(app_state.memory_bank.fragments) == 1

    def test_fragment_arc_defaults_to_1_when_no_mission(self, app_state: AppState) -> None:
        trigger_death(app_state, reason="Combat breach")
        assert app_state.memory_bank.fragments[0].arc == 1

    def test_fragment_arc_uses_current_mission_arc(self, app_state: AppState) -> None:
        app_state.current_mission = Mission(
            id="m_arc5_test",
            title="Arc 5 test",
            fixer="finn",
            arc=5,
            grade_min=4,
            grade_max=5,
            matrix_seed=42,
            zone=ZoneDepth.CORE,
        )
        trigger_death(app_state, reason="Boss wipe")
        assert app_state.memory_bank.fragments[0].arc == 5

    def test_fragment_arc_uses_mission_arc_when_valid(self, app_state: AppState) -> None:
        # If current_mission has an out-of-range arc, Mission's
        # __post_init__ raises, so the test that would have verified
        # the clamp lives at the data-layer (memory_bank) level. Here
        # we just confirm the trigger_death path uses current_mission.arc
        # when it's a valid value.
        app_state.current_mission = Mission(
            id="m_arc3_test",
            title="Arc 3 test",
            fixer="finn",
            arc=3,
            grade_min=2,
            grade_max=3,
            matrix_seed=42,
            zone=ZoneDepth.DEEP,
        )
        trigger_death(app_state, reason="Deep zone wipe")
        assert app_state.memory_bank.fragments[0].arc == 3

    def test_fragment_includes_death_reason(self, app_state: AppState) -> None:
        trigger_death(app_state, reason="Wetwork dump")
        assert "Wetwork dump" in app_state.memory_bank.fragments[0].text

    def test_fragment_timestamp_is_recent(self, app_state: AppState) -> None:
        before = int(time.time() * 1000)
        trigger_death(app_state, reason="Test")
        after = int(time.time() * 1000)
        ts = app_state.memory_bank.fragments[0].timestamp_ms
        assert before <= ts <= after

    def test_multiple_deaths_accumulate(self, app_state: AppState) -> None:
        trigger_death(app_state, reason="First")
        trigger_death(app_state, reason="Second")
        trigger_death(app_state, reason="Third")
        assert len(app_state.memory_bank.fragments) == 3
        assert "Third" in app_state.memory_bank.fragments[-1].text

    def test_cap_evicts_oldest(self, app_state: AppState) -> None:
        for i in range(MAX_FRAGMENTS + 5):
            trigger_death(app_state, reason=f"Death #{i}")
        assert len(app_state.memory_bank.fragments) == MAX_FRAGMENTS
        # The 5 oldest got evicted, oldest surviving is "Death #5".
        assert "Death #5" in app_state.memory_bank.fragments[0].text
        assert f"Death #{MAX_FRAGMENTS + 5 - 1}" in app_state.memory_bank.fragments[-1].text

    def test_death_reason_defaults_to_combat(self, app_state: AppState) -> None:
        trigger_death(app_state)
        assert "Combat" in app_state.memory_bank.fragments[0].text

    def test_state_remains_dead(self, app_state: AppState) -> None:
        trigger_death(app_state, reason="Test")
        assert app_state.is_dead is True
        assert app_state.death_reason == "Test"


class TestMemoryBankFIFOPreservation:
    def test_oldest_survives_across_three_deaths(self, app_state: AppState) -> None:
        trigger_death(app_state, reason="Alpha")
        trigger_death(app_state, reason="Beta")
        trigger_death(app_state, reason="Gamma")
        assert app_state.memory_bank.fragments[0].text.startswith("Last thing")
        assert "Alpha" in app_state.memory_bank.fragments[0].text
        assert "Gamma" in app_state.memory_bank.fragments[-1].text
