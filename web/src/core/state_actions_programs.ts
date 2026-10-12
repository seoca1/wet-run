/** Program resolution + shared combat-target helpers — split from
 * state_actions.ts per ADR-0110.
 *
 * - useProgram: resolve a played program (damage, status, loot, achievements)
 * - getIceFaction: map an ICE id to its faction
 * - advanceDeadTarget: retarget the active ICE when the current one is dead
 *   (shared by `useProgram` and `processEnemyTurns` in state_actions_combat.ts)
 *
 * Re-exported from `state_actions.ts` so existing imports keep working.
 */

import type { GameState } from "./types.ts";
import {
  applyStatus,
  applyTickEffects,
  applyBurnDamage,
  tickStatus,
  rollStatusProc,
} from "./status.ts";
import { AudioManager, SFX_IDS } from "../audio/manager.ts";
import { calculateDamage, countRoleSynergy } from "./combat_engine.ts";
import { rollLoot, getLootTable, type LootDrop } from "./loot.ts";
import iceTypesData from "../data/ice_types.json";
import { isMutatorActive, type MutableRunState } from "./run_mutators.ts";
import { onIceKill, type FactionId } from "./faction_reputation.ts";
import {
  import_vfx,
  import_vfx_ms,
  pickProgramVfxKind,
  durationForKind,
  durationMsForKind,
} from "./state_helpers.ts";

/** Retarget the active ICE when the current target is dead. */
export function advanceDeadTarget(state: GameState): GameState {
  const current = state.iceRoster[state.activeIceIndex];
  if (current && current.hp > 0) return state;
  const aliveIdx = state.iceRoster.findIndex((ice) => ice.hp > 0);
  if (aliveIdx === -1) return state;
  return { ...state, activeIceIndex: aliveIdx };
}

