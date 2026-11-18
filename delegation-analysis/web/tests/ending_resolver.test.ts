import { describe, it, expect } from "vitest";
import {
  ENDINGS,
  resolveEnding,
  getEndingsForArc,
  getEndingById,
  getEndingCounts,
  type EndingContext,
  type ArcId,
} from "../src/core/ending_resolver.ts";

describe("ending_resolver", () => {
  describe("ENDINGS constant", () => {
    it("has exactly 29 endings", () => {
      expect(ENDINGS.length).toBe(29);
    });

    it("covers all 5 arcs", () => {
      const arcs = new Set(ENDINGS.map(e => e.arc));
      expect(arcs.size).toBe(5);
      expect(arcs.has(1)).toBe(true);
      expect(arcs.has(2)).toBe(true);
      expect(arcs.has(3)).toBe(true);
      expect(arcs.has(4)).toBe(true);
      expect(arcs.has(5)).toBe(true);
    });

    it("all endings have unique IDs", () => {
      const ids = ENDINGS.map(e => e.id);
      const uniqueIds = new Set(ids);
      expect(uniqueIds.size).toBe(ids.length);
    });

    it("all endings have both English and Korean names", () => {
      for (const ending of ENDINGS) {
        expect(ending.nameEn.length).toBeGreaterThan(0);
        expect(ending.nameKo.length).toBeGreaterThan(0);
        expect(ending.descriptionEn.length).toBeGreaterThan(0);
        expect(ending.descriptionKo.length).toBeGreaterThan(0);
      }
    });

    it("all endings have a valid category", () => {
      const validCategories = new Set([
        "liberation",
        "control",
        "sacrifice",
        "exile",
        "transcendence",
        "status_quo",
        "corruption",
      ]);
      for (const ending of ENDINGS) {
        expect(validCategories.has(ending.category)).toBe(true);
      }
    });

    it("IDs follow arc<N>_<name> pattern", () => {
      const idPattern = /^arc[1-5]_[a-z_]+$/;
      for (const ending of ENDINGS) {
        expect(ending.id).toMatch(idPattern);
        const arcNum = parseInt(ending.id.substring(3, 4));
        expect(arcNum).toBe(ending.arc);
      }
    });
  });

  describe("getEndingsForArc", () => {
    it("Arc 1 has 7 endings", () => {
      const arc1 = getEndingsForArc(1);
      expect(arc1.length).toBe(7);
      expect(arc1.every(e => e.arc === 1)).toBe(true);
    });

    it("Arc 2 has 6 endings", () => {
      const arc2 = getEndingsForArc(2);
      expect(arc2.length).toBe(6);
      expect(arc2.every(e => e.arc === 2)).toBe(true);
    });

    it("Arc 3 has 6 endings", () => {
      const arc3 = getEndingsForArc(3);
      expect(arc3.length).toBe(6);
      expect(arc3.every(e => e.arc === 3)).toBe(true);
    });

    it("Arc 4 has 5 endings", () => {
      const arc4 = getEndingsForArc(4);
      expect(arc4.length).toBe(5);
      expect(arc4.every(e => e.arc === 4)).toBe(true);
    });

    it("Arc 5 has 5 endings", () => {
      const arc5 = getEndingsForArc(5);
      expect(arc5.length).toBe(5);
      expect(arc5.every(e => e.arc === 5)).toBe(true);
    });
  });

  describe("getEndingById", () => {
    it("returns ending for valid arc1 ID", () => {
      const ending = getEndingById("arc1_wage_slave");
      expect(ending).toBeDefined();
      expect(ending?.id).toBe("arc1_wage_slave");
      expect(ending?.arc).toBe(1);
    });

    it("returns ending for valid arc5 ID", () => {
      const ending = getEndingById("arc5_neuromancer");
      expect(ending).toBeDefined();
      expect(ending?.id).toBe("arc5_neuromancer");
      expect(ending?.arc).toBe(5);
    });

    it("returns undefined for invalid ID", () => {
      const ending = getEndingById("arc99_fake");
      expect(ending).toBeUndefined();
    });

    it("returns undefined for empty string", () => {
      const ending = getEndingById("");
      expect(ending).toBeUndefined();
    });
  });

  describe("getEndingCounts", () => {
    it("returns correct count per arc", () => {
      const counts = getEndingCounts();
      expect(counts[1]).toBe(7);
      expect(counts[2]).toBe(6);
      expect(counts[3]).toBe(6);
      expect(counts[4]).toBe(5);
      expect(counts[5]).toBe(5);
    });

    it("total count equals 29", () => {
      const counts = getEndingCounts();
      const total = counts[1] + counts[2] + counts[3] + counts[4] + counts[5];
      expect(total).toBe(29);
    });
  });

  describe("resolveEnding", () => {
    it("zero HP returns sacrifice ending", () => {
      const ctx: EndingContext = {
        arc: 1,
        hp: 0,
        maxHp: 100,
        credits: 0,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending.category).toBe("sacrifice");
      expect(ending.arc).toBe(1);
    });

    it("high HP + high credits returns control ending", () => {
      const ctx: EndingContext = {
        arc: 1,
        hp: 90,
        maxHp: 100,
        credits: 6000,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending.category).toBe("control");
      expect(ending.arc).toBe(1);
    });

    it("many missions completed returns liberation ending", () => {
      const ctx: EndingContext = {
        arc: 2,
        hp: 50,
        maxHp: 100,
        credits: 1000,
        missionsCompleted: 5,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending.category).toBe("liberation");
      expect(ending.arc).toBe(2);
    });

    it("many deaths falls back to status_quo", () => {
      const ctx: EndingContext = {
        arc: 3,
        hp: 70,
        maxHp: 100,
        credits: 500,
        missionsCompleted: 0,
        totalDeaths: 5,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending.category).toBe("status_quo");
      expect(ending.arc).toBe(3);
    });

    it("neutral stats return status_quo ending", () => {
      const ctx: EndingContext = {
        arc: 1,
        hp: 50,
        maxHp: 100,
        credits: 1000,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending.category).toBe("status_quo");
      expect(ending.arc).toBe(1);
    });

    it("choice-based ending takes priority over stats", () => {
      const ctx: EndingContext = {
        arc: 2,
        hp: 90,
        maxHp: 100,
        credits: 8000,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const arcEndings = getEndingsForArc(2);
      const choiceEnding = arcEndings.find(e => e.requiresChoice);
      if (choiceEnding) {
        const ctxWithChoice: EndingContext = {
          ...ctx,
          choices: [choiceEnding.requiresChoice!],
        };
        const ending = resolveEnding(ctxWithChoice);
        expect(ending.id).toBe(choiceEnding.id);
      }
    });

    it("faction-based ending takes priority over HP/credits", () => {
      const ctx: EndingContext = {
        arc: 3,
        hp: 90,
        maxHp: 100,
        credits: 8000,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const arcEndings = getEndingsForArc(3);
      const factionEnding = arcEndings.find(e => e.requiresFaction);
      if (factionEnding) {
        const ctxWithFaction: EndingContext = {
          ...ctx,
          factionScores: { [factionEnding.requiresFaction!]: 60 },
        };
        const ending = resolveEnding(ctxWithFaction);
        expect(ending.id).toBe(factionEnding.id);
      }
    });

    it("handles empty choices array", () => {
      const ctx: EndingContext = {
        arc: 1,
        hp: 50,
        maxHp: 100,
        credits: 1000,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending).toBeDefined();
      expect(ending.arc).toBe(1);
    });

    it("handles empty factionScores object", () => {
      const ctx: EndingContext = {
        arc: 2,
        hp: 50,
        maxHp: 100,
        credits: 1000,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending).toBeDefined();
      expect(ending.arc).toBe(2);
    });

    it("maxHp boundary: exactly 75% returns status_quo (not control)", () => {
      const ctx: EndingContext = {
        arc: 1,
        hp: 75,
        maxHp: 100,
        credits: 6000,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending.category).toBe("status_quo");
    });

    it("maxHp boundary: 76% + high credits returns control", () => {
      const ctx: EndingContext = {
        arc: 1,
        hp: 76,
        maxHp: 100,
        credits: 6000,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending.category).toBe("control");
    });

    it("credits boundary: 5000 credits is not enough for control", () => {
      const ctx: EndingContext = {
        arc: 1,
        hp: 90,
        maxHp: 100,
        credits: 5000,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending.category).toBe("status_quo");
    });

    it("credits boundary: 5001 credits + high HP returns control", () => {
      const ctx: EndingContext = {
        arc: 1,
        hp: 90,
        maxHp: 100,
        credits: 5001,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending.category).toBe("control");
    });

    it("missions boundary: exactly 3 missions returns liberation", () => {
      const ctx: EndingContext = {
        arc: 2,
        hp: 50,
        maxHp: 100,
        credits: 1000,
        missionsCompleted: 3,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending.category).toBe("liberation");
    });

    it("missions boundary: 2 missions falls back to first arc ending", () => {
      const ctx: EndingContext = {
        arc: 2,
        hp: 50,
        maxHp: 100,
        credits: 1000,
        missionsCompleted: 2,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending.arc).toBe(2);
    });

    it("faction score boundary: exactly 50 triggers faction ending", () => {
      const ctx: EndingContext = {
        arc: 3,
        hp: 50,
        maxHp: 100,
        credits: 1000,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const arcEndings = getEndingsForArc(3);
      const factionEnding = arcEndings.find(e => e.requiresFaction);
      if (factionEnding) {
        const ctxWithFaction: EndingContext = {
          ...ctx,
          factionScores: { [factionEnding.requiresFaction!]: 50 },
        };
        const ending = resolveEnding(ctxWithFaction);
        expect(ending.id).toBe(factionEnding.id);
      }
    });

    it("faction score boundary: 49 does not trigger faction ending", () => {
      const ctx: EndingContext = {
        arc: 3,
        hp: 50,
        maxHp: 100,
        credits: 1000,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      };
      const arcEndings = getEndingsForArc(3);
      const factionEnding = arcEndings.find(e => e.requiresFaction);
      if (factionEnding) {
        const ctxWithFaction: EndingContext = {
          ...ctx,
          factionScores: { [factionEnding.requiresFaction!]: 49 },
        };
        const ending = resolveEnding(ctxWithFaction);
        expect(ending.id).not.toBe(factionEnding.id);
      }
    });

    it("all arcs return valid ending", () => {
      const arcs: ArcId[] = [1, 2, 3, 4, 5];
      for (const arc of arcs) {
        const ctx: EndingContext = {
          arc,
          hp: 50,
          maxHp: 100,
          credits: 1000,
          missionsCompleted: 0,
          totalDeaths: 0,
          factionScores: {},
          choices: [],
        };
        const ending = resolveEnding(ctx);
        expect(ending).toBeDefined();
        expect(ending.arc).toBe(arc);
      }
    });

    it("fallback to first ending of arc when no category matches", () => {
      const ctx: EndingContext = {
        arc: 4,
        hp: 60,
        maxHp: 100,
        credits: 2000,
        missionsCompleted: 1,
        totalDeaths: 1,
        factionScores: {},
        choices: [],
      };
      const ending = resolveEnding(ctx);
      expect(ending).toBeDefined();
      expect(ending.arc).toBe(4);
    });
  });
});
