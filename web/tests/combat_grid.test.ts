/** Combat grid integration — per-target status glyph placement (proposal P14).
 *
 * `renderGrid` used to live inside `main.ts` (untestable: the module
 * self-boots a canvas). It now lives in `renderer/combat_grid.ts` so the
 * status placement can be asserted on the real grid.
 */
import { describe, it, expect } from "vitest";
import { renderGrid } from "../src/renderer/combat_grid";
import { groupStatusByTarget } from "../src/renderer/status_hud";
import { PALETTE } from "../src/renderer/palette";
import { makeInitialState } from "../src/core/state/state";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

const MOCK_MISSION: Mission = {
  id: "test",
  title: "Test",
  fixer: "test",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 10, materials: {} },
};

const MOCK_PROGRAM: Program = {
  id: "p1",
  name: "Atk",
  tier: 1,
  cost: 0,
  effect: "damage",
  description: "test",
  aoe: false,
};

function makeIce(name: string): Ice {
  return {
    id: name,
    name,
    tier: 2,
    hp: 50,
    maxHp: 50,
    armor: 0,
    personality: "aggressive",
    aggression: "standard",
  };
}

function makeState(overrides: Partial<GameState> = {}): GameState {
  const ice = makeIce("Caster");
  const state = makeInitialState(MOCK_MISSION, ice, [MOCK_PROGRAM]);
  return {
    ...state,
    iceRoster: [ice],
    activeIceIndex: 0,
    phase: "combat",
    runPhase: "combat",
    ...overrides,
  };
}

/** Fifth inner row of the inset combat frame (frame top rail on row 1). */
const PLAYER_HP_ROW = 6;

function rowText(grid: ReturnType<typeof renderGrid>, row: number): string {
  let out = "";
  for (let x = 0; x < grid.width; x++) {
    out += grid.cells[row]?.[x]?.char ?? " ";
  }
  return out;
}

describe("combat grid ICE HP display", () => {
  it.each([
    [165, "[████████████] 165/165", PALETTE.GREEN_NEON],
    [82.5, "[██████░░░░░░] 82.5/165", PALETTE.YELLOW_AMBER],
  ])("uses the scaled maximum when ICE HP is %s", (hp, text, color) => {
    // Given a grade-scaled ICE at full or half HP.
    const ice = { ...makeIce("Scaled"), hp, maxHp: 165 };
    const state = makeState({ iceRoster: [ice] });

    // When the real combat grid is rendered.
    const grid = renderGrid(state);

    // Then text, bar fill and color all use the ICE's own maximum.
    const hpRow = Math.floor(grid.height * 0.44) + 2;
    expect(rowText(grid, hpRow)).toContain(text);
    expect(rowText(grid, hpRow)).not.toContain(`${hp}/100`);
    expect(grid.get(Math.floor(grid.width * 0.45), hpRow)?.fg).toBe(color);
  });

  it.each([undefined, 0, -1, NaN, Infinity])(
    "falls back to a legacy maximum when maxHp is %s",
    (maxHp) => {
      // Given a legacy or invalid maximum.
      const ice = { ...makeIce("Legacy"), hp: 50, maxHp };
      const state = makeState({ iceRoster: [ice] });

      // When the combat grid is rendered.
      const grid = renderGrid(state);

      // Then all HP display consumers use the same positive fallback.
      const hpRow = Math.floor(grid.height * 0.44) + 2;
      expect(rowText(grid, hpRow)).toContain("[██████░░░░░░] 50/100");
      expect(grid.get(Math.floor(grid.width * 0.45), hpRow)?.fg).toBe(
        PALETTE.YELLOW_AMBER,
      );
    },
  );
});

