"""Tests for F.4 boss dispatch integration (ADR-0190 Axis 4).

Covers:
    - :func:`is_boss_id` over all 14 boss entries (11 zone + 3 expansion)
    - :func:`build_boss_combatant_from_id` returning a Combatant for each
      boss registry; ``None`` for non-boss ids and empty strings
    - Tier-aware grade scaling: HP scales linearly above declared tier,
      plateaus at base when player is below tier
    - Lazy-load behavior of ``_zone_boss_registry`` module cache
"""

from __future__ import annotations

import pytest

from wet_run.combat.boss_dispatch import (
    build_boss_combatant_from_id,
    is_boss_id,
    reset_zone_registry_cache,
)
from wet_run.combat.boss_registry import load_zone_boss_registry

# ============================================================================
# Boss-id detection
# ============================================================================


class TestIsBossIdZoneBosses:
    @pytest.mark.parametrize(
        "boss_id",
        [
            "dj_cyberspace",        # tier=3 surface
            "sense_net_sentinel",   # tier=4 deep
            "hosaka_memory_vault",  # tier=4 mid
            "locus_construct",      # tier=5 core
            "tessier_child",        # tier=5 ta
            "orbit_ghost",          # tier=5 freeside
        ],
    )
    def test_per_zone_boss(self, boss_id: str) -> None:
        assert is_boss_id(boss_id) is True

    @pytest.mark.parametrize(
        "boss_id",
        [
            "wintermute_ascended",      # tier=5 (no zone)
            "ta_prime_ascended",        # tier=5 (no zone)
            "neuromancer_ascended",     # tier=5 (no zone)
            "the_peripheral",           # tier=6 (secret)
            "the_peripheral_ascended",  # tier=6 (ascended secret)
        ],
    )
    def test_ascended_and_secret(self, boss_id: str) -> None:
        assert is_boss_id(boss_id) is True


class TestIsBossIdBossExpansion:
    @pytest.mark.parametrize(
        "boss_id",
        ["neuromancer", "loa_baron", "black_baron"],
    )
    def test_f4_profiles(self, boss_id: str) -> None:
        assert is_boss_id(boss_id) is True


class TestIsBossIdNonBoss:
    @pytest.mark.parametrize(
        "ice_id",
        ["standard", "watchdog", "goliath", "dixie", "wisp", "raven"],
    )
    def test_standard_ice_ids(self, ice_id: str) -> None:
        assert is_boss_id(ice_id) is False

    def test_unknown_id(self) -> None:
        assert is_boss_id("not_a_boss_xyz") is False

    def test_empty_string(self) -> None:
        assert is_boss_id("") is False

    def test_non_string(self) -> None:
        assert is_boss_id(None) is False  # type: ignore[arg-type]
        assert is_boss_id(123) is False  # type: ignore[arg-type]


# ============================================================================
# Boss combatant construction
# ============================================================================


class TestBuildBossCombatantReturnsCombatant:
    @pytest.mark.parametrize(
        "boss_id",
        [
            "dj_cyberspace",
            "orbit_ghost",
            "the_peripheral",
            "neuromancer",
            "black_baron",
        ],
    )
    def test_returns_combatant(self, boss_id: str) -> None:
        c = build_boss_combatant_from_id(boss_id)
        assert c is not None
        assert c.id == boss_id
        assert c.team == "enemy"
        # zone-boss path sets ice_kind="boss"; boss_expansion uses
        # "boss_<id>" convention. Both signal boss-level encounter.
        assert c.ice_kind in ("boss", f"boss_{boss_id}"), (
            f"unexpected ice_kind {c.ice_kind!r} for {boss_id}"
        )
        assert c.hp > 0
        assert c.max_hp == c.hp
        # Color varies per phase (boss_expansion) vs fixed (zone-boss).
        # Just check the color is non-default (a vivid tone).
        assert c.color != (0, 0, 0), "boss combatant should have a visible color"


class TestBuildBossCombatantNoneCases:
    def test_unknown_returns_none(self) -> None:
        assert build_boss_combatant_from_id("not_a_boss_xyz") is None

    def test_empty_string_returns_none(self) -> None:
        assert build_boss_combatant_from_id("") is None

    def test_non_string_returns_none(self) -> None:
        assert build_boss_combatant_from_id(None) is None  # type: ignore[arg-type]


