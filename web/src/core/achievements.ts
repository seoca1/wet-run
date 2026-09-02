/** Achievement system (port of wet_run/prototype/src/wet_run/achievements/).
 *
 * Provides the full achievement catalog (28 entries across 5 categories and
 * 4 tiers), the per-player :class:`AchievementState` for tracking progress
 * and unlocks, and event handlers that translate gameplay events into
 * unlock checks (combat / exploration / story / mastery).
 *
 * Split per ADR-0110 (2026):
 * - Core achievement logic (this file, ~450 lines)
 * - Achievement definitions → achievement_definitions.ts
 */

// Type exports
export type AchievementCategory =
  | "combat"
  | "exploration"
  | "story"
  | "mastery"
  | "hidden";

export type AchievementTier = "bronze" | "silver" | "gold" | "platinum";

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

// Re-export definitions
export {
  ACH_FIRST_BLOOD,
  ACH_SHARPSHOOTER,
  ACH_COMBO_MASTER,
  ACH_UNDEFEATED,
  ACH_BOSS_SLAYER,
  ACH_GOLIATH_SLAYER,
  ACH_CENTURION,
  ACH_FIRST_JACKIN,
  ACH_WORLD_WALKER,
  ACH_SERVER_DOMINATION,
  ACH_DATA_EXTRACTOR,
  ACH_JACKOUT_SURVIVOR,
  ACH_MATRIX_EXPLORER,
  ACH_CASE_JOURNEY,
  ACH_SIL_AWAKENING,
  ACH_KAS_RISE,
  ACH_FIVE_TALES,
  ACH_THE_TRUTH,
  ACH_PPL_10,
  ACH_PPL_20,
  ACH_PPL_30,
  ACH_MATRIX_MASTER,
  ACH_COMBO_QUANT,
  ACH_FLAWLESS,
  ACH_GHOST_PROTOCOL,
  ACH_PHOENIX,
  ACH_VOID_WALKER,
  ACH_TRUE_HACKER,
  ALL_ACHIEVEMENTS,
  ACHIEVEMENT_BY_ID,
  ACHIEVEMENT_CATEGORIES,
  getAchievement,
  getAchievementsByCategory,
} from "./achievement_definitions.ts";

import { ALL_ACHIEVEMENTS, getAchievement } from "./achievement_definitions.ts";

/**
 * Mutable container for player achievement progress and unlocks.
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

  /** Set progress for a progressive achievement. */
  setProgress(achId: string, value: number): void {
    this._progress.set(achId, value);
  }

  /** True if the achievement has been unlocked. */
  isUnlocked(achId: string): boolean {
    return this._unlockedIds.has(achId);
  }

  /** Current progress value for a progressive achievement. */
  getProgress(achId: string): number {
    return this._progress.get(achId) ?? 0;
  }

  /** Pop the next pending notification. */
  consumeNotification(): Achievement | null {
    const notif = this._notificationQueue.shift();
    return notif === undefined ? null : notif.achievement;
  }

  /**
   * Record progress for an achievement and unlock it if threshold is met.
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

  /** Total achievements in catalog. */
  getTotalAvailable(): number {
    return ALL_ACHIEVEMENTS.length;
  }

  /** Completion percentage (0.0-100.0). */
  getCompletionPct(): number {
    const total = this.getTotalAvailable();
    if (total === 0) return 0;
    return (100 * this.getTotalUnlocked()) / total;
  }

  /** Cumulative credits earned. */
  get totalCreditsEarned(): number {
    return this._totalCreditsEarned;
  }

  /** Most-recently unlocked achievement. */
  get lastUnlocked(): Achievement | null {
    return this._lastUnlocked;
  }

  /** Snapshot of unlocked IDs. */
  get unlockedIds(): ReadonlySet<string> {
    return new Set(this._unlockedIds);
  }

  /** Unlocked IDs as sorted array (JSON-safe). */
  get unlockedIdList(): ReadonlyArray<string> {
    return Object.freeze(Array.from(this._unlockedIds).sort());
  }

  /** Snapshot of progress counters. */
  get progress(): Readonly<Record<string, number>> {
    return Object.freeze(Object.fromEntries(this._progress));
  }

  /** Snapshot of notification queue. */
  get notificationQueue(): ReadonlyArray<AchievementUnlock> {
    return this._notificationQueue.slice();
  }

  /** Serialize to plain object for persistence. */
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

// Event handlers
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
    if (state.getTotalUnlocked() >= ALL_ACHIEVEMENTS.length - 1) {
      const ach = state.unlock("true_hacker", currentMs);
      if (ach) unlocked.push(ach);
    }
  }

  return unlocked;
}

// Meta-achievement helpers
export function checkTrueHacker(
  state: AchievementState,
  currentMs = 0,
): Achievement | null {
  if (state.getTotalUnlocked() >= ALL_ACHIEVEMENTS.length - 1) {
    return state.unlock("true_hacker", currentMs);
  }
  return null;
}

export function checkMatrixMaster(
  state: AchievementState,
  ppl: number,
  zdr: number,
  currentMs = 0,
): Achievement | null {
  if (ppl + zdr >= 60) return state.unlock("matrix_master", currentMs);
  return null;
}

// Display helpers
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
