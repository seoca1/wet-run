/** Achievement system (port of wet_run/prototype/src/wet_run/achievements/).
 *
 * Provides the full achievement catalog (28 entries across 5 categories and
 * 4 tiers), the per-player :class:`AchievementState` for tracking progress
 * and unlocks, and event handlers that translate gameplay events into
 * unlock checks (combat / exploration / story / mastery).
 *
 * Categories:
 *   - COMBAT (7):       First Blood, Sharpshooter, Combo Master, ...
 *   - EXPLORATION (6):  First Jack-In, World Walker, ...
 *   - STORY (5):        Character prologues, short stories, endings
 *   - MASTERY (6):      PPL milestones, max combo, flawless
 *   - HIDDEN (4):       Secret discoveries
 *
 * Tiers:
 *   - BRONZE: Basic feats
 *   - SILVER: Moderate challenge
 *   - GOLD: Significant accomplishment
 *   - PLATINUM: Legendary
 *
 * Achievement IDs are the canonical Python strings (e.g. "first_blood",
 * "ppl_30") so saved metadata from the Python prototype can be cross-read.
 */

// ----------------------------------------------------------------------------
// Taxonomy enums
// ----------------------------------------------------------------------------

export type AchievementCategory =
  | "combat"
  | "exploration"
  | "story"
  | "mastery"
  | "hidden";

export type AchievementTier = "bronze" | "silver" | "gold" | "platinum";

// ----------------------------------------------------------------------------
// Achievement definition
// ----------------------------------------------------------------------------

export interface Achievement {
  readonly id: string;
  readonly name: string;
  readonly nameKo: string;
  readonly description: string;
  readonly category: AchievementCategory;
  readonly tier: AchievementTier;
  readonly icon: string;
  readonly rewardCredits: number;
  readonly hidden: boolean;
}

// ----------------------------------------------------------------------------
// Notification record + state
// ----------------------------------------------------------------------------

export interface AchievementUnlock {
  readonly achievement: Achievement;
  readonly timestampMs: number;
}

export interface AchievementStateData {
  readonly unlockedIds: ReadonlySet<string>;
  readonly unlockedIdList: ReadonlyArray<string>;
  readonly progress: Readonly<Record<string, number>>;
  readonly notificationQueue: ReadonlyArray<AchievementUnlock>;
  readonly totalCreditsEarned: number;
  readonly lastUnlocked: Achievement | null;
}

// ----------------------------------------------------------------------------
// Catalog (28 entries — matches Python achievements/catalog.py)
// ----------------------------------------------------------------------------

// COMBAT (7)
export const ACH_FIRST_BLOOD: Achievement = {
  id: "first_blood",
  name: "First Blood",
  nameKo: "첫 피",
  description: "첫 번째 ICE를 처치하세요.",
  category: "combat",
  tier: "bronze",
  icon: "\u{1F5E1}",
  rewardCredits: 50,
  hidden: false,
};

export const ACH_SHARPSHOOTER: Achievement = {
  id: "sharpshooter",
  name: "Sharpshooter",
  nameKo: "정밀 사격",
  description: "한 전투에서 10회의 크리티컬 히트를 달성하세요.",
  category: "combat",
  tier: "silver",
  icon: "\u2726",
  rewardCredits: 200,
  hidden: false,
};

export const ACH_COMBO_MASTER: Achievement = {
  id: "combo_master",
  name: "Combo Master",
  nameKo: "콤보 마스터",
  description: "ANNIHILATION 단계의 콤보를 달성하세요.",
  category: "combat",
  tier: "gold",
  icon: "\u2726\u2726\u2726",
  rewardCredits: 500,
  hidden: false,
};

export const ACH_UNDEFEATED: Achievement = {
  id: "undefeated",
  name: "Undefeated",
  nameKo: "무패",
  description: "10번의 전투에서 단 한 번도 쓰러지지 않고 승리하세요.",
  category: "combat",
  tier: "silver",
  icon: "\u2727",
  rewardCredits: 300,
  hidden: false,
};

export const ACH_BOSS_SLAYER: Achievement = {
  id: "boss_slayer",
  name: "Boss Slayer",
  nameKo: "보스 슬레이어",
  description: "첫 BOSS ICE를 처치하세요.",
  category: "combat",
  tier: "gold",
  icon: "\u2620",
  rewardCredits: 1000,
  hidden: false,
};

