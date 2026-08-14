"""Tests for Phase 33 — Small content + polish improvements.

Validates:
- The new faction_event_maas_neuropozyne_market event (Option A content addition).
  First Maas faction event (0 → 1), connecting to Phase 30 maas_neuropozyne ICE
  and Phase 31 neuropozyne_withdrawal event.
- Docstring coverage on engine/story_view.py (67% → 100%).
- Improved error messages on 3 modules:
    * combat/status_effects_v2.py — lists valid status effect types
    * combat/meta_progression.py — lists valid unlock ids
    * novel/hooks.py — lists valid HookKind names
- Total events count increments from 35 to 36; total_chains stays at 6.
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
def chains(events_data: dict) -> dict:
    return events_data.get("_chains", {})


@pytest.fixture
def metadata(events_data: dict) -> dict:
    return events_data.get("_metadata", {})


# ---------------------------------------------------------------------------
# Content: faction_event_maas_neuropozyne_market
# ---------------------------------------------------------------------------


class TestMaasNeuropozyneMarketEvent:
    """Phase 33 content addition — Maas BioLabs black market faction event.

    Gibson-flavored biotech street dealer (Count Zero era). First
    faction event for the maas faction (was 0), connecting Phase 30
    maas_neuropozyne ICE and Phase 31 neuropozyne_withdrawal event.
    """

    def test_event_present(self, events: dict) -> None:
        assert "faction_event_maas_neuropozyne_market" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["faction_event_maas_neuropozyne_market"]
        assert event["event_id"] == "faction_event_maas_neuropozyne_market"
        assert event["title"] == "Maas BioLabs Black Market"
        assert event["category"] == "faction"
        assert event["faction_ref"] == "maas"
        # npc_choice trigger (matches yakuza_collection / yakuza_contract pattern)
        assert event["trigger"] == "npc_choice"
        # Compound trigger: maas rep gate + credits gate
        assert "maas_rep >= 2" in event["trigger_condition"]
        assert "credits > 1500" in event["trigger_condition"]
        assert event["arc"] == 3
        assert event["tier"] == 4

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (buy dose vs walk away) — mirrors yakuza_collection pattern."""
        event = events["faction_event_maas_neuropozyne_market"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Buy consequence should reference the credit cost
        assert "1500" in event["choice"]["consequence_a"]
        assert "credits_-1500" in event["choice"]["consequence_a"]
        assert "hp_restored_50" in event["choice"]["consequence_a"]

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored biotech street dealer (Count Zero era)."""
        event = events["faction_event_maas_neuropozyne_market"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Maas + neuropozyne + Sprawl keywords
        assert "maas" in dialogue
        assert "neuropozyne" in dialogue
        assert "sprawl" in dialogue

    def test_event_faction_affinity(self, events: dict) -> None:
        """Faction affinity +2 maas (mirrors yakuza_contract pattern)."""
        event = events["faction_event_maas_neuropozyne_market"]
        assert event["faction_affinity"]["maas"] == 2

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare maas_market_choice (matches choice pattern)."""
        event = events["faction_event_maas_neuropozyne_market"]
        assert event["consequence"] == "maas_market_choice"


# ---------------------------------------------------------------------------
# Total count: 35 → 36 events, maas faction event count: 0 → 1
# ---------------------------------------------------------------------------


class TestEventCountIncrement:
    """Phase 33 bumps total event count from 35 to 36."""

    def test_total_events_at_least_36(self, events: dict) -> None:
        assert len(events) >= 36, f"Phase 33 target 36, got {len(events)}"

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 36
        assert int(metadata["phase"]) >= 33

    def test_total_chains_unchanged(self, chains: dict) -> None:
        """Phase 33 adds no new chains; maas_market is a standalone event."""
        assert len(chains) == 6, f"Expected 6 chains, got {len(chains)}"

    def test_maas_faction_has_one_event(self, events: dict) -> None:
        """maas was 0 faction events, now has 1 (faction_event_maas_neuropozyne_market)."""
        maas_events = [k for k, v in events.items() if v.get("faction_ref") == "maas"]
        assert len(maas_events) == 1
        assert "faction_event_maas_neuropozyne_market" in maas_events


# ---------------------------------------------------------------------------
# Polish 1: engine/story_view.py docstrings (67% → 100%)
# ---------------------------------------------------------------------------


class TestStoryViewDocstringCoverage:
    """engine/story_view.py — interrogate 100% (was 67% pre-Phase 33)."""

    def test_story_registry_methods_have_docstrings(self) -> None:
        """The 3 StoryRegistry methods (load, get_aftermath, get_reaction) need docstrings."""
        from roguelike_sprawl.engine.story_view import StoryRegistry

        assert StoryRegistry.load.__doc__ is not None
        assert StoryRegistry.get_aftermath.__doc__ is not None
        assert StoryRegistry.get_reaction.__doc__ is not None

    def test_load_helpers_have_docstrings(self) -> None:
        """The 2 module-level _load_* helpers need docstrings."""
        from roguelike_sprawl.engine import story_view

        assert story_view._load_aftermaths.__doc__ is not None
        assert story_view._load_reactions.__doc__ is not None

    def test_interrogate_coverage_100(self) -> None:
        """story_view.py reaches 100% interrogate coverage."""
        from interrogate.coverage import InterrogateCoverage

        ic = InterrogateCoverage(paths=["src/roguelike_sprawl/engine/story_view.py"])
        result = ic.get_coverage()
        file_result = result.file_results[0]
        assert file_result.missing == 0, (
            f"story_view.py has {file_result.missing} missing docstrings"
        )


# ---------------------------------------------------------------------------
# Polish 2: improved error messages on 3 modules
# ---------------------------------------------------------------------------


class TestImprovedErrorMessages:
    """Phase 33 polish — error messages now list valid values."""

    def test_status_effects_v2_error_lists_valid_types(self) -> None:
        """make_status_v2 raises ValueError mentioning valid types."""
        from roguelike_sprawl.combat.status_effects_v2 import make_status_v2

        with pytest.raises(ValueError, match="must be one of") as exc_info:
            make_status_v2("nonexistent_status_xyz")
        msg = str(exc_info.value)
        assert "nonexistent_status_xyz" in msg
        assert "must be one of" in msg

    def test_meta_progression_error_lists_valid_unlock_ids(self) -> None:
        """record_meta_progress raises ValueError mentioning valid unlock ids."""
        from roguelike_sprawl.combat.meta_progression import record_meta_progress

        with pytest.raises(ValueError, match="Unknown unlock") as exc_info:
            record_meta_progress("nonexistent_unlock_xyz")
        msg = str(exc_info.value)
        assert "nonexistent_unlock_xyz" in msg
        assert "must be one of" in msg
        # Backward compat: old substring still matches (test_meta_progression.py uses this)
        assert "Unknown unlock" in msg

    def test_register_hook_action_error_lists_valid_hookkinds(self) -> None:
        """register_hook_action raises ValueError mentioning valid HookKind names."""
        from roguelike_sprawl.novel.hooks import register_hook_action

        # Use a non-HookKind sentinel via direct call (HookKind is an enum StrEnum)
        bogus_kind = type("BogusKind", (), {})()  # not a HookKind
        with pytest.raises(ValueError, match="Unknown HookKind") as exc_info:
            register_hook_action(bogus_kind, lambda ctx, state: None)  # type: ignore[arg-type]
        msg = str(exc_info.value)
        assert "Unknown HookKind" in msg
        assert "must be one of" in msg
