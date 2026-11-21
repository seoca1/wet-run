/** Mission select screens.
 *
 * `renderMissionList` is the framed Sprawl mission select (ADR-0237 §2). The
 * caller (`main.ts`) formats each mission row, so this module owns only the
 * composition: a Green Grid frame, the header, a ╠═╣ rule under it, and the
 * list centred in the remaining space.
 */
import type { Grid } from "../core/types";
import type { State } from "../core/types";
import { makeGrid } from "../core/grid";
import { PALETTE } from "./palette";
import {
  drawPanel,
  drawPanelSeparator,
  panelInnerRect,
  screenFrameRect,
  setInnerText,
  type PanelRect,
} from "./panel";

export function renderMissionSelectScreen(_state: State | null): Grid {
  return makeGrid(0, 0);
}

/** Where the mission select places its content inside the frame. */
export interface MissionListLayout {
  readonly frame: PanelRect;
  readonly inner: PanelRect;
  /** Row of the ╠═╣ rule between the header and the list. */
  readonly separatorY: number;
  readonly listX: number;
  readonly listY: number;
  /** Last row the list may use (inclusive). */
  readonly listBottom: number;
}

/** Compose the mission list within a screen frame inset one cell from the grid
 * edge (`screenFrameRect`).
 *
 * The header sits at fixed offsets inside the frame (title on the first inner
 * row, key hint two rows below, one column in). The list starts no higher than
 * two rows under the ╠═╣ rule, is centred vertically in
 * the body when it fits, and its column is centred on the widest row.
 */
export function missionListLayout(grid: Grid, rowLabels: readonly string[]): MissionListLayout {
  const frame = screenFrameRect(grid);
  const inner = panelInnerRect(grid, frame);
  const separatorY = inner.y + 3;
  const bodyTop = separatorY + 2;
  const listBottom = inner.y + inner.height - 1;
  const spare = listBottom - bodyTop + 1 - rowLabels.length;
  const widest = rowLabels.reduce((w, label) => Math.max(w, label.length + 2), 0);
  return {
    frame,
    inner,
    separatorY,
    listX: inner.x + Math.max(3, Math.floor((inner.width - widest) / 2)),
    listY: bodyTop + Math.max(0, Math.floor(spare / 2)),
    listBottom,
  };
}

/** Word-wrap to `width`, at most `maxLines` lines. */
/** Greedy wrap. When the text does not fit in `maxLines`, the last line ends
 * with `…` so the screen says there is more (2026-11-17: the briefings became
 * full sentences and outgrew the three-line preview; a preview that stops
 * mid-sentence without a mark reads as the whole story). */
function wrap(text: string, width: number, maxLines: number): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let current = "";
  for (let i = 0; i < words.length; i += 1) {
    const word = words[i] ?? "";
    const next = current === "" ? word : `${current} ${word}`;
    if (next.length > width && current !== "") {
      lines.push(current);
      current = word;
      if (lines.length === maxLines) {
        // A word is still waiting, so mark the cut. `…` needs its own column.
        const last = (lines[lines.length - 1] ?? "")
          .slice(0, Math.max(1, width - 1))
          .replace(/ $/, "");
        lines[lines.length - 1] = `${last}…`;
        return lines;
      }
    } else {
      current = next;
    }
  }
  if (current !== "") lines.push(current);
  return lines.slice(0, maxLines);
}

/** Render the framed mission select from pre-formatted row labels.
 *
 * ADR-0316: the selected mission's `briefing` (lifted from the derivative
 * fiction) is shown under the list, wrapped, so the screen says what the
 * mission is about instead of only its title and grade. */
export function renderMissionList(
  rowLabels: readonly string[],
  selected: number,
  cols: number,
  rows: number,
  briefing: string | null = null,
  /** ADR-0318: what picking this mission starts — a contract of three missions,
   * in these grades. The row above shows a grade; a grade is now the whole
   * contract's shape, so the choice says what it costs. */
  contract: string | null = null,
): Grid {
  let grid = makeGrid(cols, rows);
  const layout = missionListLayout(grid, rowLabels);
  const { inner } = layout;
  grid = setInnerText(
    grid,
    inner,
    inner.x + 1,
    inner.y,
    "WET RUN — Select Mission",
    PALETTE.GREEN_NEON,
  );
  const hint = "↑↓: navigate | ENTER: launch | ESC: back";
  const shortHint = "↑↓ pick · ENTER launch · ESC back";
  grid = setInnerText(
    grid,
    inner,
    inner.x + 1,
    inner.y + 2,
    hint.length <= inner.width - 2 ? hint : shortHint,
    PALETTE.GRAY_LIGHT,
  );
  // Reserve the bottom rows — the contract's shape, then the briefing — before
  // placing the list.
  const contractLine =
    contract !== null && contract !== "" && contract.length <= inner.width - 4 ? contract : null;
  const briefLines =
    briefing !== null && briefing !== "" ? wrap(briefing, Math.max(16, inner.width - 4), 3) : [];
  const blockRows = (contractLine !== null ? 1 : 0) + briefLines.length;
  const briefTop = inner.y + inner.height - (blockRows > 0 ? blockRows + 1 : 0);
  const listBottom = Math.min(layout.listBottom, blockRows > 0 ? briefTop - 2 : layout.listBottom);
  for (let i = 0; i < rowLabels.length; i++) {
    const y = layout.listY + i;
    if (y > listBottom) break;
    const isSelected = i === selected;
    const fg = isSelected ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
    const marker = isSelected ? "▸" : " ";
    const row = `${marker} ${rowLabels[i]}`;
    grid = setInnerText(grid, inner, layout.listX, y, row, fg);
  }
  if (contractLine !== null) {
    grid = setInnerText(grid, inner, inner.x + 2, briefTop, contractLine, PALETTE.YELLOW_AMBER);
  }
  briefLines.forEach((line, i) => {
    grid = setInnerText(
      grid,
      inner,
      inner.x + 2,
      briefTop + (contractLine !== null ? 1 : 0) + i,
      line,
      PALETTE.GRAY_LIGHT,
    );
  });
  grid = drawPanel(grid, layout.frame).grid;
  return drawPanelSeparator(grid, layout.frame, layout.separatorY);
}
