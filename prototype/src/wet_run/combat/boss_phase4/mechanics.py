"""Boss Phase 4 apply mechanics sub-module (ADR-0150 follow-up, Cycle 5).

Per-boss scripted mechanics triggered at HP <= 15% (one-shot):
- Wintermute: personality_drift (player attack_bonus 50% reduction, 3s)
- TA_PRIME: family_vote (AoE damage 20, +10 with companion)
- Neuromancer: construct_merge (heal 20% max_hp + attack +2, 3s)
- Goliath: ground_slam (player stun 1s + screen shake)
- Black_ICE: glitch_burst (3 random status effects, 3s each)

Trigger/detection lives in :mod:`trigger` (Phase4Mechanic enum,
``should_trigger_phase4``, ``trigger_phase4``). This module contains
only the per-boss apply effects and the ``apply_phase4_mechanic``
dispatcher.

Pillar 정합 (ADR-0149 §Consequences.7):
- P1 (The Run): 15% HP trigger, 1회 (one-shot)
- P5 (The Style): 5 unique 깁슨 어휘
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..state import CombatState

from .trigger import Phase4Mechanic, trigger_phase4

# Per-boss mechanic parameters.
PERSONALITY_DRIFT_PCT: int = 50
PERSONALITY_DRIFT_DURATION_MS: int = 3_000
FAMILY_VOTE_DAMAGE: int = 20
FAMILY_VOTE_COMPANION_BONUS: int = 10
CONSTRUCT_MERGE_HEAL_PCT: float = 0.20
CONSTRUCT_MERGE_ATTACK_BONUS: int = 2
CONSTRUCT_MERGE_DURATION_MS: int = 3_000
GROUND_SLAM_STUN_MS: int = 1_000
GROUND_SLAM_SHAKE_INTENSITY: float = 3.0
GROUND_SLAM_SHAKE_DURATION_MS: int = 400
GLITCH_BURST_STATUS_COUNT: int = 3
GLITCH_BURST_DURATION_MS: int = 3_000


def apply_personality_drift(state: CombatState) -> None:
    """Wintermute Phase 4: reduce player attack power by 50% for 3s.

    Pillar 5 (The Style): 깁슨 "personality drift" — construct 인격의 표류.
    """
    from ..state_models import StatusEffect

    player = state.player
    reduction = -(player.auto_attack_damage * PERSONALITY_DRIFT_PCT // 100)
    player.statuses.append(
        StatusEffect(
            effect_id="personality_drift",
            remaining_ms=PERSONALITY_DRIFT_DURATION_MS,
            attack_bonus=reduction,
        )
    )
    state.push(
        f">>> Wintermute: personality drift applied — your patterns are mine (-{PERSONALITY_DRIFT_PCT}% attack, 3s)."
    )


def apply_family_vote(state: CombatState, has_companion: bool = False) -> int:
    """T-A Prime Phase 4: AoE damage 20 (+10 with companion).

    Returns the damage dealt. Pillar 5: 깁슨 "family consensus".
    """
    from ..state import _record_event

    damage = FAMILY_VOTE_DAMAGE
    if has_companion:
        damage += FAMILY_VOTE_COMPANION_BONUS
    state.player.hp = max(0, state.player.hp - damage)
    _record_event(state, "family_vote", (255, 200, 200))
    suffix = " (+companion)" if has_companion else ""
    state.push(f">>> T-A Prime: family consensus — {damage} damage{suffix}.")
    return damage


def apply_construct_merge(state: CombatState) -> int:
    """Neuromancer Phase 4: heal 20% max_hp + attack +2 for 3s.

    Pillar 5: 깁슨 "construct merger" — Neuromancer/Wintermute 합체.
    Returns the heal amount.
    """
    from ..state_models import StatusEffect

    boss = state.target
    if boss is None:
        return 0
    heal = int(boss.max_hp * CONSTRUCT_MERGE_HEAL_PCT)
    boss.hp = min(boss.max_hp, boss.hp + heal)
    boss.statuses.append(
        StatusEffect(
            effect_id="merged",
            remaining_ms=CONSTRUCT_MERGE_DURATION_MS,
            attack_bonus=CONSTRUCT_MERGE_ATTACK_BONUS,
        )
    )
    state.push(
        f">>> Neuromancer: construct merge complete — {heal} HP restored, attack +{CONSTRUCT_MERGE_ATTACK_BONUS} (3s)."
    )
    return heal


def apply_ground_slam(state: CombatState) -> None:
    """Goliath Prime Phase 4: stun player 1s + screen shake.

    Pillar 5: 깁슨 "architecture response" — heavy protocol.
    """
    from ..state_models import StatusEffect

    state.player.statuses.append(
        StatusEffect(
            effect_id="stun",
            remaining_ms=GROUND_SLAM_STUN_MS,
            is_stunned=True,
        )
    )
    effects = getattr(state, "combat_effects", None)
    if effects is not None and hasattr(effects, "shake"):
        effects.shake.trigger(
            intensity=GROUND_SLAM_SHAKE_INTENSITY,
            duration_ms=GROUND_SLAM_SHAKE_DURATION_MS,
        )
    state.push(">>> Goliath Prime: ground slam — stunned 1s, screen shake.")


def apply_glitch_burst(state: CombatState, rng: random.Random) -> tuple[str, ...]:
    """Black ICE Lord Phase 4: 3 random status effects on player.

    Pillar 5: 깁슨 "glitch" — corrupted construct 의 무작위 status 폭주.
    Returns the applied effect_id tuple.
    """
    from ..state_models import StatusEffect

    pool: tuple[tuple[str, int], ...] = (
        ("weakened", -2),
        ("slowed", 0),
        ("damaged_up", 0),
        ("attack_down", -1),
        ("defense_down", 0),
    )
    selected = rng.sample(pool, k=GLITCH_BURST_STATUS_COUNT)
    applied: list[str] = []
    for effect_id, attack_bonus in selected:
        state.player.statuses.append(
            StatusEffect(
                effect_id=f"glitch_{effect_id}",
                remaining_ms=GLITCH_BURST_DURATION_MS,
                attack_bonus=attack_bonus,
            )
        )
        applied.append(effect_id)
    state.push(f">>> Black ICE Lord: glitch burst — {', '.join(applied)} (3s each).")
    return tuple(applied)


def apply_phase4_mechanic(
    state: CombatState,
    app_state: Any,
    boss_id: str,
    rng: random.Random | None = None,
) -> bool:
    """Dispatch the Phase 4 mechanic for the given boss.

    Returns True if a mechanic was applied. One-shot — guarded by
    ``app_state.phase4_triggered`` via :func:`trigger_phase4`.
    """
    if rng is None:
        rng = random.Random()
    mechanic = trigger_phase4(state, app_state, boss_id)
    if mechanic is None:
        return False
    if mechanic is Phase4Mechanic.PERSONALITY_DRIFT:
        apply_personality_drift(state)
    elif mechanic is Phase4Mechanic.FAMILY_VOTE:
        companion = getattr(app_state, "construct_companion_active", False)
        apply_family_vote(state, has_companion=companion)
    elif mechanic is Phase4Mechanic.CONSTRUCT_MERGE:
        apply_construct_merge(state)
    elif mechanic is Phase4Mechanic.GROUND_SLAM:
        apply_ground_slam(state)
    elif mechanic is Phase4Mechanic.GLITCH_BURST:
        apply_glitch_burst(state, rng)
    return True


__all__ = [
    "CONSTRUCT_MERGE_ATTACK_BONUS",
    "CONSTRUCT_MERGE_DURATION_MS",
    "CONSTRUCT_MERGE_HEAL_PCT",
    "FAMILY_VOTE_COMPANION_BONUS",
    "FAMILY_VOTE_DAMAGE",
    "GLITCH_BURST_DURATION_MS",
    "GLITCH_BURST_STATUS_COUNT",
    "GROUND_SLAM_SHAKE_DURATION_MS",
    "GROUND_SLAM_SHAKE_INTENSITY",
    "GROUND_SLAM_STUN_MS",
    "PERSONALITY_DRIFT_DURATION_MS",
    "PERSONALITY_DRIFT_PCT",
    "Phase4Mechanic",
    "apply_construct_merge",
    "apply_family_vote",
    "apply_glitch_burst",
    "apply_ground_slam",
    "apply_phase4_mechanic",
    "apply_personality_drift",
]
