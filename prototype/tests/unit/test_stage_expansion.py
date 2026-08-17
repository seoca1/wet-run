"""Tests for the BRIEFING / TRAVEL / BYPASS_SECURITY stages
(CONTENT_EXPANSION Phase B).

Validates:

1. The three new stages exist in the ``Stage`` enum.
2. Each has matching ``StageInfo`` in ``DEFAULT_FLOW``.
3. ``MISSION_FLOWS`` for first_jack and watchdog_patrol embed the
   new stages correctly.
4. ASCII art for BRIEFING / TRAVEL is non-empty.
"""

from __future__ import annotations

from wet_run.run import Stage
from wet_run.run.state import (
    DEFAULT_FLOW,
    MISSION_FLOWS,
    get_mission_flow,
    get_stage_info,
)


class TestNewStagesExist:
    """The three CONTENT_EXPANSION Phase B stages exist."""

    def test_briefing_exists(self) -> None:
        assert Stage.BRIEFING.value == "briefing"

    def test_travel_exists(self) -> None:
        assert Stage.TRAVEL.value == "travel"

    def test_bypass_security_exists(self) -> None:
        assert Stage.BYPASS_SECURITY.value == "bypass_security"


class TestNewStageInfo:
    """Each new stage has DEFAULT_FLOW entry with required fields."""

    def test_briefing_info(self) -> None:
        info = DEFAULT_FLOW[Stage.BRIEFING]
        assert info.stage is Stage.BRIEFING
        assert info.title
        assert info.hint
        assert info.next_stage is Stage.TRAVEL

    def test_travel_info(self) -> None:
        info = DEFAULT_FLOW[Stage.TRAVEL]
        assert info.stage is Stage.TRAVEL
        assert info.title
        assert info.hint
        assert info.next_stage is Stage.MEET_NPC

    def test_bypass_security_info(self) -> None:
        info = DEFAULT_FLOW[Stage.BYPASS_SECURITY]
        assert info.stage is Stage.BYPASS_SECURITY
        assert info.title
        assert info.hint
        assert info.next_stage is Stage.DEFEAT_ICE


class TestNewStageAsciiArt:
    """BRIEFING / TRAVEL render their own ASCII flavour."""

    def test_briefing_has_ascii_art(self) -> None:
        info = DEFAULT_FLOW[Stage.BRIEFING]
        assert info.ascii_art, "BRIEFING should show ASCII art"
        assert len(info.ascii_art) >= 3

    def test_travel_has_ascii_art(self) -> None:
        info = DEFAULT_FLOW[Stage.TRAVEL]
        assert info.ascii_art, "TRAVEL should show ASCII art"
        assert len(info.ascii_art) >= 3


class TestGetStageInfoFallback:
    """``get_stage_info`` returns proper info for new stages."""

    def test_get_stage_info_briefing(self) -> None:
        info = get_stage_info(Stage.BRIEFING)
        assert info.stage is Stage.BRIEFING
        assert "briefing" in info.title.lower() or "브리핑" in info.title or info.title

    def test_get_stage_info_travel(self) -> None:
        info = get_stage_info(Stage.TRAVEL)
        assert info.stage is Stage.TRAVEL

    def test_get_stage_info_bypass(self) -> None:
        info = get_stage_info(Stage.BYPASS_SECURITY)
        assert info.stage is Stage.BYPASS_SECURITY


class TestMissionFlowsUpdated:
    """MISSION_FLOWS embed BRIEFING + TRAVEL (+ BYPASS for watchdog)."""

    @staticmethod
    def _stages_in_flow(mission_id: str) -> list[Stage]:
        """MISSION_FLOWS stores tuples of StageInfo; extract stages."""
        return [info.stage for info in get_mission_flow(mission_id)]

    def test_first_jack_flow_includes_briefing(self) -> None:
        stages = self._stages_in_flow("first_jack")
        assert Stage.BRIEFING in stages
        assert Stage.TRAVEL in stages
        # Order: BRIEFING before TRAVEL before MEET_NPC
        assert stages.index(Stage.BRIEFING) < stages.index(Stage.TRAVEL)
        assert stages.index(Stage.TRAVEL) < stages.index(Stage.MEET_NPC)

    def test_first_jack_no_bypass(self) -> None:
        """first_jack skips BYPASS_SECURITY (data extraction path)."""
        stages = self._stages_in_flow("first_jack")
        assert Stage.BYPASS_SECURITY not in stages

    def test_watchdog_includes_bypass(self) -> None:
        """watchdog_patrol uses BYPASS_SECURITY instead of EXTRACT_DATA."""
        stages = self._stages_in_flow("watchdog_patrol")
        assert Stage.BYPASS_SECURITY in stages
        assert Stage.EXTRACT_DATA not in stages
        assert Stage.BRIEFING in stages
        assert Stage.TRAVEL in stages

    def test_ice_run_includes_briefing(self) -> None:
        stages = self._stages_in_flow("ice_run")
        assert Stage.BRIEFING in stages
        assert Stage.TRAVEL in stages
        assert Stage.BYPASS_SECURITY not in stages

    def test_flow_keys_registered(self) -> None:
        """All 3 documented missions remain in MISSION_FLOWS."""
        for mid in ("first_jack", "watchdog_patrol", "ice_run"):
            assert mid in MISSION_FLOWS
