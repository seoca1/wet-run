/** ADR-0251 slice A — the hand tells the truth about each slot.
 *
 * Every label is checked against the real reducer: the COST a row shows is
 * the COST `use_program` charges, a BLOCKED row is exactly a play the reducer
 * refuses, and slot N is the program `select_program` N plays.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";
import { combatEntryHintRows } from "../src/core/state/onboarding";
import {
  COMPACT_HAND_HEADER,
  COST_LIMIT,
  FULL_ROW_WIDTH,
  affordanceAriaLabel,
  combatHandRow,
  formatAffordanceRow,
  formatCompactAffordanceRow,
  programAffordances,
  programAlarmCost,
  touchAffordanceLines,
} from "../src/core/combat/program_affordance";
import {
  applyAction,
  makeInitialState,
  resolveProgramSelection,
} from "../src/core/state/state";
import type { RunMutator } from "../src/core/state/run_mutators";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

const MISSION: Mission = {
  id: "aff",
  title: "Affordance",
  fixer: "test",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 10, materials: {} },
};

const ICE: Ice = {
  id: "wall",
  name: "Wall",
  tier: 1,
  hp: 10_000,
  maxHp: 10_000,
  armor: 0,
  personality: "aggressive",
  aggression: "standard",
};

function program(id: string, cost: number, aoe = false): Program {
  return {
    id,
    name: id.charAt(0).toUpperCase() + id.slice(1),
    tier: 1,
    cost,
    effect: "attack",
    description: "test",
    aoe,
  };
}

const HAND: readonly Program[] = [
  program("strike", 3),
  program("split", 8, true),
  program("wisp", 8),
  program("odd", 2.5),
  program("free", 0),
];

function combat(
  alarm: number,
  mutators: readonly RunMutator[] = [],
  hand: readonly Program[] = HAND,
): GameState {
  const base = makeInitialState(MISSION, ICE, [...hand], [], [...mutators]);
  return {
    ...base,
    iceRoster: [ICE],
    activeIceIndex: 0,
    phase: "combat",
    runPhase: "combat",
    player: { ...base.player, alarm },
    lastEnemyAttackMs: 0,
    dixiePlayerTurnsSinceAttack: 0,
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("COST label = the reducer's charge", () => {
  it.each([
    ["normal", [] as RunMutator[]],
    ["double_alarm", ["double_alarm"] as RunMutator[]],
  ])("%s: every slot's COST and AFTER equal what use_program does", (_label, mutators) => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    const state = combat(38, mutators);
    const rows = programAffordances(state);
    expect(rows).toHaveLength(HAND.length);
    for (const row of rows) {
      const next = applyAction(state, {
        type: "use_program",
        programId: row.programId,
      });
      expect(row.blocked).toBe(false);
      expect(next.player.alarm - state.player.alarm).toBe(row.cost);
      expect(next.player.alarm).toBe(row.after);
    }
  });

  it("double_alarm doubles and floors exactly like the reducer", () => {
    expect(programAlarmCost(program("a", 3), [])).toBe(3);
    expect(programAlarmCost(program("a", 3), ["double_alarm"])).toBe(6);
    expect(programAlarmCost(program("a", 2.5), [])).toBe(2);
    expect(programAlarmCost(program("a", 2.5), ["double_alarm"])).toBe(5);
    expect(programAlarmCost(program("a", 3), ["ice_x2", "low_hp"])).toBe(3);
  });

  it.each([
    ["normal", [] as RunMutator[], 97, 3, false],
    ["normal", [] as RunMutator[], 98, 3, true],
    ["double_alarm", ["double_alarm"] as RunMutator[], 94, 3, false],
    ["double_alarm", ["double_alarm"] as RunMutator[], 95, 3, true],
  ])(
    "%s %j: COST %i, cost %i, BLOCKED=%s matches the reducer's refusal",
    (_label, mutators, alarm, cost, blocked) => {
      vi.spyOn(Math, "random").mockReturnValue(0.99);
      const state = combat(alarm, mutators, [program("probe", cost)]);
      const [row] = programAffordances(state);
      expect(row?.blocked).toBe(blocked);
      const next = applyAction(state, { type: "use_program", programId: "probe" });
      if (blocked) {
        expect(next.message).toBe("Cost too high — program failed");
        expect(next.deck).toEqual(state.deck);
        expect(next.player.alarm).toBe(alarm);
      } else {
        expect(next.player.alarm).toBe(COST_LIMIT);
        expect(next.message).not.toBe("Cost too high — program failed");
      }
    },
  );
});

describe("slot order = input order", () => {
  it("slot N names the program select_program N plays, and the play removes exactly that row", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    const state = combat(0);
    const rows = programAffordances(state);
    rows.forEach((row, i) => {
      expect(row.slot).toBe(i + 1);
      const resolved = resolveProgramSelection(state, {
        type: "select_program",
        handIndex: row.slot,
      });
      expect(resolved?.programId).toBe(row.programId);
      const next = applyAction(state, resolved!);
      expect(next.deck.map((p) => p.id)).toEqual(
        state.deck.filter((_, j) => j !== i).map((p) => p.id),
      );
    });
  });
});

describe("target label", () => {
  it("says ALL ICE only for aoe programs", () => {
    const rows = programAffordances(combat(0));
    expect(rows.map((r) => r.target)).toEqual([
      "ICE",
      "ALL ICE",
      "ICE",
      "ICE",
      "ICE",
    ]);
  });
});

describe("row text", () => {
  it("renders the synthesis contract", () => {
    const rows = programAffordances(
      combat(38, [], [program("strike", 3), program("split", 8, true)]),
    );
    expect(rows.map(formatAffordanceRow)).toEqual([
      "1 STRIKE    COST +3  → 41/100   TARGET ICE",
      "2 SPLIT     COST +8  → 46/100   TARGET ALL ICE",
    ]);
    const blocked = programAffordances(combat(95, [], [program("wisp", 8)]));
    expect(formatAffordanceRow(blocked[0]!)).toBe(
      "1 WISP      COST +8  → BLOCKED  TARGET ICE",
    );
  });

  it("narrow rows line up under their legend and keep every fact", () => {
    const rows = programAffordances(
      combat(95, ["double_alarm"], [program("strike", 2), program("split", 3, true)]),
    );
    const lines = rows.map(formatCompactAffordanceRow);
    expect(COMPACT_HAND_HEADER).toBe("HAND        COST AFTER    TARGET");
    expect(lines).toEqual([
      "1 STRIKE    +4   99/100   ICE",
      "2 SPLIT     +6   BLOCKED  ALL ICE",
    ]);
    for (const line of lines) {
      expect(line.indexOf("+")).toBe(COMPACT_HAND_HEADER.indexOf("COST"));
      expect(line.indexOf(" ICE") + 1 >= COMPACT_HAND_HEADER.indexOf("TARGET")).toBe(true);
      expect(line.length).toBeLessThanOrEqual(34);
    }
  });

  it("full rows fit the 60-column frame", () => {
    expect(FULL_ROW_WIDTH).toBeLessThanOrEqual(54);
  });

  it("names nothing the runtime cannot vouch for", () => {
    const state = combat(10);
    const texts = programAffordances(state).flatMap((row) => [
      formatAffordanceRow(row),
      formatCompactAffordanceRow(row),
      affordanceAriaLabel(row),
      ...touchAffordanceLines(row),
    ]);
    for (const text of texts) {
      expect(text).not.toMatch(/dmg|damage|role|kill|burn|slow|%|test/i);
    }
  });
});

describe("touch label = canvas semantics", () => {
  it("states slot, name, COST, outcome and target", () => {
    const [ok, aoe] = programAffordances(
      combat(38, [], [program("strike", 3), program("split", 8, true)]),
    );
    expect(touchAffordanceLines(ok!)).toEqual([
      "1 COST+3",
      "STRIKE",
      "→ 41/100",
      "ICE",
    ]);
    expect(affordanceAriaLabel(aoe!)).toBe(
      "2 SPLIT, COST plus 8, to 46 of 100, target ALL ICE",
    );
    const [blocked] = programAffordances(combat(95, [], [program("wisp", 8)]));
    expect(touchAffordanceLines(blocked!)).toEqual([
      "1 COST+8",
      "WISP",
      "BLOCKED",
      "ICE",
    ]);
    expect(affordanceAriaLabel(blocked!)).toBe(
      "1 WISP, COST plus 8, blocked, over 100, target ICE",
    );
    for (const line of touchAffordanceLines(blocked!)) {
      expect(line.length).toBeLessThanOrEqual(9);
    }
  });
});

describe("display path is inert", () => {
  it("consumes no RNG and never reads the clock", () => {
    const random = vi.spyOn(Math, "random");
    const now = vi.spyOn(Date, "now");
    const rows = programAffordances(combat(50, ["double_alarm"]));
    rows.forEach((row) => {
      formatAffordanceRow(row);
      formatCompactAffordanceRow(row);
      affordanceAriaLabel(row);
      touchAffordanceLines(row);
    });
    expect(random).not.toHaveBeenCalled();
    expect(now).not.toHaveBeenCalled();
  });
});

describe("hand block placement", () => {
  it.each([
    [50, 42],
    [40, 32],
    [60, 51],
  ])("rows=%i: header row %i, five slots end inside the frame", (rows, header) => {
    expect(combatHandRow(rows)).toBe(header);
    expect(combatHandRow(rows) + 5).toBeLessThanOrEqual(rows - 3);
  });
});

describe("wiring", () => {
  const mainSource = readFileSync(
    fileURLToPath(new URL("../src/main.ts", import.meta.url)),
    "utf8",
  ).replace(/\s+/g, "");

  it("feeds the touch row the same affordance rows the canvas draws", () => {
    expect(mainSource).toContain(
      'updateProgramRow(this.state.phase==="combat"?programAffordances(this.state):[]',
    );
  });

  it("hands the canvas hand band to the touch overlay only while it is mounted", () => {
    expect(mainSource).toContain("handOnOverlay:this.touchOverlayMounted");
    expect(mainSource).toContain(
      "this.unmountTouch=mountVirtualGamepad(handler);this.touchOverlayMounted=true;",
    );
  });

  it("names the program that was actually played in the touch acknowledgement", () => {
    // Before: `this.state.deck[handIndex]` was read after the play, i.e. a
    // different (or no) card than the one tapped.
    expect(mainSource).not.toContain("program?.id.slice(0,4)");
    expect(mainSource).toContain("this.pressedProgramName=");
  });

  it("keeps the combat-entry hint above the hand at every grid", () => {
    for (const rows of [50, 40, 60]) {
      for (const row of combatEntryHintRows(rows)) {
        expect(row).toBeLessThan(combatHandRow(rows));
      }
    }
  });
});
