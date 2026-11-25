/** The run's life cycle: starting a run, resuming one, ending one, and the
 * autosave that sits under all of it.
 *
 * Refactoring Stage 3a-3 (2026-11-25). These are the transitions that move
 * `state` in and out of existence, plus the save-cache bookkeeping around them.
 * They touch a lot of controller state, which is why the host is wide - the
 * plan's "widen one at a time" taken to its end for this slice.
 *
 * `main.ts` is outside the balance harness's import graph, so e2e is the guard.
 * Behaviour is preserved exactly.
 */
import type {
  GameState,
  Ice,
  Inventory,
  EquipmentLoadout,
  Mission,
  Program,
  ScreenKind,
} from "../core/types";
import type { ArcId } from "../core/combat/ending_resolver";
import type { DialogueBeat } from "../core/state/event_beats";
import type { Layout } from "../core/layout";
import type { SettingsState } from "../renderer/settings";
import type { InfoMarket } from "../core/info_market";
import type { DungeonCrawler } from "../core/dungeon/dungeon_crawler";
import type { MaterialDef, Recipe } from "../core/state/crafting";
import type { OwnedSet } from "../core/state/owned_equipment";
import type { PrepChoice } from "../core/state/prep";
import type { LootCommit, MatrixArrival } from "../renderer/growth_reveal";
import { makeInfoMarket } from "../core/state/crafting";
import { makeGrid } from "../core/grid";
import { startingDeck } from "../core/state/starting_deck";
import { JOCKEYS } from "../core/state/jockey";
import { applyPrep } from "../core/state/prep";
import { applyEquipmentSurvival } from "../core/state/equipment_stats";
import { contractFor } from "../core/state/campaign";
import { missionIce } from "../core/state/mission_ice";
import { openArrivalEncounter } from "../core/state/encounter_verbs";
import { runOpeningBeat } from "../core/state/event_beats";
import { runsFinished, markRunFinished } from "../core/state/onboarding";
import { makeInitialState, slotToGameState, stateToSaveSlot } from "../core/state/state";
import { autosaveIntent } from "../core/state/run_end";
import {
  contractSeedMaterials,
  mergeRunIntoWallet,
  seedRunWallet,
  writeWalletMaterials,
} from "../core/state/wallet";
import { mergeDroppedEquipment, writeOwnedIds } from "../core/state/owned_equipment";
import { createDungeonCrawlerFromMission } from "../core/dungeon/dungeon_crawler";
import {
  clear as clearSlot,
  getSaveMeta,
  load as loadFromSlot,
  save as saveToSlot,
  hasSave as slotHasSave,
} from "../save/storage";

/** What the run life cycle needs from the game controller. */
export interface RunLifecycleHost {
  state: GameState | null;
  screen: ScreenKind;
  layout: Layout;
  iceTypes: Readonly<Record<string, Ice>>;
  missions: ReadonlyArray<Mission>;
  programs: Readonly<Record<string, Program>>;
  selectedMission: number;
  selectedJockey: number;
  settingsState: SettingsState | null;
  prepChoice: PrepChoice;
  prepWalletOutlay: number;
  equipmentLoadout: EquipmentLoadout;
  inventory: Inventory;
  ownedEquipment: OwnedSet;
  recipes: ReadonlyArray<Recipe>;
  materials: ReadonlyArray<MaterialDef>;
  infoMarket: InfoMarket;
  dungeonCrawler: DungeonCrawler | null;
  lootCommit: LootCommit | null;
  matrixArrival: MatrixArrival | null;
  runIntroArc: ArcId | null;
  runIntroBeat: DialogueBeat | null;
  runWalletSeed: Inventory | null;
  hasSaveCache: boolean;
  saveMetaCache: { missionId: string; turnCount: number; savedAt: string } | null;
  menuSelectionNormalized: boolean;
  lastPersistedState: GameState | null;
  persistQueue: Promise<void>;
  _lastIceHp: number | null;
  _lastPlayerHp: number | null;
  draw(): void;
  loadCrafting(): {
    readonly recipes: ReadonlyArray<Recipe>;
    readonly materials: ReadonlyArray<MaterialDef>;
  };
}

