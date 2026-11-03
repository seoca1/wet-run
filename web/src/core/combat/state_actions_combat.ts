/** Combat-tick action handlers — split from state_actions.ts per ADR-0110.
 *
 * - applyCombatAction: combat phase dispatch (cycle target, use program, jack out)
 * - cycleTarget / advanceDeadTarget: active-ICE targeting
 * - drawHand: recycle discard into a fresh hand when the deck empties
 * - processEnemyTurns: enemy auto-attack / skill tick
 *
 * Program resolution lives in `state_actions_programs.ts`; non-combat phase
 * handlers live in `state_actions_phases.ts`. All three are re-exported from
 * `state_actions.ts` so existing imports keep working.
 */

import type { GameState, GameAction, Ice, BossPhase } from "../types";
import type { CombatVfxInstance } from "../../renderer/combat_vfx";
import { AUTO_ATTACK_INTERVAL_MS, COMBO_BONUSES } from "./combat_engine";
import { DEFAULT_BOSS_PROFILE, checkPhaseTransition } from "./boss_phases";
import { enemyShouldUseSkill, selectSkillByPersonality } from "./ice_ai";
import { rollIceCrit } from "./ice_crit";
import { alarmDamage } from "./idle_alarm";
import { iceAttackBonus, tickIceEffects } from "./ice_combat_effects";
import { applyPlayerMitigation } from "./player_mitigation";
import { applyIceNonDamageEffect } from "./ice_combat_effect_apply";
import { endedStatuses, statusEventLines } from "../status";
import { iceDmgBonusPctForGrade, missionGradeOf } from "./ice_scaling";
import { isMutatorActive, type MutableRunState } from "../state/run_mutators";
import {
  createDeceasedJockey,
  generateDeathSummary,
} from "../state/death_cycle";
import {
  COMBAT_LOG_CAP,
  import_vfx,
  import_vfx_deterministic,
  import_vfx_ms,
  durationForKind,
  durationMsForKind,
} from "../state/state_helpers";
import { useProgram, advanceDeadTarget } from "./state_actions_programs";
import { everyProgramBlocked } from "./program_affordance";

/** Dixie companion tuning (ADR-0244 option 2).
 * N=2 preserves the 2000ms harness baseline: first player turn, then alternate
 * successful program plays. Initial counter N-1 preserves that opening phase.
 * Changing N is a separate balance decision; damage remains 8 + combo * 3.
 * Exported for the design-conformance suite; see docs/design/systems/combat.md.
 */
export const DIXIE_ATTACK_EVERY_N_PLAYER_TURNS = 2;
export const DIXIE_BASE_DAMAGE = 8;
export const DIXIE_SYNERGY_BONUS = 3;

/** The combo ceiling the damage table defines: `COMBO_BONUSES` ends at 6 and
 * a card above it already falls back to 1.0. Dixie's synergy read the raw
 * counter, which nothing resets inside a run (`openArrivalEncounter` keeps
 * it), so by the later fights she hit for 68-92 while a card hit for 4-17 --
 * the ally fought the fights and the player watched (ADR-0268). */
export const MAX_COMBO = Math.max(...Object.keys(COMBO_BONUSES).map(Number));

/** Dixie's damage for a combo, capped at the ceiling the combo system defines. */
export function dixieDamage(combo: number): number {
  return DIXIE_BASE_DAMAGE + Math.min(combo, MAX_COMBO) * DIXIE_SYNERGY_BONUS;
}

