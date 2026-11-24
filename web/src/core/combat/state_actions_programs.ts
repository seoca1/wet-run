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

import type { GameState, Program } from "../types";
import {
  applyStatus,
  applyTickEffects,
  applyBurnDamage,
  tickStatus,
  rollStatusProc,
  endedStatuses,
  statusEventLines,
} from "../status";
import { AudioManager } from "../../audio/manager";
import { calculateDamage, countRoleSynergy, programPowerArmorBypassPct } from "./combat_engine";
import { absorbIceDamage } from "./ice_combat_effects";
import { programEffect, type ProgramEffect } from "./program_effects";
import { COST_LIMIT, programAlarmCost, programHitsAllIce } from "./program_affordance";
import { creditKills, killedBetween, resolveVictory } from "./victory";
import {
  COMBAT_LOG_CAP,
  import_vfx,
  import_vfx_ms,
  pickProgramVfxKind,
  pickProgramSfxId,
  durationForKind,
  durationMsForKind,
} from "../state/state_helpers";

/** Retarget the active ICE when the current target is dead. */
export function advanceDeadTarget(state: GameState): GameState {
  const current = state.iceRoster[state.activeIceIndex];
  if (current && current.hp > 0) return state;
  const aliveIdx = state.iceRoster.findIndex((ice) => ice.hp > 0);
  if (aliveIdx === -1) return state;
  return { ...state, activeIceIndex: aliveIdx };
}

/** The two status procs a played program can roll on its target.
 *
 * Both rolls happen whether or not the target survived the hit — the inline
 * version rolled first and checked the HP afterwards, and the draw order is
 * part of the seeded stream. A roll that lands on a dead ICE applies nothing.
 */
function rollProgramProcs(state: GameState, targetIdx: number): GameState {
  const target = state.iceRoster[targetIdx];
  let next = state;
  if (rollStatusProc("burn") && target && target.hp > 0) {
    next = applyStatus(next, "ice", "burn", 2, 3);
  }
  // 20% chance to slow the ICE for 2 turns, at 30% damage reduction.
  if (rollStatusProc("slow") && target && target.hp > 0) {
    next = applyStatus(next, "ice", "slow", 2, 30, { slowPct: 30 });
  }
  return next;
}

/** Remove the first `kind`/`ice` status — a mark is spent once it has paid. */
function consumeMark(state: GameState, kind: "vulnerable" | "slow"): GameState {
  const idx = state.statusEffects.findIndex((e) => e.kind === kind && e.target === "ice");
  if (idx < 0) return state;
  const updated = [...state.statusEffects];
  updated.splice(idx, 1);
  return { ...state, statusEffects: updated };
}

/**
 * The armor the program actually has to get through.
 *
 * ADR-0255/ADR-0277: the card's own pierce removes points, `armor_ignore`
 * keeps a share. ADR-0327: the deck's `programPower` then eats into whatever
 * survives — a share, so it scales with the ICE's plate instead of flattening
 * the damage curve.
 */
function effectiveArmorFor(effect: ProgramEffect, defenderArmor: number, programPower: number): number {
  const piercePoints = effect.kind === "pierce" ? effect.amount : 0;
  const armorKeptPct = effect.kind === "armor_ignore" ? 100 - effect.amount : 100;
  const powerBypassPct = programPowerArmorBypassPct(programPower);
  const keptAfterPower = Math.floor((armorKeptPct * (100 - powerBypassPct)) / 100);
  return Math.floor((Math.max(0, defenderArmor - piercePoints) * keptAfterPower) / 100);
}

/** Roll the damage one played program deals.
 *
 * Reads the same bonuses the inline block did (powered-status attack bonus,
 * deck attack/crit, vulnerable mark, combo, role synergy) and consumes the rng
 * in `calculateDamage`'s order — case, then crit. Extracted from `useProgram`
 * (refactor 2026-11-24); the slow reduction happens after this, on purpose, so
 * the SFX pick still sees the pre-slow number.
 */
function rollProgramDamage(
  state: GameState,
  program: Program,
  effect: ProgramEffect,
  vulnerableBonus: number,
  newCombo: number,
): { readonly damage: number; readonly isCrit: boolean } {
  const statusAttackBonus = state.statusEffects
    .filter((e) => e.kind === "powered" && e.target === "player")
    .reduce((sum, e) => sum + (e.attackBonus ?? 0), 0);

  const equipStats = state.equipmentLoadout.totalStats();
  const defenderIce = state.iceRoster[state.activeIceIndex] ?? state.ice;
  const role = (program as { role?: string }).role ?? null;

  const dmgResult = calculateDamage({
    baseDamage: program.tier * 5,
    attackerTeam: "player" as const,
    attackerAttackBonus: statusAttackBonus + equipStats.attackBonus,
    attackerCritBonusPct: equipStats.critBonusPct,
    defenderDefenseBonus: effectiveArmorFor(
      effect,
      defenderIce.armor ?? 0,
      equipStats.programPower,
    ),
    defenderIceResistance: 0,
    defenderIceKind: null,
    lastSkillRole: role,
    lastSkillCritBonus: 0,
    playerCombo: newCombo,
    roleSynergyCount: countRoleSynergy(role, []),
    defenderVulnerabilityPct: vulnerableBonus + equipStats.damageBonusPct,
    defenderSlowReductionPct: 0,
    rng: Math.random,
  });
  return { damage: dmgResult.damage, isCrit: dmgResult.isCrit };
}

