/** Non-combat phase action handlers — split from state_actions.ts per ADR-0110.
 *
 * Covers the phase transitions that do not run the combat tick:
 * - applyMatrixAction: matrix navigation + encounter entry
 * - applyLootAction: post-combat loot + mission completion
 * - applyDeathAction: death cycle / restart
 * - applyEndingAction: ending screen
 * - applyMenuAction: main menu
 * - applyApproachAction: pre-combat
 * - applyEndAction: victory/defeat exit
 *
 * The combat tick handlers live in `state_actions_combat.ts`; program
 * resolution lives in `state_actions_programs.ts`. All three are re-exported
 * from `state_actions.ts` so existing imports keep working.
 */

import type { GameState, GameAction, EndingChoice } from "../types";
import {
  import_vfx,
  import_vfx_deterministic,
  durationForKind,
  pickMovementSfxId,
} from "./state_helpers";
import { iceIntroPayload } from "../combat/combat_entry_vfx";
import { AudioManager } from "../../audio/manager";
import {
  applyEncounterDecision,
  encounterGateMessage,
  encounterGates,
  encounterResolved,
  openArrivalEncounter,
} from "./encounter_verbs";
import { createDeceasedJockey, generateDeathSummary } from "./death_cycle";
import { isTerminalNode } from "./run_end";
import { offeredCardIds, rewardProgram } from "./card_reward";
import {
  resolveEnding,
  type EndingContext,
  type ArcId,
} from "../combat/ending_resolver";
import { onMissionComplete, type FactionId } from "./faction_reputation";
import {
  recordMissionComplete,
  evaluateFarGridUnlock,
} from "../dungeon/far_grid_gate";

/** Tier 5: matrix view actions (navigate, enter combat, jack out). */
export function applyMatrixAction(
  state: GameState,
  action: GameAction,
): GameState {
  if (state.encounterDecision && action.type !== "jack_out") {
    return applyEncounterDecision(state, action);
  }
  if (action.type === "confirm" && state.matrix != null) {
    const node = state.matrix.nodes[state.currentNodeIndex];
    if (!node) return state;
    const destination = state.selectedMatrixNodeIndex;
    // ADR-0250: the gate is on the entry only. Departing never reopens the
    // decision; load and run start open it instead (openArrivalEncounter).
    if (destination != null && node.adjacent.includes(destination)) {
      const target = state.matrix.nodes[destination];
      if (!target) return state;
      void AudioManager.getInstance().playSfx(pickMovementSfxId(true));
      return openArrivalEncounter({
        ...state,
        currentNodeIndex: destination,
        selectedMatrixNodeIndex: null,
        encounterDecision: null,
        visitedNodes: state.visitedNodes.includes(destination)
          ? state.visitedNodes
          : [...state.visitedNodes, destination],
        turnCount: state.turnCount + 1,
        message: `Moved to ${target.zone} — ↑↓ picks the next route`,
      });
    }
    // Enter with no route on the unresolved ICE you stand on enters it.
    if (encounterGates(state, state.currentNodeIndex)) {
      return {
        ...state,
        selectedMatrixNodeIndex: null,
        encounterDecision: { selectedVerb: null, probed: false },
        message: encounterGateMessage(state),
      };
    }
    if (encounterResolved(state, state.currentNodeIndex)) {
      return {
        ...state,
        message: "Encounter resolved — choose an adjacent route.",
      };
    }
    if (node.iceIds.length === 0) {
      return {
        ...state,
        message: "No ICE here — move to a node with an encounter.",
      };
    }
    return state;
  }

  // List navigation only: travel (including retreat) requires a separate confirm.
  if (
    (action.type === "move_north" ||
      action.type === "move_south" ||
      action.type === "move_east" ||
      action.type === "move_west") &&
    state.matrix != null
  ) {
    const node = state.matrix.nodes[state.currentNodeIndex];
    if (!node) return state;

    const forward = action.type === "move_south" || action.type === "move_east";
    const neighbours = node.adjacent;
    if (neighbours.length === 0)
      return { ...state, message: "No adjacent routes" };
    const current = neighbours.findIndex(
      (i) => i === state.selectedMatrixNodeIndex,
    );
    const index =
      current < 0
        ? forward
          ? 0
          : neighbours.length - 1
        : (current + (forward ? 1 : -1) + neighbours.length) %
          neighbours.length;
    return {
      ...state,
      selectedMatrixNodeIndex: neighbours[index],
      message: encounterGates(state, neighbours[index] ?? -1)
        ? "Route highlighted — ENTER enters its ICE; ↑↓ to change destination"
        : "Route highlighted — ENTER to travel; ↑↓ to change destination",
    };
  }

  if (action.type === "jack_out") {
    return {
      ...state,
      encounterDecision: null,
      phase: "menu",
      message: "Jacked out — run abandoned",
      vfxInstances: [
        ...state.vfxInstances,
        import_vfx("jackout_whiteout", "", durationForKind("jackout_whiteout")),
      ],
    };
  }
  if (action.type === "select_program") {
    return {
      ...state,
      message:
        "ENTER for encounter options; utility cards can SCAN before combat",
    };
  }
  return state;
}