export function applyCombatAction(
  state: GameState,
  action: GameAction,
): GameState {
  if (action.type === "cycle_target") {
    return cycleTarget(state);
  }
  if (action.type === "select_program") {
    const idx = action.handIndex - 1;
    if (idx < 0 || idx >= state.deck.length) {
      return {
        ...state,
        message:
          state.deck.length === 0
            ? "Hand empty — no programs to play"
            : `Hand slot ${action.handIndex} is empty`,
      };
    }
    return state;
  }
  if (action.type === "use_program") {
    const result = useProgram(state, action.programId);
    if (result.deck.length === state.deck.length) return result;
    return finishPlayerTurn(result);
  }
  // ADR-0266: when every program in hand is over the COST limit, playing is
  // refused and the hand never empties -- so the turn never advanced and the
  // fight froze until JACK OUT. ENTER now ends that turn instead: the hand is
  // discarded, the enemies act, and a fresh hand is dealt. COST does not
  // fall, so the pressure stands and the run is decided by the fight, not by
  // a screen that stopped answering.
  if (action.type === "confirm" && everyProgramBlocked(state)) {
    const discarding: GameState = {
      ...state,
      deck: [],
      discardPile: [...state.discardPile, ...state.deck],
    };
    const passed = finishPlayerTurn(discarding);
    return passed.runPhase === "combat"
      ? { ...passed, message: "COST capped — turn passed" }
      : passed;
  }
  if (action.type === "jack_out") {
    return {
      ...state,
      runPhase: "dead",
      phase: "defeat",
      message: "Jacked out — mission failed",
    };
  }
  return state;
}

/** The tail of a full player turn: the enemies act, the empty hand recycles,
 * and a wiped roster resolves as a victory. Shared by playing a program and by
 * passing a turn (ADR-0266), so both can reach the same outcome. */
