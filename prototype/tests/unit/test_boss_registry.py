"""Tests for zone boss registry (ADR-0190 Axis 4 — zone-bosses part).

Covers:
    - ``ZoneBossProfile`` dataclass (slots, frozen, all fields)
    - ``ZoneBossRegistry`` lookups (id-keyed, zone-keyed)
    - ``load_zone_boss_registry`` against the actual project data file
    - Resilience: empty input, metadata-key skipping, malformed entries
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wet_run.combat.boss_registry import (
    ZoneBossProfile,
    ZoneBossRegistry,
    _default_data_path,
    _parse_entry,
    load_zone_boss_registry,
)

ZONE_BOSSES_PATH = Path(__file__).parent.parent.parent / "data" / "combat" / "zone_bosses.json"


# ============================================================================
# Dataclass shape
# ============================================================================


class TestZoneBossProfileDataclass:
    def test_frozen_and_slots(self) -> None:
        p = ZoneBossProfile(
            boss_id="x",
            name="X",
            zone=None,
            tier=1,
            hp_base=10,
            hp_per_grade=0,
            dmg_base=1,
            dmg_per_grade=0,
            defense=0,
            speed=0,
            skills=(),
            resistance=0.0,
            phase_count=1,
            portrait="ice.boss",
            description="",
            loot_table=(),
            ice_kind="boss",
        )
        with pytest.raises((AttributeError, Exception)):
            p.tier = 5  # type: ignore[misc]

    def test_equality_by_all_fields(self) -> None:
        common = {
            "name": "X",
            "zone": "a",
            "tier": 1,
            "hp_base": 10,
            "hp_per_grade": 0,
            "dmg_base": 1,
            "dmg_per_grade": 0,
            "defense": 0,
            "speed": 0,
            "skills": (),
            "resistance": 0.0,
            "phase_count": 1,
            "portrait": "ice.boss",
            "description": "",
            "loot_table": (),
            "ice_kind": "boss",
        }
        a = ZoneBossProfile(boss_id="x", **common)
        b = ZoneBossProfile(boss_id="x", **common)
        assert a == b


class TestParseEntry:
    def test_minimal_entry(self) -> None:
        e = _parse_entry("foo", {"name": "Foo", "tier": 3})
        assert e.boss_id == "foo"
        assert e.name == "Foo"
        assert e.tier == 3
        assert e.skills == ()
        assert e.phase_count == 1
        assert e.zone is None

    def test_full_entry(self) -> None:
        e = _parse_entry(
            "dj_cyberspace",
            {
                "name": "DJ Cyberspace",
                "zone": "surface",
                "tier": 3,
                "hp_base": 150,
                "hp_per_grade": 25,
                "dmg_base": 7,
                "dmg_per_grade": 2,
                "defense": 5,
                "speed": 6,
                "skills": ["signal_jam", "data_corrupt", "ride_along"],
                "resistance": 0.2,
                "phase_count": 3,
                "portrait": "ice.boss",
                "description": "Local ripper.",
                "loot_table": [{"item": "data_fragment", "chance": 1.0, "quantity": 3}],
                "ice_kind": "boss",
            },
        )
        assert e.zone == "surface"
        assert e.hp_base == 150
        assert e.hp_per_grade == 25
        assert e.dmg_base == 7
        assert e.skills == ("signal_jam", "data_corrupt", "ride_along")
        assert e.resistance == pytest.approx(0.2)
        assert e.ice_kind == "boss"
        assert len(e.loot_table) == 1

    def test_zone_none_for_ascended(self) -> None:
        e = _parse_entry("wintermute_ascended", {"name": "WM↑", "tier": 5, "phase_count": 8})
        assert e.zone is None

    def test_skills_tuple_immutable(self) -> None:
        e = _parse_entry("x", {"skills": ["a", "b"]})
        assert isinstance(e.skills, tuple)
        with pytest.raises((AttributeError, Exception)):
            e.skills[0] = "z"  # type: ignore[index]


# ============================================================================
# Registry behaviour (in-memory)
# ============================================================================


class TestRegistryEmpty:
    def test_empty_dict(self) -> None:
        reg = ZoneBossRegistry({})
        assert len(reg) == 0
        assert reg.list_all() == ()
        assert reg.list_ids() == ()
        assert reg.list_zones() == ()
        assert reg.get("anything") is None
        assert reg.get_for_zone("x") == ()
        assert "x" not in reg

    def test_contains(self) -> None:
        e = _parse_entry("a", {"name": "A"})
        reg = ZoneBossRegistry({"a": e})
        assert "a" in reg
        assert "b" not in reg
        assert len(reg) == 1

    def test_get_for_zone(self) -> None:
        e = _parse_entry("a", {"name": "A", "zone": "surface"})
        reg = ZoneBossRegistry({"a": e})
        assert reg.get_for_zone("surface") == (e,)
        assert reg.get_for_zone("deep") == ()


class TestRegistryOrdering:
    def test_list_all_preserves_json_order(self) -> None:
        a = _parse_entry("alpha", {"name": "A"})
        b = _parse_entry("beta", {"name": "B"})
        c = _parse_entry("gamma", {"name": "C"})
        reg = ZoneBossRegistry({"alpha": a, "beta": b, "gamma": c})
        assert [p.boss_id for p in reg.list_all()] == ["alpha", "beta", "gamma"]
        assert reg.list_ids() == ("alpha", "beta", "gamma")

    def test_list_zones_sorted(self) -> None:
        a = _parse_entry("a", {"name": "A", "zone": "core"})
        b = _parse_entry("b", {"name": "B", "zone": "freeside"})
        c = _parse_entry("c", {"name": "C", "zone": "surface"})
        reg = ZoneBossRegistry({"a": a, "b": b, "c": c})
        assert reg.list_zones() == ("core", "freeside", "surface")


# ============================================================================
# Loader behaviour (against actual project data file)
# ============================================================================


class TestLoaderAgainstProjectFile:
    def test_default_path_points_to_project_data(self) -> None:
        p = _default_data_path()
        assert p.exists()
        assert p.name == "zone_bosses.json"
        assert "data/combat" in str(p)

    def test_loads_actual_file_11_entries(self) -> None:
        reg = load_zone_boss_registry(ZONE_BOSSES_PATH)
        assert len(reg) == 11

    def test_load_known_zone_boss(self) -> None:
        reg = load_zone_boss_registry(ZONE_BOSSES_PATH)
        e = reg.get("dj_cyberspace")
        assert e is not None
        assert e.tier == 3
        assert e.zone == "surface"
        assert e.hp_base == 150

    def test_load_unknown_returns_none(self) -> None:
        reg = load_zone_boss_registry(ZONE_BOSSES_PATH)
        assert reg.get("not_a_boss") is None

    def test_load_for_zone_surface(self) -> None:
        reg = load_zone_boss_registry(ZONE_BOSSES_PATH)
        bosses = reg.get_for_zone("surface")
        assert len(bosses) == 1
        assert bosses[0].boss_id == "dj_cyberspace"

    def test_load_for_zone_freeside(self) -> None:
        reg = load_zone_boss_registry(ZONE_BOSSES_PATH)
        bosses = reg.get_for_zone("freeside")
        assert len(bosses) == 1
        assert bosses[0].boss_id == "orbit_ghost"

    def test_load_for_unknown_zone(self) -> None:
        reg = load_zone_boss_registry(ZONE_BOSSES_PATH)
        assert reg.get_for_zone("nonexistent_zone") == ()

    def test_ascended_variants_have_no_zone(self) -> None:
        reg = load_zone_boss_registry(ZONE_BOSSES_PATH)
        for boss in reg.list_all():
            if boss.zone is None:
                assert ("ascended" in boss.boss_id) or ("peripheral" in boss.boss_id), (
                    f"Unexpected zone-less boss: {boss.boss_id}"
                )

    def test_all_six_zones_present(self) -> None:
        reg = load_zone_boss_registry(ZONE_BOSSES_PATH)
        expected = {"surface", "mid", "deep", "core", "ta", "freeside"}
        assert set(reg.list_zones()) == expected

    def test_secret_peripheral_present(self) -> None:
        reg = load_zone_boss_registry(ZONE_BOSSES_PATH)
        p = reg.get("the_peripheral")
        assert p is not None
        assert p.tier == 6
        assert p.phase_count == 10
        assert p.zone is None

    def test_each_entry_has_required_fields(self) -> None:
        reg = load_zone_boss_registry(ZONE_BOSSES_PATH)
        for boss in reg.list_all():
            assert boss.boss_id, "missing boss_id in entry"
            assert boss.name, f"missing name in {boss.boss_id}"
            assert boss.tier >= 1, f"bad tier in {boss.boss_id}"
            assert boss.hp_base > 0, f"bad hp_base in {boss.boss_id}"
            assert boss.dmg_base >= 0, f"bad dmg_base in {boss.boss_id}"
            assert boss.phase_count >= 1
            assert 0.0 <= boss.resistance <= 1.0, f"resistance out of range for {boss.boss_id}"


# ============================================================================
# Loader resilience
# ============================================================================


class TestLoaderResilience:
    def test_metadata_keys_skipped(self, tmp_path: Path) -> None:
        f = tmp_path / "zb.json"
        f.write_text(
            json.dumps(
                {"_metadata": {"version": "1.0"}, "dj_cyberspace": {"name": "DJ", "tier": 3}}
            )
        )
        reg = load_zone_boss_registry(f)
        assert len(reg) == 1
        assert reg.get("dj_cyberspace") is not None

    def test_skips_non_dict_entries(self, tmp_path: Path) -> None:
        f = tmp_path / "zb.json"
        f.write_text(json.dumps({"dj": {"name": "DJ"}, "list_entry": [1, 2], "str_entry": "oops"}))
        reg = load_zone_boss_registry(f)
        assert len(reg) == 1
        assert reg.get("dj") is not None

    def test_silent_skip_malformed_value(self, tmp_path: Path) -> None:
        """A field of wrong type must NOT crash the loader."""
        f = tmp_path / "zb.json"
        f.write_text(json.dumps({"dj": {"name": "DJ", "tier": "not_an_int"}}))
        reg = load_zone_boss_registry(f)
        assert len(reg) == 0

    def test_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "zb.json"
        f.write_text("{}")
        reg = load_zone_boss_registry(f)
        assert len(reg) == 0

    def test_returns_consistent_state(self, tmp_path: Path) -> None:
        a = _parse_entry("a", {"name": "A"})
        reg = ZoneBossRegistry({"a": a})
        f = tmp_path / "zb.json"
        f.write_text(json.dumps({"a": {"name": "A", "tier": 1}}))
        # Confirm both paths return equivalent lookups
        loaded = load_zone_boss_registry(f)
        assert reg.get("a") == loaded.get("a")
