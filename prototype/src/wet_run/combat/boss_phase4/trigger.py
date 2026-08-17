"""Boss Phase 4 trigger/detection sub-module (ADR-0150 follow-up, Cycle 5).

Phase 4 trigger at HP <= 15% with one-shot guard via
``app_state.phase4_triggered`` flag. Maps canonical boss_id to
``Phase4Mechanic`` enum.

Pillar 정합 (ADR-0149 §Consequences.7):
- P1 (The Run): 15% HP trigger, 1회 (one-shot)
- P5 (The Style): 5 unique 깁슨 어휘 (mechanic names)
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..state import Combatant, CombatState


# Phase 4 trigger threshold (HP fraction).
PHASE4_HP_THRESHOLD: float = 0.15


class Phase4Mechanic(StrEnum):
    """Per-boss Phase 4 finale mechanic identifier (ADR-0149)."""

    PERSONALITY_DRIFT = "personality_drift"
    FAMILY_VOTE = "family_vote"
    CONSTRUCT_MERGE = "construct_merge"
    GROUND_SLAM = "ground_slam"
    GLITCH_BURST = "glitch_burst"


def should_trigger_phase4(boss: Combatant, max_boss_hp: int | None = None) -> bool:
    """Return True iff boss HP fraction is at or below PHASE4_HP_THRESHOLD."""
    if max_boss_hp is None:
        max_boss_hp = boss.max_hp
    if max_boss_hp <= 0:
        return False
    return boss.hp / max_boss_hp <= PHASE4_HP_THRESHOLD


def trigger_phase4(state: CombatState, app_state: Any, boss_id: str) -> Phase4Mechanic | None:
    """Trigger the Phase 4 finale mechanic for the given boss.

    One-shot per fight — guarded by ``app_state.phase4_triggered`` flag.

    Returns the triggered :class:`Phase4Mechanic` or None if already
    triggered or HP threshold not met.
    """
    from .intro import normalize_boss_id

    if getattr(app_state, "phase4_triggered", False):
        return None
    boss = state.target
    if boss is None:
        return None
    if not should_trigger_phase4(boss):
        return None
    canonical = normalize_boss_id(boss_id)
    mapping: dict[str, Phase4Mechanic] = {
        "wintermute": Phase4Mechanic.PERSONALITY_DRIFT,
        "ta_prime": Phase4Mechanic.FAMILY_VOTE,
        "neuromancer": Phase4Mechanic.CONSTRUCT_MERGE,
        "goliath_prime": Phase4Mechanic.GROUND_SLAM,
        "black_ice_lord": Phase4Mechanic.GLITCH_BURST,
    }
    mechanic = mapping.get(canonical)
    if mechanic is None:
        return None
    app_state.phase4_triggered = True
    state.boss_phase4_mechanic = mechanic.value
    state.push(f">>> PHASE 4: {canonical.upper()} activates {mechanic.value}!")
    return mechanic


__all__ = [
    "PHASE4_HP_THRESHOLD",
    "Phase4Mechanic",
    "should_trigger_phase4",
    "trigger_phase4",
]
