/** What the fixer's advance buys before a run (ADR-0283).
 *
 * ADR-0280 §9: at grades 4-6 the runner loses its FIRST fight, so nothing that
 * happens *between* fights reaches it — which is why the route (ADR-0281) and the
 * loot stop (ADR-0282) move the middle grades and leave 4-6 at zero.
 *
 * Three capacity levers were measured, because the obvious one — buy cards — was
 * measured to make runs WORSE (the opening deck is a curated five-slot
 * instrument; a purchase evicts `barrier` or `decoy`, and under the "one enemy
 * phase per card" model a defensive slot is worth more than a tier buys):
 *
 *   extra max HP   +30 -> g4 31.7 -> 42.5, +250 -> g5 0 -> 19.4   WORKS
 *   extra hand     +2  -> g4 31.7 -> 31.7                          INERT
 *   card purchases      -> g2/g3 down, g4 +9.2                     HARMFUL
 *
 * So prep is HP: the first fight is a survivability check, and nothing else the
 * advance can buy survives it. A bigger hand does not help because the runner
 * dies holding the extra cards, and the COST cap bounds a turn regardless.
 *
 * NOTE the table is NOT monotone: grade 5 needs more than grade 6 (7.4 encounters
 * against 7.3, and `neuromancer`'s armour 9 against `aleph`'s 7). Unlike the ICE
 * HP cap there is no invariant on a player stat, so the honest shape is allowed.
 *
 * `state/loadout.ts` is the EQUIPMENT loadout; this module is the run's prep.
 */
import type { GameState } from "../types";
import { missionGradeOf } from "../combat/ice_scaling";
import { clampGrade } from "../combat/ice_scaling";
import {
  PREP_WALLET_FLOOR_HP,
  PREP_WALLET_FLOOR_SHIELD,
  prepWalletContribution,
} from "./prep_wallet";

/** What the advance is spent on. The two options trade off, and the trade-off
 * inverts with grade (ADR-0283 C''):
 *
 *   stim  extra max HP. Wins at 5-6: the loot repair is a percentage of max HP,
 *         so a bigger pool compounds -- it absorbs more now and makes every
 *         later repair bigger.
 *   ice   a starting shield pool. Wins at 3-4: a small pool covers the early
 *         fights, where the damage per fight is modest. It is spent once.
 *
 * Measured at 12 seeds, loot=smart: g3 HP 84.1% against shield+60 87.1%;
 * g4 HP 45.8% against shield+60 57.5%; g5 HP 28.7% against shield+400 11.1%.
 */
export type PrepChoice = "stim" | "ice";

export const PREP_OPTIONS: ReadonlyArray<{
  readonly id: PrepChoice;
  readonly label: string;
  readonly short: string;
}> = [
  // The note is the actual difference, not a restatement of the number: the
  // repair scales with max HP, so only the pool compounds.
  { id: "stim", label: "STIM", short: "lasts — repairs scale with the pool" },
  { id: "ice", label: "ICE", short: "absorbs now — spent once" },
];

/** Extra starting max HP per grade, measured against the mission targets. */
/** ADR-0306: re-tuned with the smaller repair. With a 70-100% heal the curve was
 * carried by the healing itself; once the stop became a real choice (12-28%) the
 * capacity had to carry more of it, and g4 needed the most (25 -> 70). The
 * result lands best play inside 3.5pp of every mission target. */
export const PREP_HP_BY_GRADE: ReadonlyArray<number> = [0, 0, 20, 70, 185, 140];

/** Starting shield pool per grade, sized so the option is competitive where it
 * is strong rather than a token alternative (ADR-0283 C''). */
export const PREP_SHIELD_BY_GRADE: ReadonlyArray<number> = [0, 0, 35, 65, 400, 250];

/** Extra max HP the advance buys at a grade. */
export function prepHpBonus(grade: number): number {
  return PREP_HP_BY_GRADE[clampGrade(grade) - 1] ?? 0;
}

/** Shield pool the advance buys at a grade. */
export function prepShieldForGrade(grade: number): number {
  return PREP_SHIELD_BY_GRADE[clampGrade(grade) - 1] ?? 0;
}

/** What the chosen option gives at a grade, for the screen to print. */
export function prepAmountFor(grade: number, choice: PrepChoice): number {
  return choice === "ice" ? prepShieldForGrade(grade) : prepHpBonus(grade);
}

/** The grade's own value for an option. */
function prepTableValue(grade: number, choice: PrepChoice): number {
  return choice === "ice" ? prepShieldForGrade(grade) : prepHpBonus(grade);
}

/** The stockpile's share of a prep, and what it costs (ADR-0284). */
export function prepWalletUse(
  grade: number,
  choice: PrepChoice,
  balance: number,
): number {
  return prepWalletContribution(
    prepTableValue(grade, choice),
    balance,
    choice === "ice" ? PREP_WALLET_FLOOR_SHIELD : PREP_WALLET_FLOOR_HP,
  );
}

/** What a prep actually grants: the grade's table plus the stockpile's share. */
export function prepGrantFor(
  grade: number,
  choice: PrepChoice,
  walletBalance = 0,
): { readonly base: number; readonly fromWallet: number; readonly total: number } {
  const base = prepTableValue(grade, choice);
  const fromWallet = prepWalletUse(grade, choice, walletBalance);
  return { base, fromWallet, total: base + fromWallet };
}

/**
 * Apply prep to a freshly built run: a bigger pool, filled.
 *
 * Applied at run start rather than in `makeInitialState`, so the per-encounter
 * balance harness keeps measuring the same fight it always did (prep is a run
 * fact, not an encounter fact).
 */
export function applyPrep(
  state: GameState,
  choice: PrepChoice = "stim",
  walletBalance = 0,
): GameState {
  const grade = missionGradeOf(state.mission);
  const grant = prepGrantFor(grade, choice, walletBalance);
  if (grant.total <= 0) return state;
  if (choice === "ice") {
    const pool = grant.total;
    return {
      ...state,
      statusEffects: [
        ...state.statusEffects,
        {
          kind: "shield",
          target: "player",
          magnitude: pool,
          // Prep is spent by absorbing damage, not by running out of time: a
          // plain shield is only decremented by `tickStatus`, so it is given a
          // lifetime longer than any run.
          remaining: 9999,
        },
      ],
    };
  }
  const bonus = grant.total;
  const maxHp = state.player.maxHp + bonus;
  return { ...state, player: { ...state.player, maxHp, hp: maxHp } };
}
