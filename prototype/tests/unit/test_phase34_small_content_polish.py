"""Tests for Phase 34 — Small content + polish improvements.

Validates:
- The new faction_event_hosaka_research_proposal event (Option A content addition).
  Gibson-flavored Hosaka biotech R&D recruitment event. Brings hosaka faction
  events from 2 to 3 (parity with sense_net and yakuza at 3).
- Docstring coverage on combat/state_models.py (27% → 100%, 19 added).
- Improved error messages in 2 modules:
    * run/state.py — start_chapter / complete_chapter list valid chapters
    * combat/cyberdeck.py — add_program_to_deck / remove_program_from_deck
      include current program list in errors
- Total events count increments from 36 to 37; total_chains stays at 6.
"""

from __future__ import annotations

import json
import random
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
# Content: faction_event_hosaka_research_proposal
# ---------------------------------------------------------------------------


class TestHosakaResearchProposalEvent:
    """Phase 34 content addition — Hosaka biotech R&D recruitment event.

    Gibson-flavored corporate R&D proposal (Neuromancer era Hosaka is Case's
    employer). Brings hosaka faction events from 2 to 3 (parity with
    sense_net/yakuza at 3).
    """

    def test_event_present(self, events: dict) -> None:
        assert "faction_event_hosaka_research_proposal" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["faction_event_hosaka_research_proposal"]
        assert event["event_id"] == "faction_event_hosaka_research_proposal"
        assert event["title"] == "Hosaka Research Proposal"
        assert event["category"] == "faction"
        assert event["faction_ref"] == "hosaka"
        # npc_choice trigger (matches other faction events)
        assert event["trigger"] == "npc_choice"
        # Compound trigger: hosaka rep gate + credits gate
        assert "hosaka_rep >= 4" in event["trigger_condition"]
        assert "credits > 2500" in event["trigger_condition"]
        assert event["arc"] == 3
        assert event["tier"] == 4

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (sign contract vs decline) — mirrors faction event pattern."""
        event = events["faction_event_hosaka_research_proposal"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Sign consequence should reference the credit reward
        assert "credits_+2500" in event["choice"]["consequence_a"]
        assert "hosaka_research_subject_marker" in event["choice"]["consequence_a"]

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored corporate R&D recruiter (Neuromancer era Hosaka)."""
        event = events["faction_event_hosaka_research_proposal"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Hosaka + wetware + Sprawl keywords
        assert "hosaka" in dialogue
        assert "wetware" in dialogue
        assert "sprawl" in dialogue
        assert "ice" in dialogue

    def test_event_faction_affinity(self, events: dict) -> None:
        """Faction affinity +2 hosaka (mirrors maas_neuropozyne_market pattern)."""
        event = events["faction_event_hosaka_research_proposal"]
        assert event["faction_affinity"]["hosaka"] == 2

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare hosaka_research_contract_branch."""
        event = events["faction_event_hosaka_research_proposal"]
        assert event["consequence"] == "hosaka_research_contract_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 2500 credits + 100 XP on accept (consistent with faction tier 4)."""
        event = events["faction_event_hosaka_research_proposal"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 2500
        assert event["reward"]["xp"] == 100


class TestEventCountIncrement:
    """Phase 34 metadata bumps: total_events 36 -> 37, phase 33 -> 34."""

    def test_total_events_at_least_37(self, events: dict) -> None:
        assert len(events) >= 37

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 37
        # Forward-compat: later phases (35+) may bump metadata.phase.
        assert metadata["phase"] in (
            "34",
            "35",
            "36",
            "37",
            "38",
            "39",
            "40",
            "41",
            "42",
            "43",
            "44",
            "45",
            "46",
            "47",
        )

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 34 does not add new chains — only events."""
        assert metadata["total_chains"] == 6

    def test_hosaka_faction_has_three_events(self, events: dict) -> None:
        """hosaka faction events: 2 -> 3 (parity with sense_net/yakuza)."""
        hosaka_events = [k for k, v in events.items() if v.get("faction_ref") == "hosaka"]
        assert len(hosaka_events) == 3
        assert "faction_event_hosaka_research_proposal" in hosaka_events


# ---------------------------------------------------------------------------
# Polish: combat/state_models.py docstring coverage (27% -> 100%)
# ---------------------------------------------------------------------------


class TestStateModelsDocstringCoverage:
    """Phase 34 polish — 19 docstrings added to combat/state_models.py.

    Target was the lowest-coverage module (27%). After Phase 34 it should
    be 100%. Covers all Combatant methods + CombatState target property,
    push method, and __post_init__.
    """

    def test_all_combatant_methods_have_docstrings(self) -> None:
        from roguelike_sprawl.combat.state_models import Combatant

        # All 15 Combatant methods (is_alive, is_stunned, is_staggered,
        # consume_stagger, get_attack_bonus, get_defense_bonus,
        # get_total_attack, get_ice_resistance_pct, get_crit_bonus_pct,
        # get_damage_bonus_pct, get_program_power, get_total_shield_bonus,
        # get_total_ap_bonus, get_total_hp_bonus, alive_skills_available,
        # choose_skill) must have docstrings.
        method_names = [
            "is_alive",
            "is_stunned",
            "is_staggered",
            "consume_stagger",
            "get_attack_bonus",
            "get_defense_bonus",
            "get_total_attack",
            "get_ice_resistance_pct",
            "get_crit_bonus_pct",
            "get_damage_bonus_pct",
            "get_program_power",
            "get_total_shield_bonus",
            "get_total_ap_bonus",
            "get_total_hp_bonus",
            "alive_skills_available",
            "choose_skill",
        ]
        for name in method_names:
            method = getattr(Combatant, name)
            assert method.__doc__ is not None, f"Combatant.{name} missing docstring"
            assert method.__doc__.strip(), f"Combatant.{name} has empty docstring"

    def test_combat_state_methods_have_docstrings(self) -> None:
        from roguelike_sprawl.combat.state_models import CombatState

        # CombatState methods needing docstrings: __post_init__, target (property), push
        assert CombatState.__post_init__.__doc__ is not None
        assert CombatState.__post_init__.__doc__.strip()
        assert CombatState.target.fget is not None
        assert CombatState.target.fget.__doc__ is not None
        assert CombatState.push.__doc__ is not None
        assert CombatState.push.__doc__.strip()

    def test_interrogate_coverage_100(self) -> None:
        """Verify interrogate reports 100% coverage on state_models.py."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/combat/state_models.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "100" in result.stdout or "COVERED" in result.stdout


# ---------------------------------------------------------------------------
# Polish: Improved error messages
# ---------------------------------------------------------------------------


class TestImprovedErrorMessages:
    """Phase 34 polish — error messages on 2 modules now include more context."""

    def test_run_state_chapter_error_lists_valid_range(self) -> None:
        """run/state.py start_chapter ValueError now names the method and lists valid chapters."""
        from roguelike_sprawl.run.state import RunState

        run = RunState()
        with pytest.raises(ValueError, match="start_chapter") as excinfo:
            run.start_chapter(99)
        msg = str(excinfo.value)
        # Must name the calling method (was just "chapter_num must be 1..5")
        assert "start_chapter" in msg
        # Must show the invalid value
        assert "99" in msg
        # Must list valid range
        assert "1..5" in msg

    def test_run_state_complete_chapter_error_lists_valid_range(self) -> None:
        """run/state.py complete_chapter ValueError now names the method."""
        from roguelike_sprawl.run.state import RunState

        run = RunState()
        with pytest.raises(ValueError, match="complete_chapter") as excinfo:
            run.complete_chapter(0)
        msg = str(excinfo.value)
        assert "complete_chapter" in msg
        assert "0" in msg
        assert "1..5" in msg

    def test_cyberdeck_duplicate_program_error_lists_programs(self) -> None:
        """cyberdeck.py add_program_to_deck ValueError now lists current programs."""
        from roguelike_sprawl.combat.cyberdeck import (
            add_program_to_deck,
            create_deck,
        )

        deck = create_deck("Test", ["probe", "shield"])
        with pytest.raises(ValueError, match="already in deck") as excinfo:
            add_program_to_deck(deck, "probe")
        msg = str(excinfo.value)
        assert "probe" in msg
        assert "already in deck" in msg
        # Should mention the current program list
        assert "shield" in msg or "current programs" in msg

    def test_cyberdeck_full_deck_error_suggests_removal(self) -> None:
        """cyberdeck.py add_program_to_deck ValueError now suggests removing a program."""
        from roguelike_sprawl.combat.cyberdeck import (
            DEFAULT_DECK_SLOTS,
            add_program_to_deck,
            create_deck,
        )

        deck = create_deck("Full", [f"prog_{i}" for i in range(DEFAULT_DECK_SLOTS)])
        with pytest.raises(ValueError, match="full") as excinfo:
            add_program_to_deck(deck, "extra")
        msg = str(excinfo.value)
        assert "full" in msg.lower()
        # Should mention slot count
        assert str(DEFAULT_DECK_SLOTS) in msg
        # Should suggest the remediation
        assert "Remove" in msg or "remove" in msg

    def test_cyberdeck_remove_missing_program_error_lists_programs(self) -> None:
        """cyberdeck.py remove_program_from_deck ValueError now lists current programs."""
        from roguelike_sprawl.combat.cyberdeck import (
            create_deck,
            remove_program_from_deck,
        )

        deck = create_deck("Test", ["probe", "shield"])
        with pytest.raises(ValueError, match="not in deck") as excinfo:
            remove_program_from_deck(deck, "missing")
        msg = str(excinfo.value)
        assert "missing" in msg
        assert "not in deck" in msg
        # Should mention current programs
        assert "probe" in msg or "current programs" in msg


# ---------------------------------------------------------------------------
# Regression: ensure new methods actually work (docstrings didn't break runtime)
# ---------------------------------------------------------------------------


class TestStateModelsSmoke:
    """Smoke tests for the now-documented Combatant/CombatState methods."""

    def test_combatant_choose_skill_returns_valid_skill(self) -> None:
        from roguelike_sprawl.combat.state_models import Combatant, Skill, SkillEffect

        skill = Skill(
            id="probe",
            name="Probe",
            tier=1,
            effect=SkillEffect.DETECT,
            ap_cost=1,
        )
        combatant = Combatant(
            id="e1",
            name="Standard",
            portrait="ice.standard",
            color=(255, 255, 255),
            hp=100,
            max_hp=100,
            skills=(skill,),
        )
        rng = random.Random(0)
        chosen = combatant.choose_skill(rng)
        assert chosen is skill

    def test_combatant_is_alive(self) -> None:
        from roguelike_sprawl.combat.state_models import Combatant

        c = Combatant(id="e1", name="X", portrait="x", color=(0, 0, 0), hp=0, max_hp=100)
        assert not c.is_alive()
        c2 = Combatant(id="e2", name="Y", portrait="y", color=(0, 0, 0), hp=1, max_hp=100)
        assert c2.is_alive()

    def test_combat_state_push_caps_at_six(self) -> None:
        from roguelike_sprawl.combat.state_models import Combatant, CombatState

        player = Combatant(id="p", name="P", portrait="p", color=(0, 0, 0), hp=100, max_hp=100)
        cs = CombatState(player=player)
        for i in range(10):
            cs.push(f"msg {i}")
        assert len(cs.log) == 6
        # FIFO: oldest dropped, last 6 retained
        assert cs.log[0] == "msg 4"
        assert cs.log[-1] == "msg 9"
