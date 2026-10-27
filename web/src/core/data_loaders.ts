/** Runtime data loaders — schema validation at the data boundary.
 *
 * The static JSON files in `web/src/data/` are hand-maintained (the Python
 * prototype export pipeline was retired 2026-09-15; see web/README.md).
 * Some retain the legacy snake_case schema (`matrix_seed`, `grade_max`, `ap_cost`, `defense`)
 * while the TS code reads camelCase (`seed`, `grade`, `cost`, `armor`).
 *
 * These loaders enforce the schema at module load time:
 * - Validate required fields exist and have correct types.
 * - Normalize legacy field names (`ap_cost` → `cost`, `defense` → `armor`).
 * - Throw on malformed entries instead of silently producing NaN at runtime.
 *
 * No new dependencies — pure type-guard validation.
 */
import {
  parseIceSkills,
  parseIceSkillDefs,
  type IceSkillDefs,
} from "./ice_skills.ts";
import type { Mission, Program, Ice } from "./types.ts";

interface LegacyMission {
  id?: string;
  title?: string;
  matrix_seed?: number;
  seed?: number;
  grade_max?: number;
  grade_min?: number;
  grade?: number;
  zone?: string;
  fixer?: string;
  arc?: number;
  source_universe?: "sprawl" | "far-grid";
  story?: { source?: string; title?: string };
  briefing?: string;
  title_ko?: string;
  briefing_ko?: string;
  rewards?: { credits?: number; materials?: Record<string, number> };
}

interface LegacyProgram {
  id?: string;
  name?: string;
  tier?: number;
  cost?: number;
  ap_cost?: number;
  effect?: string;
  description?: string;
  aoe?: boolean;
}

interface LegacyIce {
  id?: string;
  name?: string;
  hp?: number;
  armor?: number;
  defense?: number;
  tier?: number;
  dmg_base?: number;
  skills?: ReadonlyArray<string>;
  personality?: string;
  aggression?: string;
}

/** Valid ICE personality archetypes (`Ice["personality"]`). */
const VALID_ICE_PERSONALITY: ReadonlySet<string> = new Set([
  "aggressive",
  "defensive",
  "stealth",
  "support",
]);

/** Valid ICE aggression tiers (`Ice["aggression"]`). */
const VALID_ICE_AGGRESSION: ReadonlySet<string> = new Set([
  "passive",
  "standard",
  "aggressive",
  "boss",
]);

function expectNumber(
  obj: Record<string, unknown>,
  key: string,
  ctx: string,
): number {
  const v = obj[key];
  if (typeof v !== "number" || !Number.isFinite(v)) {
    throw new Error(
      `[data_loaders] ${ctx}: field '${key}' must be a finite number (got ${typeof v}: ${String(v)})`,
    );
  }
  return v;
}

function expectString(
  obj: Record<string, unknown>,
  key: string,
  ctx: string,
): string {
  const v = obj[key];
  if (typeof v !== "string" || v.length === 0) {
    throw new Error(
      `[data_loaders] ${ctx}: field '${key}' must be a non-empty string (got ${typeof v}: ${String(v)})`,
    );
  }
  return v;
}

