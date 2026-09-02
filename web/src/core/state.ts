/** Game state factory + reducer.
 *
 * Ports the wet_run GameState to a pure-data TypeScript model. Tier 2
 * supports multiple missions (see main.ts mission catalog).
 *
 * State machine (per wet_run combat_view_input.py):
 *   menu → approach → combat → victory | defeat → exit
 *
 * Split per ADR-0110 (2026):
 * - Core state management (this file, ~330 lines)
 * - Action handlers → state_actions.ts
 * - Helper functions → state_helpers.ts
 */

import type {
  GameState,
  GameAction,
  Ice,
  Inventory,
  Mission,
  PlayerStats,
  Program,
  SaveSlot,
} from "./types.ts";
import { makeGrid } from "./grid.ts";
import { EMPTY_LOADOUT } from "./equipment.ts";
import { generateProceduralMatrix } from "./matrix.ts";
import { DEFAULT_FACTION_SCORES } from "./faction_reputation.ts";
import missionsData from "../data/missions.json";
import type { RunMutator } from "./run_mutators.ts";
import {
  applyMatrixAction,
  applyLootAction,
  applyDeathAction,
  applyEndingAction,
  applyMenuAction,
  applyApproachAction,
  applyCombatAction,
  applyEndAction,
} from "./state_actions.ts";

const MVP_GRID_W = 80;
const MVP_GRID_H = 50;
const MVP_BASE_HP = 100;
const MVP_BASE_ALARM = 0;
const MVP_BASE_CREDITS = 0;
const MVP_BASE_HAND = 5;

/** Construct a fresh GameState for the MVP mission. */
export function makeInitialState(
  mission: Mission,
  ice: Ice,
  deck: ReadonlyArray<Program>,
  drawPile: ReadonlyArray<Program> = [],
  mutators: ReadonlyArray<RunMutator> = [],
): GameState {
  const player: PlayerStats = {
    hp: MVP_BASE_HP,
    maxHp: MVP_BASE_HP,
    alarm: MVP_BASE_ALARM,
    credits: MVP_BASE_CREDITS,
    handSize: MVP_BASE_HAND,
  };
  const inventory: Inventory = {
    credits: mission.rewards.credits,
    materials: mission.rewards.materials,
    programs: [],
  };
  const gridSize = mission.grade ? { w: 80 + (mission.grade - 1) * 20, h: 50 + (mission.grade - 1) * 10 } : { w: MVP_GRID_W, h: MVP_GRID_H };
  const matrix = generateProceduralMatrix(mission.grade || 1, mission.seed || 42, mission.id);
  const finalDrawPile = drawPile.length > 0 ? drawPile : deck.slice(MVP_BASE_HAND);
  
  return {
    phase: "menu",
    mission,
    player,
    ice: { ...ice, hp: ice.hp, armor: ice.armor, tier: ice.tier, id: ice.id, name: ice.name },
    deck: deck.slice(0, MVP_BASE_HAND),
    drawPile: finalDrawPile,
    discardPile: [],
    grid: makeGrid(gridSize.w, gridSize.h),
    message: `Mission: ${mission.title}`,
    turnCount: 0,
    graphicNovel: null,
    runPhase: "matrix",
    statusEffects: [],
    iceRoster: [ice],
    activeIceIndex: 0,
    currentNodeIndex: 0,
    matrix,
    visitedNodes: [],
    bossPhase: 0,
    endingChoice: null,
    vfxInstances: [],
    playerCombo: 0,
    comboLastHitMs: 0,
    alarmLevel: 0,
    lastAlarmTickMs: 0,
    counterWindowOpenMs: 0,
    lastEnemyAttackMs: 0,
    dixieLastAttackMs: 0,
    skillCooldowns: {},
    inventory,
    equipmentLoadout: EMPTY_LOADOUT,
    activeMutators: Object.freeze([...mutators]),
    unlockedAchievements: [],
    achievementCredits: 0,
    deceasedJockeys: [],
    lastDeathSummary: null,
    totalRuns: 1,
    totalDeaths: 0,
    longestRunMinutes: 0,
    stageState: null,
    factionScores: DEFAULT_FACTION_SCORES,
  };
}

