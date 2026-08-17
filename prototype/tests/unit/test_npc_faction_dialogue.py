"""Tests for faction-aware dialogue gating (Phase 6+).

Covers:
- DialogueChoice.faction_gate / min_tier fields
- is_available() based on player reputation
- _evaluate_faction_gate() helper
- Real DIXIE_FLATLINE_EVENT has faction-gated choices
- Integration with ReputationState
"""

from __future__ import annotations

import pytest

from wet_run.engine.npc_event import (
    DIXIE_FLATLINE_EVENT,
    DialogueChoice,
    _evaluate_faction_gate,
)
from wet_run.matrix.node import Faction
from wet_run.run.reputation import ReputationState

# ============================================================================
# _evaluate_faction_gate helper
# ============================================================================


class TestEvaluateFactionGate:
    @pytest.mark.parametrize(
        ("current", "required", "expected"),
        [
            # Positive tiers: rank <= required triggers
            ("ALLIED", "FRIENDLY", True),
            ("FRIENDLY", "FRIENDLY", True),
            ("TRUSTED", "FRIENDLY", False),
            ("TRUSTED", "TRUSTED", True),
            ("NEUTRAL", "FRIENDLY", False),
            # Negative tiers: rank >= required triggers
            ("HOSTILE", "HOSTILE", True),
            ("ENEMY", "HOSTILE", True),
            ("OUTCAST", "HOSTILE", True),
            ("NEUTRAL", "HOSTILE", False),
            ("TRUSTED", "HOSTILE", False),
            # min_tier None: always true
            ("ALLIED", None, True),
            ("OUTCAST", None, True),
            ("NEUTRAL", None, True),
            # Invalid tier: always true (defensive)
            ("INVALID", "FRIENDLY", True),
            ("NEUTRAL", "INVALID", True),
        ],
    )
    def test_gate_matches_expected(
        self, current: str, required: str | None, expected: bool
    ) -> None:
        assert _evaluate_faction_gate(current, required) is expected


# ============================================================================
# DialogueChoice.faction_gate / is_available
# ============================================================================


class TestDialogueChoiceFactionGate:
    def test_no_gate_always_available(self) -> None:
        """Without faction_gate the choice is universally available."""
        choice = DialogueChoice(key="1", text="x")
        rep = ReputationState()
        rep.get(Faction.HOSAKA).score = -100  # OUTCAST
        assert choice.is_available(rep) is True
        assert choice.is_available(None) is True  # legacy

    def test_positive_gate_friendly_requires_friendly(self) -> None:
        choice = DialogueChoice(key="1", text="x", faction_gate=Faction.HOSAKA, min_tier="FRIENDLY")
        rep_neutral = ReputationState()  # default 0 → NEUTRAL
        rep_friendly = ReputationState()
        rep_friendly.get(Faction.HOSAKA).score = 60
        rep_allied = ReputationState()
        rep_allied.get(Faction.HOSAKA).score = 100

        assert choice.is_available(rep_neutral) is False
        assert choice.is_available(rep_friendly) is True
        assert choice.is_available(rep_allied) is True

    def test_negative_gate_hostile_requires_hostile(self) -> None:
        """Dark-plot choices: only visible to players hostile to a
        faction (e.g. anti-T-A options)."""
        choice = DialogueChoice(key="1", text="x", faction_gate=Faction.TA, min_tier="HOSTILE")
        rep_friendly = ReputationState()
        rep_friendly.get(Faction.TA).score = 60  # FRIENDLY
        rep_hostile = ReputationState()
        rep_hostile.get(Faction.TA).score = -30  # HOSTILE
        rep_outcast = ReputationState()
        rep_outcast.get(Faction.TA).score = -100

        assert choice.is_available(rep_friendly) is False
        assert choice.is_available(rep_hostile) is True
        assert choice.is_available(rep_outcast) is True

    def test_unrelated_faction_does_not_unlock(self) -> None:
        """Choice gated on Hosaka; player friendly with Maas → not visible."""
        choice = DialogueChoice(key="1", text="x", faction_gate=Faction.HOSAKA, min_tier="FRIENDLY")
        rep = ReputationState()
        rep.get(Faction.MAAS).score = 100  # ALLIED with Maas
        assert choice.is_available(rep) is False

    def test_neutral_rep_with_trusted_gate_locks(self) -> None:
        """TRUSTED gate (rank 2) requires rank <= 2, but NEUTRAL is rank 3."""
        choice = DialogueChoice(
            key="1", text="x", faction_gate=Faction.SENSE_NET, min_tier="TRUSTED"
        )
        rep = ReputationState()  # default 0 = NEUTRAL
        assert choice.is_available(rep) is False

    def test_allied_rep_meets_trusted(self) -> None:
        rep = ReputationState()
        rep.get(Faction.SENSE_NET).score = 100  # ALLIED
        choice = DialogueChoice(
            key="1", text="x", faction_gate=Faction.SENSE_NET, min_tier="TRUSTED"
        )
        assert choice.is_available(rep) is True


