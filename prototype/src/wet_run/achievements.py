"""Achievement system for tracking player accomplishments.

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
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


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
# COMBAT achievements (7)
# ----------------------------------------------------------------------------


ACH_FIRST_BLOOD = Achievement(
    id="first_blood",
    name="First Blood",
    name_ko="첫 피",
    description="첫 번째 ICE를 처치하세요.",
    category=AchievementCategory.COMBAT,
    tier=AchievementTier.BRONZE,
    icon="🗡",
    reward_credits=50,
)

ACH_SHARPSHOOTER = Achievement(
    id="sharpshooter",
    name="Sharpshooter",
    name_ko="정밀 사격",
    description="한 전투에서 10회의 크리티컬 히트를 달성하세요.",
    category=AchievementCategory.COMBAT,
    tier=AchievementTier.SILVER,
    icon="✦",
    reward_credits=200,
)

ACH_COMBO_MASTER = Achievement(
    id="combo_master",
    name="Combo Master",
    name_ko="콤보 마스터",
    description="ANNIHILATION 단계의 콤보를 달성하세요.",
    category=AchievementCategory.COMBAT,
    tier=AchievementTier.GOLD,
    icon="✦✦✦",
    reward_credits=500,
)

ACH_UNDEFEATED = Achievement(
    id="undefeated",
    name="Undefeated",
    name_ko="무패",
    description="10번의 전투에서 단 한 번도 쓰러지지 않고 승리하세요.",
    category=AchievementCategory.COMBAT,
    tier=AchievementTier.SILVER,
    icon="✧",
    reward_credits=300,
)

ACH_BOSS_SLAYER = Achievement(
    id="boss_slayer",
    name="Boss Slayer",
    name_ko="보스 슬레이어",
    description="첫 BOSS ICE를 처치하세요.",
    category=AchievementCategory.COMBAT,
    tier=AchievementTier.GOLD,
    icon="☠",
    reward_credits=1000,
)

ACH_GOLIATH_SLAYER = Achievement(
    id="goliath_slayer",
    name="Goliath Conqueror",
    name_ko="골리앗 정복자",
    description="GOLIATH PRIME를 처치하세요.",
    category=AchievementCategory.COMBAT,
    tier=AchievementTier.PLATINUM,
    icon="★",
    reward_credits=2000,
)

ACH_CENTURION = Achievement(
    id="centurion",
    name="Centurion",
    name_ko="100 킬",
    description="누적 100 ICE 처치.",
    category=AchievementCategory.COMBAT,
    tier=AchievementTier.GOLD,
    icon="✦",
    reward_credits=1500,
)

# ----------------------------------------------------------------------------
# EXPLORATION achievements (6)
# ----------------------------------------------------------------------------


ACH_FIRST_JACKIN = Achievement(
    id="first_jackin",
    name="First Jack-In",
    name_ko="첫 잭인",
    description="매트릭스에 처음 진입하세요.",
    category=AchievementCategory.EXPLORATION,
    tier=AchievementTier.BRONZE,
    icon="◎",
    reward_credits=50,
)

ACH_WORLD_WALKER = Achievement(
    id="world_walker",
    name="World Walker",
    name_ko="월드 워커",
    description="두 월드(Chiba, Night City) 모두 방문.",
    category=AchievementCategory.EXPLORATION,
    tier=AchievementTier.SILVER,
    icon="⊕",
    reward_credits=300,
)

ACH_SERVER_DOMINATION = Achievement(
    id="server_domination",
    name="Server Domination",
    name_ko="서버 점령",
    description="모든 6개 서버 방문.",
    category=AchievementCategory.EXPLORATION,
    tier=AchievementTier.GOLD,
    icon="⊞",
    reward_credits=1000,
)

ACH_DATA_EXTRACTOR = Achievement(
    id="data_extractor",
    name="Data Extractor",
    name_ko="데이터 추출",
    description="10개의 데이터 노드 추출.",
    category=AchievementCategory.EXPLORATION,
    tier=AchievementTier.SILVER,
    icon="▤",
    reward_credits=400,
)

ACH_JACKOUT_SURVIVOR = Achievement(
    id="jackout_survivor",
    name="Jack-Out Survivor",
    name_ko="잭아웃 서바이버",
    description="10번의 잭아웃 생존.",
    category=AchievementCategory.EXPLORATION,
    tier=AchievementTier.BRONZE,
    icon="◯",
    reward_credits=200,
)

ACH_MATRIX_EXPLORER = Achievement(
    id="matrix_explorer",
    name="Matrix Explorer",
    name_ko="매트릭스 탐험가",
    description="50개 노드 방문.",
    category=AchievementCategory.EXPLORATION,
    tier=AchievementTier.GOLD,
    icon="◇",
    reward_credits=800,
)

# ----------------------------------------------------------------------------
# STORY achievements (5)
# ----------------------------------------------------------------------------


ACH_CASE_JOURNEY = Achievement(
    id="case_journey",
    name="Case's Journey",
    name_ko="케이의 여정",
    description="케이(초보자) 프롤로그 완료.",
    category=AchievementCategory.STORY,
    tier=AchievementTier.BRONZE,
    icon="◉P",
    reward_credits=100,
)

ACH_SIL_AWAKENING = Achievement(
    id="sil_awakening",
    name="Sil's Awakening",
    name_ko="실의 자각",
    description="실(베테랑) 프롤로그 완료.",
    category=AchievementCategory.STORY,
    tier=AchievementTier.SILVER,
    icon="◉V",
    reward_credits=200,
)

ACH_KAS_RISE = Achievement(
    id="kas_rise",
    name="Kas's Rise",
    name_ko="카스의 각성",
    description="카스(헤레틱) 프롤로그 완료.",
    category=AchievementCategory.STORY,
    tier=AchievementTier.GOLD,
    icon="◉H",
    reward_credits=300,
)

ACH_FIVE_TALES = Achievement(
    id="five_tales",
    name="Five Tales",
    name_ko="다섯 단편",
    description="모든 5개 단편 소설 읽기.",
    category=AchievementCategory.STORY,
    tier=AchievementTier.SILVER,
    icon="❦",
    reward_credits=500,
)

ACH_THE_TRUTH = Achievement(
    id="the_truth",
    name="The Truth",
    name_ko="진실",
    description="모든 3 엔딩 해금.",
    category=AchievementCategory.STORY,
    tier=AchievementTier.PLATINUM,
    icon="✧",
    reward_credits=3000,
)

# ----------------------------------------------------------------------------
# MASTERY achievements (6)
# ----------------------------------------------------------------------------


ACH_PPL_10 = Achievement(
    id="ppl_10",
    name="Apprentice",
    name_ko="견습생",
    description="PPL 10 도달.",
    category=AchievementCategory.MASTERY,
    tier=AchievementTier.BRONZE,
    icon="▰",
    reward_credits=100,
)

ACH_PPL_20 = Achievement(
    id="ppl_20",
    name="Adept",
    name_ko="숙련자",
    description="PPL 20 도달.",
    category=AchievementCategory.MASTERY,
    tier=AchievementTier.SILVER,
    icon="▰▰",
    reward_credits=500,
)

ACH_PPL_30 = Achievement(
    id="ppl_30",
    name="Master",
    name_ko="달인",
    description="PPL 30 도달.",
    category=AchievementCategory.MASTERY,
    tier=AchievementTier.GOLD,
    icon="▰▰▰",
    reward_credits=1500,
)

ACH_MATRIX_MASTER = Achievement(
    id="matrix_master",
    name="Matrix Master",
    name_ko="매트릭스 정통",
    description="PPL 30 + ZDR 30 전투 승리.",
    category=AchievementCategory.MASTERY,
    tier=AchievementTier.PLATINUM,
    icon="◈",
    reward_credits=5000,
)

ACH_COMBO_QUANT = Achievement(
    id="combo_quant",
    name="Combo Quant",
    name_ko="콤보 콰이언",
    description="최대 50 콤보 달성.",
    category=AchievementCategory.MASTERY,
    tier=AchievementTier.GOLD,
    icon="⚡",
    reward_credits=2000,
)

ACH_FLAWLESS = Achievement(
    id="flawless",
    name="Flawless",
    name_ko="완벽한 자",
    description="데미지 없이 50 전투 승리.",
    category=AchievementCategory.MASTERY,
    tier=AchievementTier.PLATINUM,
    icon="✧",
    reward_credits=4000,
)

# ----------------------------------------------------------------------------
# HIDDEN achievements (4)
# ----------------------------------------------------------------------------


ACH_GHOST_PROTOCOL = Achievement(
    id="ghost_protocol",
    name="Ghost Protocol",
    name_ko="고스트 프로토콜",
    description="한 번의 매트릭스 진입에서 단 한 번의 전투도 하지 않고 데이터 3개 추출.",
    category=AchievementCategory.HIDDEN,
    tier=AchievementTier.PLATINUM,
    icon="◇",
    reward_credits=3000,
    hidden=True,
)

ACH_PHOENIX = Achievement(
    id="phoenix",
    name="Phoenix",
    name_ko="불사조",
    description="사망 후 1 HP로 부활.",
    category=AchievementCategory.HIDDEN,
    tier=AchievementTier.GOLD,
    icon="✦",
    reward_credits=2000,
    hidden=True,
)

ACH_VOID_WALKER = Achievement(
    id="void_walker",
    name="Void Walker",
    name_ko="보이드 워커",
    description="BLACK ICE LORD 처치.",
    category=AchievementCategory.HIDDEN,
    tier=AchievementTier.PLATINUM,
    icon="▓",
    reward_credits=3500,
    hidden=True,
)

ACH_TRUE_HACKER = Achievement(
    id="true_hacker",
    name="True Hacker",
    name_ko="진정한 해커",
    description="모든 업적 해금.",
    category=AchievementCategory.HIDDEN,
    tier=AchievementTier.PLATINUM,
    icon="★",
    reward_credits=10000,
    hidden=True,
)

# ----------------------------------------------------------------------------
# Registry
# ----------------------------------------------------------------------------


ALL_ACHIEVEMENTS: tuple[Achievement, ...] = (
    # Combat
    ACH_FIRST_BLOOD,
    ACH_SHARPSHOOTER,
    ACH_COMBO_MASTER,
    ACH_UNDEFEATED,
    ACH_BOSS_SLAYER,
    ACH_GOLIATH_SLAYER,
    ACH_CENTURION,
    # Exploration
    ACH_FIRST_JACKIN,
    ACH_WORLD_WALKER,
    ACH_SERVER_DOMINATION,
    ACH_DATA_EXTRACTOR,
    ACH_JACKOUT_SURVIVOR,
    ACH_MATRIX_EXPLORER,
    # Story
    ACH_CASE_JOURNEY,
    ACH_SIL_AWAKENING,
    ACH_KAS_RISE,
    ACH_FIVE_TALES,
    ACH_THE_TRUTH,
    # Mastery
    ACH_PPL_10,
    ACH_PPL_20,
    ACH_PPL_30,
    ACH_MATRIX_MASTER,
    ACH_COMBO_QUANT,
    ACH_FLAWLESS,
    # Hidden
    ACH_GHOST_PROTOCOL,
    ACH_PHOENIX,
    ACH_VOID_WALKER,
    ACH_TRUE_HACKER,
)

ACHIEVEMENT_BY_ID: dict[str, Achievement] = {a.id: a for a in ALL_ACHIEVEMENTS}


def get_achievement(ach_id: str) -> Achievement | None:
    """Get an achievement by ID."""
    return ACHIEVEMENT_BY_ID.get(ach_id)


def get_achievements_by_category(
    category: AchievementCategory,
    include_hidden: bool = False,
) -> list[Achievement]:
    """Get all achievements in a category."""
    return [
        a for a in ALL_ACHIEVEMENTS if a.category == category and (include_hidden or not a.hidden)
    ]


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
        return len(ALL_ACHIEVEMENTS)

    def get_completion_pct(self) -> float:
        """Return the completion percentage (0.0-100.0) for unlocked vs available."""
        total = self.get_total_available()
        if total == 0:
            return 0.0
        return 100.0 * self.get_total_unlocked() / total


# ----------------------------------------------------------------------------
# Event-based check helpers
# ----------------------------------------------------------------------------


def check_combat_event(
    state: AchievementState,
    event: str,
    value: int = 0,
    current_ms: int = 0,
) -> list[Achievement]:
    """Check achievements after a combat event.

    Events:
      - "ice_killed": value=number of ICE killed this fight
      - "crit_hit": value=number of crits in this fight
      - "boss_killed": value=boss kind ("goliath_prime", "black_ice_lord", ...)
      - "max_combo": value=highest combo this fight
      - "won_fight": value=1
      - "won_flawless": value=1
    """
    unlocked: list[Achievement] = []

    if event == "ice_killed":
        if value >= 1:
            ach = state.unlock("first_blood", current_ms)
            if ach:
                unlocked.append(ach)
        # Track total kills (cumulative)
        prev = state.get_progress("centurion_progress")
        state.set_progress("centurion_progress", prev + value)
        if state.get_progress("centurion_progress") >= 100:
            ach = state.unlock("centurion", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "crit_hit" and value >= 10:
        ach = state.unlock("sharpshooter", current_ms)
        if ach:
            unlocked.append(ach)

    elif event == "boss_killed":
        ach = state.unlock("boss_slayer", current_ms)
        if ach:
            unlocked.append(ach)
        boss_kind = str(value)
        if boss_kind == "goliath_prime":
            ach = state.unlock("goliath_slayer", current_ms)
            if ach:
                unlocked.append(ach)
        elif boss_kind == "black_ice_lord":
            ach = state.unlock("void_walker", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "max_combo" and value >= 6:
        ach = state.unlock("combo_master", current_ms)
        if ach:
            unlocked.append(ach)
        if value >= 50:
            ach = state.unlock("combo_quant", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "won_flawless":
        prev = state.get_progress("flawless_progress")
        state.set_progress("flawless_progress", prev + 1)
        if state.get_progress("flawless_progress") >= 50:
            ach = state.unlock("flawless", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "won_fight":
        # Undefeated tracking
        prev = state.get_progress("undefeated_progress")
        state.set_progress("undefeated_progress", prev + 1)
        if state.get_progress("undefeated_progress") >= 10:
            ach = state.unlock("undefeated", current_ms)
            if ach:
                unlocked.append(ach)

    return unlocked


def check_exploration_event(
    state: AchievementState,
    event: str,
    value: int = 0,
    current_ms: int = 0,
) -> list[Achievement]:
    """Check achievements after an exploration event.

    Events:
      - "jack_in": value=1
      - "visited_world": value=world_id
      - "visited_server": value=server_id (cumulative tracking)
      - "data_extracted": value=count
      - "jack_out": value=1
      - "node_visited": value=count
    """
    unlocked: list[Achievement] = []

    if event == "jack_in":
        ach = state.unlock("first_jackin", current_ms)
        if ach:
            unlocked.append(ach)

    elif event == "visited_world":
        # Track unique worlds (use set semantics via progress)
        prev = state.get_progress("worlds_visited")
        if value not in (1, 2):  # unknown world
            return unlocked
        bit = 1 << (value - 1)  # bit 0 for world 1, bit 1 for world 2
        new_progress = prev | bit
        state.set_progress("worlds_visited", new_progress)
        if (new_progress & 0b11) == 0b11:  # both worlds visited
            ach = state.unlock("world_walker", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "visited_server":
        prev = state.get_progress("servers_visited")
        state.set_progress("servers_visited", prev | (1 << value))
        # Check all 6 visited
        if (prev | (1 << value)) & 0b111111 == 0b111111:
            ach = state.unlock("server_domination", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "data_extracted":
        prev = state.get_progress("data_extracted_progress")
        state.set_progress("data_extracted_progress", prev + value)
        if state.get_progress("data_extracted_progress") >= 10:
            ach = state.unlock("data_extractor", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "jack_out":
        prev = state.get_progress("jackouts")
        state.set_progress("jackouts", prev + 1)
        if state.get_progress("jackouts") >= 10:
            ach = state.unlock("jackout_survivor", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "node_visited":
        prev = state.get_progress("nodes_visited")
        state.set_progress("nodes_visited", prev + 1)
        if state.get_progress("nodes_visited") >= 50:
            ach = state.unlock("matrix_explorer", current_ms)
            if ach:
                unlocked.append(ach)

    return unlocked


def check_story_event(
    state: AchievementState,
    event: str,
    value: str = "",
    current_ms: int = 0,
) -> list[Achievement]:
    """Check achievements after a story event.

    Events:
      - "prologue_complete": value=character name
      - "story_read": value=story id
      - "ending_unlocked": value=ending name
    """
    unlocked: list[Achievement] = []

    if event == "prologue_complete":
        ach_id = {
            "novice": "case_journey",
            "case": "case_journey",
            "veteran": "sil_awakening",
            "sil": "sil_awakening",
            "heretic": "kas_rise",
            "kas": "kas_rise",
        }.get(value.lower())
        if ach_id:
            ach = state.unlock(ach_id, current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "story_read":
        # Use a simple counter incremented per story_read event
        # (caller responsible for unique stories)
        prev = state.get_progress("stories_read")
        state.set_progress("stories_read", prev + 1)
        if state.get_progress("stories_read") >= 5:
            ach = state.unlock("five_tales", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "ending_unlocked":
        prev = state.get_progress("endings_unlocked")
        if not value:
            return unlocked
        # Track via progress number (incremented per unique ending)
        state.set_progress("endings_unlocked", prev + 1)
        if state.get_progress("endings_unlocked") >= 3:
            ach = state.unlock("the_truth", current_ms)
            if ach:
                unlocked.append(ach)

    return unlocked


def check_mastery_event(
    state: AchievementState,
    event: str,
    value: int = 0,
    current_ms: int = 0,
) -> list[Achievement]:
    """Check achievements after a mastery event.

    Events:
      - "ppl_reached": value=current PPL
      - "zdr_cleared": value=highest ZDR the player has cleared
      - "ppl_zdr_combined": value = max(PPL + ZDR) achieved in one fight
    """
    unlocked: list[Achievement] = []

    if event == "ppl_reached":
        if value >= 10:
            ach = state.unlock("ppl_10", current_ms)
            if ach:
                unlocked.append(ach)
        if value >= 20:
            ach = state.unlock("ppl_20", current_ms)
            if ach:
                unlocked.append(ach)
        if value >= 30:
            ach = state.unlock("ppl_30", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "zdr_cleared":
        # MATRIX_MASTER: PPL 30 + ZDR 30 in the same fight.
        # The caller is expected to fire BOTH ppl_reached AND zdr_cleared
        # with the same values; we record the highest ZDR cleared and
        # check it together with the highest PPL reached in check_meta.
        prev = state.get_progress("max_zdr_cleared")
        if value > prev:
            state.set_progress("max_zdr_cleared", value)

    elif event == "ppl_zdr_combined":
        # Single combined check: PPL + ZDR ≥ 60 (i.e. 30 + 30).
        if value >= 60:
            ach = state.unlock("matrix_master", current_ms)
            if ach:
                unlocked.append(ach)
        # Check true_hacker: player has unlocked every non-self achievement.
        if state.get_total_unlocked() >= len(ALL_ACHIEVEMENTS) - 1:
            ach = state.unlock("true_hacker", current_ms)
            if ach:
                unlocked.append(ach)

    return unlocked


def check_true_hacker(state: AchievementState, current_ms: int = 0) -> Achievement | None:
    """Manual check for the ``true_hacker`` meta-achievement.

    Returns the unlocked achievement if the player has every other
    achievement, else None. Useful to call after batch unlocks (e.g.
    end-of-run reward screens).
    """
    if state.get_total_unlocked() >= len(ALL_ACHIEVEMENTS) - 1:
        return state.unlock("true_hacker", current_ms)
    return None


def check_matrix_master(
    state: AchievementState, ppl: int, zdr: int, current_ms: int = 0
) -> Achievement | None:
    """Manual check for ``matrix_master``: PPL + ZDR ≥ 60 (one fight).

    Returns the unlocked achievement if conditions met, else None.
    """
    if ppl + zdr >= 60:
        return state.unlock("matrix_master", current_ms)
    return None


# ----------------------------------------------------------------------------
# Display helpers
# ----------------------------------------------------------------------------


def render_achievement(ach: Achievement, unlocked: bool) -> str:
    """Render an achievement as a card string."""
    status = "✅" if unlocked else "🔒"
    lines = [
        f"{status} [{ach.tier.value.upper()}] {ach.icon} {ach.name_ko} ({ach.name})",
        f"   {ach.description}",
    ]
    if ach.reward_credits > 0:
        lines.append(f"   보상: {ach.reward_credits} 크레딧")
    return "\n".join(lines)


def get_achievements_summary(state: AchievementState) -> dict[str, object]:
    """Get a summary dict of achievement progress for display."""
    return {
        "total_unlocked": state.get_total_unlocked(),
        "total_available": state.get_total_available(),
        "completion_pct": round(state.get_completion_pct(), 1),
        "credits_earned": state.total_credits_earned,
        "by_category": state.get_completion_stats(),
    }


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
