/** ADR-0270 — the ending a plain run gets must be a decision, not an accident.
 *
 * `resolveEnding` resolves by category, and falls back to `arcEndings[0]` when
 * the arc has no ending in the needed category. Only arcs 1, 3 and 5 declare a
 * `status_quo` ending, so a plain run (mid HP, few credits, one mission -- the
 * only shape this tier can produce) lands on the first declared ending of
 * arcs 2 and 4 instead: `arc2_ghost_dancer` (transcendence) and
 * `arc4_liberation_front` (liberation). That is why a single mundane mission
 * finished on "The AIs are free. What have you done?".
 *
 * ADR-0270 pinned the plain outcome per arc without adding endings (the
 * catalog was the skeleton's contract). ADR-0271 added the two status_quo
 * endings those arcs were missing, so the plain outcome is now declared rather
 * than positional -- and still pinned, so a reorder cannot change it.
 */
import { describe, expect, it } from "vitest";
import {
  ENDINGS,
  resolveEnding,
  type ArcId,
} from "../src/core/combat/ending_resolver";

const PLAIN = {
  hp: 50,
  maxHp: 100,
  credits: 100,
  missionsCompleted: 1,
  totalDeaths: 0,
  factionScores: {},
  choices: [],
} as const;

describe("ADR-0270 — a plain run's ending per arc", () => {
  it.each([
    [1, "arc1_wage_slave"],
    [2, "arc2_status_quo"],
    [3, "arc3_neutrality"],
    [4, "arc4_status_quo"],
    [5, "arc5_unknown"],
  ])("arc %i resolves to %s", (arc, id) => {
    expect(resolveEnding({ ...PLAIN, arc: arc as ArcId }).id).toBe(id);
  });

  it("every arc has a status_quo ending, so a plain run is never over-claimed", () => {
    // ADR-0271: 2 and 4 were the gaps. The fallback (`arcEndings[0]`) is still
    // there for other categories, but a plain run no longer depends on it.
    const missing = ([1, 2, 3, 4, 5] as const).filter(
      (arc) =>
        !ENDINGS.some((e) => e.arc === arc && e.category === "status_quo"),
    );
    expect(missing).toEqual([]);
  });

  it("every arc has at least one ending, so the fallback is never undefined", () => {
    for (const arc of [1, 2, 3, 4, 5] as const) {
      expect(resolveEnding({ ...PLAIN, arc })).toBeDefined();
    }
  });

  it("the control branch is reachable only with the arc's own control ending", () => {
    // Rich + healthy: picks category "control" where the arc declares one.
    for (const arc of [1, 2, 3, 4, 5] as const) {
      const ending = resolveEnding({
        ...PLAIN,
        arc,
        hp: 100,
        credits: 9000,
      });
      expect(ending.category).toBe("control");
      expect(ending.arc).toBe(arc);
    }
    // Arc 5 had no control ending either (ADR-0271 added it), so a rich run
    // there used to fall through to arc5_neuromancer (transcendence).
    const richFive = resolveEnding({
      ...PLAIN,
      arc: 5,
      hp: 100,
      credits: 9000,
    });
    expect(richFive.category).toBe("control");
    expect(richFive.id).toBe("arc5_control");
  });
});
