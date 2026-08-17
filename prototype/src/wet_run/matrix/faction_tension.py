"""Faction Tension Events (ADR-0140 P2.7).

Mid-mission faction events triggered by player's existing FactionReputation.
Adds variety to matrix runs based on cross-system state.

Behavior:
- Per DATA node entry (~25% chance), if the node's faction is not NONE:
  - Rep >= 50 (FRIENDLY+): positive event (credits + salvage fragment)
  - Rep <= -50 (HOSTILE+): negative event (alarm +1)
  - Otherwise: no event (NEUTRAL zone)

Pillar 4 safe: all rewards are in-run (death = loss), alarm resets on death.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from ..matrix.node import Faction

# Trigger probability per faction DATA node entry.
FACTION_TENSION_PROBABILITY: float = 0.25

# Reputation thresholds (aligned with FactionReputation tiers, run/reputation.py).
# >= POSITIVE_THRESHOLD → positive event
# <= NEGATIVE_THRESHOLD → negative event
POSITIVE_THRESHOLD: int = 50
NEGATIVE_THRESHOLD: int = -50

# Reward constants (positive event).
POSITIVE_CREDITS: int = 30
POSITIVE_SALVAGE: int = 1

# Penalty constants (negative event).
NEGATIVE_ALARM_DELTA: int = 1


@dataclass(frozen=True, slots=True)
class FactionTensionEvent:
    """A single faction tension event."""

    faction: Faction
    is_positive: bool
    rep_value: int
    label: str


@dataclass(frozen=True, slots=True)
class FactionTensionResult:
    """Outcome of a faction-tension check on node entry."""

    event: FactionTensionEvent | None
    status_message: str


def get_faction_rep(state: Any, faction: Faction) -> int:
    """Read current reputation score for a faction from AppState.

    Args:
        state: AppState-like object with reputation attribute.
        faction: Which faction's rep to read.

    Returns:
        Reputation score (0 if no rep recorded for this faction).
    """
    reputation = getattr(state, "reputation", None)
    if reputation is None:
        return 0
    score = reputation.get(faction).score
    return int(score) if score is not None else 0


def should_trigger(rng: random.Random) -> bool:
    """Roll whether a faction tension event should trigger.

    Args:
        rng: Random instance.

    Returns:
        True if event should trigger (probability = FACTION_TENSION_PROBABILITY).
    """
    return rng.random() < FACTION_TENSION_PROBABILITY


def classify_rep(rep_value: int, faction: Faction) -> FactionTensionEvent | None:
    """Classify reputation into a positive/negative event or None.

    Args:
        rep_value: Reputation score.
        faction: Which faction.

    Returns:
        FactionTensionEvent if rep triggers positive/negative event, else None.
    """
    if rep_value >= POSITIVE_THRESHOLD:
        return FactionTensionEvent(
            faction=faction,
            is_positive=True,
            rep_value=rep_value,
            label=f"{faction.value} contacts: positive event",
        )
    if rep_value <= NEGATIVE_THRESHOLD:
        return FactionTensionEvent(
            faction=faction,
            is_positive=False,
            rep_value=rep_value,
            label=f"{faction.value} strikes: negative event",
        )
    return None


def apply_faction_tension(state: Any, event: FactionTensionEvent) -> FactionTensionResult:
    """Apply a faction tension event to AppState.

    Args:
        state: AppState with credits, salvage_fragments, status_messages, alarm,
            reputation fields.
        event: The event to apply.

    Returns:
        FactionTensionResult with status message and the event.
    """
    if event.is_positive:
        current_credits = getattr(state, "credits", 0) or 0
        state.credits = current_credits + POSITIVE_CREDITS
        # ADR-0147: salvage_fragments is now a formal AppState field
        # (default 0). Direct attribute access preferred over getattr.
        state.salvage_fragments = (getattr(state, "salvage_fragments", 0) or 0) + POSITIVE_SALVAGE
        msg = (
            f">>> Faction tension: {event.faction.value} assistance — "
            f"+{POSITIVE_CREDITS} credits, +{POSITIVE_SALVAGE} salvage fragment"
        )
    else:
        current_alarm = getattr(state, "alarm_level", 0) or 0
        state.alarm_level = current_alarm + NEGATIVE_ALARM_DELTA
        msg = (
            f">>> Faction tension: {event.faction.value} interference — "
            f"alarm +{NEGATIVE_ALARM_DELTA}"
        )

    status_list = getattr(state, "status_messages", None)
    if isinstance(status_list, list):
        status_list.append(msg)

    return FactionTensionResult(event=event, status_message=msg)


def check_faction_tension_on_node_entry(
    state: Any,
    faction: Faction,
    rng: random.Random,
    *,
    already_triggered: set[str],
) -> FactionTensionResult:
    """Check if a faction tension event should trigger on this node entry.

    Args:
        state: AppState-like object.
        faction: The node's faction (NodeKind.DATA context).
        rng: Random instance.
        already_triggered: Set of \"{faction.value}:{event_id}\" keys already fired
            this run (prevents double-trigger).

    Returns:
        FactionTensionResult with event (or None) and status message.
    """
    if faction is Faction.NONE:
        return FactionTensionResult(event=None, status_message="")

    if not should_trigger(rng):
        return FactionTensionResult(event=None, status_message="")

    rep_value = get_faction_rep(state, faction)
    event = classify_rep(rep_value, faction)
    if event is None:
        return FactionTensionResult(event=None, status_message="")

    event_id = f"{faction.value}:{event.is_positive}"
    if event_id in already_triggered:
        return FactionTensionResult(
            event=None,
            status_message=f">>> Faction tension already triggered ({event_id})",
        )

    already_triggered.add(event_id)
    return apply_faction_tension(state, event)


__all__ = [
    "FACTION_TENSION_PROBABILITY",
    "POSITIVE_THRESHOLD",
    "NEGATIVE_THRESHOLD",
    "POSITIVE_CREDITS",
    "POSITIVE_SALVAGE",
    "NEGATIVE_ALARM_DELTA",
    "FactionTensionEvent",
    "FactionTensionResult",
    "get_faction_rep",
    "should_trigger",
    "classify_rep",
    "apply_faction_tension",
    "check_faction_tension_on_node_entry",
]
