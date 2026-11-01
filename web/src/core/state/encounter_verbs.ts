import type { GameAction, GameState, Ice, Program } from "../types";
import programs from "../../data/programs.json";
import { iceHpForGrade, missionGradeOf } from "../combat/ice_scaling";
import { clearIceEffects } from "../combat/ice_combat_effects";
import { durationForKind, import_vfx } from "./state_helpers";

// Owner-set route prices: the combat-only balance harness never walks the graph
// and cannot validate them. Validate the route economy with real play passes.
export const ENCOUNTER_VERB_COSTS = {
  probe: 8, // Small but nonzero information investment before committing.
  bypass: 60, // At most one bypass per run: COST only rises and the cap is 100.
  limit: 100, // Existing player.alarm cap; no new resource or TRACE coupling.
} as const;

export const ENCOUNTER_VERBS = [
  "PROBE",
  "BYPASS",
  "BREACH",
  "JACK OUT",
  "SCAN",
] as const;
export type EncounterVerb = (typeof ENCOUNTER_VERBS)[number];

// parseProgram drops role; resolve catalog metadata here without changing combat.
// Utility T1–T3 all grant the same intel, with no tier-scaled price or effect.
const scanProgramIds = new Set(
  Object.entries(programs)
    .filter(([, program]) => program.role === "utility")
    .map(([id]) => id),
);

export function encounterScanProgram(state: GameState): Program | undefined {
  return state.deck.find((program) => scanProgramIds.has(program.id));
}

export function bypassBlockReason(state: GameState): string | null {
  const node = state.matrix?.nodes[state.currentNodeIndex];
  if (!node) return "No encounter to bypass.";
  // applyLootAction completes the run only after combat at these terminal nodes.
  if (node.isBoss) return "Must BREACH to complete the run.";
  if (node.adjacent.length === 0) return "Must BREACH: no adjacent route.";
  return null;
}

/** ADR-0250: a node is resolved for travel once cleared or bypassed this run. */
export function encounterResolved(state: GameState, index: number): boolean {
  return (
    (state.clearedEncounterNodes?.includes(index) ?? false) ||
    (state.bypassedEncounterNodes?.includes(index) ?? false)
  );
}

/** Unresolved ICE at `index`: arriving opens the decision, leaving is blocked. */
export function encounterGates(state: GameState, index: number): boolean {
  const node = state.matrix?.nodes[index];
  return (
    node !== undefined &&
    node.iceIds.length > 0 &&
    !encounterResolved(state, index)
  );
}

function bypassPayable(state: GameState): boolean {
  return (
    bypassBlockReason(state) === null &&
    state.player.alarm + ENCOUNTER_VERB_COSTS.bypass <=
      ENCOUNTER_VERB_COSTS.limit
  );
}

/** Message shown when the gate opens the decision: every way forward. */
export function encounterGateMessage(state: GameState): string {
  const bypass =
    bypassBlockReason(state) !== null
      ? "BYPASS: blocked here"
      : !bypassPayable(state)
        ? "BYPASS: COST too high"
        : `BYPASS: ${ENCOUNTER_VERB_COSTS.bypass} COST (once per run)`;
  return `Travel blocked. BREACH: fight. ${bypass}. JACK OUT: abandon run.`;
}

function exitsHint(state: GameState): string {
  return bypassPayable(state)
    ? "Exits: BYPASS, BREACH, JACK OUT."
    : "Exits: BREACH, JACK OUT (BYPASS blocked).";
}

/** Load and run start count as an arrival: standing on unresolved ICE with no
 * decision open opens it, so a save-reload cannot skip the encounter. */
export function openArrivalEncounter(state: GameState): GameState {
  if (
    state.runPhase !== "matrix" ||
    state.encounterDecision ||
    !encounterGates(state, state.currentNodeIndex)
  )
    return state;
  return {
    ...state,
    selectedMatrixNodeIndex: null,
    encounterDecision: { selectedVerb: null, probed: false },
    message: encounterGateMessage(state),
  };
}

/** JACK OUT (verb or ESC) on the Matrix ends the run: the controller must
 * leave the board, or Enter would land back on the same ICE. */
export function runAbandoned(previous: GameState, next: GameState): boolean {
  return (
    previous.runPhase === "matrix" &&
    previous.phase !== "menu" &&
    next.runPhase === "matrix" &&
    next.phase === "menu"
  );
}

/** Verbs the arrows can land on: SCAN needs a utility program in hand. */
function selectableVerbs(state: GameState): readonly EncounterVerb[] {
  const scannable = encounterScanProgram(state) !== undefined;
  return ENCOUNTER_VERBS.filter((verb) => verb !== "SCAN" || scannable);
}

