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
 * **Post-ADR-0224 recalibration.** The band widening of ADR-0224 replaced
 * several band rows, so the ADR-0211 calibration no longer held (g2 -11.4pp,
 * g3 +6.0pp, g5 -10.4pp). `ENCOUNTER_HP_BY_GRADE` and
 * `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` were re-tuned by measurement against
 * `npm run balance` (opening deck, 100 runs/mission) and restore every
 * grade's ADR-0211 target to within ±3pp (the tightest current residual is
 * g3 at -0.2pp; the loosest is g4 at +1.6pp). The per-grade evidence and the
 * one irreducible trade-off (g5's opening-deck target vs the PPL g5 curve)
 * are recorded on the two constants below. The encounter band itself is
 * **unchanged** — ADR-0224 settled it.
 *
 * **g5 band repair (post-ADR-0224).** The recalibration above restored the
 * opening-deck curve but did so by lifting the g5/g6 HP caps to 560
 * (`neuromancer`'s natural HP) — which effectively **disabled** the cap that
 * ADR-0211 introduced to keep the climax unwinnable for the opening deck.
 * The cost was measured: **PPL g5 went 44.4% → 100.0% (+55.6pp)**.
 *
 * The root cause was ONE slot: g5's `ta_sentinel` (T4, `defensive`, 272
 * natural HP at g5, 19 auto-attack, 50%-skill-cast rate with an unscaled
 * 15-damage `straylight_protocol`). Making that slot opener-winnable
 * required gutting the cap, which in turn made the whole g5 grade
 * developed-deck-trivial. The repair therefore changes the **slot**, not the
 * cap: g5 slot 2 is now `loa_entity` (T3, `aggressive`, 188 natural HP at
 * g5, 5 auto-attack), whose `voodoo_curse` poison *does* fire (ADR-0216 /
 * ADR-0218 made skill damage live again) and whose auto-attack profile
 * matches what occupied that slot before ADR-0224. The cap is back to a flat
 * 165 for g4-g6, and `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` is back to the
 * ADR-0211 original values.
 *
 * The accepted trade: **g5 no longer carries a non-`aggressive` ICE.** The
 * archetype-diversity coverage ADR-0224 added still holds at g4 and g6,
 * which both keep `ta_sentinel`.
 *
 * **g3 recalibration (post-archetype-consistency fix).** The ICE archetype
 * consistency pass corrected 12 catalog `personality` values so that each
 * ICE's archetype matches its own name and skill effects. One of those
 * corrections landed on the g3 encounter band: **`hosaka_defender` (g3 slot
 * 2) is now `defensive`**, so it raises a 12-point `defense_grid` shield
 * instead of auto-attacking. The grade measured **73.1% → 89.7% (+16.6pp)**
 * on the opening deck, which is outside the ±3pp tolerance ADR-0225 set and
 * **broke the opening curve's monotonic non-increasing invariant** (g3 at
 * 89.7% exceeded g2 at 88.6%).
 *
 * The g3 grade was restored by trading encounter HP for auto-attack pressure:
 * the g3 HP cap dropped 155 → **141** and the g3 auto-attack bonus rose
 * 0 → **+8%**. The two levers are a matched pair — see the per-grade
 * reasoning on each constant for why no single lever can land the grade in
 * tolerance. The band, the ICE rows, the skill effects and the other five
 * grades' calibration are **unchanged**.
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
 * **Recalibrated after ADR-0224 (encounter band coverage).** ADR-0224 widened
 * slots 1-3 of every band so the ICE skill / personality systems are
 * reachable in play. That replaced several band rows and moved the grade
 * curve off the ADR-0211 calibration (g2 -11.4pp, g3 +6.0pp, g5 -10.4pp).
 * These caps are the recalibrated values; measured with
 * `npm run balance` (opening deck, 100 runs/mission) they restore the
 * ADR-0211 targets to within ±3pp on every grade:
 *
 *   | grade | ADR-0211 target | pre-recalibration | current | residual |
 *   | --- | --- | --- | --- | --- |
 *   | g1 | 100.0% | 100.0% | 100.0% | +0.0pp |
 *   | g2 | 88.8% | 77.4% | 88.6% | -0.2pp |
 *   | g3 | 73.0% | 79.0% | 72.8% | -0.2pp |
 *   | g4 | 47.4% | 48.8% | 49.0% | +1.6pp |
 *   | g5 | 42.4% | 32.0% | 43.1% | +0.7pp |
 *   | g6 | 0.0% | 0.0% | 0.0% | +0.0pp |
 *
 * ("pre-recalibration" is the post-ADR-0224 measurement. g3 and g4 were
 * re-measured after the archetype consistency fix; the g3 entry is the
 * recalibration described below and on the g3 bullet.)
 *
 * Per-grade reasoning (all measured, not derived):
 *
 *   - **g1 75** — unchanged. Every tier-1 band row sits below 75 HP, so the
 *     cap is inert at g1; the +50% dmg bonus carries the early tension.
 *   - **g2 86** — the cap now *bites* on `corporate_guard` (natural 118 HP
 *     at g2). ADR-0224 put that defensive tier-2 row in the band and it cost
 *     g2 -13.1pp on its own: it has both the highest HP (118) and a
 *     `defensive` archetype that picks its skill more often. Trimming it to
 *     86 HP shortens the fight and restores the grade. Note the g2 **dmg
 *     bonus could not do this**: the auto-attack formula
 *     `floor((tier * 3 + armor) * (1 + pct / 100))` is a step function — for
 *     `corporate_guard` (tier 2, armor 3 → 9 base) it reads 19 dmg at
 *     +120% and 20 dmg at +123%, and every value in between leaves the g2
 *     win-rate at 99.8% or 77.4% with no landing in between. The HP cap is
 *     the only fine-grained lever at g2.
 *   - **g3 141** — recalibrated after the ICE archetype consistency fix.
 *     That fix corrected `hosaka_defender`'s `personality` to `defensive`,
 *     so g3 slot 2 now raises a **12-point `defense_grid` shield** instead
 *     of auto-attacking (the shield is authored in `skill_defs` with
 *     `magnitude: 12` and lasts 3 enemy ticks). The grade measured
 *     **73.1% → 89.7% (+16.6pp)** on the opening deck — outside the ±3pp
 *     tolerance, and it broke the curve's monotonic non-increasing invariant
 *     (g3 89.7% exceeded g2 88.6%).
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
 *       closest to the ADR-0211 target (**-0.2pp** off 73.0%).
 *
 *     The mechanism is a **trade, not a nerf**: the g3 encounter ICE now has
 *     14 fewer HP and hits 1 point harder per auto-attack, so the grade
 *     keeps its difficulty while the shielded `hosaka_defender` still gets
 *     to raise its shield (the shield stays meaningful — it absorbs a fixed
 *     12 — it just no longer makes the grade trivially winnable). The
 *     effective-HP monotonicity invariant still holds (0 violations), and
 *     `ice_dixie_echo` (natural 123 HP at g3) remains the one g3 band row
 *     the cap does not trim.
 *   - **g4 165** — the ADR-0211 original cap. The g4 band is 40% `goliath`
 *     (natural 240 HP, 8 armor) which the opener never beats, so the grade is
 *     carried by the rows the opener *can* beat (`sense_net_reporter` at
 *     natural 180 HP, `yakuza_enforcer` at 154, `ta_sentinel` at 244). The
 *     earlier post-ADR-0224 attempt used 168 to claw back 1.2pp; with the
 *     flat 165 ceiling restored the grade measures 49.0%, i.e. **+1.6pp**
 *     off the 47.4% ADR-0211 target — inside the ±3pp tolerance, and the
 *     opener curve stays monotonic non-increasing. The g3 recalibration
 *     does not touch g4: its cap and its auto-attack bonus are unchanged,
 *     and the grade measures 49.0% before and after.
 *   - **g5 165** — the ADR-0211 original cap. The earlier attempt raised
 *     this to 560 to separate the tier-4 `ta_sentinel` (272 natural HP) from
 *     the tier-5 `neuromancer` (560 natural HP) so the opener could win the
 *     first while the PPL deck still lost the second. That separation is
 *     no longer needed: g5 slot 2 is `loa_entity` (T3, 188 natural HP, 5
 *     auto-attack, `voodoo_curse` poison that fires), so the g5 band rows
 *     the opener can beat are all comfortably under the cap and the grade is
 *     tunable with the flat 165 ceiling. Raising the cap to 560 also
 *     **disabled** the cap mechanism ADR-0211 introduced to keep the climax
 *     unwinnable for the opening deck, and it cost PPL g5 44.4% → 100.0%
 *     (+55.6pp). At the flat 165 ceiling g5 measures 43.1%, i.e. **+0.7pp**
 *     off the 42.4% target, and PPL g5 stays at 44.4%.
 *   - **g6 165** — the ADR-0211 original cap. `c6 >= c5` holds by
 *     construction (`165 >= 165`), so the HP-monotonicity invariant is
 *     satisfied without a raised ceiling. The g6 climax therefore stays out
 *     of reach for the opener (0.0%) while the -20% dmg penalty keeps it
 *     attainable for a developed deck.
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
 * **ADR-0211 original values, restored.** Measured with `npm run balance`
 * (opening deck, 100 runs/mission):
 *
 *   - **g1 +50** — unchanged. Tier-1 ICE deals `3 * 1.5 = 4` dmg/tick and
 *     still dies inside ~2.7 turns; g1 stays saturated at 100.0%.
 *   - **g2 +130** — unchanged. The +130 is the early-game tension lever
 *     (tier-1/2 ICE natural HP is below the cap, so the cap cannot
 *     lengthen the fight). The g2 grade is restored to 88.6% by the **HP
 *     cap** (86) instead; the bonus stays at +130 because it is what makes
 *     the remaining g2 contests real.
 *   - **g3 +8** — recalibrated after the ICE archetype consistency fix.
 *     `hosaka_defender` (g3 slot 2) became `defensive` and started raising a
 *     12-point `defense_grid` shield instead of auto-attacking, which moved
 *     the opening-deck g3 win-rate 73.1% → 89.7% (+16.6pp) and broke the
 *     curve's monotonic non-increasing invariant. The g3 HP cap alone
 *     cannot fix it — its ceiling is 165 (`c3 <= c4`, enforced by the
 *     HP-monotonicity invariant), and at 165 the grade still measures 76.3%,
 *     +3.3pp off the 73.0% target. The auto-attack bonus is therefore the
 *     second half of a **matched pair** with the HP cap: the cap drops to
 *     **141** while this bonus rises 0 → **+8%**, and the grade lands at
 *     **72.8%** (-0.2pp off the ADR-0211 target, inside the ±3pp tolerance).
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
 *     therefore lands at **72.8%** and the opening curve stays monotonic
 *     non-increasing (100.0 / 88.6 / 72.8 / 49.0 / 43.1 / 0.0). The PPL g3
 *     grade is unaffected at 100.0%.
 *
 *     Note the asymmetry this knob inherits from ADR-0211: it scales
 *     auto-attack damage only. `hosaka_defender`'s shield is a **shield**,
 *     not damage, so this bonus does not weaken it — the shield still
 *     absorbs a flat 12 and still lasts 3 enemy ticks.
 *   - **g5 0** — back to the ADR-0211 original. The earlier post-ADR-0224
 *     attempt used -79 to make g5's `ta_sentinel` (tier 4, 19 auto-attack,
 *     272 natural HP, 50% skill-cast rate) winnable for the opening deck:
 *     its 15-damage skill is *not* scaled by this knob, so only a deep
 *     auto-attack reduction could get there. The same reduction also made
 *     `neuromancer` (tier 5, 24 auto-attack, 560 natural HP) winnable for
 *     the PPL deck, so **PPL g5 moved from 44.4% to 100.0% (+55.6pp)**.
 *     The g5 slot repair removes the need for that lever entirely: slot 2
 *     is now `loa_entity` (tier 3, 5 auto-attack, 188 natural HP, poison
 *     skill that fires), so the cap alone restores the opening-deck target
 *     and the PPL deck keeps its g5 contest.
 *   - **g6 -20** — back to the ADR-0211 original. The earlier attempt used
 *     -78 because the g6 cap had been raised to 560 (forced by the g5 cap),
 *     which let `aleph` (tier 6, 520 natural HP) survive far longer than at
 *     a 165 cap. With the flat 165 ceiling restored, -20% is again the
 *     right knob: the opener still flatlines at 0.0% while the developed
 *     deck keeps the climax attainable. The knob stays negative here — the
 *     guard in `state_actions_combat.ts` applies any non-zero value, so a
 *     grade can reduce ICE damage as well as raise it.
 *
 * PPL interaction: the +130 at g2 also tips PPL g2 from 100% to 77.9% (the
 * PPL g2→g3 curve is not monotonic). That drift is a **deck** artifact, not
 * ICE tuning: `deckForGrade` fields only tier<=2 cards at g2 (all weak) but
 * jumps to tier-3 payload/exploit/goliath at g3, so the PPL deck is stronger
 * at g3 than g2. Closing it would require either a deck-definition change or
 * pushing the opening g2 above its 80-95% target (both curves move together
 * under any ICE knob), i.e. a mechanics change — out of scope here. The
 * primary **opening-deck** curve stays monotonic non-increasing.
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
