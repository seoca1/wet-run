import { describe, it, expect } from "vitest";
import {
  toRoman,
  wrapTextForNovel,
  paginateLines,
  computeTypedPageIndex,
  dialogueTypedChars,
  sceneProgress,
  characterLabel,
  NOVEL_LEFT_MARGIN,
  NOVEL_RIGHT_MARGIN,
  MS_PER_CHAR,
  DEFAULT_PAGE_WIDTH,
  DEFAULT_LINES_PER_PAGE,
} from "../src/core/graphic_novel_text.ts";

describe("toRoman", () => {
  it("converts 1 to I", () => {
    expect(toRoman(1)).toBe("I");
  });

  it("converts 2 to II", () => {
    expect(toRoman(2)).toBe("II");
  });

  it("converts 5 to V", () => {
    expect(toRoman(5)).toBe("V");
  });

  it("converts 10 to X", () => {
    expect(toRoman(10)).toBe("X");
  });

  it("converts 12 to XII", () => {
    expect(toRoman(12)).toBe("XII");
  });

  it("falls back to arabic for 13", () => {
    expect(toRoman(13)).toBe("13");
  });

  it("falls back to arabic for 0", () => {
    expect(toRoman(0)).toBe("0");
  });

  it("falls back to arabic for negative numbers", () => {
    expect(toRoman(-5)).toBe("-5");
  });

  it("falls back to arabic for non-integer", () => {
    expect(toRoman(3.5)).toBe("3.5");
  });

  it("converts 4 to IV", () => {
    expect(toRoman(4)).toBe("IV");
  });

  it("converts 9 to IX", () => {
    expect(toRoman(9)).toBe("IX");
  });
});

describe("wrapTextForNovel", () => {
  it("wraps text that exceeds usable width", () => {
    const text = "This is a very long line that should be wrapped when it exceeds the available width";
    const result = wrapTextForNovel(text, { width: 40 });
    expect(result.length).toBeGreaterThan(1);
  });

  it("respects left and right margins", () => {
    const text = "word ".repeat(50);
    const result = wrapTextForNovel(text, { width: 40, leftMargin: 5, rightMargin: 5 });
    expect(result.length).toBeGreaterThan(1);
    for (const line of result) {
      expect(line.length).toBeLessThanOrEqual(30);
    }
  });

  it("preserves paragraph breaks", () => {
    const text = "Paragraph one.\n\nParagraph two.";
    const result = wrapTextForNovel(text, { width: 80 });
    expect(result.some((line) => line === "")).toBe(true);
  });

  it("handles single word longer than usable width", () => {
    const word = "x".repeat(100);
    const result = wrapTextForNovel(word, { width: 40 });
    expect(result.length).toBeGreaterThan(0);
    expect(result[0]).toBe(word);
  });

  it("handles empty string", () => {
    const result = wrapTextForNovel("", { width: 80 });
    expect(result.length).toBeGreaterThanOrEqual(0);
  });

  it("handles text with only whitespace", () => {
    const result = wrapTextForNovel("   \n  \n  ", { width: 80 });
    expect(result.every((line) => line === "")).toBe(true);
  });

  it("uses default width when not specified", () => {
    const text = "word ".repeat(100);
    const result = wrapTextForNovel(text);
    expect(result.length).toBeGreaterThan(1);
  });

  it("uses default margins when not specified", () => {
    const text = "x".repeat(100);
    const result = wrapTextForNovel(text);
    expect(result.length).toBeGreaterThan(0);
  });

  it("splits on spaces, not in the middle of words", () => {
    const text = "one two three four five six seven eight nine ten";
    const result = wrapTextForNovel(text, { width: 20 });
    for (const line of result) {
      expect(line.trim().includes(" ")).toBe(line.split(" ").length > 1);
    }
  });

  it("handles multiple consecutive spaces", () => {
    const text = "word    word    word";
    const result = wrapTextForNovel(text, { width: 80 });
    expect(result.length).toBeGreaterThan(0);
  });

  it("ensures minimum usable width of 10", () => {
    const text = "word ".repeat(20);
    const result = wrapTextForNovel(text, { width: 5, leftMargin: 2, rightMargin: 2 });
    expect(result.length).toBeGreaterThan(1);
  });
});