/** Shared by paid intel and Breach so mutator copies and HP fallbacks agree. */
export function encounterRoster(state: GameState): readonly Ice[] {
  const node = state.matrix?.nodes[state.currentNodeIndex];
  if (!node || node.iceIds.length === 0) return [];
  const activeIce = state.iceRoster[state.activeIceIndex] ?? state.ice;
  const encounterMultiplier = state.activeMutators.includes("ice_x2") ? 2 : 1;
  const baseCount = Math.min(node.iceIds.length * encounterMultiplier, 4);
  // Preserve the existing roster construction, including ICE_X2 cycling.
  return Array.from({ length: baseCount }, (_, i) => {
    const id = node.iceIds[i % node.iceIds.length] ?? activeIce.id;
    const hp =
      node.iceHp[i % node.iceHp.length] ??
      iceHpForGrade(activeIce, missionGradeOf(state.mission));
    return { ...activeIce, id, hp, maxHp: hp };
  });
}

export function applyEncounterDecision(
  state: GameState,
  action: GameAction,
): GameState {
  const decision = state.encounterDecision;
  if (!decision) return state;
  if (
    ["move_north", "move_south", "move_east", "move_west"].includes(action.type)
  ) {
    const forward = action.type === "move_south" || action.type === "move_east";
    const verbs = selectableVerbs(state);
    const current = verbs.findIndex((verb) => verb === decision.selectedVerb);
    const index =
      current < 0
        ? forward
          ? 0
          : verbs.length - 1
        : (current + (forward ? 1 : -1) + verbs.length) % verbs.length;
    return {
      ...state,
      encounterDecision: { ...decision, selectedVerb: verbs[index] ?? null },
    };
  }
  if (action.type !== "confirm") return state;
  const verb = decision.selectedVerb;
  const revealed = `Threat already revealed. ${exitsHint(state)}`;
  switch (verb) {
    case null:
      return {
        ...state,
        message: `Nothing selected. Press ↓ to pick a verb, then ENTER. ${exitsHint(state)}`,
      };
    case "SCAN": {
      if (decision.probed) return { ...state, message: revealed };
      const program = encounterScanProgram(state);
      if (!program) {
        return {
          ...state,
          message: "SCAN unavailable — no utility program in hand.",
        };
      }
      const spentIndex = state.deck.indexOf(program);
      return {
        ...state,
        deck: state.deck.filter((_, index) => index !== spentIndex),
        discardPile: [...state.discardPile, program],
        encounterDecision: { ...decision, probed: true },
        message: `${program.name} discarded — threat revealed; combat card spent.`,
      };
    }
    case "PROBE":
    case "BYPASS": {
      const bypassReason = bypassBlockReason(state);
      if (verb === "BYPASS" && bypassReason) {
        return { ...state, message: `BYPASS blocked — ${bypassReason}` };
      }
      if (verb === "PROBE" && decision.probed)
        return { ...state, message: revealed };
      const cost =
        verb === "PROBE"
          ? ENCOUNTER_VERB_COSTS.probe
          : ENCOUNTER_VERB_COSTS.bypass;
      if (state.player.alarm + cost > ENCOUNTER_VERB_COSTS.limit) {
        return {
          ...state,
          message: `COST too high for ${verb} — choose another verb.`,
        };
      }
      const paid = {
        ...state,
        player: { ...state.player, alarm: state.player.alarm + cost },
      };
      return verb === "PROBE"
        ? {
            ...paid,
            encounterDecision: { ...decision, probed: true },
            message: bypassReason
              ? "Threat revealed — choose BREACH or JACK OUT."
              : "Threat revealed — choose BYPASS or BREACH.",
          }
        : {
            ...paid,
            encounterDecision: null,
            selectedMatrixNodeIndex: null,
            bypassedEncounterNodes: [
              ...(state.bypassedEncounterNodes ?? []),
              state.currentNodeIndex,
            ],
            message: "Bypassed — no reward. Routes are open: ↑↓ then ENTER.",
          };
    }
    case "BREACH": {
      const node = state.matrix?.nodes[state.currentNodeIndex];
      if (
        !node ||
        state.clearedEncounterNodes?.includes(state.currentNodeIndex)
      )
        return state;
      const iceRoster = encounterRoster(state);
      const matrixEntryVfx = [import_vfx("room_flash", "TIER_GOLD", 1)];
      if (node.eventKind === "cache") {
        matrixEntryVfx.push(
          import_vfx("data_acquired", "", durationForKind("data_acquired")),
        );
      }
      return {
        ...clearIceEffects(state),
        encounterDecision: null,
        selectedMatrixNodeIndex: null,
        runPhase: "combat",
        phase: "approach",
        message: `Entering ${node.zone}... (${iceRoster.length} ICE)`,
        iceRoster,
        activeIceIndex: 0,
        bossPhase: node.isBoss ? 1 : 0,
        turnCount: state.turnCount + 1,
        vfxInstances: [...state.vfxInstances, ...matrixEntryVfx],
      };
    }
    case "JACK OUT":
      return {
        ...state,
        encounterDecision: null,
        phase: "menu",
        message: "Jacked out — run abandoned",
        vfxInstances: [
          ...state.vfxInstances,
          import_vfx(
            "jackout_whiteout",
            "",
            durationForKind("jackout_whiteout"),
          ),
        ],
      };
    default: {
      const exhaustive: never = verb;
      return exhaustive;
    }
  }
}
