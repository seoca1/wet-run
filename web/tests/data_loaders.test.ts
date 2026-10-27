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

  it("defaults source_universe to sprawl when missing", () => {
    const m = parseMission(
      {
        id: "x",
        title: "X",
        fixer: "f",
        arc: 1,
        zone: "z",
        grade_min: 1,
        grade_max: 1,
        rewards: { credits: 0, materials: {} },
      },
      "x",
    );
    expect(m.source_universe).toBe("sprawl");
  });

  it("accepts source_universe far-grid", () => {
    const m = parseMission(
      {
        id: "x",
        title: "X",
        fixer: "f",
        arc: 1,
        zone: "z",
        grade_min: 1,
        grade_max: 1,
        rewards: { credits: 0, materials: {} },
        source_universe: "far-grid",
      },
      "x",
    );
    expect(m.source_universe).toBe("far-grid");
  });

  it("throws on unknown source_universe value", () => {
    expect(() =>
      parseMission(
        {
          id: "x",
          title: "X",
          fixer: "f",
          arc: 1,
          zone: "z",
          grade_min: 1,
          grade_max: 1,
          rewards: { credits: 0, materials: {} },
          source_universe: "hybridscape",
        },
        "x",
      ),
    ).toThrow(/source_universe.*sprawl.*far-grid/);
  });

  it("accepts story with source only", () => {
    const m = parseMission(
      {
        id: "x",
        title: "X",
        fixer: "f",
        arc: 1,
        zone: "z",
        grade_min: 1,
        grade_max: 1,
        rewards: { credits: 0, materials: {} },
        story: { source: "xauthors/true-names/en/2026-10-11_moat_burned_blue" },
      },
      "x",
    );
    expect(m.story?.source).toBe(
      "xauthors/true-names/en/2026-10-11_moat_burned_blue",
    );
    expect(m.story?.title).toBeUndefined();
  });

  it("accepts story with source and title", () => {
    const m = parseMission(
      {
        id: "x",
        title: "X",
        fixer: "f",
        arc: 1,
        zone: "z",
        grade_min: 1,
        grade_max: 1,
        rewards: { credits: 0, materials: {} },
        story: { source: "s", title: "T" },
      },
      "x",
    );
    expect(m.story).toEqual({ source: "s", title: "T" });
  });

  it("throws on malformed story field", () => {
    const base = {
      id: "x",
      title: "X",
      fixer: "f",
      arc: 1,
      zone: "z",
      grade_min: 1,
      grade_max: 1,
      rewards: { credits: 0, materials: {} },
    };
    expect(() => parseMission({ ...base, story: "s" }, "x")).toThrow(
      /field 'story' must be an object/,
    );
    expect(() => parseMission({ ...base, story: {} }, "x")).toThrow(
      /field 'story.source' must be a non-empty string/,
    );
    expect(() => parseMission({ ...base, story: { source: "" } }, "x")).toThrow(
      /field 'story.source' must be a non-empty string/,
    );
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

  it("derives hp from hp_base when hp_per_grade is missing (partial data)", () => {
    // Legacy rows that carry only hp_base (no hp_per_grade) still need a
    // usable hp. parseIce falls back to 100 in that case; hpBase is still
    // exposed for `iceHpForGrade` to compose at combat time.
    const ice = parseIce(
      { name: "ICE — X", tier: 1, armor: 0, hp_base: 75 },
      "x",
    );
    expect(ice.hpBase).toBe(75);
    expect(ice.hpPerGrade).toBeUndefined();
    // No per_grade data → legacy 100 fallback (pinned by existing assertion).
    expect(ice.hp).toBe(100);
  });

  it("derives hp from hp_base + hp_per_grade at default grade 1 (ADR-0211)", () => {
    // Watchdog (hp_base=50, hp_per_grade=10) → hp = 50 at grade 1, not 100.
    const watchdog = parseIce(
      { name: "ICE — Watchdog", tier: 1, armor: 1, hp_base: 50, hp_per_grade: 10 },
      "watchdog",
    );
    expect(watchdog.hpBase).toBe(50);
    expect(watchdog.hpPerGrade).toBe(10);
    expect(watchdog.hp).toBe(50);
  });

  it("falls back to legacy hp=100 when both hp_base and hp_per_grade are missing", () => {
    // Pure legacy rows (no grade data at all) keep the pre-ADR-0211 default
    // so any consumer still reading `ice.hp` directly gets a sensible value.
    const ice = parseIce({ name: "ICE — Legacy", tier: 1, armor: 0 }, "x");
    expect(ice.hpBase).toBeUndefined();
    expect(ice.hpPerGrade).toBeUndefined();
    expect(ice.hp).toBe(100);
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

  it("every mission in missions.json defaults to sprawl universe", async () => {
    const { default: data } = await import("../src/data/missions.json");
    const loaded = loadMissionsCatalog(data);
    expect(loaded.length).toBe(Object.keys(data).length);
    const farGrid = loaded.filter((m) => m.source_universe === "far-grid");
    expect(farGrid.map((m) => m.id).sort()).toEqual([
      "arkady_in_orange",
      "blue_silk_wall",
      "deathspiders_news",
      "dirtgirl_dispatch",
      "dodgers_office",
      "don_mac_audit",
      "erythrinas_list",
      "far_grid_prelude",
      "firebuds_chair",
      "hetmans_meeting",
      "limeys_long_game",
      "maidens_first_run",
      "mailmans_last_letter",
      "maurice_princes",
      "moat_burned_blue",
      "pollack_after_dark",
      "rogers_backyard",
      "tin_soldiers_end",
      "warren_meadow",
      "wileys_gate",
    ]);
    for (const m of loaded) {
      if (m.source_universe !== "far-grid") {
        expect(m.source_universe).toBe("sprawl");
      }
    }
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

/**
 * Regression: `parseIce` used to drop the ICE `skills` array entirely.
 *
 * `ice_types.json` declares skills as bare id strings; the loader must map
 * them into the typed `Ice["skills"]` shape so the combat path's skill
 * branch (`state_actions_combat.ts` → `enemyShouldUseSkill`) is reachable.
 * Before the fix, `skillCooldowns` stayed `{}` for every ICE and the skill
 * logic was dead code.
 */
describe("data_loaders: ICE skills", () => {
  it("maps a known ICE's skills into the typed skill shape", async () => {
    const { default: data } = await import("../src/data/ice_types.json");
    const catalog = loadIceCatalog(data);
    const priest = catalog["loa_priest"];
    expect(priest).toBeDefined();
    if (priest === undefined) return;
    expect(priest.skills).toBeDefined();
    expect(priest.skills?.length).toBeGreaterThan(0);
    // `loa_priest` declares ["loa_summon", "spirit_guard"] in the JSON.
    expect(priest.skills?.map((s) => s.id)).toEqual([
      "loa_summon",
      "spirit_guard",
    ]);
    const summon = priest.skills?.[0];
    expect(summon).toBeDefined();
    if (summon === undefined) return;
    expect(summon.name).toBe("Loa Summon");
    expect(summon.effect).toBe("buff");
    expect(summon.cooldownMs).toBeGreaterThan(0);
    // A non-damaging effect must carry 0 damage: the combat path only fires a
    // skill when `damage > 0`, so a positive value would make a buff skill
    // deal hits it was never meant to.
    expect(summon.damage).toBe(0);
    const guard = priest.skills?.[1];
    expect(guard?.effect).toBe("shield");
    expect(guard?.damage).toBe(0);
  });

  it("gives an offensive ICE skill a positive damage derived from its own row", async () => {
    const { default: data } = await import("../src/data/ice_types.json");
    const catalog = loadIceCatalog(data);
    const guard = catalog["corporate_guard"];
    expect(guard).toBeDefined();
    if (guard === undefined) return;
    // `corporate_guard` declares ["scan", "report"]; "report" is offensive.
    const report = guard.skills?.find((s) => s.id === "report");
    expect(report).toBeDefined();
    if (report === undefined) return;
    expect(report.effect).toBe("attack");
    expect(report.damage).toBeGreaterThan(0);
    // The raw row declares dmg_base=4 — the skill damage is that own stat.
    const raw = (data as Record<string, { dmg_base?: number }>)["corporate_guard"];
    expect(report.damage).toBe(raw?.dmg_base);
  });

  it("maps the catalog's skill-bearing ICE types to match the JSON exactly", async () => {
    const { default: data } = await import("../src/data/ice_types.json");
    const raw = data as Record<string, { skills?: ReadonlyArray<string> }>;
    const catalog = loadIceCatalog(data);
    const jsonIdsWithSkills = Object.keys(raw).filter(
      (id) => (raw[id]?.skills ?? []).length > 0,
    );
    const catalogIdsWithSkills = Object.keys(catalog).filter(
      (id) => (catalog[id]?.skills ?? []).length > 0,
    );
    expect(jsonIdsWithSkills.length).toBeGreaterThan(0);
    expect(catalogIdsWithSkills.sort()).toEqual(jsonIdsWithSkills.sort());
    // Every declared skill id survives the mapping, in order.
    for (const id of jsonIdsWithSkills) {
      const declared = raw[id]?.skills ?? [];
      const mapped = catalog[id]?.skills ?? [];
      expect(mapped.map((s) => s.id)).toEqual([...declared]);
    }
  });

  it("omits the skills key entirely for ICE types that declare none", async () => {
    const { default: data } = await import("../src/data/ice_types.json");
    const catalog = loadIceCatalog(data);
    const watchdog = catalog["watchdog"];
    expect(watchdog).toBeDefined();
    if (watchdog === undefined) return;
    expect(watchdog.skills).toBeUndefined();
    expect("skills" in watchdog).toBe(false);
  });

  it("throws on a malformed skills entry", () => {
    expect(() =>
      parseIce({ name: "X", armor: 0, skills: [42] }, "x"),
    ).toThrow(/field 'skills' entries must be non-empty strings/);
    expect(() =>
      parseIce({ name: "X", armor: 0, skills: "loa_summon" }, "x"),
    ).toThrow(/field 'skills' must be an array when present/);
  });
});

/**
 * Regression: `parseIce` used to drop the ICE `personality` field entirely.
 *
 * `ice_types.json` authors a personality archetype for every ICE
 * (aggressive 80 / defensive 12 / stealth 5 / support 0), and `ice_ai.ts`
 * reads it through `coercePersonality`. Before the fix the loader never
 * copied the field, so every catalog ICE resolved to the "aggressive"
 * fallback and the whole archetype system (defensive shielding, stealth
 * alarm halving, support ally-targeting) was inert at runtime — the same
 * defect class as ADR-0216 (dropped `skills`).
 */
describe("data_loaders: ICE personality", () => {
  it("exposes the authored personality for a known non-aggressive ICE", async () => {
    const { default: data } = await import("../src/data/ice_types.json");
    const catalog = loadIceCatalog(data);
    const watchdog = catalog["watchdog"];
    expect(watchdog).toBeDefined();
    if (watchdog === undefined) return;
    expect(watchdog.personality).toBe("defensive");
    const wisp = catalog["wisp"];
    expect(wisp?.personality).toBe("stealth");
  });

  it("maps the catalog's personality distribution to match the JSON exactly", async () => {
    const { default: data } = await import("../src/data/ice_types.json");
    const raw = data as Record<string, { personality?: string }>;
    const catalog = loadIceCatalog(data);
    const jsonIds = Object.keys(raw).filter((id) => raw[id]?.personality !== undefined);
    const catalogIds = Object.keys(catalog).filter(
      (id) => catalog[id]?.personality !== undefined,
    );
    expect(jsonIds.length).toBeGreaterThan(0);
    expect(catalogIds.sort()).toEqual(jsonIds.sort());
    // Every authored personality survives the mapping, verbatim.
    for (const id of jsonIds) {
      expect(catalog[id]?.personality).toBe(raw[id]?.personality);
    }
    // The archetype system is inert unless non-aggressive ICE survive: the
    // distribution must carry at least one defensive and one stealth ICE.
    const personalities = catalogIds.map((id) => catalog[id]?.personality);
    expect(personalities.filter((p) => p === "defensive").length).toBeGreaterThan(0);
    expect(personalities.filter((p) => p === "stealth").length).toBeGreaterThan(0);
    expect(personalities.filter((p) => p === "aggressive").length).toBeGreaterThan(0);
  });

  it("omits the personality key entirely for an ICE that declares none", () => {
    const ice = parseIce({ name: "ICE — Legacy", tier: 1, armor: 0 }, "x");
    expect(ice.personality).toBeUndefined();
    expect("personality" in ice).toBe(false);
  });

  it("throws on a malformed personality value", () => {
    expect(() =>
      parseIce({ name: "ICE — X", armor: 0, personality: "evil" }, "x"),
    ).toThrow(/^\[data_loaders\]/);
    expect(() =>
      parseIce({ name: "ICE — X", armor: 0, personality: "evil" }, "x"),
    ).toThrow(/field 'personality' must be one of/);
    expect(() =>
      parseIce({ name: "ICE — X", armor: 0, personality: 42 }, "x"),
    ).toThrow(/field 'personality' must be one of/);
  });
});