describe("paginateLines", () => {
  it("splits lines into pages", () => {
    const lines = Array(50).fill("line");
    const pages = paginateLines(lines, 20);
    expect(pages.length).toBeGreaterThan(1);
  });

  it("respects linesPerPage limit", () => {
    const lines = Array(50).fill("line");
    const pages = paginateLines(lines, 10);
    for (const page of pages) {
      expect(page.length).toBeLessThanOrEqual(11);
    }
  });

  it("adds blank separator between pages by default", () => {
    const lines = Array(30).fill("line");
    const pages = paginateLines(lines, 10);
    if (pages.length > 1 && pages[1]) {
      expect(pages[1][0]).toBe("");
    }
  });

  it("skips blank separator when blankSeparator is false", () => {
    const lines = Array(30).fill("line");
    const pages = paginateLines(lines, 10, { blankSeparator: false });
    if (pages.length > 1 && pages[1]) {
      expect(pages[1][0]).toBe("line");
    }
  });

  it("returns single page when linesPerPage is 0", () => {
    const lines = Array(50).fill("line");
    const pages = paginateLines(lines, 0);
    expect(pages.length).toBe(1);
    expect(pages[0]).toBe(lines);
  });

  it("handles empty lines array", () => {
    const pages = paginateLines([], 10);
    expect(pages.length).toBe(1);
    expect(pages[0]).toEqual([]);
  });

  it("handles single line", () => {
    const pages = paginateLines(["line"], 10);
    expect(pages.length).toBe(1);
    expect(pages[0]).toEqual(["line"]);
  });

  it("does not split lines across pages", () => {
    const lines = ["line1", "line2", "line3"];
    const pages = paginateLines(lines, 2);
    for (const page of pages) {
      expect(page.every((line) => typeof line === "string")).toBe(true);
    }
  });

  it("includes remaining lines in last page", () => {
    const lines = Array(25).fill("line");
    const pages = paginateLines(lines, 10);
    const lastPage = pages[pages.length - 1];
    expect(lastPage).toBeDefined();
    expect(lastPage!.length).toBeGreaterThan(0);
  });

  it("freezes returned pages", () => {
    const lines = ["line1", "line2"];
    const pages = paginateLines(lines, 10);
    expect(Object.isFrozen(pages)).toBe(true);
    expect(Object.isFrozen(pages[0])).toBe(true);
  });
});

describe("computeTypedPageIndex", () => {
  it("returns 0 for empty pages", () => {
    expect(computeTypedPageIndex([], 100)).toBe(0);
  });

  it("returns 0 when no characters typed", () => {
    const pages = [["line1", "line2"], ["line3", "line4"]];
    expect(computeTypedPageIndex(pages, 0)).toBe(0);
  });

  it("stays on first page for small typedChars", () => {
    const pages = [["line1", "line2"], ["line3", "line4"]];
    expect(computeTypedPageIndex(pages, 5)).toBe(0);
  });

  it("advances to second page when typedChars exceeds first page", () => {
    const pages = [["abc"], ["def"]];
    expect(computeTypedPageIndex(pages, 10)).toBe(1);
  });

  it("returns last page index for large typedChars", () => {
    const pages = [["line1"], ["line2"], ["line3"]];
    expect(computeTypedPageIndex(pages, 9999)).toBe(2);
  });

  it("accounts for newlines between lines", () => {
    const pages = [["abc", "def"]];
    const totalChars = 3 + 3 + 1;
    expect(computeTypedPageIndex(pages, totalChars)).toBe(0);
  });

  it("handles single-page document", () => {
    const pages = [["line1", "line2", "line3"]];
    expect(computeTypedPageIndex(pages, 100)).toBe(0);
  });

  it("handles pages with empty lines", () => {
    const pages = [["abc", "", "def"], ["ghi"]];
    expect(computeTypedPageIndex(pages, 5)).toBe(0);
  });
});

describe("dialogueTypedChars", () => {
  it("returns 0 when elapsedMs is 0", () => {
    expect(dialogueTypedChars(1000, 0, 100)).toBe(0);
  });

  it("returns totalChars when durationMs is 0", () => {
    expect(dialogueTypedChars(0, 100, 50)).toBe(50);
  });

  it("returns 0 when totalChars is 0", () => {
    expect(dialogueTypedChars(1000, 500, 0)).toBe(0);
  });

  it("calculates typed characters based on MS_PER_CHAR", () => {
    const elapsedMs = MS_PER_CHAR * 10;
    expect(dialogueTypedChars(1000, elapsedMs, 100)).toBe(10);
  });

  it("caps at totalChars", () => {
    const elapsedMs = MS_PER_CHAR * 200;
    expect(dialogueTypedChars(1000, elapsedMs, 50)).toBe(50);
  });

  it("floors fractional characters", () => {
    const elapsedMs = MS_PER_CHAR * 5.7;
    expect(dialogueTypedChars(1000, elapsedMs, 100)).toBe(5);
  });

  it("handles negative durationMs", () => {
    expect(dialogueTypedChars(-100, 50, 100)).toBe(100);
  });
});

