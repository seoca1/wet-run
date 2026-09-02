/** Unit tests for boss.ts.
 *
 * Run with: npx vitest run tests/boss.test.ts
 *
 * Tests the 4-phase boss state machine, HP-based phase transitions,
 * bossPhaseFromHp() threshold logic, shouldTransition() detection,
 * and bossPhaseLabel() display utilities.
 */

import { describe, it, expect } from "vitest";
import {
  BOSS_PHASE_TABLE,
  bossPhaseFromHp,
  shouldTransition,
  bossPhaseLabel,
} from "../src/core/boss.ts";
import type { BossPhase } from "../src/core/types.ts";

describe("BOSS_PHASE_TABLE", () => {
  it("contains exactly 5 phase entries (0-4)", () => {
    expect(BOSS_PHASE_TABLE.length).toBe(5);
  });

  it("phase 0 is the no-boss sentinel state", () => {
    const phase0 = BOSS_PHASE_TABLE[0];
    expect(phase0?.phase).toBe(0);
    expect(phase0?.label).toBe("—");
    expect(phase0?.minHpPct).toBe(0);
    expect(phase0?.maxHpPct).toBe(0);
  });

  it("phase 1 covers 75-100% HP", () => {
    const phase1 = BOSS_PHASE_TABLE[1];
    expect(phase1?.phase).toBe(1);
    expect(phase1?.label).toBe("Phase 1");
    expect(phase1?.minHpPct).toBe(75);
    expect(phase1?.maxHpPct).toBe(100);
  });

  it("phase 2 covers 50-75% HP", () => {
    const phase2 = BOSS_PHASE_TABLE[2];
    expect(phase2?.phase).toBe(2);
    expect(phase2?.label).toBe("Phase 2");
    expect(phase2?.minHpPct).toBe(50);
    expect(phase2?.maxHpPct).toBe(75);
  });

  it("phase 3 covers 25-50% HP", () => {
    const phase3 = BOSS_PHASE_TABLE[3];
    expect(phase3?.phase).toBe(3);
    expect(phase3?.label).toBe("Phase 3");
    expect(phase3?.minHpPct).toBe(25);
    expect(phase3?.maxHpPct).toBe(50);
  });

  it("phase 4 covers 0-25% HP", () => {
    const phase4 = BOSS_PHASE_TABLE[4];
    expect(phase4?.phase).toBe(4);
    expect(phase4?.label).toBe("Phase 4");
    expect(phase4?.minHpPct).toBe(0);
    expect(phase4?.maxHpPct).toBe(25);
  });

  it("every phase entry has phase, label, minHpPct, maxHpPct fields", () => {
    for (const phase of BOSS_PHASE_TABLE) {
      expect(phase).toHaveProperty("phase");
      expect(phase).toHaveProperty("label");
      expect(phase).toHaveProperty("minHpPct");
      expect(phase).toHaveProperty("maxHpPct");
    }
  });

  it("phases are ordered 0..4 sequentially", () => {
    for (let i = 0; i < BOSS_PHASE_TABLE.length; i++) {
      expect(BOSS_PHASE_TABLE[i]?.phase).toBe(i);
    }
  });

  it("boss phases 1-4 HP ranges are monotonically decreasing", () => {
    for (let i = 2; i < BOSS_PHASE_TABLE.length; i++) {
      const cur = BOSS_PHASE_TABLE[i];
      const prev = BOSS_PHASE_TABLE[i - 1];
      expect(cur).toBeDefined();
      expect(prev).toBeDefined();
      if (cur && prev) {
        expect(cur.maxHpPct).toBeLessThanOrEqual(prev.maxHpPct);
        expect(cur.minHpPct).toBeLessThanOrEqual(prev.minHpPct);
      }
    }
  });

  it("phase labels are non-empty strings", () => {
    for (const phase of BOSS_PHASE_TABLE) {
      expect(typeof phase.label).toBe("string");
      expect(phase.label.length).toBeGreaterThan(0);
    }
  });
});