export function applyLootAction(
  state: GameState,
  action: GameAction,
): GameState {
  // Mission complete: matrix cleared, OR dead-end node (no forward path), OR boss defeated.
  if (isTerminalNode(state)) return applyTerminalLoot(state, action);

  // ADR-0259: a non-terminal win offers cards — the run's only growth.
  if (action.type === "select_program") {
    return takeCardReward(state, action.handIndex - 1);
  }
  if (action.type === "use_program") {
    return {
      ...state,
      message: "Hand empty — press ENTER to return to route selection",
    };
  }
  if (action.type !== "confirm") return state;
  // ENTER skips the card and travels on.
  return continueToMatrix(state);
}

/** Confirm (or ESC) on a terminal loot screen: the run is over. */
function applyTerminalLoot(state: GameState, action: GameAction): GameState {
  if (action.type === "select_program" || action.type === "use_program") {
    return {
      ...state,
      message: "Hand empty — press ENTER to finish the run",
    };
  }
  // ADR-0254: the terminal loot footer promises only ENTER, and cancel stays
  // a no-op, so the screen keeps saying the truth.
  if (action.type !== "confirm") return state;
  const missionFaction = getMissionFaction(state.mission.id);
  let updatedScores = state.factionScores;
  if (missionFaction) {
    updatedScores = onMissionComplete(updatedScores, missionFaction);
  }
  const arc: ArcId = (state.mission.arc as ArcId) || 1;
  // ADR-0213 Phase 2 + tightening: full Sprawl Arc-1 clear unlocks the Far
  // Grid. Always record the mission id; on Arc-1, route the unlock decision
  // through the helper (legacy flag short-circuits to keep already-unlocked
  // saves unlocked; otherwise the helper evaluates the full-clear rule).
  recordMissionComplete(state.mission.id);
  if (arc === 1) {
    evaluateFarGridUnlock();
  }
  const ctx: EndingContext = {
    arc,
    hp: state.player.hp,
    maxHp: state.player.maxHp,
    credits: state.inventory.credits,
    missionsCompleted: 1, // single-mission run: this mission just completed
    totalDeaths: state.totalDeaths,
    factionScores: updatedScores,
    choices: [],
  };
  const ending = resolveEnding(ctx);
  return {
    ...state,
    runPhase: "ending",
    endingChoice: ending.id as EndingChoice,
    factionScores: updatedScores,
  };
}

/**
 * Take the offered card at `index` (0-based).
 *
 * ADR-0261: taking no longer travels on immediately. The screen holds the
 * moment so the acquisition is visible, and ENTER carries on — the classic
 * "pick, then proceed" beat. `cardRewardTaken` records the choice so a reload
 * shows the same thing instead of offering a second card.
 */
function takeCardReward(state: GameState, index: number): GameState {
  if (state.cardRewardTaken) {
    const already = rewardProgram(state.cardRewardTaken);
    return {
      ...state,
      message: `${already?.name ?? state.cardRewardTaken} already taken — press ENTER`,
    };
  }
  const offered = offeredCardIds(state);
  const id = index >= 0 && index < offered.length ? offered[index] : undefined;
  if (id === undefined) {
    return {
      ...state,
      message:
        offered.length === 0
          ? "No new programs left — press ENTER to continue"
          : `Reward ${index + 1} does not exist — press ENTER to continue`,
    };
  }
  const card = rewardProgram(id);
  if (card === undefined) {
    return {
      ...state,
      message: "Reward unavailable — press ENTER to continue",
    };
  }
  return {
    ...state,
    // The card joins the draw pile, so it arrives when the hand recycles.
    drawPile: [...state.drawPile, card],
    inventory: {
      ...state.inventory,
      programs: [...state.inventory.programs, card],
    },
    cardRewardTaken: card.id,
    message: `Acquired ${card.name} — press ENTER to continue`,
  };
}

/** Non-terminal loot resolution: heal 15% and return to route selection. */
function continueToMatrix(state: GameState): GameState {
  const newVisited = state.visitedNodes.includes(state.currentNodeIndex)
    ? state.visitedNodes
    : [...state.visitedNodes, state.currentNodeIndex];
  // Apply loot HEAL preview: 15% of max HP (matches renderLootScreen label).
  const healedHp = Math.min(
    state.player.maxHp,
    state.player.hp + Math.floor(state.player.maxHp * 0.15),
  );
  // ADR-0261: name the card the player just took, so the destination carries
  // the growth instead of the reward vanishing with the screen.
  const taken = state.cardRewardTaken
    ? rewardProgram(state.cardRewardTaken)
    : undefined;
  const grown = taken ? `Took ${taken.name}. ` : "";
  return {
    ...state,
    runPhase: "matrix",
    selectedMatrixNodeIndex: null,
    visitedNodes: newVisited,
    phase: "approach",
    player: { ...state.player, hp: healedHp },
    // Clear the offer memory on the way out.
    cardRewardTaken: null,
    message: `${grown}Choose an adjacent route — healed to ${healedHp}/${state.player.maxHp}`,
  };
}