describe("combat grid status glyph placement (P14)", () => {
  it("draws the player's own effect on the player HP row", () => {
    const state = makeState({
      statusEffects: [
        {
          kind: "burn",
          remaining: 2,
          magnitude: 3,
          target: "player",
        },
      ],
    });

    const grid = renderGrid(state, null, null, [], 80, 50);
    const groups = groupStatusByTarget(
      state.statusEffects,
      state.activeIceIndex,
    );
    const withStatus = renderGrid(state, null, null, groups, 80, 50);

    expect(rowText(grid, PLAYER_HP_ROW)).not.toContain("[B2]");
    expect(rowText(withStatus, PLAYER_HP_ROW)).toContain("[B2]");
  });

  it("draws the active ICE's effect on the ICE name row", () => {
    const state = makeState({
      statusEffects: [
        {
          kind: "shield",
          remaining: 3,
          magnitude: 20,
          target: "ice",
          iceIndex: 0,
          tickSource: "enemy",
        },
      ],
    });

    const groups = groupStatusByTarget(
      state.statusEffects,
      state.activeIceIndex,
    );
    const grid = renderGrid(state, null, null, groups, 80, 50);

    const rosterRow = Math.floor(50 * 0.44);
    expect(rowText(grid, rosterRow)).toContain("[D3]");
  });

  it("keeps the player's glyph and the ICE's glyph on separate rows (P14)", () => {
    const state = makeState({
      statusEffects: [
        {
          kind: "burn",
          remaining: 2,
          magnitude: 3,
          target: "player",
        },
        {
          kind: "shield",
          remaining: 3,
          magnitude: 20,
          target: "ice",
          iceIndex: 0,
          tickSource: "enemy",
        },
      ],
    });

    const groups = groupStatusByTarget(
      state.statusEffects,
      state.activeIceIndex,
    );
    const grid = renderGrid(state, null, null, groups, 80, 50);

    const rosterRow = Math.floor(50 * 0.44);
    expect(rowText(grid, PLAYER_HP_ROW)).toContain("[B2]");
    expect(rowText(grid, PLAYER_HP_ROW)).not.toContain("[D3]");
    expect(rowText(grid, rosterRow)).toContain("[D3]");
    expect(rowText(grid, rosterRow)).not.toContain("[B2]");
  });

  it("shows a non-target ICE's effect on that ICE's own row", () => {
    const second = makeIce("Wraith");
    const state = makeState({
      iceRoster: [makeIce("Caster"), second],
      activeIceIndex: 0,
      statusEffects: [
        {
          kind: "regen",
          remaining: 4,
          magnitude: 4,
          target: "ice",
          iceIndex: 1,
          tickSource: "enemy",
          healPerTick: 4,
        },
      ],
    });

    const groups = groupStatusByTarget(
      state.statusEffects,
      state.activeIceIndex,
    );
    const grid = renderGrid(state, null, null, groups, 80, 50);

    const firstRow = Math.floor(50 * 0.44);
    const secondRow = firstRow + 3;
    expect(rowText(grid, secondRow)).toContain("[R4]");
    expect(rowText(grid, firstRow)).not.toContain("[R4]");
  });

  it("does not overflow a narrow 40-column layout", () => {
    const state = makeState({
      statusEffects: [
        {
          kind: "burn",
          remaining: 2,
          magnitude: 3,
          target: "player",
        },
        {
          kind: "shield",
          remaining: 3,
          magnitude: 20,
          target: "ice",
          iceIndex: 0,
          tickSource: "enemy",
        },
        {
          kind: "powered",
          remaining: 2,
          magnitude: 6,
          target: "ice",
          iceIndex: 0,
          tickSource: "enemy",
        },
      ],
    });

    const groups = groupStatusByTarget(
      state.statusEffects,
      state.activeIceIndex,
    );
    const grid = renderGrid(state, null, null, groups, 40, 60);

    expect(grid.width).toBe(40);
    for (const row of [PLAYER_HP_ROW, Math.floor(60 * 0.44)]) {
      expect(rowText(grid, row).length).toBeLessThanOrEqual(40);
    }
  });
});

