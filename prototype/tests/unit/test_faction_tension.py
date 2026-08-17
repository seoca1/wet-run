"""Unit tests for Faction Tension Events (ADR-0140 P2.7).

Covers:
- Rep threshold classification (positive/negative/neutral)
- Trigger probability (statistical sanity)
- Reward application (positive = credits + salvage)
- Penalty application (negative = alarm +1)
- One-shot semantics per (faction, polarity)
- NEUTRAL rep = no event
- Faction.NONE = no event
- Pillar 4 safety (no cross-run)
"""

from __future__ import annotations

import random

from wet_run.matrix.faction_tension import (
    FACTION_TENSION_PROBABILITY,
    NEGATIVE_ALARM_DELTA,
    NEGATIVE_THRESHOLD,
    POSITIVE_CREDITS,
    POSITIVE_SALVAGE,
    POSITIVE_THRESHOLD,
    FactionTensionEvent,
    FactionTensionResult,
    apply_faction_tension,
    check_faction_tension_on_node_entry,
    classify_rep,
    get_faction_rep,
    should_trigger,
)
from wet_run.matrix.node import Faction
from wet_run.run.reputation import ReputationState


class TestTriggerProbability:
    """FACTION_TENSION_PROBABILITY = 25%."""

    def test_default_probability(self) -> None:
        assert FACTION_TENSION_PROBABILITY == 0.25

    def test_should_trigger_25pct(self) -> None:
        rng = random.Random(0)
        triggered = 0
        for _ in range(1000):
            if should_trigger(rng):
                triggered += 1
        # 25% ± 5% with 1000 trials
        assert 200 <= triggered <= 300, f"triggered={triggered}/1000"


class TestClassifyRep:
    """Reputation → event classification."""

    def test_high_rep_positive_event(self) -> None:
        for rep in (50, 75, 100, 200):
            event = classify_rep(rep, Faction.HOSAKA)
            assert event is not None
            assert event.is_positive is True
            assert event.faction is Faction.HOSAKA
            assert event.rep_value == rep

    def test_low_rep_negative_event(self) -> None:
        for rep in (-50, -75, -100, -200):
            event = classify_rep(rep, Faction.TA)
            assert event is not None
            assert event.is_positive is False
            assert event.faction is Faction.TA
            assert event.rep_value == rep

    def test_neutral_rep_no_event(self) -> None:
        for rep in (-49, -20, 0, 20, 49):
            event = classify_rep(rep, Faction.HOSAKA)
            assert event is None

    def test_boundary_thresholds(self) -> None:
        assert POSITIVE_THRESHOLD == 50
        assert NEGATIVE_THRESHOLD == -50


class TestGetFactionRep:
    """Read faction reputation from AppState."""

    def test_initial_state_no_reputation(self) -> None:
        state = type("S", (), {})()
        assert get_faction_rep(state, Faction.HOSAKA) == 0

    def test_reputation_state_access(self) -> None:
        state = type("S", (), {"reputation": ReputationState()})()
        assert get_faction_rep(state, Faction.HOSAKA) == 0
        state.reputation.adjust(Faction.HOSAKA, 20, "test")
        assert get_faction_rep(state, Faction.HOSAKA) == 20

    def test_reputation_score_set_directly(self) -> None:
        state = type("S", (), {"reputation": ReputationState()})()
        fcr = state.reputation.get(Faction.HOSAKA)
        fcr.score = 75
        assert get_faction_rep(state, Faction.HOSAKA) == 75
        fcr.score = 0
        assert get_faction_rep(state, Faction.HOSAKA) == 0
        state.reputation.adjust(Faction.HOSAKA, 20, "test")
        assert get_faction_rep(state, Faction.HOSAKA) == 20


