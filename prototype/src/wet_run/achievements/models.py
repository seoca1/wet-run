"""Achievement data models.

Defines the core dataclasses and enums used by the achievement system:

- :class:`AchievementCategory`, :class:`AchievementTier` — taxonomy enums.
- :class:`Achievement` — immutable achievement definition.
- :class:`AchievementUnlock` — one-shot notification record.
- :class:`AchievementState` — player progress, notifications, derived stats.

The catalog of 28 ``ACH_*`` constants and the lookup tables live in
:mod:`wet_run.achievements.catalog` (split per ADR-0110 to keep each
module ≤ 500 LOC). Event handlers and display helpers live in
:mod:`wet_run.achievements.registry`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

# ----------------------------------------------------------------------------
# Categories and tiers
# ----------------------------------------------------------------------------


class AchievementCategory(StrEnum):
    """Categories of achievements."""

    COMBAT = "combat"
    EXPLORATION = "exploration"
    STORY = "story"
    MASTERY = "mastery"
    HIDDEN = "hidden"


class AchievementTier(StrEnum):
    """Difficulty/value tiers."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


# ----------------------------------------------------------------------------
# Achievement definition
# ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Achievement:
    """A single achievement definition.

    Attributes:
        id: Unique identifier (e.g. "first_blood")
        name: English display name
        name_ko: Korean display name
        description: How to unlock
        category: Category enum
        tier: Tier enum
        icon: ASCII icon
        reward_credits: Credits awarded on unlock
        hidden: If True, not shown in list until unlocked
    """

    id: str
    name: str
    name_ko: str
    description: str
    category: AchievementCategory
    tier: AchievementTier
    icon: str
    reward_credits: int = 0
    hidden: bool = False


# ----------------------------------------------------------------------------
# State
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class AchievementUnlock:
    """Notification when an achievement is unlocked."""

    achievement: Achievement
    timestamp_ms: int


@dataclass(slots=True)
class AchievementState:
    """Player's achievement progress and unlocks.

    Tracks:
    - unlocked_ids: Set of achievement IDs unlocked
    - progress: Map of achievement_id -> progress value
    - notification_queue: Pending unlock notifications
    - total_credits_earned: Cumulative credits from achievements
    """

    unlocked_ids: set[str] = field(default_factory=set)
    progress: dict[str, int] = field(default_factory=dict)
    notification_queue: list[AchievementUnlock] = field(default_factory=list)
    total_credits_earned: int = 0
    last_unlocked: Achievement | None = None

    def unlock(self, ach_id: str, current_ms: int = 0) -> Achievement | None:
        """Unlock an achievement. Returns the achievement if newly unlocked."""
        # Local import breaks the catalog <-> models circular dependency:
        # `models.AchievementState` references `catalog.get_achievement`,
        # while `catalog` imports `models.Achievement` for typing.
        from wet_run.achievements.catalog import get_achievement

        if ach_id in self.unlocked_ids:
            return None  # Already unlocked

        ach = get_achievement(ach_id)
        if ach is None:
            return None

        self.unlocked_ids.add(ach_id)
        self.total_credits_earned += ach.reward_credits
        self.last_unlocked = ach
        self.notification_queue.append(AchievementUnlock(achievement=ach, timestamp_ms=current_ms))
        return ach

    def set_progress(self, ach_id: str, value: int) -> None:
        """Set progress for a progressive achievement (e.g. PPL_30 at value 30)."""
        self.progress[ach_id] = value

    def is_unlocked(self, ach_id: str) -> bool:
        """Return True if the achievement has been unlocked by the player."""
        return ach_id in self.unlocked_ids

    def get_progress(self, ach_id: str) -> int:
        """Return the current progress value for a progressive achievement (0 if none)."""
        return self.progress.get(ach_id, 0)

    def consume_notification(self) -> Achievement | None:
        """Pop the next pending notification, if any."""
        if self.notification_queue:
            notif = self.notification_queue.pop(0)
            return notif.achievement
        return None

    def unlock_progress_achievement(
        self,
        ach_id: str,
        current_value: int,
        threshold: int,
        current_ms: int = 0,
    ) -> Achievement | None:
        """Unlock a progress-based achievement if threshold reached."""
        self.set_progress(ach_id, current_value)
        if current_value >= threshold:
            return self.unlock(ach_id, current_ms)
        return None

    def get_completion_stats(self) -> dict[str, int]:
        """Get completion stats by category."""
        from wet_run.achievements.catalog import ALL_ACHIEVEMENTS

        stats: dict[str, int] = {c.value: 0 for c in AchievementCategory}
        for ach in ALL_ACHIEVEMENTS:
            if ach.id in self.unlocked_ids:
                stats[ach.category.value] += 1
        return stats

    def get_total_unlocked(self) -> int:
        """Return the count of currently unlocked achievements."""
        return len(self.unlocked_ids)

    def get_total_available(self) -> int:
        """Return the total number of achievements that exist in the catalog."""
        from wet_run.achievements.catalog import ALL_ACHIEVEMENTS

        return len(ALL_ACHIEVEMENTS)

    def get_completion_pct(self) -> float:
        """Return the completion percentage (0.0-100.0) for unlocked vs available."""
        total = self.get_total_available()
        if total == 0:
            return 0.0
        return 100.0 * self.get_total_unlocked() / total


__all__ = [
    "Achievement",
    "AchievementCategory",
    "AchievementState",
    "AchievementTier",
    "AchievementUnlock",
]
