"""Tests for Phase 13 Story Events Expansion (ADR-0191).

Covers 31 events (9 character + 10 faction + 12 general) and 6 chains.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "story" / "events.json"


@pytest.fixture
def events_data() -> dict:
    with open(DATA_PATH) as f:
        return json.load(f)


@pytest.fixture
def events(events_data) -> dict:
    return {k: v for k, v in events_data.items() if not k.startswith("_")}


@pytest.fixture
def chains(events_data) -> dict:
    return events_data.get("_chains", {})


CHARACTERS = ["case", "sil", "kas", "suit", "wigan", "angie", "sally", "3jane", "neuromancer"]
FACTIONS = ["hosaka", "sense_net", "yakuza", "ta_rep", "loa"]
TRIGGERS = [
    "npc_choice",
    "npc_greeting",
    "combat_end",
    "combat_start",
    "node_enter",
    "story_milestone",
    "chapter_complete",
    "vendor_unlocked",
    "hub_visited",
    "dialogue_completed",
]


class TestEventCounts:
    """30+ events across 3 categories."""

    def test_total_events(self, events) -> None:
        assert len(events) >= 30, f"Expected 30+ events, got {len(events)}"

    def test_character_events(self, events) -> None:
        char_events = [k for k, v in events.items() if v.get("category") == "character"]
        assert len(char_events) == 9, f"Expected 9 character events, got {len(char_events)}"

    def test_faction_events(self, events) -> None:
        faction_events = [k for k, v in events.items() if v.get("category") == "faction"]
        assert len(faction_events) >= 10, f"Expected 10+ faction events, got {len(faction_events)}"

    def test_general_events(self, events) -> None:
        general_events = [k for k, v in events.items() if v.get("category") == "general"]
        assert len(general_events) >= 12, f"Expected 12+ general events, got {len(general_events)}"


class TestCharacterEvents:
    """One event per character (9 characters)."""

    def test_one_event_per_character(self, events) -> None:
        char_events = [v for v in events.values() if v.get("category") == "character"]
        covered_chars = {v.get("character_ref") for v in char_events}
        for char in CHARACTERS:
            assert char in covered_chars, f"Missing character event for {char}"

    def test_character_events_have_required_fields(self, events) -> None:
        for event_id, event in events.items():
            if event.get("category") != "character":
                continue
            assert "character_ref" in event, f"{event_id}: missing character_ref"
            assert "title" in event, f"{event_id}: missing title"
            assert "dialogue" in event, f"{event_id}: missing dialogue"
            assert "trigger" in event, f"{event_id}: missing trigger"
            assert len(event["dialogue"]) > 0, f"{event_id}: empty dialogue"

    def test_case_event_uses_neuromancer_voice(self, events) -> None:
        case_event = events["char_event_case_neon_memory"]
        assert "neon" in case_event["dialogue"][0].lower()


class TestFactionEvents:
    """10 faction events, 2 per faction (5 factions)."""

    def test_two_events_per_faction(self, events) -> None:
        faction_events = [v for v in events.values() if v.get("category") == "faction"]
        for faction in FACTIONS:
            count = sum(1 for v in faction_events if v.get("faction_ref") == faction)
            assert count >= 2, f"{faction}: expected 2+ events, got {count}"

    def test_faction_events_have_required_fields(self, events) -> None:
        for event_id, event in events.items():
            if event.get("category") != "faction":
                continue
            assert "faction_ref" in event, f"{event_id}: missing faction_ref"
            assert "title" in event, f"{event_id}: missing title"
            assert "trigger" in event, f"{event_id}: missing trigger"

    def test_yakuza_event_has_choice(self, events) -> None:
        yakuza_events = [v for v in events.values() if v.get("faction_ref") == "yakuza"]
        has_choice = any(v.get("choice") for v in yakuza_events)
        assert has_choice, "At least one yakuza event should have a choice (debt collection)"


class TestGeneralEvents:
    """12 general events (zone/variety)."""

    def test_general_events_use_known_triggers(self, events) -> None:
        for event_id, event in events.items():
            if event.get("category") != "general":
                continue
            assert event.get("trigger") in TRIGGERS, (
                f"{event_id}: trigger '{event.get('trigger')}' not in {TRIGGERS}"
            )

    def test_general_events_have_dialogue(self, events) -> None:
        for event_id, event in events.items():
            if event.get("category") != "general":
                continue
            assert "dialogue" in event, f"{event_id}: missing dialogue"
            assert len(event["dialogue"]) >= 1, f"{event_id}: dialogue too short"

    def test_general_events_have_rewards_or_consequences(self, events) -> None:
        for event_id, event in events.items():
            if event.get("category") != "general":
                continue
            has_reward = bool(event.get("reward"))
            has_consequence = bool(event.get("consequence"))
            assert has_reward or has_consequence, f"{event_id}: should have reward or consequence"


class TestEventChains:
    """6 event chains."""

    def test_six_chains(self, chains) -> None:
        assert len(chains) == 6, f"Expected 6 chains, got {len(chains)}"

    def test_chain_types(self, chains) -> None:
        chain_types = [c.get("chain_type") for c in chains.values()]
        for ct in ["character", "faction", "story"]:
            assert ct in chain_types, f"Missing chain type: {ct}"

    def test_chain_has_required_fields(self, chains) -> None:
        for chain_id, chain in chains.items():
            assert "chain_name" in chain, f"{chain_id}: missing chain_name"
            assert "events" in chain, f"{chain_id}: missing events"
            assert "unlock_condition" in chain, f"{chain_id}: missing unlock_condition"
            assert "chain_reward" in chain, f"{chain_id}: missing chain_reward"

    def test_chains_reference_valid_events(self, events, chains) -> None:
        for chain_id, chain in chains.items():
            for event_id in chain["events"]:
                assert event_id in events, f"{chain_id}: references unknown event {event_id}"

    def test_chain_lengths(self, chains) -> None:
        for chain_id, chain in chains.items():
            assert 3 <= len(chain["events"]) <= 5, f"{chain_id}: chain length should be 3-5 events"


class TestTotalEvents:
    """Total event count and integration."""

    def test_target_30_plus_met(self, events) -> None:
        assert len(events) >= 30, f"ADR-0191 target was 30+ events, got {len(events)}"

    def test_chain_events_count(self, chains) -> None:
        chain_events = set()
        for chain in chains.values():
            for event_id in chain["events"]:
                chain_events.add(event_id)
        assert len(chain_events) >= 10, f"Need 10+ unique chain events, got {len(chain_events)}"


class TestPhase31NeuropozyneEvent:
    """Phase 31 — Neuropozyne Withdrawal general event (Gibson-flavored biotech crisis)."""

    EVENT_ID = "general_event_neuropozyne_withdrawal"

    def test_event_exists(self, events) -> None:
        assert self.EVENT_ID in events, f"Missing {self.EVENT_ID} (Phase 31 addition)"

    def test_event_metadata(self, events) -> None:
        event = events[self.EVENT_ID]
        assert event["event_id"] == self.EVENT_ID
        assert event["category"] == "general"
        assert event["title"] == "Neuropozyne Withdrawal"
        assert event["arc"] == 3
        assert event["tier"] == 3

    def test_event_trigger(self, events) -> None:
        event = events[self.EVENT_ID]
        assert event["trigger"] in TRIGGERS, f"trigger '{event['trigger']}' not in {TRIGGERS}"
        assert event["trigger"] == "combat_start"

    def test_event_has_choice(self, events) -> None:
        """Withdrawal must offer a binary survival choice (Gibson: addiction / cost)."""
        event = events[self.EVENT_ID]
        assert event["choice"] is not None, "Phase 31 event must have a choice"
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]

    def test_event_dialogue_uses_wetware_voice(self, events) -> None:
        """Dialogue should use the Gibson-style cyberpunk biotech warning voice."""
        event = events[self.EVENT_ID]
        dialogue_text = " ".join(event["dialogue"]).lower()
        assert "wetware" in dialogue_text
        assert "neuropozyne" in dialogue_text
        assert "warning" in dialogue_text

    def test_event_has_maas_affinity(self, events) -> None:
        """Connects to the maas faction (Phase 30 maas_neuropozyne ICE)."""
        event = events[self.EVENT_ID]
        assert event["faction_affinity"].get("maas") == 1, (
            "Phase 31 event should boost maas affinity"
        )

    def test_event_metadata_count_updated(self, events_data) -> None:
        """_metadata.total_events should reflect 34 after Phase 31 add."""
        total = events_data["_metadata"]["total_events"]
        assert total >= 34, f"Expected total_events >= 34, got {total}"
