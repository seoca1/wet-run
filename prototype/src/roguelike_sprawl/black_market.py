"""Black Market stage (v0.5 stage expansion).

A hub-side vendor where the player can trade credits and materials for
programs, deck upgrades, and intel. Reachable from the Hub between runs.

Stage state: Stage.BLACKMARKET
Game flow:
    - Player enters from Hub (PENDING)
    - Browses 3 categories: programs / deck upgrades / intel
    - Each item has a credit cost + material cost
    - ESC returns to Hub (PENDING)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BlackMarketCategory(StrEnum):
    """Market sections available in the Hub-side vendor."""

    PROGRAMS = "programs"  # Combat programs (Strike, Hammer, Virus, Wisp)
    DECK_UPGRADES = "deck_upgrades"  # T1 → T2 → T3 deck tier upgrades
    INTEL = "intel"  # Mission hints, zone maps, NPC profiles


@dataclass(frozen=True, slots=True)
class MarketItem:
    """A single black market item.

    Attributes:
        id: Stable id.
        name_en: English name.
        name_ko: Korean name.
        category: Which section of the market.
        credit_cost: Credits required to purchase.
        material_cost: Materials required (raw material id, count).
        description_en: English description.
        description_ko: Korean description.
    """

    id: str
    name_en: str
    name_ko: str
    category: BlackMarketCategory
    credit_cost: int
    material_cost: tuple[tuple[str, int], ...]
    description_en: str
    description_ko: str


MARKET_INVENTORY: dict[str, MarketItem] = {
    "market.program.strike": MarketItem(
        id="market.program.strike",
        name_en="Strike (T1 combat program)",
        name_ko="스트라이크 (T1 전투 프로그램)",
        category=BlackMarketCategory.PROGRAMS,
        credit_cost=300,
        material_cost=(("scrap_ice", 1),),
        description_en="A basic combat program. The kind of program the runner is supposed to start with.",
        description_ko="기본 전투 프로그램. 러너가 처음 시작할 때 가지고 있어야 하는 종류의 프로그램.",
    ),
    "market.program.hammer": MarketItem(
        id="market.program.hammer",
        name_en="Hammer (T2 combat program)",
        name_ko="해머 (T2 전투 프로그램)",
        category=BlackMarketCategory.PROGRAMS,
        credit_cost=1200,
        material_cost=(("scrap_ice", 3), ("raw_neural", 1)),
        description_en="A heavier combat program. Drops Watchdogs in two hits if you time it right.",
        description_ko="더 무거운 전투 프로그램. 타이밍을 맞추면 와치독을 두 번에 처리한다.",
    ),
    "market.deck.t2": MarketItem(
        id="market.deck.t2",
        name_en="Hosaka Security (T2 deck upgrade)",
        name_ko="호사카 시큐리티 (T2 데크 업그레이드)",
        category=BlackMarketCategory.DECK_UPGRADES,
        credit_cost=5000,
        material_cost=(("refined_neural", 2), ("memory_shard", 1)),
        description_en="Standard corporate deck upgrade. +1 PPL, +1 deck slot. Boring but reliable.",
        description_ko="표준 기업 데크 업그레이드. +1 PPL, +1 데크 슬롯. 지루하지만 안정적이다.",
    ),
    "market.intel.freeside_route": MarketItem(
        id="market.intel.freeside_route",
        name_en="Freeside cargo route (intel)",
        name_ko="프리사이드 화물 루트 (인텔)",
        category=BlackMarketCategory.INTEL,
        credit_cost=800,
        material_cost=(),
        description_en="A tip from a back-alley contact. Where the next Freeside delivery will be. Useful only if you can survive the orbital ride.",
        description_ko="뒷골목 연락처에서 온 팁. 다음 프리사이드 배송이 어디일지. 궤도 라이드를 살아남을 수 있을 때만 유용하다.",
    ),
    "market.intel.zion_signal": MarketItem(
        id="market.intel.zion_signal",
        name_en="Zion cluster signal (intel)",
        name_ko="자이온 클러스터 신호 (인텔)",
        category=BlackMarketCategory.INTEL,
        credit_cost=1500,
        material_cost=(("scrap_ice", 2),),
        description_en="A frequency the Romantics use to talk to each other through the matrix. They will not be happy you have it.",
        description_ko="로맨틱스들이 매트릭스를 통해 서로 대화하는 데 사용하는 주파수. 당신이 그것을 가지고 있다는 것을 좋아하지 않을 것이다.",
    ),
}


def list_by_category(category: BlackMarketCategory) -> list[MarketItem]:
    """Return all market items in a category, in catalog order."""
    return [item for item in MARKET_INVENTORY.values() if item.category == category]


__all__ = [
    "BlackMarketCategory",
    "MarketItem",
    "MARKET_INVENTORY",
    "list_by_category",
]
