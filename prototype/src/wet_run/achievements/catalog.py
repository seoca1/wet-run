"""Achievement catalog — the 28 named achievement constants and lookups.

Each ``ACH_*`` constant is a frozen :class:`~wet_run.achievements.models.Achievement`
instance. The :data:`ALL_ACHIEVEMENTS` tuple and :data:`ACHIEVEMENT_BY_ID`
dict provide O(1) lookup by ID; :func:`get_achievement` and
:func:`get_achievements_by_category` are the canonical accessors.

This module is intentionally data-only — no logic, no behavior. Behavior
(event handlers, display helpers) lives in
:mod:`wet_run.achievements.registry`. This separation keeps each module
under the 500 LOC PR-rejection threshold required by ADR-0110.
"""

from __future__ import annotations

from wet_run.achievements.models import Achievement, AchievementCategory, AchievementTier

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
    icon="\U0001f5e1",
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
    icon="\u2620",
    reward_credits=1000,
)

ACH_GOLIATH_SLAYER = Achievement(
    id="goliath_slayer",
    name="Goliath Conqueror",
    name_ko="골리앗 정복자",
    description="GOLIATH PRIME를 처치하세요.",
    category=AchievementCategory.COMBAT,
    tier=AchievementTier.PLATINUM,
    icon="\u2605",
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
    icon="\u25ce",
    reward_credits=50,
)

ACH_WORLD_WALKER = Achievement(
    id="world_walker",
    name="World Walker",
    name_ko="월드 워커",
    description="두 월드(Chiba, Night City) 모두 방문.",
    category=AchievementCategory.EXPLORATION,
    tier=AchievementTier.SILVER,
    icon="\u2295",
    reward_credits=300,
)

ACH_SERVER_DOMINATION = Achievement(
    id="server_domination",
    name="Server Domination",
    name_ko="서버 점령",
    description="모든 6개 서버 방문.",
    category=AchievementCategory.EXPLORATION,
    tier=AchievementTier.GOLD,
    icon="\u229e",
    reward_credits=1000,
)

ACH_DATA_EXTRACTOR = Achievement(
    id="data_extractor",
    name="Data Extractor",
    name_ko="데이터 추출",
    description="10개의 데이터 노드 추출.",
    category=AchievementCategory.EXPLORATION,
    tier=AchievementTier.SILVER,
    icon="\u25a4",
    reward_credits=400,
)

ACH_JACKOUT_SURVIVOR = Achievement(
    id="jackout_survivor",
    name="Jack-Out Survivor",
    name_ko="잭아웃 서바이버",
    description="10번의 잭아웃 생존.",
    category=AchievementCategory.EXPLORATION,
    tier=AchievementTier.BRONZE,
    icon="\u25ef",
    reward_credits=200,
)

ACH_MATRIX_EXPLORER = Achievement(
    id="matrix_explorer",
    name="Matrix Explorer",
    name_ko="매트릭스 탐험가",
    description="50개 노드 방문.",
    category=AchievementCategory.EXPLORATION,
    tier=AchievementTier.GOLD,
    icon="\u25c7",
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
    icon="\u25c9P",
    reward_credits=100,
)

ACH_SIL_AWAKENING = Achievement(
    id="sil_awakening",
    name="Sil's Awakening",
    name_ko="실의 자각",
    description="실(베테랑) 프롤로그 완료.",
    category=AchievementCategory.STORY,
    tier=AchievementTier.SILVER,
    icon="\u25c9V",
    reward_credits=200,
)

ACH_KAS_RISE = Achievement(
    id="kas_rise",
    name="Kas's Rise",
    name_ko="카스의 각성",
    description="카스(헤레틱) 프롤로그 완료.",
    category=AchievementCategory.STORY,
    tier=AchievementTier.GOLD,
    icon="\u25c9H",
    reward_credits=300,
)

ACH_FIVE_TALES = Achievement(
    id="five_tales",
    name="Five Tales",
    name_ko="다섯 단편",
    description="모든 5개 단편 소설 읽기.",
    category=AchievementCategory.STORY,
    tier=AchievementTier.SILVER,
    icon="\u2766",
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
    icon="\u25b0",
    reward_credits=100,
)

ACH_PPL_20 = Achievement(
    id="ppl_20",
    name="Adept",
    name_ko="숙련자",
    description="PPL 20 도달.",
    category=AchievementCategory.MASTERY,
    tier=AchievementTier.SILVER,
    icon="\u25b0\u25b0",
    reward_credits=500,
)

ACH_PPL_30 = Achievement(
    id="ppl_30",
    name="Master",
    name_ko="달인",
    description="PPL 30 도달.",
    category=AchievementCategory.MASTERY,
    tier=AchievementTier.GOLD,
    icon="\u25b0\u25b0\u25b0",
    reward_credits=1500,
)

ACH_MATRIX_MASTER = Achievement(
    id="matrix_master",
    name="Matrix Master",
    name_ko="매트릭스 정통",
    description="PPL 30 + ZDR 30 전투 승리.",
    category=AchievementCategory.MASTERY,
    tier=AchievementTier.PLATINUM,
    icon="\u25c8",
    reward_credits=5000,
)

ACH_COMBO_QUANT = Achievement(
    id="combo_quant",
    name="Combo Quant",
    name_ko="콤보 콰이언",
    description="최대 50 콤보 달성.",
    category=AchievementCategory.MASTERY,
    tier=AchievementTier.GOLD,
    icon="\u26a1",
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
    icon="\u25c7",
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
    icon="\u2593",
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
    icon="\u2605",
    reward_credits=10000,
    hidden=True,
)

# ----------------------------------------------------------------------------
# Registry (catalog lookups)
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
    "get_achievement",
    "get_achievements_by_category",
]
