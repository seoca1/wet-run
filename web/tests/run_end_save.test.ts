/** ADR-0252: the autosave reflects committed state, and a finished run ends.
 *
 * Owner report: "맵에서 보스를 쓰러뜨린후 이동하려니 또 보스가 나와서 회복 못하고
 * 패배하게 되던데." Reproduced live on the boot mission (Aleph Fragment,
 * 0 → 25 → 16 → 18 ICE → 20 boss): the slot kept the last combat frame
 * (`cleared [18]`), the ending screen never left, and CONTINUE reopened the
 * boss as a new fight whose roster was built from the wrong base ICE
 * (`wintermute 140/140` against the live 165).
 *
 * The new modules are loaded with `import()` so that, at the pre-fix HEAD,
 * only the tests that need them fail and every guard still runs.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  applyAction,
  makeInitialState,
  slotToGameState,
  stateToSaveSlot,
} from "../src/core/state/state";
import {
  encounterRoster,
  openArrivalEncounter,
  runAbandoned,
} from "../src/core/state/encounter_verbs";
import {
  loadIceCatalog,
  loadMissionsCatalog,
  loadProgramsCatalog,
} from "../src/core/data_loaders";
import missionsData from "../src/data/missions.json";
import programsData from "../src/data/programs.json";
import iceData from "../src/data/ice_types.json";
import type {
  GameAction,
  GameState,
  Ice,
  Mission,
  Program,
} from "../src/core/types";

const MISSIONS = loadMissionsCatalog(missionsData);
const PROGRAMS = loadProgramsCatalog(programsData);
const ICE = loadIceCatalog(iceData);
const MISSION = MISSIONS[0] as Mission;
/** What `main.ts` hands `slotToGameState` as the fallback (first catalog ICE). */
const FALLBACK: Ice = Object.values(ICE)[0] as Ice;
/** main.ts loadDeck: the first five program ids, sorted. */
const DECK: Program[] = Object.keys(PROGRAMS)
  .sort()
  .slice(0, 5)
  .map((id) => ({ ...(PROGRAMS[id] as Program), id }));
const BOSS = 20;

type MissionIceFn = (
  mission: Mission,
  catalog: Readonly<Record<string, Ice>>,
) => Ice;
type RunEnd = {
  autosaveIntent: (state: GameState | null) => "write" | "retire" | "skip";
  runCompleted: (previous: GameState, next: GameState) => boolean;
  runFailed: (previous: GameState, next: GameState) => boolean;
};

const missionIce = async (): Promise<MissionIceFn> =>
  (
    (await import("../src/core/state/mission_ice")) as {
      missionIce: MissionIceFn;
    }
  ).missionIce;
const runEnd = async (): Promise<RunEnd> =>
  (await import("../src/core/state/run_end")) as RunEnd;

const act = (state: GameState, action: GameAction): GameState =>
  applyAction(state, action);
const key = (state: GameState, type: GameAction["type"]): GameState =>
  act(state, { type } as GameAction);

/** The run as `launchSelected` builds it. */
function launch(base: Ice): GameState {
  const initial = makeInitialState(MISSION, base, DECK);
  return openArrivalEncounter({
    ...initial,
    currentNodeIndex: 0,
    runPhase: "matrix",
    phase: "approach",
  });
}

function travel(state: GameState, to: number): GameState {
  let next = state;
  for (let i = 0; i < 8 && next.selectedMatrixNodeIndex !== to; i += 1)
    next = key(next, "move_south");
  expect(next.selectedMatrixNodeIndex).toBe(to);
  return key(next, "confirm");
}

function choose(state: GameState, verb: string): GameState {
  let next = state;
  for (
    let i = 0;
    i < 6 && next.encounterDecision?.selectedVerb !== verb;
    i += 1
  )
    next = key(next, "move_south");
  expect(next.encounterDecision?.selectedVerb).toBe(verb);
  return key(next, "confirm");
}

/** BREACH, engage, then win: every ICE is left on 1 HP and the hand is
 * played through the real reducer until the run boundary (`loot`). */