describe("bossPhaseFromHp", () => {
  it("returns phase 1 at 100% HP", () => {
    expect(bossPhaseFromHp(100)).toBe(1);
  });

  it("returns phase 1 at the 75% boundary (inclusive)", () => {
    expect(bossPhaseFromHp(75)).toBe(1);
  });

  it("returns phase 2 just below 75%", () => {
    expect(bossPhaseFromHp(74)).toBe(2);
  });

  it("returns phase 2 at the 50% boundary (inclusive)", () => {
    expect(bossPhaseFromHp(50)).toBe(2);
  });

  it("returns phase 3 just below 50%", () => {
    expect(bossPhaseFromHp(49)).toBe(3);
  });

  it("returns phase 3 at the 25% boundary (inclusive)", () => {
    expect(bossPhaseFromHp(25)).toBe(3);
  });

  it("returns phase 4 just below 25%", () => {
    expect(bossPhaseFromHp(24)).toBe(4);
  });

  it("returns phase 4 at 0% HP", () => {
    expect(bossPhaseFromHp(0)).toBe(4);
  });

  it("returns phase 1 for HP above 100% (overheal/buff case)", () => {
    expect(bossPhaseFromHp(150)).toBe(1);
  });

  it("returns phase 4 for negative HP (overkill edge)", () => {
    expect(bossPhaseFromHp(-5)).toBe(4);
  });

  it("handles fractional HP near the 75% boundary", () => {
    expect(bossPhaseFromHp(75)).toBe(1);
    expect(bossPhaseFromHp(74.99)).toBe(2);
  });

  it("handles fractional HP near the 50% boundary", () => {
    expect(bossPhaseFromHp(50)).toBe(2);
    expect(bossPhaseFromHp(49.99)).toBe(3);
  });

  it("handles fractional HP near the 25% boundary", () => {
    expect(bossPhaseFromHp(25)).toBe(3);
    expect(bossPhaseFromHp(24.99)).toBe(4);
  });

  it("returns phase 1 for HP values 75 < hp <= 100", () => {
    for (const hp of [80, 85, 90, 95, 99.9, 100]) {
      expect(bossPhaseFromHp(hp)).toBe(1);
    }
  });

  it("returns phase 2 for HP values 50 < hp < 75", () => {
    for (const hp of [51, 60, 70, 74.5, 74.99]) {
      expect(bossPhaseFromHp(hp)).toBe(2);
    }
  });

  it("returns phase 3 for HP values 25 < hp < 50", () => {
    for (const hp of [26, 30, 40, 49, 49.99]) {
      expect(bossPhaseFromHp(hp)).toBe(3);
    }
  });

  it("returns phase 4 for HP values 0 <= hp < 25", () => {
    for (const hp of [0, 1, 10, 20, 24.99]) {
      expect(bossPhaseFromHp(hp)).toBe(4);
    }
  });
});

