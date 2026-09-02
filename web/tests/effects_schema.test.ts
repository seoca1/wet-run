/** Effects schema validation (Tier 5.6, ADR-0210).
 *
 * Reads the exported effects.json + effects.d.ts (canonical source:
 * prototype/data/effects.json via scripts/export_effects.py). Verifies:
 * 1. Schema file is loadable
 * 2. All EffectKind values from the .d.ts file match kinds in effects.json
 * 3. Each kind has the expected required fields (kind, category, duration_ms,
 *    color_hint)
 * 4. duration_ticks ≈ ceil(duration_ms / 16) is consistent
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import effectsJson from "../src/data/effects.json";

const here = dirname(fileURLToPath(import.meta.url));
const effectsDts = readFileSync(resolve(here, "../src/data/effects.d.ts"), "utf-8");

interface EffectEntry {
  kind: string;
  category: string;
  description?: string;
  payload_shape?: Record<string, string>;
  duration_ms: number;
  color_hint: string;
  tier?: string;
}

const WEB_TICK_MS = 16;
const FILE_KIND_RE = /EFFECT_([A-Z_]+):\s*\{/g;

function parseEffectKindLiteral(dts: string): string[] {
  // Extract union of EffectKind from effects.d.ts (e.g. `"attack" | "heal" | ...`).
  const match = dts.match(/export type EffectKind = (.+?);/);
  if (!match) return [];
  return match[1]
    .split("|")
    .map((s) => s.trim().replace(/^"|"$/g, ""))
    .filter(Boolean);
}

function parseConstantKinds(dts: string): string[] {
  const out: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = FILE_KIND_RE.exec(dts)) !== null) {
    const raw = m[1] ?? "";
    out.push(raw.toLowerCase().replace(/_/g, "_"));
  }
  return out;
}

function camelToSnake(s: string): string {
  return s.replace(/([A-Z])/g, "_$1").toLowerCase().replace(/^_/, "");
}

describe("effects schema (Tier 5.6, ADR-0210)", () => {
  const schema = effectsJson as unknown as { _schema_version: string; effects: EffectEntry[] };

  it("has a valid _schema_version", () => {
    expect(typeof schema._schema_version).toBe("string");
    expect(schema._schema_version).toMatch(/^\d+\.\d+\.\d+$/);
  });

  it("has 27 v1+v2 effects (Tier 6 backport)", () => {
    expect(schema.effects.length).toBe(27);
    const v1 = schema.effects.filter((e) => e.tier === "v1").length;
    const v2 = schema.effects.filter((e) => e.tier === "v2").length;
    expect(v1).toBe(15);
    expect(v2).toBe(12);
  });

  it("kind names are unique", () => {
    const kinds = schema.effects.map((e) => e.kind);
    expect(new Set(kinds).size).toBe(kinds.length);
  });

  it("each entry has required fields", () => {
    for (const e of schema.effects) {
      expect(typeof e.kind).toBe("string");
      expect(e.kind.length).toBeGreaterThan(0);
      expect(typeof e.category).toBe("string");
      expect(e.category).toMatch(/^(combat|status|cinematic|outcome|matrix)/);
      expect(typeof e.duration_ms).toBe("number");
      expect(e.duration_ms).toBeGreaterThan(0);
      expect(typeof e.color_hint).toBe("string");
    }
  });

  it("EffectKind union in effects.d.ts matches JSON kinds", () => {
    const literal = parseEffectKindLiteral(effectsDts);
    const jsonKinds = schema.effects.map((e) => e.kind).sort();
    expect(literal.sort()).toEqual(jsonKinds);
  });

  it("EFFECT_* constants in effects.d.ts match JSON kinds", () => {
    const constants = parseConstantKinds(effectsDts).map(camelToSnake);
    const jsonKinds = schema.effects.map((e) => e.kind).sort();
    expect(constants.sort()).toEqual(jsonKinds);
  });

  it("duration_ticks in d.ts matches ceil(ms / 16)", () => {
    for (const e of schema.effects) {
      const expectedTicks = Math.ceil(e.duration_ms / WEB_TICK_MS);
      const re = new RegExp(`EFFECT_${e.kind.toUpperCase()}:[\\s\\S]*?duration_ticks: ${expectedTicks};`);
      expect(effectsDts).toMatch(re);
    }
  });

  it("critical_hit kind exists with payload damage + is_player_attacker", () => {
    const crit = schema.effects.find((e) => e.kind === "critical_hit");
    expect(crit).toBeDefined();
    expect(crit?.payload_shape?.damage).toBe("integer");
    expect(crit?.payload_shape?.is_player_attacker).toBe("boolean");
  });

  it("boss_phase_transition uses single kind + payloadNum (not 4 separate kinds)", () => {
    const boss = schema.effects.find((e) => e.kind === "boss_phase_transition");
    expect(boss).toBeDefined();
    expect(boss?.payload_shape?.boss_phase).toBe("integer[1..4]");
  });

  it("matrix.dungeon effects (jackin_glitch, jackout_whiteout, room_flash, data_acquired) are all v2", () => {
    const matrixEffects = schema.effects.filter((e) => e.category === "matrix.dungeon");
    expect(matrixEffects.length).toBe(4);
    expect(matrixEffects.every((e) => e.tier === "v2")).toBe(true);
    const matrixKinds = matrixEffects.map((e) => e.kind).sort();
    expect(matrixKinds).toEqual(["data_acquired", "jackin_glitch", "jackout_whiteout", "room_flash"]);
  });

  it("all v2 combat.skill effects backported from Python effects_vfx_animations.py", () => {
    const backportedSkills = ["heavy_attack", "pierce", "multi_hit", "dot",
      "counter", "lifesteal", "detect", "regen"];
    for (const skill of backportedSkills) {
      const found = schema.effects.find((e) => e.kind === skill);
      expect(found, `expected ${skill} in schema`).toBeDefined();
      expect(found?.category).toBe("combat.skill");
      expect(found?.tier).toBe("v2");
    }
  });

  it("color_hint values are all strings (Python palette key names)", () => {
    const allowedHints = new Set([
      "DAMAGE_COLOR", "HEAL_COLOR", "SHIELD_COLOR", "BUFF_COLOR", "DEBUFF_COLOR",
      "STUN_COLOR", "CRIT_COLOR", "ICE_BREAK_COLOR", "ICE_CYAN_DIM", "ICE_FADE_PURPLE",
      "ICE_GREEN_BRIGHT", "HIT_FLASH_COLOR", "ORANGE", "WARM", "OLIVE",
      "TIER_GOLD", "GREEN_NEON", "RED_BRIGHT", "DEFAULT_COLOR",
      "PHASE_COLOR_BY_INDEX",
    ]);
    for (const e of schema.effects) {
      expect(allowedHints.has(e.color_hint), `${e.kind} has unknown color_hint '${e.color_hint}'`).toBe(true);
    }
  });
});
