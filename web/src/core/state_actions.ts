/** State action handlers — extracted from state.ts per ADR-0110.
 *
 * Contains all the phase-specific action handlers:
 * - applyMatrixAction: matrix navigation
 * - applyLootAction: post-combat loot
 * - applyDeathAction: death cycle
 * - applyEndingAction: ending screen
 * - applyMenuAction: main menu
 * - applyApproachAction: pre-combat
 * - applyCombatAction: combat phase
 * - applyEndAction: victory/defeat
 *
 * These handlers are called by the main applyAction dispatcher in state.ts.
 */

import type {
  GameState,
  GameAction,
  Ice,
  BossPhase,
  EndingChoice,
} from "./types.ts";
import { applyStatus, applyTickEffects, applyBurnDamage, tickStatus, rollStatusProc } from "./status.ts";
import { calculateDamage, countRoleSynergy, AUTO_ATTACK_INTERVAL_MS } from "./combat_engine.ts";
import { DEFAULT_BOSS_PROFILE, checkPhaseTransition } from "./boss_phases.ts";
import { enemyShouldUseSkill, selectSkillByPersonality } from "./ice_ai.ts";
import { rollLoot, getLootTable, type LootDrop } from "./loot.ts";
import iceTypesData from "../data/ice_types.json";
import type { MutableRunState } from "./run_mutators.ts";
import { isMutatorActive } from "./run_mutators.ts";
import { createDeceasedJockey, generateDeathSummary } from "./death_cycle.ts";
import { resolveEnding, type EndingContext, type ArcId } from "./ending_resolver.ts";
import { onMissionComplete, onIceKill, type FactionId } from "./faction_reputation.ts";
import { import_vfx, import_vfx_ms, pickProgramVfxKind, durationForKind, durationMsForKind } from "./state_helpers.ts";

const DIXIE_ATTACK_INTERVAL_MS = 3000;
const DIXIE_BASE_DAMAGE = 8;
const DIXIE_SYNERGY_BONUS = 3;

/** Tier 5: matrix view actions (navigate, enter combat, jack out). */
export function applyMatrixAction(state: GameState, action: GameAction): GameState {
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
    return {
      ...state,
      phase: "menu",
      message: "Jacked out — run abandoned",
      vfxInstances: [...state.vfxInstances, import_vfx("jackout_whiteout", "", durationForKind("jackout_whiteout"))],
    };
  }
  return state;
}