describe("shouldTransition", () => {
  it("returns false when phase matches current HP phase", () => {
    expect(shouldTransition(1, 80)).toBe(false);
    expect(shouldTransition(2, 60)).toBe(false);
    expect(shouldTransition(3, 40)).toBe(false);
    expect(shouldTransition(4, 10)).toBe(false);
  });

  it("returns true when crossing from phase 1 into phase 2", () => {
    expect(shouldTransition(1, 70)).toBe(true);
  });

  it("returns true when crossing from phase 2 into phase 3", () => {
    expect(shouldTransition(2, 40)).toBe(true);
  });

  it("returns true when crossing from phase 3 into phase 4", () => {
    expect(shouldTransition(3, 20)).toBe(true);
  });

  it("returns false at exact phase boundaries (still in current phase)", () => {
    expect(shouldTransition(1, 75)).toBe(false);
    expect(shouldTransition(2, 50)).toBe(false);
    expect(shouldTransition(3, 25)).toBe(false);
  });

  it("returns false when HP recovers into a higher-numbered phase (heal-back is ignored)", () => {
    expect(shouldTransition(2, 80)).toBe(false);
    expect(shouldTransition(3, 60)).toBe(false);
    expect(shouldTransition(4, 30)).toBe(false);
  });

  it("transitions forward across multiple phases in a single tick", () => {
    expect(shouldTransition(1, 40)).toBe(true);
    expect(shouldTransition(1, 10)).toBe(true);
    expect(shouldTransition(2, 10)).toBe(true);
  });

  it("handles sub-phase boundary crossings", () => {
    expect(shouldTransition(1, 74.9)).toBe(true);
    expect(shouldTransition(2, 49.9)).toBe(true);
    expect(shouldTransition(3, 24.9)).toBe(true);
  });

  it("returns false when no forward movement occurs", () => {
    expect(shouldTransition(1, 76)).toBe(false);
    expect(shouldTransition(2, 74)).toBe(false);
    expect(shouldTransition(4, 0)).toBe(false);
  });

  it("respects monotonic forward-only transitions across each phase boundary", () => {
    const drops: ReadonlyArray<readonly [BossPhase, number]> = [
      [1, 74],
      [1, 49],
      [1, 24],
      [2, 49],
      [2, 24],
      [3, 24],
    ];
    for (const [phase, hp] of drops) {
      expect(shouldTransition(phase, hp)).toBe(true);
    }
  });
});

describe("bossPhaseLabel", () => {
  it("returns em-dash placeholder for phase 0", () => {
    expect(bossPhaseLabel(0)).toBe("—");
  });

  it("returns 'Phase 1' for phase 1", () => {
    expect(bossPhaseLabel(1)).toBe("Phase 1");
  });

  it("returns 'Phase 2' for phase 2", () => {
    expect(bossPhaseLabel(2)).toBe("Phase 2");
  });

  it("returns 'Phase 3' for phase 3", () => {
    expect(bossPhaseLabel(3)).toBe("Phase 3");
  });

  it("returns 'Phase 4' for phase 4", () => {
    expect(bossPhaseLabel(4)).toBe("Phase 4");
  });

  it("falls back to em-dash for out-of-range phase values", () => {
    expect(bossPhaseLabel(5 as BossPhase)).toBe("—");
    expect(bossPhaseLabel(-1 as BossPhase)).toBe("—");
    expect(bossPhaseLabel(99 as BossPhase)).toBe("—");
  });

  it("returns non-empty strings for every valid phase", () => {
    for (let i = 0; i <= 4; i++) {
      const label = bossPhaseLabel(i as BossPhase);
      expect(typeof label).toBe("string");
      expect(label.length).toBeGreaterThan(0);
    }
  });

  it("labels match the entries in BOSS_PHASE_TABLE", () => {
    for (let i = 0; i < BOSS_PHASE_TABLE.length; i++) {
      expect(bossPhaseLabel(i as BossPhase)).toBe(BOSS_PHASE_TABLE[i]?.label);
    }
  });
});

describe("boss phase integration", () => {
  it("HP walking from 100 -> 0 produces a forward phase progression", () => {
    let phase: BossPhase = 1;
    const sequence: BossPhase[] = [phase];
    const drops = [90, 80, 74, 60, 49, 40, 24, 10, 0];
    for (const hp of drops) {
      const next: BossPhase = bossPhaseFromHp(hp);
      if (shouldTransition(phase, hp)) {
        phase = next;
      }
      sequence.push(phase);
    }
    expect(sequence).toEqual([1, 1, 1, 2, 2, 3, 3, 4, 4, 4]);
  });

  it("bossPhaseLabel(bossPhaseFromHp(hp)) returns a meaningful label for any HP", () => {
    for (const hp of [100, 75, 74, 50, 49, 25, 24, 0]) {
      const label = bossPhaseLabel(bossPhaseFromHp(hp));
      expect(label.length).toBeGreaterThan(0);
    }
  });
});
