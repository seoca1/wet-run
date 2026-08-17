"""Tests for the data_fragment game play system (v0.5 expansion).

Covers:
- FRAGMENT_CATALOG structure
- collect_fragment / is_collected / list_collected / list_uncollected
- collection_progress
- AppState integration
- Rarity tier coverage
"""

from __future__ import annotations

from wet_run.data_fragment import (
    FRAGMENT_CATALOG,
    FragmentRarity,
    collect_fragment,
    collection_progress,
    is_collected,
    list_collected,
    list_uncollected,
)
from wet_run.engine.state import AppState
from wet_run.run.state import Stage


class TestFragmentCatalog:
    def test_catalog_nonempty(self) -> None:
        assert len(FRAGMENT_CATALOG) >= 3, "Catalog should have at least 3 fragments"

    def test_all_have_required_fields(self) -> None:
        for fid, frag in FRAGMENT_CATALOG.items():
            assert frag.id == fid, f"Fragment id mismatch: {fid} != {frag.id}"
            assert frag.title_en, f"{fid} missing title_en"
            assert frag.title_ko, f"{fid} missing title_ko"
            assert frag.description_en, f"{fid} missing description_en"
            assert frag.description_ko, f"{fid} missing description_ko"
            assert frag.wiki_ref, f"{fid} missing wiki_ref"
            assert isinstance(frag.rarity, FragmentRarity)

    def test_rarity_distribution(self) -> None:
        rarities = {f.rarity for f in FRAGMENT_CATALOG.values()}
        assert FragmentRarity.COMMON in rarities, "Should have at least one common fragment"
        assert FragmentRarity.LEGENDARY in rarities, "Should have at least one legendary fragment"

    def test_known_ids(self) -> None:
        expected = {
            "fragment.tessier_archive",
            "fragment.morrison_echo",
            "fragment.zion_cluster_log",
            "fragment.sense_net_corridor",
            "fragment.freeside_manifest",
        }
        assert expected.issubset(FRAGMENT_CATALOG.keys())


class TestCollectFragment:
    def test_first_collect(self) -> None:
        state = AppState()
        added = collect_fragment(state, "fragment.sense_net_corridor")
        assert added is True
        assert is_collected(state, "fragment.sense_net_corridor") is True

    def test_duplicate_collect(self) -> None:
        state = AppState()
        collect_fragment(state, "fragment.sense_net_corridor")
        added = collect_fragment(state, "fragment.sense_net_corridor")
        assert added is False, "Second collection should return False"

    def test_invalid_collect(self) -> None:
        state = AppState()
        added = collect_fragment(state, "fragment.does_not_exist")
        assert added is False
        assert "fragment.does_not_exist" not in state.data_fragments


class TestListFragments:
    def test_list_collected_empty(self) -> None:
        state = AppState()
        assert list_collected(state) == []
        assert list_uncollected(state) == list(FRAGMENT_CATALOG.values())

    def test_list_after_collect(self) -> None:
        state = AppState()
        collect_fragment(state, "fragment.tessier_archive")
        collect_fragment(state, "fragment.zion_cluster_log")
        collected = list_collected(state)
        assert len(collected) == 2
        assert all(f.id in state.data_fragments for f in collected)

    def test_list_uncollected_after_collect(self) -> None:
        state = AppState()
        collect_fragment(state, "fragment.tessier_archive")
        uncollected = list_uncollected(state)
        assert all(f.id not in state.data_fragments for f in uncollected)


class TestCollectionProgress:
    def test_empty_progress(self) -> None:
        state = AppState()
        collected, total = collection_progress(state)
        assert collected == 0
        assert total == len(FRAGMENT_CATALOG)
        assert total > 0

    def test_partial_progress(self) -> None:
        state = AppState()
        collect_fragment(state, "fragment.tessier_archive")
        collected, total = collection_progress(state)
        assert collected == 1
        assert total == len(FRAGMENT_CATALOG)

    def test_full_progress(self) -> None:
        state = AppState()
        for fid in FRAGMENT_CATALOG:
            collect_fragment(state, fid)
        collected, total = collection_progress(state)
        assert collected == total


class TestStageIntegration:
    def test_new_stages_in_enum(self) -> None:
        assert Stage.BLACKMARKET.value == "black_market"
        assert Stage.GHOST_ENCOUNTER.value == "ghost_encounter"

    def test_new_stages_total(self) -> None:
        # v0.4: 14 stages. v0.5: +2 (BLACKMARKET, GHOST_ENCOUNTER) = 16
        all_stages = list(Stage)
        assert len(all_stages) == 16, f"Expected 16 stages, got {len(all_stages)}"
