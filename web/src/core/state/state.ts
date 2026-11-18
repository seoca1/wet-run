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
} from "../types";
export type { GameState } from "../types";
import { makeGrid } from "../grid";
import { EMPTY_LOADOUT } from "./loadout";
import { EQUIP_SLOTS } from "./equipment";
import { generateProceduralMatrix } from "../dungeon/matrix";
import { missionGradeOf, missionSeedOf } from "../combat/ice_scaling";
import { applyIdleAlarmTick } from "../combat/idle_alarm";
import { DIXIE_ATTACK_EVERY_N_PLAYER_TURNS } from "../combat/state_actions_combat";
import { DEFAULT_FACTION_SCORES } from "./faction_reputation";
import { openArrivalEncounter } from "./encounter_verbs";
import { missionIce } from "./mission_ice";
import { campaignContinues, type Campaign } from "./campaign";
import { UNIQUE_PROGRAMS } from "./card_reward";
import { isTerminalNode } from "./run_end";
import missionsData from "../../data/missions.json";
import type { RunMutator } from "./run_mutators";
import {
  applyMatrixAction,
  applyLootAction,
  applyDeathAction,
  applyEndingAction,
  applyMenuAction,
  applyApproachAction,
  applyCombatAction,
  applyEndAction,
} from "./state_actions";

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
  // Mission schema field names: matrix_seed (not seed), grade_max/grade_min (not grade).
  const missionSeed: number = missionSeedOf(mission);
  const missionGrade: number = missionGradeOf(mission);
  const gridSize = missionGrade
    ? { w: 80 + (missionGrade - 1) * 20, h: 50 + (missionGrade - 1) * 10 }
    : { w: MVP_GRID_W, h: MVP_GRID_H };
  const matrix = generateProceduralMatrix(
    missionGrade,
    missionSeed,
    mission.id,
  );
  const finalDrawPile =
    drawPile.length > 0 ? drawPile : deck.slice(MVP_BASE_HAND);

  return {
    phase: "menu",
    mission,
    player,
    ice: {
      ...ice,
      hp: ice.hp,
      armor: ice.armor,
      tier: ice.tier,
      id: ice.id,
      name: ice.name,
    },
    deck: deck.slice(0, MVP_BASE_HAND),
    drawPile: finalDrawPile,
    discardPile: [],
    grid: makeGrid(gridSize.w, gridSize.h),
    message: `Mission: ${mission.title}`,
    combatLog: [],
    turnCount: 0,
    graphicNovel: null,
    runPhase: "matrix",
    statusEffects: [],
    iceRoster: [ice],
    activeIceIndex: 0,
    currentNodeIndex: matrix.startNode,
    matrix,
    visitedNodes: [],
    clearedEncounterNodes: [],
    bypassedEncounterNodes: [],
    intelNodes: [],
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
    dixiePlayerTurnsSinceAttack: DIXIE_ATTACK_EVERY_N_PLAYER_TURNS - 1,
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
    factionScores: DEFAULT_FACTION_SCORES,
  };
}

/** Start the contract's next mission (ADR-0315 slice 2).
 *
 * `finished` is the state the terminal loot produced: its faction scores are
 * already updated and the mission is already recorded. What carries:
 *
 * - **credits** — ADR-0314 makes wealth an ending condition, and a condition
 *   only means something if it accumulates. `inventory.credits` stays per
 *   mission: it is the crafting wallet seeded from the mission's reward.
 * - **the deck** — the hand, the draw pile and the discard are one deck again
 *   and the next mission deals from it. Carrying a deck measured ~neutral
 *   (ADR-0315), and it is the run's lasting growth besides the unique.
 * - **the unique** — one per campaign, not one per mission (ADR-0303/0311).
 *
 * What resets: HP to full (Q3 — the advance between missions is where a run
 * recovers), COST, the turn count, and the whole board. The map a run already
 * walked belongs to the mission that had it.
 */