export function applyLootAction(state: GameState, action: GameAction): GameState {
  if (action.type !== "confirm") return state;
  if (!state.matrix) {
    const missionFaction = getMissionFaction(state.mission.id);
    let updatedScores = state.factionScores;
    if (missionFaction) {
      updatedScores = onMissionComplete(updatedScores, missionFaction);
    }
    const arc: ArcId = (state.mission.arc as ArcId) || 1;
    const ctx: EndingContext = {
      arc,
      hp: state.player.hp,
      maxHp: state.player.maxHp,
      credits: state.inventory.credits,
      missionsCompleted: 0,
      totalDeaths: state.totalDeaths,
      factionScores: updatedScores,
      choices: [],
    };
    const ending = resolveEnding(ctx);
    return { ...state, runPhase: "ending", endingChoice: ending.id as EndingChoice, factionScores: updatedScores };
  }
  const node = state.matrix.nodes[state.currentNodeIndex];
  if (!node || node.adjacent.length === 0) {
    const missionFaction = getMissionFaction(state.mission.id);
    let updatedScores = state.factionScores;
    if (missionFaction) {
      updatedScores = onMissionComplete(updatedScores, missionFaction);
    }
    const arc: ArcId = (state.mission.arc as ArcId) || 1;
    const ctx: EndingContext = {
      arc,
      hp: state.player.hp,
      maxHp: state.player.maxHp,
      credits: state.inventory.credits,
      missionsCompleted: 0,
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

export function applyDeathAction(state: GameState, action: GameAction): GameState {
  if (action.type === "trigger_death") {
    const jockey = createDeceasedJockey({
      name: state.mission.title,
      characterId: "novice",
      grade: state.mission.grade ?? 1,
      missionId: state.mission.id,
      inventory: state.inventory.programs.map(p => p.id),
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
          message: "Select a new jockey" 
        };
      case "same_jockey":
        return { 
          ...state, 
          phase: "menu", 
          runPhase: "matrix",
          player: { ...state.player, hp: state.player.maxHp, alarm: 0 },
          message: "The Finn took you back. Even dead, you owe him." 
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

export function applyEndingAction(state: GameState, action: GameAction): GameState {
  if (action.type === "confirm" || action.type === "jack_out") {
    return { ...state, phase: "menu", message: `Ending ${state.endingChoice}: returning to title` };
  }
  return state;
}

export function applyMenuAction(state: GameState, action: GameAction): GameState {
  if (action.type === "confirm") {
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

export function applyApproachAction(state: GameState, action: GameAction): GameState {
  if (action.type === "confirm" || action.type === "use_program") {
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

export function applyCombatAction(state: GameState, action: GameAction): GameState {
  if (action.type === "cycle_target") {
    return cycleTarget(state);
  }
  if (action.type === "use_program") {
    const result = useProgram(state, action.programId);
    if (result.deck.length === state.deck.length) return result;
    const afterEnemies = processEnemyTurns(result);
    
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
      let autoDmg = Math.max(1, enemy.tier * 3 + enemy.armor);
      
      if (enemy.tier >= 3 && state.bossPhase > 0) {
        autoDmg = Math.floor(autoDmg * bossDamageMultiplier);
      }
      
      playerHp = Math.max(0, playerHp - autoDmg);
      
      if (enemy.tier >= 3 && state.bossPhase >= 3) {
        logMessages.push(`>>> ${enemy.name} AoE: ${autoDmg} dmg (hits all!)`);
      } else {
        logMessages.push(`>>> ${enemy.name} attacks: ${autoDmg} dmg`);
      }
    }
  }

  const anyEnemyAttacked = logMessages.length > 0;

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

  if (playerHp <= 0) {
    const jockey = createDeceasedJockey({
      name: state.mission.title,
      characterId: "novice",
      grade: state.mission.grade ?? 1,
      missionId: state.mission.id,
      inventory: state.inventory.programs.map(p => p.id),
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
      runPhase: "dead",
      phase: "defeat",
      message: "FLATLINE",
      player: { ...state.player, hp: 0 },
      lastDeathSummary: summary,
      totalDeaths: state.totalDeaths + 1,
      deceasedJockeys: [...state.deceasedJockeys, jockey],
      skillCooldowns: newCooldowns,
      iceRoster: rosterForReturn,
      bossPhase: newBossPhase,
      dixieLastAttackMs: dixieAttacked ? currentMs : state.dixieLastAttackMs,
      lastEnemyAttackMs: anyEnemyAttacked ? currentMs : state.lastEnemyAttackMs,
      counterWindowOpenMs: anyEnemyAttacked ? currentMs : state.counterWindowOpenMs,
    };
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
  const allDefeated = finalState.iceRoster.every((ice) => ice.hp === 0);
  const bossPhaseChanged =
    state.bossPhase > 0 &&
    finalState.bossPhase !== state.bossPhase;
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
  let updatedFactionScores = state.factionScores;
  for (const dead of newlyDefeated) {
    const lootTable = getLootTable(dead.id, iceTypesData as Record<string, { loot_table?: { item: string; chance: number; quantity: number }[] }>);
    const drops = rollLoot(lootTable);
    lootDrops.push(...drops);
    const iceFaction = getIceFaction(dead.id);
    if (iceFaction) {
      updatedFactionScores = onIceKill(updatedFactionScores, iceFaction);
    }
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
    let totalReward = state.mission.rewards.credits +
      (state.matrix?.nodes[state.currentNodeIndex]?.reward.credits ?? 0);
    const lootMessage = lootDrops.length > 0
      ? ` Loot: ${lootDrops.map(d => `${d.item}x${d.quantity}`).join(", ")}`
      : "";
    
    const newAchievements: string[] = [];
    let achCredits = 0;

    if (stateWithLoot.unlockedAchievements.length === 0 && newlyDefeated.length > 0) {
      newAchievements.push("first_blood");
      achCredits += 50;
    }

    if (stateWithLoot.bossPhase > 0 && newlyDefeated.length > 0) {
      if (!stateWithLoot.unlockedAchievements.includes("boss_slayer")) {
        newAchievements.push("boss_slayer");
        achCredits += 1000;
      }
    }

    if (stateWithLoot.playerCombo >= 6 && !stateWithLoot.unlockedAchievements.includes("combo_master")) {
      newAchievements.push("combo_master");
      achCredits += 500;
    }

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
      factionScores: updatedFactionScores,
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
    factionScores: updatedFactionScores,
  };
}

export function applyEndAction(state: GameState, action: GameAction): GameState {
  if (action.type === "confirm") {
    return { ...state, phase: "exit" };
  }
  return state;
}

function getIceFaction(iceId: string): FactionId | null {
  if (iceId.includes("hosaka")) return "hosaka";
  if (iceId.includes("maas")) return "maas";
  if (iceId.includes("sense") || iceId.includes("net")) return "sense_net";
  if (iceId.includes("ta") || iceId.includes("construct")) return "ta";
  return null;
}

function getMissionFaction(missionId: string): FactionId | null {
  if (missionId.includes("hosaka")) return "hosaka";
  if (missionId.includes("maas")) return "maas";
  if (missionId.includes("sense") || missionId.includes("net")) return "sense_net";
  if (missionId.includes("ta")) return "ta";
  return null;
}
