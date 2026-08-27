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
import { applyStatus, applyTickEffects, applyBurnDamage, tickStatus, rollStatusProc } from "./status.ts";

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
    runPhase: "matrix",
    statusEffects: [],
    iceRoster: [ice],
    activeIceIndex: 0,
    currentNodeIndex: 0,
    matrix: null,
    visitedNodes: [],
    bossPhase: 0,
    endingChoice: null,
    vfxInstances: [],
  };
}

/** Pure reducer — apply an action to a state, returning a new state. */
export function applyAction(state: GameState, action: GameAction): GameState {
  // Tier 5: matrix → combat → loot → ending cycle.
  // The legacy `phase` field is still used within combat for
  // approach/combat/victory/defeat sub-states.
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
    return state;
  }
  // combat: dispatch by legacy phase
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

/** Tier 5: matrix view actions (navigate, enter combat, jack out). */
function applyMatrixAction(state: GameState, action: GameAction): GameState {
  if (action.type === "confirm" && state.matrix != null) {
    const node = state.matrix.nodes[state.currentNodeIndex];
    if (!node || node.iceIds.length === 0) return state;
    // Populate iceRoster from matrix node + iceTypes catalog.
    // main.ts's resolveMatrixRoster isn't accessible here (no ice catalog),
    // so we resolve against the current activeIce (fallback). For MVP the
    // matrix generator pre-resolves ids to a single default; tier 5+ will
    // inject a richer resolver.
    const activeIce = state.iceRoster[state.activeIceIndex] ?? state.ice;
    const iceRoster = node.iceIds.map((id, i) => {
      const hp = node.iceHp[i] ?? activeIce.hp;
      return { ...activeIce, id, hp };
    });
    return {
      ...state,
      runPhase: "combat",
      phase: "approach",
      message: `Entering ${node.zone}... (${iceRoster.length} ICE)`,
      iceRoster,
      activeIceIndex: 0,
      bossPhase: node.isBoss ? 1 : 0,
      turnCount: state.turnCount + 1,
    };
  }
  if (action.type === "cancel" || action.type === "jack_out") {
    return { ...state, phase: "menu", message: "Jacked out — run abandoned" };
  }
  return state;
}

/** Tier 5: loot screen between combats (Tier 4 simplification: HEAL + advance). */
function applyLootAction(state: GameState, action: GameAction): GameState {
  if (action.type !== "confirm") return state;
  if (!state.matrix) {
    return { ...state, runPhase: "ending", endingChoice: "A" };
  }
  const node = state.matrix.nodes[state.currentNodeIndex];
  if (!node || node.adjacent.length === 0) {
    // Boss defeated — run complete.
    return {
      ...state,
      runPhase: "ending",
      endingChoice: state.player.hp > 50 ? "A" : state.player.hp > 25 ? "B" : "C",
    };
  }
  const nextIdx = node.adjacent[0] ?? state.currentNodeIndex;
  const newVisited = state.visitedNodes.includes(nextIdx)
    ? state.visitedNodes
    : [...state.visitedNodes, nextIdx];
  return {
    ...state,
    runPhase: "matrix",
    currentNodeIndex: nextIdx,
    visitedNodes: newVisited,
    phase: "approach",
    message: `Advancing to next node (${nextIdx})`,
  };
}

