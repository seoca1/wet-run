/** Graphic novel — text utilities.
 *
 * Mirrors wet_run/prototype/src/wet_run/engine/gn_render/text.py:
 *   - toRoman: 1..12 → roman numerals
 *   - wrapTextForNovel: word-wrap to page width minus margins
 *   - paginateLines: chunk wrapped lines into pages
 *   - computeTypedPageIndex: pick page by typed-cursor progress
 *   - dialogueTypedChars: chars revealed at elapsed time
 *   - sceneProgress: chain 0.0..1.0 progress
 *   - characterLabel: localized chapter-card label
 */

import type { Language } from "./graphic_novel_types.ts";

export const NOVEL_LEFT_MARGIN = 2;
export const NOVEL_RIGHT_MARGIN = 2;
export const MS_PER_CHAR = 30; // typing effect speed
export const DEFAULT_PAGE_WIDTH = 80;
export const DEFAULT_LINES_PER_PAGE = 20;

const ROMAN: ReadonlyArray<string> = Object.freeze([
  "I", "II", "III", "IV", "V", "VI",
  "VII", "VIII", "IX", "X", "XI", "XII",
]);

/** Convert 1..12 to roman numerals; falls back to Arabic for larger values. */
export function toRoman(n: number): string {
  if (Number.isInteger(n) && n >= 1 && n <= ROMAN.length) {
    return ROMAN[n - 1] ?? String(n);
  }
  return String(n);
}

/** Word-wrap prose to a list of lines that fit the novel page. */
export function wrapTextForNovel(
  text: string,
  options: {
    readonly width?: number;
    readonly leftMargin?: number;
    readonly rightMargin?: number;
  } = {},
): ReadonlyArray<string> {
  const width = options.width ?? DEFAULT_PAGE_WIDTH;
  const leftMargin = options.leftMargin ?? NOVEL_LEFT_MARGIN;
  const rightMargin = options.rightMargin ?? NOVEL_RIGHT_MARGIN;
  const usable = Math.max(10, width - leftMargin - rightMargin);
  const lines: string[] = [];
  for (const paragraph of text.split("\n")) {
    if (!paragraph.trim()) {
      lines.push("");
      continue;
    }
    let current = "";
    for (const word of paragraph.split(" ")) {
      const candidate = current.length === 0 ? word : `${current} ${word}`;
      if (candidate.length > usable && current.length > 0) {
        lines.push(current);
        current = word;
      } else {
        current = candidate;
      }
    }
    if (current.length > 0) lines.push(current);
  }
  return Object.freeze(lines);
}

/** Split wrapped lines into pages; never splits a non-empty line across pages. */
export function paginateLines(
  lines: ReadonlyArray<string>,
  linesPerPage: number,
  options: { readonly blankSeparator?: boolean } = {},
): ReadonlyArray<ReadonlyArray<string>> {
  const blankSeparator = options.blankSeparator ?? true;
  if (linesPerPage <= 0) return Object.freeze([lines]);
  const pages: string[][] = [];
  let current: string[] = [];
  for (const line of lines) {
    if (current.length >= linesPerPage && current.length > 0) {
      pages.push(current);
      current = [];
      if (blankSeparator && line.length > 0) current.push("");
    }
    current.push(line);
  }
  if (current.length > 0) pages.push(current);
  if (pages.length === 0) pages.push([]);
  return Object.freeze(pages.map((p) => Object.freeze([...p])));
}

/** Determine which page is visible given how many characters have been typed. */
export function computeTypedPageIndex(
  pages: ReadonlyArray<ReadonlyArray<string>>,
  typedChars: number,
): number {
  if (pages.length === 0) return 0;
  let cumulative = 0;
  for (let i = 0; i < pages.length; i++) {
    const page = pages[i];
    if (page === undefined) continue;
    const pageChars = page.reduce((sum, line) => sum + line.length, 0)
      + Math.max(0, page.length - 1);
    cumulative += pageChars;
    if (typedChars <= cumulative) return i;
  }
  return pages.length - 1;
}

/** How many characters of a dialogue are revealed given elapsed time. */
export function dialogueTypedChars(
  durationMs: number,
  elapsedMs: number,
  totalChars: number,
): number {
  if (durationMs <= 0) return totalChars;
  if (totalChars <= 0) return 0;
  return Math.min(Math.floor(elapsedMs / MS_PER_CHAR), totalChars);
}

/** Overall chain progress (0.0..1.0). */
export function sceneProgress(chainIndex: number, chainLength: number): number {
  if (chainLength === 0) return 0;
  return Math.min(chainIndex / chainLength, 1.0);
}

/** Localized character label for chapter cards. */
export function characterLabel(characterId: string, lang: Language): string {
  const labels: Readonly<Record<string, Readonly<Record<Language, string>>>> = {
    novice: { en: "Case (K) — Novice", ko: "케이 (K) — Novice" },
    veteran: { en: "Marly (Sil) — Veteran", ko: "실 (Sil) — Veteran" },
    heretic: { en: "Kumiko (Kas) — Heretic", ko: "카스 (Kas) — Heretic" },
    suit: { en: "Suit — Corporate (3인칭)", ko: "스위트 — 기업 픽서 (3인칭)" },
    wigan: { en: "Wigan — Vodou Construct", ko: "위건 — 부두 construct" },
    angie: { en: "Angie — Loa Receiver", ko: "앤지 — 로아 수신자" },
    sally: { en: "Sally — Market Operator", ko: "샐리 — 시장 운영자" },
    "3jane": { en: "3Jane — Family Heir", ko: "3Jane — 가족의 후계자" },
    neuromancer: { en: "Neuromancer — Merged AI", ko: "뉴로맨서 — 합체된 AI" },
  };
  return labels[characterId]?.[lang] ?? characterId;
}