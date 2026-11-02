/** ADR-0251 slice B — status application and status end are no longer silent.
 *
 * Application: the `status_apply` renderer existed but nothing spawned it.
 * End: `tickStatus` (and the consumption of slow / vulnerable, and the
 * enemy-turn tick of ICE-cast effects) dropped effects without a trace.
 * Both now leave a combat-log line, which the HUD prints and which reduced
 * motion does not touch; application also spawns the existing VFX.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  applyAction,
  buildHudLines,
  makeInitialState,
} from "../src/core/state/state";
import {
  endedStatuses,
  statusEventLine,
  statusEventLines,
  tickStatus,
} from "../src/core/status";
import { composeCombatVfx } from "../src/renderer/combat_vfx";
import { makeGrid } from "../src/core/grid";
import type {
  GameState,
  Ice,
  Mission,
  Program,
  StatusEffectInstance,
} from "../src/core/types";

const MISSION: Mission = {
  id: "sb",
  title: "Status",
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
const STRIKE: Program = {
  id: "strike",
  name: "Strike",
  tier: 1,
  cost: 1,
  effect: "attack",
  description: "test",
  aoe: false,
};

function combat(
  statusEffects: StatusEffectInstance[] = [],
  roster: Ice[] = [ICE],
): GameState {
  const base = makeInitialState(MISSION, ICE, [STRIKE, { ...STRIKE, id: "s2" }]);
  return {
    ...base,
    iceRoster: roster,
    activeIceIndex: 0,
    phase: "combat",
    runPhase: "combat",
    statusEffects,
    lastEnemyAttackMs: 0,
    dixiePlayerTurnsSinceAttack: 0,
  };
}

const play = (s: GameState) =>
  applyAction(s, { type: "use_program", programId: "strike" });

afterEach(() => {
  vi.restoreAllMocks();
});

describe("status application", () => {
  it("a burn/slow proc spawns status_apply and logs who got what", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.1); // both 20% procs fire
    const next = play(combat());
    const kinds = next.statusEffects.map((e) => e.kind);
    expect(kinds).toContain("burn");
    expect(kinds).toContain("slow");
    const vfx = next.vfxInstances.filter((v) => v.kind === "status_apply");
    expect(vfx).toHaveLength(1);
    expect(vfx[0]?.payload).toBe("ICE BURN+SLOW");
    // One line per holder, so the HUD's four log lines keep it.
    expect(next.combatLog).toContain("ICE BURN+SLOW on");
    expect(buildHudLines(next)).toContain("ICE BURN+SLOW on");
  });

  it("no proc, no status feedback", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    const next = play(combat());
    expect(next.vfxInstances.some((v) => v.kind === "status_apply")).toBe(false);
    expect(next.combatLog.some((l) => / (on|off)$/.test(l))).toBe(false);
  });

  it("the spawned overlay names the status inside the frame at 40 columns", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.1);
    const next = play(combat());
    const grid = composeCombatVfx(makeGrid(40, 60), next.vfxInstances, 40, 60);
    const text = grid.cells.map((r) => r.map((c) => c.char).join(""));
    const line = text.find((t) => t.includes("ICE BURN+SLOW applied"));
    expect(line).toBeDefined();
    expect(line!.length).toBe(40);
    expect(line!.trimEnd().length).toBeLessThan(39);
  });
});

describe("status end", () => {
  const burn = (remaining: number): StatusEffectInstance => ({
    kind: "burn",
    remaining,
    magnitude: 3,
    target: "ice",
  });

  it("an expiring burn is logged as off (was silently dropped by tickStatus)", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    const next = play(combat([burn(1)]));
    expect(next.statusEffects.some((e) => e.kind === "burn")).toBe(false);
    expect(next.combatLog).toContain("ICE BURN off");
  });

  it("a burn that still has turns left is not reported as ended", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    const next = play(combat([burn(3)]));
    expect(next.combatLog).not.toContain("ICE BURN off");
  });

  it("a slow spent on the hit is logged as off", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    const slow: StatusEffectInstance = {
      kind: "slow",
      remaining: 2,
      magnitude: 30,
      target: "ice",
      slowPct: 30,
    };
    const next = play(combat([slow]));
    expect(next.statusEffects.some((e) => e.kind === "slow")).toBe(false);
    expect(next.combatLog).toContain("ICE SLOW off");
  });

  it("an ICE-cast effect ending in the enemy turn is logged with its ICE", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    const regen: StatusEffectInstance = {
      kind: "regen",
      remaining: 1,
      magnitude: 2,
      target: "ice",
      iceIndex: 1,
      tickSource: "enemy",
      healPerTick: 2,
    };
    const next = play(combat([regen], [ICE, { ...ICE, id: "w2" }]));
    expect(next.statusEffects.some((e) => e.kind === "regen")).toBe(false);
    expect(next.combatLog).toContain("ICE2 REGEN off");
    // The enemy turn's own last line is still the message and log head.
    expect(next.message).toBe(next.combatLog[0]);
  });

  it("the end is information, not animation: the HUD prints it", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    const next = play(combat([burn(1)]));
    const hud = buildHudLines(next);
    expect(hud).toContain("ICE BURN off");
  });

  it("status feedback consumes no RNG", () => {
    const calls = (s: GameState) => {
      const spy = vi.spyOn(Math, "random").mockReturnValue(0.99);
      play(s);
      const n = spy.mock.calls.length;
      spy.mockRestore();
      return n;
    };
    expect(calls(combat([burn(1)]))).toBe(calls(combat([])));
  });
});

describe("status helpers", () => {
  it("endedStatuses lists exactly what a tick dropped", () => {
    const before: StatusEffectInstance[] = [
      { kind: "burn", remaining: 1, magnitude: 3, target: "ice" },
      { kind: "burn", remaining: 2, magnitude: 3, target: "ice" },
      { kind: "slow", remaining: 1, magnitude: 30, target: "ice" },
    ];
    const state = { ...combat(before) };
    const after = tickStatus(state).statusEffects;
    const ended = endedStatuses(before, after);
    expect(ended.map((e) => e.kind).sort()).toEqual(["burn", "slow"]);
  });

  it("labels the target in words", () => {
    const effect: StatusEffectInstance = {
      kind: "burn",
      remaining: 1,
      magnitude: 3,
      target: "player",
    };
    expect(statusEventLine(effect, "off", 1)).toBe("YOU BURN off");
    expect(
      statusEventLine({ ...effect, target: "ice", iceIndex: 2 }, "on", 3),
    ).toBe("ICE3 BURN on");
    expect(statusEventLine({ ...effect, target: "ice" }, "on", 3)).toBe(
      "ICE BURN on",
    );
    expect(
      statusEventLines(
        [
          { ...effect, target: "ice" },
          { ...effect, kind: "slow", target: "ice" },
          { ...effect, kind: "regen", target: "ice", iceIndex: 1 },
        ],
        "off",
        2,
      ),
    ).toEqual(["ICE BURN+SLOW off", "ICE2 REGEN off"]);
  });
});