export const ACH_GOLIATH_SLAYER: Achievement = {
  id: "goliath_slayer",
  name: "Goliath Conqueror",
  nameKo: "골리앗 정복자",
  description: "GOLIATH PRIME를 처치하세요.",
  category: "combat",
  tier: "platinum",
  icon: "\u2605",
  rewardCredits: 2000,
  hidden: false,
};

export const ACH_CENTURION: Achievement = {
  id: "centurion",
  name: "Centurion",
  nameKo: "100 킬",
  description: "누적 100 ICE 처치.",
  category: "combat",
  tier: "gold",
  icon: "\u2726",
  rewardCredits: 1500,
  hidden: false,
};

// EXPLORATION (6)
export const ACH_FIRST_JACKIN: Achievement = {
  id: "first_jackin",
  name: "First Jack-In",
  nameKo: "첫 잭인",
  description: "매트릭스에 처음 진입하세요.",
  category: "exploration",
  tier: "bronze",
  icon: "\u25CE",
  rewardCredits: 50,
  hidden: false,
};

export const ACH_WORLD_WALKER: Achievement = {
  id: "world_walker",
  name: "World Walker",
  nameKo: "월드 워커",
  description: "두 월드(Chiba, Night City) 모두 방문.",
  category: "exploration",
  tier: "silver",
  icon: "\u2295",
  rewardCredits: 300,
  hidden: false,
};

export const ACH_SERVER_DOMINATION: Achievement = {
  id: "server_domination",
  name: "Server Domination",
  nameKo: "서버 점령",
  description: "모든 6개 서버 방문.",
  category: "exploration",
  tier: "gold",
  icon: "\u229E",
  rewardCredits: 1000,
  hidden: false,
};

export const ACH_DATA_EXTRACTOR: Achievement = {
  id: "data_extractor",
  name: "Data Extractor",
  nameKo: "데이터 추출",
  description: "10개의 데이터 노드 추출.",
  category: "exploration",
  tier: "silver",
  icon: "\u25A4",
  rewardCredits: 400,
  hidden: false,
};

export const ACH_JACKOUT_SURVIVOR: Achievement = {
  id: "jackout_survivor",
  name: "Jack-Out Survivor",
  nameKo: "잭아웃 서바이버",
  description: "10번의 잭아웃 생존.",
  category: "exploration",
  tier: "bronze",
  icon: "\u25EF",
  rewardCredits: 200,
  hidden: false,
};

export const ACH_MATRIX_EXPLORER: Achievement = {
  id: "matrix_explorer",
  name: "Matrix Explorer",
  nameKo: "매트릭스 탐험가",
  description: "50개 노드 방문.",
  category: "exploration",
  tier: "gold",
  icon: "\u25C7",
  rewardCredits: 800,
  hidden: false,
};

// STORY (5)
export const ACH_CASE_JOURNEY: Achievement = {
  id: "case_journey",
  name: "Case's Journey",
  nameKo: "케이의 여정",
  description: "케이(초보자) 프롤로그 완료.",
  category: "story",
  tier: "bronze",
  icon: "\u25C9P",
  rewardCredits: 100,
  hidden: false,
};

export const ACH_SIL_AWAKENING: Achievement = {
  id: "sil_awakening",
  name: "Sil's Awakening",
  nameKo: "실의 자각",
  description: "실(베테랑) 프롤로그 완료.",
  category: "story",
  tier: "silver",
  icon: "\u25C9V",
  rewardCredits: 200,
  hidden: false,
};

export const ACH_KAS_RISE: Achievement = {
  id: "kas_rise",
  name: "Kas's Rise",
  nameKo: "카스의 각성",
  description: "카스(헤레틱) 프롤로그 완료.",
  category: "story",
  tier: "gold",
  icon: "\u25C9H",
  rewardCredits: 300,
  hidden: false,
};

export const ACH_FIVE_TALES: Achievement = {
  id: "five_tales",
  name: "Five Tales",
  nameKo: "다섯 단편",
  description: "모든 5개 단편 소설 읽기.",
  category: "story",
  tier: "silver",
  icon: "\u2766",
  rewardCredits: 500,
  hidden: false,
};

export const ACH_THE_TRUTH: Achievement = {
  id: "the_truth",
  name: "The Truth",
  nameKo: "진실",
  description: "모든 3 엔딩 해금.",
  category: "story",
  tier: "platinum",
  icon: "\u2727",
  rewardCredits: 3000,
  hidden: false,
};