export function startRun(host: RunLifecycleHost): void {
  const mission = host.missions[host.selectedMission];
  if (!mission) return;
  // A fresh run carries no reveal from the previous one (ADR-0262).
  host.lootCommit = null;
  host.matrixArrival = null;
  // ADR-0272: the run opens on the arc's framing beat. CONTINUE does not set
  // this (a resumed run is mid-story); only a fresh run does.
  host.runIntroArc = ((mission.arc as ArcId) || 1) as ArcId;
  // ADR-0317 (3b): the construct introduces herself on the first jack-in, and
  // only then — a profile that has finished a run has already met her.
  host.runIntroBeat = runOpeningBeat(
    runsFinished(typeof localStorage === "undefined" ? null : localStorage),
    host.settingsState?.language ?? "en",
  );
  const programs = host.programs;
  // ADR-0276: the jockey decides the opening deck, not just the name.
  const deck = startingDeck(programs, JOCKEYS[host.selectedJockey]?.id ?? null);
  const ice = missionIce(mission, host.iceTypes);
  const initial = makeInitialState(mission, ice, deck);
  host.state = openArrivalEncounter({
    // ADR-0284: whatever the stockpile paid for is spent here, so it is a
    // hoard rather than a permanent bonus.
    // ADR-0326: the gear's hpBonus/shieldBonus join it — same run-start shape.
    ...applyEquipmentSurvival(
      applyPrep(initial, host.prepChoice, host.prepWalletOutlay),
      host.equipmentLoadout,
    ),
    // ADR-0315 slice 2: the run is a contract — this mission, then the rest
    // of its arc. The chosen mission decides the arc; the length is the
    // resolver's (`CONTRACT_LENGTH`).
    campaign: contractFor(mission, host.missions, (m) => missionIce(m, host.iceTypes)),
    jockeyId: JOCKEYS[host.selectedJockey]?.id ?? null,
    grid: makeGrid(host.layout.cols, host.layout.rows),
    currentNodeIndex: 0,
    runPhase: "matrix",
    phase: "approach",
  });
  // ADR-0323 / ADR-0338: the run is seeded from the HOARD, and the seed spans
  // the WHOLE contract's rewards (the run accumulates every leg's reward, see
  // `startNextLeg`), so `mergeRunIntoWallet` banks only what the run EARNED —
  // jacking out on frame one mints nothing. The span lives in `wallet.ts` now
  // (`contractSeedMaterials`), where a unit test pins it.
  const seedRewards = contractSeedMaterials(
    host.state.campaign?.legs,
    host.state.mission.rewards.materials,
  );
  host.runWalletSeed = seedRunWallet(host.inventory, { credits: 0, materials: seedRewards });
  // ADR-0322: the run reads `state.equipmentLoadout`, so the menu's gear has
  // to be ON the state — not merely next to it. `makeInitialState` builds it
  // empty, which is why the menu used to change no number at all.
  host.state = {
    ...host.state,
    equipmentLoadout: host.equipmentLoadout,
    inventory: seedRunWallet(host.inventory, host.state.mission.rewards),
  };
  const crafting = host.loadCrafting();
  host.recipes = crafting.recipes;
  host.materials = crafting.materials;
  host.infoMarket = makeInfoMarket({});
  host.draw();
}

/** Load autosave (slot 0) and resume from saved state.
 *
 * Returns silently if no save exists (gated by hasSaveCache). On success,
 * transitions to the in-game state and resets _lastIceHp/_lastPlayerHp
 * so hit-flash VFX doesn't trigger immediately on resume.
 */
