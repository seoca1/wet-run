import { describe, expect, it } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { nextHopToward } from "../src/core/dungeon/matrix_navigation";
import { generateProceduralMatrix } from "../src/core/dungeon/matrix";
import { renderMatrix } from "../src/renderer/matrix";
import { renderRunScreen } from "../src/renderer/run_screen";
import type { GameState, Matrix, MatrixNode } from "../src/core/types";
import { breachEncounter } from "./encounter_test_helpers";

function node(id: number, adjacent: readonly number[]): MatrixNode {
  return {
    id,
    adjacent,
    zone: "surface",
    iceIds: [],
    iceHp: [],
    reward: { credits: 0 },
    isBoss: id === 3,
  };
}

const matrix: Matrix = {
  nodes: [node(0, [1, 2]), node(1, [0, 3]), node(2, [0]), node(3, [1])],
  startNode: 0,
  bossNode: 3,
};

function stateAtStart(): GameState {
  return {
    ...makeInitialState(
      {
        id: "route",
        title: "Route",
        fixer: "test",
        arc: 1,
        grade_min: 1,
        grade_max: 1,
        zone: "surface",
        rewards: { credits: 0, materials: {} },
      },
      { id: "watchdog", name: "Watchdog", hp: 50, armor: 0, tier: 1 },
      [],
    ),
    matrix,
    currentNodeIndex: 0,
  };
}

