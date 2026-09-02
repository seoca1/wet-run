/** Unit tests for achievement_definitions.ts.
 *
 * Run with: npx vitest run tests/achievement_definitions.test.ts
 *
 * Tests all 28 ACH_* constant exports, ALL_ACHIEVEMENTS catalog shape,
 * ACHIEVEMENT_BY_ID lookup integrity, ACHIEVEMENT_CATEGORIES completeness,
 * getAchievement() lookup correctness, and getAchievementsByCategory()
 * filtering with hidden flag behavior.
 */

import { describe, it, expect } from "vitest";
import {
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
} from "../src/core/achievement_definitions.ts";
import type { Achievement, AchievementCategory } from "../src/core/achievements.ts";

describe("ACH_* constant exports — combat category", () => {
  it("ACH_FIRST_BLOOD has combat/bronze shape with reward 50", () => {
    expect(ACH_FIRST_BLOOD.id).toBe("first_blood");
    expect(ACH_FIRST_BLOOD.category).toBe("combat");
    expect(ACH_FIRST_BLOOD.tier).toBe("bronze");
    expect(ACH_FIRST_BLOOD.hidden).toBe(false);
    expect(ACH_FIRST_BLOOD.rewardCredits).toBe(50);
  });

  it("ACH_SHARPSHOOTER is combat/silver", () => {
    expect(ACH_SHARPSHOOTER.id).toBe("sharpshooter");
    expect(ACH_SHARPSHOOTER.category).toBe("combat");
    expect(ACH_SHARPSHOOTER.tier).toBe("silver");
  });

  it("ACH_COMBO_MASTER is combat/gold", () => {
    expect(ACH_COMBO_MASTER.category).toBe("combat");
    expect(ACH_COMBO_MASTER.tier).toBe("gold");
  });

  it("ACH_UNDEFEATED is combat/silver", () => {
    expect(ACH_UNDEFEATED.category).toBe("combat");
    expect(ACH_UNDEFEATED.tier).toBe("silver");
  });

  it("ACH_BOSS_SLAYER is combat/gold with reward 1000", () => {
    expect(ACH_BOSS_SLAYER.category).toBe("combat");
    expect(ACH_BOSS_SLAYER.tier).toBe("gold");
    expect(ACH_BOSS_SLAYER.rewardCredits).toBe(1000);
  });

  it("ACH_GOLIATH_SLAYER is combat/platinum", () => {
    expect(ACH_GOLIATH_SLAYER.category).toBe("combat");
    expect(ACH_GOLIATH_SLAYER.tier).toBe("platinum");
  });

  it("ACH_CENTURION is combat/gold", () => {
    expect(ACH_CENTURION.category).toBe("combat");
    expect(ACH_CENTURION.tier).toBe("gold");
  });
});

describe("ACH_* constant exports — exploration category", () => {
  it("ACH_FIRST_JACKIN is exploration/bronze", () => {
    expect(ACH_FIRST_JACKIN.category).toBe("exploration");
    expect(ACH_FIRST_JACKIN.tier).toBe("bronze");
  });

  it("ACH_WORLD_WALKER is exploration/silver", () => {
    expect(ACH_WORLD_WALKER.category).toBe("exploration");
    expect(ACH_WORLD_WALKER.tier).toBe("silver");
  });

  it("ACH_SERVER_DOMINATION is exploration/gold", () => {
    expect(ACH_SERVER_DOMINATION.category).toBe("exploration");
    expect(ACH_SERVER_DOMINATION.tier).toBe("gold");
  });

  it("ACH_DATA_EXTRACTOR is exploration/silver", () => {
    expect(ACH_DATA_EXTRACTOR.category).toBe("exploration");
    expect(ACH_DATA_EXTRACTOR.tier).toBe("silver");
  });

  it("ACH_JACKOUT_SURVIVOR is exploration/bronze", () => {
    expect(ACH_JACKOUT_SURVIVOR.category).toBe("exploration");
    expect(ACH_JACKOUT_SURVIVOR.tier).toBe("bronze");
  });

  it("ACH_MATRIX_EXPLORER is exploration/gold", () => {
    expect(ACH_MATRIX_EXPLORER.category).toBe("exploration");
    expect(ACH_MATRIX_EXPLORER.tier).toBe("gold");
  });
});

