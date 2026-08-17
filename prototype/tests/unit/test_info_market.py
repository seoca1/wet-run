"""Tests for the Info Market faction-discount system (P2 #16).

Covers:
- Data loading from market.json
- MarketItem.discounted_price() per reputation tier
- InfoMarket.can_purchase / purchase atomicity
- Legacy state handling (no .reputation)
- Edge cases: T5 crafting-only, missing fields, corrupt JSON
- Hub integration: market summary string formatting
- Cache invalidation for tests
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wet_run.crafting.info_market import (
    _TIER_TO_MULTIPLIER,
    DISCOUNT_DENOM,
    InfoMarket,
    MarketItem,
)
from wet_run.engine.state import AppState
from wet_run.matrix.node import Faction


@pytest.fixture(autouse=True)
def _reset_market_cache():
    """Reset the module-level market cache between tests."""
    InfoMarket._reset_cache()
    yield
    InfoMarket._reset_cache()


# ============================================================================
# Discount / markup constant sanity
# ============================================================================


class TestDiscountConstants:
    def test_discount_denom_allows_up_to_50_percent_off(self) -> None:
        # 100 (ALLIED cap) / 200 = 0.5 → 50% off
        assert DISCOUNT_DENOM == 200
        # Verify: a +100 score yields multiplier 0.5
        assert 1.0 - (100 / DISCOUNT_DENOM) == 0.5

    def test_tier_to_multiplier_covers_all_tiers(self) -> None:
        # Every tier in reputation_tier() should have a multiplier
        # (no missing entries → silent 1.0 fallback for hostile etc).
        expected_tiers = {
            "ALLIED",
            "FRIENDLY",
            "TRUSTED",
            "NEUTRAL",
            "HOSTILE",
            "ENEMY",
            "OUTCAST",
        }
        assert set(_TIER_TO_MULTIPLIER.keys()) == expected_tiers

    def test_multiplier_range_is_sane(self) -> None:
        """All multipliers must lie in [0.5, 1.5] — no extreme swings."""
        for mult in _TIER_TO_MULTIPLIER.values():
            assert 0.5 <= mult <= 1.5, f"multiplier {mult} out of safe range"


# ============================================================================
# MarketItem.discounted_price
# ============================================================================


class TestMarketItemDiscountedPrice:
    def test_neutral_rep_gives_base_price(self) -> None:
        item = MarketItem(
            item_id="x",
            name="X",
            base_price=100,
            tier_level=1,
            available=True,
            faction=Faction.HOSAKA,
        )
        assert item.discounted_price(0) == 100

    def test_allied_rep_gives_max_discount(self) -> None:
        item = MarketItem(
            item_id="x",
            name="X",
            base_price=200,
            tier_level=1,
            available=True,
            faction=Faction.HOSAKA,
        )
        # 100 (ALLIED) → multiplier 0.5 → 200*0.5 = 100
        assert item.discounted_price(100) == 100

    def test_friendly_rep_moderate_discount(self) -> None:
        item = MarketItem(
            item_id="x",
            name="X",
            base_price=1000,
            tier_level=2,
            available=True,
            faction=Faction.MAAS,
        )
        # 50 (FRIENDLY) → multiplier 0.65 → 1000*0.65 = 650
        assert item.discounted_price(50) == 650

    def test_trusted_rep_small_discount(self) -> None:
        item = MarketItem(
            item_id="x",
            name="X",
            base_price=1000,
            tier_level=2,
            available=True,
            faction=Faction.MAAS,
        )
        # 20 (TRUSTED) → multiplier 0.85 → 1000*0.85 = 850
        assert item.discounted_price(20) == 850

    def test_hostile_rep_moderate_markup(self) -> None:
        item = MarketItem(
            item_id="x",
            name="X",
            base_price=1000,
            tier_level=1,
            available=True,
            faction=Faction.HOSAKA,
        )
        # -20 (HOSTILE) → multiplier 1.15 → 1000*1.15 = 1150
        assert item.discounted_price(-20) == 1150

    def test_enemy_rep_larger_markup(self) -> None:
        item = MarketItem(
            item_id="x",
            name="X",
            base_price=1000,
            tier_level=1,
            available=True,
            faction=Faction.HOSAKA,
        )
        # -50 (ENEMY) → multiplier 1.35 → 1000*1.35 = 1350
        assert item.discounted_price(-50) == 1350

    def test_outcast_rep_max_markup(self) -> None:
        item = MarketItem(
            item_id="x",
            name="X",
            base_price=1000,
            tier_level=1,
            available=True,
            faction=Faction.HOSAKA,
        )
        # -100 (OUTCAST) → multiplier 1.5 → 1000*1.5 = 1500
        assert item.discounted_price(-100) == 1500

    def test_crafting_only_item_returns_none(self) -> None:
        item = MarketItem(
            item_id="kraken",
            name="Kraken",
            base_price=5000,  # has a price
            tier_level=5,
            available=False,  # but not for sale
            faction=Faction.TA,
        )
        assert item.discounted_price(100) is None

    def test_no_price_item_returns_none(self) -> None:
        item = MarketItem(
            item_id="kraken",
            name="Kraken",
            base_price=None,
            tier_level=5,
            available=True,  # accidentally marked available
            faction=Faction.TA,
        )
        assert item.discounted_price(100) is None

    def test_minimum_price_is_one_credit(self) -> None:
        # Even with extreme ALLIED and tiny base, price >= 1.
        item = MarketItem(
            item_id="x",
            name="X",
            base_price=1,
            tier_level=1,
            available=True,
            faction=Faction.HOSAKA,
        )
        # 100 (ALLIED) → multiplier 0.5 → 0.5 → max(1, 0.5) = 1
        assert item.discounted_price(100) == 1


# ============================================================================
# InfoMarket.load_default
# ============================================================================


class TestInfoMarketLoad:
    def test_loads_real_data(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        items = market.all_items()
        # The default market has 5 entries (T1..T5)
        assert len(items) == 5

    def test_real_items_have_factions(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        # Each market item must be tagged with a faction (drives discount)
        for item in market.all_items():
            if item.available:
                assert item.faction is not None, f"available item {item.item_id} missing faction"

    def test_t5_is_crafting_only(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        t5 = market.get("t5_program")
        assert t5 is not None
        assert not t5.available  # Kraken is crafting-only

    def test_t1_t4_are_available(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        for item_id in ("t1_program", "t2_program", "t3_program", "t4_program"):
            item = market.get(item_id)
            assert item is not None
            assert item.available

    def test_missing_file_returns_empty_market(self, tmp_path: Path) -> None:
        market = InfoMarket.load_default(data_path=tmp_path / "missing.json")
        assert market.all_items() == []
        assert market.available_items() == []

    def test_corrupt_json_falls_back_gracefully(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{ not valid json", encoding="utf-8")
        market = InfoMarket.load_default(data_path=bad)
        assert market.all_items() == []  # graceful empty

    def test_empty_faction_field_handled(self, tmp_path: Path) -> None:
        """An item with no faction is still loadable but has no discount."""
        f = tmp_path / "market.json"
        f.write_text(
            json.dumps(
                {
                    "neutral": {
                        "item_id": "neutral",
                        "name": "Neutral",
                        "price": 100,
                        "tier_level": 1,
                        "available": True,
                    }
                }
            ),
            encoding="utf-8",
        )
        market = InfoMarket.load_default(data_path=f)
        item = market.get("neutral")
        assert item is not None
        assert item.faction is None
        # price_for with no faction returns base_price unchanged
        state = AppState()
        assert market.price_for("neutral", state) == 100


# ============================================================================
# InfoMarket.price_for + faction discount integration
# ============================================================================


class TestPriceForFactionDiscount:
    def test_allied_hosaka_discounts_t1(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        # Hosaka 80 (ALLIED) → 0.5 mult
        state.reputation.get(Faction.HOSAKA).score = 80
        # T1 base 100, ALLIED → 50
        assert market.price_for("t1_program", state) == 50

    def test_neutral_hosaka_base_price(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        # No rep adjustment → NEUTRAL → 1.0 mult
        assert market.price_for("t1_program", state) == 100

    def test_hostile_maas_markup_t2(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        # Maas -50 (ENEMY) → 1.35 mult
        state.reputation.get(Faction.MAAS).score = -50
        # T2 base 300, ENEMY → 405
        assert market.price_for("t2_program", state) == 405

    def test_faction_specific_discount_t3(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        # Sense/Net 60 (FRIENDLY) → 0.65 mult
        state.reputation.get(Faction.SENSE_NET).score = 60
        # T3 base 800, FRIENDLY → 520
        assert market.price_for("t3_program", state) == 520

    def test_t5_returns_none(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        # T5 is crafting-only (available=False)
        assert market.price_for("t5_program", state) is None

    def test_unknown_item_returns_none(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        assert market.price_for("phantom_item", state) is None

    def test_legacy_state_without_reputation(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        # Strip the reputation field to simulate legacy state.
        state = AppState()
        object.__setattr__(state, "reputation", None)
        # No reputation → base price (no discount applied).
        assert market.price_for("t1_program", state) == 100


# ============================================================================
# InfoMarket.can_purchase + purchase
# ============================================================================


class TestPurchaseFlow:
    def test_can_purchase_with_enough_credits(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 500
        # T1 base 100, neutral → 100 (can afford)
        assert market.can_purchase("t1_program", state) is True

    def test_cannot_purchase_when_broke(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 50  # less than 100
        assert market.can_purchase("t1_program", state) is False

    def test_purchase_deducts_credits(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 500
        # T1 base 100, neutral
        result = market.purchase("t1_program", state)
        assert result == 400  # 500 - 100
        assert state.credits == 400

    def test_purchase_with_discount_deducts_less(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 500
        # Hosaka 80 (ALLIED) → 0.5 mult → 50
        state.reputation.get(Faction.HOSAKA).score = 80
        result = market.purchase("t1_program", state)
        assert result == 450  # 500 - 50

    def test_purchase_with_markup_deducts_more(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 500
        # Maas -50 (ENEMY) → 1.35 mult → T2 (300) * 1.35 = 405
        state.reputation.get(Faction.MAAS).score = -50
        result = market.purchase("t2_program", state)
        assert result == 95  # 500 - 405

    def test_purchase_adds_to_inventory(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 500
        market.purchase("t1_program", state)
        assert state.inventory.get("t1_program") == 1
        # Buying again increments count
        market.purchase("t1_program", state)
        assert state.inventory.get("t1_program") == 2

    def test_purchase_with_insufficient_credits_returns_none(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 50
        result = market.purchase("t1_program", state)
        assert result is None
        # Credits unchanged
        assert state.credits == 50
        # Inventory unchanged
        assert state.inventory == {}

    def test_purchase_crafting_only_returns_none(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 100000
        result = market.purchase("t5_program", state)
        assert result is None
        assert state.credits == 100000

    def test_purchase_unknown_item_returns_none(self, data_dir: Path) -> None:
        market = InfoMarket.load_default(data_path=data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 1000
        result = market.purchase("phantom_item", state)
        assert result is None
        assert state.credits == 1000


# ============================================================================
# Hub integration — surface the discount in a status message
# ============================================================================


class TestHubIntegration:
    """The Hub calls market.price_for() to surface the current discount."""

    def test_hub_status_message_includes_discount(
        self, data_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When the player has a high rep with a market faction, the
        Hub status line should surface the discounted price."""
        from wet_run.engine import config as _engine_config

        # DATA_DIR is the data/ directory itself; load_default joins
        # "crafting/market.json" onto it.
        monkeypatch.setattr(_engine_config, "DATA_DIR", data_dir, raising=False)
        market = InfoMarket.load_default()
        state = AppState()
        state.credits = 1000
        # Push Hosaka to ALLIED.
        state.reputation.get(Faction.HOSAKA).score = 100
        # The Hub calls market.price_for for the top item.
        t1_price = market.price_for("t1_program", state)
        # 100 * 0.5 = 50
        assert t1_price == 50
        # Can afford with 1000 credits.
        assert market.can_purchase("t1_program", state) is True


