"""Companion Skills sub-module (ADR-0150, depth split).

Dixie Flatline companion skills:
- `[[decompile]]` (1 AP): target attack -1 (3s)
- `[[icebreaker_overdrive]]` (3 AP): target 50 damage + damage_up 25% (5s)

Pillar 정합 (ADR-0148 §Consequences.7):
- P4 (The Build): in-run only (death = loss)
- P5 (The Style): 깁슨 "construct echo" 어휘
"""

from __future__ import annotations

import random
from enum import StrEnum
from typing import Any

from ..state_models import CombatState
from ...combat.palette import DEBUFF_COLOR, WARM


class CompanionSkillId(StrEnum):
    """Companion (Dixie) skill identifier (ADR-0148)."""

    DECOMPILE = "decompile"
    ICEBREAKER_OVERDRIVE = "icebreaker_overdrive"


# Companion skills (Dixie).
DIXIE_DECOMPILE_AP: int = 1
DIXIE_DECOMPILE_DURATION_MS: int = 3_000
DIXIE_DECOMPILE_ATTACK_REDUCTION: int = 1
DIXIE_ICEBREAKER_AP: int = 3
DIXIE_ICEBREAKER_DAMAGE: int = 50
DIXIE_ICEBREAKER_DURATION_MS: int = 5_000
DIXIE_ICEBREAKER_DAMAGE_UP_PCT: int = 25


def dixie_use_skill(
    state: CombatState,
    app_state: Any,
    skill_id: CompanionSkillId,
    rng: random.Random,
) -> bool:
    """Dixie uses a skill (decompile or icebreaker_overdrive).

    Returns True if the skill was used. Requires:
    - ``app_state.construct_companion_active == True``
    - target is alive
    - sufficient AP (caller should manage Dixie's AP pool if applicable)

    Pillar 4 (The Build): in-run only (death = loss).
    """
    if not getattr(app_state, "construct_companion_active", False):
        state.push(">>> Dixie is silent (companion mode off)")
        return False

    target = state.target
    if target is None or target.hp <= 0:
        return False

    from ..state import _apply_damage, _record_event
    from ..state_models import StatusEffect

    if skill_id is CompanionSkillId.DECOMPILE:
        target.statuses.append(
            StatusEffect(
                effect_id="decompiled",
                remaining_ms=DIXIE_DECOMPILE_DURATION_MS,
                attack_bonus=-DIXIE_DECOMPILE_ATTACK_REDUCTION,
            )
        )
        _record_event(state, "decompile", WARM)
        state.push(
            f">>> Dixie decompiles {target.name}: "
            f"-{DIXIE_DECOMPILE_ATTACK_REDUCTION} attack "
            f"({DIXIE_DECOMPILE_DURATION_MS // 1000}s)"
        )
        return True

    if skill_id is CompanionSkillId.ICEBREAKER_OVERDRIVE:
        applied = _apply_damage(state, target, DIXIE_ICEBREAKER_DAMAGE)
        target.statuses.append(
            StatusEffect(
                effect_id="damage_up",
                remaining_ms=DIXIE_ICEBREAKER_DURATION_MS,
            )
        )
        _record_event(state, "icebreaker", DEBUFF_COLOR)
        state.push(
            f">>> Dixie icebreaker overdrive: {applied} damage + "
            f"damage-up {DIXIE_ICEBREAKER_DAMAGE_UP_PCT}% "
            f"({DIXIE_ICEBREAKER_DURATION_MS // 1000}s)"
        )
        return True

    return False


def dixie_choose_skill(
    state: CombatState,
    app_state: Any,
    rng: random.Random,
) -> CompanionSkillId | None:
    """Auto-pick a companion skill to use (called from tick_dixie_ally).

    Strategy: alternate between decompile (cheap, sustain) and icebreaker
    (expensive, burst). Uses decompile if target attack is high,
    icebreaker if target HP is high.
    """
    if not getattr(app_state, "construct_companion_active", False):
        return None
    target = state.target
    if target is None or target.hp <= 0:
        return None
    if target.hp >= 80:
        return CompanionSkillId.ICEBREAKER_OVERDRIVE
    if any(s.effect_id == "decompiled" for s in target.statuses):
        return None  # already decompiled
    if rng.random() < 0.6:
        return CompanionSkillId.DECOMPILE
    return None


__all__ = [
    "CompanionSkillId",
    "DIXIE_DECOMPILE_AP",
    "DIXIE_DECOMPILE_ATTACK_REDUCTION",
    "DIXIE_DECOMPILE_DURATION_MS",
    "DIXIE_ICEBREAKER_AP",
    "DIXIE_ICEBREAKER_DAMAGE",
    "DIXIE_ICEBREAKER_DURATION_MS",
    "DIXIE_ICEBREAKER_DAMAGE_UP_PCT",
    "dixie_choose_skill",
    "dixie_use_skill",
]
