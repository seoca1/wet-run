/**
 * The payout of a won encounter — one place, so it cannot depend on who
 * landed the killing blow.
 *
 * ADR-0278. Two victory paths existed:
 *
 *   - `useProgram` → the player's card dropped the last ICE → loot rolled,
 *     achievements unlocked, faction score credited, the message said
 *     "(no COST)".
 *   - `finishPlayerTurn` → Dixie (or a DoT) dropped the last ICE → credits
 *     only. No loot, no `first_blood`, no `boss_slayer` (worth 1,000), no
 *     faction credit, no log line.
 *
 * So the boss's own loot (`combat_module` ×2 and friends) and the 1,000-credit
 * `boss_slayer` award existed only for players whose card happened to land
 * the last point of damage. Letting the companion finish a fight is the
 * natural way to play — the reward for winning cannot depend on it.
 *
 * The split that remains is deliberate and small: ADR-0258's COST exemption
 * belongs to the card that drops the last ICE. If Dixie finished the fight,
 * the card the player played did *not* drop it, so its COST stands and the
 * message does not claim "(no COST)".
 */
import type { GameState, Ice } from "../types";
import iceTypesData from "../../data/ice_types.json";
import { rollLoot, getLootTable, type LootDrop } from "../state/loot";
import { onIceKill, type FactionId } from "../state/faction_reputation";
import {
  COMBAT_LOG_CAP,
  import_vfx,
  import_vfx_deterministic,
  durationForKind,
} from "../state/state_helpers";
import { defeatedIceName } from "./roster";
import { COST_LIMIT } from "./program_affordance";
import { isTerminalNode } from "../state/run_end";
import { addPrepWallet, PREP_WALLET_BANK_SHARE } from "../state/prep_wallet";

/** The faction an ICE belongs to — its id carries the name. */
export function iceFactionOf(iceId: string): FactionId | null {
  if (iceId.includes("hosaka")) return "hosaka";
  if (iceId.includes("maas")) return "maas";
  if (iceId.includes("sense") || iceId.includes("net")) return "sense_net";
  if (iceId.includes("ta") || iceId.includes("construct")) return "ta";
  return null;
}

/** The ICE that fell between two roster snapshots. */
export function killedBetween(
  before: ReadonlyArray<Ice>,
  after: ReadonlyArray<Ice>,
): ReadonlyArray<Ice> {
  return after.filter((ice, i) => ice.hp === 0 && before[i]?.hp !== 0);
}

/**
 * Credit the kills between two roster snapshots: loot rolls into the
 * materials and the faction score moves.
 *
 * Call it once per transition that can kill ICE — the player's program and
 * the enemy phase are two separate transitions, and a kill in either one
 * owes the player the same loot.
 */
export function creditKills(
  state: GameState,
  before: ReadonlyArray<Ice>,
  after: ReadonlyArray<Ice>,
): { readonly state: GameState; readonly drops: ReadonlyArray<LootDrop> } {
  const killed = killedBetween(before, after);
  if (killed.length === 0) return { state, drops: [] };

  const drops: LootDrop[] = [];
  let factionScores = state.factionScores;
  for (const dead of killed) {
    const lootTable = getLootTable(
      dead.id,
      iceTypesData as Record<
        string,
        { loot_table?: { item: string; chance: number; quantity: number }[] }
      >,
    );
    drops.push(...rollLoot(lootTable));
    const faction = iceFactionOf(dead.id);
    if (faction) factionScores = onIceKill(factionScores, faction);
  }

  let next = state;
  if (drops.length > 0) {
    const materials = { ...state.inventory.materials };
    for (const drop of drops) {
      materials[drop.item] = (materials[drop.item] ?? 0) + drop.quantity;
    }
    next = { ...next, inventory: { ...next.inventory, materials } };
  }
  return { state: { ...next, factionScores }, drops };
}

/** How a fight was won — decides only the ADR-0258 COST note. */
export type VictoryKind = "program" | "companion";

/**
 * Resolve a won encounter: achievements, credits, the message, the log line
 * and the victory VFX.
 *
 * The caller has already credited the loot (see `creditKills`); `drops` is
 * what was rolled, so the message can name it.
 *
 * ADR-0279: the **mission** reward (`mission.rewards.credits`) is paid exactly
 * once, and paid here only when this win ends the mission (the boss, or a dead
 * end). It used to be added to *every* encounter win, so `First Jack`'s 500cr
 * was paid twice on a two-fight mission while the mission-select screen
 * promised 500 once. A fight that does not end the mission pays the node's own
 * reward.
 */
/** Credits a defeated ICE pays on top of the node's own reward, by tier
 * (ADR-0293).
 *
 * ADR-0292 made a drop worth its ICE, which gave the middle grades a reason to
 * choose one fight over another. It could not do that at g6: every card there is
 * already high tier, so "this fight drops better cards" has nothing left to say.
 * Money is the axis the top grade still had room on — and it is legible in the
 * fiction: a Neuromancer is worth more than a Watchdog.
 *
 * Deliberately not a power lever: credits buy prep capacity between runs and
 * intel inside one, and nothing in combat reads them, so the fitted per-encounter
 * curve is untouched.
 */
export const BOUNTY_BY_TIER: ReadonlyArray<number> = [0, 25, 50, 90, 140, 200];

