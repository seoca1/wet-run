"""Tests for Phase 12 ICE Type Expansion (ADR-0189).

Covers 25 faction-specific ICE types, 10 variants, and 5 cyberspace hazards.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "combat"


@pytest.fixture
def ice_types() -> dict:
    with open(DATA_DIR / "ice_types.json") as f:
        return json.load(f)


@pytest.fixture
def cyberspace_hazards() -> dict:
    with open(DATA_DIR / "cyberspace_hazards.json") as f:
        return json.load(f)


@pytest.fixture
def faction_ice_types() -> dict:
    with open(DATA_DIR / "ice_types.json") as f:
        return {k: v for k, v in json.load(f).items() if v.get("faction")}
    return faction_ice_types()


@pytest.fixture
def variant_ice_types() -> dict:
    with open(DATA_DIR / "ice_types.json") as f:
        return {k: v for k, v in json.load(f).items() if v.get("variant")}
    return variant_ice_types()


FACTIONS = ["hosaka", "sense_net", "yakuza", "tessier_ashpool", "loa"]
VARIANT_TYPES = ["ascended", "corrupted", "defensive"]


class TestFactionICE:
    """All 25 faction-specific ICE types defined (5 per faction)."""

    def test_faction_ice_count(self, faction_ice_types) -> None:
        assert len(faction_ice_types) == 25, f"Expected 25, got {len(faction_ice_types)}"

    def test_faction_ice_per_faction(self, faction_ice_types) -> None:
        for faction in FACTIONS:
            count = sum(1 for v in faction_ice_types.values() if v.get("faction") == faction)
            assert count == 5, f"{faction}: expected 5, got {count}"

    def test_faction_ice_required_fields(self, faction_ice_types) -> None:
        for ice_id, ice in faction_ice_types.items():
            assert "name" in ice, f"{ice_id}: missing name"
            assert "hp_base" in ice, f"{ice_id}: missing hp_base"
            assert "dmg_base" in ice, f"{ice_id}: missing dmg_base"
            assert "tier" in ice, f"{ice_id}: missing tier"
            assert 1 <= ice["tier"] <= 5, f"{ice_id}: tier out of range"

    def test_hosaka_faction_ice(self, faction_ice_types) -> None:
        hosaka = [k for k, v in faction_ice_types.items() if v.get("faction") == "hosaka"]
        expected = [
            "hosaka_analyst",
            "hosaka_collector",
            "hosaka_courier",
            "hosaka_terminal",
            "hosaka_defender",
        ]
        assert sorted(hosaka) == sorted(expected)

    def test_sense_net_faction_ice(self, faction_ice_types) -> None:
        sense_net = [k for k, v in faction_ice_types.items() if v.get("faction") == "sense_net"]
        expected = [
            "sense_net_alert",
            "sense_net_archive",
            "sense_net_spin",
            "sense_net_informer",
            "sense_net_reporter",
        ]
        assert sorted(sense_net) == sorted(expected)


class TestICEVariants:
    """All ICE variants (5 ascended, 4 corrupted, 2 defensive, 1 black_construct, 1 proxy)."""

    def test_variant_count(self, variant_ice_types) -> None:
        assert len(variant_ice_types) == 15

    def test_variant_types(self, variant_ice_types) -> None:
        for vtype in VARIANT_TYPES:
            count = sum(1 for v in variant_ice_types.values() if v.get("variant") == vtype)
            assert count >= 1, f"No {vtype} variants found"

    def test_ascended_variants_have_base_type(self, variant_ice_types) -> None:
        for ice_id, ice in variant_ice_types.items():
            if ice.get("variant") == "ascended":
                assert "base_type" in ice, f"{ice_id}: ascended needs base_type"

    def test_corrupted_variants_have_glitch_skills(self, variant_ice_types) -> None:
        corruption_keywords = ["glitch", "corrupt", "warp", "melt", "pollution", "stack", "rot"]
        for ice_id, ice in variant_ice_types.items():
            if ice.get("variant") == "corrupted":
                skills = ice.get("skills", [])
                assert any(any(kw in s for kw in corruption_keywords) for s in skills), (
                    f"{ice_id}: corrupted needs at least one corruption-related skill, got {skills}"
                )

    def test_defensive_hariants_have_shield_skill(self, variant_ice_types) -> None:
        for ice_id, ice in variant_ice_types.items():
            if ice.get("variant") == "defensive":
                skills = ice.get("skills", [])
                assert any("shield" in s for s in skills), f"{ice_id}: defensive needs shield skill"


class TestCyberspaceHazards:
    """All 5 cyberspace hazards are defined and well-formed."""

    def test_hazards_count(self, cyberspace_hazards) -> None:
        assert len(cyberspace_hazards) == 5

    def test_required_hazards(self, cyberspace_hazards) -> None:
        required = ["antivirus_sweep", "trace_route", "data_corruption", "system_lag", "blackout"]
        for h in required:
            assert h in cyberspace_hazards, f"Missing hazard: {h}"

    def test_hazards_have_required_fields(self, cyberspace_hazards) -> None:
        for hazard_id, hazard in cyberspace_hazards.items():
            assert "name" in hazard, f"{hazard_id}: missing name"
            assert "description" in hazard, f"{hazard_id}: missing description"
            assert "trigger" in hazard, f"{hazard_id}: missing trigger"
            assert "duration" in hazard, f"{hazard_id}: missing duration"

    def test_hazards_have_hazard_type(self, cyberspace_hazards) -> None:
        valid_types = ["structured", "environmental", "debuff", "lockout"]
        for hazard_id, hazard in cyberspace_hazards.items():
            assert hazard.get("hazard_type") in valid_types, f"{hazard_id}: invalid hazard_type"

    def test_antivirus_sweep_does_damage(self, cyberspace_hazards) -> None:
        av = cyberspace_hazards["antivirus_sweep"]
        assert av["hp_damage"] > 0
        assert av["dmg_base"] > 0

    def test_trace_route_triggers_on_stay(self, cyberspace_hazards) -> None:
        assert "turns" in cyberspace_hazards["trace_route"]["trigger"]


class TestICETypeTotals:
    """Total ICE types and base type counts."""

    def test_total_ice_types_above_60(self, ice_types) -> None:
        base = {k: v for k, v in ice_types.items() if not v.get("is_alias")}
        assert len(base) >= 60, f"Need 60+ base ICE types, got {len(base)}"

    def test_new_ice_types_count(self, ice_types) -> None:
        new_in_phase12 = ["hosaka_analyst", "ta_daemon", "loa_baron", "standard_ascended"]
        for ice_id in new_in_phase12:
            assert ice_id in ice_types, f"Missing Phase 12 ICE type: {ice_id}"