function win(state: GameState): GameState {
  let next = key(choose(state, "BREACH"), "confirm");
  expect(next.phase).toBe("combat");
  for (let i = 0; i < 40 && next.runPhase === "combat"; i += 1) {
    next = {
      ...next,
      iceRoster: next.iceRoster.map((ice) => ({
        ...ice,
        hp: Math.min(ice.hp, 1),
      })),
    };
    const program = next.deck[0];
    if (!program) break;
    next = act(next, { type: "use_program", programId: program.id });
  }
  expect(next.runPhase).toBe("loot");
  return next;
}

/** Walk the owner's route; `stop` returns the state at that point. */
function walk(
  base: Ice,
  stop: "boss-arrival" | "boss-loot",
): { live: GameState; before18: GameState } {
  let s = launch(base);
  s = travel(s, 25);
  s = travel(s, 16);
  s = travel(s, 18);
  const before18 = s;
  s = key(win(s), "confirm"); // loot → route selection (+15% heal)
  s = travel(s, BOSS);
  expect(s.encounterDecision).not.toBeNull();
  if (stop === "boss-arrival") return { live: s, before18 };
  return { live: win(s), before18 };
}

describe("ADR-0252 A — the save reflects committed state", () => {
  it("a committed move is in the slot written from the post-move state", () => {
    const moved = travel(launch(FALLBACK), 25);
    expect(moved.currentNodeIndex).toBe(25);
    expect(stateToSaveSlot(moved).currentNodeIndex).toBe(25);
  });

  it("a combat win is in the slot written from the loot state (cleared node, hp, credits)", () => {
    const { live } = walk(FALLBACK, "boss-loot");
    const slot = stateToSaveSlot(live);
    expect(live.runPhase).toBe("loot");
    expect(slot.clearedEncounterNodes).toEqual([18, BOSS]);
    expect(slot.playerHp).toBe(live.player.hp);
    expect(slot.playerCredits).toBe(live.player.credits);
  });

  it("the controller writes the slot on Matrix, loot and combat frames", async () => {
    const { autosaveIntent } = await runEnd();
    const { live, before18 } = walk(FALLBACK, "boss-loot");
    expect(autosaveIntent(travel(launch(FALLBACK), 25))).toBe("write");
    expect(autosaveIntent(before18)).toBe("write");
    expect(autosaveIntent(live)).toBe("write");
    expect(
      autosaveIntent({ ...live, runPhase: "combat", phase: "combat" }),
    ).toBe("write");
    expect(autosaveIntent(null)).toBe("skip");
  });
});

describe("ADR-0252 B — the ending ends the run", () => {
  it("the controller retires the slot once the run reaches its ending", async () => {
    const { autosaveIntent } = await runEnd();
    const ending = key(walk(FALLBACK, "boss-loot").live, "confirm");
    expect(ending.runPhase).toBe("ending");
    expect(autosaveIntent(ending)).toBe("retire");
  });

  it("confirm and ESC on the ending complete the run; nothing else does", async () => {
    const { runCompleted } = await runEnd();
    const loot = walk(FALLBACK, "boss-loot").live;
    const ending = key(loot, "confirm");
    expect(runCompleted(ending, key(ending, "confirm"))).toBe(true);
    expect(runCompleted(ending, key(ending, "jack_out"))).toBe(true);
    for (const type of [
      "move_north",
      "move_south",
      "move_west",
      "move_east",
    ] as const) {
      expect(runCompleted(ending, key(ending, type))).toBe(false);
    }
    // The loot confirm that *enters* the ending is not the completion.
    expect(runCompleted(loot, ending)).toBe(false);
    // Matrix JACK OUT stays an abandonment, not a completion.
    const board = launch(FALLBACK);
    expect(runCompleted(board, key(board, "jack_out"))).toBe(false);
    expect(runAbandoned(ending, key(ending, "confirm"))).toBe(false);
  });

  it("a slot written on the boss loot screen restores to that loot screen, and Enter ends the run", () => {
    const loot = walk(FALLBACK, "boss-loot").live;
    const restored = slotToGameState(
      stateToSaveSlot(loot),
      MISSIONS,
      PROGRAMS,
      FALLBACK,
    );
    expect(restored).not.toBeNull();
    const r = restored as GameState;
    expect(r.runPhase).toBe("loot");
    expect(r.encounterDecision ?? null).toBeNull();
    const ended = key(r, "confirm");
    expect(ended.runPhase).toBe("ending");
    expect(ended.endingChoice).not.toBeNull();
  });

  it("a slot written on a non-terminal loot screen restores onto the board (node resolved)", () => {
    const { before18 } = walk(FALLBACK, "boss-arrival");
    const loot18 = win(before18);
    const r = slotToGameState(
      stateToSaveSlot(loot18),
      MISSIONS,
      PROGRAMS,
      FALLBACK,
    ) as GameState;
    expect(r.runPhase).toBe("matrix");
    expect(r.currentNodeIndex).toBe(18);
    expect(r.encounterDecision ?? null).toBeNull();
  });
});

