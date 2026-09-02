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
  Inventory,
  Mission,
  PlayerStats,
  Program,
  SaveSlot,
  BossPhase,
} from "./types.ts";
import { makeGrid } from "./grid.ts";
import { applyStatus, applyTickEffects, applyBurnDamage, tickStatus, rollStatusProc } from "./status.ts";
import { calculateDamage, countRoleSynergy, AUTO_ATTACK_INTERVAL_MS } from "./combat_engine.ts";
import { EMPTY_LOADOUT } from "./equipment.ts";
import { generateProceduralMatrix } from "./matrix.ts";
import { DEFAULT_BOSS_PROFILE, checkPhaseTransition } from "./boss_phases.ts";
import { enemyShouldUseSkill, selectSkillByPersonality } from "./ice_ai.ts";
import { rollLoot, getLootTable, type LootDrop } from "./loot.ts";
import iceTypesData from "../data/ice_types.json";
import type { RunMutator, MutableRunState } from "./run_mutators.ts";
import { isMutatorActive } from "./run_mutators.ts";

/** Dixie companion auto-attack interval (3 seconds, slower than enemies). */
const DIXIE_ATTACK_INTERVAL_MS = 3000;
/** Dixie base attack damage. */
const DIXIE_BASE_DAMAGE = 8;
/** Dixie synergy bonus per role synergy count. */
const DIXIE_SYNERGY_BONUS = 3;

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
  // Determine grid size based on mission grade for procedural dungeons
  const gridSize = mission.grade ? { w: 80 + (mission.grade - 1) * 20, h: 50 + (mission.grade - 1) * 10 } : { w: MVP_GRID_W, h: MVP_GRID_H };
   
  // Generate procedural dungeon matrix for new runs
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
    const activeIce = state.iceRoster[state.activeIceIndex] ?? state.ice;
    const encounterMultiplier = isMutatorActive(state as unknown as MutableRunState, "ice_x2") ? 2 : 1;
    const baseCount = Math.min(node.iceIds.length * encounterMultiplier, 4);
    const iceRoster = node.iceIds.slice(0, baseCount).map((id, i) => {
      const hp = node.iceHp[i] ?? activeIce.hp;
      return { ...activeIce, id, hp };
    });
    // Tier 6 (ADR-0210): room_flash + data_acquired VFX on matrix entry.
    const matrixEntryVfx: import("../renderer/combat_vfx.js").CombatVfxInstance[] = [
      import_vfx("room_flash", "TIER_GOLD", 1),
    ];
    if (node.eventKind === "cache") {
      matrixEntryVfx.push(import_vfx("data_acquired", "", durationForKind("data_acquired")));
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
  if (action.type === "jack_out") {
    // Tier 6 (ADR-0210): jackout_whiteout on matrix exit.
    return {
      ...state,
      phase: "menu",
      message: "Jacked out — run abandoned",
      vfxInstances: [...state.vfxInstances, import_vfx("jackout_whiteout", "", durationForKind("jackout_whiteout"))],
    };
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

/** Tier 5: ending screen — confirm/jack_out returns to menu. */
function applyEndingAction(state: GameState, action: GameAction): GameState {
  if (action.type === "confirm" || action.type === "jack_out") {
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
    // Tier 6 (ADR-0210): jackin_glitch VFX on run start.
    return {
      ...state,
      phase: "approach",
      message: "Jacking in...",
      vfxInstances: [...state.vfxInstances, import_vfx("jackin_glitch", "", durationForKind("jackin_glitch"))],
    };
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
  if (action.type === "cycle_target") {
    return cycleTarget(state);
  }
  if (action.type === "use_program") {
    const result = useProgram(state, action.programId);
    if (result.deck.length === state.deck.length) return result;
    const afterEnemies = processEnemyTurns(result);
    
    // Check victory after Dixie's attack (in case she defeated remaining enemies)
    const allDefeated = afterEnemies.iceRoster.every((ice) => ice.hp === 0);
    if (allDefeated && afterEnemies.iceRoster.length > 0 && afterEnemies.runPhase === "combat") {
      const totalReward = afterEnemies.mission.rewards.credits +
        (afterEnemies.matrix?.nodes[afterEnemies.currentNodeIndex]?.reward.credits ?? 0);
      return {
        ...afterEnemies,
        runPhase: "loot",
        phase: "victory",
        message: `${afterEnemies.ice.name} defeated! +${totalReward} credits`,
        player: { ...afterEnemies.player, credits: afterEnemies.player.credits + totalReward },
        vfxInstances: [...afterEnemies.vfxInstances, import_vfx("victory", "", 5)],
      };
    }
    
    return afterEnemies;
  }
  if (action.type === "jack_out") {
    return { ...state, phase: "defeat", message: "Jacked out — mission failed" };
  }
  return state;
}

function cycleTarget(state: GameState): GameState {
  const aliveIndices: number[] = [];
  for (let i = 0; i < state.iceRoster.length; i++) {
    if (state.iceRoster[i].hp > 0) aliveIndices.push(i);
  }
  if (aliveIndices.length === 0) return state;
  const currentPos = aliveIndices.indexOf(state.activeIceIndex);
  const nextPos = (currentPos + 1) % aliveIndices.length;
  return { ...state, activeIceIndex: aliveIndices[nextPos] };
}

function advanceDeadTarget(state: GameState): GameState {
  const current = state.iceRoster[state.activeIceIndex];
  if (current && current.hp > 0) return state;
  const aliveIdx = state.iceRoster.findIndex(ice => ice.hp > 0);
  if (aliveIdx === -1) return state;
  return { ...state, activeIceIndex: aliveIdx };
}

function processEnemyTurns(state: GameState): GameState {
  state = advanceDeadTarget(state);
  const currentMs = Date.now();

  if (currentMs - state.lastEnemyAttackMs < AUTO_ATTACK_INTERVAL_MS) {
    return state;
  }

  let playerHp = state.player.hp;
  const logMessages: string[] = [];
  const newCooldowns: Record<string, number> = { ...state.skillCooldowns };

  // Decrease all cooldowns by AUTO_ATTACK_INTERVAL_MS
  for (const key of Object.keys(newCooldowns)) {
    newCooldowns[key] = Math.max(0, (newCooldowns[key] ?? 0) - AUTO_ATTACK_INTERVAL_MS);
  }

  let newBossPhase = state.bossPhase;
  if (state.bossPhase > 0) {
    const bossIce = state.iceRoster.find(ice => ice.hp > 0);
    if (bossIce) {
      const tracker = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: state.bossPhase,
        phaseChangeMs: 0,
        phaseChangeColor: "#ffffff",
      };
      const updated = checkPhaseTransition(tracker, bossIce.hp, bossIce.maxHp ?? 100, currentMs);
      if (updated.currentPhase > state.bossPhase && updated.currentPhase <= 4) {
        newBossPhase = updated.currentPhase as BossPhase;
        logMessages.push(`★ BOSS PHASE ${newBossPhase} — ${DEFAULT_BOSS_PROFILE.phases[newBossPhase - 1]?.label}`);
      }
    }
  }

  const bossDamageMultiplier = state.bossPhase > 0
    ? (state.bossPhase === 2 ? 1.25 : state.bossPhase === 3 ? 1.5 : state.bossPhase >= 4 ? 2.0 : 1.0)
    : 1.0;

  let rosterForReturn = state.iceRoster;
  if (state.bossPhase >= 4 && state.iceRoster.length < 3) {
    const minion: Ice = {
      id: `minion_${Date.now()}`,
      name: "Drone",
      tier: 1,
      hp: 30,
      maxHp: 30,
      armor: 0,
      personality: "aggressive",
      aggression: "standard",
    };
    rosterForReturn = [...state.iceRoster, minion];
    logMessages.push(`★ PHASE 4: Drone deployed!`);
  }

  for (const enemy of state.iceRoster) {
    if (enemy.hp <= 0) continue;

    let enemySkills = enemy.skills ?? [];
    
    if (isMutatorActive(state as unknown as MutableRunState, "stealth_only")) {
      const stealthEffects = ["dot", "poison", "debuff", "silence", "slow"];
      enemySkills = enemySkills.filter(s => stealthEffects.includes(s.effect));
    }
    
    let usedSkill = false;

    // Use ice_ai functions for personality-based selection
    if (enemySkills.length > 0 && enemyShouldUseSkill(enemy as any, Math.random)) {
      const selectedSkill = selectSkillByPersonality(enemy as any, enemySkills as any);
      
      if (selectedSkill) {
        const cooldownKey = `${enemy.id}_${selectedSkill.id}`;
        const remaining = newCooldowns[cooldownKey] ?? 0;
        
        if (remaining <= 0 && selectedSkill.damage > 0) {
          const skillDmg = Math.max(1, selectedSkill.damage + enemy.tier * 2);
          playerHp = Math.max(0, playerHp - skillDmg);
          logMessages.push(`>>> ${enemy.name} uses ${selectedSkill.name}: ${skillDmg} dmg`);
          newCooldowns[cooldownKey] = selectedSkill.cooldownMs;
          usedSkill = true;
        }
      }
    }

    if (!usedSkill) {
      // Auto-attack fallback
      let autoDmg = Math.max(1, enemy.tier * 3 + enemy.armor);
      
      // Apply boss damage multiplier for boss enemies (high tier)
      if (enemy.tier >= 3 && state.bossPhase > 0) {
        autoDmg = Math.floor(autoDmg * bossDamageMultiplier);
      }
      
      playerHp = Math.max(0, playerHp - autoDmg);
      
      // Phase 3-4: boss AoE also damages roster enemies
      if (enemy.tier >= 3 && state.bossPhase >= 3) {
        logMessages.push(`>>> ${enemy.name} AoE: ${autoDmg} dmg (hits all!)`);
      } else {
        logMessages.push(`>>> ${enemy.name} attacks: ${autoDmg} dmg`);
      }
    }
  }

  const anyEnemyAttacked = logMessages.length > 0;

  // Dixie companion auto-attack (separate cooldown from enemies)
  let dixieAttacked = false;
  if (currentMs - state.dixieLastAttackMs >= DIXIE_ATTACK_INTERVAL_MS) {
    const targetIdx = rosterForReturn.findIndex(ice => ice.hp > 0);
    if (targetIdx >= 0) {
      const dixieDmg = DIXIE_BASE_DAMAGE + (state.playerCombo * DIXIE_SYNERGY_BONUS);
      const newRoster = rosterForReturn.map((ice, i) => {
        if (i !== targetIdx) return ice;
        return { ...ice, hp: Math.max(0, ice.hp - dixieDmg) };
      });
      rosterForReturn = newRoster;
      logMessages.push(`>>> Dixie attacks: ${dixieDmg} dmg`);
      dixieAttacked = true;
    }
  }

  return {
    ...state,
    skillCooldowns: newCooldowns,
    iceRoster: rosterForReturn,
    bossPhase: newBossPhase,
    dixieLastAttackMs: dixieAttacked ? currentMs : state.dixieLastAttackMs,
    player: { ...state.player, hp: playerHp },
    lastEnemyAttackMs: anyEnemyAttacked ? currentMs : state.lastEnemyAttackMs,
    counterWindowOpenMs: anyEnemyAttacked ? currentMs : state.counterWindowOpenMs,
    message: logMessages.length > 0 ? logMessages[logMessages.length - 1] : state.message,
  };
}

function useProgram(state: GameState, programId: string): GameState {
  state = advanceDeadTarget(state);
  const program = state.deck.find((p) => p.id === programId);
  if (!program) {
    return { ...state, message: `Program ${programId} not in hand` };
  }
  const alarmMultiplier = isMutatorActive(state as unknown as MutableRunState, "double_alarm") ? 2.0 : 1.0;
  const newAlarm = state.player.alarm + Math.floor(program.cost * alarmMultiplier);
  if (newAlarm > 100) {
    return { ...state, message: "Alarm too high — program failed" };
  }
  const newDeck = state.deck.filter((p) => p.id !== programId);
  const discard = [...state.discardPile, program];

  const vulnerableBonus = state.statusEffects
    .filter((e) => e.kind === "vulnerable" && e.target === "ice")
    .reduce((sum, e) => sum + e.magnitude, 0);

  const statusAttackBonus = state.statusEffects
    .filter((e) => e.kind === "powered" && e.target === "player")
    .reduce((sum, e) => sum + (e.attackBonus ?? 0), 0);

  const equipStats = state.equipmentLoadout.totalStats();
  const attackerAttackBonus = statusAttackBonus + equipStats.attackBonus;

  const newCombo = state.playerCombo + 1;
  const currentMs = Date.now();

  const damageCtx = {
    baseDamage: program.tier * 5,
    attackerTeam: "player" as const,
    attackerAttackBonus,
    attackerCritBonusPct: equipStats.critBonusPct,
    defenderDefenseBonus: 0,
    defenderIceResistance: 0,
    defenderIceKind: null,
    lastSkillRole: (program as { role?: string }).role ?? null,
    lastSkillCritBonus: 0,
    playerCombo: newCombo,
    roleSynergyCount: countRoleSynergy((program as { role?: string }).role ?? null, []),
    defenderVulnerabilityPct: vulnerableBonus + equipStats.damageBonusPct,
    defenderSlowReductionPct: 0,
    rng: Math.random,
  };

  const dmgResult = calculateDamage(damageCtx);
  let damage = dmgResult.damage;

  const slowIdx = state.statusEffects.findIndex((e) => e.kind === "slow" && e.target === "ice");
  const slowReduction = slowIdx >= 0 ? (state.statusEffects[slowIdx]?.magnitude ?? 0) : 0;
  if (slowReduction > 0) {
    const reduction = Math.floor((damage * slowReduction) / 100);
    damage = Math.max(1, damage - reduction);
  }

  const targetIdx = state.activeIceIndex;
  const isAoe = (program as { aoe?: boolean }).aoe === true;
  const damagedRoster = state.iceRoster.map((ice, i) => {
    if (ice.hp <= 0) return ice;
    if (!isAoe && i !== targetIdx) return ice;
    return { ...ice, hp: Math.max(0, ice.hp - damage) };
  });

  let stateWithDamage: GameState = {
    ...state,
    iceRoster: damagedRoster,
    playerCombo: newCombo,
    comboLastHitMs: currentMs,
  };
  if (rollStatusProc("burn") && damagedRoster[targetIdx] && damagedRoster[targetIdx].hp > 0) {
    stateWithDamage = applyStatus(stateWithDamage, "ice", "burn", 2, 3);
  }

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

  stateWithDamage = tickStatus(stateWithDamage);
  const tickResult = applyTickEffects(stateWithDamage);
  const finalState = applyBurnDamage(
    tickResult.state,
    tickResult.burnDamagePlayer + tickResult.bleedDamagePlayer,
    tickResult.burnDamageIce + tickResult.bleedDamageIce,
    tickResult.healPlayer,
    tickResult.healIce,
  );
  // Tier 6 (ADR-0210): dot/regen VFX when status ticks deal damage.
  const dotOrRegenVfx: import("../renderer/combat_vfx.js").CombatVfxInstance[] = [];
  if (tickResult.burnDamagePlayer > 0 || tickResult.burnDamageIce > 0) {
    dotOrRegenVfx.push(import_vfx(
      "dot",
      "",
      durationForKind("dot"),
      undefined,
      undefined,
      tickResult.burnDamagePlayer + tickResult.burnDamageIce,
    ));
  }
  // Check if all ICE in roster defeated (any 0-HP target ends the fight in MVP).
  const allDefeated = finalState.iceRoster.every((ice) => ice.hp === 0);
  // Boss phase transition VFX: if previous bossPhase differs from new,
  // trigger phase-specific VFX (only when fighting a boss node).
  const bossPhaseChanged =
    state.bossPhase > 0 &&
    finalState.bossPhase !== state.bossPhase;
  // Tier 6 (ADR-0210): map program properties to canonical effect kinds.
  const programVfxKind = pickProgramVfxKind(program, damage);
  const programVfxInstances: ReadonlyArray<import("../renderer/combat_vfx.js").CombatVfxInstance> =
    programVfxKind === "attack"
      ? []
      : [import_vfx(programVfxKind, program.name, durationForKind(programVfxKind), undefined, undefined, damage)];
  const vfxNew: ReadonlyArray<import("../renderer/combat_vfx.js").CombatVfxInstance> = [
    ...finalState.vfxInstances,
    import_vfx(programVfxKind, program.name, 3),
    import_vfx("ice_hit", `${damage}`, 2),
    ...programVfxInstances,
    ...dotOrRegenVfx,
    ...(damage >= 10 ? [import_vfx_ms("critical_hit", "", durationMsForKind("critical_hit"), undefined, undefined, damage)] : []),
    ...(bossPhaseChanged && finalState.bossPhase >= 1 && finalState.bossPhase <= 4
      ? [import_vfx_ms("boss_phase_transition", "", durationMsForKind("boss_phase_transition"), undefined, undefined, finalState.bossPhase)]
      : []),
  ];
  
  const newlyDefeated = damagedRoster.filter(
    (ice, i) => ice.hp === 0 && state.iceRoster[i].hp > 0,
  );
  let lootDrops: LootDrop[] = [];
  for (const dead of newlyDefeated) {
    const lootTable = getLootTable(dead.id, iceTypesData as Record<string, { loot_table?: { item: string; chance: number; quantity: number }[] }>);
    const drops = rollLoot(lootTable);
    lootDrops.push(...drops);
  }
  
  let stateWithLoot = finalState;
  if (lootDrops.length > 0) {
    const newMaterials = { ...finalState.inventory.materials };
    for (const drop of lootDrops) {
      newMaterials[drop.item] = (newMaterials[drop.item] ?? 0) + drop.quantity;
    }
    stateWithLoot = {
      ...finalState,
      inventory: { ...finalState.inventory, materials: newMaterials },
    };
  }
  
  if (allDefeated && stateWithLoot.iceRoster.length > 0) {
    // Victory → loot screen
    let totalReward = state.mission.rewards.credits +
      (state.matrix?.nodes[state.currentNodeIndex]?.reward.credits ?? 0);
    const lootMessage = lootDrops.length > 0
      ? ` Loot: ${lootDrops.map(d => `${d.item}x${d.quantity}`).join(", ")}`
      : "";
    
    // Check achievements for newly defeated enemies
    const newAchievements: string[] = [];
    let achCredits = 0;

    // First Blood achievement (first enemy kill ever)
    if (stateWithLoot.unlockedAchievements.length === 0 && newlyDefeated.length > 0) {
      newAchievements.push("first_blood");
      achCredits += 50;
    }

    // Boss Slayer (first boss kill)
    if (stateWithLoot.bossPhase > 0 && newlyDefeated.length > 0) {
      if (!stateWithLoot.unlockedAchievements.includes("boss_slayer")) {
        newAchievements.push("boss_slayer");
        achCredits += 1000;
      }
    }

    // Combo Master (combo >= 6, per achievements.ts line 677)
    if (stateWithLoot.playerCombo >= 6 && !stateWithLoot.unlockedAchievements.includes("combo_master")) {
      newAchievements.push("combo_master");
      achCredits += 500;
    }

    // Update state with new achievements
    const allUnlocked = [...stateWithLoot.unlockedAchievements, ...newAchievements];
    totalReward += achCredits;

    return {
      ...stateWithLoot,
      iceRoster: stateWithLoot.iceRoster,
      deck: newDeck,
      discardPile: discard,
      runPhase: "loot",
      phase: "victory",
      message: `${stateWithLoot.ice.name} defeated! +${totalReward} credits${lootMessage}`,
      player: { ...stateWithLoot.player, credits: stateWithLoot.player.credits + totalReward },
      vfxInstances: [...vfxNew, import_vfx("victory", "", 5)],
      unlockedAchievements: allUnlocked,
      achievementCredits: stateWithLoot.achievementCredits + achCredits,
    };
  }
  const activeIceNewHp = finalState.iceRoster[targetIdx]?.hp ?? 0;
  return {
    ...finalState,
    iceRoster: finalState.iceRoster,
    deck: newDeck,
    discardPile: discard,
    player: { ...finalState.player, alarm: newAlarm },
    message: isAoe
      ? `${program.name} → ${damage} dmg ALL (roster hit)`
      : `${program.name} → ${damage} dmg (ICE HP: ${activeIceNewHp})`,
    vfxInstances: vfxNew,
    unlockedAchievements: finalState.unlockedAchievements,
    achievementCredits: finalState.achievementCredits,
  };
}

/** Tiny helper to avoid circular import: returns a VFX instance directly.
 * Derives durationMs from the tick duration so the ms-precision expiry
 * path works automatically. */
function import_vfx(
  kind: import("../renderer/combat_vfx.js").CombatVfxKind,
  payload: string,
  duration: number,
  startRow?: number,
  targetRow?: number,
  payloadNum?: number,
): import("../renderer/combat_vfx.js").CombatVfxInstance {
  const WEB_TICK_MS = 16;
  const durationMs = Math.max(0, duration) * WEB_TICK_MS;
  return {
    id: Math.floor(Math.random() * 1e9) + 1,
    kind,
    tick: 0,
    duration,
    durationMs,
    elapsedMs: 0,
    payload,
    payloadNum,
    startRow,
    targetRow,
  };
}

/** MS-precision variant: pass the canonical duration_ms from the schema
 * instead of the tick count. Use for new code where ADR-0210 schema
 * durations are available. */
function import_vfx_ms(
  kind: import("../renderer/combat_vfx.js").CombatVfxKind,
  payload: string,
  durationMs: number,
  startRow?: number,
  targetRow?: number,
  payloadNum?: number,
): import("../renderer/combat_vfx.js").CombatVfxInstance {
  const WEB_TICK_MS = 16;
  const clampedMs = Math.max(0, durationMs);
  return {
    id: Math.floor(Math.random() * 1e9) + 1,
    kind,
    tick: 0,
    duration: Math.ceil(clampedMs / WEB_TICK_MS),
    durationMs: clampedMs,
    elapsedMs: 0,
    payload,
    payloadNum,
    startRow,
    targetRow,
  };
}

/** Map a program to its primary canonical VFX kind (Tier 6, ADR-0210).
 *
 * Heuristic: program tier + role determine effect kind.
 * Falls back to `attack` for unknown roles so every program gets a VFX.
 */
function pickProgramVfxKind(
  program: { tier: number; role?: string; effect?: string },
  damage: number,
): import("../renderer/combat_vfx.js").CombatVfxKind {
  if (program.effect === "noise_attraction") return "detect";
  if (program.effect === "reset_ap") return "buff";
  if (program.role === "strike") return "pierce";
  if (program.role === "burst" && damage >= 20) return "heavy_attack";
  if (program.role === "burst" && damage >= 10) return "multi_hit";
  if (program.role === "guard") return "shield";
  if (program.role === "support") return "regen";
  return "attack";
}

/** Canonical duration in ticks for a given VFX kind (≈ ceil(ms / 16)).
 *
 * Mirrors prototype/data/effects.json duration_ms values.
 */
function durationForKind(kind: import("../renderer/combat_vfx.js").CombatVfxKind): number {
  switch (kind) {
    case "attack": return 3;
    case "heavy_attack": return 9;
    case "pierce": return 4;
    case "multi_hit": return 4;
    case "dot": return 7;
    case "shield": return 4;
    case "heal": return 4;
    case "regen": return 6;
    case "buff": return 3;
    case "debuff": return 3;
    case "stun": return 4;
    case "counter": return 6;
    case "lifesteal": return 7;
    case "detect": return 7;
    case "ice_hit": return 2;
    case "player_hit": return 3;
    case "critical_hit": return 4;
    case "status_apply": return 3;
    case "ice_intro": return 8;
    case "ice_death": return 8;
    case "boss_phase_transition": return 5;
    case "victory": return 5;
    case "defeat": return 5;
    case "jackin_glitch": return 7;
    case "jackout_whiteout": return 5;
    case "room_flash": return 1;
    case "data_acquired": return 7;
  }
}

/** Canonical duration in milliseconds for a given VFX kind.
 *
 * Mirrors prototype/data/effects.json duration_ms exactly. Use this with
 * import_vfx_ms() for ms-precise expiry (Tier 7+).
 */
export function durationMsForKind(kind: import("../renderer/combat_vfx.js").CombatVfxKind): number {
  switch (kind) {
    case "attack": return 240;
    case "heavy_attack": return 900;
    case "pierce": return 310;
    case "multi_hit": return 290;
    case "dot": return 550;
    case "shield": return 280;
    case "heal": return 320;
    case "regen": return 450;
    case "buff": return 240;
    case "debuff": return 240;
    case "stun": return 320;
    case "counter": return 420;
    case "lifesteal": return 490;
    case "detect": return 550;
    case "ice_hit": return 160;
    case "player_hit": return 200;
    case "critical_hit": return 320;
    case "status_apply": return 240;
    case "ice_intro": return 640;
    case "ice_death": return 640;
    case "boss_phase_transition": return 800;
    case "victory": return 800;
    case "defeat": return 800;
    case "jackin_glitch": return 500;
    case "jackout_whiteout": return 400;
    case "room_flash": return 80;
    case "data_acquired": return 500;
  }
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
   // Equipped items
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
  };
}
