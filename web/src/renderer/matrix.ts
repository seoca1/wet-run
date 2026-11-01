/** Matrix node graph renderer (Tier 5.5+).
 *
 * Renders the run's matrix as a vertical ASCII layout:
 * - Current position, boxed frontier, objective and depth groups
 * - Highlight current node (▸ marker) + visited nodes (✓ marker)
 * - Zone depth groups; states are labelled independently of palette mode
 * - Current node shows ICE preview (name + HP) in right HUD panel
 * - Layout adapts to grid dimensions (portrait 50×80, landscape 80×50)
 * - ADR-0237 §2: content composed inside an inset Green Grid frame (panel.ts)
 */
import type { Grid, Matrix, Ice } from "../core/types";
import { makeGrid, setText } from "../core/grid";
import { PALETTE } from "./palette";
import { matrixNodeLines } from "./matrix_nodes";
import {
  clipToInner,
  drawPanel,
  panelInnerRect,
  screenFrameRect,
  type PanelRect,
} from "./panel";
import { EVENT_LABELS, type MatrixEventKind } from "../core/event_matrix";

/** Width reserved for the right-hand CURRENT NODE column (ICE name cap). */
const PREVIEW_WIDTH = 22;
/** Blank columns between the node list and the CURRENT NODE column. */
const PREVIEW_GAP = 6;
/** Rows from the title to the first node row: title, gap, progress, gap. */
const HEADER_ROWS = 4;

/** Where the matrix screen places its content inside the Green Grid frame. */
export interface MatrixLayout {
  readonly frame: PanelRect;
  readonly inner: PanelRect;
  readonly titleY: number;
  readonly progressY: number;
  /** Column of the position block and frontier's left rail. */
  readonly listX: number;
  /** First row of the position / frontier / objective / depth stack. */
  readonly listY: number;
  /** CURRENT NODE column, or null on grids narrower than 50 columns. */
  readonly previewX: number | null;
  /** Exclusive right edge of the composed block (progress right-aligns here). */
  readonly blockRight: number;
  /** Last inner row, holding the controls footer. */
  readonly footerY: number;
}

/** Compose the matrix screen inside an inset frame (ADR-0237 §2).
 *
 * The frame leaves a one-cell gutter to the canvas edge. The node list and
 * the CURRENT NODE column are centred together horizontally; the column is
 * reserved whenever both columns fit so the list does not shift between
 * nodes with and without ICE. Compact grids give the stack priority over
 * whitespace; the controls footer stays on the last inner row.
 */
export function matrixLayout(grid: Grid, matrix: Matrix): MatrixLayout {
  const frame = screenFrameRect(grid);
  const inner = panelInnerRect(grid, frame);
  const innerRight = inner.x + inner.width;
  const footerY = inner.y + inner.height - 1;

  const listWidth = Math.max(2, Math.min(36, inner.width - 2));
  const hasPreview =
    grid.width >= 50 &&
    inner.width >= listWidth + PREVIEW_GAP + PREVIEW_WIDTH + 2;
  const blockWidth = listWidth + (hasPreview ? PREVIEW_GAP + PREVIEW_WIDTH : 0);
  const listX =
    inner.x + Math.max(1, Math.floor((inner.width - blockWidth) / 2));
  const previewX = hasPreview
    ? Math.max(
        listX + 1,
        Math.min(
          listX + listWidth + PREVIEW_GAP,
          innerRight - 1 - PREVIEW_WIDTH,
        ),
      )
    : null;
  const blockRight = Math.min(
    innerRight - 1,
    previewX !== null ? previewX + PREVIEW_WIDTH : listX + listWidth,
  );

  const blockRows = HEADER_ROWS + Math.min(32, 12 + matrix.nodes.length * 2);
  const available = footerY - 1 - inner.y;
  const titleY = inner.y + Math.max(1, Math.floor((available - blockRows) / 2));
  return {
    frame,
    inner,
    titleY,
    progressY: titleY + 2,
    listX,
    listY: titleY + HEADER_ROWS,
    previewX,
    blockRight,
    footerY,
  };
}

