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
 *
 * **ADR-0229 — the grade curve is re-baselined (2026-10-29).** The two
 * calibration constants below now describe the **baseline**, not a set of
 * targets to be chased. ADR-0211's per-grade win-rate targets (g2 88.8 /
 * g3 73.0 / g4 47.4 / g5 42.4) are **superseded** — the baseline is the
 * curve the engine actually achieves today:
 *
 *   | grade | opening baseline | PPL reference |
 *   | --- | --- | --- |
 *   | g1 | 100.0% | 100.0% |
 *   | g2 | 88.6% | 77.9% |
 *   | g3 | 73.1% | 99.6% |
 *   | g4 | 39.3% | 84.8% |
 *   | g5 | 35.7% | 44.4% |
 *   | g6 | 0.0% | 28.3% |
 *
 * (opening = `npm run balance`, 100 runs/mission; PPL = `npm run balance --
 * --deck ppl`. The opening curve is monotonic non-increasing; the PPL curve
 * is **not** — that is a deck artifact, and PPL is a *reference*, not a
 * target.)
 *
 * Why the re-baseline happened: four successive feature steps each moved the
 * ADR-0211-calibrated curve, and the two global levers could not always
 * restore it — ADR-0224 (band expansion) g2 −11.4pp / g3 +6.0pp / g5
 * −10.4pp; ADR-0226 (skill effects implemented) g4 +0.2pp; ADR-0227
 * (archetype data) g3 +16.6pp; ADR-0228 (crit wired) g4 −9.7pp / g5 −7.4pp.
 * The levers are step functions with cliffs (the auto-attack bonus floors
 * `floor((tier * 3 + armor) * (1 + pct / 100))`; the g3 HP cap is bounded by
 * `c3 <= c4`), so the reachable grades are discrete and chasing a moved
 * target per feature was churn. The engine's difficulty genuinely changed —
 * the ICE systems are now real — so the curve was re-baselined once.
 *
 * **The mechanisms stay in force.** ADR-0211 is superseded only for its
 * per-grade win-rate numbers. Its *mechanisms* — the HP cap, the damage
 * bonus curve, and the grade-driven encounter scaling — remain the design.
 *
 * **Drift policy (ADR-0229).** (a) a change that moves any opening grade by
 * more than ±3pp from this baseline must EITHER recalibrate back OR
 * explicitly re-baseline in its own ADR — no silent drift; (b) the
 * invariants are hard: the opening curve stays monotonic non-increasing,
 * g6 stays at (or near) 0, and the HP-cap array stays monotonically
 * non-decreasing; (c) the PPL curve is a *reference*, not a target, and any
 * PPL movement must be stated in the change's ADR.
 *
 * **Encounter band coverage (ADR-0219 "remaining gap (4)" — encounter band
 * 커버리지 확대).** The band is also the *reach* surface for the ICE skill
 * and personality systems: the 97-row catalog has 44 skill-bearing ICE, but
 * the band previously listed only 2 of them (`loa_entity` @ g5, `aleph` @ g6),
 * both `aggressive` — so the skill metadata authored by ADR-0222 / corrected
 * by ADR-0223 and the personality archetypes of ADR-0161 were unobservable in
 * play. Slots 1-3 of every grade now list tier-appropriate ICE that carries
 * skills, and every grade lists at least one non-`aggressive` ICE, so the
 * archetype preference lists actually have something to match against.
 *
 * Slot 0 of every band stays **immutable**: `encounterIceIdForGrade(grade)`
 * with no seed keeps returning `band[0]` (the legacy fixed-id behavior the
 * original table pinned — watchdog @ g1, spider @ g2, black @ g3, goliath @
 * g4, neuromancer @ g5/g6). Only slots 1-3 (the seed-rotated ones) changed.
 */
import type { Ice } from "./types.ts";

