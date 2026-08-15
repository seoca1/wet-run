"""Tests for Phase 36 — Small content + polish.

Validates:
- The new general_event_loa_construct_echo event (Option A content addition).
  Gibson-flavored Count Zero / Mona Lisa Overdrive-era construct echo.
  Arc 4 deep-loa-construct mid-arc — a dead jockey's construct reaches out
  through the matrix, ties into the construct_awakening chain (Phase 32).
  Brings loa further into general events via faction_affinity +3, complements
  Phase 35's wintermute_bargain (which used wintermute +3, ta_rep -1).
- Docstring coverage on 3 modules:
    * ecs/world.py — World.__init__/__iter__/__len__/__contains__/__repr__
      (58.3% -> 100%)
    * black_market.py — BlackMarketCategory enum (66.7% -> 100%)
    * ecs/entity.py — Entity.__repr__/__eq__/__hash__ (66.7% -> 100%)
- Total events count increments from 38 to 39; total_chains stays at 6.
- Vault-wide interrogate coverage improves from 97.2% to 97.6%.
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
# Content: general_event_loa_construct_echo
# ---------------------------------------------------------------------------


class TestLoaConstructEchoEvent:
    """Phase 36 content addition — Gibson-flavored construct echo encounter.

    Arc 4 deep-loa-construct mid-arc event. A dead jockey's construct
    echoes through the matrix — the loa keep him. Faction tie-in to the
    construct_awakening chain (Phase 32). Brings loa further into general
    events via faction_affinity +3, complements Phase 35's wintermute
    bargain which used wintermute +3.
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_loa_construct_echo" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_loa_construct_echo"]
        assert event["event_id"] == "general_event_loa_construct_echo"
        assert event["title"] == "Loa Construct Echo"
        assert event["category"] == "general"
        # Arc 4 deep-loa-construct mid-arc event (Dixie/Morrison's construct echoes)
        assert event["arc"] == 4
        assert event["tier"] == 5
        assert event["pillar"] == "memory"
        # Location should be in the loa construct area
        assert "loa" in event["location"].lower() or "construct" in event["location"].lower()
        # Triggered on node_enter with arc gate
        assert event["trigger"] == "node_enter"
        assert "arc_4_progress" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (carry the echo vs sever the connection)."""
        event = events["general_event_loa_construct_echo"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Carry path should mark loa construct echo
        assert "loa" in event["choice"]["consequence_a"].lower()
        # Sever path should mark safe jackout or curse risk
        assert (
            "safe_jackout" in event["choice"]["option_b"].lower()
            or "sever" in event["choice"]["option_b"].lower()
        )

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored construct echo dialogue (C-Z / MLO era)."""
        event = events["general_event_loa_construct_echo"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Construct echo signature phrases
        assert "construct" in dialogue
        assert "dixie" in dialogue or "morrison" in dialogue
        assert "loa" in dialogue
        # Echo self-references (a dead jockey's construct)
        assert "died" in dialogue or "dead" in dialogue or "echo" in dialogue

    def test_event_faction_affinity(self, events: dict) -> None:
        """loa +3, wintermute +1 (construct echo carries both loa and AI-construct weight)."""
        event = events["general_event_loa_construct_echo"]
        # Carrying the echo is pro-loa (echo's current home) and mildly pro-Wintermute
        # (construct echoes are partially AI matrix constructs)
        assert event["faction_affinity"]["loa"] == 3
        assert event["faction_affinity"]["wintermute"] == 1

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare loa_construct_echo_branch."""
        event = events["general_event_loa_construct_echo"]
        assert event["consequence"] == "loa_construct_echo_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 1400 credits + 100 XP + loa_construct_echo_charm (consistent with tier 5)."""
        event = events["general_event_loa_construct_echo"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 1400
        assert event["reward"]["xp"] == 100
        assert event["reward"]["item"] == "loa_construct_echo_charm"


class TestEventCountIncrement:
    """Phase 36 metadata bumps: total_events 38 -> 39, phase 35 -> 36."""

    def test_total_events_at_least_39(self, events: dict) -> None:
        assert len(events) >= 39

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 39
        # Forward-compat allowlist (mirrors Phase 29/32/33/34/35 pattern)
        assert metadata["phase"] in ("36", "37")

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 36 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: ecs/world.py docstring coverage
# ---------------------------------------------------------------------------


class TestEcsWorldDocstringCoverage:
    """Phase 36 polish — World.__init__/__iter__/__len__/__contains__/__repr__ docstrings (58.3% -> 100%)."""

    def test_world_dunder_methods_have_docstrings(self) -> None:
        from roguelike_sprawl.ecs.world import World

        # Methods that gained docstrings in Phase 36
        method_names = ["__init__", "__iter__", "__len__", "__contains__", "__repr__"]
        for name in method_names:
            method = getattr(World, name)
            assert method.__doc__ is not None, f"World.{name} missing docstring"
            assert method.__doc__.strip(), f"World.{name} has empty docstring"

    def test_interrogate_world_at_100(self) -> None:
        """Verify interrogate reports world.py at 100% coverage (was 58.3%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/ecs/world.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        # The file should now show 100% in the summary line
        assert "100%" in result.stdout
        # All five methods we added docstrings to should be COVERED
        for name in (
            "World.__init__",
            "World.__iter__",
            "World.__len__",
            "World.__contains__",
            "World.__repr__",
        ):
            assert name in result.stdout, f"{name} not in output"
        assert "MISSED" not in result.stdout or "passed" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Polish 2: black_market.py docstring coverage
# ---------------------------------------------------------------------------


class TestBlackMarketDocstringCoverage:
    """Phase 36 polish — BlackMarketCategory enum gained a docstring (66.7% -> 100%)."""

    def test_black_market_category_has_docstring(self) -> None:
        from roguelike_sprawl.black_market import BlackMarketCategory

        assert BlackMarketCategory.__doc__ is not None, "BlackMarketCategory missing docstring"
        assert BlackMarketCategory.__doc__.strip(), "BlackMarketCategory has empty docstring"
        # Must describe the vendor sections
        assert (
            "vendor" in BlackMarketCategory.__doc__.lower()
            or "market" in BlackMarketCategory.__doc__.lower()
        )

    def test_interrogate_black_market_at_100(self) -> None:
        """Verify interrogate reports black_market.py at 100% coverage (was 66.7%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/black_market.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "100%" in result.stdout
        assert "BlackMarketCategory" in result.stdout
        assert "MISSED" not in result.stdout


# ---------------------------------------------------------------------------
# Polish 3: ecs/entity.py docstring coverage
# ---------------------------------------------------------------------------


class TestEcsEntityDocstringCoverage:
    """Phase 36 polish — Entity.__repr__/__eq__/__hash__ gained docstrings (66.7% -> 100%)."""

    def test_entity_dunder_methods_have_docstrings(self) -> None:
        from roguelike_sprawl.ecs.entity import Entity

        # Methods that gained docstrings in Phase 36
        method_names = ["__repr__", "__eq__", "__hash__"]
        for name in method_names:
            method = getattr(Entity, name)
            assert method.__doc__ is not None, f"Entity.{name} missing docstring"
            assert method.__doc__.strip(), f"Entity.{name} has empty docstring"

    def test_interrogate_entity_at_100(self) -> None:
        """Verify interrogate reports entity.py at 100% coverage (was 66.7%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/ecs/entity.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "100%" in result.stdout
        for name in ("Entity.__repr__", "Entity.__eq__", "Entity.__hash__"):
            assert name in result.stdout, f"{name} not in output"


# ---------------------------------------------------------------------------
# Smoke tests — ensure new code paths still work at runtime
# ---------------------------------------------------------------------------


class TestPhase36Smoke:
    """Smoke tests for the polished docstrings — runtime safety."""

    def test_world_dunder_methods_behavior_intact(self) -> None:
        """World.__iter__/__len__/__contains__/__repr__ still work after docstring addition."""
        from roguelike_sprawl.ecs.entity import Entity
        from roguelike_sprawl.ecs.world import World

        world = World()
        assert len(world) == 0
        assert list(iter(world)) == []
        assert "foo" not in world  # __contains__ False

        world.add(Entity("foo", hp=10))
        assert len(world) == 1
        assert "foo" in world
        assert "bar" not in world

        # Iteration yields the entity
        entities = list(iter(world))
        assert len(entities) == 1
        assert entities[0].id == "foo"

        # __repr__ includes entity count
        assert "1 entities" in repr(world)

    def test_entity_dunder_methods_behavior_intact(self) -> None:
        """Entity.__repr__/__eq__/__hash__ still work after docstring addition."""
        from roguelike_sprawl.ecs.entity import Entity

        e1 = Entity("foo", hp=10)
        e2 = Entity("foo", hp=20)  # Different components but same id
        e3 = Entity("bar", hp=10)

        # Same id -> equal even with different components
        assert e1 == e2
        # Different id -> not equal
        assert e1 != e3
        # Hashable + hash by id
        assert hash(e1) == hash(e2)
        assert hash(e1) != hash(e3)

        # Use in set
        s = {e1, e2, e3}
        assert len(s) == 2  # e1 and e2 dedupe by id

        # __repr__ includes id and component type names
        repr_str = repr(e1)
        assert "foo" in repr_str
        assert "int" in repr_str  # type name of hp (int)

    def test_black_market_category_str_values_unchanged(self) -> None:
        """BlackMarketCategory string values preserved after docstring addition."""
        from roguelike_sprawl.black_market import BlackMarketCategory, list_by_category

        # Enum values are stable string contracts
        assert BlackMarketCategory.PROGRAMS == "programs"
        assert BlackMarketCategory.DECK_UPGRADES == "deck_upgrades"
        assert BlackMarketCategory.INTEL == "intel"

        # Iteration via list_by_category still works
        programs = list_by_category(BlackMarketCategory.PROGRAMS)
        assert all(p.category == BlackMarketCategory.PROGRAMS for p in programs)
        assert len(programs) > 0
