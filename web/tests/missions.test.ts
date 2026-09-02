import { describe, it, expect } from "vitest";
import missionsData from "../src/data/missions.json" with { type: "json" };
import iceTypesData from "../src/data/ice_types.json" with { type: "json" };

type MissionsFile = Readonly<Record<string, import("../src/core/types.js").Mission>>;

describe("mission catalog", () => {
  it("loads at least 5 missions for Tier 2a MVP", () => {
    const data = missionsData as unknown as MissionsFile;
    expect(Object.keys(data).length).toBeGreaterThanOrEqual(5);
  });

  it("loads exactly 15 missions for Tier 2c", () => {
    const data = missionsData as unknown as MissionsFile;
    expect(Object.keys(data).length).toBeGreaterThanOrEqual(15);
  });

  it("loads exactly 209 missions (full Python catalog)", () => {
    const data = missionsData as unknown as MissionsFile;
    expect(Object.keys(data).length).toBe(209);
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

  it("mission IDs include core missions", () => {
    const data = missionsData as unknown as MissionsFile;
    const ids = Object.keys(data);
    expect(ids).toContain("first_jack");
    expect(ids).toContain("watchdog_patrol");
    expect(ids).toContain("ice_run");
    expect(ids).toContain("aleph_fragment");
    expect(ids).toContain("bama_statework");
  });

  it("missions span tier 1-6 difficulty curve", () => {
    const data = missionsData as unknown as MissionsFile;
    const tiers = Object.values(data).map((m) => m.grade_max);
    const minTier = Math.min(...tiers);
    const maxTier = Math.max(...tiers);
    expect(minTier).toBe(1);
    expect(maxTier).toBe(6);
  });

  it("fixers span at least 4 distinct names", () => {
    const data = missionsData as unknown as MissionsFile;
    const fixers = new Set(Object.values(data).map((m) => m.fixer));
    expect(fixers.size).toBeGreaterThanOrEqual(4);
  });

  it("zones span surface/mid/deep/core/aftermath", () => {
    const data = missionsData as unknown as MissionsFile;
    const zones = new Set(Object.values(data).map((m) => m.zone));
    expect(zones.has("surface")).toBe(true);
    expect(zones.has("mid") || zones.has("deep") || zones.has("core")).toBe(true);
  });
});

describe("ice types (Tier 2c variety)", () => {
  it("loads exactly 12 ICE types", () => {
    const data = iceTypesData as unknown as Record<string, unknown>;
    expect(Object.keys(data).length).toBeGreaterThanOrEqual(12);
  });

  it("loads exactly 97 ICE types (full Python catalog)", () => {
    const data = iceTypesData as unknown as Record<string, unknown>;
    expect(Object.keys(data).length).toBe(97);
  });

  it("ICE types include tier 1-3 representatives", () => {
    const data = iceTypesData as unknown as Record<string, { tier?: number }>;
    const tiers = new Set(Object.values(data).map((i) => i.tier));
    expect(tiers.has(1)).toBe(true);
    expect(tiers.has(2)).toBe(true);
    expect(tiers.has(3)).toBe(true);
  });

  it("ICE catalog includes Gibson-flavor types", () => {
    const ids = Object.keys(iceTypesData as object);
    expect(ids).toContain("watchdog");
    expect(ids).toContain("spider");
    expect(ids).toContain("loa_priest");
    expect(ids).toContain("black");
    expect(ids).toContain("goliath");
  });
});
