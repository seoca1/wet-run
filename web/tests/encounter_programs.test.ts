import { describe, expect, it } from "vitest";
import { parseProgram } from "../src/core/data_loaders";
import { applyAction, makeInitialState } from "../src/core/state/state";
import type { GameState, Program } from "../src/core/types";
import programs from "../src/data/programs.json";
import { renderEncounterDecision } from "../src/renderer/encounter";

const strike = parseProgram(programs.strike, "strike");
const scan = parseProgram(programs.scan, "scan");

function encounter(hand: readonly Program[] = [strike, scan]): GameState {
  const initial = makeInitialState(
    {
      id: "program-encounter",
      title: "Program encounter",
      fixer: "test",
      zone: "surface",
      arc: 1,
      grade_min: 1,
      grade_max: 1,
      rewards: { credits: 0, materials: {} },
    },
    { id: "watchdog", name: "Watchdog", hp: 50, armor: 0, tier: 1 },
    hand,
  );
  return applyAction(
    {
      ...initial,
      currentNodeIndex: 0,
      unlockedAchievements: ["first_blood"],
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
    },
    { type: "confirm" },
  );
}

function useScan(state: GameState): GameState {
  return applyAction(applyAction(state, { type: "move_north" }), {
    type: "confirm",
  });
}

function fixed(state: GameState, index: number): GameState {
  let selected: GameState = {
    ...state,
    encounterDecision: {
      selectedVerb: null,
      probed: state.encounterDecision?.probed ?? false,
    },
  };
  for (let i = 0; i <= index; i += 1) {
    selected = applyAction(selected, { type: "move_south" });
  }
  return applyAction(selected, { type: "confirm" });
}

function text(state: GameState, cols = 80, rows = 50): string {
  return renderEncounterDecision(state, cols, rows)
    .grid.cells.map((row) => row.map((cell) => cell.char).join(""))
    .join("\n");
}

