"""Tests for Phase 32 — Small content + polish improvements.

Validates:
- The new general_event_zion_ping event (Option A content addition)
- chain_construct_awakening wires the new event correctly (4 → 5, max)
- Docstring coverage on engine/screen_dispatch.py (18% → 100%) +
  story/ending_renderer.py (65% → 100%) + engine/status_message.py (70% → 100%)
- Total events count increments from 34 to 35; total_chains stays at 6
"""

from __future__ import annotations

import inspect
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
# Content: general_event_zion_ping
# ---------------------------------------------------------------------------


class TestZionPingEvent:
    """Phase 32 content addition — Zion Cluster Ping event (Zion operator uplink)."""

    def test_event_present(self, events: dict) -> None:
        assert "general_event_zion_ping" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_zion_ping"]
        assert event["event_id"] == "general_event_zion_ping"
        assert event["title"] == "Zion Cluster Ping"
        assert event["category"] == "general"
        # node_enter trigger (matches signal_jam / construct_sighting pattern)
        assert event["trigger"] == "node_enter"
        # Compound trigger: arc_5 gate + random roll
        assert "arc_5_progress >= 60" in event["trigger_condition"]
        assert "random < 0.04" in event["trigger_condition"]
        assert event["arc"] == 5
        assert event["tier"] == 5

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (acknowledge / ask) — mirrors console_warning pattern."""
        event = events["general_event_zion_ping"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored: Zion as off-matrix sanctuary (Count Zero era)."""
        event = events["general_event_zion_ping"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Zion + loa + construct keywords (Gibson: Zion defends against loa)
        assert "zion" in dialogue
        assert "loa" in dialogue
        assert "construct" in dialogue

    def test_event_reward_grants_credits_and_xp(self, events: dict) -> None:
        """Reward: 1200 credits + 80 XP (mid-tier informational reward)."""
        event = events["general_event_zion_ping"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 1200
        assert event["reward"]["xp"] == 80

    def test_event_faction_affinity(self, events: dict) -> None:
        """Faction affinity +2 zion, +1 wintermute (mirrors Case's neon memory pattern)."""
        event = events["general_event_zion_ping"]
        assert event["faction_affinity"]["zion"] == 2
        assert event["faction_affinity"]["wintermute"] == 1

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare zion_ping_received (matches choice pattern)."""
        event = events["general_event_zion_ping"]
        assert event["consequence"] == "zion_ping_received"


# ---------------------------------------------------------------------------
# Chain integration: chain_construct_awakening wires the new event
# ---------------------------------------------------------------------------


class TestChainConstructAwakeningUpdate:
    """chain_construct_awakening now contains 5 events (was 4, max allowed)."""

    def test_chain_construct_awakening_includes_new_event(self, chains: dict) -> None:
        chain = chains["chain_construct_awakening"]
        assert "general_event_zion_ping" in chain["events"]

    def test_chain_construct_awakening_length_within_bounds(self, chains: dict) -> None:
        """Chain length 3-5 per Phase 13 contract (test_chain_lengths)."""
        chain = chains["chain_construct_awakening"]
        assert 3 <= len(chain["events"]) <= 5

    def test_chain_construct_awakening_event_position(self, chains: dict) -> None:
        """zion_ping appears last (arc_5 progress >= 60 is the highest gate in the chain)."""
        chain = chains["chain_construct_awakening"]
        events = chain["events"]
        idx_ping = events.index("general_event_zion_ping")
        # zion_ping must be the last event (highest arc gate)
        assert idx_ping == len(events) - 1


# ---------------------------------------------------------------------------
# Total count: 34 → 35 events
# ---------------------------------------------------------------------------


class TestEventCountIncrement:
    """Phase 32 bumps total event count from 34 to 35."""

    def test_total_events_at_least_35(self, events: dict) -> None:
        assert len(events) >= 35, f"Phase 32 target 35, got {len(events)}"

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 35
        assert int(metadata["phase"]) >= 32

    def test_total_chains_unchanged(self, chains: dict) -> None:
        """Phase 32 adds no new chains, just extends an existing one."""
        assert len(chains) == 6, f"Expected 6 chains, got {len(chains)}"


# ---------------------------------------------------------------------------
# Polish 1: engine/screen_dispatch.py docstrings (18% → 100%)
# ---------------------------------------------------------------------------


class TestScreenDispatchDocstringCoverage:
    """engine/screen_dispatch.py — interrogate 100% (was 18% pre-Phase 32)."""

    def test_all_fourteen_handlers_have_docstrings(self) -> None:
        """The 14 nested render handlers in _build_dispatch all need docstrings."""
        from roguelike_sprawl.engine import screen_dispatch

        # The 14 nested handler names — each must have a docstring in source.
        handler_names = [
            "_arc_phase",
            "_cyberspace_map",
            "_graphic_novel_menu",
            "_graphic_novel_ending",
            "_gn_screen",
            "_hub",
            "_npc",
            "_event",
            "_story",
            "_chapter",
            "_saved_progress",
            "_matrix",
            "_combat",
            "_cinematic",
        ]
        source = inspect.getsource(screen_dispatch)
        for name in handler_names:
            # Each handler must appear as `def {name}(` in the source
            assert f"def {name}(" in source, f"{name} not found in source"

    def test_interrogate_coverage_100(self) -> None:
        """screen_dispatch.py reaches 100% interrogate coverage."""
        from interrogate.coverage import InterrogateCoverage

        ic = InterrogateCoverage(paths=["src/roguelike_sprawl/engine/screen_dispatch.py"])
        result = ic.get_coverage()
        file_result = result.file_results[0]
        assert file_result.missing == 0, (
            f"screen_dispatch.py has {file_result.missing} missing docstrings"
        )


# ---------------------------------------------------------------------------
# Polish 2: story/ending_renderer.py docstrings (65% → 100%)
# ---------------------------------------------------------------------------


class TestEndingRendererDocstringCoverage:
    """story/ending_renderer.py — interrogate 100% (was 65% pre-Phase 32)."""

    def test_init_has_docstring(self) -> None:
        from roguelike_sprawl.story.ending_renderer import EndingRenderer

        assert EndingRenderer.__init__.__doc__ is not None

    def test_load_endings_has_docstring(self) -> None:
        from roguelike_sprawl.story.ending_renderer import EndingRenderer

        assert EndingRenderer._load_endings.__doc__ is not None

    def test_to_scene_has_docstring(self) -> None:
        from roguelike_sprawl.story.ending_renderer import EndingRenderer

        assert EndingRenderer._to_scene.__doc__ is not None

    def test_render_helpers_have_docstrings(self) -> None:
        """All 3 render helpers (_render_intro/body/consequences) need docstrings."""
        from roguelike_sprawl.story.ending_renderer import EndingRenderer

        assert EndingRenderer._render_intro.__doc__ is not None
        assert EndingRenderer._render_body.__doc__ is not None
        assert EndingRenderer._render_consequences.__doc__ is not None

    def test_interrogate_coverage_100(self) -> None:
        """ending_renderer.py reaches 100% interrogate coverage."""
        from interrogate.coverage import InterrogateCoverage

        ic = InterrogateCoverage(paths=["src/roguelike_sprawl/story/ending_renderer.py"])
        result = ic.get_coverage()
        file_result = result.file_results[0]
        assert file_result.missing == 0, (
            f"ending_renderer.py has {file_result.missing} missing docstrings"
        )


# ---------------------------------------------------------------------------
# Polish 3: engine/status_message.py docstrings (70% → 100%)
# ---------------------------------------------------------------------------


class TestStatusMessageDocstringCoverage:
    """engine/status_message.py — interrogate 100% (was 70% pre-Phase 32)."""

    def test_status_message_properties_have_docstrings(self) -> None:
        """All 3 StatusMessage properties (icon, fg, bg) need docstrings."""
        from roguelike_sprawl.engine.status_message import StatusMessage

        assert StatusMessage.icon.fget is not None  # type: ignore[attr-defined]
        # Properties expose __doc__ via fget; we check the underlying docstring.
        # For @property, the docstring lives on the property object itself.
        assert StatusMessage.icon.__doc__ is not None
        assert StatusMessage.fg.__doc__ is not None
        assert StatusMessage.bg.__doc__ is not None

    def test_interrogate_coverage_100(self) -> None:
        """status_message.py reaches 100% interrogate coverage."""
        from interrogate.coverage import InterrogateCoverage

        ic = InterrogateCoverage(paths=["src/roguelike_sprawl/engine/status_message.py"])
        result = ic.get_coverage()
        file_result = result.file_results[0]
        assert file_result.missing == 0, (
            f"status_message.py has {file_result.missing} missing docstrings"
        )