/** Per-grade encounter bands.
 *
 * Each entry lists Gibson/Sprawl-flavored ids drawn from `ice_types.json`.
 * The first id of each band matches the legacy fixed-id behavior so callers
 * that omit a seed stay backward compatible — **slot 0 is immutable**.
 * Boss rooms do NOT use this table — `dungeon.ts` keeps the wintermute
 * pinning for exit rooms.
 *
 * Slots 1-3 are the seed-rotated part of the band. They were widened to
 * cover the ICE skill and personality systems (ADR-0219 remaining gap (4)):
 *
 *  - **Skill coverage.** Every grade lists at least one ICE that carries
 *    `skills`, so the authored skill metadata (ADR-0222) and its corrected
 *    classifications (ADR-0223) are reachable in play instead of sitting on
 *    catalog rows the encounter band never selects.
 *  - **Archetype coverage.** Every grade **except g5** lists at least one
 *    non-`aggressive` ICE, so the `defensive` preference list of ADR-0161
 *    has a target. g5 is the accepted exception: it is now all-`aggressive`
 *    (`neuromancer`, `sense_net_reporter`, `loa_entity`,
 *    `yakuza_enforcer`), because its old `ta_sentinel` slot had to be
 *    replaced to restore the HP-cap mechanism (see the module header).
 *    Archetype diversity still appears at g4 and g6, which both keep
 *    `ta_sentinel`. `support` remains unreachable — the catalog has **no**
 *    `support` ICE (0 of 97 rows), and adding one is an ADR-0219 Option D
 *    content task.
 *  - **Tier band.** Each grade keeps the tier band the original table used
 *    (g1 T1, g2 T1-T2, g3 T2-T3, g4 T3-T4, g5 T3-T5, g6 T4-T6) so the HP
 *    curve and the `iceHpForGrade` cap stay meaningful.
 *
 * Known catalog limits (not worked around, on purpose):
 *  - **g1 cannot fire a skill.** Both tier-1 skill-bearing ICE
 *    (`hosaka_courier`, `sense_net_alert`) carry only `buff` / `debuff`
 *    effects, and the combat path only fires a skill with `damage > 0`
 *    (ADR-0219 Option B). There is no tier-1 ICE with a damaging skill.
 *  - **No `stealth` ICE in the catalog carries any skill** (all 5 stealth
 *    rows have `skills: []`), so a skill-bearing `stealth` slot is
 *    impossible until the catalog gains one.
 *  - **g5 has no non-`aggressive` slot** (see "Archetype coverage" above).
 *    The grade's archetype diversity is carried by g4 and g6 instead.
 */
