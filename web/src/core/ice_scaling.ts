/** Grade-driven ICE scaling — shared by the live combat path and the balance harness.
 *
 * `ice_types.json` carries `hp_base` + `hp_per_grade` per ICE; effective HP for a
 * mission grade is `hp_base + hp_per_grade * (grade - 1)`. The encounter ICE id
 * is chosen from a per-grade band (3-4 ids) so the 97-type catalog actually
 * appears in play instead of always falling on a single tier-1 watchdog.
 * Pick is deterministic by `(grade, seed)`: a numeric `seed` selects via
 * `Math.abs(seed) % band.length`; omitting the seed pins index 0 so existing
 * callers and tests that do not pass a seed still see the legacy first id of
 * the band (watchdog @ grade 1, spider @ grade 2, black @ grade 3, goliath @
 * grade 4, neuromancer @ grade 5/6). Both fall back to safe defaults
 * (`watchdog` / `ice.hp`) for legacy rows that omit the fields.
 *
 * HP cap stays a single grade curve: `iceHpForGrade` clamps every band id to
 * the same per-grade ceiling, so the chosen id never raises HP above the
 * calibrated budget — only flavor (skills, dmg_base, speed, resistance) varies.
 * Per-grade ICE auto-attack bonus (`ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`,
 * applied in `state_actions_combat.ts`) lifts early-game tension where the
 * HP cap is no-op (tier-1/2 natural HP is below cap).
 */
import type { Ice } from "./types.ts";

/** Per-grade encounter bands.
 *
 * Each entry lists Gibson/Sprawl-flavored ids drawn from `ice_types.json`.
 * The first id of each band matches the legacy fixed-id behavior so callers
 * that omit a seed stay backward compatible. Boss rooms do NOT use this table
 * — `dungeon.ts` keeps the wintermute pinning for exit rooms.
 */
export const ENCOUNTER_ICE_BY_GRADE: Readonly<Record<number, ReadonlyArray<string>>> = {
  1: ["watchdog", "spider", "wisp", "zombie"],
  2: ["spider", "raven", "surveillance", "chinese_ice"],
  3: ["black", "goliath", "raven", "ai_whisper"],
  4: ["goliath", "ai_whisper", "hellhound", "morrison_echo"],
  5: ["neuromancer", "revelation", "loa_entity", "hellhound"],
  6: ["neuromancer", "wintermute", "ice_neuromancer_warden", "aleph"],
};

export function clampGrade(grade: number): number {
  const g = Number.isFinite(grade) ? Math.round(grade) : 1;
  return Math.max(1, Math.min(6, g));
}

/** Pick the encounter ICE id for a mission grade.
 *
 * When `seed` is `undefined`, returns the first id of the band (legacy
 * behavior, matches the original fixed-id table). When `seed` is a finite
 * number, returns `band[Math.abs(seed) % band.length]` — deterministic across
 * runs and independent of the date used elsewhere.
 *
 * Boss rooms are not routed through this function; callers gate on
 * `node.isBoss` and pin `wintermute` directly.
 */
export function encounterIceIdForGrade(grade: number, seed?: number): string {
  const band = ENCOUNTER_ICE_BY_GRADE[clampGrade(grade)];
  if (band === undefined || band.length === 0) return "watchdog";
  if (seed === undefined || !Number.isFinite(seed)) {
    return band[0] ?? "watchdog";
  }
  const idx = Math.abs(Math.trunc(seed)) % band.length;
  return band[idx] ?? "watchdog";
}

/** Encounter HP curve by grade (index = grade - 1).
 *
 * Per-grade MAX (cap) HP. `iceHpForGrade` raises any natural `hp_base +
 * hp_per_grade * (grade - 1)` value to this ceiling so a mis-tuned
 * `ice_types.json` row cannot push the cap past the calibrated budget.
 * Set BELOW the natural tier-3/4 row (e.g. 140 at g3) so the cap actively
 * trims tier-3+ ICE that would otherwise one-shot the opener at low grades.
 *
 * Calibrated (ADR-0211 fun-fix + follow-up, --runs 100 evidence). With these
 * caps:
 *   - opener g1 100% (saturated — tier-1 ICE has dataHp < cap so cap
 *     irrelevant; the dmg bonus in `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`
 *     does the actual tension lift);
 *   - opener g2 88.8% (HP cap-as-MAX is irrelevant for tier-1/2 ICE whose
 *     dataHp is below cap; tension comes from dmg bonus);
 *   - opener g3 73%, g4 47.4% (cap actually trims natural tier-3+ data);
 *   - opener g5 42.4%, g6 0% (cap holds the climax unreachable for opener);
 *   - PPL g5 44.4%, g6 31.3% (the g6 dmg penalty below keeps the climax
 *     attainable for a developed deck while the opener still flatlines).
 */