export function parseMission(raw: unknown, idHint: string): Mission {
  if (typeof raw !== "object" || raw === null) {
    throw new Error(`[data_loaders] mission '${idHint}' must be an object`);
  }
  const r = raw as LegacyMission & Record<string, unknown>;
  const id = expectString(r, "id", `mission '${idHint}'`);
  const title = expectString(r, "title", `mission '${id}'`);
  const fixer = expectString(r, "fixer", `mission '${id}'`);
  const arc = expectNumber(r, "arc", `mission '${id}'`);
  const grade_min = expectNumber(r, "grade_min", `mission '${id}'`);
  const grade_max = expectNumber(r, "grade_max", `mission '${id}'`);
  // mission.seed/grade are optional in Mission type but always present after normalization
  const seed = (r.matrix_seed ?? r.seed ?? 0) as number;
  const grade = (r.grade_max ?? r.grade_min ?? r.grade ?? 1) as number;
  if (!r.rewards || typeof r.rewards !== "object") {
    throw new Error(
      `[data_loaders] mission '${id}': field 'rewards' must be an object`,
    );
  }
  const credits = expectNumber(
    r.rewards as Record<string, unknown>,
    "credits",
    `mission '${id}'`,
  );
  // source_universe is optional in JSON; absent means "sprawl" (ADR-0213)
  const source_universe = r.source_universe ?? "sprawl";
  if (source_universe !== "sprawl" && source_universe !== "far-grid") {
    throw new Error(
      `[data_loaders] mission '${id}': field 'source_universe' must be "sprawl" or "far-grid" (got ${JSON.stringify(r.source_universe)})`,
    );
  }
  // story is optional display-only metadata (ADR-0213); never resolved at runtime
  let story: Mission["story"] = undefined;
  if (r.story !== undefined) {
    if (typeof r.story !== "object" || r.story === null) {
      throw new Error(
        `[data_loaders] mission '${id}': field 'story' must be an object when present`,
      );
    }
    const sRaw = r.story as { source?: unknown; title?: unknown };
    if (typeof sRaw.source !== "string" || sRaw.source.length === 0) {
      throw new Error(
        `[data_loaders] mission '${id}': field 'story.source' must be a non-empty string`,
      );
    }
    story = {
      source: sRaw.source,
      ...(typeof sRaw.title === "string" ? { title: sRaw.title } : {}),
    };
  }
  // briefing is an optional display-only string (ADR-0213 Wave 2). When present it
  // MUST be a non-empty string; absent or empty string is treated as "no briefing"
  // and the field is omitted from the returned Mission (matches the optional typing).
  let briefing: Mission["briefing"];
  if (r.briefing !== undefined) {
    if (typeof r.briefing !== "string") {
      throw new Error(
        `[data_loaders] mission '${id}': field 'briefing' must be a string when present (got ${typeof r.briefing})`,
      );
    }
    const trimmed = r.briefing.trim();
    if (trimmed.length > 0) {
      briefing = trimmed;
    }
  }
  // title_ko is an optional display-only Korean translation of `title` (KO
  // content activation follow-up). Empty string is treated as "absent"; any
  // non-empty value passes through verbatim (no script validation here —
  // CJK contamination is enforced by tests/audit script, not at module load).
  let title_ko: Mission["title_ko"];
  if (typeof r.title_ko === "string" && r.title_ko.trim().length > 0) {
    title_ko = r.title_ko.trim();
  }
  // briefing_ko is the Korean translation of `briefing` (same conventions as
  // `briefing` itself — non-empty string passes through, empty/missing is
  // omitted).
  let briefing_ko: Mission["briefing_ko"];
  if (typeof r.briefing_ko === "string" && r.briefing_ko.trim().length > 0) {
    briefing_ko = r.briefing_ko.trim();
  }
  return {
    id,
    title,
    fixer,
    arc,
    zone: (r.zone as string) ?? "surface",
    grade_min,
    grade_max,
    rewards: {
      credits,
      materials:
        (r.rewards as { materials?: Record<string, number> }).materials ?? {},
    },
    grade,
    seed,
    source_universe,
    story,
    ...(briefing !== undefined ? { briefing } : {}),
    ...(title_ko !== undefined ? { title_ko } : {}),
    ...(briefing_ko !== undefined ? { briefing_ko } : {}),
  };
}