function startNextLeg(previous: GameState, finished: GameState): GameState {
  const campaign: Campaign | undefined = previous.campaign;
  const leg = campaign?.legs[campaign.completed + 1];
  if (campaign === undefined || leg === undefined) return finished;
  const deck = [...previous.deck, ...previous.drawPile, ...previous.discardPile];
  const fresh = makeInitialState(leg.mission, leg.ice, deck);
  return {
    ...fresh,
    campaign: { legs: campaign.legs, completed: campaign.completed + 1 },
    player: { ...fresh.player, credits: previous.player.credits },
    ...(previous.uniquePickDone ? { uniquePickDone: true } : {}),
    jockeyId: previous.jockeyId,
    factionScores: finished.factionScores,
    totalRuns: previous.totalRuns,
    totalDeaths: previous.totalDeaths,
    unlockedAchievements: previous.unlockedAchievements,
    achievementCredits: previous.achievementCredits,
    message: `Contract ${campaign.completed + 2}/${campaign.legs.length} — ${leg.mission.title}`,
  };
}

/** Pure reducer — apply an action to a state, returning a new state. */
export function applyAction(state: GameState, action: GameAction): GameState {
  if (action.type === "idle_tick") {
    return applyIdleAlarmTick(state, action.idleSinceMs, Date.now());
  }
  if (state.runPhase === "matrix") {
    return applyMatrixAction(state, action);
  }
  if (state.runPhase === "loot") {
    const next = applyLootAction(state, action);
    // ADR-0315 slice 2: a finished mission with another leg behind it starts
    // that leg instead of ending the run. The reducer resolved an ending on the
    // way through (it cannot know about the contract), so this boundary — which
    // owns `makeInitialState` — replaces it with the next mission.
    if (next.runPhase === "ending" && campaignContinues(state.campaign)) {
      return startNextLeg(state, next);
    }
    return next;
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
    case "combat": {
      const result = applyCombatAction(state, action);
      if (result.runPhase !== "loot") return result;
      // Both program kills and companion kills resolve through this run boundary.
      const cleared = state.clearedEncounterNodes ?? [];
      return {
        ...result,
        clearedEncounterNodes: cleared.includes(state.currentNodeIndex)
          ? cleared
          : [...cleared, state.currentNodeIndex],
      };
    }
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
  // ADR-0259: a digit means "play the program" only in combat. On the loot
  // screen the same digits pick a card reward, and leftover hand cards must
  // not turn the press into a play.
  if (state.runPhase !== "combat") return null;
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
    `COST ${state.player.alarm}/100`,
    `Credits ${state.player.credits}`,
  ];
  const equippedCount = state.equipmentLoadout.allSlotsFilled().length;
  lines.push(`Equipped: ${equippedCount}/${EQUIP_SLOTS.length}`);
  // ADR-0322: the growth, in one line. Measured first: a winning run takes
  // almost no cards (mean deck 5.0 at g4), so the deck's size and tier are the
  // honest readout of whether the runner is growing at all.
  lines.push(growthLine(state));
  if (state.playerCombo > 1) {
    lines.push(`Combo x${state.playerCombo}`);
  }
  if (state.alarmLevel > 0) {
    lines.push(`TRACE ${state.alarmLevel}/5`);
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
    lines.push(
      `${marker} [${i + 1}] ${ice.name.slice(0, 10)} HP: ${hpDisplay}`,
    );
  }
  lines.push("", ...recentLogLines(state));
  return lines;
}

/** The runner's growth in one short line: deck, its average tier, uniques.
 *
 * ADR-0322. The HUD already carried credits and equipped slots; nothing carried
 * the deck's own shape, which is the axis the loot stop grows. A winning run
 * takes almost no cards (measured mean 5.0 at g4), so this line is also the
 * quickest way to see that growth is not happening.
 *
 * Pure and cheap: one pass over the three piles.
 */