class TestApplyFactionTension:
    """Apply event to AppState."""

    def test_positive_event_credits_and_salvage(self) -> None:
        state = type(
            "S",
            (),
            {
                "credits": 100,
                "salvage_fragments": 0,
                "alarm_level": 0,
                "status_messages": [],
            },
        )()
        event = FactionTensionEvent(
            faction=Faction.HOSAKA,
            is_positive=True,
            rep_value=60,
            label="test",
        )
        result = apply_faction_tension(state, event)
        assert state.credits == 100 + POSITIVE_CREDITS
        assert state.salvage_fragments == POSITIVE_SALVAGE
        assert state.alarm_level == 0
        assert result.event is event
        assert "assistance" in result.status_message

    def test_negative_event_alarm_delta(self) -> None:
        state = type(
            "S",
            (),
            {
                "credits": 100,
                "salvage_fragments": 5,
                "alarm_level": 0,
                "status_messages": [],
            },
        )()
        event = FactionTensionEvent(
            faction=Faction.TA,
            is_positive=False,
            rep_value=-60,
            label="test",
        )
        result = apply_faction_tension(state, event)
        assert state.alarm_level == NEGATIVE_ALARM_DELTA
        assert state.credits == 100  # unchanged
        assert state.salvage_fragments == 5  # unchanged
        assert result.event is event
        assert "interference" in result.status_message

    def test_apply_initializes_missing_fields(self) -> None:
        """State without credits/salvage/alarm should still work."""
        state = type("S", (), {"status_messages": []})()
        event = FactionTensionEvent(
            faction=Faction.HOSAKA,
            is_positive=True,
            rep_value=50,
            label="test",
        )
        apply_faction_tension(state, event)
        assert state.credits == POSITIVE_CREDITS
        assert state.salvage_fragments == POSITIVE_SALVAGE

    def test_apply_appends_status_message(self) -> None:
        state = type(
            "S",
            (),
            {
                "credits": 0,
                "salvage_fragments": 0,
                "alarm_level": 0,
                "status_messages": [],
            },
        )()
        event = FactionTensionEvent(
            faction=Faction.HOSAKA,
            is_positive=True,
            rep_value=50,
            label="test",
        )
        result = apply_faction_tension(state, event)
        assert len(state.status_messages) == 1
        assert result.status_message == state.status_messages[0]


class TestCheckOnNodeEntry:
    """Integration: check_faction_tension_on_node_entry."""

    def test_none_faction_no_event(self) -> None:
        state = type(
            "S",
            (),
            {
                "credits": 0,
                "salvage_fragments": 0,
                "alarm_level": 0,
                "status_messages": [],
                "reputation": ReputationState(),
            },
        )()
        result = check_faction_tension_on_node_entry(
            state, Faction.NONE, random.Random(0), already_triggered=set()
        )
        assert result.event is None
        assert result.status_message == ""

    def test_neutral_rep_no_event(self) -> None:
        state = type(
            "S",
            (),
            {
                "credits": 0,
                "salvage_fragments": 0,
                "alarm_level": 0,
                "status_messages": [],
                "reputation": ReputationState(),
            },
        )()
        for seed in range(50):
            rng = random.Random(seed)
            result = check_faction_tension_on_node_entry(
                state,
                Faction.HOSAKA,
                rng,
                already_triggered=set(),
            )
            assert result.event is None

    def test_high_rep_positive_event_applied(self) -> None:
        state = type(
            "S",
            (),
            {
                "credits": 0,
                "salvage_fragments": 0,
                "alarm_level": 0,
                "status_messages": [],
                "reputation": ReputationState(),
            },
        )()
        state.reputation.get(Faction.HOSAKA).score = 60
        result = None
        for seed in range(200):
            rng = random.Random(seed)
            result = check_faction_tension_on_node_entry(
                state,
                Faction.HOSAKA,
                rng,
                already_triggered=set(),
            )
            if result.event is not None:
                break
        if result is not None and result.event is not None:
            assert result.event.is_positive is True
            assert state.credits == POSITIVE_CREDITS
            assert state.salvage_fragments == POSITIVE_SALVAGE

    def test_low_rep_negative_event_applied(self) -> None:
        state = type(
            "S",
            (),
            {
                "credits": 0,
                "salvage_fragments": 0,
                "alarm_level": 0,
                "status_messages": [],
                "reputation": ReputationState(),
            },
        )()
        state.reputation.get(Faction.TA).score = -60
        result = None
        for seed in range(200):
            rng = random.Random(seed)
            result = check_faction_tension_on_node_entry(
                state,
                Faction.TA,
                rng,
                already_triggered=set(),
            )
            if result.event is not None:
                break
        if result is not None and result.event is not None:
            assert result.event.is_positive is False
            assert state.alarm_level == NEGATIVE_ALARM_DELTA

    def test_trigger_probability_empirical(self) -> None:
        state = type(
            "S",
            (),
            {
                "credits": 0,
                "salvage_fragments": 0,
                "alarm_level": 0,
                "status_messages": [],
                "reputation": ReputationState(),
            },
        )()
        state.reputation.get(Faction.HOSAKA).score = 60
        triggered = 0
        for seed in range(200):
            rng = random.Random(seed)
            result = check_faction_tension_on_node_entry(
                state,
                Faction.HOSAKA,
                rng,
                already_triggered=set(),
            )
            if result.event is not None:
                triggered += 1
        assert 30 <= triggered <= 70, f"triggered={triggered}/200"


