"""Tests for Phase 14 Endings + Programs + Equipment Sets (ADR-0192, ADR-0193).

Covers 22 endings, 27 programs, 2 equipment sets, and 10 wetware augments.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent.parent.parent / "data"


@pytest.fixture
def endings_data() -> dict:
    with open(DATA_DIR / "story" / "endings.json") as f:
        return json.load(f)


@pytest.fixture
def endings(endings_data) -> dict:
    return {k: v for k, v in endings_data.items() if not k.startswith("_")}


@pytest.fixture
def programs_data() -> dict:
    with open(DATA_DIR / "programs" / "programs.json") as f:
        return json.load(f)


@pytest.fixture
def sets_data() -> dict:
    with open(DATA_DIR / "equipment" / "sets.json") as f:
        return json.load(f)


@pytest.fixture
def sets(sets_data) -> dict:
    return {k: v for k, v in sets_data.items() if not k.startswith("_")}


@pytest.fixture
def wetware_data() -> dict:
    with open(DATA_DIR / "equipment" / "wetware.json") as f:
        return json.load(f)


@pytest.fixture
def wetware(wetware_data) -> dict:
    return {k: v for k, v in wetware_data.items() if not k.startswith("_")}


class TestEndings:
    """22 endings across 6 types (ADR-0192 target was 18+)."""

    def test_ending_count(self, endings) -> None:
        assert len(endings) >= 18, f"Expected 18+ endings, got {len(endings)}"

    def test_ending_types_present(self, endings) -> None:
        types = {e.get("type") for e in endings.values()}
        for required in ["redemption", "sacrifice", "transcendence", "betrayal", "absolution", "integration"]:
            assert required in types, f"Missing ending type: {required}"

    def test_ending_required_fields(self, endings) -> None:
        for eid, e in endings.items():
            assert "title" in e, f"{eid}: missing title"
            assert "character_ref" in e, f"{eid}: missing character_ref"
            assert "trigger_condition" in e, f"{eid}: missing trigger_condition"
            assert "description" in e, f"{eid}: missing description"

    def test_three_ngplus_endings(self, endings) -> None:
        ngplus = [e for e in endings.values() if e.get("arc") == 6]
        assert len(ngplus) == 3, f"Expected 3 NG+ endings, got {len(ngplus)}"

    def test_no_duplicate_titles(self, endings) -> None:
        titles = [e.get("title") for e in endings.values()]
        assert len(titles) == len(set(titles)), "Duplicate ending titles found"


class TestPrograms:
    """27 programs (9 existing + 18 new per ADR-0193)."""

    def test_program_count(self, programs_data) -> None:
        assert len(programs_data) >= 27, f"Expected 27+ programs, got {len(programs_data)}"

    def test_new_programs_18_per_adr(self, programs_data) -> None:
        new_programs = ["ward", "decoy", "reflect", "barrier", "scan", "decrypt",
                        "cloak", "trace", "echo", "exploit", "payload", "backdoor",
                        "surge", "boost", "repair", "heal", "salvage", "inspire"]
        for p in new_programs:
            assert p in programs_data, f"Missing new program: {p}"

    def test_program_categories(self, programs_data) -> None:
        categories = {"defense": 0, "detect": 0, "attack": 0, "support": 0}
        for p in programs_data.values():
            t = p.get("type")
            if t in categories:
                categories[t] += 1
        assert categories["defense"] >= 4, f"Need 4+ defense, got {categories['defense']}"
        assert categories["detect"] >= 5, f"Need 5+ detect, got {categories['detect']}"
        assert categories["attack"] >= 4, f"Need 4+ attack, got {categories['attack']}"
        assert categories["support"] >= 5, f"Need 5+ support, got {categories['support']}"

    def test_program_required_fields(self, programs_data) -> None:
        for pid, p in programs_data.items():
            assert "name" in p, f"{pid}: missing name"
            assert "tier" in p, f"{pid}: missing tier"
            assert "type" in p, f"{pid}: missing type"
            assert "ap_cost" in p, f"{pid}: missing ap_cost"
            assert "description" in p, f"{pid}: missing description"
            assert "role" in p, f"{pid}: missing role"


class TestEquipmentSets:
    """2 equipment sets (Ghost + Architect per ADR-0193)."""

    def test_set_count(self, sets) -> None:
        assert len(sets) == 2, f"Expected 2 sets, got {len(sets)}"

    def test_ghost_set_exists(self, sets) -> None:
        assert "ghost_set" in sets
        assert sets["ghost_set"]["theme"] == "Stealth + counter-intrusion"

    def test_architect_set_exists(self, sets) -> None:
        assert "architect_set" in sets
        assert sets["architect_set"]["theme"] == "Matrix control + program power"

    def test_set_has_4_pieces(self, sets) -> None:
        for sid, s in sets.items():
            assert len(s["pieces"]) == 4, f"{sid}: expected 4 pieces, got {len(s['pieces'])}"

    def test_set_has_4_bonuses(self, sets) -> None:
        for sid, s in sets.items():
            for bonus_key in ["set_bonus_2_piece", "set_bonus_3_piece", "set_bonus_4_piece"]:
                assert bonus_key in s, f"{sid}: missing {bonus_key}"

    def test_set_pieces_have_required_fields(self, sets) -> None:
        for sid, s in sets.items():
            for piece in s["pieces"]:
                assert "piece_id" in piece, f"{sid}: piece missing piece_id"
                assert "slot" in piece, f"{sid}: piece missing slot"
                assert "tier" in piece, f"{sid}: piece missing tier"


class TestWetwareAugments:
    """10 wetware augments (7 tier-3 + 3 new stats per ADR-0193)."""

    def test_augment_count(self, wetware) -> None:
        assert len(wetware) == 10, f"Expected 10 augments, got {len(wetware)}"

    def test_required_augments(self, wetware) -> None:
        required = ["ap_regen_lv3", "crit_lv3", "dodge_lv3", "max_hp_lv3",
                    "healing_lv3", "shield_lv3", "speed_lv3",
                    "mana_lv3", "armor_lv3", "focus_lv3"]
        for aug in required:
            assert aug in wetware, f"Missing augment: {aug}"

    def test_new_stat_augments(self, wetware) -> None:
        new_stats = ["mana_lv3", "armor_lv3", "focus_lv3"]
        for aug in new_stats:
            assert wetware[aug].get("is_new_stat") is True, f"{aug}: should be new stat"

    def test_augment_required_fields(self, wetware) -> None:
        for aug_id, aug in wetware.items():
            assert "name" in aug, f"{aug_id}: missing name"
            assert "tier" in aug, f"{aug_id}: missing tier"
            assert "type" in aug, f"{aug_id}: missing type"
            assert "description" in aug, f"{aug_id}: missing description"

    def test_tier_3_augments(self, wetware) -> None:
        for aug_id, aug in wetware.items():
            assert aug.get("tier") == 3, f"{aug_id}: should be tier 3"


class TestTotals:
    """Total content counts for Phase 14."""

    def test_endings_target_18_plus(self, endings) -> None:
        assert len(endings) >= 18

    def test_programs_target_30_plus(self, programs_data) -> None:
        assert len(programs_data) >= 30, f"ADR-0193 target was 30+, got {len(programs_data)}"

    def test_sets_target_2(self, sets) -> None:
        assert len(sets) == 2

    def test_wetware_target_10(self, wetware) -> None:
        assert len(wetware) == 10
