"""Achievement system — public package entrypoint.

Provides 28 achievements across 5 categories and 4 tiers. Each
achievement has an unlock condition, reward, and visible name.

Categories:
  - COMBAT (전투, 7):     First Blood, Sharpshooter, Combo Master, ...
  - EXPLORATION (탐험, 6): First Jack-In, World Walker, ...
  - STORY (스토리, 5):    Character prologues, short stories, endings
  - MASTERY (정통, 6):    PPL milestones, max combo, flawless
  - HIDDEN (히든, 4):     Secret discoveries

Tiers:
  - BRONZE: Basic feats
  - SILVER: Moderate challenge
  - GOLD: Significant accomplishment
  - PLATINUM: Legendary

This sub-package splits the original monolithic ``achievements.py`` (943 LOC)
into three focused modules, each ≤ 500 LOC per ADR-0110:

- :mod:`wet_run.achievements.models` — enums, ``Achievement`` dataclass,
  ``AchievementState``, ``AchievementUnlock`` (data shapes).
- :mod:`wet_run.achievements.catalog` — the 28 ``ACH_*`` constants,
  ``ALL_ACHIEVEMENTS`` / ``ACHIEVEMENT_BY_ID`` lookups, and
  ``get_achievement`` / ``get_achievements_by_category`` accessors.
- :mod:`wet_run.achievements.registry` — event handlers (``check_*_event``,
  ``check_*_master``, ``check_true_hacker``) and display helpers
  (``render_achievement``, ``get_achievements_summary``).
"""

from __future__ import annotations

from wet_run.achievements.catalog import (
    ACH_BOSS_SLAYER,
    ACH_CASE_JOURNEY,
    ACH_CENTURION,
    ACH_COMBO_MASTER,
    ACH_COMBO_QUANT,
    ACH_DATA_EXTRACTOR,
    ACH_FIRST_BLOOD,
    ACH_FIRST_JACKIN,
    ACH_FIVE_TALES,
    ACH_FLAWLESS,
    ACH_GHOST_PROTOCOL,
    ACH_GOLIATH_SLAYER,
    ACH_JACKOUT_SURVIVOR,
    ACH_KAS_RISE,
    ACH_MATRIX_EXPLORER,
    ACH_MATRIX_MASTER,
    ACH_PHOENIX,
    ACH_PPL_10,
    ACH_PPL_20,
    ACH_PPL_30,
    ACH_SERVER_DOMINATION,
    ACH_SHARPSHOOTER,
    ACH_SIL_AWAKENING,
    ACH_THE_TRUTH,
    ACH_TRUE_HACKER,
    ACH_UNDEFEATED,
    ACH_VOID_WALKER,
    ACH_WORLD_WALKER,
    ACHIEVEMENT_BY_ID,
    ALL_ACHIEVEMENTS,
    get_achievement,
    get_achievements_by_category,
)
from wet_run.achievements.models import (
    Achievement,
    AchievementCategory,
    AchievementState,
    AchievementTier,
    AchievementUnlock,
)
from wet_run.achievements.registry import (
    check_combat_event,
    check_exploration_event,
    check_mastery_event,
    check_matrix_master,
    check_story_event,
    check_true_hacker,
    get_achievements_summary,
    render_achievement,
)

__all__ = [
    "ACHIEVEMENT_BY_ID",
    "ACH_FIRST_BLOOD",
    "ACH_SHARPSHOOTER",
    "ACH_COMBO_MASTER",
    "ACH_UNDEFEATED",
    "ACH_BOSS_SLAYER",
    "ACH_GOLIATH_SLAYER",
    "ACH_CENTURION",
    "ACH_FIRST_JACKIN",
    "ACH_WORLD_WALKER",
    "ACH_SERVER_DOMINATION",
    "ACH_DATA_EXTRACTOR",
    "ACH_JACKOUT_SURVIVOR",
    "ACH_MATRIX_EXPLORER",
    "ACH_CASE_JOURNEY",
    "ACH_SIL_AWAKENING",
    "ACH_KAS_RISE",
    "ACH_FIVE_TALES",
    "ACH_THE_TRUTH",
    "ACH_PPL_10",
    "ACH_PPL_20",
    "ACH_PPL_30",
    "ACH_MATRIX_MASTER",
    "ACH_COMBO_QUANT",
    "ACH_FLAWLESS",
    "ACH_GHOST_PROTOCOL",
    "ACH_PHOENIX",
    "ACH_VOID_WALKER",
    "ACH_TRUE_HACKER",
    "ALL_ACHIEVEMENTS",
    "Achievement",
    "AchievementCategory",
    "AchievementState",
    "AchievementTier",
    "AchievementUnlock",
    "check_combat_event",
    "check_exploration_event",
    "check_mastery_event",
    "check_story_event",
    "check_matrix_master",
    "check_true_hacker",
    "get_achievement",
    "get_achievements_by_category",
    "get_achievements_summary",
    "render_achievement",
]