export function parseProgram(raw: unknown, idHint: string): Program {
  if (typeof raw !== "object" || raw === null) {
    throw new Error(`[data_loaders] program '${idHint}' must be an object`);
  }
  const r = raw as LegacyProgram & Record<string, unknown>;
  const name = expectString(r, "name", `program '${idHint}'`);
  const tier = expectNumber(r, "tier", `program '${name}'`);
  // ap_cost (legacy) → cost (current). Both must not be set simultaneously.
  if (typeof r.cost === "number" && typeof r.ap_cost === "number") {
    throw new Error(
      `[data_loaders] program '${name}' has both 'cost' and 'ap_cost'; choose one`,
    );
  }
  const cost = r.cost ?? r.ap_cost;
  if (typeof cost !== "number" || !Number.isFinite(cost)) {
    throw new Error(
      `[data_loaders] program '${name}' requires 'cost' or 'ap_cost' as finite number`,
    );
  }
  const description = typeof r.description === "string" ? r.description : "";
  const effect = typeof r.effect === "string" ? r.effect : "attack";
  const aoe = r.aoe === true;
  return {
    id: idHint,
    name,
    tier,
    cost,
    effect,
    description,
    aoe,
  };
}

/** Default grade used to derive the static `hp` field when `hp_base` +
 * `hp_per_grade` are present in the JSON (ADR-0211 Option 2). The HP curve
 * itself is computed at runtime via `iceHpForGrade()` from `ice_scaling.ts`
 * using the mission's actual grade; this constant only seeds the loader's
 * fallback so the static `hp` field is non-arbitrary (e.g. a watchdog at
 * grade 1 has hp=50, not 100). */
const PARSE_ICE_DEFAULT_GRADE = 1;

/** Default fallback HP for legacy rows that omit both `hp_base` and
 * `hp_per_grade`. Matches the legacy `parseIce` behavior pinned by
 * `tests/data_loaders.test.ts:234` (`expect(ice.hp).toBeGreaterThan(0)`). */
const PARSE_ICE_LEGACY_HP = 100;

export function parseIce(
  raw: unknown,
  idHint: string,
  skillDefs: IceSkillDefs = {},
): Ice {
  if (typeof raw !== "object" || raw === null) {
    throw new Error(`[data_loaders] ice '${idHint}' must be an object`);
  }
  const r = raw as LegacyIce & Record<string, unknown>;
  const name = expectString(r, "name", `ice '${idHint}'`);
  // defense (legacy) → armor (current). Throw if both set.
  if (typeof r.armor === "number" && typeof r.defense === "number") {
    throw new Error(
      `[data_loaders] ice '${name}' has both 'armor' and 'defense'; choose one`,
    );
  }
  const armor = (r.armor ?? r.defense ?? 0) as number;
  if (typeof armor !== "number" || !Number.isFinite(armor)) {
    throw new Error(
      `[data_loaders] ice '${name}' requires 'armor' or 'defense' as finite number`,
    );
  }
  const tier = typeof r.tier === "number" ? r.tier : 1;
  const hpBase = typeof r.hp_base === "number" ? r.hp_base : undefined;
  const hpPerGrade =
    typeof r.hp_per_grade === "number" ? r.hp_per_grade : undefined;
  // ADR-0211 Option 2: derive `hp` from `hp_base` + `hp_per_grade` when both are
  // available so the field is non-arbitrary and aligned with the runtime
  // `iceHpForGrade` curve. Fall back to the legacy 100 default when grade data
  // is missing (preserves `tests/data_loaders.test.ts:234` pinning).
  const hp =
    hpBase !== undefined && hpPerGrade !== undefined
      ? hpBase + hpPerGrade * Math.max(0, PARSE_ICE_DEFAULT_GRADE - 1)
      : PARSE_ICE_LEGACY_HP;
  const dmgBase = typeof r.dmg_base === "number" ? r.dmg_base : 0;
  const skills = parseIceSkills(r.skills, `ice '${name}'`, dmgBase, skillDefs);
  // `personality` drives the archetype system (`ice_ai.ts`): defensive ICE
  // shield below half HP, stealth ICE halves the alarm tick rate, aggressive
  // ICE gains crit chance, support ICE targets wounded allies. It is dropped
  // silently when absent (the field is optional and `coercePersonality` falls
  // back to "aggressive"), but a malformed value is a data bug — throw rather
  // than coerce (ADR-0216 defect class).
  let personality: Ice["personality"];
  if (r.personality !== undefined) {
    if (
      typeof r.personality !== "string" ||
      !VALID_ICE_PERSONALITY.has(r.personality)
    ) {
      throw new Error(
        `[data_loaders] ice '${name}': field 'personality' must be one of ${[...VALID_ICE_PERSONALITY].join(", ")} (got ${JSON.stringify(r.personality)})`,
      );
    }
    personality = r.personality as Ice["personality"];
  }
  // `aggression` drives the per-tick skill-use probability (`ice_ai.ts`):
  // `enemyShouldUseSkill` reads it through `coerceAggression` and maps it
  // onto `AGGRESSION_PROBABILITY` (passive 0.05 / standard 0.15 /
  // aggressive 0.35 / boss 0.5). It is dropped silently when absent (the
  // field is optional and `coerceAggression` falls back to "standard"), but a
  // malformed value is a data bug — throw rather than coerce (ADR-0216 /
  // ADR-0220 defect class).
  let aggression: Ice["aggression"];
  if (r.aggression !== undefined) {
    if (
      typeof r.aggression !== "string" ||
      !VALID_ICE_AGGRESSION.has(r.aggression)
    ) {
      throw new Error(
        `[data_loaders] ice '${name}': field 'aggression' must be one of ${[...VALID_ICE_AGGRESSION].join(", ")} (got ${JSON.stringify(r.aggression)})`,
      );
    }
    aggression = r.aggression as Ice["aggression"];
  }
  return {
    id: idHint,
    name,
    armor,
    tier,
    hp,
    ...(hpBase !== undefined ? { hpBase } : {}),
    ...(hpPerGrade !== undefined ? { hpPerGrade } : {}),
    ...(skills !== undefined ? { skills } : {}),
    ...(personality !== undefined ? { personality } : {}),
    ...(aggression !== undefined ? { aggression } : {}),
  };
}

