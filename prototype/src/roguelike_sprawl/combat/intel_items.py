"""Info Market Intel Items (ADR-0151, Cycle 6).

3 intel items purchasable with CRED at the Info Market (픽서 construct).
Closes the salvage 3-way trade-off (HEAL / FRAG / CRED) by giving CRED
a consumption path.

Items:
- alarm_reducer (30 credits base): alarm_level -= 2 (clamped ≥ 0)
- mission_hint (40 credits base): reveals current mission objective
- faction_rumor (50 credits base, Loa faction): next faction event +25%

Pillar 정합 (ADR-0151 §Consequences.7):
- P1 (The Run): alarm_reducer + mission_hint → run weight 감소
- P4 (The Build): in-run only (death = loss via AppState reset)
- P5 (The Style): faction_rumor → 깁슨 "construct echo" 어휘 강화
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from ..crafting.info_market import MarketItem


# Intel item base prices (credits). Faction discount applied on top.
ALARM_REDUCER_PRICE: int = 30
MISSION_HINT_PRICE: int = 40
FACTION_RUMOR_PRICE: int = 50

# Item effect parameters.
ALARM_REDUCER_DELTA: int = 2
FACTION_RUMOR_PROBABILITY_BOOST: float = 0.25
FACTION_RUMOR_FACTION: str = "loa"

# Alarm floor (Pillar 1 weight preservation).
ALARM_FLOOR: int = 0

# ADR-0154: faction_rumor faction variants. Each faction has its own
# faction_rumor item that boosts that faction's event probability.
FACTION_RUMOR_FACTIONS: dict[str, str] = {
    "hosaka_faction_rumor": "hosaka",
    "sense_net_faction_rumor": "sense_net",
    "yakuza_faction_rumor": "yakuza",
    "loa_faction_rumor": "loa",
}


class IntelItemId(StrEnum):
    """Intel item identifier (ADR-0151)."""

    ALARM_REDUCER = "alarm_reducer"
    MISSION_HINT = "mission_hint"
    FACTION_RUMOR = "faction_rumor"


class _IntelStateLike(Protocol):
    """Protocol for the state object passed to :func:`apply_intel_item`.

    Mirrors the attributes used: credits, alarm_level, purchased_intel_items,
    status_messages, current_mission, and optional faction_tension fields.
    """

    credits: int
    alarm_level: int
    purchased_intel_items: list[str]
    status_messages: Any
    current_mission: Any
    faction_tension_probability_boost: float
    faction_tension_triggered: Any


def _record_status(state: _IntelStateLike, message: str) -> None:
    """Append a status message if the state supports it (defensive)."""
    status_list = getattr(state, "status_messages", None)
    if status_list is not None and hasattr(status_list, "append"):
        status_list.append(message)


def apply_alarm_reducer(state: _IntelStateLike) -> int:
    """Apply alarm_reducer: reduce alarm by ALARM_REDUCER_DELTA (clamped ≥ 0).

    Returns the actual alarm reduction applied.
    """
    before = state.alarm_level
    state.alarm_level = max(ALARM_FLOOR, state.alarm_level - ALARM_REDUCER_DELTA)
    actual = before - state.alarm_level
    _record_status(
        state, f">>> Alarm Reducer applied: alarm -{actual} ({before} → {state.alarm_level})"
    )
    return actual


def apply_mission_hint(state: _IntelStateLike) -> bool:
    """Apply mission_hint: reveal current mission objective.

    Returns True if a mission was active and hint was given, False otherwise.
    """
    mission = getattr(state, "current_mission", None)
    if mission is None:
        _record_status(state, ">>> Mission Hint: no active mission — info cached for next run")
        return False
    # Extract objective info — defensive attribute access.
    title = getattr(mission, "title", "unknown") or "unknown"
    objective = getattr(mission, "primary_objective", None)
    zone = getattr(mission, "zone", None)
    objectives = getattr(mission, "secondary_objectives", None) or []
    n_obj = len(objectives) + (1 if objective else 0)
    if n_obj > 1:
        next_obj = objective or "next objective"
        _record_status(
            state,
            f">>> Mission Hint: {n_obj} objectives — next: '{next_obj}'"
            + (f" (zone: {zone})" if zone else ""),
        )
    else:
        zone_str = f" (zone: {zone})" if zone else ""
        _record_status(
            state,
            f">>> Mission Hint: objective = '{objective or title}'{zone_str}",
        )
    return True


def apply_faction_rumor(state: _IntelStateLike, app_state: Any | None = None) -> float:
    """Apply faction_rumor: boost next faction event probability.

    Returns the probability boost (FACTION_RUMOR_PROBABILITY_BOOST).
    The boost is stored on app_state.faction_tension_probability_boost if
    available, otherwise on state (backward compat for tests / single-state usage).
    """
    # ADR-0154 backward compat: write to app_state if available, else state
    if app_state is not None and hasattr(app_state, "faction_tension_probability_boost"):
        app_state.faction_tension_probability_boost = (
            getattr(app_state, "faction_tension_probability_boost", 0.0) or 0.0
        ) + FACTION_RUMOR_PROBABILITY_BOOST
    elif hasattr(state, "faction_tension_probability_boost"):
        state.faction_tension_probability_boost = (
            getattr(state, "faction_tension_probability_boost", 0.0) or 0.0
        ) + FACTION_RUMOR_PROBABILITY_BOOST
    _record_status(
        state,
        f">>> Faction Rumor: {FACTION_RUMOR_FACTION.upper()} contacts — "
        f"next event probability +{int(FACTION_RUMOR_PROBABILITY_BOOST * 100)}%",
    )
    return FACTION_RUMOR_PROBABILITY_BOOST


def apply_intel_item(
    state: _IntelStateLike,
    item_id: str,
    app_state: Any | None = None,
) -> bool:
    """Apply the given intel item to the state.

    Returns True if the item was applied, False if the item_id is unknown
    or the item was already purchased (one-shot per item_id).
    """
    purchased = getattr(state, "purchased_intel_items", None)
    if purchased is None:
        purchased = []
    if item_id in purchased:
        _record_status(state, f">>> already purchased: {item_id} (one-shot per run)")
        return False
    if item_id == IntelItemId.ALARM_REDUCER:
        apply_alarm_reducer(state)
    elif item_id == IntelItemId.MISSION_HINT:
        apply_mission_hint(state)
    elif item_id == IntelItemId.FACTION_RUMOR:
        apply_faction_rumor(state, app_state)
    else:
        return False
    purchased.append(item_id)
    return True


def get_intel_item_price(item_id: str, market_item: MarketItem | None = None) -> int | None:
    """Return the base price for an intel item (for fallback pricing).

    The canonical price is resolved by ``InfoMarket.price_for`` which
    applies faction discount. This helper returns the static base price
    for tests and direct lookups.
    """
    prices: dict[IntelItemId, int] = {
        IntelItemId.ALARM_REDUCER: ALARM_REDUCER_PRICE,
        IntelItemId.MISSION_HINT: MISSION_HINT_PRICE,
        IntelItemId.FACTION_RUMOR: FACTION_RUMOR_PRICE,
    }
    try:
        canonical = IntelItemId(item_id)
    except ValueError:
        return None
    return prices.get(canonical)


__all__ = [
    "ALARM_FLOOR",
    "ALARM_REDUCER_DELTA",
    "ALARM_REDUCER_PRICE",
    "FACTION_RUMOR_FACTION",
    "FACTION_RUMOR_PRICE",
    "FACTION_RUMOR_PROBABILITY_BOOST",
    "IntelItemId",
    "MISSION_HINT_PRICE",
    "apply_alarm_reducer",
    "apply_faction_rumor",
    "apply_intel_item",
    "apply_mission_hint",
    "get_intel_item_price",
]