// MASTERY (6)
export const ACH_PPL_10: Achievement = {
  id: "ppl_10",
  name: "Apprentice",
  nameKo: "견습생",
  description: "PPL 10 도달.",
  category: "mastery",
  tier: "bronze",
  icon: "\u25B0",
  rewardCredits: 100,
  hidden: false,
};

export const ACH_PPL_20: Achievement = {
  id: "ppl_20",
  name: "Adept",
  nameKo: "숙련자",
  description: "PPL 20 도달.",
  category: "mastery",
  tier: "silver",
  icon: "\u25B0\u25B0",
  rewardCredits: 500,
  hidden: false,
};

export const ACH_PPL_30: Achievement = {
  id: "ppl_30",
  name: "Master",
  nameKo: "달인",
  description: "PPL 30 도달.",
  category: "mastery",
  tier: "gold",
  icon: "\u25B0\u25B0\u25B0",
  rewardCredits: 1500,
  hidden: false,
};

export const ACH_MATRIX_MASTER: Achievement = {
  id: "matrix_master",
  name: "Matrix Master",
  nameKo: "매트릭스 정통",
  description: "PPL 30 + ZDR 30 전투 승리.",
  category: "mastery",
  tier: "platinum",
  icon: "\u25C8",
  rewardCredits: 5000,
  hidden: false,
};

export const ACH_COMBO_QUANT: Achievement = {
  id: "combo_quant",
  name: "Combo Quant",
  nameKo: "콤보 콰이언",
  description: "최대 50 콤보 달성.",
  category: "mastery",
  tier: "gold",
  icon: "\u26A1",
  rewardCredits: 2000,
  hidden: false,
};

export const ACH_FLAWLESS: Achievement = {
  id: "flawless",
  name: "Flawless",
  nameKo: "완벽한 자",
  description: "데미지 없이 50 전투 승리.",
  category: "mastery",
  tier: "platinum",
  icon: "\u2727",
  rewardCredits: 4000,
  hidden: false,
};

// HIDDEN (4)
export const ACH_GHOST_PROTOCOL: Achievement = {
  id: "ghost_protocol",
  name: "Ghost Protocol",
  nameKo: "고스트 프로토콜",
  description: "한 번의 매트릭스 진입에서 단 한 번의 전투도 하지 않고 데이터 3개 추출.",
  category: "hidden",
  tier: "platinum",
  icon: "\u25C7",
  rewardCredits: 3000,
  hidden: true,
};

export const ACH_PHOENIX: Achievement = {
  id: "phoenix",
  name: "Phoenix",
  nameKo: "불사조",
  description: "사망 후 1 HP로 부활.",
  category: "hidden",
  tier: "gold",
  icon: "\u2726",
  rewardCredits: 2000,
  hidden: true,
};

export const ACH_VOID_WALKER: Achievement = {
  id: "void_walker",
  name: "Void Walker",
  nameKo: "보이드 워커",
  description: "BLACK ICE LORD 처치.",
  category: "hidden",
  tier: "platinum",
  icon: "\u2593",
  rewardCredits: 3500,
  hidden: true,
};

export const ACH_TRUE_HACKER: Achievement = {
  id: "true_hacker",
  name: "True Hacker",
  nameKo: "진정한 해커",
  description: "모든 업적 해금.",
  category: "hidden",
  tier: "platinum",
  icon: "\u2605",
  rewardCredits: 10000,
  hidden: true,
};

// ----------------------------------------------------------------------------
// Catalog lookups
// ----------------------------------------------------------------------------

export const ALL_ACHIEVEMENTS: ReadonlyArray<Achievement> = [
  // Combat
  ACH_FIRST_BLOOD,
  ACH_SHARPSHOOTER,
  ACH_COMBO_MASTER,
  ACH_UNDEFEATED,
  ACH_BOSS_SLAYER,
  ACH_GOLIATH_SLAYER,
  ACH_CENTURION,
  // Exploration
  ACH_FIRST_JACKIN,
  ACH_WORLD_WALKER,
  ACH_SERVER_DOMINATION,
  ACH_DATA_EXTRACTOR,
  ACH_JACKOUT_SURVIVOR,
  ACH_MATRIX_EXPLORER,
  // Story
  ACH_CASE_JOURNEY,
  ACH_SIL_AWAKENING,
  ACH_KAS_RISE,
  ACH_FIVE_TALES,
  ACH_THE_TRUTH,
  // Mastery
  ACH_PPL_10,
  ACH_PPL_20,
  ACH_PPL_30,
  ACH_MATRIX_MASTER,
  ACH_COMBO_QUANT,
  ACH_FLAWLESS,
  // Hidden
  ACH_GHOST_PROTOCOL,
  ACH_PHOENIX,
  ACH_VOID_WALKER,
  ACH_TRUE_HACKER,
];

