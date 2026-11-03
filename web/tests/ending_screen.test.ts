/** ADR-0269 — the ending looks back at the run it ended.
 *
 * The ending screen used to be two lines of verdict with no reference to the
 * run: which mission, at what cost, for what. The context already carried the
 * numbers; the screen simply did not show them.
 */
import { describe, expect, it } from "vitest";
import { renderEndingScreen } from "../src/renderer/ending";

const text = (grid: ReturnType<typeof renderEndingScreen>) =>
  grid.cells.map((row) => row.map((c) => c.char).join("")).join("\n");

const SUMMARY = {
  mission: "Aleph Fragment",
  hp: 87,
  maxHp: 100,
  credits: 4700,
  turns: 21,
};

describe("ending screen — run summary (ADR-0269)", () => {
  it("names the mission and the run's final numbers", () => {
    const grid = renderEndingScreen("arc4_liberation_front", 80, 50, SUMMARY);
    const out = text(grid);
    expect(out).toContain("Aleph Fragment");
    expect(out).toContain("HP 87/100");
    expect(out).toContain("4,700cr");
    expect(out).toContain("21 turns");
    // The verdict and the exit key are still there.
    expect(out).toContain("LIBERATION FRONT");
    expect(out).toContain("ENTER / ESC: return to title");
  });

  it("fits the 40-column layout without spilling", () => {
    const grid = renderEndingScreen("arc4_liberation_front", 40, 60, {
      ...SUMMARY,
      mission: "Neuromancer Negotiation",
    });
    for (const row of grid.cells) {
      expect(row.map((c) => c.char).join("").length).toBeLessThanOrEqual(40);
    }
    const out = text(grid);
    expect(out).toContain("HP 87/100");
    expect(out).toContain("4,700cr");
  });

  it("draws nothing extra when no summary is given", () => {
    const without = renderEndingScreen("arc4_liberation_front", 80, 50);
    const withSummary = renderEndingScreen(
      "arc4_liberation_front",
      80,
      50,
      SUMMARY,
    );
    expect(text(without)).not.toContain("turns");
    expect(text(withSummary)).toContain("turns");
  });
});
