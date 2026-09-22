import { describe, expect, it } from "vitest";
import {
  parseMission,
  parseProgram,
  parseIce,
  loadMissionsCatalog,
  loadProgramsCatalog,
  loadIceCatalog,
} from "../src/core/data_loaders";

describe("data_loaders: parseMission", () => {
  it("accepts canonical schema (matrix_seed, grade_max)", () => {
    const m = parseMission(
      {
        id: "test_mission",
        title: "Test",
        fixer: "finn",
        arc: 1,
        zone: "surface",
        grade_min: 3,
        grade_max: 5,
        rewards: { credits: 1000, materials: { foo: 1 } },
        matrix_seed: 42,
      },
      "test_mission",
    );
    expect(m.id).toBe("test_mission");
    expect(m.seed).toBe(42);
    expect(m.grade).toBe(5);
  });

  it("normalizes legacy fields (seed, grade) when canonical fields missing", () => {
    const m = parseMission(
      {
        id: "legacy",
        title: "Legacy",
        fixer: "finn",
        arc: 1,
        zone: "surface",
        grade_min: 2,
        grade_max: 2,
        rewards: { credits: 0, materials: {} },
        seed: 99,
      },
      "legacy",
    );
    expect(m.seed).toBe(99);
    expect(m.grade).toBe(2);
  });

  it("throws on missing required id", () => {
    expect(() =>
      parseMission({ title: "X" }, "missing_id"),
    ).toThrow(/field 'id' must be a non-empty string/);
  });

  it("throws on missing rewards", () => {
    expect(() =>
      parseMission(
        { id: "x", title: "X", fixer: "f", arc: 1, zone: "z", grade_min: 1, grade_max: 1 },
        "x",
      ),
    ).toThrow(/field 'rewards' must be an object/);
  });
});

describe("data_loaders: parseProgram", () => {
  it("accepts canonical schema (cost)", () => {
    const p = parseProgram(
      {
        name: "Strike",
        tier: 1,
        cost: 2,
        effect: "attack",
        description: "Basic attack.",
      },
      "strike",
    );
    expect(p.id).toBe("strike");
    expect(p.cost).toBe(2);
    expect(p.tier).toBe(1);
  });

  it("normalizes ap_cost → cost (legacy Python schema)", () => {
    const p = parseProgram(
      {
        name: "Wisp",
        tier: 1,
        ap_cost: 3,
        effect: "defense",
        description: "Shield buff.",
      },
      "wisp",
    );
    expect(p.cost).toBe(3);
  });

  it("throws when both cost and ap_cost are set", () => {
    expect(() =>
      parseProgram({ name: "X", tier: 1, cost: 2, ap_cost: 3 }, "x"),
    ).toThrow(/both 'cost' and 'ap_cost'/);
  });

  it("throws when neither cost nor ap_cost is set", () => {
    expect(() =>
      parseProgram({ name: "X", tier: 1 }, "x"),
    ).toThrow(/requires 'cost' or 'ap_cost'/);
  });
});

describe("data_loaders: parseIce", () => {
  it("normalizes defense → armor (legacy Python schema)", () => {
    const ice = parseIce(
      { name: "ICE — Watchdog", tier: 1, defense: 5 },
      "watchdog",
    );
    expect(ice.armor).toBe(5);
    expect(ice.tier).toBe(1);
    expect(ice.hp).toBeGreaterThan(0);
  });

  it("throws when both armor and defense are set", () => {
    expect(() =>
      parseIce({ name: "X", armor: 5, defense: 3 }, "x"),
    ).toThrow(/both 'armor' and 'defense'/);
  });
});

describe("data_loaders: load catalogs", () => {
  it("loadMissionsCatalog validates every entry (throws on first bad row)", () => {
    expect(() =>
      loadMissionsCatalog({
        good: {
          id: "good",
          title: "Good",
          fixer: "finn",
          arc: 1,
          zone: "surface",
          grade_min: 1,
          grade_max: 1,
          rewards: { credits: 0, materials: {} },
        },
        bad: { title: "Bad" },
      }),
    ).toThrow(/field 'id'/);
  });

  it("loadProgramsCatalog throws on bad program", () => {
    expect(() =>
      loadProgramsCatalog({ good: { name: "G", tier: 1, cost: 1 }, bad: { name: "B", tier: 1 } }),
    ).toThrow(/requires 'cost' or 'ap_cost'/);
  });

  it("loadIceCatalog throws on bad ice", () => {
    expect(() =>
      loadIceCatalog({ good: { name: "G", tier: 1, defense: 2 }, bad: { tier: 1 } }),
    ).toThrow(/field 'name'/);
  });
});

describe("data_loaders: integration with real JSON files", () => {
  it("missions.json loads without errors (all rows pass validation)", async () => {
    const { default: data } = await import("../src/data/missions.json");
    expect(() => loadMissionsCatalog(data)).not.toThrow();
  });

  it("programs.json loads without errors", async () => {
    const { default: data } = await import("../src/data/programs.json");
    expect(() => loadProgramsCatalog(data)).not.toThrow();
  });

  it("ice_types.json loads without errors", async () => {
    const { default: data } = await import("../src/data/ice_types.json");
    expect(() => loadIceCatalog(data)).not.toThrow();
  });
});