export const ACHIEVEMENT_BY_ID: Readonly<Record<string, Achievement>> = Object.freeze(
  Object.fromEntries(ALL_ACHIEVEMENTS.map((a) => [a.id, a])),
);

export const ACHIEVEMENT_CATEGORIES: ReadonlyArray<AchievementCategory> = [
  "combat",
  "exploration",
  "story",
  "mastery",
  "hidden",
];

/** Get an achievement by ID, or null if unknown. */
export function getAchievement(achId: string): Achievement | null {
  return ACHIEVEMENT_BY_ID[achId] ?? null;
}

/** Get all achievements in a category (hidden omitted unless requested). */
export function getAchievementsByCategory(
  category: AchievementCategory,
  includeHidden = false,
): ReadonlyArray<Achievement> {
  return ALL_ACHIEVEMENTS.filter(
    (a) => a.category === category && (includeHidden || !a.hidden),
  );
}

// ----------------------------------------------------------------------------
// Mutable state container
// ----------------------------------------------------------------------------

/**
 * Mutable container for player achievement progress and unlocks.
 *
 * Mirrors the Python ``AchievementState`` dataclass: tracks unlocked IDs,
 * progressive counters (e.g. PPL_30 progress), a FIFO notification queue,
 * cumulative credits earned, and the most-recent unlock.
 *
 * Mutations always go through methods (never set fields directly) so the
 * invariant "credits_earned == sum(unlocked.reward_credits)" holds.
 */
export class AchievementState {
  private _unlockedIds: Set<string> = new Set();
  private _progress: Map<string, number> = new Map();
  private _notificationQueue: AchievementUnlock[] = [];
  private _totalCreditsEarned = 0;
  private _lastUnlocked: Achievement | null = null;

  /** Unlock an achievement. Returns the achievement if newly unlocked, else null. */
  unlock(achId: string, currentMs = 0): Achievement | null {
    if (this._unlockedIds.has(achId)) return null;
    const ach = getAchievement(achId);
    if (ach === null) return null;
    this._unlockedIds.add(achId);
    this._totalCreditsEarned += ach.rewardCredits;
    this._lastUnlocked = ach;
    this._notificationQueue.push({ achievement: ach, timestampMs: currentMs });
    return ach;
  }

  /** Set progress for a progressive achievement (e.g. PPL_30 at value 30). */
  setProgress(achId: string, value: number): void {
    this._progress.set(achId, value);
  }

  /** True if the achievement has been unlocked by the player. */
  isUnlocked(achId: string): boolean {
    return this._unlockedIds.has(achId);
  }

  /** Current progress value for a progressive achievement (0 if none). */
  getProgress(achId: string): number {
    return this._progress.get(achId) ?? 0;
  }

  /** Pop the next pending notification, or null if the queue is empty. */
  consumeNotification(): Achievement | null {
    const notif = this._notificationQueue.shift();
    return notif === undefined ? null : notif.achievement;
  }

  /**
   * Record progress for an achievement and unlock it if the threshold is met.
   * Returns the unlocked achievement if the threshold was just crossed.
   */
  unlockProgressAchievement(
    achId: string,
    currentValue: number,
    threshold: number,
    currentMs = 0,
  ): Achievement | null {
    this.setProgress(achId, currentValue);
    if (currentValue >= threshold) return this.unlock(achId, currentMs);
    return null;
  }

  /** Completion counts grouped by category. */
  getCompletionStats(): Readonly<Record<AchievementCategory, number>> {
    const stats: Record<AchievementCategory, number> = {
      combat: 0,
      exploration: 0,
      story: 0,
      mastery: 0,
      hidden: 0,
    };
    for (const ach of ALL_ACHIEVEMENTS) {
      if (this._unlockedIds.has(ach.id)) stats[ach.category] += 1;
    }
    return Object.freeze(stats);
  }