describe("ACH_* constant exports — story category", () => {
  it("ACH_CASE_JOURNEY is story/bronze", () => {
    expect(ACH_CASE_JOURNEY.category).toBe("story");
    expect(ACH_CASE_JOURNEY.tier).toBe("bronze");
  });

  it("ACH_SIL_AWAKENING is story/silver", () => {
    expect(ACH_SIL_AWAKENING.category).toBe("story");
    expect(ACH_SIL_AWAKENING.tier).toBe("silver");
  });

  it("ACH_KAS_RISE is story/gold", () => {
    expect(ACH_KAS_RISE.category).toBe("story");
    expect(ACH_KAS_RISE.tier).toBe("gold");
  });

  it("ACH_FIVE_TALES is story/silver", () => {
    expect(ACH_FIVE_TALES.category).toBe("story");
    expect(ACH_FIVE_TALES.tier).toBe("silver");
  });

  it("ACH_THE_TRUTH is story/platinum", () => {
    expect(ACH_THE_TRUTH.category).toBe("story");
    expect(ACH_THE_TRUTH.tier).toBe("platinum");
  });
});

describe("ACH_* constant exports — mastery category", () => {
  it("ACH_PPL_10 is mastery/bronze", () => {
    expect(ACH_PPL_10.category).toBe("mastery");
    expect(ACH_PPL_10.tier).toBe("bronze");
  });

  it("ACH_PPL_20 is mastery/silver", () => {
    expect(ACH_PPL_20.category).toBe("mastery");
    expect(ACH_PPL_20.tier).toBe("silver");
  });

  it("ACH_PPL_30 is mastery/gold", () => {
    expect(ACH_PPL_30.category).toBe("mastery");
    expect(ACH_PPL_30.tier).toBe("gold");
  });

  it("ACH_MATRIX_MASTER is mastery/platinum", () => {
    expect(ACH_MATRIX_MASTER.category).toBe("mastery");
    expect(ACH_MATRIX_MASTER.tier).toBe("platinum");
  });

  it("ACH_COMBO_QUANT is mastery/gold", () => {
    expect(ACH_COMBO_QUANT.category).toBe("mastery");
    expect(ACH_COMBO_QUANT.tier).toBe("gold");
  });

  it("ACH_FLAWLESS is mastery/platinum", () => {
    expect(ACH_FLAWLESS.category).toBe("mastery");
    expect(ACH_FLAWLESS.tier).toBe("platinum");
  });
});

describe("ACH_* constant exports — hidden category", () => {
  it("ACH_GHOST_PROTOCOL is hidden/platinum and hidden flag is true", () => {
    expect(ACH_GHOST_PROTOCOL.category).toBe("hidden");
    expect(ACH_GHOST_PROTOCOL.tier).toBe("platinum");
    expect(ACH_GHOST_PROTOCOL.hidden).toBe(true);
  });

  it("ACH_PHOENIX is hidden/gold and hidden flag is true", () => {
    expect(ACH_PHOENIX.category).toBe("hidden");
    expect(ACH_PHOENIX.tier).toBe("gold");
    expect(ACH_PHOENIX.hidden).toBe(true);
  });

  it("ACH_VOID_WALKER is hidden/platinum and hidden flag is true", () => {
    expect(ACH_VOID_WALKER.category).toBe("hidden");
    expect(ACH_VOID_WALKER.tier).toBe("platinum");
    expect(ACH_VOID_WALKER.hidden).toBe(true);
  });

  it("ACH_TRUE_HACKER is hidden/platinum and hidden flag is true", () => {
    expect(ACH_TRUE_HACKER.category).toBe("hidden");
    expect(ACH_TRUE_HACKER.tier).toBe("platinum");
    expect(ACH_TRUE_HACKER.hidden).toBe(true);
  });
});