/** COST a kill leaves behind, per tier of the ICE that fell (ADR-0294).
 *
 * ADR-0293 gave the top grade a reward axis, and the measurement then showed the
 * remaining shape of the problem: with no cost that scales with FIGHTING, "fight
 * everything" led on both completion and credits at g5 and g6 (+6.3pp each), so
 * the top grades had an answer rather than a trade-off. Raising encounter strength
 * did not converge the two strategies -- it widened the gap, because the runner
 * who fights arrives at the core with gear and the other does not.
 *
 * What does scale with fighting is the run's COST budget, and it is already the
 * game's clock: programs spend it, it never refills, and at 100 nothing can be
 * cast. A kill now leaves a trace worth its ICE's tier, so every fight is paid
 * for twice -- once in HP during it, once in capacity after it. Measured at
 * tier x 1 over 48 seeds: long/blind 85.6/89.2 (g3), 76.7/74.4 (g4), 40.0/43.3
 * (g5), 14.6/13.9 (g6) -- a real trade-off at every grade instead of a lean.
 */
export const TRACE_COST_PER_TIER = 1;

/** COST one kill leaves behind. */
export function traceCostFor(ice: { readonly tier?: number }): number {
  const tier = Math.round(Number(ice.tier));
  if (!Number.isFinite(tier) || tier <= 0) return 0;
  return tier * TRACE_COST_PER_TIER;
}

/** What one defeated ICE pays on top of its node's reward. */
export function bountyFor(ice: { readonly tier: number }): number {
  const tier = Math.max(0, Math.min(BOUNTY_BY_TIER.length - 1, Math.round(ice.tier)));
  return BOUNTY_BY_TIER[tier] ?? 0;
}

export function resolveVictory(
  state: GameState,
  opts: {
    readonly defeated: ReadonlyArray<Ice>;
    readonly drops: ReadonlyArray<LootDrop>;
    readonly kind: VictoryKind;
  },
): GameState {
  const { defeated, drops, kind } = opts;
  const newAchievements: string[] = [];
  let achievementCredits = 0;

  if (state.unlockedAchievements.length === 0 && defeated.length > 0) {
    newAchievements.push("first_blood");
    achievementCredits += 50;
  }
  if (
    state.bossPhase > 0 &&
    defeated.length > 0 &&
    !state.unlockedAchievements.includes("boss_slayer")
  ) {
    newAchievements.push("boss_slayer");
    achievementCredits += 1000;
  }
  if (
    state.playerCombo >= 6 &&
    !state.unlockedAchievements.includes("combo_master")
  ) {
    newAchievements.push("combo_master");
    achievementCredits += 500;
  }

  const terminal = isTerminalNode(state);
  const nodeReward =
    state.matrix?.nodes[state.currentNodeIndex]?.reward.credits ?? 0;
  const missionReward = terminal ? state.mission.rewards.credits : 0;
  // ADR-0293: each kill carries its own bounty, so a strong ICE is worth more
  // than a routine one even when the cards it drops are indistinguishable.
  const bounty = defeated.reduce((sum, ice) => sum + bountyFor(ice), 0);
  const trace = defeated.reduce((sum, ice) => sum + traceCostFor(ice), 0);
  const totalReward = nodeReward + missionReward + achievementCredits + bounty;

  // ADR-0285: the loot SALVAGE slot no longer pays credits (it patches now), so
  // the prep stockpile banks from what a win pays instead. Same precedent as the
  // far-grid gate: the reducer already owns that localStorage write.
  addPrepWallet(Math.floor(totalReward * PREP_WALLET_BANK_SHARE));

  const lootMessage =
    drops.length > 0
      ? ` Loot: ${drops.map((d) => `${d.item} x${d.quantity}`).join(", ")}`
      : "";
  // ADR-0258: only the card that drops the last ICE is exempt from COST. A
  // companion's finishing blow exempts nothing, so it does not claim it.
  const costNote = kind === "program" ? " (no COST)" : "";
  const missionNote = missionReward > 0 ? " (mission complete)" : "";
  const bountyNote = bounty > 0 ? ` (bounty ${bounty})` : "";
  const traceNote = trace > 0 ? ` · trace +${trace}` : "";
  const victoryMessage = `${defeatedIceName(state, defeated)} defeated!${costNote} +${totalReward} credits${missionNote}${bountyNote}${traceNote}${lootMessage}`;

  return {
    ...state,
    runPhase: "loot",
    phase: "victory",
    message: victoryMessage,
    combatLog: [victoryMessage, ...state.combatLog].slice(0, COMBAT_LOG_CAP),
    player: {
      ...state.player,
      // ADR-0294: the trace closes in. Capped at the run's COST ceiling, so a
      // kill can exhaust the budget but can never make a program cost more than
      // the ceiling itself.
      alarm: Math.min(COST_LIMIT, state.player.alarm + trace),
      credits: state.player.credits + totalReward,
    },
    vfxInstances: [
      ...state.vfxInstances,
      import_vfx_deterministic(
        "ice_death",
        defeatedIceName(state, defeated),
        durationForKind("ice_death"),
      ),
      import_vfx("victory", "", 5),
    ],
    unlockedAchievements: [...state.unlockedAchievements, ...newAchievements],
    achievementCredits: state.achievementCredits + achievementCredits,
  };
}