export function applyDeathAction(
  state: GameState,
  action: GameAction,
): GameState {
  if (action.type === "trigger_death") {
    const jockey = createDeceasedJockey({
      name: state.mission.title,
      characterId: "novice",
      grade: state.mission.grade ?? 1,
      missionId: state.mission.id,
      inventory: state.inventory.programs.map((p) => p.id),
      missionsCompleted: 0,
      dataRecovered: 0,
      playtimeMinutes: Math.floor(state.turnCount * 0.5),
    });
    const summary = generateDeathSummary(
      jockey,
      state.totalRuns,
      state.totalDeaths + 1,
      Math.max(state.longestRunMinutes, Math.floor(state.turnCount * 0.5)),
    );
    return {
      ...state,
      phase: "defeat",
      lastDeathSummary: summary,
      totalDeaths: state.totalDeaths + 1,
      deceasedJockeys: [...state.deceasedJockeys, jockey],
      message: "FLATLINE",
    };
  }
  if (action.type === "confirm" || action.type === "jack_out") {
    // The defeat screen must be escapable. ENTER / ESC end the run at the
    // title, mirroring the ending screen (ADR-0252). Before this the screen
    // accepted no input at all, so a flatline parked the player forever.
    return { ...state, phase: "menu", message: "FLATLINE — back at the title" };
  }
  if (action.type === "select_restart") {
    switch (action.choice) {
      case "new_jockey":
        return {
          ...state,
          phase: "menu",
          runPhase: "matrix",
          message: "Select a new jockey",
        };
      case "same_jockey":
        return {
          ...state,
          phase: "menu",
          runPhase: "matrix",
          player: { ...state.player, hp: state.player.maxHp, alarm: 0 },
          message: "The Finn took you back. Even dead, you owe him.",
        };
      case "hall_of_dead":
        return { ...state, phase: "menu", message: "Hall of Dead Jockeys" };
      case "main_menu":
        return { ...state, phase: "menu", runPhase: "matrix" };
    }
  }
  if (action.type === "view_hall_of_dead") {
    return { ...state, phase: "menu", message: "Hall of Dead Jockeys" };
  }
  return state;
}

export function applyEndingAction(
  state: GameState,
  action: GameAction,
): GameState {
  if (action.type === "confirm" || action.type === "jack_out") {
    return {
      ...state,
      phase: "menu",
      message: `Ending ${state.endingChoice}: returning to title`,
    };
  }
  return state;
}

export function applyMenuAction(
  state: GameState,
  action: GameAction,
): GameState {
  if (action.type === "confirm") {
    return {
      ...state,
      phase: "approach",
      message: "Jacking in...",
      vfxInstances: [
        ...state.vfxInstances,
        import_vfx("jackin_glitch", "", durationForKind("jackin_glitch")),
      ],
    };
  }
  if (action.type === "jack_out") {
    return { ...state, phase: "exit" };
  }
  return state;
}

export function applyApproachAction(
  state: GameState,
  action: GameAction,
): GameState {
  if (action.type === "confirm") {
    // P15 — combat entry presentation. The `ice_intro` banner ("INCOMING:
    // <ICE>" + scanning line) had a renderer but no spawn site, so combat
    // started as an instant cut from the approach screen.
    // `import_vfx_deterministic` draws no `Math.random` value — the balance
    // harness seeds `Math.random`, so a new `import_vfx` call here would
    // silently shift the ADR-0229 grade curve.
    return {
      ...state,
      phase: "combat",
      message: `Combat vs ${state.ice.name}`,
      turnCount: state.turnCount + 1,
      vfxInstances: [
        ...state.vfxInstances,
        import_vfx_deterministic(
          "ice_intro",
          iceIntroPayload(state.ice.name),
          durationForKind("ice_intro"),
        ),
      ],
    };
  }
  if (action.type === "select_program") {
    return {
      ...state,
      message:
        "Press ENTER (or SPACE) to engage combat — programs activate during combat",
    };
  }
  if (action.type === "jack_out") {
    return { ...state, phase: "exit" };
  }
  return state;
}

export function applyEndAction(
  state: GameState,
  action: GameAction,
): GameState {
  if (action.type === "confirm") {
    return { ...state, phase: "exit" };
  }
  return state;
}

function getMissionFaction(missionId: string): FactionId | null {
  if (missionId.includes("hosaka")) return "hosaka";
  if (missionId.includes("maas")) return "maas";
  if (missionId.includes("sense") || missionId.includes("net"))
    return "sense_net";
  if (missionId.includes("ta")) return "ta";
  return null;
}
