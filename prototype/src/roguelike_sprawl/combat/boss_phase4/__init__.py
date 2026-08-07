"""Boss Phase 4 Finale sub-package (ADR-0150, boss_phase4 split; ADR-0150 follow-up Cycle 5).

Four sub-modules for ADR-0110 250 LOC compliance:
- trigger: Phase 4 trigger/detection (Phase4Mechanic enum, threshold check)
- mechanics: Per-boss scripted mechanics (5 bosses × unique effect)
- intro: 3-stage text overlay on boss encounter
- taunts: Death taunts on player death by boss

Original single-file module was 448 LOC (179% of 250 ceiling).
mechanics.py was 266 LOC (6% over) after Cycle 4 — split into
trigger.py (88 LOC) + mechanics.py (~228 LOC) in Cycle 5 for strict
ADR-0110 compliance.

Pillar 정합 (ADR-0149 §Consequences.7):
- P1 (The Run): 15% HP trigger, 1회 (one-shot)
- P2 (The Matrix): 깁슨 어휘
- P3 (The Flatline): death taunts 가 Pillar 3 weight 강화
- P4 (The Build): Phase 4 mechanic 보상 = ADR-0147 salvage 통합
- P5 (The Style): 5 unique 깁슨 어휘
"""

from __future__ import annotations

from .intro import (
    BOSS_INTRO,
    BossIntroEnhancement,
    apply_boss_intro_enhancement,
    get_boss_intro,
    normalize_boss_id,
)
from .mechanics import (
    CONSTRUCT_MERGE_ATTACK_BONUS,
    CONSTRUCT_MERGE_DURATION_MS,
    CONSTRUCT_MERGE_HEAL_PCT,
    FAMILY_VOTE_COMPANION_BONUS,
    FAMILY_VOTE_DAMAGE,
    GLITCH_BURST_DURATION_MS,
    GLITCH_BURST_STATUS_COUNT,
    GROUND_SLAM_SHAKE_DURATION_MS,
    GROUND_SLAM_SHAKE_INTENSITY,
    GROUND_SLAM_STUN_MS,
    PERSONALITY_DRIFT_DURATION_MS,
    PERSONALITY_DRIFT_PCT,
    apply_construct_merge,
    apply_family_vote,
    apply_glitch_burst,
    apply_ground_slam,
    apply_personality_drift,
    apply_phase4_mechanic,
)
from .taunts import (
    DEATH_TAUNTS,
    apply_death_taunt,
    pick_death_taunt,
)
from .trigger import (
    PHASE4_HP_THRESHOLD,
    Phase4Mechanic,
    should_trigger_phase4,
    trigger_phase4,
)

__all__ = [
    "BOSS_INTRO",
    "BossIntroEnhancement",
    "CONSTRUCT_MERGE_ATTACK_BONUS",
    "CONSTRUCT_MERGE_DURATION_MS",
    "CONSTRUCT_MERGE_HEAL_PCT",
    "DEATH_TAUNTS",
    "FAMILY_VOTE_COMPANION_BONUS",
    "FAMILY_VOTE_DAMAGE",
    "GLITCH_BURST_DURATION_MS",
    "GLITCH_BURST_STATUS_COUNT",
    "GROUND_SLAM_SHAKE_DURATION_MS",
    "GROUND_SLAM_SHAKE_INTENSITY",
    "GROUND_SLAM_STUN_MS",
    "PERSONALITY_DRIFT_DURATION_MS",
    "PERSONALITY_DRIFT_PCT",
    "PHASE4_HP_THRESHOLD",
    "Phase4Mechanic",
    "apply_boss_intro_enhancement",
    "apply_construct_merge",
    "apply_death_taunt",
    "apply_family_vote",
    "apply_glitch_burst",
    "apply_ground_slam",
    "apply_phase4_mechanic",
    "apply_personality_drift",
    "get_boss_intro",
    "normalize_boss_id",
    "pick_death_taunt",
    "should_trigger_phase4",
    "trigger_phase4",
]