# ============================================================================
# Grade scaling
# ============================================================================


class TestZoneBossScaling:
    """Tier-aware linear scaling (max(0, grade - tier) increment)."""

    def test_no_grade_uses_base(self) -> None:
        c = build_boss_combatant_from_id("dj_cyberspace")
        assert c is not None
        assert c.hp == 150  # hp_base
        assert c.auto_attack_damage == 7  # dmg_base

    def test_player_at_tier_uses_base(self) -> None:
        # DJ Cyberspace is tier=3; player grade=3 means at-tier
        c = build_boss_combatant_from_id("dj_cyberspace", player_grade=3)
        assert c is not None
        assert c.hp == 150
        assert c.auto_attack_damage == 7

    def test_player_below_tier_still_uses_base(self) -> None:
        # Boss resists downscaling — base stats preserved
        c = build_boss_combatant_from_id("dj_cyberspace", player_grade=1)
        assert c is not None
        assert c.hp == 150

    def test_player_above_tier_scales(self) -> None:
        # Tier=3, grade=5: diff=2, +25 hp/grade = 150 + 50 = 200
        c = build_boss_combatant_from_id("dj_cyberspace", player_grade=5)
        assert c is not None
        assert c.hp == 200
        # DMG: 7 + 2*2 = 11
        assert c.auto_attack_damage == 11

    def test_player_high_above_tier(self) -> None:
        # Tier=3, grade=10: diff=7, +25*7 = 175
        c = build_boss_combatant_from_id("dj_cyberspace", player_grade=10)
        assert c is not None
        assert c.hp == 150 + 25 * 7

    def test_orbit_ghost_tier5_scaling(self) -> None:
        # orbit_ghost tier=5, hp_base=400, hp_per_grade=60
        c = build_boss_combatant_from_id("orbit_ghost", player_grade=10)
        assert c is not None
        # diff=5, hp=400+60*5=700
        assert c.hp == 700


class TestBossExpansionScaling:
    """boss_expansion uses (1 + (grade-1)*0.15) factor inside
    build_boss_combatant, not the zone-boss tier-aware formula.
    """

    def test_at_grade1_uses_base(self) -> None:
        c = build_boss_combatant_from_id("neuromancer", player_grade=1)
        assert c is not None
        assert c.hp == 400  # hp_base from NEUROMANCER_PROFILE

    def test_loa_baron_base(self) -> None:
        c = build_boss_combatant_from_id("loa_baron", player_grade=1)
        assert c is not None
        assert c.hp == 300  # hp_base from LOA_BARON_PROFILE


# ============================================================================
# Module-level lazy load
# ============================================================================


class TestLazyZoneRegistryLoad:
    def test_reset_then_loads_on_demand(self) -> None:
        import wet_run.combat.boss_dispatch as mod

        mod._zone_boss_registry = None
        # First call loads from disk
        is_boss_id("dj_cyberspace")
        assert mod._zone_boss_registry is not None

    def test_cache_persists_across_calls(self) -> None:
        import wet_run.combat.boss_dispatch as mod

        mod._zone_boss_registry = None
        is_boss_id("dj_cyberspace")
        first_ref = mod._zone_boss_registry
        # Second call uses cached registry
        is_boss_id("tessier_child")
        assert mod._zone_boss_registry is first_ref

    def test_reset_zone_registry_cache_helper(self) -> None:
        import wet_run.combat.boss_dispatch as mod

        is_boss_id("dj_cyberspace")
        assert mod._zone_boss_registry is not None
        reset_zone_registry_cache()
        assert mod._zone_boss_registry is None


# ============================================================================
# Registry parity with project data
# ============================================================================


class TestRegistryParity:
    def test_zone_registry_entries_all_resolvable(self) -> None:
        """Every boss_id in zone_bosses.json must resolve via dispatch."""
        reg = load_zone_boss_registry()
        for boss in reg.list_all():
            c = build_boss_combatant_from_id(boss.boss_id)
            assert c is not None, f"{boss.boss_id} missing dispatch"
            assert c.id == boss.boss_id
            assert c.hp == boss.hp_base
            assert c.base_defense == boss.defense
