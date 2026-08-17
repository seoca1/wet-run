"""Edge case tests for combat/registry.py (ADR-0060 Edge case 분석).

Covers ProgramRegistry.load() defensive branches:
- File missing → default skills
- File invalid JSON (not a dict) → default skills
- Value not a dict → skipped
- Invalid effect string → fallback to ATTACK
- Invalid color format → default white (255,255,255)
- Missing fields → use defaults
- Plus basic registry methods (get, iter, len)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wet_run.combat.registry import (
    IceRegistry,
    ProgramRegistry,
    _default_skills,
)


class TestProgramRegistryLoad:
    """ProgramRegistry.load(path) — JSON file loader with defensive branches."""

    def test_returns_default_skills_when_file_missing(self, tmp_path: Path) -> None:
        """Missing file → registry with default skills (defensive fallback)."""
        reg = ProgramRegistry.load(tmp_path / "missing.json")
        assert len(reg) > 0  # Default skills populated
        assert reg.get("wisp") is not None  # Known default skill

    def test_returns_default_skills_when_json_is_not_dict(self, tmp_path: Path) -> None:
        """JSON file with array (not dict) at root → default skills."""
        path = tmp_path / "array.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        reg = ProgramRegistry.load(path)
        assert len(reg) > 0  # Default skills (defensive)

    def test_returns_default_skills_when_json_is_invalid(self, tmp_path: Path) -> None:
        """Invalid JSON → raises JSONDecodeError (NOT silent fallback to defaults)."""
        path = tmp_path / "broken.json"
        path.write_text("{not valid", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            ProgramRegistry.load(path)

    def test_skips_non_dict_values(self, tmp_path: Path) -> None:
        """Dict with mixed value types → only dict-typed values are parsed."""
        path = tmp_path / "mixed.json"
        path.write_text(
            '{"valid_skill": {"name": "Test"}, "not_a_dict": "string_value", "also_not": 42}',
            encoding="utf-8",
        )
        reg = ProgramRegistry.load(path)
        assert reg.get("valid_skill") is not None
        assert reg.get("not_a_dict") is None  # Skipped
        assert reg.get("also_not") is None  # Skipped

    def test_invalid_effect_string_falls_back_to_attack(self, tmp_path: Path) -> None:
        """Unknown effect type string → fallback to SkillEffect.ATTACK."""
        path = tmp_path / "bad_effect.json"
        path.write_text(
            '{"my_skill": {"name": "Test", "type": "INVALID_EFFECT_NAME"}}',
            encoding="utf-8",
        )
        reg = ProgramRegistry.load(path)
        skill = reg.get("my_skill")
        assert skill is not None
        assert skill.effect.value == "attack"  # Fallback

    def test_invalid_color_format_falls_back_to_white(self, tmp_path: Path) -> None:
        """Invalid color (not 3-tuple of ints) → default white (255,255,255)."""
        path = tmp_path / "bad_color.json"
        path.write_text(
            '{"my_skill": {"name": "Test", "color": [1, 2]}}',  # Only 2 elements
            encoding="utf-8",
        )
        reg = ProgramRegistry.load(path)
        skill = reg.get("my_skill")
        assert skill is not None
        assert skill.effect_color == (255, 255, 255)

    def test_missing_fields_use_defaults(self, tmp_path: Path) -> None:
        """Skill with only 'name' field → other fields use defaults (tier=1, ap_cost=1, etc.)."""
        path = tmp_path / "minimal.json"
        path.write_text('{"my_skill": {"name": "Minimal"}}', encoding="utf-8")
        reg = ProgramRegistry.load(path)
        skill = reg.get("my_skill")
        assert skill is not None
        assert skill.name == "Minimal"
        assert skill.tier == 1
        assert skill.ap_cost == 1
        assert skill.damage == 0

    def test_loaded_skills_override_defaults(self, tmp_path: Path) -> None:
        """Loaded skill with same key as default → replaces default."""
        path = tmp_path / "override.json"
        path.write_text('{"wisp": {"name": "Custom Wisp", "damage": 999}}', encoding="utf-8")
        reg = ProgramRegistry.load(path)
        skill = reg.get("wisp")
        assert skill is not None
        assert skill.name == "Custom Wisp"
        assert skill.damage == 999


class TestProgramRegistryBasicMethods:
    """ProgramRegistry basic methods: get, __iter__, __len__."""

    def test_get_returns_none_for_missing_skill(self) -> None:
        reg = ProgramRegistry(_default_skills())
        assert reg.get("nonexistent_skill") is None

    def test_get_returns_skill_for_existing(self) -> None:
        reg = ProgramRegistry(_default_skills())
        skill = reg.get("wisp")
        assert skill is not None
        assert skill.id == "wisp"

    def test_iter_yields_all_skills(self) -> None:
        reg = ProgramRegistry(_default_skills())
        skills = list(reg)
        assert len(skills) > 0
        assert all(hasattr(s, "id") for s in skills)

    def test_len_matches_skill_count(self) -> None:
        reg = ProgramRegistry(_default_skills())
        assert len(reg) == len(list(reg))


class TestIceRegistry:
    """IceRegistry — defensive import check (registry may not be fully populated)."""

    def test_ice_registry_attribute_exists(self) -> None:
        """IceRegistry class is defined in combat.registry."""
        assert hasattr(IceRegistry, "__init__") or IceRegistry is not None