# ============================================================================
# DIXIE_FLATLINE_EVENT integration
# ============================================================================


class TestDixieEventHasFactionGatedChoices:
    def test_default_choices_still_available(self) -> None:
        """The 3 original choices (1, 2, 3) have no faction gate."""
        first_line = DIXIE_FLATLINE_EVENT.lines[0]
        rep = ReputationState()  # all neutral
        available = [c for c in first_line.choices if c.is_available(rep)]
        # Choices 1, 2, 3 are always available (no faction_gate).
        keys = {c.key for c in available}
        assert "1" in keys
        assert "2" in keys
        assert "3" in keys
        # Choice 4 (Hosaka FRIENDLY) is NOT visible at neutral.
        assert "4" not in keys
        # Choice 5 (T-A HOSTILE) is NOT visible at neutral.
        assert "5" not in keys

    def test_choice_4_visible_with_hosaka_friendly(self) -> None:
        """Dixie's Hosaka branch unlocks at FRIENDLY+ reputation."""
        rep = ReputationState()
        rep.get(Faction.HOSAKA).score = 60  # FRIENDLY
        first_line = DIXIE_FLATLINE_EVENT.lines[0]
        available = [c for c in first_line.choices if c.is_available(rep)]
        assert "4" in {c.key for c in available}

    def test_choice_5_visible_with_ta_hostile(self) -> None:
        """Dixie's anti-T-A branch unlocks at HOSTILE+ reputation."""
        rep = ReputationState()
        rep.get(Faction.TA).score = -30  # HOSTILE
        first_line = DIXIE_FLATLINE_EVENT.lines[0]
        available = [c for c in first_line.choices if c.is_available(rep)]
        assert "5" in {c.key for c in available}

    def test_all_branches_with_max_rep(self) -> None:
        """At ALLIED with Hosaka AND HOSTILE with T-A (technically
        impossible — but if it were, both would show)."""
        rep = ReputationState()
        rep.get(Faction.HOSAKA).score = 100  # ALLIED
        rep.get(Faction.TA).score = -30  # HOSTILE
        first_line = DIXIE_FLATLINE_EVENT.lines[0]
        available = [c for c in first_line.choices if c.is_available(rep)]
        keys = {c.key for c in available}
        # 1, 2, 3 (no gate) + 4 (Hosaka gate met) + 5 (T-A gate met)
        assert keys == {"1", "2", "3", "4", "5"}

    def test_choice_4_response_mentions_hosaka_intel(self) -> None:
        """Choice 4's response should mention the faction-specific intel."""
        first_line = DIXIE_FLATLINE_EVENT.lines[0]
        choice_4 = next(c for c in first_line.choices if c.key == "4")
        assert "Hosaka" in choice_4.response

    def test_choice_5_response_mentions_ta_intel(self) -> None:
        first_line = DIXIE_FLATLINE_EVENT.lines[0]
        choice_5 = next(c for c in first_line.choices if c.key == "5")
        assert "T-A" in choice_5.response
        assert "second" in choice_5.response.lower()


# ============================================================================
# view layer integration (visible_choices count)
# ============================================================================


class TestViewLayerFiltering:
    def test_visible_choices_count_at_neutral(self) -> None:
        from wet_run.run.reputation import ReputationState

        rep = ReputationState()
        first_line = DIXIE_FLATLINE_EVENT.lines[0]
        visible = [c for c in first_line.choices if c.is_available(rep)]
        # 3 ungated + 0 gated (Hosaka at neutral, T-A at neutral)
        assert len(visible) == 3

    def test_visible_choices_count_with_hosaka_friendly(self) -> None:
        rep = ReputationState()
        rep.get(Faction.HOSAKA).score = 60
        first_line = DIXIE_FLATLINE_EVENT.lines[0]
        visible = [c for c in first_line.choices if c.is_available(rep)]
        # 3 ungated + 1 (Hosaka friendly)
        assert len(visible) == 4

    def test_visible_choices_count_with_both_branches(self) -> None:
        rep = ReputationState()
        rep.get(Faction.HOSAKA).score = 60  # FRIENDLY
        rep.get(Faction.TA).score = -30  # HOSTILE
        first_line = DIXIE_FLATLINE_EVENT.lines[0]
        visible = [c for c in first_line.choices if c.is_available(rep)]
        # All 5 available.
        assert len(visible) == 5

    def test_visible_choices_count_at_outcast_with_ta(self) -> None:
        """Player OUTCAST with T-A (rank 6) meets HOSTILE+ (rank 4)."""
        rep = ReputationState()
        rep.get(Faction.TA).score = -100
        first_line = DIXIE_FLATLINE_EVENT.lines[0]
        visible = [c for c in first_line.choices if c.is_available(rep)]
        # 3 ungated + 1 (T-A hostile) = 4
        assert len(visible) == 4