export async function continueRun(host: RunLifecycleHost): Promise<void> {
  if (!host.hasSaveCache) {
    // No save — show stub message (should be unreachable from menu but safe).
    host.draw();
    return;
  }
  const slot = await loadFromSlot(0);
  if (!slot) {
    // Stale cache: hasSave said true but load failed. Refresh + stub.
    await refreshSaveCache(host);
    host.draw();
    return;
  }
  const fallbackIce = Object.values(host.iceTypes)[0];
  if (!fallbackIce) {
    host.draw();
    return;
  }
  const restored = slotToGameState(slot, host.missions, host.programs, fallbackIce, host.iceTypes);
  if (!restored) {
    // Mission no longer in catalog or all programs disappeared.
    host.draw();
    return;
  }
  host.state = {
    ...restored,
    grid: makeGrid(host.layout.cols, host.layout.rows),
  };
  host.screen = "menu"; // game-internal state; main screen renderer picks up state != null
  host._lastIceHp = restored.ice.hp;
  host._lastPlayerHp = restored.player.hp;
  host.draw();
}

/** ADR-0323: bank the run's earnings into the hoard and clear the seed.
 *
 * Called on every way a run ends — jack out, the ending, and a flatline — so
 * a failed run keeps what it picked up. That is the owner's decision: without
 * it, no recipe can cost more than one run's yield. */
export function settleRun(host: RunLifecycleHost): void {
  const run = host.state?.inventory ?? null;
  host.inventory = mergeRunIntoWallet(host.inventory, run, host.runWalletSeed);
  host.runWalletSeed = null;
  writeWalletMaterials(host.inventory.materials);
  // ADR-0329 / ADR-0346: gear salvaged during the run becomes owned when it
  // ends. The fold lives in `owned_equipment.ts` (tested); the same record is
  // returned when nothing was added, so the write is skipped then.
  const owned = mergeDroppedEquipment(host.ownedEquipment, host.state?.droppedEquipment ?? []);
  if (owned !== host.ownedEquipment) {
    host.ownedEquipment = owned;
    writeOwnedIds(owned);
  }
}

export function startDungeonCrawl(host: RunLifecycleHost): void {
  const mission = host.missions[0] ?? null;
  host.dungeonCrawler = createDungeonCrawlerFromMission(mission);
  host.screen = "dungeon";
  host.draw();
}

/** ADR-0252: write the rendered run state to slot 0, or retire the slot
 * once the run has reached its ending. Storage operations are chained so
 * a retirement can never be overtaken by an earlier, slower write. */
export function autosaveRun(host: RunLifecycleHost): void {
  const state = host.state;
  const intent = autosaveIntent(state);
  if (state === null || intent === "skip") return;
  if (state === host.lastPersistedState) return; // unchanged frame
  host.lastPersistedState = state;
  // Snapshot now: the slot must hold this frame, not a later one.
  const slot = intent === "write" ? stateToSaveSlot(state) : null;
  host.persistQueue = host.persistQueue
    .then(() => (slot === null ? clearSlot(0) : saveToSlot(0, slot)))
    .then(() => refreshSaveCache(host))
    .catch(() => {
      // Best-effort (fire-and-forget, ADR-0209); the chain must stay usable.
    });
}

/** ADR-0315: the menu grows with the player. A finished run (ending or
 * flatline) unlocks the archive/workshop entries, which otherwise open onto
 * nothing. Also re-normalizes the cursor, since the visible list just grew. */
export function noteRunFinished(host: RunLifecycleHost): void {
  if (typeof localStorage === "undefined") return;
  markRunFinished(localStorage);
  host.menuSelectionNormalized = false;
}

/** Reload hasSave + meta caches from storage. Call after save/load/clear. */
export async function refreshSaveCache(host: RunLifecycleHost): Promise<void> {
  host.hasSaveCache = await slotHasSave(0);
  host.saveMetaCache = await getSaveMeta(0);
  // Re-draw the title menu to reflect availability. In a run `screen` can
  // also be "menu" (after CONTINUE); redrawing it would re-trigger the
  // autosave and loop on every write.
  if (host.screen === "menu" && host.state === null) host.draw();
}