const ENCOUNTER_HP_BY_GRADE: ReadonlyArray<number> = [
  75, 125, 140, 165, 165, 165,
];

/** Per-grade ICE auto-attack bonus (percentage added to the base `tier * 3 +
 * armor` formula). Index = grade - 1.
 *
 * Pairs with `ENCOUNTER_HP_BY_GRADE`: HP cap creates contest at g3+ (where
 * tier-3+ ICE has natural HP > cap), and this dmg bonus creates contest at
 * g1-g2 (where tier-1/2 ICE natural HP < cap so the cap is a no-op — the
 * opener annihilates the ICE in 3-4 turns before any dmg matters). The
 * opener base dmg (program.tier * 5) is fixed, so the only knob to lengthen
 * early-grade combat is to push ICE dmg up.
 *
 * **Boss rooms (bossPhase > 0) skip this bonus** in
 * `state_actions_combat.ts`: boss encounter tension is already carried by
 * the phase multipliers (1.25x / 1.5x / 2x for phases 2/3/4), and stacking
 * the per-grade bonus would push phase-specific dmg expectations out of
 * the boss_ai test contracts. Boss ICE always uses the raw `tier * 3 +
 * armor` baseline.
 *
 * Calibrated (ADR-0211 fun-fix + follow-up, --runs 100 evidence):
 *   - opener g1 100% — tier-1 ICE deals 4*1.5=6 dmg/tick at +50%; ICE still
 *     dies in 2.5 turns before mattering;
 *   - opener g2 88.8% — tier-2 ICE deals 9*2.3≈21 dmg/tick at +130%; 4 turns
 *     of combat push the player from 100 HP down to ~36, and crit variance
 *     tips ~11% of runs into a loss;
 *   - opener g3-g5 unchanged — cap carries tension; high-tier ICE base dmg
 *     already exceeds what the opener can sustain.
 *   - g6 -20% — the g6 band (neuromancer / wintermute / warden / aleph) is
 *     the tankiest + hardest-hitting set, so at the g5/g6 HP cap (165) the
 *     developed deck flatlined (0%). A -20% ICE auto-attack penalty makes the
 *     climax attainable (PPL g6 31.3%) without touching the opener (still 0%)
 *     or the boss rooms (bonus skipped when bossPhase > 0). The knob is
 *     deliberately negative here — the guard in `state_actions_combat.ts`
 *     applies any non-zero value, so a grade can reduce ICE damage as well as
 *     raise it.
 *
 * PPL interaction: the +130 at g2 also tips PPL g2 from 100% to 72.3% (the
 * PPL g2→g3 curve is not monotonic). That drift is a **deck** artifact, not
 * ICE tuning: `deckForGrade` fields only tier<=2 cards at g2 (all weak) but
 * jumps to tier-3 payload/exploit/goliath at g3, so the PPL deck is stronger
 * at g3 than g2. Closing it would require either a deck-definition change or
 * pushing the opening g2 above its 80-95% target (both curves move together
 * under any ICE knob), i.e. a mechanics change — out of scope here. The
 * primary **opening-deck** curve stays monotonic non-increasing.
 */
const ENCOUNTER_DMG_BONUS_PCT_BY_GRADE: ReadonlyArray<number> = [
  50, 130, 0, 0, 0, -20,
];

export function iceDmgBonusPctForGrade(grade: number): number {
  const idx = clampGrade(grade) - 1;
  return ENCOUNTER_DMG_BONUS_PCT_BY_GRADE[idx] ?? 0;
}

export function iceHpForGrade(ice: Ice, grade: number): number {
  const g = clampGrade(grade);
  const base = ice.hpBase;
  const perGrade = ice.hpPerGrade;
  const dataHp =
    base !== undefined && perGrade !== undefined
      ? base + perGrade * (g - 1)
      : Number.isFinite(ice.hp)
        ? ice.hp
        : 100;
  const cap = ENCOUNTER_HP_BY_GRADE[g - 1];
  return cap !== undefined ? Math.min(dataHp, cap) : dataHp;
}

export function missionGradeOf(mission: {
  readonly grade?: number;
  readonly grade_max?: number;
  readonly grade_min?: number;
}): number {
  return mission.grade_max ?? mission.grade_min ?? mission.grade ?? 1;
}

/** Resolve the seed the matrix generator uses for a mission.
 *
 * Mirrors the precedence applied by `state.ts` (`matrix_seed` first, then
 * `seed`, then a fixed default) so dungeon determinism propagates to the
 * encounter ICE pick: the same mission always faces the same ICE.
 */
export function missionSeedOf(mission: {
  readonly seed?: number;
  readonly matrix_seed?: number;
}): number {
  return (mission as { matrix_seed?: number }).matrix_seed ?? mission.seed ?? 42;
}
