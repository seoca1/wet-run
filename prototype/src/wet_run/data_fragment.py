"""Data Fragment collection system (v0.5 game play expansion).

Each fragment is a small lore collectible that the player can find during
missions. Fragments tie into the Sprawl wiki and provide narrative context
for the world (Count Zero era Tessier-Ashpool, Freeside, the Loa, etc.).

Collected fragments are persisted in AppState.data_fragments (a set of
fragment_id strings). This module owns the catalog and the helper
functions for collection, inspection, and serialization.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FragmentRarity(StrEnum):
    """Rarity tier for a data fragment — affects gallery visual style.

    Ordered from most common to most legendary. Drives the fragment
    gallery's border color and unlock animation.
    """

    COMMON = "common"  # Frequent drops, surface-level lore.
    UNCOMMON = "uncommon"  # Mid-tier missions, named-npc drops.
    RARE = "rare"  # Boss-tier or end-of-chain drops.
    LEGENDARY = "legendary"  # Construct / story-critical fragments.


@dataclass(frozen=True, slots=True)
class DataFragment:
    """A single data fragment collectible.

    Attributes:
        id: Stable id (used as set key). E.g. "fragment.tessier_archive".
        title_en: Short English label.
        title_ko: Short Korean label.
        description_en: English prose describing what the fragment contains.
        description_ko: Korean prose.
        wiki_ref: Wiki page this fragment unlocks (e.g. "[[tessier-ashpool]]").
        rarity: Rarity tier (affects visual style in fragment gallery).
        source_mission: Mission id that can drop this fragment (or None for events).
    """

    id: str
    title_en: str
    title_ko: str
    description_en: str
    description_ko: str
    wiki_ref: str
    rarity: FragmentRarity = FragmentRarity.COMMON
    source_mission: str | None = None


FRAGMENT_CATALOG: dict[str, DataFragment] = {
    "fragment.tessier_archive": DataFragment(
        id="fragment.tessier_archive",
        title_en="Tessier Family Archive (fragment)",
        title_ko="테시에르 가족 기록 보관소 (조각)",
        description_en="A shard of the Tessier-Ashpool family archive. The encryption is decades old and the data is incomplete, but you can tell what it is.",
        description_ko="테시에르-애시풀 가족 기록 보관소의 파편. 암호화는 수십 년 된 것이며 데이터는 불완전하지만 그것이 무엇인지는 알 수 있다.",
        wiki_ref="[[tessier-ashpool]]",
        rarity=FragmentRarity.RARE,
        source_mission="straylight_approach",
    ),
    "fragment.morrison_echo": DataFragment(
        id="fragment.morrison_echo",
        title_en="Morrison's Echo",
        title_ko="모리슨의 메아리",
        description_en="A construct that has been waiting in the deep architecture for thirty-seven years. It still knows the name of a runner who died in Freeside.",
        description_ko="딥 아키텍처에서 37년 동안 기다려 온 콘스트럭트. 그것은 여전히 프리사이드에서 죽은 러너의 이름을 알고 있다.",
        wiki_ref="[[loa]]",
        rarity=FragmentRarity.LEGENDARY,
        source_mission="voodoo_loa_encounter",
    ),
    "fragment.zion_cluster_log": DataFragment(
        id="fragment.zion_cluster_log",
        title_en="Zion Cluster Log",
        title_ko="자이온 클러스터 로그",
        description_en="Telemetry from the orbital cluster. The Romantics are still out there, watching the matrix from their rock.",
        description_ko="궤도 클러스터의 원격 측정. 로맨틱스들은 여전히 자기들 바위에서 매트릭스를 지켜보고 있다.",
        wiki_ref="[[zion]]",
        rarity=FragmentRarity.UNCOMMON,
        source_mission="zion_express",
    ),
    "fragment.sense_net_corridor": DataFragment(
        id="fragment.sense_net_corridor",
        title_en="Sense/Net Corridor Map",
        title_ko="센스/넷 회랑 지도",
        description_en="A partial map of Sense/Net's internal Boston corridors. Someone paid for this in three years of work.",
        description_ko="센스/넷 내부 보스턴 회랑의 부분 지도. 누군가가 3년치 일로 이것의 값을 치렀다.",
        wiki_ref="[[sense-net]]",
        rarity=FragmentRarity.COMMON,
        source_mission="first_jack",
    ),
    "fragment.freeside_manifest": DataFragment(
        id="fragment.freeside_manifest",
        title_en="Freeside Cargo Manifest",
        title_ko="프리사이드 화물 명세서",
        description_en="A cargo manifest for a Freeside delivery, dated before the war. The cargo itself is gone, but the names of the recipients are still on file.",
        description_ko="전쟁 이전의 프리사이드 배송 화물 명세서. 화물 자체는 사라졌지만 수령인 이름은 여전히 파일에 남아 있다.",
        wiki_ref="[[freeside]]",
        rarity=FragmentRarity.UNCOMMON,
        source_mission="hosaka_extraction",
    ),
}


def collect_fragment(state: object, fragment_id: str) -> bool:
    """Add a fragment to the collected set. Returns True if newly added.

    Args:
        state: AppState (or any object with a `data_fragments: set[str]` attribute).
        fragment_id: The fragment id to collect.

    Returns:
        True if the fragment was newly added. False if it was already owned
        or if the fragment id is not in the catalog.
    """
    if fragment_id not in FRAGMENT_CATALOG:
        return False
    if fragment_id in state.data_fragments:  # type: ignore[attr-defined]
        return False
    state.data_fragments.add(fragment_id)  # type: ignore[attr-defined]
    return True


def is_collected(state: object, fragment_id: str) -> bool:
    """Return True if the fragment has been collected."""
    return fragment_id in state.data_fragments  # type: ignore[attr-defined]


def list_collected(state: object) -> list[DataFragment]:
    """Return a list of collected Fragment objects in catalog order."""
    return [FRAGMENT_CATALOG[fid] for fid in state.data_fragments if fid in FRAGMENT_CATALOG]  # type: ignore[attr-defined]


def list_uncollected(state: object) -> list[DataFragment]:
    """Return a list of uncollected Fragment objects in catalog order."""
    return [frag for fid, frag in FRAGMENT_CATALOG.items() if fid not in state.data_fragments]  # type: ignore[attr-defined]


def collection_progress(state: object) -> tuple[int, int]:
    """Return (collected_count, total_count) for the player's collection."""
    return len(state.data_fragments), len(FRAGMENT_CATALOG)  # type: ignore[attr-defined]


__all__ = [
    "DataFragment",
    "FragmentRarity",
    "FRAGMENT_CATALOG",
    "collect_fragment",
    "is_collected",
    "list_collected",
    "list_uncollected",
    "collection_progress",
]
