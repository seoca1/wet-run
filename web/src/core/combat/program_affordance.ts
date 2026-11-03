/** Program affordance — what a hand slot will really do, from runtime fields
 * only (ADR-0251, combat-directions synthesis "first slice").
 *
 * Every row is derived from fields the reducer itself reads when a program is
 * played: the slot order of `state.deck` (the order `resolveProgramSelection`
 * maps digits through), `program.cost` scaled by the `double_alarm` mutator,
 * the COST cap, and `program.aoe`. `useProgram` charges COST through
 * `programAlarmCost` and tests the cap with `COST_LIMIT`, so the label and
 * the charge share one definition and cannot drift.
 *
 * Deliberately absent: role, authored damage / damage_bonus, effect text,
 * descriptions and kill chance. The runtime `Program` does not carry role or
 * authored damage, every program resolves through the same `tier * 5` damage
 * path, and burn/slow are universal random procs — none of those would be a
 * true statement about what the key does.
 *
 * Pure: no `Math.random`, no clock, no DOM.
 */
import type { GameState, Program } from "../types";
import { programEffectTag } from "./program_effects";
import {
  offeredCardIds,
  rewardProgram,
  type RewardSource,
} from "../state/card_reward";
import type { RunMutator } from "../state/run_mutators";

/** COST cap: a play that would take COST above this is refused. */
export const COST_LIMIT = 100;

/** Name column width shared by the canvas rows and the touch buttons. */
const NAME_WIDTH = 9;

/** Hand slots the combat layout always reserves (the base hand size), so
 * playing a card never moves the rows that remain. */
export const HAND_LAYOUT_SLOTS = 5;

/** The COST a play charges: `cost`, doubled under `double_alarm`, floored. */
export function programAlarmCost(
  program: Pick<Program, "cost">,
  activeMutators: ReadonlyArray<RunMutator>,
): number {
  const multiplier = activeMutators.includes("double_alarm") ? 2.0 : 1.0;
  return Math.floor(program.cost * multiplier);
}

/** True when the program hits every ICE in the roster. */
export function programHitsAllIce(program: Pick<Program, "aoe">): boolean {
  return (program as { aoe?: boolean }).aoe === true;
}

/** One hand slot, as the player can read it before pressing its number. */
export interface ProgramAffordance {
  /** 1-based slot: the digit / button that plays this program. */
  readonly slot: number;
  readonly programId: string;
  /** Upper-case display name, cut to the shared column width. */
  readonly name: string;
  /** COST the play charges. */
  readonly cost: number;
  /** COST after the play (meaningful only when not blocked). */
  readonly after: number;
  /** True when the play would exceed `COST_LIMIT` and is refused. */
  readonly blocked: boolean;
  readonly target: "ICE" | "ALL ICE";
  /** ADR-0257: what this card does besides damage, ≤ 8 chars. Empty for a
   * plain attack. Read from the mechanic (program_effects.ts), so the row
   * cannot claim an effect the reducer does not apply. */
  readonly effectTag: string;
}

/** Affordance rows for the current hand, in slot order. */
export function programAffordances(
  state: Pick<GameState, "deck" | "player" | "activeMutators">,
): ReadonlyArray<ProgramAffordance> {
  return state.deck.map((program, i) => {
    const cost = programAlarmCost(program, state.activeMutators);
    const after = state.player.alarm + cost;
    return {
      slot: i + 1,
      programId: program.id,
      name: program.name.toUpperCase().slice(0, NAME_WIDTH),
      cost,
      after,
      blocked: after > COST_LIMIT,
      target: programHitsAllIce(program) ? "ALL ICE" : "ICE",
      effectTag: programEffectTag(program),
    };
  });
}

/** The effect column of a hand row: the card's effect, or `BLOCKED` when the
 * play is refused (a refused card's effect cannot happen, so it does not
 * claim the space). */
function effectText(a: ProgramAffordance): string {
  return a.blocked ? "BLOCKED" : a.effectTag;
}

/**
 * Full canvas row, e.g. `1 STRIKE    COST +3   TARGET ICE`.
 *
 * ADR-0251 rule 5: the hand states what the screen will do. The row used
 * to end with `→ 41/100` — the COST left after the play. That figure is a
 * prediction, and it is wrong on the killing blow: the reducer charges
 * nothing when the play defeats the last ICE, so the row promised a COST
 * that was never charged. Kill prediction is forbidden (rule 5), so the row
 * cannot special-case the killing card either — the honest form is the
 * card's own COST, and the current total stays in the HUD.
 */
