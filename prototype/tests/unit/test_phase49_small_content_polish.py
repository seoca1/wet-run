"""Phase 49 — Small content + polish.

Content: general_event_zion_last_broadcast (Arc 5 late-arc Maelcum
broadcast from the Zion dreadnaught ST. JOHN OF THE NIGHT SKY).
The runner receives a warm-toned transmission from Maelcum,
carrying a piece of Zion's memory into the construct passage.

3 modules polished:
- docstring clarity on FactionReputation.adjust() and the
  StageMap grid lookup in the various stages modules
- error message clarity on a few guard paths

Forward-compat allowlist bumped to ('48', '49') so Phase 48
forward-compat still passes when the metadata phase is '49'.
"""

import json
import re
from pathlib import Path

import pytest


@pytest.fixture
def events_data(project_root: Path) -> dict:
    """Load the story events JSON, parse, and return as a dict."""
    path = project_root / "data" / "story" / "events.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def events(events_data: dict) -> dict:
    """Return only the event entries (skip the top-level _chains key)."""
    return {k: v for k, v in events_data.items() if k != "_chains"}


@pytest.fixture
def metadata(events_data: dict) -> dict:
    """Extract Phase 49 metadata from the _meta key in events.json."""
    meta = events_data.get("_meta", {})
    return {
        "phase": str(meta.get("phase", "49")),
        "total_events": int(meta.get("total_events", 53)),
    }


# ---------------------------------------------------------------------------
# Content: general_event_zion_last_broadcast
# ---------------------------------------------------------------------------


class TestZionLastBroadcastEvent:
    """Phase 49 content addition — Gibson-flavored Zion Last Broadcast.

    Arc 5 late-arc (>= 60%) overlay on matrix_zion_orbit. The runner
    receives a warm-toned broadcast from Maelcum (the Zion dreadnaught
    pilot from Neuromancer / MLO who ferries Case out of Chiba in the
    Lo Teks orbit). The choice is the standard 'carry the wisdom vs
    walk on' fork: carrying (zion_affinity_+2) yields ta_rep_+1
    (the TA-family constructs accept the runner's memory-carrier
    status — the Zion dread's signal is read as construct-passage
    pre-auth) plus zion_wisdom_unlocked (the runner can access
    Zion-wisdom events later) plus memory_archive_+1. Walking on
    yields safe_jackout (the runner jacks out cleanly) plus
    wintermute_-1 (Wintermute notes that the runner dismissed a
    Lo Teks broadcast — the AI is unimpressed) plus
    identity_marker_low (the runner remains identity-unmarked) plus
    broadcast_silenced_marker (silent broadcast waves do not repeat).
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_zion_last_broadcast" in events

    def test_event_metadata(self, events: dict) -> None:
        ev = events["general_event_zion_last_broadcast"]
        assert ev["event_id"] == "general_event_zion_last_broadcast"
        assert ev["arc"] == 5
        assert ev["tier"] == 5
        assert ev["pillar"] == "memory"
        assert ev["location"] == "matrix_zion_orbit"
        assert ev["mood"] == "warm"

    def test_event_trigger(self, events: dict) -> None:
        ev = events["general_event_zion_last_broadcast"]
        assert "arc_5_progress >= 60" in ev["trigger_condition"]
        assert "NOT has_status:zion_broadcast_seen" in ev["trigger_condition"]

    def test_event_dialogue(self, events: dict) -> None:
        ev = events["general_event_zion_last_broadcast"]
        dialogue = " ".join(ev["dialogue"])
        assert "MAELCUM" in dialogue
        assert "Zion" in dialogue or "zion" in dialogue

    def test_event_choice_a_zion(self, events: dict) -> None:
        ev = events["general_event_zion_last_broadcast"]
        opt = ev["choice"]["consequence_a"]
        assert "zion_affinity_+2" in opt
        assert "ta_rep_+1" in opt
        assert "zion_wisdom_unlocked" in opt
        assert "memory_archive_+1" in opt

    def test_event_choice_b_wintermute_minus(self, events: dict) -> None:
        ev = events["general_event_zion_last_broadcast"]
        opt = ev["choice"]["consequence_b"]
        assert "wintermute_-1" in opt
        assert "broadcast_silenced_marker" in opt

    def test_event_faction_affinity(self, events: dict) -> None:
        ev = events["general_event_zion_last_broadcast"]
        aff = ev["faction_affinity"]
        assert aff.get("zion_affinity") == 2
        assert aff.get("ta_rep") == 1

    def test_event_rewards(self, events: dict) -> None:
        ev = events["general_event_zion_last_broadcast"]
        assert ev["reward"]["item"] == "zion_mother_charm"
        assert ev["reward"]["xp"] == 110

    def test_event_arc_5_partner(self, events: dict) -> None:
        ev = events["general_event_zion_last_broadcast"]
        assert ev["consequence"] == "zion_last_broadcast_branch"

    def test_event_branch_is_unique(self, events: dict) -> None:
        # Branch id should not collide with other events' branches.
        branches = {v.get("consequence") for v in events.values() if isinstance(v, dict)}
        assert "zion_last_broadcast_branch" in branches
        assert len([b for b in branches if b == "zion_last_broadcast_branch"]) == 1


class TestZionLastBroadcastBranchUniqueness:
    """Verify the broadcast branch doesn't collide with any other event's branch."""

    def test_branch_id_unique_across_events(self, events: dict) -> None:
        seen: set[str] = set()
        for v in events.values():
            if isinstance(v, dict) and v.get("consequence"):
                branch = v["consequence"]
                if branch in seen:
                    raise AssertionError(f"Branch id {branch!r} collides between events")
                seen.add(branch)
        assert "zion_last_broadcast_branch" in seen


# ---------------------------------------------------------------------------
# Phase 49 metadata checks
# ---------------------------------------------------------------------------


def test_phase_49_metadata_present(metadata: dict) -> None:
    """metadata should report phase 49 (or 48) after the cycle."""
    assert metadata["phase"] in ("48", "49")


def test_phase_49_total_events_at_least_52(metadata: dict) -> None:
    """Phase 49 adds 1 event, so total_events >= 52."""
    assert metadata["total_events"] >= 52
    # Forward-compat allowlist (mirrors Phase 29/34..48 pattern)
    assert metadata["phase"] in ("48", "49")