describe("ADR-0250 holds — a load cannot dodge an unresolved ICE", () => {
  it("a slot written at the boss before it falls reopens the boss decision; BYPASS stays blocked", () => {
    const { live } = walk(FALLBACK, "boss-arrival");
    const fighting = key(choose(live, "BREACH"), "confirm");
    expect(fighting.phase).toBe("combat");
    const r = slotToGameState(
      stateToSaveSlot(fighting),
      MISSIONS,
      PROGRAMS,
      FALLBACK,
    ) as GameState;
    expect(r.runPhase).toBe("matrix");
    expect(r.currentNodeIndex).toBe(BOSS);
    expect(r.encounterDecision).toEqual({ selectedVerb: null, probed: false });
    const bypass = choose(r, "BYPASS");
    expect(bypass.currentNodeIndex).toBe(BOSS);
    expect(bypass.encounterDecision).not.toBeNull();
    expect(bypass.bypassedEncounterNodes ?? []).not.toContain(BOSS);
    expect(bypass.player.alarm).toBe(r.player.alarm);
  });

  it("a mid-fight slot at a non-terminal ICE reopens its decision, not the loot screen", () => {
    const { before18 } = walk(FALLBACK, "boss-arrival");
    const fighting = key(choose(before18, "BREACH"), "confirm");
    const r = slotToGameState(
      stateToSaveSlot(fighting),
      MISSIONS,
      PROGRAMS,
      FALLBACK,
    ) as GameState;
    expect(r.runPhase).toBe("matrix");
    expect(r.encounterDecision).toEqual({ selectedVerb: null, probed: false });
  });
});

describe("ADR-0252 C — CONTINUE rebuilds the same fight", () => {
  it("the restored boss roster uses the mission ICE, as the live fight does (ADR-0280: the apex of the grade)", () => {
    const { live } = walk(FALLBACK, "boss-arrival");
    const restored = slotToGameState(
      stateToSaveSlot(live),
      MISSIONS,
      PROGRAMS,
      FALLBACK,
      ICE,
    ) as GameState;
    const restoredRoster = encounterRoster(restored);
    expect(restoredRoster.map((i) => `${i.id}:${i.hp}`)).toEqual([
      "neuromancer:165",
    ]);
  });

  it("the restored roster deep-equals the live one when the run starts from the mission ICE", async () => {
    const base = (await missionIce())(MISSION, ICE);
    const { live } = walk(base, "boss-arrival");
    const restored = slotToGameState(
      stateToSaveSlot(live),
      MISSIONS,
      PROGRAMS,
      FALLBACK,
      ICE,
    ) as GameState;
    expect(encounterRoster(restored)).toEqual(encounterRoster(live));
    expect(restored.ice.name).toBe(live.ice.name);
  });

  it("an old caller without the catalog still restores (fallback ICE, as before)", () => {
    const { live } = walk(FALLBACK, "boss-arrival");
    const restored = slotToGameState(
      stateToSaveSlot(live),
      MISSIONS,
      PROGRAMS,
      FALLBACK,
    ) as GameState;
    expect(restored.ice).toEqual(FALLBACK);
  });
});

