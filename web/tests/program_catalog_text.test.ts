import { describe, it, expect } from "vitest";
import { loadProgramsCatalog } from "../src/core/data_loaders";
import {
  programEffect,
  programEffectDescription,
  programEffectTag,
} from "../src/core/combat/program_effects";
import programsData from "../src/data/programs.json";

/**
 * The program catalog's text must state what the program does.
 *
 * ADR-0251 rule 5: the screen states what will happen. ADR-0255 wires the
 * opening hand's mechanics, so the text is built from the mechanic
 * (`program_effects.ts`) rather than typed by hand — it cannot drift away
 * from the reducer.
 */
describe("program catalog text", () => {
  const catalog = loadProgramsCatalog(programsData);

  it("describes the damage the program actually deals", () => {
    for (const program of Object.values(catalog)) {
      const damage = program.tier * 5;
      expect(program.description).toContain(
        `Deals ${damage} damage to ${program.aoe ? "every ICE" : "the ICE"}`,
      );
    }
  });

  it("is derived from the mechanic, not typed by hand", () => {
    for (const program of Object.values(catalog)) {
      expect(program.description).toBe(
        programEffectDescription({
          id: program.id,
          tier: program.tier,
          aoe: program.aoe,
        }),
      );
    }
  });

  it("keeps the designed effect that is not wired yet", () => {
    const rows = Object.values(catalog);
    expect(rows.length).toBeGreaterThan(0);
    for (const program of rows) {
      expect(program.plannedDescription).toBeTruthy();
    }
  });

  it("names an effect only where one is implemented", () => {
    for (const program of Object.values(catalog)) {
      const effect = programEffect(program);
      if (effect.kind === "damage") {
        // A plain attack must not claim an extra effect.
        expect(program.description).not.toMatch(
          /shield|evade|decoy|pierce|evasion|armor pierce|raises your damage/i,
        );
        expect(programEffectTag(program)).toBe("");
      }
      // Where an effect exists, the text must mention it.
      if (effect.kind === "shield") {
        expect(program.description).toMatch(/shield/i);
      }
      if (effect.kind === "evade") {
        expect(program.description).toMatch(/incoming damage/i);
      }
      if (effect.kind === "decoy") {
        expect(program.description).toMatch(/soaks \d+% of the next hit/i);
      }
      if (effect.kind === "pierce") {
        expect(program.description).toMatch(/ignores \d+ points of its armor/);
      }
      if (effect.kind === "armor_ignore") {
        expect(program.description).toMatch(/ignores \d+% of its armor/);
      }
      if (effect.kind === "empower") {
        expect(program.description).toMatch(/adds \d+ damage to your attacks/i);
      }
    }
  });
});