describe("ALL_ACHIEVEMENTS catalog", () => {
  it("contains exactly 28 achievements", () => {
    expect(ALL_ACHIEVEMENTS.length).toBe(28);
  });

  it("contains all ACH_* constants by reference", () => {
    const all: ReadonlyArray<Achievement> = [
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
    ];
    for (const ach of all) {
      expect(ALL_ACHIEVEMENTS).toContain(ach);
    }
  });

  it("has expected category distribution (7/6/5/6/4)", () => {
    const counts: Record<AchievementCategory, number> = {
      combat: 0,
      exploration: 0,
      story: 0,
      mastery: 0,
      hidden: 0,
    };
    for (const ach of ALL_ACHIEVEMENTS) {
      counts[ach.category] += 1;
    }
    expect(counts.combat).toBe(7);
    expect(counts.exploration).toBe(6);
    expect(counts.story).toBe(5);
    expect(counts.mastery).toBe(6);
    expect(counts.hidden).toBe(4);
  });

  it("every achievement has populated required fields", () => {
    for (const ach of ALL_ACHIEVEMENTS) {
      expect(ach.id).toBeTruthy();
      expect(ach.name).toBeTruthy();
      expect(ach.nameKo).toBeTruthy();
      expect(ach.description).toBeTruthy();
      expect(ach.icon).toBeTruthy();
      expect(ach.category).toBeTruthy();
      expect(ach.tier).toBeTruthy();
      expect(typeof ach.rewardCredits).toBe("number");
      expect(typeof ach.hidden).toBe("boolean");
    }
  });

  it("all achievement IDs are unique", () => {
    const ids = ALL_ACHIEVEMENTS.map((a) => a.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("all tier values are one of the four valid tiers", () => {
    const validTiers = new Set(["bronze", "silver", "gold", "platinum"]);
    for (const ach of ALL_ACHIEVEMENTS) {
      expect(validTiers.has(ach.tier)).toBe(true);
    }
  });

  it("hidden flag is true exactly for hidden-category entries", () => {
    for (const ach of ALL_ACHIEVEMENTS) {
      if (ach.category === "hidden") {
        expect(ach.hidden).toBe(true);
      } else {
        expect(ach.hidden).toBe(false);
      }
    }
  });

  it("all reward credit values are non-negative", () => {
    for (const ach of ALL_ACHIEVEMENTS) {
      expect(ach.rewardCredits).toBeGreaterThanOrEqual(0);
    }
  });

  it("credits scale with tier (platinum >= gold >= silver >= bronze on average)", () => {
    const avg = (tier: Achievement["tier"]): number => {
      const values = ALL_ACHIEVEMENTS.filter((a) => a.tier === tier).map(
        (a) => a.rewardCredits,
      );
      return values.reduce((s, n) => s + n, 0) / values.length;
    };
    expect(avg("platinum")).toBeGreaterThan(avg("gold"));
    expect(avg("gold")).toBeGreaterThan(avg("silver"));
    expect(avg("silver")).toBeGreaterThan(avg("bronze"));
  });
});

describe("ACHIEVEMENT_BY_ID lookup", () => {
  it("contains exactly 28 entries", () => {
    expect(Object.keys(ACHIEVEMENT_BY_ID).length).toBe(28);
  });

  it("maps every achievement id to the correct object reference", () => {
    for (const ach of ALL_ACHIEVEMENTS) {
      expect(ACHIEVEMENT_BY_ID[ach.id]).toBe(ach);
    }
  });

  it("resolves combat achievement ids", () => {
    expect(ACHIEVEMENT_BY_ID["first_blood"]).toBe(ACH_FIRST_BLOOD);
    expect(ACHIEVEMENT_BY_ID["sharpshooter"]).toBe(ACH_SHARPSHOOTER);
    expect(ACHIEVEMENT_BY_ID["combo_master"]).toBe(ACH_COMBO_MASTER);
    expect(ACHIEVEMENT_BY_ID["undefeated"]).toBe(ACH_UNDEFEATED);
    expect(ACHIEVEMENT_BY_ID["boss_slayer"]).toBe(ACH_BOSS_SLAYER);
    expect(ACHIEVEMENT_BY_ID["goliath_slayer"]).toBe(ACH_GOLIATH_SLAYER);
    expect(ACHIEVEMENT_BY_ID["centurion"]).toBe(ACH_CENTURION);
  });

  it("resolves exploration achievement ids", () => {
    expect(ACHIEVEMENT_BY_ID["first_jackin"]).toBe(ACH_FIRST_JACKIN);
    expect(ACHIEVEMENT_BY_ID["world_walker"]).toBe(ACH_WORLD_WALKER);
    expect(ACHIEVEMENT_BY_ID["server_domination"]).toBe(ACH_SERVER_DOMINATION);
    expect(ACHIEVEMENT_BY_ID["data_extractor"]).toBe(ACH_DATA_EXTRACTOR);
    expect(ACHIEVEMENT_BY_ID["jackout_survivor"]).toBe(ACH_JACKOUT_SURVIVOR);
    expect(ACHIEVEMENT_BY_ID["matrix_explorer"]).toBe(ACH_MATRIX_EXPLORER);
  });

  it("resolves story achievement ids", () => {
    expect(ACHIEVEMENT_BY_ID["case_journey"]).toBe(ACH_CASE_JOURNEY);
    expect(ACHIEVEMENT_BY_ID["sil_awakening"]).toBe(ACH_SIL_AWAKENING);
    expect(ACHIEVEMENT_BY_ID["kas_rise"]).toBe(ACH_KAS_RISE);
    expect(ACHIEVEMENT_BY_ID["five_tales"]).toBe(ACH_FIVE_TALES);
    expect(ACHIEVEMENT_BY_ID["the_truth"]).toBe(ACH_THE_TRUTH);
  });

  it("resolves mastery achievement ids", () => {
    expect(ACHIEVEMENT_BY_ID["ppl_10"]).toBe(ACH_PPL_10);
    expect(ACHIEVEMENT_BY_ID["ppl_20"]).toBe(ACH_PPL_20);
    expect(ACHIEVEMENT_BY_ID["ppl_30"]).toBe(ACH_PPL_30);
    expect(ACHIEVEMENT_BY_ID["matrix_master"]).toBe(ACH_MATRIX_MASTER);
    expect(ACHIEVEMENT_BY_ID["combo_quant"]).toBe(ACH_COMBO_QUANT);
    expect(ACHIEVEMENT_BY_ID["flawless"]).toBe(ACH_FLAWLESS);
  });

  it("resolves hidden achievement ids", () => {
    expect(ACHIEVEMENT_BY_ID["ghost_protocol"]).toBe(ACH_GHOST_PROTOCOL);
    expect(ACHIEVEMENT_BY_ID["phoenix"]).toBe(ACH_PHOENIX);
    expect(ACHIEVEMENT_BY_ID["void_walker"]).toBe(ACH_VOID_WALKER);
    expect(ACHIEVEMENT_BY_ID["true_hacker"]).toBe(ACH_TRUE_HACKER);
  });

  it("is a frozen object", () => {
    expect(Object.isFrozen(ACHIEVEMENT_BY_ID)).toBe(true);
  });
});

describe("ACHIEVEMENT_CATEGORIES", () => {
  it("contains exactly 5 categories", () => {
    expect(ACHIEVEMENT_CATEGORIES.length).toBe(5);
  });

  it("contains every expected category literal", () => {
    expect(ACHIEVEMENT_CATEGORIES).toContain("combat");
    expect(ACHIEVEMENT_CATEGORIES).toContain("exploration");
    expect(ACHIEVEMENT_CATEGORIES).toContain("story");
    expect(ACHIEVEMENT_CATEGORIES).toContain("mastery");
    expect(ACHIEVEMENT_CATEGORIES).toContain("hidden");
  });
});

describe("getAchievement", () => {
  it("returns achievement for valid id", () => {
    expect(getAchievement("first_blood")).toBe(ACH_FIRST_BLOOD);
  });

  it("returns null for unknown id", () => {
    expect(getAchievement("not_a_real_id")).toBeNull();
  });

  it("returns null for empty string", () => {
    expect(getAchievement("")).toBeNull();
  });

  it("returns correct achievements for representative ids per category", () => {
    expect(getAchievement("first_blood")).toBe(ACH_FIRST_BLOOD);
    expect(getAchievement("sharpshooter")).toBe(ACH_SHARPSHOOTER);
    expect(getAchievement("first_jackin")).toBe(ACH_FIRST_JACKIN);
    expect(getAchievement("case_journey")).toBe(ACH_CASE_JOURNEY);
    expect(getAchievement("ppl_10")).toBe(ACH_PPL_10);
    expect(getAchievement("ghost_protocol")).toBe(ACH_GHOST_PROTOCOL);
    expect(getAchievement("true_hacker")).toBe(ACH_TRUE_HACKER);
  });

  it("is consistent with ACHIEVEMENT_BY_ID indexing", () => {
    for (const id of Object.keys(ACHIEVEMENT_BY_ID)) {
      expect(getAchievement(id)).toBe(ACHIEVEMENT_BY_ID[id]);
    }
  });
});

describe("getAchievementsByCategory", () => {
  it("returns all 7 combat achievements (no hidden in combat)", () => {
    const result = getAchievementsByCategory("combat");
    expect(result.length).toBe(7);
    expect(result).toContain(ACH_FIRST_BLOOD);
    expect(result).toContain(ACH_CENTURION);
  });

  it("returns all 6 exploration achievements", () => {
    const result = getAchievementsByCategory("exploration");
    expect(result.length).toBe(6);
    expect(result).toContain(ACH_FIRST_JACKIN);
    expect(result).toContain(ACH_MATRIX_EXPLORER);
  });

  it("returns all 5 story achievements", () => {
    const result = getAchievementsByCategory("story");
    expect(result.length).toBe(5);
    expect(result).toContain(ACH_CASE_JOURNEY);
    expect(result).toContain(ACH_THE_TRUTH);
  });

  it("returns all 6 mastery achievements", () => {
    const result = getAchievementsByCategory("mastery");
    expect(result.length).toBe(6);
    expect(result).toContain(ACH_PPL_10);
    expect(result).toContain(ACH_FLAWLESS);
  });

  it("returns empty array for hidden category when includeHidden is false", () => {
    expect(getAchievementsByCategory("hidden", false).length).toBe(0);
  });

  it("returns all 4 hidden achievements when includeHidden is true", () => {
    const result = getAchievementsByCategory("hidden", true);
    expect(result.length).toBe(4);
    expect(result).toContain(ACH_GHOST_PROTOCOL);
    expect(result).toContain(ACH_PHOENIX);
    expect(result).toContain(ACH_VOID_WALKER);
    expect(result).toContain(ACH_TRUE_HACKER);
  });

  it("omits hidden entries from non-hidden categories regardless of includeHidden", () => {
    for (const cat of ["combat", "exploration", "story", "mastery"] as const) {
      const result = getAchievementsByCategory(cat, true);
      for (const ach of result) {
        expect(ach.category).toBe(cat);
        expect(ach.hidden).toBe(false);
      }
    }
  });

  it("filters correctly based on includeHidden flag for hidden", () => {
    const without = getAchievementsByCategory("hidden", false);
    const withHidden = getAchievementsByCategory("hidden", true);
    expect(without.length).toBe(0);
    expect(withHidden.length).toBe(4);
  });

  it("default includeHidden parameter is false", () => {
    expect(getAchievementsByCategory("hidden").length).toBe(0);
  });
});