export function growthLine(state: GameState): string {
  const cards = [...state.deck, ...state.drawPile, ...state.discardPile];
  const tiers = cards
    .map((p) => p.tier)
    .filter((t): t is number => Number.isFinite(t));
  const avg = tiers.length > 0 ? tiers.reduce((a, b) => a + b, 0) / tiers.length : 0;
  const uniques = cards.filter((p) => UNIQUE_PROGRAMS.has(p.id)).length;
  const uniqueNote = uniques > 0 ? ` · UNQ ${uniques}` : "";
  return `Deck ${cards.length} · T${avg.toFixed(1)}${uniqueNote}`;
}

/** The combat log lines to show in the HUD.
 *
 * `combatLog` is newest-first, so the first four entries are the four most
 * recent events. Falls back to `state.message` when the log is empty (a
 * fresh run, or a state built without the log).
 */
function recentLogLines(state: GameState): string[] {
  if (state.combatLog.length === 0) return [state.message];
  return state.combatLog.slice(0, 4);
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
    ...(state.cardRewardTaken
      ? { cardRewardTaken: state.cardRewardTaken }
      : {}),
    ...(state.uniquePickDone ? { uniquePickDone: true } : {}),
    ...(state.jockeyId ? { jockeyId: state.jockeyId } : {}),
    // ADR-0315 slice 2: a campaign keeps its contract. Ids only, so a slot
    // stays a recipe the restore path can rebuild from the catalogs.
    ...(state.campaign
      ? {
          campaignMissionIds: state.campaign.legs.map((leg) => leg.mission.id),
          campaignCompleted: state.campaign.completed,
        }
      : {}),
    discardIds: state.discardPile.map((p: Program) => p.id),
    drawIds: state.drawPile.map((p: Program) => p.id),
    savedAt: new Date().toISOString(),
    graphicNovelProgress: gnProgress,
    currentNodeIndex: state.currentNodeIndex,
    clearedEncounterNodes: state.clearedEncounterNodes ?? [],
    bypassedEncounterNodes: state.bypassedEncounterNodes ?? [],
    ...((state.intelNodes ?? []).length > 0
      ? { intelNodes: state.intelNodes ?? [] }
      : {}),
  };
}

/** Rebuild a contract from a save slot, or undefined when it cannot be trusted.
 *
 * The slot keeps ids, not objects (the same as `missionId`). Two things must
 * line up before the chain is restored: the ICE catalog has to be there to
 * derive each leg's ICE the way the run start does, and the leg the save says
 * the run is on has to be the mission the save is on. Anything else restores as
 * the single-mission run it was. */
function campaignFromSlot(
  slot: SaveSlot,
  missionCatalog: ReadonlyArray<Mission>,
  iceCatalog: Readonly<Record<string, Ice>> | undefined,
): Campaign | undefined {
  const ids = slot.campaignMissionIds;
  if (!iceCatalog || !ids || ids.length === 0) return undefined;
  const legs = ids
    .map((id) => missionCatalog.find((m) => m.id === id))
    .filter((m): m is Mission => m !== undefined)
    .map((mission) => ({ mission, ice: missionIce(mission, iceCatalog) }));
  const completed = Math.max(0, slot.campaignCompleted ?? 0);
  if (legs.length !== ids.length) return undefined;
  if (legs[completed]?.mission.id !== slot.missionId) return undefined;
  return { legs, completed };
}

/** Reconstruct a GameState from a SaveSlot (CONTINUE option reverse).
 *
 * With `iceCatalog`, the run's base ICE is re-derived from the mission as the
 * run start does (ADR-0252), so encounters rebuild the same roster; without
 * it, `iceFallback` is used as before. */