export function useProgram(state: GameState, programId: string): GameState {
  state = advanceDeadTarget(state);
  const program = state.deck.find((p) => p.id === programId);
  if (!program) {
    return { ...state, message: `Program ${programId} not in hand` };
  }
  // ADR-0251: the hand label reads the same helper, so the COST it shows is
  // the COST charged here and BLOCKED is exactly this refusal.
  const newAlarm = state.player.alarm + programAlarmCost(program, state.activeMutators);
  if (newAlarm > COST_LIMIT) {
    return { ...state, message: "Cost too high — program failed" };
  }
  const newDeck = state.deck.filter((p) => p.id !== programId);
  const discard = [...state.discardPile, program];

  const vulnerableBonus = state.statusEffects
    .filter((e) => e.kind === "vulnerable" && e.target === "ice")
    .reduce((sum, e) => sum + e.magnitude, 0);

  const newCombo = state.playerCombo + 1;
  // ADR-0280: no clock in the reducer. `comboLastHitMs` was stamped with
  // `Date.now()` and read only by `tickCombo`, which has no caller — the
  // combo window (`COMBO_WINDOW_MS`) is authored but never enforced. Stamping
  // 0 keeps the field's meaning ("no hit recorded") without reading a clock.
  // Making the window real is a separate decision: it is a wall-clock rule in
  // a turn-based fight (ADR-0280), so it would need a turn-based form.
  const currentMs = 0;

  // ADR-0255: Backdoor ignores N points of the ICE's armor. Armor is a flat
  // subtraction, so a pierce has to remove points from it — a share of the
  // armor would round away to nothing on the lightly armored ICEs.
  // ADR-0277: `exploit` is the other direction — it keeps a share of the
  // armor, so it is worth nothing on a bare ICE and a lot on a plated one.
  const effect = programEffect(program);

  const roll = rollProgramDamage(state, program, effect, vulnerableBonus, newCombo);
  let damage = roll.damage;

  // Tier 5 SFX dispatch: pick role-specific SFX (combat_block /
  // combat_skill_*) based on the actual damage the program delivered.
  // damage === 0 with a non-support/guard program → COMBAT_BLOCK; role-driven
  // dispatch otherwise; falls back to legacy COMBAT_HIT default.
  void AudioManager.getInstance().playSfx(pickProgramSfxId(program, damage));

  const slowIdx = state.statusEffects.findIndex((e) => e.kind === "slow" && e.target === "ice");
  const slowReduction = slowIdx >= 0 ? (state.statusEffects[slowIdx]?.magnitude ?? 0) : 0;
  if (slowReduction > 0) {
    const reduction = Math.floor((damage * slowReduction) / 100);
    damage = Math.max(1, damage - reduction);
  }

  const targetIdx = state.activeIceIndex;
  const isAoe = programHitsAllIce(program);
  // ADR-0219 Option A: an ICE's shield pool absorbs incoming player damage
  // before it reaches the ICE's HP. Each roster ICE has its own pool, so the
  // absorption runs per entry and the spent pools are written back.
  let shieldState = state;
  let shieldAbsorbed = 0;
  const shieldedRoster = shieldState.iceRoster.map((ice, i) => {
    if (ice.hp <= 0) return ice;
    if (!isAoe && i !== targetIdx) return ice;
    const absorbed = absorbIceDamage(shieldState, i, damage);
    shieldState = absorbed.state;
    shieldAbsorbed += absorbed.absorbed;
    return { ...ice, hp: Math.max(0, ice.hp - absorbed.damage) };
  });
  const damagedRoster = shieldedRoster;

  let stateWithDamage: GameState = {
    ...shieldState,
    iceRoster: damagedRoster,
    playerCombo: newCombo,
    comboLastHitMs: currentMs,
  };
  const statusCountBeforeProcs = stateWithDamage.statusEffects.length;
  stateWithDamage = rollProgramProcs(stateWithDamage, targetIdx);

  // A mark is spent by the attack it was placed for: the vulnerable stack and
  // the ice slow are both consumed here, whatever they did to the damage.
  if (vulnerableBonus > 0) stateWithDamage = consumeMark(stateWithDamage, "vulnerable");
  if (slowReduction > 0) stateWithDamage = consumeMark(stateWithDamage, "slow");

  stateWithDamage = tickStatus(stateWithDamage);
  const tickResult = applyTickEffects(stateWithDamage);
  let finalState = applyBurnDamage(
    tickResult.state,
    tickResult.burnDamagePlayer + tickResult.bleedDamagePlayer,
    tickResult.burnDamageIce + tickResult.bleedDamageIce,
    tickResult.healPlayer,
    tickResult.healIce,
  );

  // ADR-0255: the program's own effect. Applied AFTER the status tick so it
  // starts at its full duration — a 3-turn shield must not be born at 2, and
  // a 1-turn decoy must not expire in the same turn it was played.
  if (effect.kind === "shield") {
    finalState = applyStatus(finalState, "player", "shield", effect.turns, effect.amount);
  } else if (effect.kind === "empower") {
    finalState = applyStatus(finalState, "player", "powered", effect.turns, effect.amount, {
      attackBonus: effect.amount,
    });
  } else if (effect.kind === "evade") {
    finalState = applyStatus(finalState, "player", "evasive", effect.turns, effect.amount);
  } else if (effect.kind === "decoy") {
    // The decoy takes part of the next hit meant for the player.
    finalState = applyStatus(finalState, "player", "evasive", effect.turns, effect.amount);
  }

  // ADR-0251 slice B: procs append, so what this play applied is the tail.
  const appliedStatuses = finalState.statusEffects.slice(statusCountBeforeProcs);
  // ADR-0251 slice B: name every status this play started or ended. Between
  // the input and `finalState` effects are only added by the procs above, so
  // the before/after difference is exactly what a shield break, a spent
  // slow / vulnerable or the tick removed. Display only; no RNG.
  const rosterSize = state.iceRoster.length;
  const statusLines = [
    ...statusEventLines(appliedStatuses, "on", rosterSize),
    ...statusEventLines(
      endedStatuses([...state.statusEffects, ...appliedStatuses], finalState.statusEffects),
      "off",
      rosterSize,
    ),
  ];
  const statusApplyVfx =
    appliedStatuses.length > 0
      ? [
          import_vfx(
            "status_apply",
            `ICE ${appliedStatuses.map((e) => e.kind.toUpperCase()).join("+")}`,
            durationForKind("status_apply"),
          ),
        ]
      : [];
  const dotOrRegenVfx: import("../../renderer/combat_vfx.ts").CombatVfxInstance[] = [];
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
  const bossPhaseChanged = state.bossPhase > 0 && finalState.bossPhase !== state.bossPhase;
  const programVfxKind = pickProgramVfxKind(program, damage);
  const programVfxInstances: ReadonlyArray<
    import("../../renderer/combat_vfx.ts").CombatVfxInstance
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
  const vfxNew: ReadonlyArray<import("../../renderer/combat_vfx.ts").CombatVfxInstance> = [
    ...finalState.vfxInstances,
    import_vfx(programVfxKind, program.name, 3),
    import_vfx("ice_hit", `${damage}`, 2),
    ...programVfxInstances,
    ...statusApplyVfx,
    ...dotOrRegenVfx,
    // ADR-0241: the CRIT flash tracks the real crit roll, not a damage
    // threshold. Spawning draws no Math.random (ADR-0239), so this condition
    // cannot shift the seeded gameplay stream.
    ...(roll.isCrit
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
    ...(bossPhaseChanged && finalState.bossPhase >= 1 && finalState.bossPhase <= 4
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

  // ADR-0278: the loot and the faction credit belong to the kill, not to the
  // victory — so they are credited here for a program kill, and in
  // `finishPlayerTurn` for a companion kill. One rule, either way.
  const { state: stateWithLoot, drops: lootDrops } = creditKills(
    finalState,
    state.iceRoster,
    finalState.iceRoster,
  );
  const newlyDefeated = killedBetween(state.iceRoster, finalState.iceRoster);

  if (allDefeated && stateWithLoot.iceRoster.length > 0) {
    // ADR-0258: this branch IS the killing blow, so it is where the COST
    // exemption applies. State it here; the hand row may not predict it.
    const victory = resolveVictory(
      {
        ...stateWithLoot,
        deck: newDeck,
        discardPile: discard,
        combatLog: [...statusLines, ...stateWithLoot.combatLog].slice(0, COMBAT_LOG_CAP),
        vfxInstances: vfxNew,
      },
      { defeated: newlyDefeated, drops: lootDrops, kind: "program" },
    );
    return victory;
  }
  const activeIceNewHp = finalState.iceRoster[targetIdx]?.hp ?? 0;
  const shieldNote = shieldAbsorbed > 0 ? ` (${shieldAbsorbed} absorbed)` : "";
  const programMessage = isAoe
    ? `${program.name} → ${damage} dmg ALL (roster hit)${shieldNote}`
    : `${program.name} → ${damage} dmg (ICE HP: ${activeIceNewHp})${shieldNote}`;
  return {
    ...stateWithLoot,
    iceRoster: stateWithLoot.iceRoster,
    deck: newDeck,
    discardPile: discard,
    player: { ...stateWithLoot.player, alarm: newAlarm },
    message: programMessage,
    combatLog: [programMessage, ...statusLines, ...stateWithLoot.combatLog].slice(
      0,
      COMBAT_LOG_CAP,
    ),
    vfxInstances: vfxNew,
    unlockedAchievements: stateWithLoot.unlockedAchievements,
    achievementCredits: stateWithLoot.achievementCredits,
    factionScores: stateWithLoot.factionScores,
  };
}
