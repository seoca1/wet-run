"""Tests for Phase 28 — Sense/Net Classified event + polish improvements.

Validates:
- The new faction_event_sensenet_classified event (Option A content addition)
- chain_news_story wires the new event correctly
- Docstring coverage on portraits/manager.py (100%) + missions/board.py (>=80%)
- Improved error messages on missions/mission.py:Chain.__post_init__
- Total events count increments from 30 to 31
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roguelike_sprawl.missions.mission import (
    ChainFailure,
    ChainMission,
    ChainReward,
    ChainUnlockCondition,
    MissionChain,
)

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "story" / "events.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def events_data() -> dict:
    with open(DATA_PATH) as f:
        return json.load(f)


@pytest.fixture
def events(events_data: dict) -> dict:
    return {k: v for k, v in events_data.items() if not k.startswith("_")}


@pytest.fixture
def chains(events_data: dict) -> dict:
    return events_data.get("_chains", {})


@pytest.fixture
def metadata(events_data: dict) -> dict:
    return events_data.get("_metadata", {})


# ---------------------------------------------------------------------------
# Content: faction_event_sensenet_classified
# ---------------------------------------------------------------------------


class TestSensenetClassifiedEvent:
    """Phase 28 content addition — Sense/Net Classified Files event."""

    def test_event_present(self, events: dict) -> None:
        assert "faction_event_sensenet_classified" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["faction_event_sensenet_classified"]
        assert event["event_id"] == "faction_event_sensenet_classified"
        assert event["title"] == "Sense/Net Classified Files"
        assert event["category"] == "faction"
        assert event["faction_ref"] == "sense_net"
        assert event["trigger"] == "npc_choice"
        assert event["trigger_condition"] == "sense_net_rep >= 5"
        assert event["arc"] == 3
        assert event["tier"] == 5

    def test_event_has_choice(self, events: dict) -> None:
        event = events["faction_event_sensenet_classified"]
        assert event["choice"] is not None
        # Choice mirrors the Phase 27 sensenet_spin "branch choice" pattern
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored: Sense/Net's "we archive everything" voice."""
        event = events["faction_event_sensenet_classified"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Archive + Sprawl keywords (Gibson: Sense/Net is the Sprawl's memory)
        assert "archive" in dialogue
        assert "sprawl" in dialogue

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare sensenet_classified_branch (matches choice pattern)."""
        event = events["faction_event_sensenet_classified"]
        assert event["consequence"] == "sensenet_classified_branch"


# ---------------------------------------------------------------------------
# Chain integration: chain_news_story wires the new event
# ---------------------------------------------------------------------------


class TestChainNewsStoryUpdate:
    """chain_news_story now contains 5 events (was 4)."""

    def test_chain_news_story_includes_new_event(self, chains: dict) -> None:
        chain = chains["chain_news_story"]
        assert "faction_event_sensenet_classified" in chain["events"]

    def test_chain_news_story_length_within_bounds(self, chains: dict) -> None:
        """Chain length 3-5 per Phase 13 contract (test_chain_lengths)."""
        chain = chains["chain_news_story"]
        assert 3 <= len(chain["events"]) <= 5

    def test_chain_news_story_event_order(self, chains: dict) -> None:
        """sensnet_classified appears between sensenet_alert and sensenet_spin (chronologically)."""
        chain = chains["chain_news_story"]
        events = chain["events"]
        idx_alert = events.index("faction_event_sensenet_alert")
        idx_classified = events.index("faction_event_sensenet_classified")
        idx_spin = events.index("faction_event_sensenet_spin")
        # classified must sit between alert and spin in the timeline
        assert idx_alert < idx_classified < idx_spin


# ---------------------------------------------------------------------------
# Total count: 30 → 31 events
# ---------------------------------------------------------------------------


class TestEventCountIncrement:
    """Phase 28 bumps total event count from 30 to 31."""

    def test_total_events_at_least_31(self, events: dict) -> None:
        assert len(events) >= 31, f"Phase 28 target 31, got {len(events)}"

    def test_total_sensenet_events(self, events: dict) -> None:
        """Sense/Net now has 3 faction events (was 2)."""
        sensenet = [v for v in events.values() if v.get("faction_ref") == "sense_net"]
        assert len(sensenet) == 3, f"Expected 3 sensenet events, got {len(sensenet)}"

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        # Phase 29 bumped metadata when adding yakuza_contract; original
        # invariant relaxed to >= since Phase 28 era.
        assert metadata["total_events"] >= 31
        assert int(metadata["phase"]) >= 28


# ---------------------------------------------------------------------------
# Polish 1: portraits/manager.py docstrings
# ---------------------------------------------------------------------------


class TestPortraitDocstringCoverage:
    """portraits/manager.py — interrogate 100% (was 67% pre-Phase 28)."""

    def test_load_has_docstring(self) -> None:
        from roguelike_sprawl.portraits.manager import PortraitManager

        assert PortraitManager._load.__doc__ is not None
        assert "portraits.json" in PortraitManager._load.__doc__.lower()

    def test_dunder_methods_have_docstrings(self) -> None:
        from roguelike_sprawl.portraits.manager import PortraitManager

        assert PortraitManager.__len__.__doc__ is not None
        assert PortraitManager.__repr__.__doc__ is not None


# ---------------------------------------------------------------------------
# Polish 2: missions/board.py docstrings
# ---------------------------------------------------------------------------


class TestJobBoardDocstringCoverage:
    """missions/board.py — interrogate >=80% per file (was 59% pre-Phase 28)."""

    def test_dunder_methods_have_docstrings(self) -> None:
        from roguelike_sprawl.missions.board import JobBoard

        assert JobBoard.__iter__.__doc__ is not None
        assert JobBoard.__len__.__doc__ is not None
        assert JobBoard.__contains__.__doc__ is not None
        assert JobBoard.__repr__.__doc__ is not None

    def test_opt_helpers_have_docstrings(self) -> None:
        from roguelike_sprawl.missions import board

        assert board._opt_int.__doc__ is not None
        assert board._opt_str.__doc__ is not None


# ---------------------------------------------------------------------------
# Polish 3: missions/mission.py improved error messages
# ---------------------------------------------------------------------------


class TestChainErrorMessages:
    """MissionChain.__post_init__ error messages now point to remediation hints."""

    def _make_chain(self, **overrides: object) -> MissionChain:
        """Construct a minimal valid MissionChain (overrides can break it)."""
        kwargs: dict[str, object] = {
            "chain_id": "test_chain",
            "chain_name": "Test Chain",
            "chain_type": "story_driven",
            "chain_arc": 3,
            "unlock_condition": ChainUnlockCondition(arc_progress_min=10),
            "missions": tuple(
                ChainMission(
                    id=f"m{i}",
                    order=i,
                    type="investigation",
                    chain_role="intro" if i == 1 else ("climax" if i == 3 else "escalation"),
                )
                for i in (1, 2, 3)
            ),
            "chain_reward": ChainReward(credits=100),
            "chain_failure": ChainFailure(),
        }
        kwargs.update(overrides)
        return MissionChain(**kwargs)  # type: ignore[arg-type]

    def test_chain_length_error_message_helpful(self) -> None:
        """Error message names the events.json: _chains section as reference."""
        with pytest.raises(ValueError, match="3-5") as exc:
            self._make_chain(missions=())  # 0 missions, fails 3..5 check
        msg = str(exc.value)
        assert "events.json" in msg  # Phase 28 added hint

    def test_chain_type_error_message_helpful(self) -> None:
        """Error message lists the 3 valid chain_type values."""
        with pytest.raises(ValueError, match="bogus_type") as exc:
            self._make_chain(chain_type="bogus_type")
        msg = str(exc.value)
        assert "faction_driven" in msg
        assert "character_driven" in msg
        assert "story_driven" in msg

    def test_valid_chain_still_constructs(self) -> None:
        """Regression: a fully valid chain still instantiates without error."""
        chain = self._make_chain()
        assert chain.chain_id == "test_chain"
        assert len(chain.missions) == 3
