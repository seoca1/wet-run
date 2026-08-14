"""Tests for Phase 12 Boss Expansion (ADR-0190).

Covers 6 zone-bosses, 3 ascended variants, and 1 secret boss.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "combat"


@pytest.fixture
def zone_bosses() -> dict:
    with open(DATA_DIR / "zone_bosses.json") as f:
        return json.load(f)


ZONES = ["surface", "deep", "mid", "core", "ta", "freeside"]


class TestZoneBosses:
    """6 zone-bosses, one per zone."""

    def test_zone_bosses_count(self, zone_bosses) -> None:
        assert len(zone_bosses) == 11, f"Expected 11 bosses, got {len(zone_bosses)}"

    def test_one_zone_boss_per_zone(self, zone_bosses) -> None:
        zone_boss_ids = [
            "dj_cyberspace",
            "sense_net_sentinel",
            "hosaka_memory_vault",
            "locus_construct",
            "tessier_child",
            "orbit_ghost",
        ]
        for boss_id, zone in zip(zone_boss_ids, ZONES):
            assert boss_id in zone_bosses, f"Missing {boss_id}"
            assert zone_bosses[boss_id]["zone"] == zone, f"{boss_id}: expected zone {zone}"

    def test_zone_boss_required_fields(self, zone_bosses) -> None:
        for zone in ZONES:
            boss_id = {
                "surface": "dj_cyberspace",
                "deep": "sense_net_sentinel",
                "mid": "hosaka_memory_vault",
                "core": "locus_construct",
                "ta": "tessier_child",
                "freeside": "orbit_ghost",
            }[zone]
            boss = zone_bosses[boss_id]
            assert "name" in boss
            assert "hp_base" in boss
            assert "dmg_base" in boss
            assert "tier" in boss
            assert "phase_count" in boss
            assert "skills" in boss
            assert "loot_table" in boss

    def test_dj_cyberspace_is_surface(self, zone_bosses) -> None:
        assert zone_bosses["dj_cyberspace"]["zone"] == "surface"
        assert zone_bosses["dj_cyberspace"]["tier"] == 3

    def test_tessier_child_is_ta(self, zone_bosses) -> None:
        assert zone_bosses["tessier_child"]["zone"] == "ta"
        assert zone_bosses["tessier_child"]["tier"] == 5


class TestAscendedBosses:
    """4 ascended boss variants (Wintermute, TA Prime, Neuromancer, Peripheral)."""

    def test_ascended_bosses_count(self, zone_bosses) -> None:
        ascended = [k for k, v in zone_bosses.items() if v.get("name", "").endswith("Ascended")]
        assert len(ascended) == 4, f"Expected 4 ascended bosses, got {len(ascended)}"

    def test_ascended_required_names(self, zone_bosses) -> None:
        for name in ["Wintermute Ascended", "TA Prime Ascended", "Neuromancer Ascended"]:
            found = any(v.get("name") == name for v in zone_bosses.values())
            assert found, f"Missing ascended boss: {name}"

    def test_ascended_have_unlock(self, zone_bosses) -> None:
        for ice_id, ice in zone_bosses.items():
            if "Ascended" in ice.get("name", ""):
                assert "unlock_condition" in ice, f"{ice_id}: ascended needs unlock_condition"

    def test_neuromancer_ascended_has_8_phases(self, zone_bosses) -> None:
        for ice in zone_bosses.values():
            if ice.get("name") == "Neuromancer Ascended":
                assert ice["phase_count"] == 8


class TestSecretBoss:
    """1 secret boss (post-Salvation NG+ only)."""

    def test_peripheral_exists(self, zone_bosses) -> None:
        assert "the_peripheral" in zone_bosses

    def test_peripheral_is_tier_6(self, zone_bosses) -> None:
        assert zone_bosses["the_peripheral"]["tier"] == 6

    def test_peripheral_requires_salvation(self, zone_bosses) -> None:
        unlock = zone_bosses["the_peripheral"]["unlock_condition"]
        assert "salvation" in unlock

    def test_peripheral_has_10_phases(self, zone_bosses) -> None:
        assert zone_bosses["the_peripheral"]["phase_count"] == 10

    def test_peripheral_drops_peripheral_artifact(self, zone_bosses) -> None:
        loot = zone_bosses["the_peripheral"]["loot_table"]
        items = [loot_item["item"] for loot_item in loot]
        assert "peripheral_artifact" in items


class TestTotalBosses:
    """Total boss count.

    Zone bosses: 6 + Ascended: 4 + Secret: 1 = 11 total. Integration with F.4 registry
    (Neuromancer, Loa Baron, Black Baron) raises boss_expansion.py to 14.
    """

    def test_zone_bosses_total(self, zone_bosses) -> None:
        assert len(zone_bosses) == 11

    def test_tier_distribution(self, zone_bosses) -> None:
        tiers = [b["tier"] for b in zone_bosses.values()]
        assert min(tiers) >= 3, "All zone bosses should be tier 3+"
        assert max(tiers) == 6, "Highest tier should be 6 (secret boss)"
