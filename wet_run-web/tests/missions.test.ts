/** Tier 2a tests for mission catalog loading + selection logic.
 */
import { describe, it, expect } from "vitest";
import missionsData from "../src/data/missions.json" with { type: "json" };

type MissionsFile = Readonly<Record<string, import("../src/core/types.js").Mission>>;

describe("mission catalog", () => {
  it("loads at least 5 missions for Tier 2a MVP", () => {
    const data = missionsData as unknown as MissionsFile;
    expect(Object.keys(data).length).toBeGreaterThanOrEqual(5);
  });

  it("each mission has required fields", () => {
    const data = missionsData as unknown as MissionsFile;
    for (const [id, mission] of Object.entries(data)) {
      expect(mission.id, `mission ${id} missing id`).toBeDefined();
      expect(mission.title.length, `mission ${id} missing title`).toBeGreaterThan(0);
      expect(mission.fixer.length, `mission ${id} missing fixer`).toBeGreaterThan(0);
      expect(mission.grade_max).toBeGreaterThanOrEqual(1);
      expect(mission.grade_max).toBeLessThanOrEqual(6);
      expect(mission.rewards.credits).toBeGreaterThan(0);
    }
  });

  it("mission IDs are unique", () => {
    const data = missionsData as unknown as MissionsFile;
    const ids = Object.keys(data);
    const uniqueIds = new Set(ids);
    expect(uniqueIds.size).toBe(ids.length);
  });

  it("mission IDs match tier 2a curation", () => {
    const data = missionsData as unknown as MissionsFile;
    const ids = Object.keys(data);
    // Tier 2a selection: 5 curated missions (per export script MVP_MISSION_IDS).
    const expected = ["first_jack", "watchdog_patrol", "ono_sendai_repair", "construct_market", "ghost_signal_origin"];
    for (const id of expected) {
      expect(ids, `expected ${id} in tier 2a catalog`).toContain(id);
    }
  });

  it("missions span tier 1-2 difficulty curve", () => {
    const data = missionsData as unknown as MissionsFile;
    const tiers = Object.values(data).map((m) => m.grade_max);
    const minTier = Math.min(...tiers);
    const maxTier = Math.max(...tiers);
    expect(minTier).toBeLessThanOrEqual(2); // tutorial entry
    expect(maxTier).toBeGreaterThanOrEqual(2); // some tier 2
  });

  it("fixers are diverse (variety for narrative)", () => {
    const data = missionsData as unknown as MissionsFile;
    const fixers = new Set(Object.values(data).map((m) => m.fixer));
    expect(fixers.size).toBeGreaterThanOrEqual(2); // At least 2 fixers across the 5 missions
  });
});
