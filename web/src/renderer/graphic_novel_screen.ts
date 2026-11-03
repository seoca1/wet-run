/** Graphic novel composition from already-resolved story data. */
import { makeGrid, setText, type Grid } from "../core/grid";
import {
  computeTypedPageIndex,
  paginateLines,
  toRoman,
  wrapTextForNovel,
} from "../core/graphic_novel/graphic_novel_text";
import { PALETTE } from "./palette";

export interface GraphicNovelView {
  readonly chapter: {
    readonly order: number;
    readonly title: string;
    readonly speaker: string;
  } | null;
  readonly text: string;
  readonly dialogueText: string | null;
  readonly progress: number;
  readonly isPaused: boolean;
  /** ADR-0273: the chain finished — the screen offers the run that follows. */
  readonly done?: boolean;
}

/** Original dialogue area and footer rows, including the 15-line page size. */
export function graphicNovelLayout(cols: number, rows: number) {
  return {
    x: 2,
    textY: 8,
    textBottom: rows - 2,
    wrapWidth: cols - 4,
    linesPerPage: 15,
    statusY: rows - 2,
    hintY: rows - 1,
  } as const;
}

/** Render the current typed page; story loading and playback stay in the controller. */
export function renderGraphicNovelScreen(
  view: GraphicNovelView,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);
  const layout = graphicNovelLayout(cols, rows);
  grid = setText(grid, 2, 1, "GRAPHIC NOVEL", PALETTE.GREEN_NEON);
  if (view.chapter) {
    grid = setText(
      grid,
      2,
      3,
      `Chapter: ${toRoman(view.chapter.order)}`,
      PALETTE.GRAY_LIGHT,
    );
    grid = setText(
      grid,
      2,
      4,
      `Speaker: ${view.chapter.speaker}`,
      PALETTE.YELLOW_AMBER,
    );
    grid = setText(
      grid,
      2,
      5,
      `Title: ${view.chapter.title}`,
      PALETTE.GRAY_LIGHT,
    );
  }
  const wrapped = wrapTextForNovel(view.text, { width: layout.wrapWidth });
  const paginated = paginateLines(wrapped, layout.linesPerPage);
  const typedChars = view.dialogueText !== null ? view.dialogueText.length : 0;
  const pageIndex = computeTypedPageIndex(paginated, typedChars);
  const page = paginated[pageIndex] ?? [];
  let y: number = layout.textY;
  for (const line of page) {
    if (y >= layout.textBottom) break;
    grid = setText(grid, 2, y, line, PALETTE.FOREGROUND);
    y += 1;
  }
  const statusText = view.isPaused ? "PAUSED" : "PLAYING";
  grid = setText(
    grid,
    2,
    layout.statusY,
    `[${statusText}] Progress: ${Math.round(view.progress * 100)}%`,
    PALETTE.GRAY_DARK,
  );
  return setText(
    grid,
    2,
    layout.hintY,
    view.done === true
      ? "ENTER: start a run | ESC: exit"
      : "ENTER: continue | TAB: pause | ESC: exit",
    PALETTE.GRAY_DARK,
  );
}