export function slotToGameState(
  slot: SaveSlot,
  missionCatalog: ReadonlyArray<Mission>,
  programCatalog: Readonly<Record<string, Program>>,
  iceFallback: Ice,
  iceCatalog?: Readonly<Record<string, Ice>>,
): GameState | null {
  const mission = missionCatalog.find((m) => m.id === slot.missionId);
  if (!mission) return null;
  const baseIce = iceCatalog ? missionIce(mission, iceCatalog) : iceFallback;
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

  // ADR-0315 slice 2: rebuild the contract from the ids the slot kept. It is
  // only rebuilt when the catalog is there to derive each leg's ICE from, and
  // only when the legs still agree with the mission the save is on — a
  // mismatched chain would send the run to the wrong job.
  const campaign = campaignFromSlot(slot, missionCatalog, iceCatalog);

  let graphicNovel = null;
  if (slot.graphicNovelProgress) {
    const parts = slot.graphicNovelProgress.chainId.split("_");
    const mode = (parts[0] || "prologue") as
      "prologue" | "novice" | "veteran" | "heretic";
    const characterId = (parts[1] || "novice") as
      "novice" | "veteran" | "heretic";
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

  // Regenerate the run's matrix from the same deterministic inputs
  // `makeInitialState` uses (mission grade + seed), so the resumed run is
  // byte-identical to the one that was saved. Without a matrix the restored
  // state is unplayable: `applyMatrixAction` gates both its confirm and
  // movement branches on `state.matrix != null`, so every input is a no-op.
  const matrix = generateProceduralMatrix(
    missionGradeOf(mission),
    missionSeedOf(mission),
    mission.id,
  );
  // Old saves (written before `currentNodeIndex` was persisted) fall back to
  // the matrix entry node. An out-of-range index would also be unusable, so
  // clamp it to the matrix bounds.
  const savedIndex = slot.currentNodeIndex;
  const currentNodeIndex =
    savedIndex !== undefined &&
    Number.isInteger(savedIndex) &&
    savedIndex >= 0 &&
    savedIndex < matrix.nodes.length
      ? savedIndex
      : matrix.startNode;

  // Restoring onto unresolved ICE is an arrival: the decision opens again.
  const restored = openArrivalEncounter({
    phase: "approach",
    mission,
    player,
    ice: baseIce,
    deck,
    drawPile,
    discardPile,
    grid: makeGrid(MVP_GRID_W, MVP_GRID_H),
    message: `Resumed from autosave (turn ${slot.turnCount + 1})`,
    combatLog: [],
    turnCount: slot.turnCount,
    graphicNovel,
    runPhase: "matrix",
    statusEffects: [],
    iceRoster: [baseIce],
    activeIceIndex: 0,
    currentNodeIndex,
    matrix,
    visitedNodes: [],
    clearedEncounterNodes: slot.clearedEncounterNodes ?? [],
    bypassedEncounterNodes: slot.bypassedEncounterNodes ?? [],
    // ADR-0287: the runner paid for this knowledge, so a reload keeps it. Older
    // slots omit it and see nothing revealed, exactly as before.
    intelNodes: (slot.intelNodes ?? []).filter(
      (i) => Number.isInteger(i) && i >= 0 && i < matrix.nodes.length,
    ),
    cardRewardTaken: slot.cardRewardTaken ?? null,
    ...(slot.uniquePickDone ? { uniquePickDone: true } : {}),
    ...(campaign !== undefined ? { campaign } : {}),
    jockeyId: slot.jockeyId ?? null,
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
    dixiePlayerTurnsSinceAttack: DIXIE_ATTACK_EVERY_N_PLAYER_TURNS - 1,
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
    factionScores: DEFAULT_FACTION_SCORES,
  });
  // ADR-0252: a cleared terminal node can only be saved from the winning
  // loot screen (its confirm ends the run and retires the slot), so resume
  // there; the board would offer no way to finish the run.
  const wonTerminal =
    restored.clearedEncounterNodes?.includes(currentNodeIndex) === true &&
    isTerminalNode(restored);
  return wonTerminal
    ? { ...restored, runPhase: "loot", phase: "victory" }
    : restored;
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
export { durationMsForKind } from "./state_helpers";
