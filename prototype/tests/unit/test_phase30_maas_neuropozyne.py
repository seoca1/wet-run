"""Tests for Phase 30 — Maas Neuropozyne ICE + polish improvements.

Covers:
- maas_neuropozyne ICE type (Count Zero's Maas Biolabs biotech defense — Gibson
  faction fill: tier-2 ICE for the Maas megacorp).
- Docstring additions to matrix/graph.py (68% → 100%) and
  combat/state_effects.py (32% → 100%).
- Total ICE count increments 96 → 97; maas faction is now represented.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wet_run.combat import IceRegistry, build_ice_enemy

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "combat"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ice_types() -> dict:
    with open(DATA_DIR / "ice_types.json") as f:
        return json.load(f)


@pytest.fixture
def ice_registry() -> IceRegistry:
    return IceRegistry.load(DATA_DIR / "ice_types.json")


# ---------------------------------------------------------------------------
# 1. Content addition: maas_neuropozyne ICE (Gibson-flavored biotech defense)
# ---------------------------------------------------------------------------


class TestMaasNeuropozyne:
    """Phase 30 content addition — Maas Biolabs biotech ICE for the maas faction."""

    def test_maas_neuropozyne_present(self, ice_types: dict) -> None:
        assert "maas_neuropozyne" in ice_types, "missing maas_neuropozyne entry"

    def test_maas_neuropozyne_metadata(self, ice_types: dict) -> None:
        """Tier-2 biotech ICE — fills missing maas faction representation."""
        ice = ice_types["maas_neuropozyne"]
        assert ice["name"] == "ICE — Maas Biolabs Neuropozyne (Tier-2 biotech defense)"
        assert ice["faction"] == "maas"
        assert ice["tier"] == 2
        assert ice["ice_kind"] == "standard"

    def test_maas_neuropozyne_has_biotech_skills(self, ice_types: dict) -> None:
        """Gibson-flavored: neuropozyne dependency loops (Count Zero)."""
        ice = ice_types["maas_neuropozyne"]
        skills = ice.get("skills", [])
        # biofeedback — biotech resonance attack
        assert "biofeedback" in skills, f"expected biofeedback, got {skills}"
        # addiction_loop — neuropozyne withdrawal mechanic
        assert "addiction_loop" in skills, f"expected addiction_loop, got {skills}"

    def test_maas_neuropozyne_loot_drops_dose(self, ice_types: dict) -> None:
        """Low-chance drop: neuropozyne_dose (rare crafting reagent)."""
        ice = ice_types["maas_neuropozyne"]
        loot_items = {entry["item"] for entry in ice["loot_table"]}
        assert "maas_neuropozyne_dose" in loot_items
        assert "ice_shard" in loot_items
        assert "data_fragment" in loot_items

    def test_maas_neuropozyne_builds_combatant(self, ice_registry: IceRegistry) -> None:
        """build_ice_enemy must succeed for the new ICE type."""
        enemy = build_ice_enemy("maas_neuropozyne", ice_registry)
        assert enemy.name == "ICE — Maas Biolabs Neuropozyne (Tier-2 biotech defense)"
        assert enemy.ice_kind == "standard"
        assert enemy.team == "enemy"
        # tier 2 ICE base hp=90 at grade 0
        assert enemy.hp >= 70  # 0.7 scale floor at low grade

    def test_maas_neuropozyne_scales_with_grade(self, ice_registry: IceRegistry) -> None:
        """Per build_ice_enemy scaling: hp grows with player_grade."""
        e_g3 = build_ice_enemy("maas_neuropozyne", ice_registry, player_grade=3)
        e_g7 = build_ice_enemy("maas_neuropozyne", ice_registry, player_grade=7)
        assert e_g7.hp > e_g3.hp, "grade 7 should have more HP than grade 3"


# ---------------------------------------------------------------------------
# 2. ICE count: 96 → 97 (maas faction now has 1 representative)
# ---------------------------------------------------------------------------


class TestIceCountIncrement:
    """Phase 30 bumps total ICE count from 96 to 97."""

    def test_total_ice_at_least_97(self, ice_types: dict) -> None:
        assert len(ice_types) >= 97, f"Phase 30 target 97, got {len(ice_types)}"

    def test_maas_faction_now_represented(self, ice_types: dict) -> None:
        """maas faction now has at least 1 ICE type (was 0)."""
        maas = [v for v in ice_types.values() if v.get("faction") == "maas"]
        assert len(maas) >= 1, f"Expected at least 1 maas ICE, got {len(maas)}"

    def test_maas_neuropozyne_is_tier_2(self, ice_types: dict) -> None:
        """Tier-2 ICE for early-to-mid game biotech defense."""
        ice = ice_types["maas_neuropozyne"]
        assert ice["tier"] == 2


# ---------------------------------------------------------------------------
# 3. Polish: docstring additions to matrix/graph.py
# ---------------------------------------------------------------------------


class TestGraphDocstringCoverage:
    """matrix/graph.py — interrogate 100% (was 68% pre-Phase 30)."""

    def test_dunder_methods_have_docstrings(self) -> None:
        """MatrixGraph + Edge dunder methods all need docstrings."""
        from wet_run.matrix.graph import Edge, MatrixGraph

        # Edge dunders
        assert Edge.__post_init__.__doc__, "Edge.__post_init__ missing docstring"

        # MatrixGraph dunders
        assert MatrixGraph.__post_init__.__doc__, "MatrixGraph.__post_init__ missing docstring"
        assert MatrixGraph.__contains__.__doc__, "MatrixGraph.__contains__ missing docstring"
        assert MatrixGraph.__iter__.__doc__, "MatrixGraph.__iter__ missing docstring"
        assert MatrixGraph.__len__.__doc__, "MatrixGraph.__len__ missing docstring"
        assert MatrixGraph.__repr__.__doc__, "MatrixGraph.__repr__ missing docstring"

    def test_interrogate_coverage_100(self) -> None:
        """graph.py reaches 100% interrogate coverage."""
        from interrogate.coverage import InterrogateCoverage

        ic = InterrogateCoverage(paths=["src/wet_run/matrix/graph.py"])
        result = ic.get_coverage()
        file_result = result.file_results[0]
        assert file_result.missing == 0, f"graph.py has {file_result.missing} missing docstrings"


# ---------------------------------------------------------------------------
# 4. Polish: docstring additions to combat/state_effects.py
# ---------------------------------------------------------------------------


class TestStateEffectsDocstringCoverage:
    """combat/state_effects.py — interrogate 100% (was 32% pre-Phase 30)."""

    def test_skill_handlers_have_docstrings(self) -> None:
        """All 13 private _apply_* skill handlers need docstrings."""
        from wet_run.combat import state_effects

        handler_names = [
            "_apply_damage_skill",
            "_apply_heavy_attack",
            "_apply_pierce",
            "_apply_multi_hit",
            "_apply_dot",
            "_apply_shield",
            "_apply_heal",
            "_apply_regen",
            "_apply_buff",
            "_apply_debuff",
            "_apply_stun",
            "_apply_detect",
            "_apply_lifesteal",
        ]
        for name in handler_names:
            func = getattr(state_effects, name)
            assert func.__doc__ is not None, f"state_effects.{name} has no docstring"

    def test_interrogate_coverage_100(self) -> None:
        """state_effects.py reaches 100% interrogate coverage."""
        from interrogate.coverage import InterrogateCoverage

        ic = InterrogateCoverage(paths=["src/wet_run/combat/state_effects.py"])
        result = ic.get_coverage()
        file_result = result.file_results[0]
        assert file_result.missing == 0, (
            f"state_effects.py has {file_result.missing} missing docstrings"
        )
