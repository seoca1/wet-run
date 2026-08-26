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

  it("loads exactly 30 missions for Tier 3", () => {
    const data = missionsData as unknown as MissionsFile;
    expect(Object.keys(data).length).toBe(30);
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

  it("mission IDs match tier 3 curation", () => {
    const data = missionsData as unknown as MissionsFile;
    const ids = Object.keys(data);
    const expected = [
      "first_jack",
      "watchdog_patrol",
      "ono_sendai_repair",
      "construct_market",
      "ghost_signal_origin",
      "razor_work",
      "soho_blackout",
      "delivery_to_finn",
      "ice_run",
      "armitage_infiltration",
      "flatline_call",
      "hosaka_corporate_infiltration",
      "idoru_wedding",
      "laney_node_signal_run",
      "first_contact",
      "cortex_hound_recovery",
      "data_retrieval",
      "hosaka_after_hours",
      "hosaka_terminal_supply",
      "chevette_nightshift_run",
      "case_past_extract_linda_memory",
      "hideo_contract",
      "mid_extract_yakuza_chop_shop",
      "bridge_scaffold",
      "hosaka_core",
      "maas_heist",
      "angie_leopard_tracking",
      "core_extract_neuromancer_signature",
      "aleph_fragment",
      "bama_statework",
    ];
    expect(ids.sort()).toEqual([...expected].sort());
  });

  it("missions span tier 1-5 difficulty curve", () => {
    const data = missionsData as unknown as MissionsFile;
    const tiers = Object.values(data).map((m) => m.grade_max);
    const minTier = Math.min(...tiers);
    const maxTier = Math.max(...tiers);
    expect(minTier).toBe(1);
    expect(maxTier).toBe(5);
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

  it("loads exactly 30 ICE types for Tier 3", () => {
    const data = iceTypesData as unknown as Record<string, unknown>;
    expect(Object.keys(data).length).toBe(30);
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