export function useProgram(state: GameState, programId: string): GameState {
  state = advanceDeadTarget(state);
  const program = state.deck.find((p) => p.id === programId);
  if (!program) {
    return { ...state, message: `Program ${programId} not in hand` };
  }
  const alarmMultiplier = isMutatorActive(
    state as unknown as MutableRunState,
    "double_alarm",
  )
    ? 2.0
    : 1.0;
  const newAlarm =
    state.player.alarm + Math.floor(program.cost * alarmMultiplier);
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

  // Play combat hit SFX automatically
  void AudioManager.getInstance().playSfx(SFX_IDS.COMBAT_HIT);

  const defenderIce = state.iceRoster[state.activeIceIndex] ?? state.ice;
  const damageCtx = {
    baseDamage: program.tier * 5,
    attackerTeam: "player" as const,
    attackerAttackBonus,
    attackerCritBonusPct: equipStats.critBonusPct,
    defenderDefenseBonus: defenderIce.armor ?? 0,
    defenderIceResistance: 0,
    defenderIceKind: null,
    lastSkillRole: (program as { role?: string }).role ?? null,
    lastSkillCritBonus: 0,
    playerCombo: newCombo,
    roleSynergyCount: countRoleSynergy(
      (program as { role?: string }).role ?? null,
      [],
    ),
    defenderVulnerabilityPct: vulnerableBonus + equipStats.damageBonusPct,
    defenderSlowReductionPct: 0,
    rng: Math.random,
  };

  const dmgResult = calculateDamage(damageCtx);
  let damage = dmgResult.damage;

  const slowIdx = state.statusEffects.findIndex(
    (e) => e.kind === "slow" && e.target === "ice",
  );
  const slowReduction =
    slowIdx >= 0 ? (state.statusEffects[slowIdx]?.magnitude ?? 0) : 0;
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
  if (
    rollStatusProc("burn") &&
    damagedRoster[targetIdx] &&
    damagedRoster[targetIdx].hp > 0
  ) {
    stateWithDamage = applyStatus(stateWithDamage, "ice", "burn", 2, 3);
  }

  // Apply slow effect 20% chance to slow ice for 2 turns with 30% damage reduction
  if (
    rollStatusProc("slow") &&
    damagedRoster[targetIdx] &&
    damagedRoster[targetIdx].hp > 0
  ) {
    stateWithDamage = applyStatus(stateWithDamage, "ice", "slow", 2, 30, {
      slowPct: 30,
    });
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
  const dotOrRegenVfx: import("../renderer/combat_vfx.js").CombatVfxInstance[] =
    [];
  if (tickResult.burnDamagePlayer > 0 || tickResult.burnDamageIce > 0) {
    dotOrRegenVfx.push(
      import_vfx(
        "dot",
        "",
        durationForKind("dot"),
        undefined,
        undefined,
        tickResult.burnDamagePlayer + tickResult.burnDamageIce,
      ),
    );
  }
  const allDefeated = finalState.iceRoster.every((ice) => ice.hp === 0);
  const bossPhaseChanged =
    state.bossPhase > 0 && finalState.bossPhase !== state.bossPhase;
  const programVfxKind = pickProgramVfxKind(program, damage);
  const programVfxInstances: ReadonlyArray<
    import("../renderer/combat_vfx.js").CombatVfxInstance
  > =
    programVfxKind === "attack"
      ? []
      : [
          import_vfx(
            programVfxKind,
            program.name,
            durationForKind(programVfxKind),
            undefined,
            undefined,
            damage,
          ),
        ];
  const vfxNew: ReadonlyArray<
    import("../renderer/combat_vfx.js").CombatVfxInstance
  > = [
    ...finalState.vfxInstances,
    import_vfx(programVfxKind, program.name, 3),
    import_vfx("ice_hit", `${damage}`, 2),
    ...programVfxInstances,
    ...dotOrRegenVfx,
    ...(damage >= 10
      ? [
          import_vfx_ms(
            "critical_hit",
            "",
            durationMsForKind("critical_hit"),
            undefined,
            undefined,
            damage,
          ),
        ]
      : []),
    ...(bossPhaseChanged &&
    finalState.bossPhase >= 1 &&
    finalState.bossPhase <= 4
      ? [
          import_vfx_ms(
            "boss_phase_transition",
            "",
            durationMsForKind("boss_phase_transition"),
            undefined,
            undefined,
            finalState.bossPhase,
          ),
        ]
      : []),
  ];

  const newlyDefeated = finalState.iceRoster.filter(
    (ice, i) => ice.hp === 0 && state.iceRoster[i]?.hp !== 0,
  );
  const lootDrops: LootDrop[] = [];
  let updatedFactionScores = state.factionScores;
  for (const dead of newlyDefeated) {
    const lootTable = getLootTable(
      dead.id,
      iceTypesData as Record<
        string,
        { loot_table?: { item: string; chance: number; quantity: number }[] }
      >,
    );
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
    let totalReward =
      state.mission.rewards.credits +
      (state.matrix?.nodes[state.currentNodeIndex]?.reward.credits ?? 0);
    const lootMessage =
      lootDrops.length > 0
        ? ` Loot: ${lootDrops.map((d) => `${d.item}x${d.quantity}`).join(", ")}`
        : "";

    const newAchievements: string[] = [];
    let achCredits = 0;

    if (
      stateWithLoot.unlockedAchievements.length === 0 &&
      newlyDefeated.length > 0
    ) {
      newAchievements.push("first_blood");
      achCredits += 50;
    }

    if (stateWithLoot.bossPhase > 0 && newlyDefeated.length > 0) {
      if (!stateWithLoot.unlockedAchievements.includes("boss_slayer")) {
        newAchievements.push("boss_slayer");
        achCredits += 1000;
      }
    }

    if (
      stateWithLoot.playerCombo >= 6 &&
      !stateWithLoot.unlockedAchievements.includes("combo_master")
    ) {
      newAchievements.push("combo_master");
      achCredits += 500;
    }

    const allUnlocked = [
      ...stateWithLoot.unlockedAchievements,
      ...newAchievements,
    ];
    totalReward += achCredits;

    return {
      ...stateWithLoot,
      iceRoster: stateWithLoot.iceRoster,
      deck: newDeck,
      discardPile: discard,
      runPhase: "loot",
      phase: "victory",
      message: `${stateWithLoot.ice.name} defeated! +${totalReward} credits${lootMessage}`,
      player: {
        ...stateWithLoot.player,
        credits: stateWithLoot.player.credits + totalReward,
      },
      vfxInstances: [...vfxNew, import_vfx("victory", "", 5)],
      unlockedAchievements: allUnlocked,
      achievementCredits: stateWithLoot.achievementCredits + achCredits,
      factionScores: updatedFactionScores,
    };
  }
  const activeIceNewHp = finalState.iceRoster[targetIdx]?.hp ?? 0;
  return {
    ...stateWithLoot,
    iceRoster: stateWithLoot.iceRoster,
    deck: newDeck,
    discardPile: discard,
    player: { ...stateWithLoot.player, alarm: newAlarm },
    message: isAoe
      ? `${program.name} → ${damage} dmg ALL (roster hit)`
      : `${program.name} → ${damage} dmg (ICE HP: ${activeIceNewHp})`,
    vfxInstances: vfxNew,
    unlockedAchievements: stateWithLoot.unlockedAchievements,
    achievementCredits: stateWithLoot.achievementCredits,
    factionScores: updatedFactionScores,
  };
}

function getIceFaction(iceId: string): FactionId | null {
  if (iceId.includes("hosaka")) return "hosaka";
  if (iceId.includes("maas")) return "maas";
  if (iceId.includes("sense") || iceId.includes("net")) return "sense_net";
  if (iceId.includes("ta") || iceId.includes("construct")) return "ta";
  return null;
}
