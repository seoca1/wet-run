"""Automated tests for Info Market Intel Items (ADR-0151, Cycle 6).

Source spec: Game/wet_run/testcases/combat/info-market.md (TC-INTEL-001 ~ 012)

Three intel items purchasable with CRED:
- alarm_reducer (30 credits): alarm_level -= 2 (clamped >= 0)
- mission_hint (40 credits): reveals current mission objective
- faction_rumor (50 credits, Loa faction): next faction event +25%
"""

from __future__ import annotations

import pytest

from wet_run.combat.intel_items import (
    ALARM_FLOOR,
    ALARM_REDUCER_DELTA,
    ALARM_REDUCER_PRICE,
    FACTION_RUMOR_PRICE,
    FACTION_RUMOR_PROBABILITY_BOOST,
    MISSION_HINT_PRICE,
    IntelItemId,
    apply_alarm_reducer,
    apply_faction_rumor,
    apply_intel_item,
    apply_mission_hint,
    get_intel_item_price,
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


class _StubMission:
    __slots__ = ("title", "primary_objective", "zone", "secondary_objectives")

    def __init__(
        self,
        *,
        title: str = "Test Mission",
        primary_objective: str | None = "extract data",
        zone: str | None = "MID",
        secondary_objectives: tuple[str, ...] = (),
    ) -> None:
        self.title = title
        self.primary_objective = primary_objective
        self.zone = zone
        self.secondary_objectives = secondary_objectives


# ---------------------------------------------------------------------------
# TC-INTEL-001: alarm_reducer reduces alarm by 2
# ---------------------------------------------------------------------------


class TestAlarmReducer:
    def test_reduces_alarm_by_delta(self) -> None:
        state = _StubState(credits=50, alarm_level=4)
        result = apply_alarm_reducer(state)
        assert state.alarm_level == 2
        assert result == 2
        assert any("Alarm Reducer applied" in m for m in state.status_messages.data)

    def test_reduces_alarm_full(self) -> None:
        state = _StubState(credits=50, alarm_level=5)
        apply_alarm_reducer(state)
        assert state.alarm_level == 3

    def test_does_not_go_negative(self) -> None:
        state = _StubState(credits=50, alarm_level=0)
        apply_alarm_reducer(state)
        assert state.alarm_level == 0

    def test_clamped_at_zero(self) -> None:
        state = _StubState(credits=50, alarm_level=1)
        apply_alarm_reducer(state)
        assert state.alarm_level == 0

    def test_delta_constant(self) -> None:
        assert ALARM_REDUCER_DELTA == 2
        assert ALARM_FLOOR == 0


# ---------------------------------------------------------------------------
# TC-INTEL-002: mission_hint reveals objective
# ---------------------------------------------------------------------------


class TestMissionHint:
    def test_reveals_single_objective(self) -> None:
        state = _StubState(
            current_mission=_StubMission(primary_objective="extract data", zone="MID")
        )
        result = apply_mission_hint(state)
        assert result is True
        assert any("extract data" in m for m in state.status_messages.data)
        assert any("MID" in m for m in state.status_messages.data)

    def test_reveals_multi_objectives(self) -> None:
        state = _StubState(
            current_mission=_StubMission(
                primary_objective="extract data",
                secondary_objectives=("bypass security", "defeat ICE"),
            )
        )
        apply_mission_hint(state)
        assert any("3 objectives" in m for m in state.status_messages.data)

    def test_no_active_mission(self) -> None:
        state = _StubState(current_mission=None)
        result = apply_mission_hint(state)
        assert result is False
        assert any("no active mission" in m for m in state.status_messages.data)


# ---------------------------------------------------------------------------
# TC-INTEL-003: faction_rumor increases event probability
# ---------------------------------------------------------------------------


class TestFactionRumor:
    def test_increases_probability_boost(self) -> None:
        state = _StubState()
        result = apply_faction_rumor(state)
        assert result == FACTION_RUMOR_PROBABILITY_BOOST
        assert any("Faction Rumor" in m for m in state.status_messages.data)

    def test_appends_to_app_state_boost(self) -> None:
        state = _StubState()
        app_state = _StubState()
        app_state.faction_tension_probability_boost = 0.1
        apply_faction_rumor(state, app_state=app_state)
        assert app_state.faction_tension_probability_boost == pytest.approx(0.35)

    def test_starts_from_zero(self) -> None:
        state = _StubState()
        app_state = _StubState()
        apply_faction_rumor(state, app_state=app_state)
        assert app_state.faction_tension_probability_boost == pytest.approx(0.25)

    def test_message_includes_pct(self) -> None:
        state = _StubState()
        apply_faction_rumor(state)
        assert any("+25%" in m for m in state.status_messages.data)


# ---------------------------------------------------------------------------
# TC-INTEL-004: apply_intel_item one-shot per item
# ---------------------------------------------------------------------------


class TestApplyIntelItem:
    def test_alarm_reducer_one_shot(self) -> None:
        state = _StubState(alarm_level=4)
        assert apply_intel_item(state, IntelItemId.ALARM_REDUCER) is True
        assert state.alarm_level == 2
        assert IntelItemId.ALARM_REDUCER in state.purchased_intel_items
        # Re-apply should fail
        state.alarm_level = 4  # reset
        result = apply_intel_item(state, IntelItemId.ALARM_REDUCER)
        assert result is False
        assert state.alarm_level == 4  # unchanged

    def test_mission_hint_one_shot(self) -> None:
        state = _StubState(current_mission=_StubMission(primary_objective="extract"))
        assert apply_intel_item(state, IntelItemId.MISSION_HINT) is True
        result = apply_intel_item(state, IntelItemId.MISSION_HINT)
        assert result is False

    def test_faction_rumor_one_shot(self) -> None:
        state = _StubState()
        app_state = _StubState()
        assert apply_intel_item(state, IntelItemId.FACTION_RUMOR, app_state=app_state) is True
        result = apply_intel_item(state, IntelItemId.FACTION_RUMOR, app_state=app_state)
        assert result is False

    def test_unknown_item_returns_false(self) -> None:
        state = _StubState()
        result = apply_intel_item(state, "unknown_item")
        assert result is False


# ---------------------------------------------------------------------------
# TC-INTEL-005: Pricing constants
# ---------------------------------------------------------------------------


class TestPricing:
    def test_alarm_reducer_price(self) -> None:
        assert ALARM_REDUCER_PRICE == 30
        assert get_intel_item_price(IntelItemId.ALARM_REDUCER) == 30

    def test_mission_hint_price(self) -> None:
        assert MISSION_HINT_PRICE == 40
        assert get_intel_item_price(IntelItemId.MISSION_HINT) == 40

    def test_faction_rumor_price(self) -> None:
        assert FACTION_RUMOR_PRICE == 50
        assert get_intel_item_price(IntelItemId.FACTION_RUMOR) == 50

    def test_unknown_item_returns_none(self) -> None:
        assert get_intel_item_price("unknown_item") is None


# ---------------------------------------------------------------------------
# TC-INTEL-006: IntelItemId enum
# ---------------------------------------------------------------------------


class TestIntelItemId:
    def test_alarm_reducer_value(self) -> None:
        assert IntelItemId.ALARM_REDUCER == "alarm_reducer"

    def test_mission_hint_value(self) -> None:
        assert IntelItemId.MISSION_HINT == "mission_hint"

    def test_faction_rumor_value(self) -> None:
        assert IntelItemId.FACTION_RUMOR == "faction_rumor"


# ---------------------------------------------------------------------------
# TC-INTEL-007: Integration with state
# ---------------------------------------------------------------------------


class TestStateIntegration:
    def test_purchased_intel_items_tracks_history(self) -> None:
        state = _StubState(credits=200, alarm_level=5)
        apply_intel_item(state, IntelItemId.ALARM_REDUCER)
        apply_intel_item(state, IntelItemId.MISSION_HINT)
        apply_intel_item(state, IntelItemId.FACTION_RUMOR)
        assert state.purchased_intel_items == [
            IntelItemId.ALARM_REDUCER,
            IntelItemId.MISSION_HINT,
            IntelItemId.FACTION_RUMOR,
        ]

    def test_status_messages_appended(self) -> None:
        state = _StubState(alarm_level=4)
        apply_intel_item(state, IntelItemId.ALARM_REDUCER)
        assert len(state.status_messages.data) >= 1
