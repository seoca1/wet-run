"""Tests for the 5-grade progression simulator."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def grades_module():
    spec = importlib.util.spec_from_file_location(
        "combat_grades",
        Path(__file__).parent.parent.parent / "scripts" / "combat_grades.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_grades_table_has_five_entries(grades_module) -> None:
    assert len(grades_module.GRADES) == 5
    labels = [g["label"] for g in grades_module.GRADES]
    assert "1-up 신참" in labels
    assert "5-up 전설" in labels


def test_grade_ppl_monotonic(grades_module) -> None:
    """PPL strictly increases across grades."""
    ppls = [grades_module._ppl_for_grade(g) for g in grades_module.GRADES]
    for a, b in zip(ppls, ppls[1:]):
        assert b > a, f"PPL not monotonic: {ppls}"


def test_grade_hp_monotonic(grades_module) -> None:
    """HP pool strictly increases across grades."""
    hps = [g["max_hp"] for g in grades_module.GRADES]
    for a, b in zip(hps, hps[1:]):
        assert b > a, f"HP not monotonic: {hps}"


def test_grade_attack_damage_monotonic(grades_module) -> None:
    atks = [g["auto_attack_damage"] for g in grades_module.GRADES]
    for a, b in zip(atks, atks[1:]):
        assert b > a, f"ATK not monotonic: {atks}"


def test_1up_ppl_matches_formula(grades_module) -> None:
    """1-up PPL is 3 + 2*2 + 1 = 8 with wisp+strike T1, T1 wetware."""
    g1 = grades_module.GRADES[0]
    ppl = grades_module._ppl_for_grade(g1)
    assert ppl == 8


def test_5up_has_construct(grades_module) -> None:
    g5 = grades_module.GRADES[4]
    assert g5["construct_tier"] == 5
    assert "kraken" in g5["program_ids"]


def test_run_one_grade_returns_expected_fields(grades_module) -> None:
    from wet_run.combat.registry import ProgramRegistry
    from wet_run.portraits import PortraitManager

    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    programs = ProgramRegistry.load(data_dir / "programs" / "programs.json")
    ice = grades_module.IceRegistry.load(data_dir / "combat" / "ice_types.json")
    portraits = PortraitManager(data_dir=data_dir / "portraits")
    enemy = grades_module._build_enemy("standard", ice, portraits)

    summary, _ = grades_module._run_one_grade(
        grades_module.GRADES[4],
        enemy,
        programs,
        max_tick_ms=20000,
        rng_seed=42,
    )
    for key in (
        "grade",
        "ppl",
        "outcome",
        "time_s",
        "skill_uses",
        "damage_dealt",
        "damage_taken",
        "player_hp_remaining",
        "heal_potential",
    ):
        assert key in summary
    assert summary["outcome"] == "victory"
    assert summary["damage_dealt"] == enemy.max_hp


def test_run_one_grade_creates_fresh_enemy_per_call(grades_module) -> None:
    """The enemy is not the template; a fresh Combatant is built per call."""
    from wet_run.combat.registry import ProgramRegistry
    from wet_run.portraits import PortraitManager

    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    programs = ProgramRegistry.load(data_dir / "programs" / "programs.json")
    ice = grades_module.IceRegistry.load(data_dir / "combat" / "ice_types.json")
    portraits = PortraitManager(data_dir=data_dir / "portraits")
    enemy_template = grades_module._build_enemy("standard", ice, portraits)
    enemy_template.hp = 1  # poison the template

    _, returned_enemy = grades_module._run_one_grade(
        grades_module.GRADES[0],
        enemy_template,
        programs,
        max_tick_ms=20000,
        rng_seed=42,
    )
    # The fresh enemy starts at max_hp (80) — not the poisoned 1.
    # After combat, hp may be 0 (victory), so we check max_hp.
    assert returned_enemy.max_hp == 80
    assert returned_enemy is not enemy_template


def test_avatar_renders_all_grades(grades_module) -> None:
    for grade in grades_module.GRADES:
        out = grades_module._print_avatar_for_grade(grade)
        assert "◉P◉" in out
        assert f"DK{grade['deck_tier']}" in out
        assert grade["label"]  # not empty


def test_tier_glyph_uses_program_id(grades_module) -> None:
    g1 = grades_module._tier_glyph("wisp", 1)
    g2 = grades_module._tier_glyph("goliath", 3)
    g3 = grades_module._tier_glyph("kraken", 5)
    assert "W" in g1
    assert "G" in g2
    assert "K" in g3


def test_heal_potential_scales_with_hp(grades_module) -> None:
    """HEAL = 20% of max_hp — bigger pool means more recovery."""
    heals = [g["max_hp"] // 5 for g in grades_module.GRADES]
    for a, b in zip(heals, heals[1:]):
        assert b > a, f"HEAL not monotonic: {heals}"


def test_aftermath_for_all_victory_grades(grades_module) -> None:
    """Aftermath data exists for all 5 grades."""
    for key in ("1-up", "2-up", "3-up", "4-up", "5-up"):
        assert key in grades_module.AFTERMATHS
        after = grades_module.AFTERMATHS[key]
        assert "narrative" in after
        assert "ko" in after
        assert "character" in after
        assert "reaction" in after
        assert "reaction_ko" in after


def test_5up_dominates_1up(grades_module) -> None:
    """5-up clearly outperforms 1-up in time and damage taken."""
    from wet_run.combat.registry import ProgramRegistry
    from wet_run.portraits import PortraitManager

    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    programs = ProgramRegistry.load(data_dir / "programs" / "programs.json")
    ice = grades_module.IceRegistry.load(data_dir / "combat" / "ice_types.json")
    portraits = PortraitManager(data_dir=data_dir / "portraits")
    enemy_template = grades_module._build_enemy("standard", ice, portraits)

    s1, _ = grades_module._run_one_grade(
        grades_module.GRADES[0],
        enemy_template,
        programs,
        max_tick_ms=20000,
        rng_seed=42,
    )
    s5, _ = grades_module._run_one_grade(
        grades_module.GRADES[4],
        enemy_template,
        programs,
        max_tick_ms=20000,
        rng_seed=42,
    )
    # 5-up is faster and takes less damage.
    assert s5["time_s"] < s1["time_s"]
    assert s5["damage_taken"] < s1["damage_taken"]
    # 5-up has more HP to start with, so it ends with more HP.
    assert s5["player_hp_remaining"] > s1["player_hp_remaining"]
