/** Combat-tick action handlers — split from state_actions.ts per ADR-0110.
 *
 * - applyCombatAction: combat phase dispatch (cycle target, use program, jack out)
 * - cycleTarget / advanceDeadTarget: active-ICE targeting
 * - drawHand: recycle discard into a fresh hand when the deck empties
 * - processEnemyTurns: enemy auto-attack / skill tick + Dixie companion tick
 *
 * Program resolution lives in `state_actions_programs.ts`; non-combat phase
 * handlers live in `state_actions_phases.ts`. All three are re-exported from
 * `state_actions.ts` so existing imports keep working.
 */

import type { GameState, GameAction, Ice, BossPhase } from "./types.ts";
import type { CombatVfxInstance } from "../renderer/combat_vfx.ts";
import { AUTO_ATTACK_INTERVAL_MS } from "./combat_engine.ts";
import { DEFAULT_BOSS_PROFILE, checkPhaseTransition } from "./boss_phases.ts";
import { enemyShouldUseSkill, selectSkillByPersonality } from "./ice_ai.ts";
import { rollIceCrit } from "./ice_crit.ts";
import { iceAttackBonus, tickIceEffects } from "./ice_combat_effects.ts";
import { applyIceNonDamageEffect } from "./ice_combat_effect_apply.ts";
import { iceDmgBonusPctForGrade, missionGradeOf } from "./ice_scaling.ts";
import { isMutatorActive, type MutableRunState } from "./run_mutators.ts";
import { createDeceasedJockey, generateDeathSummary } from "./death_cycle.ts";
import {
  COMBAT_LOG_CAP,
  import_vfx,
  import_vfx_deterministic,
  import_vfx_ms,
  durationForKind,
  durationMsForKind,
} from "./state_helpers.ts";
import { useProgram, advanceDeadTarget } from "./state_actions_programs.ts";

/** Dixie companion tuning.
 *
 * Design reference: `docs/design/systems/combat.md` L101-102 specifies
 * "Dixie ally: 2000ms interval, 5 dmg per tick (fixed, no stat boost)".
 * The shipped values below diverge (see `design_conformance.test.ts`).
 * Exported so the design-conformance suite can assert them against the doc.
 */
export const DIXIE_ATTACK_INTERVAL_MS = 3000;
export const DIXIE_BASE_DAMAGE = 8;
export const DIXIE_SYNERGY_BONUS = 3;

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
    const afterEnemies = drawHand(processEnemyTurns(result));

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
      enemyShouldUseSkill(enemy, Math.random)
    ) {
      const selectedSkill = selectSkillByPersonality(
        enemy,
        enemySkills,
      );

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
          const skillDmg = crit.damage;
          playerHp = Math.max(0, playerHp - skillDmg);
          enemyTurnVfx.push(
            import_vfx_deterministic(
              "player_hit",
              "",
              durationForKind("player_hit"),
              undefined,
              undefined,
              skillDmg,
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
      autoDmg = crit.damage;

      playerHp = Math.max(0, playerHp - autoDmg);
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
  working = tickIceEffects(working);
  // The acted roster shares the prefix of `rosterForReturn`; the phase-4
  // minion is appended after it, so merge positionally (roster ids are not
  // unique — the encounter band repeats ids when a node has fewer ids than
  // the roster needs).
  rosterForReturn = [
    ...working.iceRoster,
    ...rosterForReturn.slice(working.iceRoster.length),
  ];

  const anyEnemyAttacked = logMessages.length > 0;

  let dixieAttacked = false;
  if (currentMs - state.dixieLastAttackMs >= DIXIE_ATTACK_INTERVAL_MS) {
    const targetIdx = rosterForReturn.findIndex((ice) => ice.hp > 0);
    if (targetIdx >= 0) {
      const dixieDmg =
        DIXIE_BASE_DAMAGE + state.playerCombo * DIXIE_SYNERGY_BONUS;
      const newRoster = rosterForReturn.map((ice, i) => {
        if (i !== targetIdx) return ice;
        return { ...ice, hp: Math.max(0, ice.hp - dixieDmg) };
      });
      rosterForReturn = newRoster;
      working = { ...working, iceRoster: newRoster };
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
      dixieLastAttackMs: dixieAttacked ? currentMs : state.dixieLastAttackMs,
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
    dixieLastAttackMs: dixieAttacked ? currentMs : state.dixieLastAttackMs,
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
      logMessages.length > 0
        ? [...logMessages.slice().reverse(), ...state.combatLog].slice(
            0,
            COMBAT_LOG_CAP,
          )
        : state.combatLog,
    vfxInstances:
      bossPhaseVfx.length > 0 || enemyTurnVfx.length > 0
        ? [...state.vfxInstances, ...enemyTurnVfx, ...bossPhaseVfx]
        : state.vfxInstances,
  };
}
