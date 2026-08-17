"""Tests for the NPC faction-aware greeting system.

The greeting system picks the best matching :class:`ReputationGreeting`
for an NPC based on the player's faction reputation. Each NPC has a
list of rules; the first matching one wins. The default rule
(faction=None, min_tier=None) is used if no other rule matches.
"""

from __future__ import annotations

import pytest

from wet_run.engine.npc_greeting import (
    NPC_GREETINGS,
    ReputationGreeting,
    get_greeting,
    get_greeting_text,
)
from wet_run.engine.state import AppState
from wet_run.matrix.node import Faction

# ============================================================================
# ReputationGreeting.matches()
# ============================================================================


class TestReputationGreetingMatches:
    def test_default_rule_never_matches(self) -> None:
        """The default rule (faction=None, min_tier=None) is a fallback
        marker — it must NOT match via the regular matches() path so
        get_greeting can detect it separately."""
        rule = ReputationGreeting(
            npc_id="finn",
            faction=None,
            min_tier=None,
            line_en="default",
        )
        assert rule.matches({}) is False

    def test_friendly_min_tier_matches_allied(self) -> None:
        rule = ReputationGreeting(
            npc_id="finn",
            faction=Faction.HOSAKA,
            min_tier="FRIENDLY",
            line_en="hosaka like",
        )
        # Hosaka score 60 → FRIENDLY (>=50)
        assert rule.matches({Faction.HOSAKA: 60}) is True

    def test_friendly_min_tier_does_not_match_trusted(self) -> None:
        rule = ReputationGreeting(
            npc_id="finn",
            faction=Faction.HOSAKA,
            min_tier="FRIENDLY",
            line_en="hosaka like",
        )
        # Hosaka score 25 → TRUSTED (<50)
        assert rule.matches({Faction.HOSAKA: 25}) is False

    def test_hostile_min_tier_matches_outcast(self) -> None:
        rule = ReputationGreeting(
            npc_id="finn",
            faction=Faction.MAAS,
            min_tier="HOSTILE",
            line_en="maas bad",
        )
        # Maas score -90 → OUTCAST (hostile or worse)
        assert rule.matches({Faction.MAAS: -90}) is True

    def test_hostile_does_not_match_neutral(self) -> None:
        rule = ReputationGreeting(
            npc_id="finn",
            faction=Faction.MAAS,
            min_tier="HOSTILE",
            line_en="maas bad",
        )
        # Maas score 0 → NEUTRAL (>=-20)
        assert rule.matches({Faction.MAAS: 0}) is False

    def test_missing_faction_uses_default_zero(self) -> None:
        rule = ReputationGreeting(
            npc_id="finn",
            faction=Faction.HOSAKA,
            min_tier="FRIENDLY",
            line_en="hosaka like",
        )
        # No Hosaka entry → 0 (NEUTRAL) → not matching FRIENDLY
        assert rule.matches({Faction.MAAS: 100}) is False


# ============================================================================
# get_greeting — selection logic
# ============================================================================


class TestGetGreeting:
    def test_unknown_npc_returns_none(self) -> None:
        state = AppState()
        assert get_greeting("phantom_npc", state) is None

    def test_default_greeting_when_neutral_rep(self) -> None:
        state = AppState()
        greeting = get_greeting("finn", state)
        assert greeting is not None
        # New state has no faction rep → all NEUTRAL → default wins
        assert greeting.faction is None
        assert "Sprawl" in greeting.line_en

    def test_finn_friendly_hosaka_greeting(self) -> None:
        state = AppState()
        state.reputation.get(Faction.HOSAKA).score = 60  # FRIENDLY
        greeting = get_greeting("finn", state)
        assert greeting is not None
        assert greeting.faction is Faction.HOSAKA
        assert "Hosaka" in greeting.line_en

    def test_finn_hostile_maas_greeting(self) -> None:
        state = AppState()
        state.reputation.get(Faction.MAAS).score = -90  # OUTCAST
        greeting = get_greeting("finn", state)
        assert greeting is not None
        assert greeting.faction is Faction.MAAS
        assert "Maas" in greeting.line_en

    def test_first_matching_rule_wins(self) -> None:
        """If both Hosaka and Sense/Net are FRIENDLY, the first listed wins."""
        state = AppState()
        state.reputation.get(Faction.HOSAKA).score = 60
        state.reputation.get(Faction.SENSE_NET).score = 60
        greeting = get_greeting("finn", state)
        assert greeting is not None
        # Hosaka is listed first in NPC_GREETINGS["finn"]
        assert greeting.faction is Faction.HOSAKA

    def test_dixie_ta_hostile(self) -> None:
        state = AppState()
        state.reputation.get(Faction.TA).score = -90
        greeting = get_greeting("dixie", state)
        assert greeting is not None
        assert greeting.faction is Faction.TA
        assert "Tessier" in greeting.line_en

    def test_maelcum_ta_friendly(self) -> None:
        state = AppState()
        # Maelcum's first faction rule is TA FRIENDLY (Tessier-Ashpool
        # trust). Push TA rep to FRIENDLY tier to trigger.
        state.reputation.get(Faction.TA).score = 60
        greeting = get_greeting("maelcum", state)
        assert greeting is not None
        assert greeting.faction is Faction.TA
        assert "Tessier" in greeting.line_en

    def test_bartender_maas_hostile_turns_away(self) -> None:
        state = AppState()
        state.reputation.get(Faction.MAAS).score = -90
        greeting = get_greeting("bartender", state)
        assert greeting is not None
        assert greeting.faction is Faction.MAAS
        assert "bar" in greeting.line_en.lower() or "leave" in greeting.line_en.lower()

    def test_ta_rep_allied_ta_approval(self) -> None:
        state = AppState()
        state.reputation.get(Faction.TA).score = 100
        greeting = get_greeting("ta_rep", state)
        assert greeting is not None
        assert greeting.faction is Faction.TA
        assert "Onikiri" in greeting.line_en

    def test_legacy_state_without_reputation(self) -> None:
        """Pre-Phase-6 states have no .reputation attribute — should
        still return a default greeting, never raise."""
        # Build a fresh state, then strip the reputation field
        state = AppState()
        object.__setattr__(state, "reputation", None)
        greeting = get_greeting("finn", state)
        # Should fall back to default (treat missing as zero rep)
        assert greeting is not None
        assert greeting.faction is None


