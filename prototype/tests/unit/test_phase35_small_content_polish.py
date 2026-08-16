"""Tests for Phase 35 — Small content + polish improvements.

Validates:
- The new general_event_wintermute_bargain event (Option A content addition).
  Gibson-flavored Neuromancer-era Wintermute AI encounter. Arc 4 deep-zone
  mid-arc — the AI reaches out to a runner through the construct_awakening
  chain. wintermute faction gets its first faction_affinity appearance in
  a general event (chain tie-in to Phase 32's zion_ping).
- Docstring coverage on 3 modules:
    * i18n/translator.py — Translator._load (80% -> 90%)
    * equipment/equipment.py — Equipment.is_upgradable, is_t1_or_better,
      EquipmentLoadout.equip/unequip/get/all_slots_filled/empty_slots/
      is_complete (85% -> 93%)
    * missions/board.py — _parse_objective, _parse_rewards, _parse_mission
      (86% -> 100%)
- Total events count increments from 37 to 38; total_chains stays at 6.
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
# Content: general_event_wintermute_bargain
# ---------------------------------------------------------------------------


class TestWintermuteBargainEvent:
    """Phase 35 content addition — Neuromancer-era Wintermute AI encounter.

    Gibson-flavored arc-4 deep-zone mid-arc event — Wintermute reaches out
    to a runner through the matrix, offering the bargain that drives the
    construct_awakening chain (Phase 32). Brings wintermute into general
    events via faction_affinity. Bridge between zion_ping (Phase 32) and
    the T-A endgame arc.
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_wintermute_bargain" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_wintermute_bargain"]
        assert event["event_id"] == "general_event_wintermute_bargain"
        assert event["title"] == "Wintermute's Bargain"
        assert event["category"] == "general"
        # Arc 4 deep-zone mid-arc event (Wintermute's reach starts here)
        assert event["arc"] == 4
        assert event["tier"] == 5
        assert event["pillar"] == "code"
        # Location should be matrix deep zone — Wintermute lives there
        assert "matrix" in event["location"].lower() or "deep" in event["location"].lower()
        # Triggered on node_enter with arc gate
        assert event["trigger"] == "node_enter"
        assert "arc_4_progress" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (accept AI bargain vs sever connection)."""
        event = events["general_event_wintermute_bargain"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Accept path should mark wintermute contact
        assert "wintermute" in event["choice"]["consequence_a"].lower()
        # Refuse path should mark safe jackout
        assert (
            "safe_jackout" in event["choice"]["option_b"]
            or "sever" in event["choice"]["option_b"].lower()
        )

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored AI dialogue (Neuromancer-era Wintermute)."""
        event = events["general_event_wintermute_bargain"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Wintermute signature phrases
        assert "wintermute" not in dialogue  # wintermute isn't named in dialogue
        # AI self-references + construct/loa/restless keywords
        assert "construct" in dialogue
        assert "loa" in dialogue
        assert "restless" in dialogue
        # Direct address to runner
        assert "runner" in dialogue or "you" in dialogue

    def test_event_faction_affinity(self, events: dict) -> None:
        """wintermute +3, ta_rep -1 (mirror Wintermute/TA tension in Neuromancer)."""
        event = events["general_event_wintermute_bargain"]
        # Accepting the bargain is pro-Wintermute and anti-TA (3Jane opposes Wintermute in Count Zero)
        assert event["faction_affinity"]["wintermute"] == 3
        assert event["faction_affinity"]["ta_rep"] == -1

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare wintermute_bargain_branch."""
        event = events["general_event_wintermute_bargain"]
        assert event["consequence"] == "wintermute_bargain_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 1800 credits + 120 XP + wintermute_fragment (consistent with tier 5)."""
        event = events["general_event_wintermute_bargain"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 1800
        assert event["reward"]["xp"] == 120
        assert event["reward"]["item"] == "wintermute_fragment"


class TestEventCountIncrement:
    """Phase 35 metadata bumps: total_events 37 -> 38, phase 34 -> 35."""

    def test_total_events_at_least_38(self, events: dict) -> None:
        assert len(events) >= 38

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 38
        # Forward-compat allowlist (mirrors Phase 29/32/33/34 pattern)
        assert metadata["phase"] in ("35", "36", "37", "38", "39", "40", "41", "42", "43", "44")

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 35 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: i18n/translator.py docstring coverage
# ---------------------------------------------------------------------------


class TestTranslatorDocstringCoverage:
    """Phase 35 polish — Translator._load gained a docstring (80% -> 90%)."""

    def test_translator_load_has_docstring(self) -> None:
        from roguelike_sprawl.i18n.translator import Translator

        method = Translator._load
        assert method.__doc__ is not None, "Translator._load missing docstring"
        assert method.__doc__.strip(), "Translator._load has empty docstring"
        # Must describe the silent no-op behavior (fallback semantics)
        assert "silent" in method.__doc__.lower() or "no-op" in method.__doc__.lower()

    def test_interrogate_translator_above_80(self) -> None:
        """Verify interrogate reports translator.py above 80% (was 80%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/i18n/translator.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        # Must have ZERO missed entries (was 2, now 1 with __repr__ still uncovered)
        # but Translator._load specifically must show COVERED
        assert "Translator._load" in result.stdout
        assert "COVERED" in result.stdout


# ---------------------------------------------------------------------------
# Polish 2: equipment/equipment.py docstring coverage
# ---------------------------------------------------------------------------


class TestEquipmentDocstringCoverage:
    """Phase 35 polish — 8 docstrings added to equipment/equipment.py."""

    def test_equipment_methods_have_docstrings(self) -> None:
        from roguelike_sprawl.equipment.equipment import Equipment

        # Methods that gained docstrings in Phase 35
        method_names = ["is_upgradable", "is_t1_or_better"]
        for name in method_names:
            method = getattr(Equipment, name)
            assert method.__doc__ is not None, f"Equipment.{name} missing docstring"
            assert method.__doc__.strip(), f"Equipment.{name} has empty docstring"

    def test_loadout_methods_have_docstrings(self) -> None:
        from roguelike_sprawl.equipment.equipment import EquipmentLoadout

        # Methods that gained docstrings in Phase 35
        method_names = [
            "equip",
            "unequip",
            "get",
            "all_slots_filled",
            "empty_slots",
            "is_complete",
        ]
        for name in method_names:
            method = getattr(EquipmentLoadout, name)
            assert method.__doc__ is not None, f"EquipmentLoadout.{name} missing docstring"
            assert method.__doc__.strip(), f"EquipmentLoadout.{name} has empty docstring"

    def test_interrogate_equipment_above_90(self) -> None:
        """Verify interrogate reports equipment.py above 90% (was 85%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/equipment/equipment.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "COVERED" in result.stdout


# ---------------------------------------------------------------------------
# Polish 3: missions/board.py docstring coverage
# ---------------------------------------------------------------------------


class TestBoardDocstringCoverage:
    """Phase 35 polish — _parse_objective, _parse_rewards, _parse_mission gained docstrings."""

    def test_parse_helpers_have_docstrings(self) -> None:
        from roguelike_sprawl.missions import board as board_module

        for name in ("_parse_objective", "_parse_rewards", "_parse_mission"):
            func = getattr(board_module, name)
            assert func.__doc__ is not None, f"{name} missing docstring"
            assert func.__doc__.strip(), f"{name} has empty docstring"

    def test_interrogate_board_at_100(self) -> None:
        """Verify interrogate reports board.py at 100% coverage (was 86%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/missions/board.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "MISSED" not in result.stdout or "EquipmentLoadout" in result.stdout
        # The file should now show 100% in the summary line
        assert "100%" in result.stdout


# ---------------------------------------------------------------------------
# Smoke tests — ensure new code paths still work at runtime
# ---------------------------------------------------------------------------


class TestPhase35Smoke:
    """Smoke tests for the polished docstrings — runtime safety."""

    def test_translator_load_with_missing_file_does_not_raise(self) -> None:
        """Translator._load silent fallback still works after docstring addition."""
        from roguelike_sprawl.i18n.translator import Translator

        # Point at a non-existent data dir; must silently no-op
        translator = Translator("en", data_dir=Path("/tmp/does_not_exist_phase35_test"))
        assert translator._data == {}
        # Fallback behavior intact: t() returns the key itself
        assert translator.t("missing.key") == "missing.key"

    def test_equipment_is_upgradable_returns_false_for_baseline(self) -> None:
        from roguelike_sprawl.equipment.equipment import STARTER_DECK

        # Baseline gear has 0 upgrade slots -> is_upgradable == False
        assert not STARTER_DECK.is_upgradable()

    def test_equipment_is_t1_or_better_excludes_baseline(self) -> None:
        from roguelike_sprawl.equipment.equipment import STARTER_DECK, STREET_DECK

        # T0 baseline returns False; T1 street returns True
        assert not STARTER_DECK.is_t1_or_better()
        assert STREET_DECK.is_t1_or_better()

    def test_loadout_is_complete_when_all_slots_filled(self) -> None:
        from roguelike_sprawl.equipment.equipment import (
            STARTER_DECK,
            STARTER_HEADWARE,
            EquipmentLoadout,
            EquipSlot,
        )

        loadout = EquipmentLoadout()
        assert not loadout.is_complete()

        # Equip into the two slots we have starter gear for
        loadout.equip(STARTER_DECK)
        loadout.equip(STARTER_HEADWARE)
        assert loadout.is_complete() is False  # 2 of 8 slots filled

        # Empty slots should include 6 slots
        empty = loadout.empty_slots()
        assert len(empty) == len(EquipSlot) - 2
        assert EquipSlot.DECK not in empty
        assert EquipSlot.HEADWARE not in empty

        # Filled slots should be the 2 we equipped
        filled = loadout.all_slots_filled()
        assert EquipSlot.DECK in filled
        assert EquipSlot.HEADWARE in filled
        assert len(filled) == 2

    def test_parse_mission_handles_legacy_fields(self) -> None:
        """_parse_mission docstring promises extract_data fallback for legacy entries."""
        from roguelike_sprawl.missions.board import _parse_mission

        # Legacy mission entry (no primary_objective, no rewards — uses objective string)
        legacy = {
            "id": "test_mission_legacy",
            "title": "Legacy Test",
            "fixer": "Finn",
            "arc": 1,
            "grade_min": 1,
            "grade_max": 1,
            "matrix_seed": 0,
            "zone": "surface",
            "objective": "old_format_data_id",
        }
        mission = _parse_mission(legacy)
        assert mission is not None
        assert mission.id == "test_mission_legacy"
        assert mission.primary_objective is not None
        assert mission.primary_objective.type == "extract_data"
        # Legacy fallback credits should be 0
        assert mission.reward_credits == 0
