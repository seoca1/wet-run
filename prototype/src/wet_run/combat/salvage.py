"""Data Salvage menu (ADR-0014 + ADR-0147 + ADR-0152).

Player chooses one of 4 options after defeating ICE:
- HEAL: +15% max HP (Pillar 3 weight preserved, ADR-0152 rebalance 20%→15%)
- FRAG: +1 salvage_fragment (in-run, Pillar 4 build)
- CRED: +30 credits + alarm -1 (Pillar 1 weight trade-off)
- SKIP: no reward (strategic choice)

Alarm interaction (Pillar 1, ADR-0147):
- alarm >= 3: FRAG/CRED yields reduced 50% (rounded down, min 0).
- alarm < 0: clamped to 0 (defensive).
- HEAL unaffected by alarm (Pillar 3 weight preservation).

Pillar 정합 (ADR-0147 §Consequences.7):
- P1 (The Run): alarm-aware salvage trade-off
- P2 (The Matrix): 데이터 추출 메타포
- P3 (The Flatline): HEAL 15% + 1-of-4 choice — 무게 보존 (1vN 에서 trivial 방지)
- P4 (The Build): FRAG in-run only (death = loss)
- P5 (The Style): 깁슨 어휘 ("data exposed", "ICE breach")
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol

from .gibson_fluff import push_fluff
from .run_mutators import is_heal_disabled


class SalvageChoice(StrEnum):
    """Player's choice from the post-victory salvage menu (ADR-0014)."""

    HEAL = "heal"
    FRAG = "frag"
    CRED = "cred"
    SKIP = "skip"


# Pillar 3 (The Flatline): HEAL yields 15% of max HP, minimum 1.
# ADR-0152 rebalance: was 20% (0.20), now 15% (0.15) to preserve
# Pillar 3 weight in 1vN encounters (multi-enemy expansion).
HEAL_PCT: float = 0.15
HEAL_MIN: int = 1

# Pillar 4 (The Build): FRAG grants +1 salvage fragment (in-run only).
FRAG_YIELD: int = 1

# Pillar 1 (The Run): CRED grants +30 credits and -1 alarm (clamped ≥ 0).
CRED_CREDITS: int = 30
CRED_ALARM_RELIEF: int = 1

# Pillar 1 trade-off: at or above this alarm level, FRAG/CRED yields
# are reduced by 50% (rounded down, min 0). HEAL is not affected
# (Pillar 3 weight preservation).
ALARM_HIGH_THRESHOLD: int = 3
ALARM_REDUCTION_PCT: float = 0.50

# Defensive bounds for alarm level.
ALARM_MIN: int = 0


class _StateLike(Protocol):
    """Protocol for the state object passed to :func:apply_salvage.

    The actual implementation is :class:`engine.state.AppState`; this
    protocol lets the module be unit-tested without importing the
    full engine (which would create a circular import).
    """

    hp: int
    max_hp: int
    credits: int
    alarm_level: int
    salvage_fragments: int
    status_messages: Any


def _heal_amount(max_hp: int) -> int:
    """Compute HEAL yield: 15% of max HP, minimum 1 (Pillar 3, ADR-0152)."""
    return max(HEAL_MIN, round(max_hp * HEAL_PCT))


def _alarm_reduces_yield(alarm_level: int) -> bool:
    """True if alarm level triggers the 50% FRAG/CRED yield reduction."""
    return alarm_level >= ALARM_HIGH_THRESHOLD


def _apply_alarm_relief(state: _StateLike) -> None:
    """Reduce alarm level by CRED_ALARM_RELIEF, clamped at ALARM_MIN."""
    state.alarm_level = max(ALARM_MIN, state.alarm_level - CRED_ALARM_RELIEF)


def _record_status(state: _StateLike, message: str) -> None:
    """Append a status message if the state supports it (defensive)."""
    status_list = getattr(state, "status_messages", None)
    if status_list is not None and hasattr(status_list, "append"):
        status_list.append(message)


def apply_salvage(state: _StateLike, choice: SalvageChoice) -> int:
    """Apply the player's salvage choice to state and return new HP.

    Side effects on state (Pillar-validated):
    - HEAL: ``state.hp = min(max_hp, hp + heal)``
    - FRAG: ``state.salvage_fragments += yield`` (yield 0 or 1, alarm-aware)
    - CRED: ``state.credits += yield`` (yield 0 or 30, alarm-aware)
             + ``state.alarm_level -= 1`` (clamped ≥ 0)
    - SKIP: no state change

    Status messages (i18n-free, English only) are appended to
    ``state.status_messages`` when available.

    Args:
        state: AppState-like object with hp, max_hp, credits, alarm_level,
            salvage_fragments, status_messages attributes.
        choice: Player's salvage choice.

    Returns:
        New HP after applying the choice. For non-HEAL choices, returns
        the current HP unchanged.
    """
    if choice is SalvageChoice.HEAL:
        if is_heal_disabled(state):
            _record_status(state, ">>> HEAL disabled by run mutator")
            return state.hp
        heal = _heal_amount(state.max_hp)
        before = state.hp
        state.hp = min(state.max_hp, state.hp + heal)
        actual_heal = state.hp - before
        if actual_heal > 0:
            _record_status(state, f">>> HEAL applied: +{actual_heal} HP")
        else:
            _record_status(state, ">>> no damage to repair")
        return state.hp

    if choice is SalvageChoice.FRAG:
        if _alarm_reduces_yield(state.alarm_level):
            _record_status(state, ">>> alarm high — fragment lost in noise")
            return state.hp
        state.salvage_fragments = getattr(state, "salvage_fragments", 0) + FRAG_YIELD
        _record_status(state, f">>> FRAG recovered: +{FRAG_YIELD} program fragment")
        return state.hp

    if choice is SalvageChoice.CRED:
        if _alarm_reduces_yield(state.alarm_level):
            yield_credits = int(CRED_CREDITS * ALARM_REDUCTION_PCT)
            _record_status(state, ">>> alarm high — reduced yield")
        else:
            yield_credits = CRED_CREDITS
        state.credits = getattr(state, "credits", 0) + yield_credits
        _apply_alarm_relief(state)
        _record_status(
            state, f">>> CRED recovered: +{yield_credits} credits, alarm -{CRED_ALARM_RELIEF}"
        )
        return state.hp

    # SKIP: no state change
    _record_status(state, ">>> salvage skipped")
    push_fluff(state, "salvage")
    return state.hp


__all__ = [
    "ALARM_HIGH_THRESHOLD",
    "ALARM_MIN",
    "ALARM_REDUCTION_PCT",
    "CRED_ALARM_RELIEF",
    "CRED_CREDITS",
    "FRAG_YIELD",
    "HEAL_MIN",
    "HEAL_PCT",
    "SalvageChoice",
    "apply_salvage",
]
