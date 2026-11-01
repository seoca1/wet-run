import { describe, expect, it } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { renderRunScreen } from "../src/renderer/run_screen";
import type { GameState } from "../src/core/types";

function onIce(): GameState {
  const initial = makeInitialState(
    {
      id: "verbs",
      title: "Verbs",
      fixer: "test",
      zone: "surface",
      arc: 1,
      grade_min: 1,
      grade_max: 1,
      rewards: { credits: 0, materials: {} },
    },
    { id: "watchdog", name: "Watchdog", hp: 50, armor: 0, tier: 1 },
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
  return {
    ...initial,
    currentNodeIndex: 0,
    matrix: {
      startNode: 0,
      bossNode: 1,
      nodes: [
        {
          id: 0,
          zone: "surface",
          iceIds: ["watchdog"],
          iceHp: [1],
          reward: { credits: 75 },
          adjacent: [1],
          isBoss: false,
        },
        {
          id: 1,
          zone: "mid",
          iceIds: [],
          iceHp: [],
          reward: { credits: 0 },
          adjacent: [0],
          isBoss: true,
        },
      ],
    },
  };
}

/** Real arrows + confirm, starting from an already opened decision. */
function choose(state: GameState, index: number): GameState {
  let selected = state;
  for (let i = 0; i <= index; i += 1) {
    selected = applyAction(selected, { type: "move_south" });
  }
  return applyAction(selected, { type: "confirm" });
}

function screenText(state: GameState, cols = 80, rows = 50): string {
  const screen = renderRunScreen(state, cols, rows);
  return [
    screen?.grid.cells
      .map((row) => row.map((cell) => cell.char).join(""))
      .join("\n"),
    screen?.hud.join("\n"),
  ].join("\n");
}

describe("fixed encounter verbs (ADR-0246 slice 2)", () => {
  it("does not leak exact HP through the matrix current-node preview before PROBE", () => {
    // Given
    const initial = onIce();
    // When
    const text = screenText(initial);
    // Then
    expect(text).not.toContain("HP:  1");
    expect(text).not.toContain("Watchdog");
    expect(text).toContain("1 ICE");
  });

  it.each([
    [0, 92],
    [1, 70],
  ])("accepts verb %s exactly at the existing COST ceiling", (verb, alarm) => {
    // Given
    const initial = onIce();
    const decision = applyAction(
      { ...initial, player: { ...initial.player, alarm } },
      { type: "confirm" },
    );
    // When
    const result = choose(decision, verb);
    // Then
    expect(result.player.alarm).toBe(100);
    expect(result.alarmLevel).toBe(initial.alarmLevel);
    expect(result.player.hp).toBe(initial.player.hp);
  });

  it("spends program headroom rather than a cosmetic counter when bypassing", () => {
    // Given
    const initial = onIce();
    const expensive = {
      ...initial.deck[0],
      id: "costly",
      name: "Costly",
      tier: 1,
      cost: 10,
      effect: "damage",
      description: "",
      aoe: false,
    };
    const costly = {
      ...initial,
      player: { ...initial.player, alarm: 70 },
      deck: [expensive],
    };
    const bypassed = choose(applyAction(costly, { type: "confirm" }), 1);
    const breach = choose(applyAction(bypassed, { type: "confirm" }), 2);
    const fighting = applyAction(breach, { type: "confirm" });
    // When
    const rejected = applyAction(fighting, {
      type: "use_program",
      programId: "costly",
    });
    // Then
    expect(rejected.player.alarm).toBe(100);
    expect(rejected.deck).toEqual(fighting.deck);
    expect(rejected.iceRoster).toEqual(fighting.iceRoster);
    expect(rejected.runPhase).toBe("combat");
  });

  it("reveals every mutator ICE copy with the same HP that BREACH will spawn", () => {
    // Given
    const initial: GameState = { ...onIce(), activeMutators: ["ice_x2"] };
    const probed = choose(applyAction(initial, { type: "confirm" }), 0);
    // When: from PROBE, two more arrows select BREACH.
    const breach = applyAction(
      applyAction(applyAction(probed, { type: "move_south" }), {
        type: "move_south",
      }),
      { type: "confirm" },
    );
    // Then
    expect(screenText(probed).match(/watchdog HP 1\/1/g)).toHaveLength(2);
    expect(breach.iceRoster.map((ice) => [ice.id, ice.hp])).toEqual([
      ["watchdog", 1],
      ["watchdog", 1],
    ]);
  });

  it("bypasses without combat, loot, healing or credits when COST is available", () => {
    // Given
    const initial = onIce();
    // When
    const result = choose(applyAction(initial, { type: "confirm" }), 1);
    // Then
    expect(result.runPhase).toBe("matrix");
    expect(result.player.alarm).toBe(initial.player.alarm + 30);
    expect(result.player.hp).toBe(initial.player.hp);
    expect(result.player.credits).toBe(initial.player.credits);
    expect(result.inventory).toEqual(initial.inventory);
    expect(result.currentNodeIndex).toBe(0);
    expect(result.clearedEncounterNodes ?? []).not.toContain(0);
  });

  it.each([
    [80, 50],
    [60, 40],
    [40, 60],
  ])(
    "reveals exact ICE identity and HP only after paid PROBE on %s×%s",
    (cols, rows) => {
      // Given
      const decision = applyAction(onIce(), { type: "confirm" });
      expect(screenText(decision, cols, rows)).not.toContain("watchdog");
      // When
      const probed = choose(decision, 0);
      // Then
      expect(probed.runPhase).toBe("matrix");
      expect(probed.player.alarm).toBe(8);
      expect(screenText(probed, cols, rows)).toContain("watchdog");
      expect(screenText(probed, cols, rows)).toContain("HP 1/1");
      for (const verb of ["PROBE", "BYPASS", "BREACH", "JACK OUT"]) {
        expect(screenText(probed, cols, rows)).toContain(verb);
      }
    },
  );

  it("does not silently engage when confirm is repeated without selecting a verb", () => {
    // Given
    const decision = applyAction(onIce(), { type: "confirm" });
    // When
    const result = applyAction(decision, { type: "confirm" });
    // Then
    expect(result.runPhase).toBe("matrix");
    expect(result.player.alarm).toBe(0);
  });

  it("breaches through the existing approach and combat reward flow", () => {
    // Given
    const initial = onIce();
    // When
    const breach = choose(applyAction(initial, { type: "confirm" }), 2);
    const fighting = applyAction(breach, { type: "confirm" });
    const won = applyAction(fighting, {
      type: "use_program",
      programId: "strike",
    });
    // Then
    expect(breach.runPhase).toBe("combat");
    expect(breach.phase).toBe("approach");
    expect(breach.player.alarm).toBe(0);
    expect(fighting.phase).toBe("combat");
    expect(won.runPhase).toBe("loot");
    expect(won.player.credits - initial.player.credits).toBe(125);
    expect(won.clearedEncounterNodes).toContain(0);
  });

  it("can return to a bypassed uncleared node and Breach for its full reward", () => {
    // Given: bypass, leave, then explicitly return.
    const initial = onIce();
    const bypassed = choose(applyAction(initial, { type: "confirm" }), 1);
    const away = applyAction(applyAction(bypassed, { type: "move_south" }), {
      type: "confirm",
    });
    const returned = applyAction(applyAction(away, { type: "move_south" }), {
      type: "confirm",
    });
    expect(away.currentNodeIndex).toBe(1);
    expect(returned.currentNodeIndex).toBe(0);
    expect(returned.clearedEncounterNodes ?? []).not.toContain(0);
    // When
    const breach = choose(applyAction(returned, { type: "confirm" }), 2);
    const won = applyAction(applyAction(breach, { type: "confirm" }), {
      type: "use_program",
      programId: "strike",
    });
    // Then
    expect(won.runPhase).toBe("loot");
    expect(won.player.credits - initial.player.credits).toBe(125);
    expect(won.player.alarm).toBe(30);
  });

  it("cannot avoid paying BYPASS by selecting an outgoing route first", () => {
    // Given
    const initial = onIce();
    // When
    const attempted = applyAction(
      applyAction(initial, { type: "move_south" }),
      { type: "confirm" },
    );
    // Then
    expect(attempted.currentNodeIndex).toBe(0);
    expect(screenText(attempted)).toContain("BYPASS");
  });

  it.each([
    [0, 93],
    [1, 71],
  ])(
    "rejects unaffordable verb %s instead of capping away its price",
    (verb, alarm) => {
      // Given
      const initial = onIce();
      const costly = { ...initial, player: { ...initial.player, alarm } };
      // When
      const result = choose(applyAction(costly, { type: "confirm" }), verb);
      // Then
      expect(result.runPhase).toBe("matrix");
      expect(result.player.alarm).toBe(alarm);
      expect(screenText(result)).toContain("BLOCKED");
    },
  );

  it("does not recharge an already revealed probe", () => {
    // Given
    const probed = choose(applyAction(onIce(), { type: "confirm" }), 0);
    // When: the selected PROBE remains highlighted.
    const repeated = applyAction(probed, { type: "confirm" });
    // Then
    expect(repeated.player.alarm).toBe(8);
  });

  it("cannot farm an encounter after Breach and loot confirmation", () => {
    // Given
    const breach = choose(applyAction(onIce(), { type: "confirm" }), 2);
    const won = applyAction(applyAction(breach, { type: "confirm" }), {
      type: "use_program",
      programId: "strike",
    });
    const looted = applyAction(won, { type: "confirm" });
    // When
    const repeated = choose(applyAction(looted, { type: "confirm" }), 2);
    // Then
    expect(repeated.runPhase).toBe("matrix");
    expect(repeated.player.credits).toBe(won.player.credits);
    expect(repeated.inventory).toEqual(won.inventory);
  });

  it("abandons the run through JACK OUT without awarding loot", () => {
    // Given
    const initial = onIce();
    // When
    const result = choose(applyAction(initial, { type: "confirm" }), 3);
    // Then
    expect(result.phase).toBe("menu");
    expect(result.player.credits).toBe(initial.player.credits);
  });
});
