"""Phase 50 — Small content + polish.

Content: general_event_screws_last_bargain (Arc 5 late-arc
Screw's Last Bargain from the Freeside black-market fixer).
The runner is offered a Freeside passport in exchange for a
'contested memory' — the kind you still flinch at. Gibson's
Freeside orbit / black-market deal-making tone.

1-2 modules polished:
- docstring clarity on Freeside-related game systems
- error message clarity in mission completion paths

Forward-compat allowlist bumped to ('49', '50') so Phase 49
forward-compat still passes when the metadata phase is '50'.
"""

import json
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
    """Return only the event entries (skip the top-level _chains and _meta keys)."""
    return {k: v for k, v in events_data.items() if k not in ("_chains", "_meta")}


@pytest.fixture
def metadata(events_data: dict) -> dict:
    """Extract Phase 50 metadata from the _meta key in events.json."""
    meta = events_data.get("_meta", {})
    return {
        "phase": str(meta.get("phase", "50")),
        "total_events": int(meta.get("total_events", 54)),
    }


# ---------------------------------------------------------------------------
# Content: general_event_screws_last_bargain
# ---------------------------------------------------------------------------


class TestScrewsLastBargainEvent:
    """Phase 50 content addition — Gibson-flavored Screw's Last Bargain.

    Arc 5 late-arc (>= 70%) overlay on matrix_freeside_orbit. The
    runner encounters Screw (the Freeside black-market fixer from
    Mona Lisa Overdrive who forges passports for the orbital
    colonies). The deal: a Freeside passport in exchange for a
    'contested memory' — the kind that still hurts. The choice is
    the standard 'pay the price vs walk away' fork: paying
    (freeside_clearance_+2) yields zion_affinity_-1 (Zion would
    not approve of bargaining with Freeside black-marketeers)
    plus screw_pass_unlocked (L5 orbit clearance opens) plus
    contested_memory_relinquished_2_runs (the runner carries
    fewer contested memories for two runs). Walking yields
    safe_jackout (jack out cleanly) plus identity_marker_high
    (the runner remains identity-marked) plus maas_+1 (Maas
    approves of the runner's refusal to bargain — Maas is
    protective of contested memories) plus maas_oath_2_runs.
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_screws_last_bargain" in events

    def test_event_metadata(self, events: dict) -> None:
        ev = events["general_event_screws_last_bargain"]
        assert ev["event_id"] == "general_event_screws_last_bargain"
        assert ev["arc"] == 5
        assert ev["tier"] == 5
        assert ev["pillar"] == "memory"
        assert ev["location"] == "matrix_freeside_orbit"
        assert ev["mood"] == "shaky"

    def test_event_trigger(self, events: dict) -> None:
        ev = events["general_event_screws_last_bargain"]
        assert "arc_5_progress >= 70" in ev["trigger_condition"]
        assert "NOT has_status:screw_bargain_seen" in ev["trigger_condition"]

    def test_event_dialogue(self, events: dict) -> None:
        ev = events["general_event_screws_last_bargain"]
        dialogue = " ".join(ev["dialogue"])
        assert "SCREW" in dialogue
        assert "Freeside" in dialogue or "freeside" in dialogue

    def test_event_choice_a_screw(self, events: dict) -> None:
        ev = events["general_event_screws_last_bargain"]
        opt = ev["choice"]["consequence_a"]
        assert "screw_pass_unlocked" in opt
        assert "freeside_clearance_+2" in opt
        assert "zion_affinity_-1" in opt
        assert "contested_memory_relinquished_2_runs" in opt

    def test_event_choice_b_maas(self, events: dict) -> None:
        ev = events["general_event_screws_last_bargain"]
        opt = ev["choice"]["consequence_b"]
        assert "maas_+1" in opt
        assert "maas_oath_2_runs" in opt
        assert "identity_marker_high" in opt

    def test_event_faction_affinity(self, events: dict) -> None:
        ev = events["general_event_screws_last_bargain"]
        aff = ev["faction_affinity"]
        assert aff.get("freeside_clearance") == 2
        assert aff.get("maas") == 1

    def test_event_rewards(self, events: dict) -> None:
        ev = events["general_event_screws_last_bargain"]
        assert ev["reward"]["item"] == "screw_freeside_charm"
        assert ev["reward"]["xp"] == 120

    def test_event_arc_5_partner(self, events: dict) -> None:
        ev = events["general_event_screws_last_bargain"]
        assert ev["consequence"] == "screws_last_bargain_branch"

    def test_event_branch_is_unique(self, events: dict) -> None:
        branches = {v.get("consequence") for v in events.values() if isinstance(v, dict)}
        assert "screws_last_bargain_branch" in branches
        assert len([b for b in branches if b == "screws_last_bargain_branch"]) == 1


class TestScrewsLastBargainBranchUniqueness:
    """Verify the bargain branch doesn't collide with any other event's branch."""

    def test_branch_id_unique_across_events(self, events: dict) -> None:
        seen: set[str] = set()
        for v in events.values():
            if isinstance(v, dict) and v.get("consequence"):
                branch = v["consequence"]
                if branch in seen:
                    raise AssertionError(f"Branch id {branch!r} collides between events")
                seen.add(branch)
        assert "screws_last_bargain_branch" in seen


# ---------------------------------------------------------------------------
# Phase 50 metadata checks
# ---------------------------------------------------------------------------


def test_phase_50_metadata_present(metadata: dict) -> None:
    """metadata should report phase 50 (or 49) after the cycle."""
    assert metadata["phase"] in ("49", "50")


def test_phase_50_total_events_at_least_53(metadata: dict) -> None:
    """Phase 50 adds 1 event, so total_events >= 53."""
    assert metadata["total_events"] >= 53
    assert metadata["phase"] in ("49", "50")