describe("ADR-0252 B — what the player sees", () => {
  const LAYOUTS = [
    [80, 50],
    [60, 40],
    [40, 60],
  ] as const;
  const rows = (
    cells: ReadonlyArray<ReadonlyArray<{ char: string }>>,
  ): string[] => cells.map((r) => r.map((c) => c.char).join(""));

  it.each(LAYOUTS)(
    "the ending footer says where Enter goes (%ix%i)",
    async (cols, h) => {
      const { renderRunScreen } = await import("../src/renderer/run_screen");
      const ending = key(walk(FALLBACK, "boss-loot").live, "confirm");
      const view = renderRunScreen(ending, cols, h);
      const text = rows(view?.grid.cells ?? []);
      expect(text.some((l) => l.includes("ENTER / ESC: return to title"))).toBe(
        true,
      );
      expect(text.some((l) => l.includes("ESC: back"))).toBe(false);
    },
  );

  it.each(LAYOUTS)(
    "the title after a completed run offers no CONTINUE and says why (%ix%i)",
    async (cols, h) => {
      const { renderMainMenu } = await import("../src/renderer/menu_main");
      const { RUN_COMPLETE_MESSAGE } =
        (await import("../src/core/state/run_end")) as {
          RUN_COMPLETE_MESSAGE: string;
        };
      const text = rows(
        renderMainMenu(0, cols, h, false, null, RUN_COMPLETE_MESSAGE).cells,
      );
      expect(text.some((l) => /CONTINUE\s+\(no save\)/.test(l))).toBe(true);
      expect(text.some((l) => l.includes(RUN_COMPLETE_MESSAGE))).toBe(true);
      expect(text.some((l) => l.includes("→ aleph_fragment"))).toBe(false);
    },
  );
});

describe("ADR-0263 — the defeat screen is escapable", () => {
  /** The state a lost fight leaves: FLATLINE on the dead run phase. */
  const dead = (): GameState => {
    const live = walk(FALLBACK, "boss-loot").live;
    return {
      ...live,
      runPhase: "dead",
      phase: "defeat",
      player: { ...live.player, hp: 0 },
    };
  };

  it("confirm and ESC leave the defeat screen; nothing else does", async () => {
    const { runFailed } = await runEnd();
    const d = dead();
    // ENTER and ESC are the way out (both map to the same exit).
    expect(runFailed(d, key(d, "confirm"))).toBe(true);
    expect(runFailed(d, key(d, "jack_out"))).toBe(true);
    // The screen promised no other key, and no other key does anything.
    for (const type of [
      "move_north",
      "move_south",
      "move_east",
      "move_west",
      "cycle_target",
    ] as const) {
      expect(runFailed(d, key(d, type))).toBe(false);
    }
    // Death itself is not the exit — only leaving the screen is.
    const loot = walk(FALLBACK, "boss-loot").live;
    expect(runFailed(loot, d)).toBe(false);
  });

  it("keeps runPhase dead, so it cannot be confused with the ending", async () => {
    const d = dead();
    const after = key(d, "confirm");
    expect(after.phase).toBe("menu");
    expect(after.runPhase).toBe("dead");
    expect(after.lastDeathSummary).toBe(d.lastDeathSummary);
    // The ending keeps its own completion path.
    const ending = key(walk(FALLBACK, "boss-loot").live, "confirm");
    expect(ending.runPhase).toBe("ending");
    expect(key(ending, "confirm").phase).toBe("menu");
  });

  it("retires the slot on death, so a flatline is not a resumable run (ADR-0264)", async () => {
    const { autosaveIntent } = await runEnd();
    expect(autosaveIntent(dead())).toBe("retire");
    // Still alive == still written; the sliver between the two is the run.
    expect(
      autosaveIntent({ ...dead(), runPhase: "combat", phase: "combat" }),
    ).toBe("write");
  });

  it("main.ts turns that exit into the title, and the screen states the key", () => {
    const mainSource = readFileSync(
      fileURLToPath(new URL("../src/main.ts", import.meta.url)),
      "utf-8",
    ).replace(/\s+/g, "");
    expect(mainSource).toContain("runFailed(previous,this.state)");
    expect(mainSource).toContain("this._message=FLATLINE_MESSAGE;");

    const gridSource = readFileSync(
      fileURLToPath(new URL("../src/renderer/combat_grid.ts", import.meta.url)),
      "utf-8",
    );
    expect(gridSource).toContain("ENTER / ESC: return to title");
  });
});