/** Pure reducer — apply an action to a state, returning a new state. */
export function applyAction(state: GameState, action: GameAction): GameState {
  if (state.runPhase === "matrix") {
    return applyMatrixAction(state, action);
  }
  if (state.runPhase === "loot") {
    return applyLootAction(state, action);
  }
  if (state.runPhase === "ending") {
    return applyEndingAction(state, action);
  }
  if (state.runPhase === "dead") {
    return applyDeathAction(state, action);
  }
  switch (state.phase) {
    case "menu":
      return applyMenuAction(state, action);
    case "approach":
      return applyApproachAction(state, action);
    case "combat":
      return applyCombatAction(state, action);
    case "victory":
    case "defeat":
      return applyEndAction(state, action);
    case "exit":
      return state;
  }
}

/** Resolve a select_program (hand index, 1-based) to the matching use_program. */
export function resolveProgramSelection(
  state: GameState,
  action: GameAction,
): { readonly type: "use_program"; readonly programId: string } | null {
  if (action.type !== "select_program") return null;
  const idx = action.handIndex - 1;
  if (idx < 0 || idx >= state.deck.length) return null;
  const program = state.deck[idx];
  if (!program) return null;
  return { type: "use_program", programId: program.id };
}

/** Generate HUD lines from current state — feeds the right-side panel. */
export function buildHudLines(state: GameState): string[] {
   const lines: string[] = [
     `HP ${state.player.hp}/${state.player.maxHp}`,
     `Alarm ${state.player.alarm}/100`,
     `Credits ${state.player.credits}`,
   ];
   const equippedCount = Object.values(state.equipmentLoadout).filter(e => e !== null).length;
   lines.push(`Equipped: ${equippedCount}/8`);
   if (state.playerCombo > 1) {
     lines.push(`Combo x${state.playerCombo}`);
   }
   if (state.alarmLevel > 0) {
     lines.push(`ALARM ${state.alarmLevel}/5`);
   }
   if (state.bossPhase > 0 && state.bossPhase <= 4) {
     lines.push(`★ BOSS PHASE ${state.bossPhase}/4`);
   }
   lines.push("", `Phase: ${state.phase}`);
   for (let i = 0; i < state.iceRoster.length; i++) {
     const ice = state.iceRoster[i];
     const marker = i === state.activeIceIndex ? ">" : " ";
     const alive = ice.hp > 0;
     const hpDisplay = alive ? `${ice.hp}` : "DEAD";
     lines.push(`${marker} [${i + 1}] ${ice.name.slice(0, 10)} HP: ${hpDisplay}`);
   }
   lines.push("", state.message);
   return lines;
 }

/** Serialize a GameState to a SaveSlot (Tier 2 save round-trip). */
export function stateToSaveSlot(state: GameState): SaveSlot {
  const gnProgress = state.graphicNovel?.player
    ? {
        chainId: `${state.graphicNovel.player.mode}_${state.graphicNovel.player.character_id}`,
        sceneIndex: state.graphicNovel.player.scene_index,
        dialogueIndex: state.graphicNovel.player.dialogue_index,
      }
    : null;

  return {
    version: 1,
    missionId: state.mission.id,
    playerHp: state.player.hp,
    playerMaxHp: state.player.maxHp,
    playerAlarm: state.player.alarm,
    playerCredits: state.player.credits,
    turnCount: state.turnCount,
    deckIds: state.deck.map((p: Program) => p.id),
    discardIds: state.discardPile.map((p: Program) => p.id),
    drawIds: state.drawPile.map((p: Program) => p.id),
    savedAt: new Date().toISOString(),
    graphicNovelProgress: gnProgress,
  };
}

