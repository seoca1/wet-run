"""Combat depth expansion sub-package (ADR-0150, depth split).

Four sub-features split into separate modules for ADR-0110 250 LOC compliance:
- counter: Counter Window (200ms reactive gameplay)
- defense: Defense Stackable + Duration (Wisp/Shield/Wardrone)
- companion: Companion Skills (Dixie decompile/icebreaker_overdrive)
- aggression: ICE Aggression Tiers (PASSIVE/STANDARD/AGGRESSIVE/BOSS)

Original single-file module was 311 LOC (124% of 250 ceiling).
Split into 4 sub-modules + this __init__.py for backward-compat re-exports.

Pillar 정합 (ADR-0148 §Consequences.7):
- P1 (The Run): 점진적 (alarm-aware salvage ADR-0147 가 보완)
- P2 (The Matrix): ICE signature / construct echo 어휘
- P3 (The Flatline): HEAL 변화 없음, counter 가 *기술적* 깊이
- P4 (The Build): Companion skill in-run only (death = loss)
- P5 (The Style): 깁슨 어휘 ("counter-trace", "ICE signature", "construct echo")
"""

from __future__ import annotations

from .aggression import (
    AGGRESSION_PROBABILITY,
    AggressionLevel,
    enemy_should_use_skill,
)
from .companion import (
    DIXIE_DECOMPILE_AP,
    DIXIE_DECOMPILE_ATTACK_REDUCTION,
    DIXIE_DECOMPILE_DURATION_MS,
    DIXIE_ICEBREAKER_AP,
    DIXIE_ICEBREAKER_DAMAGE,
    DIXIE_ICEBREAKER_DAMAGE_UP_PCT,
    DIXIE_ICEBREAKER_DURATION_MS,
    CompanionSkillId,
    dixie_choose_skill,
    dixie_use_skill,
)
from .counter import (
    COUNTER_DAMAGE_MULTIPLIER,
    COUNTER_STUN_MS,
    COUNTER_WINDOW_MS,
    apply_counter_attack,
    counter_window_active_and_expired,
    is_counter_window_open,
    open_counter_window,
)
from .defense import (
    SHIELD_BARRIER,
    WARDRONE_COUNTER_DMG,
    WARDRONE_COUNTER_INTERVAL_MS,
    WARDRONE_DURATION_MS,
    WARDRONE_SHIELD,
    WISP_DURATION_MS,
    WISP_SHIELD,
    DefenseProgram,
    apply_shield_barrier,
    apply_wardrone,
    apply_wisp,
    tick_defense_durations,
    tick_defense_expiry,
)

__all__ = [
    "AGGRESSION_PROBABILITY",
    "AggressionLevel",
    "COUNTER_DAMAGE_MULTIPLIER",
    "COUNTER_STUN_MS",
    "COUNTER_WINDOW_MS",
    "CompanionSkillId",
    "DIXIE_DECOMPILE_AP",
    "DIXIE_DECOMPILE_ATTACK_REDUCTION",
    "DIXIE_DECOMPILE_DURATION_MS",
    "DIXIE_ICEBREAKER_AP",
    "DIXIE_ICEBREAKER_DAMAGE",
    "DIXIE_ICEBREAKER_DURATION_MS",
    "DIXIE_ICEBREAKER_DAMAGE_UP_PCT",
    "DefenseProgram",
    "SHIELD_BARRIER",
    "WARDRONE_COUNTER_DMG",
    "WARDRONE_COUNTER_INTERVAL_MS",
    "WARDRONE_DURATION_MS",
    "WARDRONE_SHIELD",
    "WISP_DURATION_MS",
    "WISP_SHIELD",
    "apply_counter_attack",
    "apply_shield_barrier",
    "apply_wardrone",
    "apply_wisp",
    "counter_window_active_and_expired",
    "dixie_choose_skill",
    "dixie_use_skill",
    "enemy_should_use_skill",
    "is_counter_window_open",
    "open_counter_window",
    "tick_defense_durations",
    "tick_defense_expiry",
]