function finishPlayerTurn(state: GameState): GameState {
  const afterEnemies = drawHand(processDixieTurn(processEnemyTurns(state)));
  const allDefeated = afterEnemies.iceRoster.every((ice) => ice.hp === 0);
  if (
    allDefeated &&
    afterEnemies.iceRoster.length > 0 &&
    afterEnemies.runPhase === "combat"
  ) {
    const totalReward =
      afterEnemies.mission.rewards.credits +
      (afterEnemies.matrix?.nodes[afterEnemies.currentNodeIndex]?.reward
        .credits ?? 0);
    return {
      ...afterEnemies,
      runPhase: "loot",
      phase: "victory",
      message: `${afterEnemies.ice.name} defeated! +${totalReward} credits`,
      player: {
        ...afterEnemies.player,
        credits: afterEnemies.player.credits + totalReward,
      },
      vfxInstances: [
        ...afterEnemies.vfxInstances,
        import_vfx("victory", "", 5),
      ],
    };
  }
  return afterEnemies;
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

/** Card draw (ADR-0212 step-4): when the hand empties, recycle the discard into
 * the draw pile and deal a fresh hand so combat can continue past the opening 5
 * cards. Order is preserved (no shuffle) so the draw consumes no RNG and stays
 * deterministic; the fight is bounded by the alarm cap. Runs after the enemy
 * turn so the "was a program played" guard in applyCombatAction still works.
 */
function drawHand(state: GameState): GameState {
  if (state.deck.length > 0) return state;
  const pool = [...state.drawPile, ...state.discardPile];
  if (pool.length === 0) return state;
  const size = state.player.handSize;
  return {
    ...state,
    deck: pool.slice(0, size),
    drawPile: pool.slice(size),
    discardPile: [],
  };
}

function processDixieTurn(state: GameState): GameState {
  const turns = state.dixiePlayerTurnsSinceAttack + 1;
  const targetIdx = state.iceRoster.findIndex((ice) => ice.hp > 0);
  if (turns < DIXIE_ATTACK_EVERY_N_PLAYER_TURNS || targetIdx < 0) {
    return { ...state, dixiePlayerTurnsSinceAttack: turns };
  }
  const dixieDmg = dixieDamage(state.playerCombo);
  const message = `>>> Dixie attacks: ${dixieDmg} dmg`;
  return {
    ...state,
    dixiePlayerTurnsSinceAttack: 0,
    iceRoster: state.iceRoster.map((ice, i) =>
      i === targetIdx ? { ...ice, hp: Math.max(0, ice.hp - dixieDmg) } : ice,
    ),
    message: state.phase === "defeat" ? state.message : message,
    combatLog:
      state.phase === "defeat"
        ? state.combatLog
        : [message, ...state.combatLog].slice(0, COMBAT_LOG_CAP),
  };
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
  const enemyTurnVfx: CombatVfxInstance[] = [];

  for (const key of Object.keys(newCooldowns)) {
    newCooldowns[key] = Math.max(
      0,
      (newCooldowns[key] ?? 0) - AUTO_ATTACK_INTERVAL_MS,
    );
  }

  let newBossPhase = state.bossPhase;
  if (state.bossPhase > 0) {
    const bossIce = state.iceRoster.find((ice) => ice.hp > 0);
    if (bossIce) {
      const tracker = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: state.bossPhase,
        phaseChangeMs: 0,
        phaseChangeColor: "#ffffff",
      };
      const updated = checkPhaseTransition(
        tracker,
        bossIce.hp,
        bossIce.maxHp ?? 100,
        currentMs,
      );
      if (updated.currentPhase > state.bossPhase && updated.currentPhase <= 4) {
        newBossPhase = updated.currentPhase as BossPhase;
        logMessages.push(
          `★ BOSS PHASE ${newBossPhase} — ${DEFAULT_BOSS_PROFILE.phases[newBossPhase - 1]?.label}`,
        );
      }
    }
  }

  const bossDamageMultiplier =
    state.bossPhase > 0
      ? state.bossPhase === 2
        ? 1.25
        : state.bossPhase === 3
          ? 1.5
          : state.bossPhase >= 4
            ? 2.0
            : 1.0
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

  // Working copy so the ICE-side effects (shield / regen / buff) can mutate
  // `statusEffects` and the roster's HP inside the loop. ADR-0219 Option A.
  // It starts from the roster that existed *before* the phase-4 minion was
  // appended: a freshly deployed minion acts from the next enemy turn on.
  let working: GameState = { ...state, iceRoster: state.iceRoster };

  for (let iceIndex = 0; iceIndex < working.iceRoster.length; iceIndex++) {
    const enemy = working.iceRoster[iceIndex];
    if (!enemy || enemy.hp <= 0) continue;

    let enemySkills = enemy.skills ?? [];

    if (isMutatorActive(state as unknown as MutableRunState, "stealth_only")) {
      const stealthEffects = ["dot", "poison", "debuff", "silence", "slow"];
      enemySkills = enemySkills.filter((s) =>
        stealthEffects.includes(s.effect),
      );
    }

    let usedSkill = false;

    if (
      enemySkills.length > 0 &&
      enemyShouldUseSkill(enemy, Math.random, state.alarmLevel)
    ) {
      const selectedSkill = selectSkillByPersonality(enemy, enemySkills);

      if (selectedSkill) {
        const cooldownKey = `${enemy.id}_${selectedSkill.id}`;
        const remaining = newCooldowns[cooldownKey] ?? 0;

        if (remaining <= 0 && selectedSkill.damage > 0) {
          const rawSkillDmg =
            selectedSkill.damage +
            enemy.tier * 2 +
            iceAttackBonus(working, iceIndex);
          const baseSkillDmg = Math.max(
            1,
            Number.isFinite(rawSkillDmg) ? rawSkillDmg : 1,
          );
          // ADR-0161 `aggressive` archetype: +5% crit chance on the ICE's
          // outgoing damage. The roll is a pure function of the injected RNG
          // and consumes the same `Math.random` the balance harness controls,
          // so the simulation stays deterministic.
          const crit = rollIceCrit(enemy, baseSkillDmg, Math.random);
          const skillDmg = alarmDamage(crit.damage, state.alarmLevel);
          // ADR-0255: the player's shield pool and evasion stand between the
          // ICE's hit and the player's HP.
          const mitigated = applyPlayerMitigation(working, skillDmg);
          working = mitigated.state;
          playerHp = Math.max(0, playerHp - mitigated.damage);
          if (mitigated.absorbed > 0 || mitigated.dodged > 0) {
            logMessages.push(
              `>>> shield absorbed ${mitigated.absorbed}, evasion dodged ${mitigated.dodged}`,
            );
          }
          enemyTurnVfx.push(
            import_vfx_deterministic(
              "player_hit",
              "",
              durationForKind("player_hit"),
              undefined,
              undefined,
              mitigated.damage,
            ),
          );
          logMessages.push(
            `>>> ${enemy.name} uses ${selectedSkill.name}: ${skillDmg} dmg${crit.isCrit ? " CRITICAL" : ""}`,
          );
          newCooldowns[cooldownKey] = selectedSkill.cooldownMs;
          usedSkill = true;
        } else if (remaining <= 0) {
          // ADR-0219 Option A: a non-damaging skill now fires as an effect
          // instead of being blocked by the `damage > 0` gate. The skill
          // still consumes the ICE's action.
          const outcome = applyIceNonDamageEffect(
            working,
            iceIndex,
            enemy,
            selectedSkill,
          );
          working = outcome.state;
          if (outcome.message !== null) {
            logMessages.push(outcome.message);
            enemyTurnVfx.push(...outcome.vfx);
            newCooldowns[cooldownKey] = selectedSkill.cooldownMs;
            usedSkill = true;
          }
        }
      }
    }

    if (!usedSkill) {
      const rawAutoDmg = enemy.tier * 3 + (enemy.armor ?? 0);
      let autoDmg = Math.max(1, Number.isFinite(rawAutoDmg) ? rawAutoDmg : 1);
      // ADR-0211 fun-fix: per-grade ICE dmg modifier. Pairs with the HP cap in
      // ice_scaling.ts — cap contests g3+ (where tier-3+ natural HP > cap),
      // the bonus contests g1-g2 (where tier-1/2 natural HP < cap and the
      // opener otherwise kills the ICE before taking any meaningful dmg).
      // The value may be negative (g6 -20%): the g6 band is tanky enough that
      // the developed deck flatlined at the HP cap, so the climax needs an ICE
      // dmg *penalty* to stay attainable. Any non-zero value applies.
      // Skipped for boss rooms (bossPhase > 0): boss encounter tension is
      // already carried by phase multipliers (1.25x / 1.5x / 2x) so stacking
      // the per-grade modifier would tip the boss AI tests out of phase intent.
      if (state.bossPhase === 0) {
        const dmgBonusPct = iceDmgBonusPctForGrade(
          state.mission.grade ?? missionGradeOf(state.mission),
        );
        if (dmgBonusPct !== 0) {
          autoDmg = Math.max(1, Math.floor(autoDmg * (1 + dmgBonusPct / 100)));
        }
      }

      if (enemy.tier >= 3 && state.bossPhase > 0) {
        autoDmg = Math.floor(autoDmg * bossDamageMultiplier);
      }

      // ADR-0219 Option A: the `buff` bonus is added after the grade and
      // boss multipliers, so a temporary in-combat buff is worth the same
      // flat amount at every grade instead of being amplified by the
      // difficulty curve.
      autoDmg += iceAttackBonus(working, iceIndex);

      // ADR-0161 `aggressive` archetype: +5% crit chance on the ICE's
      // outgoing auto-attack. The roll is a pure function of the injected RNG
      // and consumes the same `Math.random` the balance harness controls, so
      // the simulation stays deterministic.
      const crit = rollIceCrit(enemy, autoDmg, Math.random);
      autoDmg = alarmDamage(crit.damage, state.alarmLevel);

      // ADR-0255: the player's shield pool and evasion stand between the
      // ICE's hit and the player's HP.
      const autoMitigated = applyPlayerMitigation(working, autoDmg);
      working = autoMitigated.state;
      playerHp = Math.max(0, playerHp - autoMitigated.damage);
      if (autoMitigated.absorbed > 0 || autoMitigated.dodged > 0) {
        logMessages.push(
          `>>> shield absorbed ${autoMitigated.absorbed}, evasion dodged ${autoMitigated.dodged}`,
        );
      }
      enemyTurnVfx.push(
        import_vfx_deterministic(
          "player_hit",
          "",
          durationForKind("player_hit"),
          undefined,
          undefined,
          autoDmg,
        ),
      );

      if (enemy.tier >= 3 && state.bossPhase >= 3) {
        logMessages.push(
          `>>> ${enemy.name} AoE: ${autoDmg} dmg (hits all!)${crit.isCrit ? " CRITICAL" : ""}`,
        );
      } else {
        logMessages.push(
          `>>> ${enemy.name} attacks: ${autoDmg} dmg${crit.isCrit ? " CRITICAL" : ""}`,
        );
      }
    }
  }

  // ADR-0219 Option A: advance the enemy-timed ICE effects (shield pool
  // lifetime, regen ticks, buff lifetime). One tick = one enemy turn.
  const iceEffectsBeforeTick = working.statusEffects;
  working = tickIceEffects(working);
  // ADR-0251 slice B: the tick used to drop ended ICE-cast effects silently.
  // Log lines only — `logMessages` (and so `anyEnemyAttacked`) is untouched.
  const endedIceEffectLines = statusEventLines(
    endedStatuses(iceEffectsBeforeTick, working.statusEffects),
    "off",
    working.iceRoster.length,
  );
  // The acted roster shares the prefix of `rosterForReturn`; the phase-4
  // minion is appended after it, so merge positionally (roster ids are not
  // unique — the encounter band repeats ids when a node has fewer ids than
  // the roster needs).
  rosterForReturn = [
    ...working.iceRoster,
    ...rosterForReturn.slice(working.iceRoster.length),
  ];

  const anyEnemyAttacked = logMessages.length > 0;

  if (playerHp <= 0) {
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
      runPhase: "dead",
      phase: "defeat",
      message: "FLATLINE",
      player: { ...state.player, hp: 0 },
      lastDeathSummary: summary,
      totalDeaths: state.totalDeaths + 1,
      deceasedJockeys: [...state.deceasedJockeys, jockey],
      skillCooldowns: newCooldowns,
      iceRoster: rosterForReturn,
      statusEffects: working.statusEffects,
      bossPhase: newBossPhase,
      vfxInstances: [
        ...state.vfxInstances,
        ...enemyTurnVfx,
        import_vfx_deterministic("defeat", "", durationForKind("defeat")),
      ],
      lastEnemyAttackMs: anyEnemyAttacked ? currentMs : state.lastEnemyAttackMs,
      counterWindowOpenMs: anyEnemyAttacked
        ? currentMs
        : state.counterWindowOpenMs,
    };
  }

  const bossPhaseChangedInEnemyTurn = newBossPhase > state.bossPhase;

  const bossPhaseVfx: CombatVfxInstance[] =
    bossPhaseChangedInEnemyTurn && newBossPhase >= 1 && newBossPhase <= 4
      ? [
          import_vfx_ms(
            "boss_phase_transition",
            "",
            durationMsForKind("boss_phase_transition"),
            undefined,
            undefined,
            newBossPhase,
          ),
        ]
      : [];

  return {
    ...state,
    skillCooldowns: newCooldowns,
    iceRoster: rosterForReturn,
    statusEffects: working.statusEffects,
    bossPhase: newBossPhase,
    player: { ...state.player, hp: playerHp },
    lastEnemyAttackMs: anyEnemyAttacked ? currentMs : state.lastEnemyAttackMs,
    counterWindowOpenMs: anyEnemyAttacked
      ? currentMs
      : state.counterWindowOpenMs,
    message:
      logMessages.length > 0
        ? logMessages[logMessages.length - 1]
        : state.message,
    combatLog:
      logMessages.length > 0 || endedIceEffectLines.length > 0
        ? [
            ...logMessages.slice().reverse(),
            ...endedIceEffectLines,
            ...state.combatLog,
          ].slice(0, COMBAT_LOG_CAP)
        : state.combatLog,
    vfxInstances:
      bossPhaseVfx.length > 0 || enemyTurnVfx.length > 0
        ? [...state.vfxInstances, ...enemyTurnVfx, ...bossPhaseVfx]
        : state.vfxInstances,
  };
}