/** Reconstruct a GameState from a SaveSlot (CONTINUE option reverse). */
export function slotToGameState(
  slot: SaveSlot,
  missionCatalog: ReadonlyArray<Mission>,
  programCatalog: Readonly<Record<string, Program>>,
  iceFallback: Ice,
): GameState | null {
  const mission = missionCatalog.find((m) => m.id === slot.missionId);
  if (!mission) return null;
  const findProgram = (id: string): Program | undefined => programCatalog[id];
  const restoreHand = (ids: ReadonlyArray<string>): ReadonlyArray<Program> =>
    ids.map(findProgram).filter((p): p is Program => p !== undefined);
  const deck = restoreHand(slot.deckIds);
  const discardPile = restoreHand(slot.discardIds);
  const drawPile = restoreHand(slot.drawIds);
  if (deck.length === 0 && slot.deckIds.length > 0) return null;
  const player: PlayerStats = {
    hp: slot.playerHp,
    maxHp: slot.playerMaxHp,
    alarm: slot.playerAlarm,
    credits: slot.playerCredits,
    handSize: MVP_BASE_HAND,
  };
  const inventory: Inventory = {
    credits: slot.playerCredits,
    materials: {},
    programs: [],
  };

  let graphicNovel = null;
  if (slot.graphicNovelProgress) {
    const parts = slot.graphicNovelProgress.chainId.split("_");
    const mode = (parts[0] || "prologue") as "prologue" | "novice" | "veteran" | "heretic";
    const characterId = (parts[1] || "novice") as "novice" | "veteran" | "heretic";
    const sceneIndex = slot.graphicNovelProgress.sceneIndex;
    const dialogueIndex = slot.graphicNovelProgress.dialogueIndex;
    
    graphicNovel = {
      player: {
        mode,
        chain: [],
        character_id: characterId,
        ending: "A" as const,
        scene_index: sceneIndex,
        dialogue_index: dialogueIndex,
        elapsed_ms: 0,
        paused: false,
        done: false,
      },
      currentScene: null,
      currentText: "",
      isPaused: false,
    };
  }

  return {
    phase: "approach",
    mission,
    player,
    ice: iceFallback,
    deck,
    drawPile,
    discardPile,
    grid: makeGrid(MVP_GRID_W, MVP_GRID_H),
    message: `Resumed from autosave (turn ${slot.turnCount + 1})`,
    turnCount: slot.turnCount,
    graphicNovel,
    runPhase: "matrix",
    statusEffects: [],
    iceRoster: [iceFallback],
    activeIceIndex: 0,
    currentNodeIndex: 0,
    matrix: null,
    visitedNodes: [],
    bossPhase: 0,
    endingChoice: null,
    vfxInstances: [],
    playerCombo: 0,
    comboLastHitMs: 0,
    alarmLevel: 0,
    lastAlarmTickMs: 0,
    counterWindowOpenMs: 0,
    lastEnemyAttackMs: 0,
    dixieLastAttackMs: 0,
    skillCooldowns: {},
    inventory,
    equipmentLoadout: EMPTY_LOADOUT,
    activeMutators: Object.freeze([]),
    unlockedAchievements: [],
    achievementCredits: 0,
    deceasedJockeys: [],
    lastDeathSummary: null,
    totalRuns: 1,
    totalDeaths: 0,
    longestRunMinutes: 0,
    stageState: null,
    factionScores: DEFAULT_FACTION_SCORES,
  };
}

/** Load all missions from JSON. */
export function loadMissions(): ReadonlyArray<Mission> {
  return Object.values(missionsData as Readonly<Record<string, Mission>>);
}

/** Get mission by ID. */
export function getMissionById(id: string): Mission | undefined {
  const data = missionsData as Readonly<Record<string, Mission>>;
  return data[id];
}

// Re-export helpers for backward compatibility
export { durationMsForKind } from "./state_helpers.ts";
