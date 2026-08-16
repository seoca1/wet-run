"""Tests for Phase 39 — Small content + polish.

Validates:
- The new general_event_spn_handoff event (Option A content addition).
  Gibson-flavored Count Zero-era stolen personality handoff. Arc 2
  mid-arc Chiba back-room encounter. An anonymous simstim personality
  broker offers the runner a piece of somebody — famous, wanting out.
  Carrying it means carrying a mind fragment for three runs (the
  weight). Complements Phase 35/36/37/38 chain by adding a third
  identity-pillar arc-2 event with yakuza +2 (the broker network) and
  loa +1 (the borrowed personality has spectral memory).
- Docstring coverage on 3 modules:
    * ecs/dungeon_system.py — __init__/mission_id/__repr__ (83% -> 100%)
    * combat/boss.py — max_phases/_wintermute_phase_5_super_skill/
      _ta_phase_5_super_skill (87% -> 100%)
    * novel/dispatcher.py — NovelDispatcher.__init__ (86% -> 100%)
- Total events count increments from 41 to 42; total_chains stays at 6.
- Vault-wide interrogate coverage improves from 98.5% to 98.9%+.
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
# Content: general_event_spn_handoff
# ---------------------------------------------------------------------------


class TestSpnHandoffEvent:
    """Phase 39 content addition — Gibson-flavored Count Zero stolen SPN handoff.

    Arc 2 mid-arc Chiba back-room encounter. An anonymous simstim
    personality broker offers the runner a piece of somebody — famous,
    wanting out. Carrying it means carrying a mind fragment for three
    runs (the weight). Complements Phase 35 wintermute_bargain (wintermute
    +3), Phase 36 loa_construct_echo (loa +3), Phase 37 3jane_puppet_show
    (ta_rep +3), and Phase 38 kumiko_tea (ta_rep +2 + loa +2) by giving
    yakuza +2 (the broker network's customer base) and loa +1 (the
    borrowed personality has spectral memory).
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_spn_handoff" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_spn_handoff"]
        assert event["event_id"] == "general_event_spn_handoff"
        assert event["title"] == "Stolen Personality Handoff"
        assert event["category"] == "general"
        # Arc 2 mid-arc Chiba back-room event
        assert event["arc"] == 2
        assert event["tier"] == 4
        assert event["pillar"] == "identity"
        # Location should be in Chiba (Count Zero / Neuromancer territory)
        assert "chiba" in event["location"].lower() or "matrix" in event["location"].lower()
        # Triggered on node_enter with arc gate
        assert event["trigger"] == "node_enter"
        assert "arc_2_progress" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (accept the handoff vs refuse and walk away)."""
        event = events["general_event_spn_handoff"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Accept path should mention identity or stolen
        accept = event["choice"]["consequence_a"].lower()
        assert "identity" in accept or "stolen" in accept or "spn" in accept or "broker" in accept
        # Refuse path should mark safe jackout or blacklist
        refuse = event["choice"]["option_b"].lower() + event["choice"]["consequence_b"].lower()
        assert (
            "safe_jackout" in refuse
            or "refuse" in refuse
            or "blacklist" in refuse
            or "walk" in refuse
        )

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored Count Zero SPN broker dialogue."""
        event = events["general_event_spn_handoff"]
        dialogue = " ".join(event["dialogue"]).lower()
        # SPN / personality / stolen signature phrases (Count Zero opens with SPN-napping)
        assert "personality" in dialogue or "spn" in dialogue or "somebody" in dialogue
        assert "broker" in dialogue or "anonymous" in dialogue or "handshake" in dialogue
        # Count Zero era — weight / money / forget
        assert "weight" in dialogue or "money" in dialogue or "forget" in dialogue

    def test_event_faction_affinity(self, events: dict) -> None:
        """yakuza +2 (broker network), loa +1 (borrowed personality's spectral memory)."""
        event = events["general_event_spn_handoff"]
        assert event["faction_affinity"]["yakuza"] == 2
        assert event["faction_affinity"]["loa"] == 1

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare spn_handoff_branch."""
        event = events["general_event_spn_handoff"]
        assert event["consequence"] == "spn_handoff_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 2000 credits + 90 XP + stolen_personality_charm (consistent with tier 4)."""
        event = events["general_event_spn_handoff"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 2000
        assert event["reward"]["xp"] == 90
        assert event["reward"]["item"] == "stolen_personality_charm"

    def test_event_mood(self, events: dict) -> None:
        """Mood should be 'shady' — back-room broker tone."""
        event = events["general_event_spn_handoff"]
        assert event["mood"] == "shady"


class TestEventCountIncrement:
    """Phase 39 metadata bumps: total_events 41 -> 42, phase 38 -> 39."""

    def test_total_events_at_least_42(self, events: dict) -> None:
        assert len(events) >= 42

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 42
        # Forward-compat allowlist (mirrors Phase 29/32..38 pattern)
        assert metadata["phase"] in ("39", "40", "41")

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 39 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: ecs/dungeon_system.py docstring coverage
# ---------------------------------------------------------------------------


class TestDungeonSystemDocstringCoverage:
    """Phase 39 polish — DungeonSystem.__init__/mission_id/__repr__ docs (83% -> 100%)."""

    def test_dungeon_system_init_has_docstring(self) -> None:
        from roguelike_sprawl.ecs.dungeon_system import DungeonSystem

        assert DungeonSystem.__init__.__doc__ is not None
        assert DungeonSystem.__init__.__doc__.strip()
        # Should mention world + mission_id
        doc_lower = DungeonSystem.__init__.__doc__.lower()
        assert "world" in doc_lower
        assert "mission" in doc_lower

    def test_dungeon_system_mission_id_has_docstring(self) -> None:
        from roguelike_sprawl.ecs.dungeon_system import DungeonSystem

        assert DungeonSystem.mission_id.__doc__ is not None
        assert DungeonSystem.mission_id.__doc__.strip()

    def test_dungeon_system_repr_has_docstring(self) -> None:
        from roguelike_sprawl.ecs.dungeon_system import DungeonSystem

        assert DungeonSystem.__repr__.__doc__ is not None
        assert DungeonSystem.__repr__.__doc__.strip()

    def test_interrogate_dungeon_system_at_100(self) -> None:
        """Verify interrogate reports dungeon_system.py at 100% coverage (was 83%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/ecs/dungeon_system.py",
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
# Polish 2: combat/boss.py docstring coverage
# ---------------------------------------------------------------------------


class TestBossDocstringCoverage:
    """Phase 39 polish — max_phases + 2 phase-5 super skills (87% -> 100%)."""

    def test_boss_profile_max_phases_has_docstring(self) -> None:
        from roguelike_sprawl.combat.boss import BossProfile

        assert BossProfile.max_phases.__doc__ is not None
        assert BossProfile.max_phases.__doc__.strip()

    def test_wintermute_phase_5_super_skill_has_docstring(self) -> None:
        """Wintermute's phase-5 super — Count Zero neural whisper."""
        from roguelike_sprawl.combat.boss import _wintermute_phase_5_super_skill

        doc = _wintermute_phase_5_super_skill.__doc__
        assert doc is not None
        assert doc.strip()
        # Must explain Gibson inspiration
        assert "Count Zero" in doc or "Wintermute" in doc or "neural" in doc.lower()

    def test_ta_phase_5_super_skill_has_docstring(self) -> None:
        """Tessier-Ashpool's phase-5 super — Mona Lisa Overdrive family vote."""
        from roguelike_sprawl.combat.boss import _ta_phase_5_super_skill

        doc = _ta_phase_5_super_skill.__doc__
        assert doc is not None
        assert doc.strip()
        # Must explain Gibson inspiration
        assert "Mona Lisa Overdrive" in doc or "Tessier" in doc or "family" in doc.lower()

    def test_interrogate_boss_at_100(self) -> None:
        """Verify interrogate reports boss.py at 100% coverage (was 87%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/combat/boss.py",
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
# Polish 3: novel/dispatcher.py docstring coverage
# ---------------------------------------------------------------------------


class TestDispatcherDocstringCoverage:
    """Phase 39 polish — NovelDispatcher.__init__ docstring (86% -> 100%)."""

    def test_novel_dispatcher_init_has_docstring(self) -> None:
        from roguelike_sprawl.novel.dispatcher import NovelDispatcher

        doc = NovelDispatcher.__init__.__doc__
        assert doc is not None
        assert doc.strip()
        # Must explain catalog + manifest + dry_run contract
        doc_lower = doc.lower()
        assert "catalog" in doc_lower
        assert "manifest" in doc_lower
        assert "dry_run" in doc_lower or "dry run" in doc_lower

    def test_interrogate_dispatcher_at_100(self) -> None:
        """Verify interrogate reports dispatcher.py at 100% coverage (was 86%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/novel/dispatcher.py",
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


class TestPhase39Smoke:
    """Smoke tests for the polished code paths — runtime safety."""

    def test_dungeon_system_init_unchanged(self) -> None:
        """DungeonSystem.__init__ semantics intact after docstring addition."""
        from roguelike_sprawl.ecs.dungeon_system import DungeonSystem
        from roguelike_sprawl.ecs.world import World

        world = World()
        sys = DungeonSystem(world, mission_id="test_phase39")
        assert sys.mission_id() == "test_phase39"
        assert sys.cleared_rooms() == []
        assert sys.visited_rooms() == []

    def test_dungeon_system_repr_format(self) -> None:
        """__repr__ format unchanged after docstring addition."""
        from roguelike_sprawl.ecs.dungeon_system import DungeonSystem
        from roguelike_sprawl.ecs.world import World

        world = World()
        sys = DungeonSystem(world, mission_id="repr_test")
        r = repr(sys)
        assert "DungeonSystem" in r
        assert "repr_test" in r
        assert "visited=0" in r
        assert "cleared=0" in r

    def test_boss_profile_max_phases_intact(self) -> None:
        """BossProfile.max_phases still returns phase count after docstring addition."""
        from roguelike_sprawl.combat.boss import BossProfile, PhaseProfile
        from roguelike_sprawl.combat.effects import IceType

        phases = (
            PhaseProfile(
                phase=1,
                hp_threshold=1.0,
                damage_multiplier=1.0,
                color=(255, 0, 0),
                glyph="*",
                intro_text="Phase 1",
                skills=(),
            ),
            PhaseProfile(
                phase=2,
                hp_threshold=0.5,
                damage_multiplier=1.5,
                color=(255, 0, 0),
                glyph="*",
                intro_text="Phase 2",
                skills=(),
            ),
            PhaseProfile(
                phase=3,
                hp_threshold=0.0,
                damage_multiplier=2.0,
                color=(255, 0, 0),
                glyph="*",
                intro_text="Phase 3",
                skills=(),
            ),
        )
        profile = BossProfile(ice_type=IceType.WINTERMUTE, name="Test", phases=phases)
        assert profile.max_phases == 3

    def test_phase5_super_skills_construct(self) -> None:
        """Wintermute + TA phase-5 super skills still construct correctly."""
        from roguelike_sprawl.combat.boss import (
            _ta_phase_5_super_skill,
            _wintermute_phase_5_super_skill,
        )

        wm = _wintermute_phase_5_super_skill()
        assert wm.id == "wintermute_neural_whisper"
        assert wm.tier == 4
        assert wm.damage == 50

        ta = _ta_phase_5_super_skill()
        assert ta.id == "ta_family_vote"
        assert ta.tier == 4
        assert ta.damage == 45
        assert ta.aoe is True

    def test_novel_dispatcher_init_unchanged(self) -> None:
        """NovelDispatcher.__init__ semantics intact after docstring addition."""
        from roguelike_sprawl.novel.catalog import NovelCatalog
        from roguelike_sprawl.novel.dispatcher import NovelDispatcher
        from roguelike_sprawl.novel.manifest import NovelManifest

        catalog = NovelCatalog(repo_root=Path(__file__).parent.parent.parent)
        manifest = NovelManifest()
        # Default TextProvider
        d1 = NovelDispatcher(catalog, manifest)
        assert d1.catalog is catalog
        assert d1.manifest is manifest
        assert d1.dry_run is False

        # dry_run=True
        d2 = NovelDispatcher(catalog, manifest, dry_run=True)
        assert d2.dry_run is True
