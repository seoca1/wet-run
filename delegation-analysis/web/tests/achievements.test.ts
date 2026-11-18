/** Unit tests for the achievement system.
 *
 * Run with: npx vitest run tests/achievements.test.ts
 *
 * Tests the catalog shape (counts, categories, hidden flags), the
 * AchievementState container (unlock idempotency, progress tracking,
 * notification FIFO, credits math, completion stats), and every event
 * handler (combat / exploration / story / mastery) against deterministic
 * scenarios.
 */

import { describe, it, expect } from "vitest";
import {
  ACHIEVEMENT_BY_ID,
  ACHIEVEMENT_CATEGORIES,
  ALL_ACHIEVEMENTS,
  AchievementState,
  checkCombatEvent,
  checkExplorationEvent,
  checkMasteryEvent,
  checkMatrixMaster,
  checkStoryEvent,
  checkTrueHacker,
  getAchievement,
  getAchievementsByCategory,
  getAchievementsSummary,
  renderAchievement,
  type Achievement,
  type AchievementCategory,
} from "../src/core/achievements.ts";

describe("achievement catalog", () => {
  it("contains exactly 28 achievements (matches Python catalog)", () => {
    expect(ALL_ACHIEVEMENTS.length).toBe(28);
  });

  it("ACHIEVEMENT_BY_ID is keyed by every achievement id", () => {
    for (const ach of ALL_ACHIEVEMENTS) {
      expect(ACHIEVEMENT_BY_ID[ach.id]).toBe(ach);
    }
  });

  it("all achievement ids are unique", () => {
    const ids = new Set(ALL_ACHIEVEMENTS.map((a) => a.id));
    expect(ids.size).toBe(ALL_ACHIEVEMENTS.length);
  });

  it("every achievement has a non-empty id, name, and description", () => {
    for (const ach of ALL_ACHIEVEMENTS) {
      expect(ach.id.length).toBeGreaterThan(0);
      expect(ach.name.length).toBeGreaterThan(0);
      expect(ach.nameKo.length).toBeGreaterThan(0);
      expect(ach.description.length).toBeGreaterThan(0);
      expect(ach.icon.length).toBeGreaterThan(0);
    }
  });

  it("category counts match the documented split", () => {
    const counts: Record<AchievementCategory, number> = {
      combat: 0,
      exploration: 0,
      story: 0,
      mastery: 0,
      hidden: 0,
    };
    for (const ach of ALL_ACHIEVEMENTS) counts[ach.category] += 1;
    expect(counts.combat).toBe(7);
    expect(counts.exploration).toBe(6);
    expect(counts.story).toBe(5);
    expect(counts.mastery).toBe(6);
    expect(counts.hidden).toBe(4);
  });

  it("every category has hidden-flagged achievements", () => {
    const hidden = ALL_ACHIEVEMENTS.filter((a) => a.hidden);
    expect(hidden.length).toBe(4);
    for (const ach of hidden) expect(ach.category).toBe("hidden");
  });

  it("non-hidden categories have no hidden entries", () => {
    for (const cat of ["combat", "exploration", "story", "mastery"] as const) {
      const inCat = ALL_ACHIEVEMENTS.filter((a) => a.category === cat);
      for (const ach of inCat) expect(ach.hidden).toBe(false);
    }
  });

  it("every achievement has a positive or zero reward credits", () => {
    for (const ach of ALL_ACHIEVEMENTS) {
      expect(ach.rewardCredits).toBeGreaterThanOrEqual(0);
    }
  });

  it("getAchievement returns null for unknown ids", () => {
    expect(getAchievement("nope_does_not_exist")).toBeNull();
  });

  it("getAchievement returns the canonical entry for known ids", () => {
    expect(getAchievement("first_blood")?.name).toBe("First Blood");
    expect(getAchievement("true_hacker")?.hidden).toBe(true);
  });

  it("getAchievementsByCategory returns the matching slice", () => {
    const combat = getAchievementsByCategory("combat");
    expect(combat.length).toBe(7);
    for (const ach of combat) expect(ach.category).toBe("combat");
  });

  it("getAchievementsByCategory omits hidden by default, includes with flag", () => {
    const hidden = getAchievementsByCategory("hidden");
    expect(hidden.length).toBe(0);
    const hiddenIncluded = getAchievementsByCategory("hidden", true);
    expect(hiddenIncluded.length).toBe(4);
  });

  it("ACHIEVEMENT_CATEGORIES lists every category", () => {
    expect(new Set(ACHIEVEMENT_CATEGORIES)).toEqual(
      new Set<AchievementCategory>(["combat", "exploration", "story", "mastery", "hidden"]),
    );
  });
});

