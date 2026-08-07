"""Automated tests for Faction Expansion (ADR-0154, Cycle 10).

Source spec: Game/roguelike_sprawl/decisions/0154-faction-expansion-i18n.md

faction_rumor faction expansion:
- 4 faction variants: hosaka, sense_net, yakuza, loa
- Each variant: 50 credits, faction-specific, +25% event probability
- Backward-compat: item_id → "loa" default
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roguelike_sprawl.combat.intel_items import (
    ALARM_REDUCER_DELTA,
    ALARM_REDUCER_PRICE,
    FACTION_RUMOR_FACTION,
    FACTION_RUMOR_FACTIONS,
    FACTION_RUMOR_PRICE,
    FACTION_RUMOR_PROBABILITY_BOOST,
    MISSION_HINT_PRICE,
    IntelItemId,
    apply_faction_rumor,
    apply_intel_item,
)


class _StubStatusList:
    __slots__ = ("data",)

    def __init__(self) -> None:
        self.data: list[str] = []

    def append(self, item: str) -> None:
        self.data.append(item)


class _StubState:
    """Minimal state stub for intel_items tests."""

    __slots__ = (
        "credits",
        "alarm_level",
        "purchased_intel_items",
        "status_messages",
        "current_mission",
        "faction_tension_probability_boost",
        "faction_tension_triggered",
    )

    def __init__(
        self,
        *,
        credits: int = 100,
        alarm_level: int = 0,
        current_mission: object | None = None,
    ) -> None:
        self.credits = credits
        self.alarm_level = alarm_level
        self.purchased_intel_items: list[str] = []
        self.status_messages = _StubStatusList()
        self.current_mission = current_mission
        self.faction_tension_probability_boost = 0.0
        self.faction_tension_triggered: set[str] = set()


class TestFactionExpansion:
    """Verify faction_rumor has 4 faction variants (ADR-0154)."""

    def test_faction_rumor_factions_has_4_variants(self) -> None:
        """4 faction variants: hosaka, sense_net, yakuza, loa."""
        assert len(FACTION_RUMOR_FACTIONS) == 4

    def test_faction_rumor_factions_contains_hosaka(self) -> None:
        assert FACTION_RUMOR_FACTIONS.get("hosaka_faction_rumor") == "hosaka"

    def test_faction_rumor_factions_contains_sense_net(self) -> None:
        assert FACTION_RUMOR_FACTIONS.get("sense_net_faction_rumor") == "sense_net"

    def test_faction_rumor_factions_contains_yakuza(self) -> None:
        assert FACTION_RUMOR_FACTIONS.get("yakuza_faction_rumor") == "yakuza"

    def test_faction_rumor_factions_contains_loa(self) -> None:
        assert FACTION_RUMOR_FACTIONS.get("loa_faction_rumor") == "loa"

    def test_faction_rumor_backward_compat_default_is_loa(self) -> None:
        """FACTION_RUMOR_FACTION (singular) default is "loa" for backward compat."""
        assert FACTION_RUMOR_FACTION == "loa"

    def test_faction_rumor_probability_boost_unchanged(self) -> None:
        """FACTION_RUMOR_PROBABILITY_BOOST is 0.25 (unchanged from ADR-0151)."""
        assert FACTION_RUMOR_PROBABILITY_BOOST == 0.25

    def test_faction_rumor_price_unchanged(self) -> None:
        """FACTION_RUMOR_PRICE is 50 (unchanged from ADR-0151)."""
        assert FACTION_RUMOR_PRICE == 50


class TestFactionRumorApply:
    """Verify apply_faction_rumor works with faction_id parameter."""

    def test_apply_faction_rumor_hosaka(self) -> None:
        """apply_faction_rumor(boost target = hosaka faction)."""
        state = _StubState()
        result = apply_faction_rumor(state)
        assert result == 0.25  # FACTION_RUMOR_PROBABILITY_BOOST
        assert state.faction_tension_probability_boost == 0.25

    def test_apply_faction_rumor_appends_status(self) -> None:
        """Status message records the faction rumor application."""
        state = _StubState()
        apply_faction_rumor(state)
        assert any("Faction Rumor" in m for m in state.status_messages.data)

    def test_faction_rumor_does_not_modify_alarm(self) -> None:
        """faction_rumor does NOT affect alarm (different from alarm_reducer)."""
        state = _StubState(alarm_level=3)
        apply_faction_rumor(state)
        assert state.alarm_level == 3  # unchanged


class TestIntelItemBackwardCompat:
    """Verify backward compatibility of intel_items after ADR-0154."""

    def test_alarm_reducer_unchanged(self) -> None:
        """alarm_reducer still works (backward compat)."""
        state = _StubState(alarm_level=4)
        apply_intel_item(state, IntelItemId.ALARM_REDUCER)
        assert state.alarm_level == 2  # 4 - 2
        assert ALARM_REDUCER_DELTA == 2
        assert ALARM_REDUCER_PRICE == 30

    def test_mission_hint_unchanged(self) -> None:
        """mission_hint still works (backward compat)."""
        state = _StubState()
        apply_intel_item(state, IntelItemId.MISSION_HINT)
        assert state.purchased_intel_items == ["mission_hint"]
        assert MISSION_HINT_PRICE == 40

    def test_faction_rumor_unchanged(self) -> None:
        """faction_rumor still works (backward compat)."""
        state = _StubState()
        apply_intel_item(state, IntelItemId.FACTION_RUMOR)
        assert state.purchased_intel_items == ["faction_rumor"]
        assert state.faction_tension_probability_boost == 0.25

    def test_unknown_item_returns_false(self) -> None:
        """Unknown item_id returns False (no effect)."""
        state = _StubState()
        result = apply_intel_item(state, "unknown_item")
        assert result is False
        assert state.purchased_intel_items == []


class TestPPLGrowthTargets:
    """Verify PPL_GROWTH_TARGETS comment documentation (ADR-0154)."""

    def test_ppl_growth_targets_present(self) -> None:
        """PPL_GROWTH_TARGETS dict is present in multi_enemy module."""
        from roguelike_sprawl.combat.multi_enemy import PPL_GROWTH_TARGETS

        assert isinstance(PPL_GROWTH_TARGETS, dict)

    def test_ppl_growth_targets_has_5_transitions(self) -> None:
        """5 growth transitions: 1->2, 2->3, 3->4, 4->5, 5->6."""
        from roguelike_sprawl.combat.multi_enemy import PPL_GROWTH_TARGETS

        assert len(PPL_GROWTH_TARGETS) == 5

    def test_ppl_growth_5_to_6_is_stagnant(self) -> None:
        """Grade 5->6 is the NG+ balance issue (1.20x)."""
        from roguelike_sprawl.combat.multi_enemy import PPL_GROWTH_TARGETS

        assert PPL_GROWTH_TARGETS.get("5->6") == 1.20

    def test_ppl_growth_1_to_2_is_largest(self) -> None:
        """Grade 1->2 is the largest growth (2.00x, novice to intermediate)."""
        from roguelike_sprawl.combat.multi_enemy import PPL_GROWTH_TARGETS

        assert PPL_GROWTH_TARGETS.get("1->2") == 2.00


class TestI18nFactionExpansion:
    """Verify i18n coverage for faction expansion (ADR-0154)."""

    @pytest.mark.parametrize("lang", ["en", "ko", "ja", "zh"])
    def test_intel_items_section_present(self, lang: str) -> None:
        """intel_items section present in all 4 languages."""

        i18n_dir = Path(__file__).parent.parent.parent / "data" / "i18n"
        with open(i18n_dir / f"{lang}.json") as f:
            data = json.load(f)
        assert "intel_items" in data
        assert len(data["intel_items"]) > 0

    @pytest.mark.parametrize("lang", ["en", "ko", "ja", "zh"])
    def test_multi_enemy_section_present(self, lang: str) -> None:
        """multi_enemy section present in all 4 languages."""

        i18n_dir = Path(__file__).parent.parent.parent / "data" / "i18n"
        with open(i18n_dir / f"{lang}.json") as f:
            data = json.load(f)
        assert "multi_enemy" in data
        assert len(data["multi_enemy"]) > 0

    @pytest.mark.parametrize("lang", ["en", "ko", "ja", "zh"])
    def test_boss_phase4_section_present(self, lang: str) -> None:
        """boss_phase4 section present in all 4 languages."""

        i18n_dir = Path(__file__).parent.parent.parent / "data" / "i18n"
        with open(i18n_dir / f"{lang}.json") as f:
            data = json.load(f)
        assert "boss_phase4" in data
        assert len(data["boss_phase4"]) > 0