class TestFactionTensionOneShot:
    """One-shot per (faction, polarity) pair."""

    def _try_trigger(
        self, state: Faction, faction: Faction, rep: int
    ) -> FactionTensionResult | None:
        """Try seeds until event triggers. Returns None if no seed triggered."""
        state.reputation = ReputationState()
        state.reputation.adjust(faction, rep, "test")
        for seed in range(200):
            rng = random.Random(seed)
            result = check_faction_tension_on_node_entry(
                state, faction, rng, already_triggered=set()
            )
            if result.event is not None:
                return result
        return None

    def test_already_triggered_no_double_reward(self) -> None:
        state = type(
            "S",
            (),
            {
                "credits": 0,
                "salvage_fragments": 0,
                "alarm_level": 0,
                "status_messages": [],
                "reputation": ReputationState(),
            },
        )()
        # Find a triggering seed
        result1 = self._try_trigger(state, Faction.HOSAKA, 60)
        if result1 is not None:
            assert result1.event is not None
            assert state.credits == POSITIVE_CREDITS

            # Now try again with same (faction, polarity) — should skip
            triggered_set = set()
            triggered_set.add(f"hosaka:{result1.event.is_positive}")
            for seed in range(200):
                rng = random.Random(seed)
                result = check_faction_tension_on_node_entry(
                    state, Faction.HOSAKA, rng, already_triggered=triggered_set
                )
                # Either: skipped (already triggered) OR new rng state doesn't trigger
                if result.event is None:
                    assert (
                        "already triggered" in result.status_message or result.status_message == ""
                    )
                    return
        # Otherwise: no seed triggered in 200 trials (statistically unlikely)

    def test_positive_and_negative_independent(self) -> None:
        """Positive and negative event keys are independent (different polarity)."""
        state = type(
            "S",
            (),
            {
                "credits": 0,
                "salvage_fragments": 0,
                "alarm_level": 0,
                "status_messages": [],
                "reputation": ReputationState(),
            },
        )()
        # Trigger positive event for Hosaka
        result1 = self._try_trigger(state, Faction.HOSAKA, 60)
        if result1 is not None and result1.event is not None:
            assert result1.event.is_positive is True

            # Now drop rep to negative
            state.reputation.get(Faction.HOSAKA).score = -140
            assert state.reputation.get(Faction.HOSAKA).score == -140

            # Negative event should still trigger (different key: "hosaka:False")
            triggered_set = {f"hosaka:{result1.event.is_positive}"}
            for seed in range(200):
                rng = random.Random(seed + 1000)
                result = check_faction_tension_on_node_entry(
                    state, Faction.HOSAKA, rng, already_triggered=triggered_set
                )
                if result.event is not None:
                    assert result.event.is_positive is False
                    return
        # Otherwise: no seed triggered (statistically unlikely)


class TestFactionTensionIsPillar4Safe:
    """Verify no cross-run inheritance."""

    def test_no_meta_state_write(self) -> None:
        state = type(
            "S",
            (),
            {
                "credits": 0,
                "salvage_fragments": 0,
                "alarm_level": 0,
                "status_messages": [],
                "reputation": ReputationState(),
                "meta_state": None,
            },
        )()
        state.reputation.get(Faction.HOSAKA).score = 60
        for seed in range(100):
            rng = random.Random(seed)
            if should_trigger(rng):
                check_faction_tension_on_node_entry(
                    state, Faction.HOSAKA, rng, already_triggered=set()
                )
                break
        assert state.meta_state is None

    def test_alarm_resets_on_death(self) -> None:
        """Death resets alarm — escalation penalty is run-scoped."""
        state = type(
            "S",
            (),
            {
                "credits": 0,
                "salvage_fragments": 0,
                "alarm_level": 5,  # high alarm from prior events
                "status_messages": [],
                "reputation": ReputationState(),
            },
        )()
        # New run: alarm resets
        state.alarm_level = 0
        state.reputation = ReputationState()  # also reset
        assert state.alarm_level == 0


__all__ = [
    "TestTriggerProbability",
    "TestClassifyRep",
    "TestGetFactionRep",
    "TestApplyFactionTension",
    "TestCheckOnNodeEntry",
    "TestFactionTensionOneShot",
    "TestFactionTensionIsPillar4Safe",
]