/** ADR-0251 slice A — the vertical, numbered hand. */
describe("combat grid program hand (ADR-0251)", () => {
  function prog(id: string, name: string, cost: number, aoe = false): Program {
    return { ...MOCK_PROGRAM, id, name, cost, aoe };
  }
  const HAND = [
    prog("backdoor", "Backdoor", 2),
    prog("barrier", "Barrier", 3),
    prog("sweep", "Sweep", 1, true),
    prog("kraken", "Kraken", 4),
    prog("ice_break", "Ice Break", 2),
  ];

  function handState(alarm: number, mutators: string[] = []): GameState {
    const base = makeState({ deck: HAND });
    return {
      ...base,
      player: { ...base.player, alarm },
      activeMutators: mutators as GameState["activeMutators"],
    };
  }

  function allRows(grid: ReturnType<typeof renderGrid>): string[] {
    return Array.from({ length: grid.height }, (_, y) => rowText(grid, y));
  }

  it.each([
    [80, 50],
    [60, 40],
    [40, 60],
  ])(
    "%ix%i: every slot is listed, numbered in input order, inside the rails",
    (cols, rows) => {
      const grid = renderGrid(handState(97), null, null, [], cols, rows);
      const text = allRows(grid);
      const slotRows = HAND.map((p, i) =>
        text.findIndex((line) =>
          line.includes(`${i + 1} ${p.name.toUpperCase()}`),
        ),
      );
      expect(slotRows.every((y) => y > 0)).toBe(true);
      // One row per slot, top to bottom in slot order.
      slotRows.forEach((y, i) => {
        if (i > 0) expect(y).toBe(slotRows[i - 1]! + 1);
      });
      // Rails intact and nothing past them on every hand row and the header.
      for (const y of [slotRows[0]! - 1, ...slotRows]) {
        const line = text[y]!;
        expect(line).toHaveLength(cols);
        expect(line[1]).toBe("║");
        expect(line[cols - 2]).toBe("║");
        expect(line[cols - 1]).toBe(" ");
      }
      expect(slotRows[slotRows.length - 1]!).toBeLessThan(rows - 2);
      // The old four-letter id strip is gone.
      expect(text.join("\n")).not.toContain("[back]");
      expect(text.join("\n")).not.toContain("HAND:");
    },
  );

  it.each([
    [80, 50],
    [60, 40],
    [40, 60],
  ])(
    "%ix%i: COST, BLOCKED and the ALL ICE target are on screen",
    (cols, rows) => {
      const text = allRows(
        renderGrid(handState(97), null, null, [], cols, rows),
      );
      const line = (slot: number) =>
        text.find((t) =>
          t.includes(`${slot} ${HAND[slot - 1]!.name.toUpperCase()}`),
        )!;
      expect(line(1)).toContain("+2");
      expect(line(2)).toContain("+3");
      expect(line(3)).toContain("ALL ICE");
      expect(line(4)).toContain("BLOCKED");
      // No predicted remaining COST on a hand row: the killing blow charges
      // nothing, so the row may not promise an after-value (ADR-0251 rule 5).
      for (const slot of [1, 2, 3, 4]) {
        expect(line(slot)).not.toContain("/100");
      }
    },
  );

  it("double_alarm doubles the COST the row shows", () => {
    const text = allRows(
      renderGrid(handState(10, ["double_alarm"]), null, null, [], 80, 50),
    );
    expect(text.some((t) => t.includes("1 BACKDOOR  COST +4"))).toBe(true);
    expect(text.some((t) => t.includes("4 KRAKEN    COST +8"))).toBe(true);
  });

  it("a BLOCKED row is drawn in a different ink as well as worded", () => {
    const grid = renderGrid(handState(97), null, null, [], 80, 50);
    const text = allRows(grid);
    const ok = text.findIndex((t) => t.includes("1 BACKDOOR"));
    const blocked = text.findIndex((t) => t.includes("4 KRAKEN"));
    expect(grid.get(3, ok)?.fg).toBe(PALETTE.CYAN_LIGHT);
    expect(grid.get(3, blocked)?.fg).toBe(PALETTE.GRAY_MID);
  });

  it("keeps the remaining rows in place when a card is played", () => {
    const full = allRows(renderGrid(handState(0), null, null, [], 60, 40));
    const less = allRows(
      renderGrid(
        { ...handState(0), deck: HAND.slice(1) },
        null,
        null,
        [],
        60,
        40,
      ),
    );
    const header = (t: string[]) => t.findIndex((l) => l.includes(" HAND "));
    expect(header(less)).toBe(header(full));
  });

  it("leaves the hand band empty when the touch overlay carries the hand", () => {
    const text = allRows(
      renderGrid(handState(10), null, null, [], 40, 60, true),
    );
    expect(text.join("\n")).not.toContain("BACKDOOR");
    expect(text.join("\n")).not.toContain("HAND");
  });
});
