"""Tests for Phase 37 — Small content + polish.

Validates:
- The new general_event_3jane_puppet_show event (Option A content addition).
  Gibson-flavored Count Zero-era Tessier-Ashpool / 3Jane encounter.
  Arc 4 mid-arc TA orbit event. 3Jane's voice reaches out via the
  family private network — complements Phase 35's wintermute_bargain
  (wintermute +3, ta_rep -1) and Phase 36's loa_construct_echo (loa +3,
  wintermute +1) by giving ta_rep +3 and including a wintermute +1 nod
  (Count Zero 3Jane/Wintermute connection via the construct).
- Docstring coverage on 5 modules:
    * achievements.py — is_unlocked/get_progress/get_total_unlocked/
      get_total_available/get_completion_pct (81% -> 100%)
    * matrix/dungeon_generator.py — _BspNode.__hash__/__eq__/is_leaf,
      edge_pairs, find, union, _faction_for (78% -> 100%)
    * ghost_encounter.py — GhostChoice enum (75% -> 100%)
    * cyberspace/registry.py — WorldRegistry.__init__ (83% -> 100%)
    * matrix/ppl.py — Loadout.__post_init__ (83% -> 100%)
- Total events count increments from 39 to 40; total_chains stays at 6.
- Vault-wide interrogate coverage improves from 97.6% to 98.3%.
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
# Content: general_event_3jane_puppet_show
# ---------------------------------------------------------------------------


class TestThreeJanePuppetShowEvent:
    """Phase 37 content addition — Gibson-flavored TA / 3Jane encounter.

    Arc 4 mid-arc TA orbit event. 3Jane's voice reaches out via the
    family private network — the puppet show metaphor from Count Zero.
    Complements Phase 35 wintermute_bargain (wintermute +3, ta_rep -1)
    and Phase 36 loa_construct_echo (loa +3, wintermute +1) by giving
    ta_rep +3 + wintermute +1 (the 3Jane/Wintermute connection).
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_3jane_puppet_show" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_3jane_puppet_show"]
        assert event["event_id"] == "general_event_3jane_puppet_show"
        assert event["title"] == "3Jane's Puppet Show"
        assert event["category"] == "general"
        # Arc 4 mid-arc TA orbit event
        assert event["arc"] == 4
        assert event["tier"] == 5
        assert event["pillar"] == "code"
        # Location should be in the TA orbit area
        assert "ta" in event["location"].lower() or "orbit" in event["location"].lower()
        # Triggered on node_enter with arc gate
        assert event["trigger"] == "node_enter"
        assert "arc_4_progress" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (accept the invitation vs refuse the puppet show)."""
        event = events["general_event_3jane_puppet_show"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Accept path should mention ta or invitation
        assert (
            "ta_" in event["choice"]["consequence_a"].lower()
            or "3jane" in event["choice"]["consequence_a"].lower()
        )
        # Refuse path should mark safe jackout or disdain
        assert (
            "safe_jackout" in event["choice"]["option_b"].lower()
            or "refuse" in event["choice"]["option_b"].lower()
            or "amused" in event["choice"]["consequence_b"].lower()
        )

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored 3Jane / TA puppet show dialogue (Count Zero era)."""
        event = events["general_event_3jane_puppet_show"]
        dialogue = " ".join(event["dialogue"]).lower()
        # 3Jane / TA / puppet show signature phrases
        assert "3jane" in dialogue
        assert "family" in dialogue or "construct" in dialogue
        assert "puppet" in dialogue or "rotate" in dialogue
        # TA polymath tone — polished, faintly condescending
        assert "small" in dialogue or "dress" in dialogue or "dine" in dialogue

    def test_event_faction_affinity(self, events: dict) -> None:
        """ta_rep +3, wintermute +1 (3Jane/Wintermute Count Zero connection)."""
        event = events["general_event_3jane_puppet_show"]
        # Accepting the invitation is pro-TA (3Jane's table) and mildly pro-Wintermute
        # (the 3Jane/Wintermute construct connection in Count Zero)
        assert event["faction_affinity"]["ta_rep"] == 3
        assert event["faction_affinity"]["wintermute"] == 1

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare 3jane_puppet_show_branch."""
        event = events["general_event_3jane_puppet_show"]
        assert event["consequence"] == "3jane_puppet_show_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 1600 credits + 110 XP + ta_polymath_invitation (consistent with tier 5)."""
        event = events["general_event_3jane_puppet_show"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 1600
        assert event["reward"]["xp"] == 110
        assert event["reward"]["item"] == "ta_polymath_invitation"


class TestEventCountIncrement:
    """Phase 37 metadata bumps: total_events 39 -> 40, phase 36 -> 37."""

    def test_total_events_at_least_40(self, events: dict) -> None:
        assert len(events) >= 40

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 40
        # Forward-compat allowlist (mirrors Phase 29/32/33/34/35/36 pattern)
        assert metadata["phase"] in ("37", "38", "39", "40")

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 37 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: achievements.py docstring coverage
# ---------------------------------------------------------------------------


class TestAchievementsDocstringCoverage:
    """Phase 37 polish — 5 AchievementState methods gained docstrings (81% -> 100%)."""

    def test_achievement_state_methods_have_docstrings(self) -> None:
        from roguelike_sprawl.achievements import AchievementState

        method_names = [
            "is_unlocked",
            "get_progress",
            "get_total_unlocked",
            "get_total_available",
            "get_completion_pct",
        ]
        for name in method_names:
            method = getattr(AchievementState, name)
            assert method.__doc__ is not None, f"AchievementState.{name} missing docstring"
            assert method.__doc__.strip(), f"AchievementState.{name} has empty docstring"

    def test_interrogate_achievements_at_100(self) -> None:
        """Verify interrogate reports achievements.py at 100% coverage (was 81%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/achievements.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "100%" in result.stdout
        for name in (
            "AchievementState.is_unlocked",
            "AchievementState.get_progress",
            "AchievementState.get_total_unlocked",
            "AchievementState.get_total_available",
            "AchievementState.get_completion_pct",
        ):
            assert name in result.stdout, f"{name} not in output"
        assert "MISSED" not in result.stdout


# ---------------------------------------------------------------------------
# Polish 2: matrix/dungeon_generator.py docstring coverage
# ---------------------------------------------------------------------------


class TestDungeonGeneratorDocstringCoverage:
    """Phase 37 polish — 7 items gained docstrings (78% -> 100%)."""

    def test_bsp_node_dunder_methods_have_docstrings(self) -> None:
        from roguelike_sprawl.matrix.dungeon_generator import _BspNode

        # _BspNode.__hash__/__eq__/is_leaf gained docstrings
        for name in ("__hash__", "__eq__", "is_leaf"):
            attr = getattr(_BspNode, name)
            assert attr.__doc__ is not None, f"_BspNode.{name} missing docstring"
            assert attr.__doc__.strip(), f"_BspNode.{name} has empty docstring"

    def test_faction_for_has_docstring(self) -> None:
        from roguelike_sprawl.matrix.dungeon_generator import ProceduralDungeonGenerator

        method = ProceduralDungeonGenerator._faction_for
        assert method.__doc__ is not None
        assert method.__doc__.strip()

    def test_interrogate_dungeon_generator_at_100(self) -> None:
        """Verify interrogate reports dungeon_generator.py at 100% coverage (was 78%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/matrix/dungeon_generator.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "100%" in result.stdout
        for name in ("_BspNode.__hash__", "_BspNode.__eq__", "_BspNode.is_leaf", "_faction_for"):
            assert name in result.stdout, f"{name} not in output"
        assert "MISSED" not in result.stdout


# ---------------------------------------------------------------------------
# Polish 3: ghost_encounter.py + registry.py + ppl.py docstring coverage
# ---------------------------------------------------------------------------


class TestSmallModuleDocstringCoverage:
    """Phase 37 polish — GhostChoice / WorldRegistry.__init__ / Loadout.__post_init__ docs."""

    def test_ghost_choice_has_docstring(self) -> None:
        from roguelike_sprawl.ghost_encounter import GhostChoice

        assert GhostChoice.__doc__ is not None
        assert GhostChoice.__doc__.strip()
        # Must describe the three Loa encounter choices
        assert "talk" in GhostChoice.__doc__.lower()
        assert "fight" in GhostChoice.__doc__.lower()
        assert "leave" in GhostChoice.__doc__.lower()

    def test_registry_init_has_docstring(self) -> None:
        from roguelike_sprawl.cyberspace.registry import WorldRegistry

        init = WorldRegistry.__init__
        assert init.__doc__ is not None
        assert init.__doc__.strip()

    def test_ppl_post_init_has_docstring(self) -> None:
        from roguelike_sprawl.matrix.ppl import Loadout

        post_init = Loadout.__post_init__
        assert post_init.__doc__ is not None
        assert post_init.__doc__.strip()


# ---------------------------------------------------------------------------
# Smoke tests — ensure new code paths still work at runtime
# ---------------------------------------------------------------------------


class TestPhase37Smoke:
    """Smoke tests for the polished docstrings — runtime safety."""

    def test_achievement_state_methods_behavior_intact(self) -> None:
        """AchievementState methods still work after docstring addition."""
        from roguelike_sprawl.achievements import AchievementState

        state = AchievementState()
        assert state.get_total_unlocked() == 0
        assert state.get_total_available() >= 25
        assert state.get_completion_pct() == 0.0
        assert state.is_unlocked("first_blood") is False
        assert state.get_progress("centurion_progress") == 0

        # Unlock one and verify counters
        state.unlock("first_blood", current_ms=100)
        assert state.is_unlocked("first_blood") is True
        assert state.get_total_unlocked() == 1
        assert state.get_completion_pct() > 0.0

    def test_bsp_node_dunder_methods_behavior_intact(self) -> None:
        """_BspNode.__hash__/__eq__/is_leaf still work after docstring addition."""
        from roguelike_sprawl.matrix.dungeon_generator import _BspNode

        a = _BspNode(x=0, y=0, w=4, h=4)
        b = _BspNode(x=2, y=0, w=4, h=4)
        # Identity-based equality
        assert a == a
        assert a != b
        assert hash(a) == hash(a)
        assert hash(a) != hash(b)
        # Both leaves (no children)
        assert a.is_leaf
        assert b.is_leaf
        # Set semantics
        assert len({a, a, b}) == 2

    def test_ghost_choice_string_values_unchanged(self) -> None:
        """GhostChoice string values preserved after docstring addition."""
        from roguelike_sprawl.ghost_encounter import GhostChoice

        assert GhostChoice.TALK == "talk"
        assert GhostChoice.FIGHT == "fight"
        assert GhostChoice.LEAVE == "leave"

    def test_ppl_post_init_validates_tier(self) -> None:
        """Loadout.__post_init__ still validates tier ranges after docstring addition."""
        from roguelike_sprawl.matrix.ppl import Loadout, Program

        # Valid loadout
        loadout = Loadout(
            deck_tier=3, programs=(Program(id="p1", name="P1", tier=2),), wetware_tier=2
        )
        assert loadout.deck_tier == 3

        # Invalid tier raises ValueError
        with pytest.raises(ValueError, match="must be in 0..6"):
            Loadout(deck_tier=7, programs=(), wetware_tier=2)

    def test_registry_init_accepts_optional_world_map(self) -> None:
        """WorldRegistry.__init__ still accepts optional WorldMap after docstring addition."""
        from roguelike_sprawl.cyberspace.registry import WorldRegistry
        from roguelike_sprawl.cyberspace.world import WorldMap

        # Default: empty WorldMap
        reg1 = WorldRegistry()
        assert isinstance(reg1.world_map, WorldMap)

        # Pass-through: caller provides one
        wm = WorldMap()
        reg2 = WorldRegistry(world_map=wm)
        assert reg2.world_map is wm