/** Render the matrix navigation screen with labelled route groups + ICE preview.
 *
 * Content is placed by `matrixLayout` and the frame is drawn last, so an
 * overlong label is clipped by a rail instead of erasing it.
 */
export function renderMatrix(
  matrix: Matrix,
  currentNodeIndex: number,
  visited: ReadonlyArray<number>,
  cols: number,
  rows: number,
  icePreview: Ice | null = null,
  selectedNodeIndex: number | null = null,
  cleared: readonly number[] = [],
): Grid {
  let grid = makeGrid(cols, rows);
  const layout = matrixLayout(grid, matrix);
  const { inner, listX, listY, footerY } = layout;

  // Title
  const title = "MATRIX — CYBERSPACE";
  grid = put(
    grid,
    inner,
    inner.x + Math.max(1, Math.floor((inner.width - title.length) / 2)),
    layout.titleY,
    title,
    PALETTE.GREEN_NEON,
  );

  // Subtitle: progress, right-aligned to the composed block
  const progress = `${visited.length}/${matrix.nodes.length} nodes`;
  grid = put(
    grid,
    inner,
    Math.max(inner.x + 1, layout.blockRight - progress.length),
    layout.progressY,
    progress,
    PALETTE.GRAY_LIGHT,
  );

  const lines = matrixNodeLines(
    {
      matrix,
      current: currentNodeIndex,
      visited,
      cleared,
      selected: selectedNodeIndex,
    },
    Math.max(2, Math.min(36, inner.width - 2)),
    footerY - 1 - listY,
  );
  for (const [offset, line] of lines.entries()) {
    if (listY + offset >= footerY - 1) break;
    grid = put(grid, inner, listX, listY + offset, line.text, line.fg);
  }

  // ICE preview panel (right column, current node)
  if (icePreview && layout.previewX !== null) {
    const previewX = layout.previewX;
    const previewY = listY;
    grid = put(
      grid,
      inner,
      previewX,
      previewY,
      "── CURRENT NODE ──",
      PALETTE.GRAY_LIGHT,
    );
    const iceName = icePreview.name.slice(0, PREVIEW_WIDTH);
    grid = put(grid, inner, previewX, previewY + 1, iceName, PALETTE.ICE_BLUE);
    const node = matrix.nodes[currentNodeIndex];
    const hpStr = node?.iceHp[0]?.toString() ?? "—";
    grid = put(
      grid,
      inner,
      previewX,
      previewY + 2,
      `HP:  ${hpStr}`,
      PALETTE.GREEN_NEON,
    );
    if (node) {
      const eventKind: MatrixEventKind = node.eventKind ?? "combat";
      grid = put(
        grid,
        inner,
        previewX,
        previewY + 3,
        `Evt: ${EVENT_LABELS[eventKind]}`,
        PALETTE.YELLOW_AMBER,
      );
      grid = put(
        grid,
        inner,
        previewX,
        previewY + 4,
        `Rew: ${node.reward.credits}cr`,
        PALETTE.CYAN_LIGHT,
      );
    }
  }

  // Footer
  const status =
    inner.width < 40
      ? selectedNodeIndex !== null
        ? "↑↓ route | ENTER travel | ESC back"
        : "↑↓ route | ENTER ICE | ESC back"
      : selectedNodeIndex !== null
        ? "ENTER: travel | ↑↓: route | ESC: back"
        : "ENTER: enter ICE | ↑↓: route | ESC: back";
  grid = put(grid, inner, inner.x + 1, footerY, status, PALETTE.YELLOW_AMBER);

  // Frame last, so an overlong label can never erase a rail.
  return drawPanel(grid, layout.frame).grid;
}

/** Write text clipped to the frame's inner rectangle, so it can reach
 * neither a rail nor the gutter beyond it. */
function put(
  grid: Grid,
  inner: PanelRect,
  x: number,
  y: number,
  text: string,
  fg: string,
): Grid {
  return setText(grid, x, y, clipToInner(inner, x, text), fg);
}
