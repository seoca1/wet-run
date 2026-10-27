/** ICE skill effect derivation.
 *
 * `ice_types.json` declares each ICE's skills as a list of **skill ids**
 * (e.g. `"skills": ["loa_summon", "spirit_guard"]`) — the JSON carries no
 * per-skill metadata, and no skill catalog exists in the repo (the retired
 * Python prototype resolved ids against the *program* registry, which matched
 * only 2 of the 88 ids). The loader therefore derives the typed
 * `{id, name, effect, cooldownMs, damage}` shape from the id itself plus the
 * owning ICE row's own attack stat.
 *
 * Matching is per snake_case token (prefix-tolerant so `corruption` matches
 * `corrupt`), never per raw substring — substring matching mis-derived
 * `enforce_contract` as a multi-hit because "enforce" contains "force".
 * Rules are ordered and first-match-wins; `attack` is the fallback.
 *
 * Split out of `data_loaders.ts` (module-size guidance, ADR-0110 carry-over:
 * web TypeScript modules average 100-300 LOC). The derivation rules, ordering,
 * cooldown default and non-damage effect set are unchanged — this is a pure
 * move.
 */
import type { Ice } from "./types.ts";

const ICE_SKILL_EFFECT_RULES: ReadonlyArray<
  readonly [ReadonlyArray<string>, string]
> = [
  [["absorb", "shield", "defense", "fortress", "vault", "guard"], "shield"],
  [["curse", "voodoo"], "poison"],
  [
    ["plague", "poison", "corrupt", "pollution", "melt", "overload", "biofeedback"],
    "dot",
  ],
  [["lock"], "silence"],
  [["stub"], "slow"],
  [["stun", "system", "stack", "glitch", "timeline"], "stun"],
  [["heal", "preserve"], "heal"],
  [["regen", "resilience"], "regen"],
  [["scan", "trace", "vision", "intel"], "detect"],
  [["pierce", "penetrating"], "pierce"],
  [["strike", "brute", "brutal", "force", "datamine"], "multi_hit"],
  [["critical", "siege", "domin"], "heavy_attack"],
  [["debt", "possession", "random"], "debuff"],
  [
    [
      "summon",
      "manifest",
      "evolution",
      "proxy",
      "construct",
      "negotiate",
      "subversion",
      "distortion",
      "warp",
      "territory",
      "mark",
      "aleph",
      "family",
    ],
    "buff",
  ],
];

/** Effects that deal no direct damage. The combat path only fires a skill
 * when `damage > 0`, so these stay at 0 and never fire — they exist so the
 * skill roster is complete (and so personality matching / the `stealth_only`
 * mutator filter have something to match on). */
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

/** Default ICE skill cooldown (ms). Two auto-attack intervals, so an ICE that
 * rolls a skill fires it at most on every other auto-attack tick. */
const ICE_SKILL_COOLDOWN_MS = 4000;

/** Derive a skill's effect kind from its id (`"attack"` when unmatched). */
function iceSkillEffectFor(skillId: string): string {
  const tokens = skillId.split("_");
  for (const [keywords, effect] of ICE_SKILL_EFFECT_RULES) {
    for (const token of tokens) {
      for (const keyword of keywords) {
        if (token.startsWith(keyword)) return effect;
      }
    }
  }
  return "attack";
}

/** Humanize a skill id for display: `loa_summon` → `Loa Summon`. */
function iceSkillNameFor(skillId: string): string {
  return skillId
    .split("_")
    .filter((part) => part.length > 0)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

/**
 * Parse the `skills` array of an ICE row into the typed skill shape.
 *
 * The JSON declares skills as bare id strings. Each id is expanded into
 * `{id, name, effect, cooldownMs, damage}`: the id is passed through
 * verbatim, the name is humanized, the effect is derived from the id
 * keywords (`iceSkillEffectFor`), the cooldown is the shared default, and
 * the damage is the ICE row's own `dmg_base` attack stat — or 0 for effects
 * that deal no direct damage.
 *
 * Returns `undefined` when the row declares no skills, so the `skills` key is
 * omitted from the returned `Ice` entirely (matching the optional-field
 * spread style used for `hpBase` / `hpPerGrade`).
 */
export function parseIceSkills(
  raw: unknown,
  ctx: string,
  damageBase: number,
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
    const effect = iceSkillEffectFor(entry);
    skills.push({
      id: entry,
      name: iceSkillNameFor(entry),
      effect,
      cooldownMs: ICE_SKILL_COOLDOWN_MS,
      damage: ICE_SKILL_NON_DAMAGE_EFFECTS.has(effect) ? 0 : damageBase,
    });
  }
  return skills.length > 0 ? skills : undefined;
}