describe("program-funded encounter intel (ADR-0247 E first slice)", () => {
  it.each(Object.entries(programs).filter(([, p]) => p.role === "utility"))(
    "grants SCAN from the real catalog utility program %s at its authored tier",
    (id, raw) => {
      // Given
      const card = parseProgram(raw, id);
      const decision = encounter([card]);
      // When
      const result = useScan(decision);
      // Then
      expect(result.encounterDecision?.probed).toBe(true);
      expect(result.deck).toEqual([]);
      expect(result.discardPile).toEqual([card]);
      expect(result.player.alarm).toBe(decision.player.alarm);
    },
  );

  it.each(["strike", "hammer", "shield", "heal"] as const)(
    "does not grant SCAN for the catalog role of %s",
    (id) => {
      // Given
      const decision = encounter([parseProgram(programs[id], id)]);
      // When
      const result = useScan(decision);
      // Then
      expect(result.encounterDecision?.probed).toBe(false);
      expect(result.deck).toEqual(decision.deck);
      expect(result.discardPile).toEqual([]);
      expect(text(result)).toContain("NO UTILITY IN HAND");
      for (const verb of ["PROBE", "BYPASS", "BREACH", "JACK OUT"])
        expect(text(result)).toContain(verb);
    },
  );

  it("does not grant an option from draw, discard or inventory ownership", () => {
    // Given
    const base = encounter([strike]);
    const decision = {
      ...base,
      drawPile: [scan],
      discardPile: [scan],
      inventory: { ...base.inventory, programs: [scan] },
    };
    // When
    const result = useScan(decision);
    // Then
    expect(result.encounterDecision?.probed).toBe(false);
    expect(text(result)).toContain("NO UTILITY IN HAND");
    expect(result.drawPile).toEqual([scan]);
    expect(result.discardPile).toEqual([scan]);
  });

  it.each([
    [40, 60],
    [60, 40],
    [80, 50],
  ])(
    "shows payment, unavailable state and full threat within the %s×%s frame",
    (cols, rows) => {
      // Given
      const decision = encounter();
      const hidden = text(decision, cols, rows);
      // When
      const result = useScan(decision);
      const revealed = text(result, cols, rows);
      // Then
      expect(hidden).toContain("SCAN");
      expect(hidden).toContain("Discard Scan (T1)");
      expect(hidden).not.toContain("watchdog HP");
      expect(revealed).toContain("watchdog HP 1/1");
      expect(revealed).toContain("ENTER/SPACE: act");
      expect(revealed).toContain("PROBE REVEALED");
      expect(text(encounter([strike]), cols, rows)).toContain(
        "NO UTILITY IN HAND",
      );
    },
  );

  it("discards exactly the named first matching card without replacing it or advancing combat", () => {
    // Given
    const second = parseProgram(programs.trace, "trace");
    const decision = encounter([strike, scan, second, scan]);
    // When
    const result = useScan(decision);
    // Then
    expect(result.deck).toEqual([strike, second, scan]);
    expect(result.discardPile).toEqual([scan]);
    expect(result.drawPile).toEqual(decision.drawPile);
    expect(result.player).toEqual(decision.player);
    expect(result.inventory).toEqual(decision.inventory);
    expect(result.iceRoster).toEqual(decision.iceRoster);
    expect(result.turnCount).toBe(decision.turnCount);
    expect(result.playerCombo).toBe(decision.playerCombo);
  });

  it("cannot reuse a spent program in the following combat", () => {
    // Given
    const scanned = useScan(encounter());
    const fighting = applyAction(fixed(scanned, 2), { type: "confirm" });
    // When
    const result = applyAction(fighting, {
      type: "use_program",
      programId: "scan",
    });
    // Then
    expect(fighting.deck).toEqual([strike]);
    expect(result.deck).toEqual([strike]);
    expect(result.discardPile).toEqual([scan]);
    expect(result.iceRoster).toEqual(fighting.iceRoster);
    expect(result.playerCombo).toBe(fighting.playerCombo);
  });

  it.each(["scan", "probe"] as const)(
    "does not consume another card after intel bought with %s",
    (source) => {
      // Given
      const decision = encounter([
        strike,
        scan,
        parseProgram(programs.trace, "trace"),
      ]);
      const revealed =
        source === "scan" ? useScan(decision) : fixed(decision, 0);
      const selected = {
        ...revealed,
        encounterDecision: { selectedVerb: null, probed: true },
      };
      // When
      const result = useScan(selected);
      // Then
      expect(result.deck).toEqual(revealed.deck);
      expect(result.discardPile).toEqual(revealed.discardPile);
      expect(result.player.alarm).toBe(revealed.player.alarm);
    },
  );

  it.each([
    [0, 8],
    [1, 60],
  ])(
    "preserves fixed verb %s and its COST with no matching program",
    (index, cost) => {
      // Given
      const decision = encounter([strike]);
      // When
      const result = fixed(decision, index);
      // Then
      expect(result.player.alarm).toBe(cost);
      expect(result.deck).toEqual([strike]);
      expect(result.discardPile).toEqual([]);
    },
  );

  it("permits program intel at the COST cap but does not grant free passage", () => {
    // Given
    const base = encounter();
    const decision = { ...base, player: { ...base.player, alarm: 100 } };
    // When
    const result = useScan(decision);
    // Then
    expect(result.encounterDecision?.probed).toBe(true);
    expect(result.player.alarm).toBe(100);
    expect(result.bypassedEncounterNodeIndex).not.toBe(0);
    expect(result.clearedEncounterNodes ?? []).not.toContain(0);
  });

  it("keeps no-farming after SCAN, BREACH, victory and loot", () => {
    // Given
    const scanned = useScan(encounter());
    const fighting = applyAction(fixed(scanned, 2), { type: "confirm" });
    const won = applyAction(fighting, {
      type: "use_program",
      programId: "strike",
    });
    const looted = applyAction(won, { type: "confirm" });
    // When
    const result = applyAction(looted, { type: "confirm" });
    // Then
    expect(won.clearedEncounterNodes).toContain(0);
    expect(result.runPhase).toBe("matrix");
    expect(result.encounterDecision).toBeNull();
    expect(result.player.credits).toBe(won.player.credits);
    expect(result.inventory).toEqual(won.inventory);
  });
});
