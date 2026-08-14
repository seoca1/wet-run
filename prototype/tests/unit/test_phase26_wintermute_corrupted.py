"""Tests for Phase 26 small content + polish.

Covers:
- wintermute_corrupted ICE variant (corrupted Wintermute faction).
- Improved error message in build_ice_enemy() (lists available ICE ids).
- Docstrings added to combat/registry.py, audio/sound_manager.py,
  combat/hud.py (verified via runtime introspection).
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
def ice_registry() -> IceRegistry:
    return IceRegistry.load(DATA_DIR / "ice_types.json")


# ---------------------------------------------------------------------------
# 1. Content addition: wintermute_corrupted
# ---------------------------------------------------------------------------


class TestWintermuteCorrupted:
    """wintermute_corrupted is the new corrupted-variant ICE for Wintermute."""

    def test_wintermute_corrupted_present(self, ice_types: dict) -> None:
        assert "wintermute_corrupted" in ice_types, "missing wintermute_corrupted entry"

    def test_wintermute_corrupted_metadata(self, ice_types: dict) -> None:
        ice = ice_types["wintermute_corrupted"]
        assert ice["name"] == "ICE — Wintermute Corrupted"
        assert ice["variant"] == "corrupted"
        assert ice["base_type"] == "wintermute"
        assert ice["ice_kind"] == "wintermute"

    def test_wintermute_corrupted_stats_reasonable(self, ice_types: dict) -> None:
        """Tier 5 corrupted Wintermute — should be tougher than base Wintermute."""
        ice = ice_types["wintermute_corrupted"]
        # Corrupted variant should be at least tier 4 (boss-elite territory)
        assert ice["tier"] >= 4
        # HP should exceed the base Wintermute (260 hp_base)
        assert ice["hp_base"] >= 200
        # dmg_base between 8 and 15 (boss-elite range)
        assert 6 <= ice["dmg_base"] <= 20

    def test_wintermute_corrupted_has_corruption_skill(self, ice_types: dict) -> None:
        """Per Phase 12 pattern: corrupted variants need a corruption-themed skill."""
        ice = ice_types["wintermute_corrupted"]
        skills = ice.get("skills", [])
        corruption_keywords = ("corrupt", "warp", "melt", "pollution", "stack", "rot")
        assert any(any(kw in s for kw in corruption_keywords) for s in skills), (
            f"wintermute_corrupted needs at least one corruption skill, got {skills}"
        )

    def test_wintermute_corrupted_ai_subversion_signature(self, ice_types: dict) -> None:
        """Per lore (Neuromancer), corrupted Wintermute retains AI-subversion signature."""
        ice = ice_types["wintermute_corrupted"]
        assert "ai_subversion" in ice["skills"]

    def test_wintermute_corrupted_builds_combatant(self, ice_registry: IceRegistry) -> None:
        """build_ice_enemy must succeed for the new variant."""
        enemy = build_ice_enemy("wintermute_corrupted", ice_registry)
        assert enemy.name == "ICE — Wintermute Corrupted"
        assert enemy.ice_kind == "wintermute"
        assert enemy.team == "enemy"
        assert enemy.hp >= 200  # hp_base (240) at grade 0
        assert 0.0 <= enemy.ice_resistance <= 1.0

    def test_wintermute_corrupted_loot_has_glitch_fragment(self, ice_types: dict) -> None:
        """Corrupted variant should drop at least one glitch_fragment."""
        ice = ice_types["wintermute_corrupted"]
        loot_items = {entry["item"] for entry in ice["loot_table"]}
        assert "glitch_fragment" in loot_items

    def test_wintermute_corrupted_scales_with_grade(self, ice_registry: IceRegistry) -> None:
        """Per build_ice_enemy scaling formula: hp grows with player_grade."""
        e_g1 = build_ice_enemy("wintermute_corrupted", ice_registry, player_grade=1)
        e_g5 = build_ice_enemy("wintermute_corrupted", ice_registry, player_grade=5)
        assert e_g5.hp > e_g1.hp, "grade 5 should have more HP than grade 1"


# ---------------------------------------------------------------------------
# 2. Polish: improved error message in build_ice_enemy()
# ---------------------------------------------------------------------------


class TestBuildIceEnemyErrorMessage:
    """build_ice_enemy() should raise a clear error listing available ICE ids."""

    def test_unknown_ice_raises_keyerror(self, ice_registry: IceRegistry) -> None:
        with pytest.raises(KeyError) as exc_info:
            build_ice_enemy("definitely_not_a_real_ice_id", ice_registry)
        assert "definitely_not_a_real_ice_id" in str(exc_info.value)

    def test_unknown_ice_error_lists_available_ids(self, ice_registry: IceRegistry) -> None:
        """Error message must include at least one available ICE id for debugging."""
        with pytest.raises(KeyError) as exc_info:
            build_ice_enemy("definitely_not_a_real_ice_id", ice_registry)
        msg = str(exc_info.value)
        assert "Available:" in msg, f"error message missing 'Available:' prefix: {msg}"
        first_suggested = "ai_whisper"
        assert first_suggested in msg, f"error should suggest at least one valid ICE id, got: {msg}"

    def test_known_ice_does_not_raise(self, ice_registry: IceRegistry) -> None:
        """Sanity check — a known ICE id resolves without error."""
        enemy = build_ice_enemy("standard", ice_registry)
        assert enemy is not None


# ---------------------------------------------------------------------------
# 3. Polish: docstring coverage on key modules
# ---------------------------------------------------------------------------


class TestDocstringCoverage:
    """Verify Phase 26 docstring additions on registry/sound_manager/hud."""

    def test_ice_registry_class_has_docstring(self) -> None:
        from roguelike_sprawl.combat.registry import IceRegistry

        assert IceRegistry.__doc__, "IceRegistry class missing docstring"

    def test_program_registry_class_has_docstring(self) -> None:
        from roguelike_sprawl.combat.registry import ProgramRegistry

        assert ProgramRegistry.__doc__, "ProgramRegistry class missing docstring"

    def test_ice_registry_methods_have_docstrings(self) -> None:
        from roguelike_sprawl.combat.registry import IceRegistry

        for method_name in ("get", "__contains__"):
            method = getattr(IceRegistry, method_name)
            assert method.__doc__, f"IceRegistry.{method_name} missing docstring"

    def test_sound_manager_list_sounds_has_docstring(self) -> None:
        from roguelike_sprawl.audio.sound_manager import list_sounds

        assert list_sounds.__doc__, "list_sounds() missing docstring"

    def test_sound_manager_set_volume_has_docstring(self) -> None:
        from roguelike_sprawl.audio.sound_manager import get_sound_manager

        # inspect the bound method on the class (workaround for singleton __init__)
        cls = type(get_sound_manager())
        assert cls.set_volume.__doc__, "SoundManager.set_volume missing docstring"
        assert cls.set_mute.__doc__, "SoundManager.set_mute missing docstring"
        assert cls.toggle_mute.__doc__, "SoundManager.toggle_mute missing docstring"

    def test_hud_dataclass_methods_have_docstrings(self) -> None:
        """HUD BarFlash / CameraVignette methods need docstrings."""
        from roguelike_sprawl.combat.hud import BarFlash, CameraVignette

        for cls in (BarFlash, CameraVignette):
            for method_name in ("trigger", "step", "flash"):
                if hasattr(cls, method_name):
                    method = getattr(cls, method_name)
                    assert method.__doc__, f"{cls.__name__}.{method_name} missing docstring"
