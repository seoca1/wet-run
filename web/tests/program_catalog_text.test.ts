import { describe, it, expect } from "vitest";
import { loadProgramsCatalog } from "../src/core/data_loaders";
import programsData from "../src/data/programs.json";

/**
 * The program catalog's text must state what the program does.
 *
 * ADR-0251 rule 5: the screen states what will happen. The web reducer
 * gives every program the same damage path (`baseDamage: program.tier * 5`
 * in state_actions_programs.ts), so the catalog's per-program design
 * intent — shield, buff, decoy, armor pierce — is not what a program does
 * yet. The loader therefore reports the real effect in `description` and
 * keeps the design intent in `plannedDescription`, so a program browser
 * (PROGRAM INSPECT) cannot show the intent as if it were live.
 */
describe("program catalog text", () => {
  const catalog = loadProgramsCatalog(programsData);

  it("describes the damage the program actually deals", () => {
    for (const program of Object.values(catalog)) {
      const damage = program.tier * 5;
      expect(program.description).toBe(
        program.aoe
          ? `Deals ${damage} damage to every ICE.`
          : `Deals ${damage} damage to the ICE.`,
      );
    }
  });

  it("keeps the designed effect, which is not wired yet", () => {
    const rows = Object.values(catalog);
    expect(rows.length).toBeGreaterThan(0);
    for (const program of rows) {
      expect(program.plannedDescription).toBeTruthy();
    }
  });

  it("no longer promises an effect the web tier does not implement", () => {
    for (const program of Object.values(catalog)) {
      // The planned text may name a shield / buff / decoy; the live text
      // must not.
      expect(program.description).not.toMatch(
        /shield|buff|decoy|evasion|armor pierce|counter|heal/i,
      );
    }
  });
});