export const ENCOUNTER_ICE_BY_GRADE: Readonly<Record<number, ReadonlyArray<string>>> = {
  1: ["watchdog", "sense_net_alert", "wisp", "hosaka_courier"],
  2: ["spider", "sense_net_spin", "corporate_guard", "loa_zombie"],
  3: ["black", "hosaka_defender", "ice_dixie_echo", "sense_net_reporter"],
  4: ["goliath", "sense_net_reporter", "yakuza_enforcer", "ta_sentinel"],
  5: ["neuromancer", "sense_net_reporter", "loa_entity", "yakuza_enforcer"],
  6: ["neuromancer", "standard_ascended", "ta_sentinel", "aleph"],
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
 * Per-grade MAX (cap) HP. `iceHpForGrade` takes `min(natural HP, cap)`, so a
 * cap only bites when it sits BELOW the ICE row's own `hp_base +
 * hp_per_grade * (grade - 1)` value — raising it above that value is a no-op
 * for the affected row.
 *
 * **Baseline (ADR-0229, 2026-10-29).** These caps are the **baseline**
 * configuration, not a set of values to be chased toward ADR-0211's retired
 * per-grade targets. ADR-0211's per-grade win-rate numbers are superseded;
 * the *mechanism* it introduced — the per-grade HP cap — remains in force and
 * is what these values implement.
 *
 * Measured with `npm run balance` (opening deck, 100 runs/mission), the
 * opening baseline these caps produce is:
 *
 *   | grade | baseline | ADR-0211 target (superseded) |
 *   | --- | --- | --- |
 *   | g1 | 100.0% | 100.0% |
 *   | g2 | 88.6% | 88.8% |
 *   | g3 | 73.1% | 73.0% |
 *   | g4 | 39.3% | 47.4% |
 *   | g5 | 35.7% | 42.4% |
 *   | g6 | 0.0% | 0.0% |
 *
 * The opening curve is **monotonic non-increasing** (100.0 ≥ 88.6 ≥ 73.1 ≥
 * 39.3 ≥ 35.7 ≥ 0.0) — this is a hard invariant under ADR-0229, not a
 * coincidence of the current numbers.
 *
 * Per-grade reasoning (all measured, not derived):
 *
 *   - **g1 75** — unchanged. Every tier-1 band row sits below 75 HP, so the
 *     cap is inert at g1; the +50% dmg bonus carries the early tension.
 *   - **g2 86** — the cap *bites* on `corporate_guard` (natural 118 HP at
 *     g2). ADR-0224 put that defensive tier-2 row in the band and it cost
 *     g2 -13.1pp on its own: it has both the highest HP (118) and a
 *     `defensive` archetype that picks its skill more often. Trimming it to
 *     86 HP shortens the fight. Note the g2 **dmg bonus could not do this**:
 *     the auto-attack formula `floor((tier * 3 + armor) * (1 + pct / 100))`
 *     is a step function — for `corporate_guard` (tier 2, armor 3 → 9 base)
 *     it reads 19 dmg at +120% and 20 dmg at +123%, and every value in
 *     between leaves the g2 win-rate at 99.8% or 77.4% with no landing in
 *     between. The HP cap is the only fine-grained lever at g2.
 *   - **g3 141** — recalibrated after the ICE archetype consistency fix
 *     (ADR-0227). That fix corrected `hosaka_defender`'s `personality` to
 *     `defensive`, so g3 slot 2 now raises a **12-point `defense_grid`
 *     shield** instead of auto-attacking (the shield is authored in
 *     `skill_defs` with `magnitude: 12` and lasts 3 enemy ticks). The grade
 *     measured **73.1% → 89.7% (+16.6pp)** on the opening deck, which broke
 *     the curve's monotonic non-increasing invariant (g3 89.7% exceeded g2
 *     88.6%).
 *
 *     The cap is **141** (was 155) and it is paired with a **+8%** g3
 *     auto-attack bonus (see `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`). The
 *     pairing is forced, not stylistic — measured, with the opening deck at
 *     100 runs/mission:
 *
 *     - **Raising the cap alone cannot reach tolerance.** The cap is
 *       bounded above by the HP-monotonicity invariant: `c3 <= c4 = 165`
 *       (above 165 the same ICE would have *more* HP at g3 than at g4, which
 *       the `keeps HP monotonic non-decreasing across grades for every band
 *       id` test rejects). At the maximum c3 = 165 the grade measures
 *       **76.3%** — still **+3.3pp** off the 73.0% target, i.e. outside the
 *       ±3pp tolerance. No cap value in 155..165 lands inside it.
 *     - **The auto-attack bonus alone cannot reach tolerance either**, and
 *       it is a step function: `floor((tier * 3 + armor) * (1 + pct / 100))`
 *       over the g3 band's auto-attack bases (14 / 15 / 13 / 13) yields only
 *       two reachable damage vectors below +14% — `(14, 15, 13, 13)` at 0%
 *       and `(15, 16, 14, 14)` at +8%. The intermediate +7% step (which
 *       raises only `hosaka_defender`, 15 → 16) is measurably a **no-op**:
 *       839/1100 wins, identical to 0%. The next step (+8%) is a **cliff** —
 *       at c3 = 165 it drops the grade straight from 76.3% to **51.5%**
 *       (-24.8pp), with no reachable value in between. So at the maximum cap
 *       the grade cannot be placed inside the tolerance window at all.
 *     - **Lowering the cap is what re-opens the tolerance band.** With the
 *       +8% bonus applied, the reachable grade values step down through the
 *       70-76% window as the cap drops: c3 = 142 → 71.5%, **c3 = 141 →
 *       72.8%**, c3 = 140 → 75.0%. The cap is set to **141**, the value
 *       closest to the then-current 73.0% target.
 *
 *     The mechanism is a **trade, not a nerf**: the g3 encounter ICE now has
 *     14 fewer HP and hits 1 point harder per auto-attack, so the grade
 *     keeps its difficulty while the shielded `hosaka_defender` still gets
 *     to raise its shield (the shield stays meaningful — it absorbs a fixed
 *     12 — it just no longer makes the grade trivially winnable). The
 *     effective-HP monotonicity invariant still holds (0 violations), and
 *     `ice_dixie_echo` (natural 123 HP at g3) remains the one g3 band row
 *     the cap does not trim.
 *   - **g4 165** — the flat ceiling. The g4 band is 40% `goliath` (natural
 *     240 HP, 8 armor) which the opener never beats, so the grade is carried
 *     by the rows the opener *can* beat (`sense_net_reporter` at natural
 *     180 HP, `yakuza_enforcer` at 154, `ta_sentinel` at 244). The earlier
 *     post-ADR-0224 attempt used 168 to claw back 1.2pp; with the flat 165
 *     ceiling restored the grade measured 49.0% — inside the ±3pp tolerance
 *     of the then-current target, and the opener curve stayed monotonic
 *     non-increasing. ADR-0228's crit wiring later moved g4 to **39.3%**
 *     (crit is `aggressive`-only and g4's band is 3-of-4 `aggressive`); that
 *     is now the baseline, and ADR-0229's drift policy governs any further
 *     movement.
 *   - **g5 165** — the flat ceiling. An earlier attempt raised this to 560
 *     to separate the tier-4 `ta_sentinel` (272 natural HP) from the tier-5
 *     `neuromancer` (560 natural HP) so the opener could win the first while
 *     the PPL deck still lost the second. That separation is no longer
 *     needed: g5 slot 2 is `loa_entity` (T3, 188 natural HP, 5 auto-attack,
 *     `voodoo_curse` poison that fires), so the g5 band rows the opener can
 *     beat are all comfortably under the cap and the grade is tunable with
 *     the flat 165 ceiling. Raising the cap to 560 also **disabled** the cap
 *     mechanism ADR-0211 introduced to keep the climax unwinnable for the
 *     opening deck, and it cost PPL g5 44.4% → 100.0% (+55.6pp). At the flat
 *     165 ceiling the opening g5 baseline is **35.7%** (ADR-0228's crit
 *     wiring moved it from 43.1%), and PPL g5 stays at 44.4%.
 *   - **g6 165** — the flat ceiling. `c6 >= c5` holds by construction
 *     (`165 >= 165`), so the HP-monotonicity invariant is satisfied without
 *     a raised ceiling. The g6 climax therefore stays out of reach for the
 *     opener (0.0%) while the -20% dmg penalty keeps it attainable for a
 *     developed deck.
 *
 * **Hard invariants (ADR-0229 §B).** (1) the opening curve stays monotonic
 * non-increasing; (2) g6 stays at (or near) 0 — the opener must not be able
 * to win the climax; (3) this array stays monotonically non-decreasing; and
 * (4) the max cap stays at 165 — a cap above the ICE's natural HP is a
 * no-op, which would silently disable the mechanism.
 */
const ENCOUNTER_HP_BY_GRADE: ReadonlyArray<number> = [
  75, 86, 141, 165, 165, 165,
];

/** Per-grade ICE auto-attack bonus (percentage added to the base `tier * 3 +
 * armor` formula). Index = grade - 1.
 *
 * Pairs with `ENCOUNTER_HP_BY_GRADE`: the HP cap creates contest at g3+ (where
 * tier-3+ ICE has natural HP > cap), and this dmg bonus creates contest at
 * g1-g2 (where tier-1/2 ICE natural HP < cap so the cap is a no-op — the
 * opener annihilates the ICE in 3-4 turns before any dmg matters). The
 * opener base dmg (program.tier * 5) is fixed, so the only knob to lengthen
 * early-grade combat is to push ICE dmg up.
 *
 * **Scope: auto-attack only.** The bonus multiplies the `tier * 3 + armor`
 * auto-attack. It does **not** touch ICE *skill* damage, which is
 * `dmg_base + tier * 2` with no grade term (see `ice_skills.ts`). That
 * asymmetry matters at g5, where a 50%-skill-caster's strikes (e.g. the
 * 15-damage `straylight_protocol`) cannot be scaled down by this knob.
 *
 * **Boss rooms (bossPhase > 0) skip this bonus** in
 * `state_actions_combat.ts`: boss encounter tension is already carried by
 * the phase multipliers (1.25x / 1.5x / 2x for phases 2/3/4), and stacking
 * the per-grade bonus would push phase-specific dmg expectations out of
 * the boss_ai test contracts. Boss ICE always uses the raw `tier * 3 +
 * armor` baseline.
 *
 * **Baseline (ADR-0229, 2026-10-29).** These values are the **baseline**
 * configuration; ADR-0211's per-grade win-rate targets are superseded, while
 * the damage-bonus *curve* itself (its scope, its step-function nature, its
 * boss-phase exclusion) remains the design.
 *
 * Measured with `npm run balance` (opening deck, 100 runs/mission):
 *
 *   - **g1 +50** — unchanged. Tier-1 ICE deals `3 * 1.5 = 4` dmg/tick and
 *     still dies inside ~2.7 turns; g1 stays saturated at 100.0%.
 *   - **g2 +130** — unchanged. The +130 is the early-game tension lever
 *     (tier-1/2 ICE natural HP is below the cap, so the cap cannot
 *     lengthen the fight). The g2 grade sits at **88.6%** in the baseline
 *     curve via the **HP cap** (86); the bonus stays at +130 because it is
 *     what makes the remaining g2 contests real.
 *   - **g3 +8** — recalibrated after the ICE archetype consistency fix
 *     (ADR-0227). `hosaka_defender` (g3 slot 2) became `defensive` and
 *     started raising a 12-point `defense_grid` shield instead of
 *     auto-attacking, which moved the opening-deck g3 win-rate 73.1% → 89.7%
 *     (+16.6pp) and broke the curve's monotonic non-increasing invariant. The
 *     g3 HP cap alone could not fix it — its ceiling is 165 (`c3 <= c4`,
 *     enforced by the HP-monotonicity invariant), and at 165 the grade still
 *     measured 76.3%. The auto-attack bonus is therefore the second half of a
 *     **matched pair** with the HP cap: the cap drops to **141** while this
 *     bonus rises 0 → **+8%**.
 *
 *     **+8% is the smallest reachable step.** The bonus is a step function
 *     — `floor((tier * 3 + armor) * (1 + pct / 100))` — over the g3 band's
 *     auto-attack bases (14 / 15 / 13 / 13). It has only two reachable
 *     damage vectors below +14%:
 *
 *     | pct | g3 band auto-attack damage |
 *     | --- | --- |
 *     | 0 | `(14, 15, 13, 13)` |
 *     | +7 | `(14, 16, 13, 13)` — raises `hosaka_defender` only |
 *     | +8 | `(15, 16, 14, 14)` — raises all four band rows |
 *
 *     The intermediate **+7%** step is measurably a **no-op** (839/1100
 *     wins, identical to 0%) — it moves the shielded ICE's auto-attack by 1
 *     point and changes no outcome at the grade level. **+8%** is the first
 *     step that moves all four band rows, and it is the smallest one that
 *     combines with a cap inside the tolerance window. The g3 grade
 *     therefore lands at **73.1%** in the current baseline, and the opening
 *     curve stays monotonic non-increasing.
 *
 *     Note the asymmetry this knob inherits from ADR-0211: it scales
 *     auto-attack damage only. `hosaka_defender`'s shield is a **shield**,
 *     not damage, so this bonus does not weaken it — the shield still
 *     absorbs a flat 12 and still lasts 3 enemy ticks.
 *   - **g5 0** — no penalty. An earlier post-ADR-0224 attempt used -79 to
 *     make g5's `ta_sentinel` (tier 4, 19 auto-attack, 272 natural HP, 50%
 *     skill-cast rate) winnable for the opening deck: its 15-damage skill is
 *     *not* scaled by this knob, so only a deep auto-attack reduction could
 *     get there. The same reduction also made `neuromancer` (tier 5, 24
 *     auto-attack, 560 natural HP) winnable for the PPL deck, so **PPL g5
 *     moved from 44.4% to 100.0% (+55.6pp)**. The g5 slot repair removes the
 *     need for that lever entirely: slot 2 is now `loa_entity` (tier 3, 5
 *     auto-attack, 188 natural HP, poison skill that fires), so the cap alone
 *     carries the grade and the PPL deck keeps its g5 contest.
 *   - **g6 -20** — the opener still flatlines at 0.0% while the developed
 *     deck keeps the climax attainable. An earlier attempt used -78 because
 *     the g6 cap had been raised to 560 (forced by the g5 cap), which let
 *     `aleph` (tier 6, 520 natural HP) survive far longer than at a 165 cap.
 *     With the flat 165 ceiling in place, -20% is the right knob. The knob
 *     stays negative here — the guard in `state_actions_combat.ts` applies
 *     any non-zero value, so a grade can reduce ICE damage as well as raise
 *     it.
 *
 * PPL interaction: the +130 at g2 also tips PPL g2 to 77.9% (the PPL g2→g3
 * curve is not monotonic: 77.9 < 99.6). That drift is a **deck** artifact,
 * not ICE tuning: `deckForGrade` fields only tier<=2 cards at g2 (all weak)
 * but jumps to tier-3 payload/exploit/goliath at g3, so the PPL deck is
 * stronger at g3 than g2. Closing it would require either a deck-definition
 * change or pushing the opening g2 up (both curves move together under any
 * ICE knob), i.e. a mechanics change — out of scope here. Under ADR-0229 the
 * PPL curve is a **reference, not a target** (§C of the drift policy), and
 * the primary **opening-deck** curve stays monotonic non-increasing.
 */
const ENCOUNTER_DMG_BONUS_PCT_BY_GRADE: ReadonlyArray<number> = [
  50, 130, 8, 0, 0, -20,
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
