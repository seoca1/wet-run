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
}

function expectNumber(obj: Record<string, unknown>, key: string, ctx: string): number {
  const v = obj[key];
  if (typeof v !== "number" || !Number.isFinite(v)) {
    throw new Error(`[data_loaders] ${ctx}: field '${key}' must be a finite number (got ${typeof v}: ${String(v)})`);
  }
  return v;
}

function expectString(obj: Record<string, unknown>, key: string, ctx: string): string {
  const v = obj[key];
  if (typeof v !== "string" || v.length === 0) {
    throw new Error(`[data_loaders] ${ctx}: field '${key}' must be a non-empty string (got ${typeof v}: ${String(v)})`);
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
    throw new Error(`[data_loaders] mission '${id}': field 'rewards' must be an object`);
  }
  const credits = expectNumber(r.rewards as Record<string, unknown>, "credits", `mission '${id}'`);
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
      materials: (r.rewards as { materials?: Record<string, number> }).materials ?? {},
    },
    grade,
    seed,
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
    throw new Error(`[data_loaders] program '${name}' has both 'cost' and 'ap_cost'; choose one`);
  }
  const cost = r.cost ?? r.ap_cost;
  if (typeof cost !== "number" || !Number.isFinite(cost)) {
    throw new Error(`[data_loaders] program '${name}' requires 'cost' or 'ap_cost' as finite number`);
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

export function parseIce(raw: unknown, idHint: string): Ice {
  if (typeof raw !== "object" || raw === null) {
    throw new Error(`[data_loaders] ice '${idHint}' must be an object`);
  }
  const r = raw as LegacyIce & Record<string, unknown>;
  const name = expectString(r, "name", `ice '${idHint}'`);
  // defense (legacy) → armor (current). Throw if both set.
  if (typeof r.armor === "number" && typeof r.defense === "number") {
    throw new Error(`[data_loaders] ice '${name}' has both 'armor' and 'defense'; choose one`);
  }
  const armor = (r.armor ?? r.defense ?? 0) as number;
  if (typeof armor !== "number" || !Number.isFinite(armor)) {
    throw new Error(`[data_loaders] ice '${name}' requires 'armor' or 'defense' as finite number`);
  }
  const tier = typeof r.tier === "number" ? r.tier : 1;
  const hp = 100;
  return {
    id: idHint,
    name,
    armor,
    tier,
    hp,
  };
}

/** Load a missions JSON file. Throws on first malformed entry. */
export function loadMissionsCatalog(raw: unknown): ReadonlyArray<Mission> {
  if (typeof raw !== "object" || raw === null) {
    throw new Error("[data_loaders] missions JSON must be an object keyed by id");
  }
  return Object.entries(raw as Record<string, unknown>).map(([id, m]) => parseMission(m, id));
}

/** Load a programs JSON file into a Map. Throws on first malformed entry. */
export function loadProgramsCatalog(raw: unknown): Readonly<Record<string, Program>> {
  if (typeof raw !== "object" || raw === null) {
    throw new Error("[data_loaders] programs JSON must be an object keyed by id");
  }
  const out: Record<string, Program> = {};
  for (const [id, p] of Object.entries(raw as Record<string, unknown>)) {
    out[id] = parseProgram(p, id);
  }
  return out;
}

/** Load an ICE types JSON file into a Map. Throws on first malformed entry. */
export function loadIceCatalog(raw: unknown): Readonly<Record<string, Ice>> {
  if (typeof raw !== "object" || raw === null) {
    throw new Error("[data_loaders] ice types JSON must be an object keyed by id");
  }
  const out: Record<string, Ice> = {};
  for (const [id, ice] of Object.entries(raw as Record<string, unknown>)) {
    out[id] = parseIce(ice, id);
  }
  return out;
}