describe("AchievementState", () => {
  it("starts empty", () => {
    const s = new AchievementState();
    expect(s.getTotalUnlocked()).toBe(0);
    expect(s.getTotalAvailable()).toBe(28);
    expect(s.getCompletionPct()).toBe(0);
    expect(s.totalCreditsEarned).toBe(0);
    expect(s.lastUnlocked).toBeNull();
    expect(s.unlockedIds.size).toBe(0);
    expect(Object.keys(s.progress).length).toBe(0);
    expect(s.notificationQueue.length).toBe(0);
  });

  it("unlock adds the achievement and returns it", () => {
    const s = new AchievementState();
    const ach = s.unlock("first_blood", 1000);
    expect(ach?.id).toBe("first_blood");
    expect(s.isUnlocked("first_blood")).toBe(true);
    expect(s.getTotalUnlocked()).toBe(1);
    expect(s.totalCreditsEarned).toBe(50);
    expect(s.lastUnlocked?.id).toBe("first_blood");
    expect(s.notificationQueue.length).toBe(1);
    expect(s.notificationQueue[0]?.timestampMs).toBe(1000);
  });

  it("unlock is idempotent — second call returns null and credits do not double", () => {
    const s = new AchievementState();
    expect(s.unlock("first_blood", 1000)?.id).toBe("first_blood");
    expect(s.unlock("first_blood", 2000)).toBeNull();
    expect(s.totalCreditsEarned).toBe(50);
    expect(s.notificationQueue.length).toBe(1);
  });

  it("unlock returns null for unknown ids (no exception)", () => {
    const s = new AchievementState();
    expect(s.unlock("not_real")).toBeNull();
    expect(s.getTotalUnlocked()).toBe(0);
  });

  it("setProgress stores and retrieves progress values", () => {
    const s = new AchievementState();
    s.setProgress("custom_counter", 7);
    expect(s.getProgress("custom_counter")).toBe(7);
    expect(s.getProgress("never_set")).toBe(0);
  });

  it("consumeNotification pops FIFO and returns the achievement", () => {
    const s = new AchievementState();
    s.unlock("first_blood", 1000);
    s.unlock("first_jackin", 2000);
    expect(s.notificationQueue.length).toBe(2);
    expect(s.consumeNotification()?.id).toBe("first_blood");
    expect(s.consumeNotification()?.id).toBe("first_jackin");
    expect(s.consumeNotification()).toBeNull();
  });

  it("unlockProgressAchievement unlocks when value meets threshold", () => {
    const s = new AchievementState();
    expect(s.unlockProgressAchievement("ppl_30", 25, 30, 5000)).toBeNull();
    expect(s.getProgress("ppl_30")).toBe(25);
    expect(s.isUnlocked("ppl_30")).toBe(false);

    expect(s.unlockProgressAchievement("ppl_30", 30, 30, 6000)?.id).toBe("ppl_30");
    expect(s.getProgress("ppl_30")).toBe(30);
    expect(s.isUnlocked("ppl_30")).toBe(true);
    expect(s.notificationQueue[0]?.timestampMs).toBe(6000);
  });

  it("getCompletionStats counts by category", () => {
    const s = new AchievementState();
    s.unlock("first_blood"); // combat
    s.unlock("boss_slayer"); // combat
    s.unlock("first_jackin"); // exploration
    s.unlock("case_journey"); // story
    const stats = s.getCompletionStats();
    expect(stats.combat).toBe(2);
    expect(stats.exploration).toBe(1);
    expect(stats.story).toBe(1);
    expect(stats.mastery).toBe(0);
    expect(stats.hidden).toBe(0);
  });

  it("getCompletionPct rounds correctly", () => {
    const s = new AchievementState();
    for (let i = 0; i < 7; i++) {
      // Unlock the first 7 (combat).
      s.unlock(ALL_ACHIEVEMENTS[i]?.id ?? "");
    }
    expect(s.getCompletionPct()).toBeCloseTo(100 * 7 / 28);
  });

  it("toJSON snapshot is JSON-safe", () => {
    const s = new AchievementState();
    s.unlock("first_blood", 1234);
    const json = JSON.parse(JSON.stringify(s.toJSON()));
    expect(json.unlockedIdList).toEqual(["first_blood"]);
    expect(json.totalCreditsEarned).toBe(50);
    expect(json.lastUnlocked.id).toBe("first_blood");
    expect(json.notificationQueue[0].timestampMs).toBe(1234);
  });
});

