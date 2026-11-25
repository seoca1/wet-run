/**
 * ADR-0315 — the jockey screen must say what the choice does.
 *
 * The jockey changes the starting deck (ADR-0276), so a bare list of three
 * handles is exactly the kind of choice the redesign is meant to remove. Each
 * entry now carries its tagline and its deck, wrapped rather than sliced.
 */
import { describe, expect, it } from "vitest";
import { renderJockeySelect } from "../src/renderer/jockey_select";
import { JOCKEYS } from "../src/core/state/jockey";
import { startingDeckIds } from "../src/core/state/starting_deck";

import { gridText } from "./view_fixtures";
describe("ADR-0315 · jockey select", () => {
  it("names every jockey", () => {
    const text = gridText(renderJockeySelect(0, 80, 50));
    for (const j of JOCKEYS) expect(text).toContain(j.handle);
  });

  it("shows the deck each jockey brings", () => {
    const text = gridText(renderJockeySelect(0, 80, 50));
    for (const j of JOCKEYS) {
      const ids = startingDeckIds(j.id);
      expect(text).toContain(`deck: ${ids.join(" ")}`);
    }
  });

  it("wraps the tagline instead of cutting it at 40 columns", () => {
    // Given: the narrowest layout.
    const text = gridText(renderJockeySelect(0, 40, 60));
    // Then: every word of every tagline is on screen.
    for (const j of JOCKEYS) {
      for (const word of j.tagline.split(" ")) {
        expect(text, `${j.handle}: "${word}" missing`).toContain(word);
      }
    }
  });

  it("marks the selected jockey", () => {
    const text = gridText(renderJockeySelect(2, 80, 50));
    const marked = text.split("\n").filter((l) => l.includes(">"));
    expect(marked.length).toBe(1);
    expect(marked[0]).toContain(JOCKEYS[2]!.handle);
  });
});
