"""Counter Window sub-module (ADR-0150, depth split).

Enemy skill use opens a 200ms counter-attack window for the player.
COUNTER skill during the window deals 2x damage + 500ms stun.

Pillar 정합 (ADR-0148 §Consequences.7):
- P3 (The Flatline): counter 가 *기술적* 깊이 (HEAL 변화 없음)
- P5 (The Style): 깁슨 "counter-trace" 어휘
"""

from __future__ import annotations

from ..state_models import CombatState, Skill

# Counter Window: 200ms reactive gameplay window after enemy skill use.
COUNTER_WINDOW_MS: int = 200
COUNTER_DAMAGE_MULTIPLIER: float = 2.0
COUNTER_STUN_MS: int = 500


def open_counter_window(state: CombatState) -> None:
    """Open a 200ms counter-attack window after enemy skill use.

    Sets ``state.counter_window_open_ms = state.tick_ms + 200``. The
    window is consumed by a player COUNTER skill use, or expires when
    ``state.tick_ms >= counter_window_open_ms`` (callers should check
    via :func:`is_counter_window_open`).
    """
    state.counter_window_open_ms = state.tick_ms + COUNTER_WINDOW_MS


def is_counter_window_open(state: CombatState) -> bool:
    """Return True iff the counter window is still open (200ms window)."""
    deadline = getattr(state, "counter_window_open_ms", 0)
    return state.tick_ms < deadline


def apply_counter_attack(state: CombatState, skill: Skill) -> int:
    """Resolve a player COUNTER skill during an open window.

    Returns the damage dealt (2x base). Also applies a 0.5s stun to the
    target. Caller is responsible for prerequisite checks (AP, etc.).
    """
    target = state.target
    if target is None:
        return 0
    base = skill.damage if skill.damage > 0 else state.player.auto_attack_damage
    dmg = int(base * COUNTER_DAMAGE_MULTIPLIER)
    from ..state import _apply_damage, _record_event
    from ..state_models import StatusEffect

    applied = _apply_damage(state, target, dmg)
    _record_event(state, "counter", skill.effect_color)
    state.push(f">>> Counter-attack lands for {applied} damage!")
    target.statuses.append(
        StatusEffect(
            effect_id="stun",
            remaining_ms=COUNTER_STUN_MS,
            is_stunned=True,
        )
    )
    state.push(f">>> {target.name} stunned for {COUNTER_STUN_MS // 1000}s!")
    state.counter_window_open_ms = 0
    return applied


def counter_window_active_and_expired(state: CombatState) -> bool:
    """Return True iff a counter window was open but has now expired.

    Used by ``step_combat`` to log a missed window.
    """
    if not hasattr(state, "counter_window_open_ms"):
        return False
    deadline = state.counter_window_open_ms
    if deadline == 0:
        return False
    return state.tick_ms >= deadline


__all__ = [
    "COUNTER_DAMAGE_MULTIPLIER",
    "COUNTER_STUN_MS",
    "COUNTER_WINDOW_MS",
    "apply_counter_attack",
    "counter_window_active_and_expired",
    "is_counter_window_open",
    "open_counter_window",
]
