"""Multi-enemy encounter support (ADR-0152, Cycle 8).

Functions for 1v2/1v3 encounters:
- cycle_target: Tab key cycles target_index through alive enemies
- all_alive_enemies: list of enemies with hp > 0
- encounter_count_for_grade: 1/2/3 mapping (Grade 1-2: 1, Grade 3-4: 2, Grade 5-6: 3)

Pillar 정합 (ADR-0152 §Consequences.8):
- P1 (The Run): 1vN alarm accumulate → alarm-aware salvage + intel alarm_reducer 보완
- P3 (The Flatline): HEAL 15% + 1-of-4 choice → Pillar 3 weight 보존 (1vN 에서 trivial 방지)
- P5 (The Style): 깁슨 어휘 + multi-enemy 묘사 ("swarm", "pack", "encircle")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import Combatant, CombatState


# Grade-based encounter count mapping (ADR-0152).
# Grade 1-2: 1 enemy (novice, tutorial)
# Grade 3-4: 2 enemies (intermediate, pack)
# Grade 5-6: 3 enemies (veteran, swarm)
ENCOUNTER_COUNT_BY_GRADE: dict[int, int] = {
    1: 1,
    2: 1,
    3: 2,
    4: 2,
    5: 3,
    6: 3,
}


# ADR-0154: PPL growth targets (per design/balance/ppl_zdr_balance.md).
# These are *target* growth ratios for the loadout-based PPL formula.
# Grade 1→2: 2.00x, 2→3: 1.50x, 3→4: 1.67x, 4→5: 1.62x, 5→6: 1.20x ⚠
# Known issue: Grade 5→6 is stagnant (NG+ balance, ADR-0130 §잔존 이슈).
# Actual rebalance deferred — PPL formula in this module is loadout-based,
# not grade-based. This dict documents the *target* ratios for reference.
PPL_GROWTH_TARGETS: dict[str, float] = {
    "1->2": 2.00,
    "2->3": 1.50,
    "3->4": 1.67,
    "4->5": 1.62,
    "5->6": 1.20,  # NG+ balance issue (ADR-0130)
}


def encounter_count_for_grade(grade: int) -> int:
    """Return the number of enemies in an encounter for the given player grade.

    Grade 1-2: 1 enemy (novice, tutorial)
    Grade 3-4: 2 enemies (intermediate, pack)
    Grade 5-6: 3 enemies (veteran, swarm)
    """
    return ENCOUNTER_COUNT_BY_GRADE.get(max(1, min(6, grade)), 1)


def all_alive_enemies(state: CombatState) -> list[Combatant]:
    """Return a list of all enemies with hp > 0.

    Returns an empty list if state.enemies is empty or all enemies are dead.
    Used by step_combat to determine which enemies attack the player.
    """
    return [e for e in state.enemies if e.hp > 0]


def cycle_target(state: CombatState) -> Combatant | None:
    """Cycle target_index to the next alive enemy (Tab key handler).

    Returns the new target Combatant, or None if no alive enemies exist.
    Skips dead enemies (player can still tab through them, but they're
    skipped in the visual indicator).

    Pillar 1: lets the player pick a focus target in 1vN encounters
    so they can prioritize high-threat ICE first.
    """
    if not state.enemies:
        return None
    alive = all_alive_enemies(state)
    if not alive:
        return None
    # Find current target's index in alive list
    current = state.target
    if current is None or current not in alive:
        # Default to first alive
        new_idx = 0
    else:
        current_alive_idx = alive.index(current)
        new_idx = (current_alive_idx + 1) % len(alive)
    new_target = alive[new_idx]
    # Find this alive enemy in the full enemies tuple
    state.target_index = state.enemies.index(new_target)
    return new_target


def auto_attack_all_alive(state: CombatState, base_dmg: int) -> list[tuple[Combatant, int]]:
    """Apply base_dmg to all alive enemies (used by step_combat auto-attack).

    Returns a list of (enemy, damage_applied) tuples for test verification.
    Caller is responsible for shield, crit, and combo logic.
    """
    from .state import _apply_damage

    results: list[tuple[Combatant, int]] = []
    for enemy in all_alive_enemies(state):
        applied = _apply_damage(state, enemy, base_dmg)
        results.append((enemy, applied))
    return results


__all__ = [
    "ENCOUNTER_COUNT_BY_GRADE",
    "all_alive_enemies",
    "auto_attack_all_alive",
    "cycle_target",
    "encounter_count_for_grade",
]
