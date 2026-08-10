"""Tests for Wetware Stacking Logic (ADR-0193)."""

from __future__ import annotations

import dataclasses

import pytest

from roguelike_sprawl.equipment.wetware_stacking import (
    StackedWetware,
    count_tier3_augments,
    get_all_augments,
    get_augment,
    get_augment_count,
    get_augments_by_type,
    get_max_ap_regen,
    get_new_stat_augments,
    stack_wetware,
    validate_stacking,
)


class TestAugmentQueries:
    """Augment lookup functions."""

    def test_get_augment_existing(self) -> None:
        aug = get_augment("ap_regen_lv3")
        assert aug is not None
        assert aug["name"] == "AP Regen Lv3"

    def test_get_augment_nonexistent(self) -> None:
        assert get_augment("nonexistent") is None

    def test_get_all_augments(self) -> None:
        all_augs = get_all_augments()
        assert len(all_augs) == 10, f"Expected 10 augments, got {len(all_augs)}"

    def test_get_augments_by_type(self) -> None:
        ap_augs = get_augments_by_type("ap_regen")
        assert len(ap_augs) == 1
        assert ap_augs[0]["id"] == "ap_regen_lv3"

    def test_get_augment_count(self) -> None:
        assert get_augment_count() == 10

    def test_get_new_stat_augments(self) -> None:
        new_stats = get_new_stat_augments()
        assert len(new_stats) == 3
        new_stat_ids = [a["id"] for a in new_stats]
        assert "mana_lv3" in new_stat_ids
        assert "armor_lv3" in new_stat_ids
        assert "focus_lv3" in new_stat_ids


class TestWetwareStacking:
    """Stack wetware augments and verify combined effects."""

    def test_stack_empty(self) -> None:
        stacked = stack_wetware([])
        assert stacked.augment_count == 0

    def test_stack_single_ap_regen(self) -> None:
        stacked = stack_wetware(["ap_regen_lv3"])
        assert stacked.ap_regen == 0.5
        assert stacked.augment_count == 1

    def test_stack_single_crit(self) -> None:
        stacked = stack_wetware(["crit_lv3"])
        assert stacked.crit_chance == 0.15
        assert stacked.crit_damage == 0.5

    def test_stack_single_dodge(self) -> None:
        stacked = stack_wetware(["dodge_lv3"])
        assert stacked.dodge == 0.20

    def test_stack_single_hp(self) -> None:
        stacked = stack_wetware(["max_hp_lv3"])
        assert stacked.hp_bonus == 30

    def test_stack_single_shield(self) -> None:
        stacked = stack_wetware(["shield_lv3"])
        assert stacked.shield == 0.25

    def test_stack_single_speed(self) -> None:
        stacked = stack_wetware(["speed_lv3"])
        assert stacked.speed == 0.30

    def test_stack_single_healing(self) -> None:
        stacked = stack_wetware(["healing_lv3"])
        assert stacked.healing == 0.30

    def test_stack_single_mana(self) -> None:
        stacked = stack_wetware(["mana_lv3"])
        assert stacked.mana == 1

    def test_stack_single_armor(self) -> None:
        stacked = stack_wetware(["armor_lv3"])
        assert stacked.armor == 0.25

    def test_stack_single_focus(self) -> None:
        stacked = stack_wetware(["focus_lv3"])
        assert stacked.focus == 0.30

    def test_stack_multiple_ap_regen(self) -> None:
        stacked = stack_wetware(["ap_regen_lv3", "ap_regen_lv3"])
        assert stacked.ap_regen == 1.0

    def test_stack_hp_bonus_aditive(self) -> None:
        stacked = stack_wetware(["max_hp_lv3", "max_hp_lv3", "max_hp_lv3"])
        assert stacked.hp_bonus == 90

    def test_stack_mana_aditive(self) -> None:
        stacked = stack_wetware(["mana_lv3", "mana_lv3"])
        assert stacked.mana == 2

    def test_stack_unknown_augment_ignored(self) -> None:
        stacked = stack_wetware(["ap_regen_lv3", "nonexistent"])
        assert stacked.ap_regen == 0.5
        assert stacked.augment_count == 2


class TestStackingCaps:
    """Verify caps are applied on stacking."""

    def test_dodge_capped(self) -> None:
        stacked = stack_wetware(["dodge_lv3"] * 10)
        assert stacked.dodge == 0.95

    def test_shield_capped(self) -> None:
        stacked = stack_wetware(["shield_lv3"] * 10)
        assert stacked.shield == 0.95

    def test_healing_capped(self) -> None:
        stacked = stack_wetware(["healing_lv3"] * 10)
        assert stacked.healing == 1.0

    def test_armor_capped(self) -> None:
        stacked = stack_wetware(["armor_lv3"] * 10)
        assert stacked.armor == 1.0

    def test_focus_capped(self) -> None:
        stacked = stack_wetware(["focus_lv3"] * 10)
        assert stacked.focus == 1.0

    def test_speed_capped(self) -> None:
        stacked = stack_wetware(["speed_lv3"] * 10)
        assert stacked.speed == 1.0

    def test_ap_regen_capped(self) -> None:
        stacked = stack_wetware(["ap_regen_lv3"] * 10)
        assert stacked.ap_regen == 1.0


class TestStackingValidation:
    """Validate stacking inputs."""

    def test_validate_stacking_all_valid(self) -> None:
        assert validate_stacking(["ap_regen_lv3", "crit_lv3", "dodge_lv3"]) is True

    def test_validate_stacking_with_invalid(self) -> None:
        assert validate_stacking(["ap_regen_lv3", "nonexistent"]) is False

    def test_count_tier3_augments(self) -> None:
        count = count_tier3_augments(["ap_regen_lv3", "crit_lv3", "nonexistent"])
        assert count == 2

    def test_get_max_ap_regen(self) -> None:
        assert get_max_ap_regen() == 0.5


class TestStackedWetwareResult:
    """Verify StackedWetware dataclass."""

    def test_default_values(self) -> None:
        stacked = StackedWetware()
        assert stacked.ap_regen == 0.0
        assert stacked.hp_bonus == 0
        assert stacked.augment_count == 0

    def test_immutability(self) -> None:
        stacked = stack_wetware(["ap_regen_lv3"])
        with pytest.raises(dataclasses.FrozenInstanceError):
            stacked.ap_regen = 0.9  # type: ignore[misc]
