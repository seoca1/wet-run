/** ICE skill metadata lookup.
 *
 * `ice_types.json` declares each ICE's skills as a list of **skill ids**
 * (e.g. `"skills": ["loa_summon", "spirit_guard"]`) and carries the
 * per-skill metadata in a sibling top-level `skill_defs` map:
 *
 * ```json
 * "skill_defs": {
 *   "loa_summon": { "name": "Loa Summon", "effect": "buff", "cooldown_ms": 4000 }
 * }
 * ```
 *
 * The loader expands each declared id into the typed
 * `{id, name, effect, cooldownMs, damage}` shape by looking the id up in
 * `skill_defs`. There is **no id → effect heuristic any more**: the
 * classification is authored data, so an id that is missing from the table
 * is a data bug and throws (ADR-0216 / ADR-0219 defect class — the loader
 * must not silently guess).
 *
 * ## Scope (ADR-0219 Option D)
 *
 * Option D authors the *classification* only. The **magnitude** of a
 * non-damaging effect (`shield` / `heal` / `regen` / `buff` / `debuff` /
 * `detect` / `stun` / `slow` / `silence`) is **not** authored here and no
 * effect mechanics are implemented — the combat path still only fires a
 * skill whose `damage > 0`. Implementing the effects is ADR-0219 Option A
 * and remains deferred.
 *
 * ## Damage semantics
 *
 * `damage` is **per-ICE, not per-skill**: it is the owning ICE row's own
 * `dmg_base` attack stat for offensive effects, and `0` for non-damaging
 * effects (which the combat path's `damage > 0` gate can never fire). It is
 * deliberately **not** part of `skill_defs` — the same skill id can belong to
 * ICE rows with different `dmg_base` values (e.g. `ice_pierce` is owned by
 * rows with `dmg_base` 12 and 15), so moving it into the table would change
 * behavior. The per-ICE derivation lives here, in the loader.
 *
 * Split out of `data_loaders.ts` (module-size guidance, ADR-0110 carry-over:
 * web TypeScript modules average 100-300 LOC).
 */
import type { Ice } from "./types.ts";

/** A single authored skill definition, read from `ice_types.json`'s
 * `skill_defs` map. */
export interface IceSkillDef {
  /** Human-readable display name (e.g. `"Loa Summon"`). */
  readonly name: string;
  /** Effect kind (e.g. `"buff"`, `"attack"`, `"shield"`). */
  readonly effect: string;
  /** Cooldown in milliseconds. */
  readonly cooldownMs: number;
  /** Effect magnitude (ADR-0219 Option A).
   *
   * Meaning depends on the effect:
   * - `shield` — HP the absorbing pool can still absorb
   * - `heal` — HP restored immediately
   * - `regen` — HP restored per enemy tick
   * - `buff` — flat outgoing damage bonus
   *
   * Absent for damaging effects, whose damage already comes from the
   * owning ICE row's `dmg_base`. */
  readonly magnitude?: number;
}

/** The authored `skill_defs` map: skill id → definition. */
export type IceSkillDefs = Readonly<Record<string, IceSkillDef>>;

/** Effects that deal no direct damage. The combat path only fires a skill
 * when `damage > 0`, so these stay at 0 and never fire — they exist so the
 * skill roster is complete (and so personality matching / the `stealth_only`
 * mutator filter have something to match on).
 *
 * The set stays here (not in `skill_defs`) because it is a *loader* rule
 * about how `damage` is derived, not per-skill data. */
const ICE_SKILL_NON_DAMAGE_EFFECTS: ReadonlySet<string> = new Set([
  "shield",
  "heal",
  "regen",
  "buff",
  "debuff",
  "detect",
  "stun",
  "slow",
  "silence",
]);

/** Validate the raw `skill_defs` table and normalize it into the typed map.
 *
 * Throws on a malformed entry (missing / wrong-typed field) rather than
 * coercing it — a silently-defaulted skill definition is the same defect
 * class ADR-0216 / ADR-0219 removed (the loader guessing instead of the
 * data declaring).
 *
 * @param raw - The raw `skill_defs` value from `ice_types.json`.
 * @param ctx - Context string for error messages (e.g. `"ice_types.json"`).
 */