describe("explicit matrix routes (ADR-0246 first slice)", () => {
  it("takes either neighbouring offer from the same generated seed", () => {
    // Given
    const generated = generateProceduralMatrix(3, 42);
    const branch = generated.nodes.findIndex((n) => n.adjacent.length > 1);
    const neighbours = generated.nodes[branch]?.adjacent ?? [];
    expect(neighbours.length).toBeGreaterThan(1);
    const initial: GameState = {
      ...stateAtStart(),
      matrix: generated,
      currentNodeIndex: branch,
    };
    const destinations = [];
    // When
    for (const [slot, neighbour] of neighbours.entries()) {
      let selected = initial;
      for (let i = 0; i <= slot; i += 1) {
        selected = applyAction(selected, { type: "move_south" });
      }
      const arrived = applyAction(selected, { type: "confirm" });
      destinations.push(arrived.currentNodeIndex);
      // Then
      expect(arrived.currentNodeIndex).toBe(neighbour);
      expect(generated.nodes[arrived.currentNodeIndex]?.reward.credits).toBe(
        50 + neighbour * 25,
      );
    }
    expect(new Set(destinations).size).toBe(neighbours.length);
  });

  it("renders the selected frontier entry through the live run screen", () => {
    // Given
    const initial = stateAtStart();
    // When
    const selected = applyAction(initial, { type: "move_south" });
    const screen = renderRunScreen(selected, 80, 50);
    const text = screen?.grid.cells
      .map((row) => row.map((cell) => cell.char).join(""))
      .join("\n");
    // Then
    expect(text).toContain("> ⚔ N02 SURFACE");
    expect(text).toContain("ENTER: travel");
    expect(selected.currentNodeIndex).toBe(0);
  });

  it("travels to a selected side branch instead of the BFS hop", () => {
    // Given: node 2 is a side branch, not the shortest path to the boss.
    const initial = stateAtStart();
    expect(nextHopToward(matrix, 0, 3)).toBe(1);
    // When: highlight the second neighbour, then confirm travel.
    const first = applyAction(initial, { type: "move_south" });
    const selected = applyAction(first, { type: "move_south" });
    const arrived = applyAction(selected, { type: "confirm" });
    // Then: arrows did not move; confirm used the actual chosen neighbour.
    expect(first.currentNodeIndex).toBe(0);
    expect(selected.currentNodeIndex).toBe(0);
    expect(selected.turnCount).toBe(initial.turnCount);
    expect(arrived.currentNodeIndex).toBe(2);
    expect(arrived.runPhase).toBe("matrix");
    expect(arrived.selectedMatrixNodeIndex).toBeNull();
    expect(arrived.turnCount).toBe(initial.turnCount + 1);
  });

  it("returns from a side branch through an explicitly selected visited neighbour", () => {
    // Given: a leaf whose only exit is the already visited entry.
    const state = {
      ...stateAtStart(),
      currentNodeIndex: 2,
      visitedNodes: [0, 2],
    };
    // When: select retreat and confirm.
    const selected = applyAction(state, { type: "move_north" });
    const arrived = applyAction(selected, { type: "confirm" });
    // Then: retreat is a choice, not an automatic path toward start.
    expect(selected.currentNodeIndex).toBe(2);
    expect(arrived.currentNodeIndex).toBe(0);
    expect(nextHopToward(matrix, arrived.currentNodeIndex, 3)).toBe(1);
  });

  it("keeps the current position and clears destination selection after loot confirm", () => {
    // Given: loot on a non-boss node with a stale destination highlight.
    const state: GameState = {
      ...stateAtStart(),
      runPhase: "loot",
      selectedMatrixNodeIndex: 1,
      player: { ...stateAtStart().player, hp: 50 },
    };
    // When
    const result = applyAction(state, { type: "confirm" });
    // Then: existing heal still applies, but no next node is selected or visited.
    expect(result.runPhase).toBe("matrix");
    expect(result.currentNodeIndex).toBe(0);
    expect(result.selectedMatrixNodeIndex).toBeNull();
    expect(result.visitedNodes).toEqual([0]);
    expect(result.player.hp).toBe(65);
  });

  it.each([1, 12])(
    "cannot farm a cleared encounter by confirming again after loot (ICE HP %s)",
    (hp) => {
      // Given: travel marks the node visited BEFORE its encounter is cleared.
      const initial = stateAtStart();
      const atEntry: GameState = {
        ...initial,
        matrix: {
          ...matrix,
          nodes: matrix.nodes.map((n) =>
            n.id === 1
              ? {
                  ...n,
                  iceIds: ["watchdog"],
                  iceHp: [hp],
                  reward: { credits: 75 },
                }
              : n,
          ),
        },
        deck: [
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
      };
      const arrived = applyAction(
        applyAction(atEntry, { type: "move_south" }),
        { type: "confirm" },
      );
      expect(arrived.visitedNodes).toContain(1);
      const encounter = breachEncounter(arrived);
      expect(encounter.runPhase).toBe("combat");
      const fighting = applyAction(encounter, { type: "confirm" });
      const cleared = applyAction(fighting, {
        type: "use_program",
        programId: "strike",
      });
      expect(cleared.runPhase).toBe("loot");
      expect(cleared.player.credits).toBeGreaterThan(arrived.player.credits);
      const afterLoot = applyAction(cleared, { type: "confirm" });
      expect(afterLoot.currentNodeIndex).toBe(1);
      expect(afterLoot.runPhase).toBe("matrix");
      // When: repeat the exploit's confirm/confirm/program sequence.
      const confirmed = applyAction(afterLoot, { type: "confirm" });
      const retried = applyAction(applyAction(confirmed, { type: "confirm" }), {
        type: "use_program",
        programId: "strike",
      });
      // Then: neither a new encounter nor any reward can be obtained.
      expect(confirmed.runPhase).not.toBe("combat");
      expect(retried.runPhase).toBe("matrix");
      expect(retried.player.credits).toBe(cleared.player.credits);
      expect(retried.inventory).toEqual(cleared.inventory);
    },
  );

  it.each([
    [80, 50],
    [60, 40],
    [40, 60],
  ])(
    "shows every frontier offer before travel on %s×%s, including late and visited nodes",
    (cols, rows) => {
      // Given: the frontier is beyond the old list's visible range (no geometry).
      const nodes = Array.from({ length: 30 }, (_, i) => node(i, []));
      nodes[0] = node(0, [28, 29]);
      nodes[28] = {
        ...node(28, [0]),
        zone: "deep",
        iceIds: ["a", "b"],
        reward: { credits: 321 },
        eventKind: "trap",
      };
      nodes[29] = {
        ...node(29, [0]),
        zone: "mid",
        reward: { credits: 654 },
        eventKind: "cache",
      };
      // When: no target yet, then each offer targeted with the arrows' state.
      const text = (selected: number | null): string =>
        renderMatrix({ ...matrix, nodes }, 0, [29], cols, rows, null, selected)
          .cells.map((row) => row.map((cell) => cell.char).join(""))
          .join("\n");
      // Then: ADR-0249 — the card names both offers up front and details the
      // targeted one (zone, ICE presence/count, credits, event) before travel.
      expect(text(null)).toContain("ROUTES (2): N29 N30");
      expect(text(28)).toContain("> ✦ N29 DEEP");
      expect(text(28)).toContain("2 ICE · 321cr · TRAP");
      expect(text(28)).toContain("ROUTES (2): >N29 N30");
      // ◆ is reserved for the boss on the Matrix screen; a cache reads ¤.
      expect(text(29)).toContain("> ¤ N30 MID · SEEN");
      expect(text(29)).toContain("0 ICE · 654cr · CACHE");
    },
  );
});
