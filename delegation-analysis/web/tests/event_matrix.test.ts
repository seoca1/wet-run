/** Unit tests for event_matrix (Tier 5.5). */
import { describe, it, expect } from "vitest";
import {
  buildEventMatrix,
  pickEventKind,
  makeRng,
  EVENT_GLYPHS,
  EVENT_LABELS,
} from "../src/core/event_matrix.ts";
import type { Ice, Program } from "../src/core/types.ts";

const iceCatalog: Readonly<Record<string, Ice>> = Object.freeze({
  watchdog: { id: "watchdog", name: "Watchdog", hp: 100, armor: 0, tier: 1 },
  wintermute: { id: "wintermute", name: "Wintermute", hp: 200, armor: 0, tier: 4 },
});

const programCatalog: Readonly<Record<string, Program>> = Object.freeze({
  strike: { id: "strike", name: "Strike", tier: 1, cost: 10, effect: "damage", description: "", aoe: false },
  shield: { id: "shield", name: "Shield", tier: 1, cost: 10, effect: "block", description: "", aoe: false },
});

describe("event_matrix (Tier 5.5)", () => {
  it("buildEventMatrix returns 5 nodes", () => {
    const nodes = buildEventMatrix(iceCatalog, programCatalog, 42);
    expect(nodes.length).toBe(5);
  });

  it("last node is boss with combat event", () => {
    const nodes = buildEventMatrix(iceCatalog, programCatalog, 42);
    const boss = nodes[4];
    expect(boss?.isBoss).toBe(true);
    expect(boss?.eventKind).toBe("combat");
  });

  it("surface node is mostly combat (deterministic with seed)", () => {
    const nodes = buildEventMatrix(iceCatalog, programCatalog, 42);
    const surface = nodes[0];
    expect(surface?.zone).toBe("surface");
    expect(["combat", "discovery"]).toContain(surface?.eventKind);
  });

  it("deterministic: same seed produces same eventKind sequence", () => {
    const a = buildEventMatrix(iceCatalog, programCatalog, 42);
    const b = buildEventMatrix(iceCatalog, programCatalog, 42);
    expect(a.map((n) => n.eventKind)).toEqual(b.map((n) => n.eventKind));
  });

  it("event_data populated for non-combat events", () => {
    const nodes = buildEventMatrix(iceCatalog, programCatalog, 42);
    for (const node of nodes) {
      if (node.eventKind === "combat") {
        expect(node.eventData).toBeNull();
      } else {
        // trap: damage 10..20; cache: programId; rest: healPct 0.25; etc.
        expect(node.eventData).not.toBeNull();
      }
    }
  });

  it("trap event has damage in 10..20 range", () => {
    const nodes = buildEventMatrix(iceCatalog, programCatalog, 99);
    const trap = nodes.find((n) => n.eventKind === "trap");
    if (trap) {
      expect(trap.eventData?.damage).toBeGreaterThanOrEqual(10);
      expect(trap.eventData?.damage).toBeLessThanOrEqual(20);
    }
  });

  it("rest event heals 25% of max hp", () => {
    const nodes = buildEventMatrix(iceCatalog, programCatalog, 99);
    const rest = nodes.find((n) => n.eventKind === "rest");
    if (rest) {
      expect(rest.eventData?.healPct).toBe(0.25);
    }
  });

  it("EVENT_GLYPHS has 6 entries (combat/discovery/trap/cache/rest/merchant)", () => {
    expect(Object.keys(EVENT_GLYPHS).sort()).toEqual(
      ["cache", "combat", "discovery", "merchant", "rest", "trap"].sort(),
    );
  });

  it("EVENT_LABELS has 6 entries", () => {
    expect(Object.keys(EVENT_LABELS).sort()).toEqual(
      ["cache", "combat", "discovery", "merchant", "rest", "trap"].sort(),
    );
  });
});

describe("makeRng (deterministic)", () => {
  it("same seed produces same sequence", () => {
    const a = makeRng(42);
    const b = makeRng(42);
    for (let i = 0; i < 5; i++) {
      expect(a()).toBe(b());
    }
  });

  it("different seeds diverge", () => {
    const a = makeRng(42);
    const b = makeRng(43);
    expect(a()).not.toBe(b());
  });
});

describe("pickEventKind (zone-distribution)", () => {
  it("surface: combat or discovery", () => {
    for (let i = 0; i < 20; i++) {
      const r = pickEventKind("surface", makeRng(i));
      expect(["combat", "discovery"]).toContain(r);
    }
  });
  it("mid: combat, trap, or discovery", () => {
    for (let i = 0; i < 20; i++) {
      const r = pickEventKind("mid", makeRng(i));
      expect(["combat", "trap", "discovery"]).toContain(r);
    }
  });
  it("core-deep: always combat (boss)", () => {
    for (let i = 0; i < 20; i++) {
      const r = pickEventKind("core-deep", makeRng(i));
      expect(r).toBe("combat");
    }
  });
});