  /** Count of currently unlocked achievements. */
  getTotalUnlocked(): number {
    return this._unlockedIds.size;
  }

  /** Total number of achievements that exist in the catalog. */
  getTotalAvailable(): number {
    return ALL_ACHIEVEMENTS.length;
  }

  /** Completion percentage (0.0-100.0) for unlocked vs available. */
  getCompletionPct(): number {
    const total = this.getTotalAvailable();
    if (total === 0) return 0;
    return (100 * this.getTotalUnlocked()) / total;
  }

  /** Cumulative credits earned from all unlocked achievements. */
  get totalCreditsEarned(): number {
    return this._totalCreditsEarned;
  }

  /** The most-recently unlocked achievement, or null if none. */
  get lastUnlocked(): Achievement | null {
    return this._lastUnlocked;
  }

  /** Snapshot of unlocked IDs as a readonly set. */
  get unlockedIds(): ReadonlySet<string> {
    return new Set(this._unlockedIds);
  }

  /** Unlocked IDs as a sorted array (JSON-safe, deterministic order). */
  get unlockedIdList(): ReadonlyArray<string> {
    return Object.freeze(Array.from(this._unlockedIds).sort());
  }

  /** Snapshot of progress counters as a readonly record. */
  get progress(): Readonly<Record<string, number>> {
    return Object.freeze(Object.fromEntries(this._progress));
  }

  /** Snapshot of the notification queue (FIFO, oldest first). */
  get notificationQueue(): ReadonlyArray<AchievementUnlock> {
    return this._notificationQueue.slice();
  }

  /** Serialize to a plain object for persistence (JSON-safe). */
  toJSON(): AchievementStateData {
    return {
      unlockedIds: this.unlockedIds,
      unlockedIdList: this.unlockedIdList,
      progress: this.progress,
      notificationQueue: this.notificationQueue,
      totalCreditsEarned: this._totalCreditsEarned,
      lastUnlocked: this._lastUnlocked,
    };
  }
}

// ----------------------------------------------------------------------------
// Combat event handler
// ----------------------------------------------------------------------------

/**
 * Check achievements after a combat event.
 *
 * Events:
 *   - "ice_killed":      value=number of ICE killed this fight
 *   - "crit_hit":        value=number of crits in this fight
 *   - "boss_killed":     value=boss kind ("goliath_prime", "black_ice_lord", ...)
 *   - "max_combo":       value=highest combo this fight
 *   - "won_fight":       value=1
 *   - "won_flawless":    value=1
 */
export function checkCombatEvent(
  state: AchievementState,
  event: string,
  value: number | string = 0,
  currentMs = 0,
): ReadonlyArray<Achievement> {
  const unlocked: Achievement[] = [];

  if (event === "ice_killed" && typeof value === "number") {
    if (value >= 1) {
      const ach = state.unlock("first_blood", currentMs);
      if (ach) unlocked.push(ach);
    }
    // Cumulative kill tracking (centurion at 100).
    const prev = state.getProgress("centurion_progress");
    state.setProgress("centurion_progress", prev + value);
    if (state.getProgress("centurion_progress") >= 100) {
      const ach = state.unlock("centurion", currentMs);
      if (ach) unlocked.push(ach);
    }
  } else if (event === "crit_hit" && typeof value === "number" && value >= 10) {
    const ach = state.unlock("sharpshooter", currentMs);
    if (ach) unlocked.push(ach);
  } else if (event === "boss_killed") {
    const ach = state.unlock("boss_slayer", currentMs);
    if (ach) unlocked.push(ach);
    const bossKind = String(value);
    if (bossKind === "goliath_prime") {
      const g = state.unlock("goliath_slayer", currentMs);
      if (g) unlocked.push(g);
    } else if (bossKind === "black_ice_lord") {
      const v = state.unlock("void_walker", currentMs);
      if (v) unlocked.push(v);
    }
  } else if (event === "max_combo" && typeof value === "number" && value >= 6) {
    const ach = state.unlock("combo_master", currentMs);
    if (ach) unlocked.push(ach);
    if (value >= 50) {
      const q = state.unlock("combo_quant", currentMs);
      if (q) unlocked.push(q);
    }
  } else if (event === "won_flawless") {
    const prev = state.getProgress("flawless_progress");
    state.setProgress("flawless_progress", prev + 1);
    if (state.getProgress("flawless_progress") >= 50) {
      const ach = state.unlock("flawless", currentMs);
      if (ach) unlocked.push(ach);
    }
  } else if (event === "won_fight") {
    const prev = state.getProgress("undefeated_progress");
    state.setProgress("undefeated_progress", prev + 1);
    if (state.getProgress("undefeated_progress") >= 10) {
      const ach = state.unlock("undefeated", currentMs);
      if (ach) unlocked.push(ach);
    }
  }

  return unlocked;
}

