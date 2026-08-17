"""Story system — narrative content (aftermath, reactions, rewards, arcs).

Phase 6+ content expansion:
  - 12 aftermath events (vs original 5)
  - 25 NPC reactions across 7 characters (vs original 10)
  - 9 EventTrigger types covering all major story beats
  - StoryReward system for credit/material/rep/achievement grants
"""

from .rewards import (  # noqa: F401
    RewardKind,
    StoryReward,
    apply_event_rewards,
    load_rewards_from,
)

__all__ = [
    "RewardKind",
    "StoryReward",
    "apply_event_rewards",
    "load_rewards_from",
]