describe("checkCombatEvent", () => {
  it("ice_killed of 1 unlocks first_blood", () => {
    const s = new AchievementState();
    const unlocked = checkCombatEvent(s, "ice_killed", 1);
    expect(unlocked.map((a) => a.id)).toEqual(["first_blood"]);
    expect(s.isUnlocked("first_blood")).toBe(true);
  });

  it("ice_killed accumulates centurion_progress across calls", () => {
    const s = new AchievementState();
    for (let i = 0; i < 9; i++) checkCombatEvent(s, "ice_killed", 10);
    expect(s.getProgress("centurion_progress")).toBe(90);
    expect(s.isUnlocked("centurion")).toBe(false);
    // One more ice_killed = 100 cumulative → unlock.
    const last = checkCombatEvent(s, "ice_killed", 10);
    expect(s.isUnlocked("centurion")).toBe(true);
    expect(last.map((a) => a.id)).toContain("centurion");
  });

  it("crit_hit ≥ 10 unlocks sharpshooter (and below threshold does not)", () => {
    const s = new AchievementState();
    expect(checkCombatEvent(s, "crit_hit", 9)).toEqual([]);
    expect(checkCombatEvent(s, "crit_hit", 10).map((a) => a.id)).toEqual(["sharpshooter"]);
  });

  it("boss_killed unlocks boss_slayer and goliath_slayer for goliath_prime", () => {
    const s = new AchievementState();
    const unlocked = checkCombatEvent(s, "boss_killed", "goliath_prime");
    expect(unlocked.map((a) => a.id).sort()).toEqual(["boss_slayer", "goliath_slayer"].sort());
  });

  it("boss_killed unlocks void_walker for black_ice_lord", () => {
    const s = new AchievementState();
    const unlocked = checkCombatEvent(s, "boss_killed", "black_ice_lord");
    expect(unlocked.map((a) => a.id).sort()).toEqual(["boss_slayer", "void_walker"].sort());
  });

  it("boss_killed with unknown kind only unlocks boss_slayer", () => {
    const s = new AchievementState();
    const unlocked = checkCombatEvent(s, "boss_killed", "watchdog");
    expect(unlocked.map((a) => a.id)).toEqual(["boss_slayer"]);
  });

  it("max_combo ≥ 6 unlocks combo_master and ≥ 50 also unlocks combo_quant (combo_master already unlocked is idempotent)", () => {
    const s = new AchievementState();
    expect(checkCombatEvent(s, "max_combo", 6).map((a) => a.id)).toEqual(["combo_master"]);
    // Second call at 50: combo_master is already unlocked (idempotent),
    // so only combo_quant appears as a *newly* unlocked achievement.
    expect(checkCombatEvent(s, "max_combo", 50).map((a) => a.id)).toEqual(["combo_quant"]);
    expect(s.isUnlocked("combo_master")).toBe(true);
    expect(s.isUnlocked("combo_quant")).toBe(true);
  });

  it("won_flawless tracks progress and unlocks at 50", () => {
    const s = new AchievementState();
    for (let i = 0; i < 50; i++) {
      const last = checkCombatEvent(s, "won_flawless", 1);
      if (i < 49) expect(last).toEqual([]);
      else expect(last.map((a) => a.id)).toEqual(["flawless"]);
    }
    expect(s.isUnlocked("flawless")).toBe(true);
  });

  it("won_fight accumulates undefeated_progress and unlocks at 10", () => {
    const s = new AchievementState();
    for (let i = 0; i < 10; i++) checkCombatEvent(s, "won_fight", 1);
    expect(s.isUnlocked("undefeated")).toBe(true);
  });

  it("unknown combat event is a no-op", () => {
    const s = new AchievementState();
    expect(checkCombatEvent(s, "totally_unknown", 99)).toEqual([]);
    expect(s.getTotalUnlocked()).toBe(0);
  });
});