// ----------------------------------------------------------------------------
// Exploration event handler
// ----------------------------------------------------------------------------

/**
 * Check achievements after an exploration event.
 *
 * Events:
 *   - "jack_in":        value=1
 *   - "visited_world":  value=world_id (1=Chiba, 2=Night City)
 *   - "visited_server": value=server_id (0-5)
 *   - "data_extracted": value=count
 *   - "jack_out":       value=1
 *   - "node_visited":   value=count
 */
export function checkExplorationEvent(
  state: AchievementState,
  event: string,
  value: number = 0,
  currentMs = 0,
): ReadonlyArray<Achievement> {
  const unlocked: Achievement[] = [];

  if (event === "jack_in") {
    const ach = state.unlock("first_jackin", currentMs);
    if (ach) unlocked.push(ach);
  } else if (event === "visited_world") {
    if (value !== 1 && value !== 2) return unlocked;
    const prev = state.getProgress("worlds_visited");
    const bit = 1 << (value - 1);
    const next = prev | bit;
    state.setProgress("worlds_visited", next);
    if ((next & 0b11) === 0b11) {
      const ach = state.unlock("world_walker", currentMs);
      if (ach) unlocked.push(ach);
    }
  } else if (event === "visited_server") {
    const prev = state.getProgress("servers_visited");
    const next = prev | (1 << value);
    state.setProgress("servers_visited", next);
    if ((next & 0b111111) === 0b111111) {
      const ach = state.unlock("server_domination", currentMs);
      if (ach) unlocked.push(ach);
    }
  } else if (event === "data_extracted") {
    const prev = state.getProgress("data_extracted_progress");
    state.setProgress("data_extracted_progress", prev + value);
    if (state.getProgress("data_extracted_progress") >= 10) {
      const ach = state.unlock("data_extractor", currentMs);
      if (ach) unlocked.push(ach);
    }
  } else if (event === "jack_out") {
    const prev = state.getProgress("jackouts");
    state.setProgress("jackouts", prev + 1);
    if (state.getProgress("jackouts") >= 10) {
      const ach = state.unlock("jackout_survivor", currentMs);
      if (ach) unlocked.push(ach);
    }
  } else if (event === "node_visited") {
    const prev = state.getProgress("nodes_visited");
    state.setProgress("nodes_visited", prev + 1);
    if (state.getProgress("nodes_visited") >= 50) {
      const ach = state.unlock("matrix_explorer", currentMs);
      if (ach) unlocked.push(ach);
    }
  }

  return unlocked;
}

// ----------------------------------------------------------------------------
// Story event handler
// ----------------------------------------------------------------------------

/**
 * Check achievements after a story event.
 *
 * Events:
 *   - "prologue_complete": value=character name ("case"|"novice",
 *                          "sil"|"veteran", "kas"|"heretic")
 *   - "story_read":        value=story id (any non-empty string)
 *   - "ending_unlocked":   value=ending name (any non-empty string)
 */
export function checkStoryEvent(
  state: AchievementState,
  event: string,
  value: string = "",
  currentMs = 0,
): ReadonlyArray<Achievement> {
  const unlocked: Achievement[] = [];

  if (event === "prologue_complete") {
    const map: Readonly<Record<string, string>> = {
      novice: "case_journey",
      case: "case_journey",
      veteran: "sil_awakening",
      sil: "sil_awakening",
      heretic: "kas_rise",
      kas: "kas_rise",
    };
    const achId = map[value.toLowerCase()];
    if (achId !== undefined) {
      const ach = state.unlock(achId, currentMs);
      if (ach) unlocked.push(ach);
    }
  } else if (event === "story_read") {
    const prev = state.getProgress("stories_read");
    state.setProgress("stories_read", prev + 1);
    if (state.getProgress("stories_read") >= 5) {
      const ach = state.unlock("five_tales", currentMs);
      if (ach) unlocked.push(ach);
    }
  } else if (event === "ending_unlocked") {
    if (value === "") return unlocked;
    const prev = state.getProgress("endings_unlocked");
    state.setProgress("endings_unlocked", prev + 1);
    if (state.getProgress("endings_unlocked") >= 3) {
      const ach = state.unlock("the_truth", currentMs);
      if (ach) unlocked.push(ach);
    }
  }

  return unlocked;
}

