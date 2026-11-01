import type { GameAction, GameState, Ice, Program } from "../types";
import programs from "../../data/programs.json";
import { iceHpForGrade, missionGradeOf } from "../combat/ice_scaling";
import { clearIceEffects } from "../combat/ice_combat_effects";
import { durationForKind, import_vfx } from "./state_helpers";

// Conservative route-economy starting points: the combat-only balance harness
// never walks the graph. Validate these prices with a real play pass.
export const ENCOUNTER_VERB_COSTS = {
  probe: 8, // Small but nonzero information investment before committing.
  bypass: 30, // Three passages consume 90/100, displacing expensive programs.
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
    const current = ENCOUNTER_VERBS.findIndex(
      (verb) => verb === decision.selectedVerb,
    );
    const index =
      current < 0
        ? forward
          ? 0
          : ENCOUNTER_VERBS.length - 1
        : (current + (forward ? 1 : -1) + ENCOUNTER_VERBS.length) %
          ENCOUNTER_VERBS.length;
    return {
      ...state,
      encounterDecision: { ...decision, selectedVerb: ENCOUNTER_VERBS[index] },
    };
  }
  if (action.type !== "confirm") return state;
  const verb = decision.selectedVerb;
  switch (verb) {
    case null:
      return { ...state, message: "Choose a verb with arrows, then ENTER." };
    case "SCAN": {
      if (decision.probed) return state;
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
      if (verb === "PROBE" && decision.probed) return state;
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
            bypassedEncounterNodeIndex: state.currentNodeIndex,
            message:
              "Bypassed — no reward. Choose a route; ENTER reopens this encounter.",
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
