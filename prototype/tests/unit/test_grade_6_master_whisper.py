"""Unit tests for Grade 6 Master Whisper (ADR-0140 §Proposal 4).

Covers:
- MASTER_HINTS_BY_FACTION data structure
- get_master_hint_for_faction lookup
- is_player_master threshold check
- check_construct_whisper_on_combat_start uses master voice when Grade 6
- check_construct_whisper_on_combat_start uses normal voice when Grade < 6
- Master voice replaces normal voice (one-shot semantics preserved)
"""

from __future__ import annotations

from wet_run.lore.construct_whisper import (
    MASTER_GRADE_THRESHOLD,
    MASTER_HINTS_BY_FACTION,
    ConstructWhisper,
    get_master_hint_for_faction,
    is_player_master,
)
from wet_run.lore.construct_whisper_hook import (
    check_construct_whisper_on_combat_start,
)
from wet_run.matrix.node import Faction
from wet_run.run.reputation import ReputationState


class TestMasterHintsTable:
    """MASTER_HINTS_BY_FACTION data structure."""

    def test_all_factions_have_master_hints(self) -> None:
        for faction in (Faction.HOSAKA, Faction.MAAS, Faction.SENSE_NET, Faction.TA):
            assert faction in MASTER_HINTS_BY_FACTION
            hint = MASTER_HINTS_BY_FACTION[faction]
            assert isinstance(hint, str)
            assert len(hint) > 0

    def test_master_grade_threshold(self) -> None:
        assert MASTER_GRADE_THRESHOLD == 6


class TestGetMasterHintForFaction:
    """get_master_hint_for_faction lookup."""

    def test_returns_master_hint_for_known_faction(self) -> None:
        hint = get_master_hint_for_faction(Faction.HOSAKA)
        assert hint is not None
        assert "Hosaka" in hint
        assert "master" in hint.lower()

    def test_returns_none_for_none_faction(self) -> None:
        hint = get_master_hint_for_faction(Faction.NONE)
        assert hint is None

    def test_all_factions_have_unique_master_voice(self) -> None:
        hints = {MASTER_HINTS_BY_FACTION[f] for f in Faction if f != Faction.NONE}
        assert len(hints) == 4


class TestIsPlayerMaster:
    """is_player_master threshold check."""

    def test_grade_6_is_master(self) -> None:
        state = type("S", (), {"player_grade": 6})()
        assert is_player_master(state) is True

    def test_grade_above_6_is_master(self) -> None:
        state = type("S", (), {"player_grade": 7})()
        assert is_player_master(state) is True

    def test_grade_5_is_not_master(self) -> None:
        state = type("S", (), {"player_grade": 5})()
        assert is_player_master(state) is False

    def test_grade_1_is_not_master(self) -> None:
        state = type("S", (), {"player_grade": 1})()
        assert is_player_master(state) is False

    def test_missing_grade_defaults_to_zero(self) -> None:
        state = type("S", (), {})()
        assert is_player_master(state) is False


class TestCombatStartHookIntegration:
    """check_construct_whisper_on_combat_start uses master voice when Grade 6."""

    @staticmethod
    def _make_state(
        player_grade: int = 1,
        factions_with_rep: dict[Faction, int] | None = None,
    ) -> object:
        reputation = ReputationState()
        for faction, rep in (factions_with_rep or {}).items():
            fcr = reputation.get(faction)
            fcr.score = rep
        return type(
            "S",
            (),
            {
                "reputation": reputation,
                "construct_whisper_tracker": ConstructWhisper(),
                "status_messages": [],
                "player_grade": player_grade,
            },
        )()

    def test_grade_6_uses_master_voice(self) -> None:
        state = self._make_state(
            player_grade=6,
            factions_with_rep={Faction.HOSAKA: 50},
        )
        delivered = check_construct_whisper_on_combat_start(state)
        assert len(delivered) == 1
        assert "master construct decrees" in delivered[0]
        assert "HOSAKA" in delivered[0]
        assert "Hosaka" in delivered[0]

    def test_grade_5_uses_normal_voice(self) -> None:
        state = self._make_state(
            player_grade=5,
            factions_with_rep={Faction.HOSAKA: 50},
        )
        delivered = check_construct_whisper_on_combat_start(state)
        assert len(delivered) == 1
        assert "construct whispers" in delivered[0]
        assert "master" not in delivered[0].lower()

    def test_master_voice_replaces_normal_one_shot(self) -> None:
        """Master voice still uses ConstructWhisper tracker (one-shot)."""
        state = self._make_state(
            player_grade=6,
            factions_with_rep={Faction.HOSAKA: 50, Faction.MAAS: 50},
        )
        delivered1 = check_construct_whisper_on_combat_start(state)
        assert len(delivered1) == 2
        # Second call: no double-delivery
        delivered2 = check_construct_whisper_on_combat_start(state)
        assert len(delivered2) == 0

    def test_no_whispers_below_trusted(self) -> None:
        """Grade 6 + low rep = no whisper (rep tier gate still applies)."""
        state = self._make_state(
            player_grade=6,
            factions_with_rep={Faction.HOSAKA: 10},
        )
        delivered = check_construct_whisper_on_combat_start(state)
        assert len(delivered) == 0

    def test_master_voice_for_all_eligible_factions(self) -> None:
        """All factions with rep >= TRUSTED get master voice when Grade 6."""
        state = self._make_state(
            player_grade=6,
            factions_with_rep={
                Faction.HOSAKA: 50,
                Faction.MAAS: 50,
                Faction.SENSE_NET: 50,
                Faction.TA: 50,
            },
        )
        delivered = check_construct_whisper_on_combat_start(state)
        assert len(delivered) == 4
        for msg in delivered:
            assert "master construct decrees" in msg


__all__ = [
    "TestMasterHintsTable",
    "TestGetMasterHintForFaction",
    "TestIsPlayerMaster",
    "TestCombatStartHookIntegration",
]