// ----------------------------------------------------------------------------
// Mastery event handler
// ----------------------------------------------------------------------------

/**
 * Check achievements after a mastery event.
 *
 * Events:
 *   - "ppl_reached":        value=current PPL
 *   - "zdr_cleared":         value=highest ZDR cleared (recorded for later)
 *   - "ppl_zdr_combined":    value=max(PPL + ZDR) achieved in one fight
 */
export function checkMasteryEvent(
  state: AchievementState,
  event: string,
  value: number = 0,
  currentMs = 0,
): ReadonlyArray<Achievement> {
  const unlocked: Achievement[] = [];

  if (event === "ppl_reached") {
    if (value >= 10) {
      const ach = state.unlock("ppl_10", currentMs);
      if (ach) unlocked.push(ach);
    }
    if (value >= 20) {
      const ach = state.unlock("ppl_20", currentMs);
      if (ach) unlocked.push(ach);
    }
    if (value >= 30) {
      const ach = state.unlock("ppl_30", currentMs);
      if (ach) unlocked.push(ach);
    }
  } else if (event === "zdr_cleared") {
    const prev = state.getProgress("max_zdr_cleared");
    if (value > prev) state.setProgress("max_zdr_cleared", value);
  } else if (event === "ppl_zdr_combined") {
    if (value >= 60) {
      const ach = state.unlock("matrix_master", currentMs);
      if (ach) unlocked.push(ach);
    }
    // true_hacker requires every other achievement unlocked.
    if (state.getTotalUnlocked() >= ALL_ACHIEVEMENTS.length - 1) {
      const ach = state.unlock("true_hacker", currentMs);
      if (ach) unlocked.push(ach);
    }
  }

  return unlocked;
}

// ----------------------------------------------------------------------------
// Meta-achievement helpers
// ----------------------------------------------------------------------------

/** Manual check for the ``true_hacker`` meta-achievement. */
export function checkTrueHacker(
  state: AchievementState,
  currentMs = 0,
): Achievement | null {
  if (state.getTotalUnlocked() >= ALL_ACHIEVEMENTS.length - 1) {
    return state.unlock("true_hacker", currentMs);
  }
  return null;
}

/** Manual check for ``matrix_master``: PPL + ZDR ≥ 60 in one fight. */
export function checkMatrixMaster(
  state: AchievementState,
  ppl: number,
  zdr: number,
  currentMs = 0,
): Achievement | null {
  if (ppl + zdr >= 60) return state.unlock("matrix_master", currentMs);
  return null;
}

// ----------------------------------------------------------------------------
// Display helpers
// ----------------------------------------------------------------------------

/** Render an achievement as a card string for UI. */
export function renderAchievement(ach: Achievement, unlocked: boolean): string {
  const status = unlocked ? "\u2705" : "\u{1F512}";
  const lines: string[] = [
    `${status} [${ach.tier.toUpperCase()}] ${ach.icon} ${ach.nameKo} (${ach.name})`,
    `   ${ach.description}`,
  ];
  if (ach.rewardCredits > 0) {
    lines.push(`   보상: ${ach.rewardCredits} 크레딧`);
  }
  return lines.join("\n");
}

/** Aggregate stats for HUD/UI display. */
export function getAchievementsSummary(
  state: AchievementState,
): {
  readonly totalUnlocked: number;
  readonly totalAvailable: number;
  readonly completionPct: number;
  readonly creditsEarned: number;
  readonly byCategory: Readonly<Record<AchievementCategory, number>>;
} {
  return {
    totalUnlocked: state.getTotalUnlocked(),
    totalAvailable: state.getTotalAvailable(),
    completionPct: Math.round(state.getCompletionPct() * 10) / 10,
    creditsEarned: state.totalCreditsEarned,
    byCategory: state.getCompletionStats(),
  };
}
