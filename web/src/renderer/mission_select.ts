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
export function missionListLayout(
  grid: Grid,
  rowLabels: readonly string[],
): MissionListLayout {
  const frame = screenFrameRect(grid);
  const inner = panelInnerRect(grid, frame);
  const separatorY = inner.y + 3;
  const bodyTop = separatorY + 2;
  const listBottom = inner.y + inner.height - 1;
  const spare = listBottom - bodyTop + 1 - rowLabels.length;
  const widest = rowLabels.reduce(
    (w, label) => Math.max(w, label.length + 2),
    0,
  );
  return {
    frame,
    inner,
    separatorY,
    listX: inner.x + Math.max(3, Math.floor((inner.width - widest) / 2)),
    listY: bodyTop + Math.max(0, Math.floor(spare / 2)),
    listBottom,
  };
}

/** Render the framed mission select from pre-formatted row labels. */
export function renderMissionList(
  rowLabels: readonly string[],
  selected: number,
  cols: number,
  rows: number,
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
  grid = setInnerText(
    grid,
    inner,
    inner.x + 1,
    inner.y + 2,
    "↑↓: navigate | ENTER: launch | ESC: back",
    PALETTE.GRAY_LIGHT,
  );
  for (let i = 0; i < rowLabels.length; i++) {
    const y = layout.listY + i;
    if (y > layout.listBottom) break;
    const isSelected = i === selected;
    const fg = isSelected ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
    const marker = isSelected ? "▸" : " ";
    const row = `${marker} ${rowLabels[i]}`;
    grid = setInnerText(grid, inner, layout.listX, y, row, fg);
  }
  grid = drawPanel(grid, layout.frame).grid;
  return drawPanelSeparator(grid, layout.frame, layout.separatorY);
}
