"""Info Market: faction-aware pricing for Cyberspace programs.

The Info Market is the fixer's storefront where the player can spend
credits on programs / ICE-breakers / data fragments instead of
crafting them. Each item is associated with a faction; the player's
reputation with that faction modifies the price:

  - ALLIED / FRIENDLY / TRUSTED  → discount (up to 50% off)
  - NEUTRAL                       → base price
  - HOSTILE / ENEMY / OUTCAST     → markup (up to 50% extra)

Discount formula (per reputation_tier):

  final_price = base_price * (1 - max(0, rep_score) / DISCOUNT_DENOM)
  final_price = base_price * (1 + abs(min(0, rep_score)) / MARKUP_DENOM)

Both denominator = 200 → a maxed ALLIED (100) gives 50% off, a maxed
OUTCAST (-100) gives 50% markup. T5 items with ``available=False`` are
crafting-only and never appear in the market.

Data source: ``data/crafting/market.json`` (loaded at construction
time, cached via module-level helpers).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from ..matrix.node import Faction
from ..run.reputation import reputation_tier

if TYPE_CHECKING:
    from ..engine.state import AppState


# Discount / markup denominator. A score of ±100 yields ±50% adjustment.
DISCOUNT_DENOM: int = 200
MARKUP_DENOM: int = 200


# Tier → price modifier (1.0 = base price, 0.5 = 50% off, 1.5 = 50% markup).
# Maps the player's reputation tier to a multiplier for the price.
_TIER_TO_MULTIPLIER: dict[str, float] = {
    "ALLIED": 0.5,
    "FRIENDLY": 0.65,
    "TRUSTED": 0.85,
    "NEUTRAL": 1.0,
    "HOSTILE": 1.15,
    "ENEMY": 1.35,
    "OUTCAST": 1.5,
}


@dataclass(frozen=True, slots=True)
class MarketItem:
    """A single item sold by the Info Market.

    Attributes:
        item_id: Unique identifier.
        name: Human-readable name.
        base_price: Base credits cost (None for crafting-only items).
        tier_level: Item tier (1..5).
        available: True if the market can sell this item. False for
            crafting-only items (T5).
        faction: Which faction sells this item (drives discount logic).
        examples: Suggested program ids for the player to choose from
            when purchasing.
        description: Short flavor text.
    """

    item_id: str
    name: str
    base_price: int | None
    tier_level: int
    available: bool
    faction: Faction | None
    examples: tuple[str, ...] = ()
    description: str = ""

    def discounted_price(self, faction_score: int) -> int | None:
        """Return the price for this item after faction discount.

        Args:
            faction_score: Player's reputation score with this item's
                faction (typically -100..+100).

        Returns:
            Adjusted credit cost, or None if the item is not for sale.
        """
        if not self.available or self.base_price is None:
            return None
        tier = reputation_tier(faction_score)
        mult = _TIER_TO_MULTIPLIER.get(tier, 1.0)
        adjusted = round(self.base_price * mult)
        return max(1, adjusted)  # never free / negative


@dataclass
class InfoMarket:
    """The fixer's storefront. Loads from data/crafting/market.json.

    The market is a singleton-friendly object — all instances share
    the same data directory and item registry.
    """

    items: dict[str, MarketItem] = field(default_factory=dict)
    # JSON path is read from config at __post_init__; left as
    # None for explicit construction (tests).
    data_path: Path | None = None

    #: How many items appear in market.json at game start.
    DEFAULT_PATH: ClassVar[Path] = Path("data/crafting/market.json")

    # Module-level cache: load_default() is called frequently by the
    # Hub render path (every frame), so we cache the constructed market
    # keyed by data_path. Tests can call _reset_cache() to clear.
    _CACHE: ClassVar[dict[str, InfoMarket]] = {}

    @classmethod
    def _reset_cache(cls) -> None:
        """Clear the module-level market cache (for tests)."""
        cls._CACHE.clear()

    @classmethod
    def load_default(cls, data_path: Path | None = None) -> InfoMarket:
        """Construct an InfoMarket from the default JSON file.

        Args:
            data_path: Override the JSON path (for tests / mods). If
                None, uses the standard data/crafting/market.json
                resolved via the engine config.
        """
        if data_path is None:
            try:
                from ..engine import config as _engine_config

                data_path = _engine_config.DATA_DIR / "crafting" / "market.json"
            except (ImportError, AttributeError):
                data_path = cls.DEFAULT_PATH
        market = cls(data_path=data_path)
        if data_path.exists():
            try:
                with data_path.open(encoding="utf-8") as f:
                    raw = json.load(f)
            except (OSError, json.JSONDecodeError):
                raw = {}
            for key, payload in raw.items():
                if not isinstance(payload, dict):
                    continue
                faction_str = payload.get("faction")
                faction: Faction | None = None
                if faction_str:
                    try:
                        faction = Faction(faction_str)
                    except ValueError:
                        faction = None
                market.items[key] = MarketItem(
                    item_id=str(payload.get("item_id", key)),
                    name=str(payload.get("name", key)),
                    base_price=(
                        int(payload["price"]) if payload.get("price") is not None else None
                    ),
                    tier_level=int(payload.get("tier_level", 1)),
                    available=bool(payload.get("available", True)),
                    faction=faction,
                    examples=tuple(payload.get("examples", []) or ()),
                    description=str(payload.get("description", "")),
                )
        # Cache the loaded market.
        cls._CACHE[str(data_path)] = market
        return market

    def get(self, item_id: str) -> MarketItem | None:
        """Return the MarketItem for ``item_id``, or None if absent."""
        return self.items.get(item_id)

    def all_items(self) -> list[MarketItem]:
        """Return every loaded market item, including crafting-only."""
        return list(self.items.values())

    def available_items(self) -> list[MarketItem]:
        """Return only items that can be purchased in the market."""
        return [item for item in self.items.values() if item.available]

    def price_for(self, item_id: str, state: AppState) -> int | None:
        """Convenience: lookup + faction discount in one call.

        Args:
            item_id: Market item id.
            state: Player state (for reputation lookup).

        Returns:
            Discounted credit cost, or None if item not found / not
            for sale / reputation field missing.
        """
        item = self.get(item_id)
        if item is None or item.faction is None:
            return item.base_price if item is not None and item.available else None
        rep = getattr(state, "reputation", None)
        if rep is None:
            # Legacy / stripped state → no discount.
            return item.base_price
        score = rep.get(item.faction).score
        return item.discounted_price(score)

    def can_purchase(self, item_id: str, state: AppState) -> bool:
        """Return True if the player can afford ``item_id``."""
        price = self.price_for(item_id, state)
        if price is None:
            return False
        return state.credits >= price

    def purchase(self, item_id: str, state: AppState) -> int | None:
        """Atomically purchase an item. Returns the new credit balance.

        Args:
            item_id: Item to buy.
            state: App state (credits + reputation).

        Returns:
            New credit balance after purchase, or None if the purchase
            failed (item not found / not for sale / insufficient
            credits).
        """
        price = self.price_for(item_id, state)
        if price is None:
            return None
        if state.credits < price:
            return None
        state.credits -= price
        # Add to inventory: increase count for the item's primary
        # example (or fall back to item_id itself).
        inv_key = self._inventory_key(item_id)
        if not hasattr(state, "inventory") or state.inventory is None:
            state.inventory = {}
        state.inventory[inv_key] = state.inventory.get(inv_key, 0) + 1
        # ADR-0151 follow-up (Cycle 7): intel items auto-apply effect
        # on purchase. The apply_intel_item function reads/writes
        # AppState fields (alarm_level, purchased_intel_items, etc.)
        # and is one-shot per item_id.
        from ..combat.intel_items import IntelItemId, apply_intel_item

        if item_id in {
            IntelItemId.ALARM_REDUCER,
            IntelItemId.MISSION_HINT,
            IntelItemId.FACTION_RUMOR,
        }:
            apply_intel_item(state, item_id, state)
        return state.credits

    @staticmethod
    def _inventory_key(item_id: str) -> str:
        """Map market item_id → inventory key.

        Strips the tier prefix (e.g. "t3_program" → "t3_program") and
        uses the first example if available, otherwise the item_id.
        """
        # The market items already use stable ids ("t1_program", etc.)
        # so we just return the item_id. Kept as a separate method for
        # future flexibility (e.g. mapping to specific program names).
        return item_id


__all__ = [
    "DISCOUNT_DENOM",
    "InfoMarket",
    "MARKUP_DENOM",
    "MarketItem",
    "_TIER_TO_MULTIPLIER",
]
