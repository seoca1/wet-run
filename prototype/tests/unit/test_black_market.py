"""Tests for the black_market stage (v0.5 expansion)."""

from __future__ import annotations

from wet_run.black_market import (
    MARKET_INVENTORY,
    BlackMarketCategory,
    list_by_category,
)


class TestMarketInventory:
    def test_nonempty(self) -> None:
        assert len(MARKET_INVENTORY) >= 3, "Should have at least 3 market items"

    def test_all_categories_present(self) -> None:
        cats = {item.category for item in MARKET_INVENTORY.values()}
        assert BlackMarketCategory.PROGRAMS in cats
        assert BlackMarketCategory.DECK_UPGRADES in cats
        assert BlackMarketCategory.INTEL in cats

    def test_credit_costs_positive(self) -> None:
        for item in MARKET_INVENTORY.values():
            assert item.credit_cost > 0, f"{item.id} has non-positive credit cost"

    def test_material_costs_nonnegative(self) -> None:
        for item in MARKET_INVENTORY.values():
            for mat_id, count in item.material_cost:
                assert count >= 0, f"{item.id} has negative material count for {mat_id}"


class TestListByCategory:
    def test_programs(self) -> None:
        programs = list_by_category(BlackMarketCategory.PROGRAMS)
        assert all(item.category == BlackMarketCategory.PROGRAMS for item in programs)
        assert len(programs) >= 1

    def test_deck_upgrades(self) -> None:
        upgrades = list_by_category(BlackMarketCategory.DECK_UPGRADES)
        assert all(item.category == BlackMarketCategory.DECK_UPGRADES for item in upgrades)
        assert len(upgrades) >= 1

    def test_intel(self) -> None:
        intel = list_by_category(BlackMarketCategory.INTEL)
        assert all(item.category == BlackMarketCategory.INTEL for item in intel)
        assert len(intel) >= 1

    def test_categories_partition_inventory(self) -> None:
        """Every inventory item appears in exactly one category list."""
        all_by_cat = (
            list_by_category(BlackMarketCategory.PROGRAMS)
            + list_by_category(BlackMarketCategory.DECK_UPGRADES)
            + list_by_category(BlackMarketCategory.INTEL)
        )
        assert len(all_by_cat) == len(MARKET_INVENTORY)


class TestSpecificItems:
    def test_strike_program(self) -> None:
        strike = MARKET_INVENTORY["market.program.strike"]
        assert strike.category == BlackMarketCategory.PROGRAMS
        assert strike.credit_cost <= 500, "T1 program should be cheap"
        assert strike.material_cost, "T1 program should require materials"

    def test_deck_t2_upgrade(self) -> None:
        upgrade = MARKET_INVENTORY["market.deck.t2"]
        assert upgrade.category == BlackMarketCategory.DECK_UPGRADES
        assert upgrade.credit_cost >= 1000, "T2 deck upgrade is expensive"
        assert "refined_neural" in dict(upgrade.material_cost), "T2 requires refined_neural"

    def test_intel_freeside(self) -> None:
        intel = MARKET_INVENTORY["market.intel.freeside_route"]
        assert intel.category == BlackMarketCategory.INTEL
        assert intel.material_cost == (), "Intel should not require materials"
