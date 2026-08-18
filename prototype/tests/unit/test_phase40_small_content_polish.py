"""Tests for Phase 40 — Small content + polish.

Validates:
- The new general_event_chiba_hotel_aftermath event (Option A content
  addition). Gibson-flavored Neuromancer / Count Zero "aftermath safe
  house" recovery scene for arc 5 (the convergence climax). The
  runner wakes up in a Chiba back-alley clinic after a flatline-level
  wetware hit (hp < 30%). The clinic fixer patches the deck but at
  the cost of identity strips — taking the deal yields construct_peek
  unlock and ta_rep +1, walking out bleeding yields loa +1 (endurance
  recognized) but at the cost of construct_whisper.
- Docstring coverage on 3 modules:
    * matrix/node.py — Node.__post_init__ (88% -> 100%)
    * missions/mission.py — Mission.__post_init__ + MissionChain.__post_init__ (88% -> 100%)
    * engine/dungeon_view.py — _handle_cardinal_movement + _handle_backtrack (83% -> 100%)
- Total events count increments from 42 to 43; total_chains stays at 6.
- Vault-wide interrogate coverage improves from 98.9% to 99.1%+.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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
def metadata(events_data: dict) -> dict:
    return events_data.get("_metadata", {})


# ---------------------------------------------------------------------------
# Content: general_event_chiba_hotel_aftermath
# ---------------------------------------------------------------------------


class TestChibaHotelAftermathEvent:
    """Phase 40 content addition — Gibson-flavored Chiba clinic aftermath.

    Arc 5 late-arc near-climax encounter. The runner wakes in a Chiba
    back-alley clinic after a wetware-flatlining run (hp < 30%). The
    clinic fixer reveals that somebody paid the tab — somebody who
    wants the runner back in the matrix. Pairs naturally with Phase 35
    wintermute_bargain (wintermute +3), Phase 36 loa_construct_echo
    (loa +3), Phase 37 3jane_puppet_show (ta_rep +3), Phase 38
    kumiko_tea (ta_rep +2 + loa +2), and Phase 39 spn_handoff
    (yakuza +2 + loa +1) as the arc 5 late-dot "I woke up in a clinic"
    scene. Faction affinity pairs ta_rep +1 (TA-adjacent fixer covering
    the tab) with loa +1 (either path), giving a mild ta/loa choice
    without leaning heavily on either side.
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_chiba_hotel_aftermath" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_chiba_hotel_aftermath"]
        assert event["event_id"] == "general_event_chiba_hotel_aftermath"
        assert event["title"] == "Chiba Hotel Aftermath"
        assert event["category"] == "general"
        # Arc 5 late-arc Chiba recovery event
        assert event["arc"] == 5
        assert event["tier"] == 5
        assert event["pillar"] == "identity"
        # Location should be in Chiba
        assert "chiba" in event["location"].lower()
        # Triggered on node_enter with arc + hp gates
        assert event["trigger"] == "node_enter"
        assert "arc_5_progress" in event["trigger_condition"]
        assert "hp_pct" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (take clinic deal vs walk out bleeding)."""
        event = events["general_event_chiba_hotel_aftermath"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Accept path should mention clinic and identity marker
        accept = (event["choice"]["option_a"] + event["choice"]["consequence_a"]).lower()
        assert "clinic" in accept or "wetware" in accept or "identity" in accept
        # Refuse path should mention walking out or bleeding
        refuse = (event["choice"]["option_b"] + event["choice"]["consequence_b"]).lower()
        assert "walk" in refuse or "bleed" in refuse or "loa" in refuse

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored Chi-city clinic scene — Case/Lee style."""
        event = events["general_event_chiba_hotel_aftermath"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Gibson Chi-city operative-tone signatures
        assert "chiba" in dialogue or "clinic" in dialogue or "wetware" in dialogue
        # Gibson "forgot", "matrix", "deck" used in fixer's lines
        assert "deck" in dialogue or "matrix" in dialogue or "tab" in dialogue
        # Gibson runner voice — "where" / "how long"
        assert "where" in dialogue or "how long" in dialogue or "out" in dialogue

    def test_event_faction_affinity(self, events: dict) -> None:
        """ta_rep +1 (the clinic tab is paid by TA-adjacent fixer), loa +1."""
        event = events["general_event_chiba_hotel_aftermath"]
        assert event["faction_affinity"]["ta_rep"] == 1
        assert event["faction_affinity"]["loa"] == 1

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare chiba_hotel_aftermath_branch."""
        event = events["general_event_chiba_hotel_aftermath"]
        assert event["consequence"] == "chiba_hotel_aftermath_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 0 credits (clinic deal costs the runner), 110 XP, chiba_clinic_charm."""
        event = events["general_event_chiba_hotel_aftermath"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 0
        assert event["reward"]["xp"] == 110
        assert event["reward"]["item"] == "chiba_clinic_charm"

    def test_event_mood(self, events: dict) -> None:
        """Mood should be 'shaky' — post-flatline disorientation."""
        event = events["general_event_chiba_hotel_aftermath"]
        assert event["mood"] == "shaky"

    def test_event_trigger_gates_combined(self, events: dict) -> None:
        """trigger_condition should gate by arc + hp + random + status exclusion."""
        event = events["general_event_chiba_hotel_aftermath"]
        cond = event["trigger_condition"]
        assert "arc_5_progress >= 50" in cond
        assert "random <" in cond
        assert "NOT has_status" in cond


class TestEventCountIncrement:
    """Phase 40 metadata bumps: total_events 42 -> 43, phase 39 -> 40."""

    def test_total_events_at_least_43(self, events: dict) -> None:
        assert len(events) >= 43

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 43
        # Forward-compat allowlist (mirrors Phase 29/32..39 pattern)
        assert metadata["phase"] in ("40", "41", "42", "43", "44", "45", "46", "47", "48", "49")

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 40 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: matrix/node.py docstring coverage
# ---------------------------------------------------------------------------


class TestMatrixNodeDocstringCoverage:
    """Phase 40 polish — Node.__post_init__ docstring (88% -> 100%)."""

    def test_node_post_init_has_docstring(self) -> None:
        from wet_run.matrix.node import Node

        doc = Node.__post_init__.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions validation
        assert "valid" in doc_lower or "invariant" in doc_lower
        # Mentions key invariants
        assert "id" in doc_lower or "label" in doc_lower
        assert "ice" in doc_lower
        assert "anomaly" in doc_lower

    def test_interrogate_node_at_100(self) -> None:
        """Verify interrogate reports matrix/node.py at 100% coverage (was 88%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/matrix/node.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "100%" in result.stdout
        assert "MISSED" not in result.stdout


# ---------------------------------------------------------------------------
# Polish 2: missions/mission.py docstring coverage
# ---------------------------------------------------------------------------


class TestMissionsDocstringCoverage:
    """Phase 40 polish — Mission + MissionChain __post_init__ docs (88% -> 100%)."""

    def test_mission_post_init_has_docstring(self) -> None:
        from wet_run.missions.mission import Mission

        doc = Mission.__post_init__.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        assert "valid" in doc_lower or "invariant" in doc_lower
        assert "arc" in doc_lower
        assert "grade" in doc_lower
        assert "reward" in doc_lower

    def test_mission_chain_post_init_has_docstring(self) -> None:
        from wet_run.missions.mission import MissionChain

        doc = MissionChain.__post_init__.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        assert "valid" in doc_lower or "invariant" in doc_lower
        assert "chain_id" in doc_lower
        # Mentions 3-5 mission requirement
        assert "3-5" in doc or "3 to 5" in doc or "3..5" in doc
        # Mentions chain_type constraint
        assert "chain_type" in doc_lower

    def test_interrogate_mission_at_100(self) -> None:
        """Verify interrogate reports missions/mission.py at 100% coverage (was 88%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/missions/mission.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "100%" in result.stdout
        assert "MISSED" not in result.stdout


# ---------------------------------------------------------------------------
# Polish 3: engine/dungeon_view.py docstring coverage
# ---------------------------------------------------------------------------


class TestDungeonViewDocstringCoverage:
    """Phase 40 polish — _handle_cardinal_movement + _handle_backtrack docs (83% -> 100%)."""

    def test_cardinal_movement_has_docstring(self) -> None:
        from wet_run.engine.dungeon_view import _handle_cardinal_movement

        doc = _handle_cardinal_movement.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions movement / neighbor
        assert "movement" in doc_lower or "neighbor" in doc_lower or "arrow" in doc_lower

    def test_backtrack_has_docstring(self) -> None:
        from wet_run.engine.dungeon_view import _handle_backtrack

        doc = _handle_backtrack.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions backtracking/pop semantics
        assert "backtrack" in doc_lower or "pop" in doc_lower or "rewind" in doc_lower

    def test_interrogate_dungeon_view_at_100(self) -> None:
        """Verify interrogate reports engine/dungeon_view.py at 100% (was 83%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/engine/dungeon_view.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "100%" in result.stdout
        assert "MISSED" not in result.stdout


# ---------------------------------------------------------------------------
# Smoke tests — ensure polished code paths still work at runtime
# ---------------------------------------------------------------------------


class TestPhase40Smoke:
    """Smoke tests for the polished code paths — runtime safety."""

    def test_node_post_init_validates_empty_id(self) -> None:
        """Node.__post_init__ semantics intact after docstring addition (empty id rejected)."""
        from wet_run.matrix.node import Node, NodeKind, ZoneDepth

        with pytest.raises(ValueError, match="Node id must be non-empty"):
            Node(
                id="",
                kind=NodeKind.DATA,
                label="L",
                zone=ZoneDepth.SURFACE,
                x=0,
                y=0,
            )

    def test_node_post_init_validates_ice_needs_ice_kind(self) -> None:
        """ICE node without IceKind is rejected (validation preserved)."""
        from wet_run.matrix.node import IceKind, Node, NodeKind, ZoneDepth

        with pytest.raises(ValueError, match="ICE node"):
            Node(
                id="E_ice",
                kind=NodeKind.ICE,
                label="ICE",
                zone=ZoneDepth.SURFACE,
                ice=IceKind.NONE,
                x=0,
                y=0,
            )

    def test_mission_post_init_rejects_bad_arc(self) -> None:
        """Mission.__post_init__ rejects arc > 5 (validation preserved)."""
        from wet_run.missions.mission import Mission

        with pytest.raises(ValueError, match="arc must be.*1..5"):
            Mission(
                id="m_bad",
                title="t",
                fixer="x",
                arc=6,  # out of range
                grade_min=1,
                grade_max=6,
                matrix_seed=0,
                zone="surface",
            )

    def test_mission_post_init_rejects_negative_reward(self) -> None:
        """Mission.__post_init__ rejects negative reward_credits (validation preserved)."""
        from wet_run.missions.mission import Mission

        with pytest.raises(ValueError, match="reward_credits"):
            Mission(
                id="m_neg",
                title="t",
                fixer="x",
                arc=1,
                grade_min=1,
                grade_max=6,
                matrix_seed=0,
                zone="surface",
                reward_credits=-1,
            )

    def test_mission_chain_post_init_rejects_short_chain(self) -> None:
        """MissionChain.__post_init__ rejects chains with <3 missions (validation preserved)."""
        from wet_run.missions.mission import (
            ChainFailure,
            ChainMission,
            ChainReward,
            ChainUnlockCondition,
            MissionChain,
        )

        too_few = (ChainMission(id="x", order=1, type="y", chain_role="intro"),)
        with pytest.raises(ValueError, match="chain must have 3-5 missions"):
            MissionChain(
                chain_id="c_bad",
                chain_name="Bad",
                chain_type="story_driven",
                chain_arc=1,
                unlock_condition=ChainUnlockCondition(),
                missions=too_few,
                chain_reward=ChainReward(),
                chain_failure=ChainFailure(),
            )

    def test_mission_chain_post_init_rejects_bad_chain_type(self) -> None:
        """MissionChain.__post_init__ rejects invalid chain_type (validation preserved)."""
        from wet_run.missions.mission import (
            ChainFailure,
            ChainMission,
            ChainReward,
            ChainUnlockCondition,
            MissionChain,
        )

        missions = tuple(
            ChainMission(id=f"x{i}", order=i + 1, type="y", chain_role="intro") for i in range(3)
        )
        with pytest.raises(ValueError, match="invalid chain_type"):
            MissionChain(
                chain_id="c_bad",
                chain_name="Bad",
                chain_type="not_a_valid_type",
                chain_arc=1,
                unlock_condition=ChainUnlockCondition(),
                missions=missions,
                chain_reward=ChainReward(),
                chain_failure=ChainFailure(),
            )