class TestMarketSummary:
    """The Hub's _render_market_summary formats the discount line."""

    def test_neutral_default(self, data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from wet_run.engine import config as _engine_config
        from wet_run.engine.hub import _render_market_summary

        monkeypatch.setattr(_engine_config, "DATA_DIR", data_dir, raising=False)
        state = AppState()
        # Neutral rep → base price, no discount/markup suffix.
        line = _render_market_summary(state)
        assert "T1" in line
        assert "100cr" in line
        assert "neutral" in line

    def test_allied_shows_discount(self, data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from wet_run.engine import config as _engine_config
        from wet_run.engine.hub import _render_market_summary

        monkeypatch.setattr(_engine_config, "DATA_DIR", data_dir, raising=False)
        state = AppState()
        state.reputation.get(Faction.HOSAKA).score = 100  # ALLIED
        line = _render_market_summary(state)
        assert "T1" in line
        assert "50cr" in line
        assert "hosaka" in line
        assert "-50%" in line

    def test_hostile_shows_markup(self, data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from wet_run.engine import config as _engine_config
        from wet_run.engine.hub import _render_market_summary

        monkeypatch.setattr(_engine_config, "DATA_DIR", data_dir, raising=False)
        state = AppState()
        state.reputation.get(Faction.HOSAKA).score = -20  # HOSTILE
        line = _render_market_summary(state)
        assert "T1" in line
        # 100 * 1.15 = 115
        assert "115cr" in line
        assert "+15%" in line

    def test_legacy_state_returns_neutral(
        self, data_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from wet_run.engine import config as _engine_config
        from wet_run.engine.hub import _render_market_summary

        monkeypatch.setattr(_engine_config, "DATA_DIR", data_dir, raising=False)
        state = AppState()
        object.__setattr__(state, "reputation", None)
        line = _render_market_summary(state)
        assert "neutral" in line
        assert "100cr" in line
