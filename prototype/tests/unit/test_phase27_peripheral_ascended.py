"""Tests for Phase 27 small content + polish.

Covers:
- peripheral_ascended ICE variant (ascended Jackpot-timeline boss).
- The Peripheral Ascended boss entry in zone_bosses.json.
- Improved error message in build_ice_enemy() with typo suggestions
  via difflib.get_close_matches.
- Docstring additions to audio/bgm_manager.py, audio/theme.py,
  audio/config.py (verified via runtime introspection).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roguelike_sprawl.combat import IceRegistry, build_ice_enemy

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "combat"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ice_types() -> dict:
    with open(DATA_DIR / "ice_types.json") as f:
        return json.load(f)


@pytest.fixture
def zone_bosses() -> dict:
    with open(DATA_DIR / "zone_bosses.json") as f:
        return json.load(f)


@pytest.fixture
def ice_registry() -> IceRegistry:
    return IceRegistry.load(DATA_DIR / "ice_types.json")


# ---------------------------------------------------------------------------
# 1. Content addition: peripheral_ascended ICE variant
# ---------------------------------------------------------------------------


class TestPeripheralAscended:
    """peripheral_ascended is the new ascended variant of The Peripheral (Jackpot)."""

    def test_peripheral_ascended_present(self, ice_types: dict) -> None:
        assert "peripheral_ascended" in ice_types, "missing peripheral_ascended entry"

    def test_peripheral_ascended_metadata(self, ice_types: dict) -> None:
        ice = ice_types["peripheral_ascended"]
        assert ice["name"] == "ICE — Peripheral Ascended"
        assert ice["variant"] == "ascended"
        assert ice["base_type"] == "the_peripheral"
        assert ice["ice_kind"] == "construct"

    def test_peripheral_ascended_stats_higher_than_base(self, ice_types: dict) -> None:
        """Ascended variant should be tougher than base The Peripheral (tier 6)."""
        ice = ice_types["peripheral_ascended"]
        # HP should exceed the base Peripheral (700 hp_base)
        assert ice["hp_base"] >= 700, f"expected >= 700, got {ice['hp_base']}"
        # dmg_base should exceed base Peripheral (25)
        assert ice["dmg_base"] >= 25, f"expected >= 25, got {ice['dmg_base']}"

    def test_peripheral_ascended_has_timeline_collapse_skill(self, ice_types: dict) -> None:
        """The ascended boss must have a unique timeline-themed skill."""
        ice = ice_types["peripheral_ascended"]
        skills = ice.get("skills", [])
        assert "timeline_collapse" in skills, (
            f"peripheral_ascended needs timeline_collapse skill, got {skills}"
        )

    def test_peripheral_ascended_retains_base_skills(self, ice_types: dict) -> None:
        """Per Phase 12 pattern: ascended variants retain base_type skills."""
        ice = ice_types["peripheral_ascended"]
        skills = ice.get("skills", [])
        for base_skill in ("stub_time", "lowbeer_vision", "peripheral_strike"):
            assert base_skill in skills, f"ascended missing base skill {base_skill}"

    def test_peripheral_ascended_builds_combatant(self, ice_registry: IceRegistry) -> None:
        """build_ice_enemy must succeed for the new variant."""
        enemy = build_ice_enemy("peripheral_ascended", ice_registry)
        assert enemy.name == "ICE — Peripheral Ascended"
        assert enemy.ice_kind == "construct"
        assert enemy.team == "enemy"
        assert enemy.hp >= 850  # hp_base (850) at grade 0
        assert 0.0 <= enemy.ice_resistance <= 1.0

    def test_peripheral_ascended_loot_has_timeline_echo(self, ice_types: dict) -> None:
        """Ascended endgame boss should drop the timeline_echo fragment."""
        ice = ice_types["peripheral_ascended"]
        loot_items = {entry["item"] for entry in ice["loot_table"]}
        assert "fragment.timeline_echo" in loot_items
        assert "peripheral_artifact" in loot_items

    def test_peripheral_ascended_scales_with_grade(self, ice_registry: IceRegistry) -> None:
        """Per build_ice_enemy scaling formula: hp grows with player_grade."""
        e_g1 = build_ice_enemy("peripheral_ascended", ice_registry, player_grade=1)
        e_g7 = build_ice_enemy("peripheral_ascended", ice_registry, player_grade=7)
        assert e_g7.hp > e_g1.hp, "grade 7 should have more HP than grade 1"


# ---------------------------------------------------------------------------
# 2. Content addition: the_peripheral_ascended zone boss
# ---------------------------------------------------------------------------


class TestThePeripheralAscendedBoss:
    """The Peripheral Ascended is a new zone boss matching the new ICE type."""

    def test_boss_present(self, zone_bosses: dict) -> None:
        assert "the_peripheral_ascended" in zone_bosses

    def test_boss_unlock_condition(self, zone_bosses: dict) -> None:
        boss = zone_bosses["the_peripheral_ascended"]
        assert "beat_the_peripheral" in boss["unlock_condition"]
        assert "ngplus_active" in boss["unlock_condition"]

    def test_boss_has_more_phases_than_base(self, zone_bosses: dict) -> None:
        """Ascended boss should have more phases than base Peripheral (10)."""
        base_phases = zone_bosses["the_peripheral"]["phase_count"]
        ascended_phases = zone_bosses["the_peripheral_ascended"]["phase_count"]
        assert ascended_phases > base_phases

    def test_boss_timeline_collapse_skill(self, zone_bosses: dict) -> None:
        boss = zone_bosses["the_peripheral_ascended"]
        assert "timeline_collapse" in boss["skills"]

    def test_boss_loot_drops_peripheral_artifact(self, zone_bosses: dict) -> None:
        boss = zone_bosses["the_peripheral_ascended"]
        loot_items = {entry["item"] for entry in boss["loot_table"]}
        assert "peripheral_artifact" in loot_items


# ---------------------------------------------------------------------------
# 3. Polish: improved error message with typo-tolerant suggestions
# ---------------------------------------------------------------------------


class TestBuildIceEnemyErrorMessage:
    """build_ice_enemy() should raise a clear error with close-match suggestions."""

    def test_unknown_ice_raises_keyerror(self, ice_registry: IceRegistry) -> None:
        with pytest.raises(KeyError) as exc_info:
            build_ice_enemy("definitely_not_a_real_ice_id", ice_registry)
        assert "definitely_not_a_real_ice_id" in str(exc_info.value)

    def test_unknown_ice_error_lists_available_ids(self, ice_registry: IceRegistry) -> None:
        """Error message must include 'Available:' prefix for debugging."""
        with pytest.raises(KeyError) as exc_info:
            build_ice_enemy("definitely_not_a_real_ice_id", ice_registry)
        msg = str(exc_info.value)
        assert "Available:" in msg, f"error message missing 'Available:' prefix: {msg}"

    def test_typo_error_suggests_close_match(self, ice_registry: IceRegistry) -> None:
        """Typo 'standrd' should suggest 'standard' via difflib."""
        with pytest.raises(KeyError) as exc_info:
            build_ice_enemy("standrd", ice_registry)  # missing 'a'
        msg = str(exc_info.value)
        assert "Did you mean:" in msg, f"expected 'Did you mean:' hint, got: {msg}"
        assert "standard" in msg, f"expected 'standard' suggestion, got: {msg}"

    def test_typo_error_suggests_wintermute_variant(self, ice_registry: IceRegistry) -> None:
        """Typo 'wintermut_corrupted' should suggest 'wintermute_corrupted'."""
        with pytest.raises(KeyError) as exc_info:
            build_ice_enemy("wintermut_corrupted", ice_registry)
        msg = str(exc_info.value)
        assert "wintermute_corrupted" in msg, f"expected close match suggestion, got: {msg}"

    def test_completely_unrelated_id_no_suggestion(self, ice_registry: IceRegistry) -> None:
        """Totally unrelated id should NOT include 'Did you mean:' (no close match)."""
        with pytest.raises(KeyError) as exc_info:
            build_ice_enemy("xyz123notreal", ice_registry)
        msg = str(exc_info.value)
        # cutoff=0.6 means no close matches for unrelated strings
        assert "Did you mean:" not in msg, f"unexpected suggestion for unrelated id: {msg}"

    def test_known_ice_does_not_raise(self, ice_registry: IceRegistry) -> None:
        """Sanity check — known ICE ids resolve without error."""
        enemy = build_ice_enemy("peripheral_ascended", ice_registry)
        assert enemy is not None
        assert enemy.name == "ICE — Peripheral Ascended"


# ---------------------------------------------------------------------------
# 4. Polish: docstring additions to audio/ modules
# ---------------------------------------------------------------------------


class TestAudioDocstringCoverage:
    """Verify Phase 27 docstring additions on audio/bgm_manager, theme, config."""

    def test_bgm_manager_init_has_docstring(self) -> None:
        from roguelike_sprawl.audio.bgm_manager import BgmManager

        assert BgmManager.__init__.__doc__, "BgmManager.__init__ missing docstring"

    def test_bgm_manager_is_muted_has_docstring(self) -> None:
        from roguelike_sprawl.audio.bgm_manager import BgmManager

        assert BgmManager.is_muted.fget.__doc__, "BgmManager.is_muted missing docstring"

    def test_bgm_manager_volume_has_docstring(self) -> None:
        from roguelike_sprawl.audio.bgm_manager import BgmManager

        assert BgmManager.volume.fget.__doc__, "BgmManager.volume missing docstring"

    def test_theme_player_init_has_docstring(self) -> None:
        from roguelike_sprawl.audio.theme import ThemePlayer

        assert ThemePlayer.__init__.__doc__, "ThemePlayer.__init__ missing docstring"

    def test_sound_config_post_init_has_docstring(self) -> None:
        from roguelike_sprawl.audio.config import SoundConfig

        assert SoundConfig.__post_init__.__doc__, "SoundConfig.__post_init__ missing docstring"
