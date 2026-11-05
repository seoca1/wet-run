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
import { isTerminalNode } from "../state/run_end";

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
  const totalReward = nodeReward + missionReward + achievementCredits;

  const lootMessage =
    drops.length > 0
      ? ` Loot: ${drops.map((d) => `${d.item} x${d.quantity}`).join(", ")}`
      : "";
  // ADR-0258: only the card that drops the last ICE is exempt from COST. A
  // companion's finishing blow exempts nothing, so it does not claim it.
  const costNote = kind === "program" ? " (no COST)" : "";
  const bountyNote = missionReward > 0 ? " (mission complete)" : "";
  const victoryMessage = `${defeatedIceName(state, defeated)} defeated!${costNote} +${totalReward} credits${bountyNote}${lootMessage}`;

  return {
    ...state,
    runPhase: "loot",
    phase: "victory",
    message: victoryMessage,
    combatLog: [victoryMessage, ...state.combatLog].slice(0, COMBAT_LOG_CAP),
    player: {
      ...state.player,
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
