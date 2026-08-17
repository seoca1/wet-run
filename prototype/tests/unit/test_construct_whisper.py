"""Tests for ConstructWhisper (ADR-0140 §Proposal 1)."""

from __future__ import annotations

from wet_run.lore import (
    HINTS_BY_FACTION,
    WHISPER_UNLOCK_TIER,
    ConstructWhisper,
    get_hint_for_faction,
)
from wet_run.matrix.node import Faction
from wet_run.run.reputation import ReputationState


class TestConstructWhisperBasics:
    """Tracker state, cap enforcement, recording."""

    def test_default_state(self) -> None:
        w = ConstructWhisper()
        assert w.count == 0
        assert w.remaining == 5
        assert w.whispered_factions == set()

    def test_record_whisper(self) -> None:
        w = ConstructWhisper()
        assert w.record_whisper(Faction.HOSAKA) is True
        assert w.has_whispered(Faction.HOSAKA)
        assert w.count == 1
        assert w.remaining == 4

    def test_record_idempotent(self) -> None:
        w = ConstructWhisper()
        w.record_whisper(Faction.HOSAKA)
        assert w.record_whisper(Faction.HOSAKA) is False
        assert w.count == 1

    def test_cap_enforced(self) -> None:
        w = ConstructWhisper(max_total=2)
        w.record_whisper(Faction.HOSAKA)
        w.record_whisper(Faction.MAAS)
        assert w.can_whisper(Faction.SENSE_NET) is False
        assert w.record_whisper(Faction.SENSE_NET) is False
        assert w.count == 2

    def test_reset(self) -> None:
        w = ConstructWhisper()
        w.record_whisper(Faction.HOSAKA)
        w.record_whisper(Faction.MAAS)
        w.reset()
        assert w.count == 0
        assert w.whispered_factions == set()


class TestHintLookup:
    """Static hint data by faction + tier."""

    def test_all_factions_have_trusted_hint(self) -> None:
        for faction in (Faction.HOSAKA, Faction.MAAS, Faction.SENSE_NET, Faction.TA):
            hint = get_hint_for_faction(faction, "TRUSTED")
            assert hint, f"{faction} missing TRUSTED hint"

    def test_unknown_faction_returns_none(self) -> None:
        assert get_hint_for_faction(Faction.NONE, "TRUSTED") is None

    def test_unknown_tier_returns_none(self) -> None:
        assert get_hint_for_faction(Faction.HOSAKA, "BOGUS") is None

    def test_hints_have_gibson_tone(self) -> None:
        """All hints reference Sprawl-style faction voice (no gameplay terms)."""
        for faction, hints in HINTS_BY_FACTION.items():
            for tier, hint in hints.items():
                assert "ICE" in hint or "construct" in hint or "matrix" in hint, (
                    f"{faction}/{tier} hint lacks Sprawl terminology: {hint[:50]}"
                )


class TestFindEligibleFactions:
    """Faction tier gating."""

    def test_neutral_factions_excluded(self) -> None:
        rep = ReputationState()
        w = ConstructWhisper()
        eligible = w.find_eligible_factions(rep)
        assert eligible == []

    def test_trusted_faction_eligible(self) -> None:
        rep = ReputationState()
        rep.adjust(Faction.HOSAKA, 25, source="test")
        w = ConstructWhisper()
        eligible = w.find_eligible_factions(rep)
        assert (Faction.HOSAKA, "TRUSTED") in eligible

    def test_friendly_faction_eligible(self) -> None:
        rep = ReputationState()
        rep.adjust(Faction.HOSAKA, 55, source="test")
        w = ConstructWhisper()
        eligible = w.find_eligible_factions(rep)
        assert any(f == Faction.HOSAKA for f, _ in eligible)

    def test_already_whispered_excluded(self) -> None:
        rep = ReputationState()
        rep.adjust(Faction.HOSAKA, 25, source="test")
        w = ConstructWhisper()
        w.record_whisper(Faction.HOSAKA)
        eligible = w.find_eligible_factions(rep)
        assert all(f != Faction.HOSAKA for f, _ in eligible)

    def test_unlock_tier_constant(self) -> None:
        """WHISPER_UNLOCK_TIER must be TRUSTED for proper gating."""
        assert WHISPER_UNLOCK_TIER == "TRUSTED"
