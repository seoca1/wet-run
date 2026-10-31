import type { GameState, Grid, Ice, Mission, Program } from "../src/core/types";
import { makeInitialState } from "../src/core/state/state";
import { EQUIP_SLOTS, makeLoadout } from "../src/core/state/equipment";
import { INITIAL_PWA_STATE } from "../src/core/pwa_manager";
import type { PreGameView } from "../src/renderer/pre_game_screen";

export const mission: Mission = {
  id: "test",
  title: "Test",
  fixer: "test",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  seed: 42,
  rewards: { credits: 10, materials: {} },
};
export const program: Program = {
  id: "p1",
  name: "Atk",
  tier: 1,
  cost: 0,
  effect: "damage",
  description: "test",
  aoe: false,
};
const ice: Ice = {
  id: "caster",
  name: "Caster",
  tier: 2,
  hp: 50,
  maxHp: 50,
  armor: 0,
};

export function runState(overrides: Partial<GameState> = {}): GameState {
  return {
    ...makeInitialState(mission, ice, [program]),
    iceRoster: [ice],
    activeIceIndex: 0,
    phase: "combat",
    runPhase: "combat",
    ...overrides,
  };
}

export function preGameView(overrides: Partial<PreGameView> = {}): PreGameView {
  return {
    screen: "menu",
    menuIndex: 0,
    missionIndex: 0,
    missionRows: ["[1] Test"],
    farGridMissions: [mission],
    hasSave: false,
    saveMeta: null,
    message: "",
    farGridUnlocked: true,
    language: "en",
    settings: {
      selectedField: "audio",
      audioEnabled: true,
      masterVolume: 0.8,
      bgmVolume: 0.5,
      sfxVolume: 0.7,
      muted: false,
      language: "en",
      storageQuota: { state: "unavailable", reason: "test fixture" },
      pwa: INITIAL_PWA_STATE,
    },
    crafting: {
      inventory: { credits: 0, materials: {}, programs: [] },
      recipes: [],
      materials: [],
      marketItemCount: 0,
      message: "",
    },
    loadout: makeLoadout(),
    equipmentSlots: EQUIP_SLOTS,
    dungeon: null,
    ...overrides,
  };
}

export function rowText(grid: Grid, y: number): string {
  return (grid.cells[y] ?? []).map((c) => c.char).join("");
}
