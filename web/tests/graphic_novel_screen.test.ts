import { describe, expect, it } from "vitest";
import {
  graphicNovelLayout,
  renderGraphicNovelScreen,
  type GraphicNovelView,
} from "../src/renderer/graphic_novel_screen";
import { PALETTE } from "../src/renderer/palette";
import { rowText } from "./view_fixtures";

const view: GraphicNovelView = {
  chapter: { order: 4, title: "Night", speaker: "Case" },
  text: "The port is quiet tonight.",
  dialogueText: null,
  progress: 0.236,
  isPaused: false,
};

describe("graphic novel screen", () => {
  it("preserves chapter metadata, dialogue colour and bottom status rows", () => {
    const grid = renderGraphicNovelScreen(view, 80, 50);
    expect(graphicNovelLayout(80, 50)).toEqual({
      x: 2,
      textY: 8,
      textBottom: 48,
      wrapWidth: 76,
      linesPerPage: 15,
      statusY: 48,
      hintY: 49,
    });
    expect(rowText(grid, 3).slice(2).trimEnd()).toBe("Chapter: IV");
    expect(rowText(grid, 4).slice(2).trimEnd()).toBe("Speaker: Case");
    expect(grid.cells[4]?.[2]?.fg).toBe(PALETTE.YELLOW_AMBER);
    expect(rowText(grid, 5).slice(2).trimEnd()).toBe("Title: Night");
    expect(rowText(grid, 8).slice(2).trimEnd()).toBe(view.text);
    expect(grid.cells[8]?.[2]?.fg).toBe(PALETTE.FOREGROUND);
    expect(rowText(grid, 48).slice(2).trimEnd()).toBe(
      "[PLAYING] Progress: 24%",
    );
    expect(rowText(grid, 49).slice(2).trimEnd()).toBe(
      "ENTER: continue | TAB: pause | ESC: exit",
    );
  });

  it("omits absent scene metadata and shows paused status on a short grid", () => {
    const grid = renderGraphicNovelScreen(
      { ...view, chapter: null, isPaused: true, text: "one\ntwo\nthree\nfour" },
      40,
      12,
    );
    expect(rowText(grid, 3).trim()).toBe("");
    expect(rowText(grid, 8).slice(2).trimEnd()).toBe("one");
    expect(rowText(grid, 9).slice(2).trimEnd()).toBe("two");
    expect(rowText(grid, 10).slice(2).trimEnd()).toBe("[PAUSED] Progress: 24%");
    expect(grid.cells[10]?.[2]?.fg).toBe(PALETTE.GRAY_DARK);
  });

  it("selects the page from full dialogue length and retains the blank page separator", () => {
    const text = Array.from({ length: 18 }, (_, i) => `line${i + 1}`).join(
      "\n",
    );
    const grid = renderGraphicNovelScreen(
      { ...view, text, dialogueText: text },
      40,
      30,
    );
    expect(rowText(grid, 8).trim()).toBe("");
    expect(rowText(grid, 9).slice(2).trimEnd()).toBe("line16");
    expect(rowText(grid, 11).slice(2).trimEnd()).toBe("line18");
  });

  it("retains both wrapping margins inside the controller-supplied width", () => {
    const grid = renderGraphicNovelScreen(
      { ...view, text: "aaaa bbbb cccc dddd eeee" },
      24,
      30,
    );
    expect(rowText(grid, 8).slice(2).trimEnd()).toBe("aaaa bbbb cccc");
    expect(rowText(grid, 9).slice(2).trimEnd()).toBe("dddd eeee");
  });
});

describe("ADR-0273 — the graphic novel's exit key", () => {
  it("offers the run that follows once the chain is done", () => {
    const grid = renderGraphicNovelScreen({ ...view, done: true }, 80, 50);
    const text = grid.cells
      .map((r) => r.map((c) => c.char).join(""))
      .join("\n");
    expect(text).toContain("ENTER: start a run");
    expect(text).not.toContain("ENTER: continue");
  });
});
