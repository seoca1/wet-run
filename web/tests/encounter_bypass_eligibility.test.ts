import { describe, expect, it } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state/state";
import type { GameState, MatrixNode } from "../src/core/types";
import { renderRunScreen } from "../src/renderer/run_screen";

function atEncounter(terminal: "boss" | "isolated"): GameState {
  const initial = makeInitialState(
    {
      id: "bypass-eligibility",
      title: "Breach required",
      fixer: "test",
      zone: "surface",
      arc: 1,
      grade_min: 1,
      grade_max: 1,
      rewards: { credits: 0, materials: {} },
    },
    { id: "watchdog", name: "Watchdog", hp: 1, armor: 0, tier: 1 },
    [
      {
        id: "strike",
        name: "Strike",
        tier: 1,
        cost: 0,
        effect: "damage",
        description: "",
        aoe: false,
      },
    ],
  );
  const encounter: MatrixNode = {
    id: 1,
    zone: "mid",
    iceIds: ["watchdog"],
    iceHp: [1],
    reward: { credits: 75 },
    isBoss: terminal === "boss",
    adjacent: terminal === "boss" ? [0] : [],
  };
  return {
    ...initial,
    currentNodeIndex: 1,
    matrix: {
      startNode: 0,
      bossNode: 1,
      nodes: [
        {
          ...encounter,
          id: 0,
          iceIds: [],
          iceHp: [],
          isBoss: false,
          adjacent: [1],
        },
        encounter,
      ],
    },
  };
}

function select(
  state: GameState,
  selectedVerb: "PROBE" | "BYPASS" | "BREACH" | "JACK OUT",
): GameState {
  return { ...state, encounterDecision: { selectedVerb, probed: false } };
}

describe.each(["boss", "isolated"] as const)(
  "BYPASS at a %s encounter",
  (terminal) => {
    it("rejects a directly selected BYPASS without passage, clearing or payment", () => {
      // Given: select directly so hiding or skipping the UI entry cannot pass this test.
      const initial = select(atEncounter(terminal), "BYPASS");
      // When
      const rejected = applyAction(initial, { type: "confirm" });
      // Then
      expect(rejected.encounterDecision).toEqual(initial.encounterDecision);
      expect(rejected.bypassedEncounterNodeIndex).toBe(
        initial.bypassedEncounterNodeIndex,
      );
      expect(rejected.clearedEncounterNodes).toEqual(
        initial.clearedEncounterNodes,
      );
      expect(rejected.player).toEqual(initial.player);
      expect(rejected.inventory).toEqual(initial.inventory);
      expect(rejected.runPhase).toBe("matrix");
      expect(rejected.message).toMatch(/breach/i);
    });

    it.each([
      [80, 50],
      [60, 40],
      [40, 60],
    ])("explains the blocked verb before choosing at %s×%s", (cols, rows) => {
      // Given
      const decision = applyAction(atEncounter(terminal), { type: "confirm" });
      // When
      const view = renderRunScreen(decision, cols, rows);
      const lines =
        view?.grid.cells.map((row) => row.map((cell) => cell.char).join("")) ??
        [];
      // Then
      expect(lines.find((line) => line.includes("BYPASS"))).toContain(
        "BLOCKED",
      );
      expect(lines.join("\n")).toMatch(/Must BREACH/);
      for (const verb of ["PROBE", "BREACH", "JACK OUT"])
        expect(lines.join("\n")).toContain(verb);
    });

    it("still permits paid PROBE", () => {
      // Given
      const initial = select(atEncounter(terminal), "PROBE");
      // When
      const probed = applyAction(initial, { type: "confirm" });
      // Then
      expect(probed.encounterDecision?.probed).toBe(true);
      expect(probed.player.alarm).toBe(initial.player.alarm + 8);
    });

    it("still permits JACK OUT without loot", () => {
      // Given
      const initial = select(atEncounter(terminal), "JACK OUT");
      // When
      const exited = applyAction(initial, { type: "confirm" });
      // Then
      expect(exited.phase).toBe("menu");
      expect(exited.inventory).toEqual(initial.inventory);
    });

    it("remains reachable and completes the run through BREACH and real combat", () => {
      // Given: navigate to the boss from its neighbour; isolated nodes have no arrival edge.
      const initial = atEncounter(terminal);
      const arrived =
        terminal === "boss"
          ? applyAction(
              applyAction(
                { ...initial, currentNodeIndex: 0 },
                { type: "move_south" },
              ),
              { type: "confirm" },
            )
          : initial;
      expect(arrived.currentNodeIndex).toBe(1);
      const decision = applyAction(arrived, { type: "confirm" });
      const selected = applyAction(
        applyAction(applyAction(decision, { type: "move_south" }), {
          type: "move_south",
        }),
        { type: "move_south" },
      );
      // When
      const breach = applyAction(selected, { type: "confirm" });
      const fighting = applyAction(breach, { type: "confirm" });
      const won = applyAction(fighting, {
        type: "use_program",
        programId: "strike",
      });
      const completed = applyAction(won, { type: "confirm" });
      // Then
      expect(breach.phase).toBe("approach");
      expect(breach.runPhase).toBe("combat");
      expect(breach.bossPhase).toBe(terminal === "boss" ? 1 : 0);
      expect(won.runPhase).toBe("loot");
      expect(won.clearedEncounterNodes).toContain(1);
      expect(completed.runPhase).toBe("ending");
    });
  },
);
