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
 * The catalog is pinned to docs/design/story_skeleton.md (29 endings, 7/6/6/
 * 5/5), so this does not add endings. It pins the plain outcome per arc, so a
 * reorder of the array or a new ending cannot silently change which story a
 * plain run is told.
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
    // Arc 2 declares no status_quo: the positional fallback decides.
    [2, "arc2_ghost_dancer"],
    [3, "arc3_neutrality"],
    // Arc 4 declares no status_quo either — this is the observed
    // "LIBERATION FRONT / The AIs are free" on a single-mission run.
    [4, "arc4_liberation_front"],
    [5, "arc5_unknown"],
  ])("arc %i resolves to %s", (arc, id) => {
    expect(resolveEnding({ ...PLAIN, arc: arc as ArcId }).id).toBe(id);
  });

  it("records which arcs have no status_quo ending (the fallback's cause)", () => {
    const missing = ([1, 2, 3, 4, 5] as const).filter(
      (arc) =>
        !ENDINGS.some((e) => e.arc === arc && e.category === "status_quo"),
    );
    expect(missing).toEqual([2, 4]);
  });

  it("every arc has at least one ending, so the fallback is never undefined", () => {
    for (const arc of [1, 2, 3, 4, 5] as const) {
      expect(resolveEnding({ ...PLAIN, arc })).toBeDefined();
    }
  });

  it("the control branch is reachable only with the arc's own control ending", () => {
    // Rich + healthy: picks category "control" where the arc declares one.
    for (const arc of [1, 2, 3, 4] as const) {
      const ending = resolveEnding({
        ...PLAIN,
        arc,
        hp: 100,
        credits: 9000,
      });
      expect(ending.category).toBe("control");
      expect(ending.arc).toBe(arc);
    }
    // Arc 5 declares no control ending, so it falls back positionally too.
    expect(
      resolveEnding({ ...PLAIN, arc: 5, hp: 100, credits: 9000 }).category,
    ).not.toBe("control");
  });
});
