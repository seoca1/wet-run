"""Tests for Phase 43 — Small content + polish.

Validates:
- The new general_event_neon_jack_out event (Option A content addition).
  Gibson-flavored arc 2 mid-arc "neon jack-out" event. The runner's
  Jack-Out sequence starts echoing a construct fragment's exit pattern
  — a recurring Sprawl trilogy motif (Case's sim hangover, Molly's
  razorgirl backtalk, loa-tech construct residue). Two paths:
  ride the echo (ta_rep_+1, archived exit pattern for later recall) or
  sever the line (loa_+1, clean jackout recorded, exit pattern kept).
  matrix_chiba_backroom location, mood nervous, pillar code, tier 3.
- Docstring coverage on 3 modules:
    * combat/boss_phase_tracker.py — BossPhaseTracker.__init__
    * combat/performance_integration.py — PerfTracker.__init__
    * matrix/exploration.py — ExplorationState.__post_init__
- Total events count increments from 45 to 46; total_chains stays at 6.
- Vault-wide interrogate coverage improves from 99.5% to 99.7%+.
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
# Content: general_event_neon_jack_out
# ---------------------------------------------------------------------------


class TestNeonJackOutEvent:
    """Phase 43 content addition — Gibson-flavored neon jack-out event.

    Arc 2 mid-arc (>= 25%) overlay on matrix_chiba_backroom. The
    runner's Jack-Out sequence starts echoing an archived construct
    fragment's exit pattern — a recurring Sprawl trilogy motif
    (Case's sim hangover, loa-tech construct residue). The choice
    is the standard "ride the echo vs sever it" fork: riding the
    echo yields ta_rep_+1 (T-A's biometric wetware is the source of
    the construct residue), severing the line yields loa_+1 (loa
    recognizes the construct's exit pattern as resonance).
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_neon_jack_out" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_neon_jack_out"]
        assert event["event_id"] == "general_event_neon_jack_out"
        assert event["title"] == "Neon Jack-Out"
        assert event["category"] == "general"
        # Arc 2 mid-arc encounter — chiba_backroom, tier 3
        assert event["arc"] == 2
        assert event["tier"] == 3
        assert event["pillar"] == "code"
        assert "chiba" in event["location"].lower()
        # Triggered on node_enter with arc + random + status gates
        assert event["trigger"] == "node_enter"
        assert "arc_2_progress" in event["trigger_condition"]
        assert "random <" in event["trigger_condition"]
        assert "NOT has_status" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (ride the echo vs sever the line)."""
        event = events["general_event_neon_jack_out"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Ride path should mention ta_rep / archive
        ride_path = (event["choice"]["option_a"] + event["choice"]["consequence_a"]).lower()
        assert "ta_rep" in ride_path or "archive" in ride_path or "ride" in ride_path
        # Sever path should mention loa or sever/clean
        sever_path = (event["choice"]["option_b"] + event["choice"]["consequence_b"]).lower()
        assert "loa" in sever_path or "sever" in sever_path or "clean" in sever_path

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored reveal — exit pattern matches construct_fragment.

        Gibson wetware signatures:
        - Jack-Out sequence / exit pattern (Count Zero / Neuromancer)
        - construct_fragment (Mona Lisa Overdrive recurring motif)
        - runner voice: 'A construct doesn't jack out'
        """
        event = events["general_event_neon_jack_out"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Gibson wetware / matrix signatures
        assert "jack-out" in dialogue or "exit" in dialogue
        # Gibson construct motif (Mona Lisa Overdrive)
        assert "construct" in dialogue
        # Runner voice — "a construct doesn't jack out"
        assert "construct" in dialogue
        assert "jack" in dialogue

    def test_event_faction_affinity_ta_rep_plus_loa(self, events: dict) -> None:
        """ta_rep +1 AND loa +1 — ride vs sever trade-off spans two factions.

        The ride-echo branch yields ta_rep (T-A biometric wetware
        technology is the source of the construct residue). The
        sever-line branch yields loa (loa recognizes the construct's
        exit pattern as resonance). Both paths contribute a faction
        shift, but to different factions — the runner picks which
        exit pattern they want to keep.
        """
        event = events["general_event_neon_jack_out"]
        affinity = event["faction_affinity"]
        assert affinity["ta_rep"] == 1
        assert affinity["loa"] == 1
        # No other faction shifts
        assert set(affinity.keys()) == {"ta_rep", "loa"}

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare neon_jack_out_branch."""
        event = events["general_event_neon_jack_out"]
        assert event["consequence"] == "neon_jack_out_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 0 credits (the echo isn't worth money), 60 XP, neon_jack_out_charm."""
        event = events["general_event_neon_jack_out"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 0
        assert event["reward"]["xp"] == 60
        assert event["reward"]["item"] == "neon_jack_out_charm"

    def test_event_mood(self, events: dict) -> None:
        """Mood should be 'nervous' — the deck is exiting wrong."""
        event = events["general_event_neon_jack_out"]
        assert event["mood"] == "nervous"

    def test_event_trigger_gates_arc2_mid(self, events: dict) -> None:
        """Arc 2 mid-arc gate (>= 25%) with status flag — surface-of-mid."""
        event = events["general_event_neon_jack_out"]
        cond = event["trigger_condition"]
        assert "arc_2_progress >= 25" in cond
        assert "neon_jack_out_seen" in cond


class TestEventCountIncrement:
    """Phase 43 metadata bumps: total_events 45 -> 46, phase 42 -> 43."""

    def test_total_events_at_least_46(self, events: dict) -> None:
        assert len(events) >= 46

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 46
        # Forward-compat allowlist (mirrors Phase 29/34..42 pattern)
        assert metadata["phase"] in ("43", "44", "45", "46", "47", "48", "49", "50")

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 43 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: combat/boss_phase_tracker.py docstring coverage
# ---------------------------------------------------------------------------


class TestBossPhaseTrackerDocstringCoverage:
    """Phase 43 polish — BossPhaseTracker.__init__ (was MISSED)."""

    def test_boss_phase_tracker_init_has_docstring(self) -> None:
        from wet_run.combat.boss_phase_tracker import BossPhaseTracker

        doc = BossPhaseTracker.__init__.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions phase 0 / binding / seed
        assert "phase" in doc_lower or "bind" in doc_lower or "seed" in doc_lower
        # Mentions boss profile reference
        assert "boss" in doc_lower or "profile" in doc_lower

    def test_interrogate_boss_phase_tracker_at_100(self) -> None:
        """Verify interrogate reports combat/boss_phase_tracker.py at 100% coverage."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/combat/boss_phase_tracker.py",
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
# Polish 2: combat/performance_integration.py docstring coverage
# ---------------------------------------------------------------------------


class TestPerfTrackerDocstringCoverage:
    """Phase 43 polish — PerfTracker.__init__ (was MISSED)."""

    def test_perf_tracker_init_has_docstring(self) -> None:
        from wet_run.combat.performance_integration import PerfTracker

        doc = PerfTracker.__init__.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions budget / threshold / frame / memory
        assert "budget" in doc_lower or "threshold" in doc_lower or "frame" in doc_lower
        assert "memory" in doc_lower or "snapshot" in doc_lower

    def test_interrogate_performance_integration_at_100(self) -> None:
        """Verify interrogate reports combat/performance_integration.py at 100% coverage."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/combat/performance_integration.py",
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
# Polish 3: matrix/exploration.py docstring coverage
# ---------------------------------------------------------------------------


class TestExplorationStateDocstringCoverage:
    """Phase 43 polish — ExplorationState.__post_init__ (was MISSED)."""

    def test_exploration_state_post_init_has_docstring(self) -> None:
        from wet_run.matrix.exploration import ExplorationState

        doc = ExplorationState.__post_init__.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions seed / initial / current
        assert "seed" in doc_lower or "initial" in doc_lower or "current" in doc_lower
        # Mentions discovered / path
        assert "discover" in doc_lower or "path" in doc_lower or "visit" in doc_lower

    def test_interrogate_exploration_at_100(self) -> None:
        """Verify interrogate reports matrix/exploration.py at 100% coverage."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/matrix/exploration.py",
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


class TestPhase43Smoke:
    """Smoke tests for the polished code paths — runtime safety."""

    def test_boss_phase_tracker_initial_state(self) -> None:
        """BossPhaseTracker.__init__ seeds at phase index 0."""
        from wet_run.combat.boss_expansion import (
            BossPhase,
            BossProfile,
        )
        from wet_run.combat.boss_phase_tracker import BossPhaseTracker

        # Construct a minimal profile to avoid coupling to specific bosses
        minimal = BossProfile(
            id="test_minimal",
            name="Test Minimal",
            description="Minimal phase profile for tracker init smoke test",
            hp_base=100,
            damage_base=10,
            defense=1,
            tier=1,
            phases=(
                BossPhase(1, 0.5, 1.0, (255, 0, 0), "X", "PHASE 1"),
                BossPhase(2, 0.0, 1.0, (255, 0, 0), "Y", "PHASE 2"),
            ),
        )
        tracker = BossPhaseTracker(minimal)
        assert tracker.current_phase_index == 0
        assert tracker.boss is minimal
        assert not tracker.is_last_phase  # 2 phases -> not on last

    def test_perf_tracker_init_defaults(self) -> None:
        """PerfTracker.__init__ with no args uses 60fps / 100MB defaults."""
        from wet_run.combat.performance_integration import PerfTracker

        tracker = PerfTracker()
        assert tracker.snapshot_count() == 0
        assert tracker.tick_count() == 0

    def test_perf_tracker_init_custom_budgets(self) -> None:
        """PerfTracker.__init__ accepts custom frame/memory budgets."""
        from wet_run.combat.performance_integration import PerfTracker

        tracker = PerfTracker(frame_budget_ms=33.0, memory_budget_mb=200.0)
        assert tracker.snapshot_count() == 0
        assert tracker.tick_count() == 0

    def test_perf_tracker_record_tick_works(self) -> None:
        """PerfTracker.record_tick appends a profile and returns it."""
        from wet_run.combat.performance_integration import PerfTracker

        tracker = PerfTracker()
        profile = tracker.record_tick(label="test_tick", frame_time_ms=10.0)
        assert tracker.snapshot_count() == 1
        assert tracker.tick_count() == 1
        assert profile.tick_label == "test_tick"

    def test_exploration_state_post_init_seeds_current(self) -> None:
        """ExplorationState.__post_init__ adds current to discovered + path."""
        from wet_run.matrix.exploration import ExplorationState

        state = ExplorationState(current="node_a")
        assert "node_a" in state.discovered
        assert state.path == ["node_a"]

    def test_exploration_state_post_init_empty_current(self) -> None:
        """ExplorationState.__post_init__ no-op when current is empty string."""
        from wet_run.matrix.exploration import ExplorationState

        state = ExplorationState(current="")
        assert state.discovered == set()
        assert state.path == []

    def test_exploration_state_post_init_dedup_path(self) -> None:
        """ExplorationState.__post_init__ does not duplicate current in path."""
        from wet_run.matrix.exploration import ExplorationState

        state = ExplorationState(current="node_b", path=["node_b", "node_b"])
        # Constructor should not append if path[-1] == current
        assert state.path.count("node_b") == 2  # unchanged
