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
    };
  });
}

function afterText(a: ProgramAffordance): string {
  return a.blocked ? "BLOCKED" : `${a.after}/${COST_LIMIT}`;
}

/** Full canvas row, e.g. `1 STRIKE    COST +3  → 41/100   TARGET ICE`. */
export function formatAffordanceRow(a: ProgramAffordance): string {
  const name = a.name.padEnd(NAME_WIDTH);
  const cost = `+${a.cost}`.padEnd(3);
  return `${a.slot} ${name} COST ${cost} → ${afterText(a).padEnd(7)}  TARGET ${a.target}`;
}

/** Narrow canvas row, e.g. `1 STRIKE    +3   41/100   ICE`; its columns line
 * up under `COMPACT_HAND_HEADER`, which names them. */
export function formatCompactAffordanceRow(a: ProgramAffordance): string {
  const name = a.name.padEnd(NAME_WIDTH);
  const cost = `+${a.cost}`.padEnd(4);
  return `${a.slot} ${name} ${cost} ${afterText(a).padEnd(8)} ${a.target}`;
}

/** Column legend for the narrow rows. */
export const COMPACT_HAND_HEADER = `${"HAND".padEnd(NAME_WIDTH + 3)}${"COST".padEnd(5)}${"AFTER".padEnd(9)}TARGET`;

/** Longest full row a hand can produce (two-digit COST, `100/100`, `ALL ICE`). */
export const FULL_ROW_WIDTH = formatAffordanceRow({
  slot: 9,
  programId: "",
  name: "",
  cost: 99,
  after: COST_LIMIT,
  blocked: false,
  target: "ALL ICE",
}).length;

/** Visible lines of a touch button (narrow enough for five in a phone row). */
export function touchAffordanceLines(a: ProgramAffordance): readonly string[] {
  return [
    `${a.slot} COST+${a.cost}`,
    a.name,
    a.blocked ? "BLOCKED" : `→ ${a.after}/${COST_LIMIT}`,
    a.target,
  ];
}

/** Spoken label for a touch button; says the same facts as the canvas row. */
export function affordanceAriaLabel(a: ProgramAffordance): string {
  const outcome = a.blocked
    ? `blocked, over ${COST_LIMIT}`
    : `to ${a.after} of ${COST_LIMIT}`;
  return `${a.slot} ${a.name}, COST plus ${a.cost}, ${outcome}, target ${a.target}`;
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