/** Load a missions JSON file. Throws on first malformed entry. */
export function loadMissionsCatalog(raw: unknown): ReadonlyArray<Mission> {
  if (typeof raw !== "object" || raw === null) {
    throw new Error(
      "[data_loaders] missions JSON must be an object keyed by id",
    );
  }
  return Object.entries(raw as Record<string, unknown>).map(([id, m]) =>
    parseMission(m, id),
  );
}

/** Load a programs JSON file into a Map. Throws on first malformed entry. */
export function loadProgramsCatalog(
  raw: unknown,
): Readonly<Record<string, Program>> {
  if (typeof raw !== "object" || raw === null) {
    throw new Error(
      "[data_loaders] programs JSON must be an object keyed by id",
    );
  }
  const out: Record<string, Program> = {};
  for (const [id, p] of Object.entries(raw as Record<string, unknown>)) {
    out[id] = parseProgram(p, id);
  }
  return out;
}

/** Top-level key of `ice_types.json` that holds the authored skill table
 * rather than an ICE row. `loadIceCatalog` skips it. */
const ICE_SKILL_DEFS_KEY = "skill_defs";

/** Load an ICE types JSON file into a Map. Throws on first malformed entry.
 *
 * The JSON's top-level map holds the ICE rows plus one non-ICE key,
 * `skill_defs` — the authored per-skill metadata table (ADR-0219 Option D).
 * That key is consumed here and skipped when the ICE rows are parsed.
 */
export function loadIceCatalog(raw: unknown): Readonly<Record<string, Ice>> {
  if (typeof raw !== "object" || raw === null) {
    throw new Error(
      "[data_loaders] ice types JSON must be an object keyed by id",
    );
  }
  const entries = Object.entries(raw as Record<string, unknown>);
  const skillDefs = parseIceSkillDefs(
    entries.find(([id]) => id === ICE_SKILL_DEFS_KEY)?.[1] ?? {},
    "ice_types.json",
  );
  const out: Record<string, Ice> = {};
  for (const [id, ice] of entries) {
    if (id === ICE_SKILL_DEFS_KEY) continue;
    out[id] = parseIce(ice, id, skillDefs);
  }
  return out;
}
