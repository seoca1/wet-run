"""Defense Stackable + Duration sub-module (ADR-0150, depth split).

Three defense programs with stackable + duration logic:
- Wisp: +1 shield, 5s (stackable, duration refresh)
- Shield: +3 shield, one-hit (consumed on attack)
- Wardrone: +2 shield, 10s + auto-counter every 5s

Pillar 정합 (ADR-0148 §Consequences.7):
- P3 (The Flatline): HEAL 변화 없음, defense 가 *기술적* 깊이
- P5 (The Style): 깁슨 "ICE signature" 어휘
"""

from __future__ import annotations

from enum import StrEnum

from ..state_models import CombatState
from .counter import COUNTER_STUN_MS


class DefenseProgram(StrEnum):
    """Defense program type (ADR-0148)."""

    WISP = "wisp"
    SHIELD = "shield"
    WARDRONE = "wardrone"


# Defense programs: stackable + duration.
WISP_SHIELD: int = 1
WISP_DURATION_MS: int = 5_000
SHIELD_BARRIER: int = 3  # one-hit absorbs 3 damage
WARDRONE_SHIELD: int = 2
WARDRONE_DURATION_MS: int = 10_000
WARDRONE_COUNTER_DMG: int = 5
WARDRONE_COUNTER_INTERVAL_MS: int = 5_000


def apply_wisp(state: CombatState) -> None:
    """Apply Wisp: +1 shield (stackable, 5s duration refresh)."""
    from ..state import _record_event
    from ..state_models import StatusEffect

    state.shield += WISP_SHIELD
    for status in state.player.statuses:
        if status.effect_id == "wisp":
            status.remaining_ms = WISP_DURATION_MS
            _record_event(state, "shield", (180, 200, 255))
            state.push(f">> Wisp: +1 shield (Total: {state.shield}, refreshed 5s)")
            return
    state.player.statuses.append(
        StatusEffect(
            effect_id="wisp",
            remaining_ms=WISP_DURATION_MS,
            is_shield=True,
        )
    )
    _record_event(state, "shield", (180, 200, 255))
    state.push(f">> Wisp: +1 shield (Total: {state.shield}, 5s)")


def apply_shield_barrier(state: CombatState) -> None:
    """Apply Shield barrier: +3 shield (one-hit, consumed on attack)."""
    from ..state import _record_event
    from ..state_models import StatusEffect

    state.shield += SHIELD_BARRIER
    state.player.statuses.append(
        StatusEffect(
            effect_id="shield_barrier",
            remaining_ms=999_999,  # consumed by attack, not by time
            is_shield=True,
        )
    )
    _record_event(state, "shield", (200, 220, 255))
    state.push(">> Shield barrier: +3 shield (one-hit)")


def apply_wardrone(state: CombatState) -> None:
    """Apply Wardrone: +2 shield (10s) + auto-counter every 5s."""
    from ..state import _record_event
    from ..state_models import StatusEffect

    state.shield += WARDRONE_SHIELD
    state.player.statuses.append(
        StatusEffect(
            effect_id="wardrone",
            remaining_ms=WARDRONE_DURATION_MS,
            is_shield=True,
        )
    )
    _record_event(state, "shield", (160, 200, 255))
    state.push(f">> Wardrone: +2 shield (Total: {state.shield}, 10s) + auto-counter")


def tick_defense_durations(state: CombatState) -> None:
    """Decrement defense status durations; remove expired entries.

    Called once per ``step_combat`` tick to maintain the 5s/10s windows.
    Also handles Wardrone auto-counter trigger.
    """
    wardrone = next((s for s in state.player.statuses if s.effect_id == "wardrone"), None)
    if wardrone is not None:
        from ..state import _apply_damage, _record_event
        from ..state_models import StatusEffect

        now = state.tick_ms
        last = getattr(state, "_wardrone_last_counter_ms", -WARDRONE_COUNTER_INTERVAL_MS)
        if now - last >= WARDRONE_COUNTER_INTERVAL_MS:
            target = state.target
            if target is not None and target.hp > 0:
                applied = _apply_damage(state, target, WARDRONE_COUNTER_DMG)
                _record_event(state, "counter", (160, 200, 255))
                state.push(f">>> Wardrone auto-counter: {applied} damage to {target.name}")
                target.statuses.append(
                    StatusEffect(
                        effect_id="stun",
                        remaining_ms=COUNTER_STUN_MS,
                        is_stunned=True,
                    )
                )
            state._wardrone_last_counter_ms = now  # type: ignore[attr-defined]


def tick_defense_expiry(state: CombatState) -> None:
    """Remove expired defense status entries (wisp, wardrone, shield_barrier)."""
    for status in list(state.player.statuses):
        if status.effect_id in {"wisp", "wardrone"} and status.remaining_ms <= 0:
            state.player.statuses.remove(status)
            state.push(f">> {status.effect_id} expired")


__all__ = [
    "DefenseProgram",
    "SHIELD_BARRIER",
    "WARDRONE_COUNTER_DMG",
    "WARDRONE_COUNTER_INTERVAL_MS",
    "WARDRONE_DURATION_MS",
    "WARDRONE_SHIELD",
    "WISP_DURATION_MS",
    "WISP_SHIELD",
    "apply_shield_barrier",
    "apply_wardrone",
    "apply_wisp",
    "tick_defense_durations",
    "tick_defense_expiry",
]