# ============================================================================
# get_greeting_text — convenience helper
# ============================================================================


class TestGetGreetingText:
    def test_returns_english_by_default(self) -> None:
        state = AppState()
        text = get_greeting_text("finn", state)
        assert "Sprawl" in text  # English
        assert "스프롤" not in text  # not Korean

    def test_returns_korean_when_requested(self) -> None:
        state = AppState()
        text = get_greeting_text("finn", state, korean=True)
        assert "스프롤" in text

    def test_falls_back_to_english_when_korean_empty(self) -> None:
        """If a greeting has no Korean translation, fall back gracefully."""
        state = AppState()
        # Add a rule with empty Korean
        original = NPC_GREETINGS["finn"][-1]  # default
        NPC_GREETINGS["finn"][-1] = ReputationGreeting(
            npc_id=original.npc_id,
            faction=original.faction,
            min_tier=original.min_tier,
            line_en=original.line_en,
            line_ko="",  # no Korean
        )
        try:
            text = get_greeting_text("finn", state, korean=True)
            assert "Sprawl" in text  # falls back to English
        finally:
            # Restore
            NPC_GREETINGS["finn"][-1] = original

    def test_unknown_npc_returns_empty_string(self) -> None:
        state = AppState()
        assert get_greeting_text("phantom_npc", state) == ""


# ============================================================================
# Hub integration — get_greeting_text used in hub subtitle
# ============================================================================


class TestHubIntegration:
    """The Hub subtitle uses the Finn greeting to surface reputation."""

    def test_hub_subtitle_uses_default_greeting_when_neutral(self) -> None:
        from wet_run.engine.npc_greeting import get_greeting_text

        state = AppState()
        # Neutral → default greeting ("Welcome to the Sprawl, cowboy")
        greeting = get_greeting_text("finn", state)
        assert "cowboy" in greeting.lower() or "sprawl" in greeting.lower()

    def test_hub_subtitle_uses_faction_greeting(self) -> None:
        from wet_run.engine.npc_greeting import get_greeting_text

        state = AppState()
        # Push Maas to HOSTILE so Finn warns about them
        state.reputation.get(Faction.MAAS).score = -50
        greeting = get_greeting_text("finn", state)
        assert "Maas" in greeting


# ============================================================================
# NPC_GREETINGS table integrity
# ============================================================================


class TestGreetingTable:
    @pytest.mark.parametrize("npc_id", list(NPC_GREETINGS.keys()))
    def test_each_npc_has_default_greeting(self, npc_id: str) -> None:
        """Every NPC must have exactly one default (fallback) greeting."""
        defaults = [r for r in NPC_GREETINGS[npc_id] if r.faction is None and r.min_tier is None]
        assert len(defaults) == 1, f"{npc_id}: expected 1 default, got {len(defaults)}"

    @pytest.mark.parametrize("npc_id", list(NPC_GREETINGS.keys()))
    def test_all_factions_are_valid_enums(self, npc_id: str) -> None:
        """Non-default rules must reference valid Faction enum values."""
        for rule in NPC_GREETINGS[npc_id]:
            if rule.faction is not None:
                # Faction(rule.faction) — this would be the canonical check
                # but faction is already typed as Faction, so just verify
                # it's a real enum member.
                assert rule.faction in list(Faction), f"{npc_id}: invalid faction {rule.faction}"

    @pytest.mark.parametrize("npc_id", list(NPC_GREETINGS.keys()))
    def test_all_tiers_are_valid(self, npc_id: str) -> None:
        """All min_tier values must be one of the 7 valid tiers."""
        valid_tiers = {
            "OUTCAST",
            "ENEMY",
            "HOSTILE",
            "NEUTRAL",
            "TRUSTED",
            "FRIENDLY",
            "ALLIED",
        }
        for rule in NPC_GREETINGS[npc_id]:
            if rule.min_tier is not None:
                assert rule.min_tier in valid_tiers, f"{npc_id}: invalid tier {rule.min_tier}"

    def test_all_npc_ids_have_at_least_one_faction_rule(self) -> None:
        """Each NPC should have ≥1 faction rule (not just the default)."""
        for npc_id, rules in NPC_GREETINGS.items():
            non_default = [r for r in rules if r.faction is not None]
            assert non_default, f"{npc_id}: no faction rules — greeting table is dead"
