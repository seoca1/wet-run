/** Game state factory + reducer.
 *
 * Ports the wet_run GameState to a pure-data TypeScript model. Tier 2
 * supports multiple missions (see main.ts mission catalog).
 *
 * State machine (per wet_run combat_view_input.py):
 *   menu → approach → combat → victory | defeat → exit
 */

import type {
  GameState,
  GameAction,
  Ice,
  Mission,
  PlayerStats,
  Program,
  SaveSlot,
} from "./types.ts";
import { makeGrid } from "./grid.ts";

const MVP_GRID_W = 80;
const MVP_GRID_H = 50;
const MVP_BASE_HP = 100;
const MVP_BASE_ALARM = 0;
const MVP_BASE_CREDITS = 0;
const MVP_BASE_HAND = 5;

/** Construct a fresh GameState for the MVP mission. */
export function makeInitialState(mission: Mission, ice: Ice, deck: ReadonlyArray<Program>): GameState {
  const player: PlayerStats = {
    hp: MVP_BASE_HP,
    maxHp: MVP_BASE_HP,
    alarm: MVP_BASE_ALARM,
    credits: MVP_BASE_CREDITS,
    handSize: MVP_BASE_HAND,
  };
  return {
    phase: "menu",
    mission,
    player,
    ice: { ...ice, hp: ice.hp, armor: ice.armor, tier: ice.tier, id: ice.id, name: ice.name },
    deck: deck.slice(0, MVP_BASE_HAND),
    drawPile: deck.slice(MVP_BASE_HAND),
    discardPile: [],
    grid: makeGrid(MVP_GRID_W, MVP_GRID_H),
    message: `Mission: ${mission.title}`,
    turnCount: 0,
  };
}

/** Pure reducer — apply an action to a state, returning a new state. */
export function applyAction(state: GameState, action: GameAction): GameState {
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
      return state; // terminal — ignore further actions
  }
}

/** Resolve a select_program (hand index, 1-based) to the matching use_program.
 * Returns null if the index is out of range or no state.hand is provided.
 * Used by main.ts to bridge input handlers with the reducer.
 */
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

function applyMenuAction(state: GameState, action: GameAction): GameState {
  if (action.type === "confirm") {
    return { ...state, phase: "approach", message: "Jacking in..." };
  }
  if (action.type === "jack_out") {
    return { ...state, phase: "exit" };
  }
  return state;
}

function applyApproachAction(state: GameState, action: GameAction): GameState {
  if (action.type === "confirm" || action.type === "use_program") {
    // ENTER or any program use transitions into combat (MVP simplification).
    return {
      ...state,
      phase: "combat",
      message: `Combat vs ${state.ice.name}`,
      turnCount: state.turnCount + 1,
    };
  }
  if (action.type === "jack_out") {
    return { ...state, phase: "exit" };
  }
  return state;
}

function applyCombatAction(state: GameState, action: GameAction): GameState {
  if (action.type === "use_program") {
    return useProgram(state, action.programId);
  }
  if (action.type === "jack_out") {
    return { ...state, phase: "defeat", message: "Jacked out — mission failed" };
  }
  return state;
}

function useProgram(state: GameState, programId: string): GameState {
  const program = state.deck.find((p) => p.id === programId);
  if (!program) {
    return { ...state, message: `Program ${programId} not in hand` };
  }
  const newAlarm = state.player.alarm + program.cost;
  if (newAlarm > 100) {
    return { ...state, message: "Alarm too high — program failed" };
  }
  const newDeck = state.deck.filter((p) => p.id !== programId);
  const discard = [...state.discardPile, program];
  const damage = program.tier * 5;
  const newIceHp = Math.max(0, state.ice.hp - damage);
  if (newIceHp === 0) {
    return {
      ...state,
      ice: { ...state.ice, hp: 0 },
      deck: newDeck,
      discardPile: discard,
      phase: "victory",
      message: `${state.ice.name} defeated! +${state.mission.rewards.credits} credits`,
    };
  }
  return {
    ...state,
    ice: { ...state.ice, hp: newIceHp },
    deck: newDeck,
    discardPile: discard,
    player: { ...state.player, alarm: newAlarm },
    message: `${program.name} → ${damage} dmg (ICE HP: ${newIceHp})`,
  };
}

function applyEndAction(state: GameState, action: GameAction): GameState {
  if (action.type === "confirm") {
    return { ...state, phase: "exit" };
  }
  return state;
}

/** Generate HUD lines from current state — feeds the right-side panel. */
export function buildHudLines(state: GameState): string[] {
  return [
    `HP ${state.player.hp}/${state.player.maxHp}`,
    `Alarm ${state.player.alarm}/100`,
    `Credits ${state.player.credits}`,
    "",
    `Phase: ${state.phase}`,
    `ICE HP: ${state.ice.hp}`,
    "",
    state.message,
  ];
}

/** Serialize a GameState to a SaveSlot (Tier 2 save round-trip). */
export function stateToSaveSlot(state: GameState): SaveSlot {
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
  };
}

/** Reconstruct a GameState from a SaveSlot (CONTINUE option reverse).
 *
 * Looks up the mission in the catalog, picks the first matching ICE,
 * and rebuilds the deck from saved ids (skipping any that no longer exist
 * in programsData — defensive against data drift).
 *
 * Returns null if the saved missionId is no longer in MISSIONS or no
 * programs survive filtering (loadable state invariant).
 */
export function slotToGameState(
  slot: SaveSlot,
  missionCatalog: ReadonlyArray<Mission>,
  programCatalog: Readonly<Record<string, Program>>,
  iceFallback: Ice,
): GameState | null {
  const mission = missionCatalog.find((m) => m.id === slot.missionId);
  if (!mission) return null;
  // Reconstruct deck from saved program ids; skip any missing in catalog.
  const findProgram = (id: string): Program | undefined => programCatalog[id];
  const restoreHand = (ids: ReadonlyArray<string>): ReadonlyArray<Program> =>
    ids.map(findProgram).filter((p): p is Program => p !== undefined);
  const deck = restoreHand(slot.deckIds);
  const discardPile = restoreHand(slot.discardIds);
  const drawPile = restoreHand(slot.drawIds);
  // If all programs in hand disappeared (data drift), refuse to load.
  if (deck.length === 0 && slot.deckIds.length > 0) return null;
  const player: PlayerStats = {
    hp: slot.playerHp,
    maxHp: slot.playerMaxHp,
    alarm: slot.playerAlarm,
    credits: slot.playerCredits,
    handSize: MVP_BASE_HAND,
  };
  return {
    phase: "approach", // resume from approach (post-combat-first-step)
    mission,
    player,
    ice: iceFallback, // ICE state not in save; use mission's primary ICE
    deck,
    drawPile,
    discardPile,
    grid: makeGrid(MVP_GRID_W, MVP_GRID_H),
    message: `Resumed from autosave (turn ${slot.turnCount + 1})`,
    turnCount: slot.turnCount,
  };
}