/** Tier 5: ending screen — confirm returns to menu. */
function applyEndingAction(state: GameState, action: GameAction): GameState {
  if (action.type === "confirm" || action.type === "cancel") {
    return { ...state, phase: "menu", message: `Ending ${state.endingChoice}: returning to title` };
  }
  return state;
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
  // Tier 5.5 status effect: check if ICE is vulnerable (next attack +X% dmg)
  const vulnerableBonus = state.statusEffects
    .filter((e) => e.kind === "vulnerable" && e.target === "ice")
    .reduce((sum, e) => sum + e.magnitude, 0);
  // Tier 5.5: slow on ICE reduces damage taken by latest slow magnitude%.
  // Find the most-recent slow effect (highest index).
  const slowIdx = state.statusEffects.findIndex((e) => e.kind === "slow" && e.target === "ice");
  const slowReduction = slowIdx >= 0 ? (state.statusEffects[slowIdx]?.magnitude ?? 0) : 0;
  const baseDamage = program.tier * 5;
  const damageWithVuln = baseDamage + Math.floor((baseDamage * vulnerableBonus) / 100);
  const damage = Math.max(1, damageWithVuln - Math.floor((damageWithVuln * slowReduction) / 100));
  // Tier 5: damage applies to active ICE in roster, not single state.ice.
  const targetIdx = state.activeIceIndex;
  const damagedRoster = state.iceRoster.map((ice, i) => {
    if (i !== targetIdx) return ice;
    return { ...ice, hp: Math.max(0, ice.hp - damage) };
  });
  // Apply burn to ICE on player attack (proc ~20%) — add to damagedRoster state.
  let stateWithDamage: GameState = { ...state, iceRoster: damagedRoster };
  if (rollStatusProc("burn") && damagedRoster[targetIdx] && damagedRoster[targetIdx].hp > 0) {
    stateWithDamage = applyStatus(stateWithDamage, "ice", "burn", 2, 3);
  }
  // Clear one stack of vulnerable after being hit
  if (vulnerableBonus > 0) {
    const vulnerableIdx = stateWithDamage.statusEffects.findIndex(
      (e) => e.kind === "vulnerable" && e.target === "ice",
    );
    if (vulnerableIdx >= 0) {
      const updated = [...stateWithDamage.statusEffects];
      updated.splice(vulnerableIdx, 1);
      stateWithDamage = { ...stateWithDamage, statusEffects: updated };
    }
  }
  // Clear consumed slow stack after damage applied (one-shot per attack).
  if (slowReduction > 0) {
    const slowAbsIdx = stateWithDamage.statusEffects.findIndex(
      (e) => e.kind === "slow" && e.target === "ice",
    );
    if (slowAbsIdx >= 0) {
      const updated = [...stateWithDamage.statusEffects];
      updated.splice(slowAbsIdx, 1);
      stateWithDamage = { ...stateWithDamage, statusEffects: updated };
    }
  }
  // Tick status effects at turn start
  stateWithDamage = tickStatus(stateWithDamage);
  // Apply burn damage from tick
  const tickResult = applyTickEffects(stateWithDamage);
  const finalState = applyBurnDamage(
    tickResult.state,
    tickResult.burnDamagePlayer,
    tickResult.burnDamageIce,
  );
  // Check if all ICE in roster defeated (any 0-HP target ends the fight in MVP).
  const allDefeated = finalState.iceRoster.every((ice) => ice.hp === 0);
  // Boss phase transition VFX: if previous bossPhase differs from new,
  // trigger phase-specific VFX (only when fighting a boss node).
  const bossPhaseChanged =
    state.bossPhase > 0 &&
    finalState.bossPhase !== state.bossPhase;
  const vfxNew: ReadonlyArray<import("../renderer/combat_vfx.js").CombatVfxInstance> = [
    ...finalState.vfxInstances,
    import_vfx("card_use", program.name, 3),
    import_vfx("card_hit", `${damage}`, 3),
    import_vfx("ice_hit", `${damage}`, 2),
    ...(bossPhaseChanged && finalState.bossPhase >= 1 && finalState.bossPhase <= 4
      ? [import_vfx(`boss_phase_${finalState.bossPhase}` as "boss_phase_1" | "boss_phase_2" | "boss_phase_3" | "boss_phase_4", "", 5)]
      : []),
  ];
  if (allDefeated && finalState.iceRoster.length > 0) {
    // Victory → loot screen
    const totalReward = state.mission.rewards.credits +
      (state.matrix?.nodes[state.currentNodeIndex]?.reward.credits ?? 0);
    return {
      ...finalState,
      iceRoster: finalState.iceRoster,
      deck: newDeck,
      discardPile: discard,
      runPhase: "loot",
      phase: "victory",
      message: `${finalState.ice.name} defeated! +${totalReward} credits`,
      player: { ...finalState.player, credits: finalState.player.credits + totalReward },
      vfxInstances: [...vfxNew, import_vfx("victory", "", 5)],
    };
  }
  const activeIceNewHp = finalState.iceRoster[targetIdx]?.hp ?? 0;
  return {
    ...finalState,
    iceRoster: finalState.iceRoster,
    deck: newDeck,
    discardPile: discard,
    player: { ...finalState.player, alarm: newAlarm },
    message: `${program.name} → ${damage} dmg (ICE HP: ${activeIceNewHp})`,
    vfxInstances: vfxNew,
  };
}

/** Tiny helper to avoid circular import: returns a VFX instance directly. */
function import_vfx(
  kind: import("../renderer/combat_vfx.js").CombatVfxKind,
  payload: string,
  duration: number,
): import("../renderer/combat_vfx.js").CombatVfxInstance {
  return {
    id: Math.floor(Math.random() * 1e9) + 1,
    kind,
    tick: 0,
    duration,
    payload,
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
  const lines: string[] = [
    `HP ${state.player.hp}/${state.player.maxHp}`,
    `Alarm ${state.player.alarm}/100`,
    `Credits ${state.player.credits}`,
  ];
  // Boss phase badge (only when fighting a boss and phase > 0).
  if (state.bossPhase > 0 && state.bossPhase <= 4) {
    lines.push(`★ BOSS PHASE ${state.bossPhase}/4`);
  }
  lines.push("", `Phase: ${state.phase}`, `ICE HP: ${state.ice.hp}`, "", state.message);
  return lines;
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
  };
}