describe("checkExplorationEvent", () => {
  it("jack_in unlocks first_jackin", () => {
    const s = new AchievementState();
    expect(checkExplorationEvent(s, "jack_in").map((a) => a.id)).toEqual(["first_jackin"]);
  });

  it("visited_world sets bit and unlocks world_walker when both visited", () => {
    const s = new AchievementState();
    checkExplorationEvent(s, "visited_world", 1);
    expect(s.isUnlocked("world_walker")).toBe(false);
    expect(s.getProgress("worlds_visited")).toBe(0b01);
    expect(checkExplorationEvent(s, "visited_world", 2).map((a) => a.id)).toEqual(["world_walker"]);
  });

  it("visited_world ignores unknown world ids", () => {
    const s = new AchievementState();
    checkExplorationEvent(s, "visited_world", 5);
    expect(s.getProgress("worlds_visited")).toBe(0);
  });

  it("visited_server unlocks server_domination only when all 6 visited", () => {
    const s = new AchievementState();
    for (let i = 0; i < 5; i++) checkExplorationEvent(s, "visited_server", i);
    expect(s.isUnlocked("server_domination")).toBe(false);
    checkExplorationEvent(s, "visited_server", 5);
    expect(s.isUnlocked("server_domination")).toBe(true);
  });

  it("data_extracted unlocks data_extractor at cumulative 10", () => {
    const s = new AchievementState();
    checkExplorationEvent(s, "data_extracted", 5);
    expect(s.isUnlocked("data_extractor")).toBe(false);
    expect(checkExplorationEvent(s, "data_extracted", 5).map((a) => a.id)).toEqual(["data_extractor"]);
  });

  it("jack_out unlocks jackout_survivor at 10", () => {
    const s = new AchievementState();
    for (let i = 0; i < 9; i++) checkExplorationEvent(s, "jack_out", 1);
    expect(s.isUnlocked("jackout_survivor")).toBe(false);
    checkExplorationEvent(s, "jack_out", 1);
    expect(s.isUnlocked("jackout_survivor")).toBe(true);
  });

  it("node_visited unlocks matrix_explorer at 50", () => {
    const s = new AchievementState();
    for (let i = 0; i < 49; i++) checkExplorationEvent(s, "node_visited", 1);
    expect(s.isUnlocked("matrix_explorer")).toBe(false);
    checkExplorationEvent(s, "node_visited", 1);
    expect(s.isUnlocked("matrix_explorer")).toBe(true);
  });

  it("unknown exploration event is a no-op", () => {
    const s = new AchievementState();
    expect(checkExplorationEvent(s, "mystery")).toEqual([]);
    expect(s.getTotalUnlocked()).toBe(0);
  });
});

describe("checkStoryEvent", () => {
  it("prologue_complete maps every character alias to the right achievement", () => {
    const cases: ReadonlyArray<readonly [string, string]> = [
      ["novice", "case_journey"],
      ["case", "case_journey"],
      ["NOVICE", "case_journey"],
      ["veteran", "sil_awakening"],
      ["sil", "sil_awakening"],
      ["heretic", "kas_rise"],
      ["kas", "kas_rise"],
    ];
    for (const [value, expectedId] of cases) {
      const s = new AchievementState();
      const unlocked = checkStoryEvent(s, "prologue_complete", value);
      expect(unlocked.map((a) => a.id)).toEqual([expectedId]);
    }
  });

  it("prologue_complete with unknown character is a no-op", () => {
    const s = new AchievementState();
    expect(checkStoryEvent(s, "prologue_complete", "wonderland")).toEqual([]);
  });

  it("story_read unlocks five_tales at 5 unique reads", () => {
    const s = new AchievementState();
    for (let i = 0; i < 5; i++) checkStoryEvent(s, "story_read", `story_${i}`);
    expect(s.isUnlocked("five_tales")).toBe(true);
  });

  it("ending_unlocked with empty value is a no-op (no progress, no unlock)", () => {
    const s = new AchievementState();
    expect(checkStoryEvent(s, "ending_unlocked", "")).toEqual([]);
    expect(s.getProgress("endings_unlocked")).toBe(0);
  });

  it("ending_unlocked unlocks the_truth at 3 unique endings", () => {
    const s = new AchievementState();
    checkStoryEvent(s, "ending_unlocked", "A");
    checkStoryEvent(s, "ending_unlocked", "B");
    expect(s.isUnlocked("the_truth")).toBe(false);
    const third = checkStoryEvent(s, "ending_unlocked", "C");
    expect(third.map((a) => a.id)).toEqual(["the_truth"]);
  });

  it("unknown story event is a no-op", () => {
    const s = new AchievementState();
    expect(checkStoryEvent(s, "narrative")).toEqual([]);
  });
});

