"""Status effects system (ADR-0160).

5-effect vocabulary: DoT, Stun, Slow, Silence, Vulnerability.
Each effect has an application helper (adds to ``target.statuses``),
tick logic (in ``state_transitions._tick_status_effects``), and a
read consumer (multiplier/boolean for combat tick + damage calc).

The data schema (``StatusEffect`` dataclass) lives in
:mod:`state_models`; this module owns the *vocabulary* and *accessors*.
"""

from __future__ import annotations

from .state_models import Combatant, CombatState, StatusEffect

__all__ = [
    "apply_silence",
    "apply_slow",
    "apply_vulnerable",
    "get_slow_multiplier",
    "get_vulnerability_multiplier",
    "is_silenced",
]


def apply_slow(state: CombatState, target: Combatant, slow_pct: int, duration_ms: int) -> None:
    """Apply a slow effect to target. Stacks with existing slows."""
    target.statuses.append(
        StatusEffect(
            effect_id="slow",
            remaining_ms=duration_ms,
            slow_pct=slow_pct,
        )
    )
    state.push(f"  {target.name} slowed ({slow_pct}%) for {duration_ms // 1000}s")


def apply_silence(state: CombatState, target: Combatant, duration_ms: int) -> None:
    """Apply a silence effect to target. Disables skill use for duration."""
    target.statuses.append(
        StatusEffect(
            effect_id="silence",
            remaining_ms=duration_ms,
            is_silenced=True,
        )
    )
    state.push(f"  {target.name} silenced for {duration_ms // 1000}s")


def apply_vulnerable(
    state: CombatState, target: Combatant, vuln_pct: int, duration_ms: int
) -> None:
    """Apply a vulnerability effect to target. Damage taken increases."""
    target.statuses.append(
        StatusEffect(
            effect_id="vulnerable",
            remaining_ms=duration_ms,
            vulnerability_pct=vuln_pct,
        )
    )
    state.push(f"  {target.name} vulnerable (+{vuln_pct}% damage taken) for {duration_ms // 1000}s")


def get_slow_multiplier(combattant: Combatant) -> float:
    """Return the slow multiplier (1.0 = no slow, 0.7 = 30% slow).

    Composes multiplicatively across multiple slow effects.
    """
    mult = 1.0
    for status in combattant.statuses:
        if status.effect_id == "slow" and status.slow_pct > 0:
            mult *= 1.0 - status.slow_pct / 100.0
    return mult


def get_vulnerability_multiplier(combattant: Combatant) -> float:
    """Return the damage-taken multiplier (1.0 = neutral, 1.2 = +20%).

    Composes multiplicatively across multiple vulnerability effects.
    """
    mult = 1.0
    for status in combattant.statuses:
        if status.effect_id == "vulnerable" and status.vulnerability_pct > 0:
            mult *= 1.0 + status.vulnerability_pct / 100.0
    return mult


def is_silenced(combattant: Combatant) -> bool:
    """Return True iff combattant has any active silence status."""
    return any(
        status.effect_id == "silence" and status.is_silenced and status.remaining_ms > 0
        for status in combattant.statuses
    )
