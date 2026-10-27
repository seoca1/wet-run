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

import type { GameState, GameAction, EndingChoice } from "./types.ts";
import {
  import_vfx,
  durationForKind,
  pickMovementSfxId,
} from "./state_helpers.ts";
import { AudioManager } from "../audio/manager.ts";
import { isMutatorActive, type MutableRunState } from "./run_mutators.ts";
import { iceHpForGrade, missionGradeOf } from "./ice_scaling.ts";
import { createDeceasedJockey, generateDeathSummary } from "./death_cycle.ts";
import {
  resolveEnding,
  type EndingContext,
  type ArcId,
} from "./ending_resolver.ts";
import { onMissionComplete, type FactionId } from "./faction_reputation.ts";
import {
  recordMissionComplete,
  evaluateFarGridUnlock,
} from "./far_grid_gate.ts";
import { nextHopToward } from "./matrix_navigation.ts";

/** Tier 5: matrix view actions (navigate, enter combat, jack out). */
export function applyMatrixAction(
  state: GameState,
  action: GameAction,
): GameState {
  if (action.type === "confirm" && state.matrix != null) {
    const node = state.matrix.nodes[state.currentNodeIndex];
    if (!node) return state;
    if (node.iceIds.length === 0) {
      return {
        ...state,
        message: "No ICE here — move to a node with an encounter.",
      };
    }
    const activeIce = state.iceRoster[state.activeIceIndex] ?? state.ice;
    const encounterMultiplier = isMutatorActive(
      state as unknown as MutableRunState,
      "ice_x2",
    )
      ? 2
      : 1;
    const baseCount = Math.min(node.iceIds.length * encounterMultiplier, 4);
    // Cycle the node's ICE ids so the roster actually reaches `baseCount`.
    // A plain `slice` could only ever SHORTEN the list, which made the
    // ICE_X2 mutator inert (nodes carry exactly one ice id → roster 1).
    const iceRoster = Array.from({ length: baseCount }, (_, i) => {
      const id = node.iceIds[i % node.iceIds.length] as string;
      const hp =
        node.iceHp[i % node.iceHp.length] ??
        iceHpForGrade(activeIce, missionGradeOf(state.mission));
      return { ...activeIce, id, hp };
    });
    const matrixEntryVfx: import("../renderer/combat_vfx.js").CombatVfxInstance[] =
      [import_vfx("room_flash", "TIER_GOLD", 1)];
    if (node.eventKind === "cache") {
      matrixEntryVfx.push(
        import_vfx("data_acquired", "", durationForKind("data_acquired")),
      );
    }
    return {
      ...state,
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

  // Matrix navigation - move between adjacent nodes
  if (
    (action.type === "move_north" ||
      action.type === "move_south" ||
      action.type === "move_east" ||
      action.type === "move_west") &&
    state.matrix != null
  ) {
    const node = state.matrix.nodes[state.currentNodeIndex];
    if (!node) return state;

    // Determine direction: south/east = forward, north/west = backward
    const isForward =
      action.type === "move_south" || action.type === "move_east";

    if (isForward) {
      // Graph-directed move: step to the neighbour on a shortest path to
      // the boss. Never fall back to `adjacent[0]` — that degenerates into a
      // 2-cycle and makes the boss unreachable.
      const nextIndex = nextHopToward(
        state.matrix,
        state.currentNodeIndex,
        state.matrix.bossNode,
      );
      if (nextIndex >= 0 && nextIndex < state.matrix.nodes.length) {
        // Tier 5 SFX: forward node transition dispatches MOVEMENT_STEP.
        void AudioManager.getInstance().playSfx(pickMovementSfxId(true));
        return {
          ...state,
          currentNodeIndex: nextIndex,
          turnCount: state.turnCount + 1,
          message: `Moved to ${state.matrix.nodes[nextIndex].zone}`,
        };
      }
      return { ...state, message: "No route to the objective" };
    }
    // Backward: retreat along the shortest path back to the entry node.
    const prevIndex = nextHopToward(
      state.matrix,
      state.currentNodeIndex,
      state.matrix.startNode,
    );
    if (prevIndex >= 0 && prevIndex !== state.currentNodeIndex) {
      // Tier 5 SFX: backtrack dispatches MOVEMENT_NODE.
      void AudioManager.getInstance().playSfx(pickMovementSfxId(false));
      return {
        ...state,
        currentNodeIndex: prevIndex,
        turnCount: state.turnCount + 1,
        message: `Moved back to ${state.matrix.nodes[prevIndex].zone}`,
      };
    }
    return { ...state, message: "No route back to the entry" };
  }

  if (action.type === "jack_out") {
    return {
      ...state,
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
      message: "Programs only usable in combat — press ENTER to engage ICE",
    };
  }
  return state;
}

export function applyLootAction(
  state: GameState,
  action: GameAction,
): GameState {
  if (action.type === "select_program" || action.type === "use_program") {
    return {
      ...state,
      message: "Hand empty — press ENTER to advance to next node",
    };
  }
  if (action.type !== "confirm") return state;
  const node = state.matrix?.nodes[state.currentNodeIndex];
  // Mission complete: matrix cleared, OR dead-end node (no forward path), OR boss defeated.
  const missionComplete =
    !state.matrix || !node || node.adjacent.length === 0 || node.isBoss;
  if (missionComplete) {
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
  // Graph-directed progression: step to the neighbour on a shortest path to
  // the boss. The old index-order advance (`currentNodeIndex + 1`) ignored
  // adjacency entirely and could walk into a dead end.
  const hop = nextHopToward(
    state.matrix,
    state.currentNodeIndex,
    state.matrix.bossNode,
  );
  const nextIdx = hop >= 0 ? hop : state.currentNodeIndex;
  const newVisited = state.visitedNodes.includes(nextIdx)
    ? state.visitedNodes
    : [...state.visitedNodes, nextIdx];
  // Apply loot HEAL preview: 15% of max HP (matches renderLootScreen label).
  const healedHp = Math.min(
    state.player.maxHp,
    state.player.hp + Math.floor(state.player.maxHp * 0.15),
  );
  return {
    ...state,
    runPhase: "matrix",
    currentNodeIndex: nextIdx,
    visitedNodes: newVisited,
    phase: "approach",
    player: { ...state.player, hp: healedHp },
    message: `Advancing to next node (${nextIdx}) — healed to ${healedHp}/${state.player.maxHp}`,
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
    return {
      ...state,
      phase: "combat",
      message: `Combat vs ${state.ice.name}`,
      turnCount: state.turnCount + 1,
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