describe("checkMasteryEvent", () => {
  it("ppl_reached at 10/20/30 unlocks ppl_10/20/30 in order", () => {
    const s = new AchievementState();
    expect(checkMasteryEvent(s, "ppl_reached", 10).map((a) => a.id)).toEqual(["ppl_10"]);
    expect(checkMasteryEvent(s, "ppl_reached", 20).map((a) => a.id)).toEqual(["ppl_20"]);
    expect(checkMasteryEvent(s, "ppl_reached", 30).map((a) => a.id)).toEqual(["ppl_30"]);
    // Re-firing ppl_reached=30 is idempotent (no duplicates).
    expect(checkMasteryEvent(s, "ppl_reached", 30)).toEqual([]);
  });

  it("ppl_reached at 30 unlocks all three milestones at once", () => {
    const s = new AchievementState();
    const unlocked = checkMasteryEvent(s, "ppl_reached", 30).map((a) => a.id).sort();
    expect(unlocked).toEqual(["ppl_10", "ppl_20", "ppl_30"].sort());
  });

  it("zdr_cleared records the highest value (never decreases)", () => {
    const s = new AchievementState();
    checkMasteryEvent(s, "zdr_cleared", 10);
    checkMasteryEvent(s, "zdr_cleared", 25);
    expect(s.getProgress("max_zdr_cleared")).toBe(25);
    checkMasteryEvent(s, "zdr_cleared", 5);
    expect(s.getProgress("max_zdr_cleared")).toBe(25);
  });

  it("ppl_zdr_combined ≥ 60 unlocks matrix_master", () => {
    const s = new AchievementState();
    expect(checkMasteryEvent(s, "ppl_zdr_combined", 59)).toEqual([]);
    expect(checkMasteryEvent(s, "ppl_zdr_combined", 60).map((a) => a.id)).toEqual(["matrix_master"]);
  });

  it("checkMatrixMaster is the manual matrix_master shortcut", () => {
    const s = new AchievementState();
    expect(checkMatrixMaster(s, 30, 29)).toBeNull();
    expect(checkMatrixMaster(s, 30, 30)?.id).toBe("matrix_master");
  });

  it("checkTrueHacker unlocks true_hacker when every other achievement is unlocked", () => {
    const s = new AchievementState();
    // Unlock all 27 non-self achievements.
    for (const ach of ALL_ACHIEVEMENTS) {
      if (ach.id === "true_hacker") continue;
      s.unlock(ach.id);
    }
    expect(s.getTotalUnlocked()).toBe(27);
    expect(checkTrueHacker(s)?.id).toBe("true_hacker");
    expect(s.isUnlocked("true_hacker")).toBe(true);
  });

  it("checkTrueHacker returns null when not all other achievements are unlocked", () => {
    const s = new AchievementState();
    s.unlock("first_blood");
    expect(checkTrueHacker(s)).toBeNull();
  });

  it("unknown mastery event is a no-op", () => {
    const s = new AchievementState();
    expect(checkMasteryEvent(s, "nope")).toEqual([]);
  });
});

describe("display helpers", () => {
  const sample: Achievement = ACHIEVEMENT_BY_ID["first_blood"] as Achievement;

  it("renderAchievement shows status icon, tier, name, description", () => {
    const rendered = renderAchievement(sample, true);
    expect(rendered).toContain("BRONZE");
    expect(rendered).toContain("첫 피");
    expect(rendered).toContain("First Blood");
    expect(rendered).toContain("50 크레딧");
  });

  it("renderAchievement omits the reward line when zero", () => {
    const noReward: Achievement = { ...sample, rewardCredits: 0 };
    expect(renderAchievement(noReward, false)).not.toContain("크레딧");
  });

  it("getAchievementsSummary returns aggregate HUD data", () => {
    const s = new AchievementState();
    s.unlock("first_blood");
    s.unlock("first_jackin");
    const summary = getAchievementsSummary(s);
    expect(summary.totalUnlocked).toBe(2);
    expect(summary.totalAvailable).toBe(28);
    expect(summary.creditsEarned).toBe(100);
    expect(summary.byCategory.combat).toBe(1);
    expect(summary.byCategory.exploration).toBe(1);
    // Completion rounded to one decimal.
    expect(summary.completionPct).toBeCloseTo(100 * 2 / 28, 0);
  });
});