export function formatAffordanceRow(a: ProgramAffordance): string {
  const name = a.name.padEnd(NAME_WIDTH);
  const cost = `+${a.cost}`.padEnd(3);
  const effect = effectText(a).padEnd(8);
  return `${a.slot} ${name} COST ${cost}  ${effect}  TARGET ${a.target}`;
}

/** Narrow canvas row, e.g. `1 BARRIER   +3   SHIELD 2 ICE`; its columns line
 * up under `COMPACT_HAND_HEADER`, which names them. */
export function formatCompactAffordanceRow(a: ProgramAffordance): string {
  const name = a.name.padEnd(NAME_WIDTH);
  const cost = `+${a.cost}`.padEnd(4);
  const effect = effectText(a).padEnd(8);
  return `${a.slot} ${name} ${cost} ${effect} ${a.target}`;
}

/** Column legend for the narrow rows. */
export const COMPACT_HAND_HEADER = `${"HAND".padEnd(NAME_WIDTH + 3)}${"COST".padEnd(5)}${"EFFECT".padEnd(9)}TARGET`;

/** Longest full row a hand can produce (two-digit COST, `SHIELD 2`, `ALL ICE`). */
export const FULL_ROW_WIDTH = formatAffordanceRow({
  slot: 9,
  programId: "",
  name: "",
  cost: 99,
  after: COST_LIMIT,
  blocked: false,
  target: "ALL ICE",
  effectTag: "SHIELD 2",
}).length;

/** Visible lines of a touch button (narrow enough for five in a phone row). */
export function touchAffordanceLines(a: ProgramAffordance): readonly string[] {
  return [
    `${a.slot} COST+${a.cost}`,
    a.name,
    a.blocked ? "BLOCKED" : a.effectTag,
    a.target,
  ];
}

/** Spoken label for a touch button; says the same facts as the canvas row. */
export function affordanceAriaLabel(a: ProgramAffordance): string {
  // ADR-0257: the spoken label carries the effect too, so a screen reader
  // gets the same information as the row.
  if (a.blocked) {
    return `${a.slot} ${a.name}, COST plus ${a.cost}, blocked, over ${COST_LIMIT}, target ${a.target}`;
  }
  const effect = a.effectTag ? `, ${a.effectTag}` : "";
  return `${a.slot} ${a.name}, COST plus ${a.cost}${effect}, target ${a.target}`;
}

/**
 * Affordance rows for the loot screen's card offer (ADR-0259).
 *
 * The row shape is the same as the hand's, so the touch row renders the
 * reward with the same facts and the same tap handler shape.
 */
export function rewardAffordances(
  state: RewardSource & Pick<GameState, "player" | "activeMutators">,
): ReadonlyArray<ProgramAffordance> {
  return offeredCardIds(state).map((id, i) => {
    const card = rewardProgram(id);
    const cost = card ? programAlarmCost(card, state.activeMutators) : 0;
    return {
      slot: i + 1,
      programId: id,
      name: (card?.name ?? id).toUpperCase().slice(0, NAME_WIDTH),
      cost,
      after: state.player.alarm + cost,
      // A reward is not being played now, so it is never refused.
      blocked: false,
      target:
        card && programHitsAllIce(card)
          ? ("ALL ICE" as const)
          : ("ICE" as const),
      effectTag: card ? programEffectTag(card) : "",
    };
  });
}

/** One line of the loot screen's card offer, e.g. `1 BACKDOOR   PIERCE 2`.
 * ADR-0261: the taken card is marked, and shows what the run gained. */
export function formatRewardOption(
  slot: number,
  program: Program,
  taken = false,
): string {
  const name = program.name
    .toUpperCase()
    .slice(0, NAME_WIDTH)
    .padEnd(NAME_WIDTH);
  const tag = programEffectTag(program);
  const body = `${slot} ${name} ${tag}`.trimEnd();
  // The caret marks the card the player actually took; the others are spent,
  // so nothing on them should read as still selectable.
  return taken ? `> ${body}  ACQUIRED` : body;
}

/** Row of the hand header in the combat grid. The list below it holds
 * `max(HAND_LAYOUT_SLOTS, count)` rows and ends on the last inner row of the
 * screen frame (`rows - 3`); the header never sits lower than the pre-0251
 * `HAND:` row. */
export function combatHandRow(
  rows: number,
  count: number = HAND_LAYOUT_SLOTS,
): number {
  const slots = Math.max(HAND_LAYOUT_SLOTS, count);
  return Math.max(
    8,
    Math.min(rows - Math.floor(rows * 0.16), rows - 3 - slots),
  );
}