export function parseIceSkillDefs(
  raw: unknown,
  ctx: string,
): IceSkillDefs {
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) {
    throw new Error(
      `[data_loaders] ${ctx}: field 'skill_defs' must be an object when present`,
    );
  }
  const out: Record<string, IceSkillDef> = {};
  for (const [id, value] of Object.entries(raw as Record<string, unknown>)) {
    if (typeof value !== "object" || value === null) {
      throw new Error(
        `[data_loaders] ${ctx}: skill_defs entry '${id}' must be an object (got ${typeof value}: ${String(value)})`,
      );
    }
    const r = value as Record<string, unknown>;
    const name = r["name"];
    if (typeof name !== "string" || name.length === 0) {
      throw new Error(
        `[data_loaders] ${ctx}: skill_defs entry '${id}': field 'name' must be a non-empty string (got ${typeof name}: ${String(name)})`,
      );
    }
    const effect = r["effect"];
    if (typeof effect !== "string" || effect.length === 0) {
      throw new Error(
        `[data_loaders] ${ctx}: skill_defs entry '${id}': field 'effect' must be a non-empty string (got ${typeof effect}: ${String(effect)})`,
      );
    }
    const cooldownMs = r["cooldown_ms"];
    if (typeof cooldownMs !== "number" || !Number.isFinite(cooldownMs)) {
      throw new Error(
        `[data_loaders] ${ctx}: skill_defs entry '${id}': field 'cooldown_ms' must be a finite number (got ${typeof cooldownMs}: ${String(cooldownMs)})`,
      );
    }
    const magnitude = r["magnitude"];
    if (magnitude !== undefined && (typeof magnitude !== "number" || !Number.isFinite(magnitude))) {
      throw new Error(
        `[data_loaders] ${ctx}: skill_defs entry '${id}': field 'magnitude' must be a finite number when present (got ${typeof magnitude}: ${String(magnitude)})`,
      );
    }
    out[id] = { name, effect, cooldownMs, ...(magnitude !== undefined ? { magnitude } : {}) };
  }
  return out;
}

/**
 * Parse the `skills` array of an ICE row into the typed skill shape.
 *
 * The JSON declares skills as bare id strings. Each id is expanded into
 * `{id, name, effect, cooldownMs, damage}`: the id is passed through
 * verbatim; `name` / `effect` / `cooldownMs` come from the authored
 * `skill_defs` table; and `damage` is the ICE row's own `dmg_base` attack
 * stat — or `0` for effects that deal no direct damage.
 *
 * An id that is declared on an ICE row but absent from `skill_defs` throws:
 * there is no heuristic fallback, because a silent guess is exactly the
 * defect class this lookup removes.
 *
 * Returns `undefined` when the row declares no skills, so the `skills` key is
 * omitted from the returned `Ice` entirely (matching the optional-field
 * spread style used for `hpBase` / `hpPerGrade`).
 *
 * @param raw - The raw `skills` value from an ICE row.
 * @param ctx - Context string for error messages (e.g. `"ice 'ICE — X'"`).
 * @param damageBase - The owning ICE row's `dmg_base` attack stat.
 * @param skillDefs - The authored `skill_defs` table.
 */
export function parseIceSkills(
  raw: unknown,
  ctx: string,
  damageBase: number,
  skillDefs: IceSkillDefs,
): Ice["skills"] | undefined {
  if (raw === undefined) return undefined;
  if (!Array.isArray(raw)) {
    throw new Error(
      `[data_loaders] ${ctx}: field 'skills' must be an array when present`,
    );
  }
  type IceSkill = NonNullable<Ice["skills"]>[number];
  const skills: IceSkill[] = [];
  for (const entry of raw) {
    if (typeof entry !== "string" || entry.length === 0) {
      throw new Error(
        `[data_loaders] ${ctx}: field 'skills' entries must be non-empty strings (got ${typeof entry}: ${String(entry)})`,
      );
    }
    const def = skillDefs[entry];
    if (def === undefined) {
      throw new Error(
        `[data_loaders] ${ctx}: unknown skill id '${entry}' — no entry in 'skill_defs'`,
      );
    }
    skills.push({
      id: entry,
      name: def.name,
      effect: def.effect,
      cooldownMs: def.cooldownMs,
      // Per-ICE damage: the owning row's own `dmg_base` for offensive effects,
      // 0 for non-damaging ones. Deliberately not authored per-skill — see the
      // module docstring.
      damage: ICE_SKILL_NON_DAMAGE_EFFECTS.has(def.effect) ? 0 : damageBase,
      // Effect magnitude (ADR-0219 Option A) is authored per skill and is
      // therefore the same for every owner of that skill id.
      ...(def.magnitude !== undefined ? { magnitude: def.magnitude } : {}),
    });
  }
  return skills.length > 0 ? skills : undefined;
}