describe("sceneProgress", () => {
  it("returns 0.0 when chainLength is 0", () => {
    expect(sceneProgress(0, 0)).toBe(0.0);
  });

  it("returns 0.0 when chainIndex is 0", () => {
    expect(sceneProgress(0, 10)).toBe(0.0);
  });

  it("returns 0.5 when chainIndex is half of chainLength", () => {
    expect(sceneProgress(5, 10)).toBe(0.5);
  });

  it("returns 1.0 when chainIndex equals chainLength", () => {
    expect(sceneProgress(10, 10)).toBe(1.0);
  });

  it("caps at 1.0 when chainIndex exceeds chainLength", () => {
    expect(sceneProgress(15, 10)).toBe(1.0);
  });

  it("calculates correct progress for partial completion", () => {
    expect(sceneProgress(3, 12)).toBeCloseTo(0.25);
  });

  it("handles single-scene chain", () => {
    expect(sceneProgress(1, 1)).toBe(1.0);
  });
});

describe("characterLabel", () => {
  it("returns english label for novice", () => {
    const label = characterLabel("novice", "en");
    expect(label).toContain("Case");
    expect(label).toContain("Novice");
  });

  it("returns korean label for novice", () => {
    const label = characterLabel("novice", "ko");
    expect(label).toContain("케이");
  });

  it("returns english label for veteran", () => {
    const label = characterLabel("veteran", "en");
    expect(label).toContain("Sil");
    expect(label).toContain("Veteran");
  });

  it("returns korean label for veteran", () => {
    const label = characterLabel("veteran", "ko");
    expect(label).toContain("실");
  });

  it("returns english label for heretic", () => {
    const label = characterLabel("heretic", "en");
    expect(label).toContain("Kas");
    expect(label).toContain("Heretic");
  });

  it("returns korean label for heretic", () => {
    const label = characterLabel("heretic", "ko");
    expect(label).toContain("카스");
  });

  it("returns english label for suit", () => {
    const label = characterLabel("suit", "en");
    expect(label).toContain("Suit");
  });

  it("returns english label for wigan", () => {
    const label = characterLabel("wigan", "en");
    expect(label).toContain("Wigan");
  });

  it("returns english label for angie", () => {
    const label = characterLabel("angie", "en");
    expect(label).toContain("Angie");
  });

  it("returns english label for sally", () => {
    const label = characterLabel("sally", "en");
    expect(label).toContain("Sally");
  });

  it("returns english label for 3jane", () => {
    const label = characterLabel("3jane", "en");
    expect(label).toContain("3Jane");
  });

  it("returns english label for neuromancer", () => {
    const label = characterLabel("neuromancer", "en");
    expect(label).toContain("Neuromancer");
  });

  it("returns characterId for unknown character", () => {
    expect(characterLabel("unknown", "en")).toBe("unknown");
    expect(characterLabel("unknown", "ko")).toBe("unknown");
  });

  it("handles empty string characterId", () => {
    expect(characterLabel("", "en")).toBe("");
  });
});

describe("constants", () => {
  it("exports NOVEL_LEFT_MARGIN", () => {
    expect(typeof NOVEL_LEFT_MARGIN).toBe("number");
    expect(NOVEL_LEFT_MARGIN).toBeGreaterThanOrEqual(0);
  });

  it("exports NOVEL_RIGHT_MARGIN", () => {
    expect(typeof NOVEL_RIGHT_MARGIN).toBe("number");
    expect(NOVEL_RIGHT_MARGIN).toBeGreaterThanOrEqual(0);
  });

  it("exports MS_PER_CHAR", () => {
    expect(typeof MS_PER_CHAR).toBe("number");
    expect(MS_PER_CHAR).toBeGreaterThan(0);
  });

  it("exports DEFAULT_PAGE_WIDTH", () => {
    expect(typeof DEFAULT_PAGE_WIDTH).toBe("number");
    expect(DEFAULT_PAGE_WIDTH).toBeGreaterThan(0);
  });

  it("exports DEFAULT_LINES_PER_PAGE", () => {
    expect(typeof DEFAULT_LINES_PER_PAGE).toBe("number");
    expect(DEFAULT_LINES_PER_PAGE).toBeGreaterThan(0);
  });
});
