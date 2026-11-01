/** Matrix operation board renderer (ADR-0249, inside the ADR-0237 frame).
 *
 * One screen, no camera and no scrolling: the generated rooms are drawn where
 * the dungeon generator placed them, `@` holds the current position, `◆` the
 * boss, and every corridor is an adjacency from `MatrixNode.adjacent`. The
 * targeted neighbour is highlighted; the card under the board details it.
 * The reducer's arrow / Enter semantics are unchanged; this only draws them.
 */
import type { Grid, Matrix, Ice } from "../core/types";
import { makeGrid } from "../core/grid";
import { PALETTE } from "./palette";
import {
  CARD_ROWS,
  matrixCardLines,
  type MatrixPosition,
} from "./matrix_nodes";
import {
  drawPanel,
  panelInnerRect,
  screenFrameRect,
  type PanelRect,
} from "./panel";
import { EVENT_LABELS, type MatrixEventKind } from "../core/event_matrix";
import { planBoard, type BoardPlan } from "./matrix_board_layout";
import { routeCorridors, type CorridorSet } from "./matrix_board_routes";
import { BOARD_LEGEND, drawBoard, putInside } from "./matrix_board";
import { MATRIX_ENTRY_HINT_LINES } from "../core/state/onboarding";
import { drawTravelBoard, type MatrixTravelFrame } from "./matrix_travel";

/** Width reserved for the right-hand CURRENT NODE column (ICE name cap). */
const PREVIEW_WIDTH = 22;
/** Blank columns between the card and the CURRENT NODE column. */
const PREVIEW_GAP = 4;
/** Card width cap; the 40-column frame narrows it. */
const CARD_WIDTH = 36;
/** Rows outside the board: title, gap, progress, legend x2, gap, card. */
const FIXED_ROWS = 6 + CARD_ROWS;

/** Where the matrix screen places its content inside the Green Grid frame. */
export interface MatrixLayout {
  readonly frame: PanelRect;
  readonly inner: PanelRect;
  readonly titleY: number;
  readonly progressY: number;
  readonly board: BoardPlan;
  readonly corridors: CorridorSet;
  readonly legendY: number;
  readonly cardX: number;
  readonly cardY: number;
  readonly cardWidth: number;
  /** CURRENT NODE column, or null when the frame is too narrow for it. */
  readonly previewX: number | null;
  /** Last inner row, holding the controls footer. */
  readonly footerY: number;
}

/** Compose the board, legend and card inside the inset frame (ADR-0237 §2).
 * The block is centred; the board gets every row the fixed rows leave. */
export function matrixLayout(grid: Grid, matrix: Matrix): MatrixLayout {
  const frame = screenFrameRect(grid);
  const inner = panelInnerRect(grid, frame);
  const footerY = inner.y + inner.height - 1;
  const available = Math.max(0, footerY - 1 - inner.y);
  const sizing = planBoard(matrix, inner, 0, available - FIXED_ROWS);
  const block = sizing.rect.height + FIXED_ROWS;
  const titleY = inner.y + Math.max(0, Math.floor((available - block) / 2));
  const board = planBoard(matrix, inner, titleY + 3, available - FIXED_ROWS);
  const cardWidth = Math.max(2, Math.min(CARD_WIDTH, inner.width - 2));
  const hasPreview =
    inner.width >= CARD_WIDTH + PREVIEW_GAP + PREVIEW_WIDTH + 2;
  const blockWidth = cardWidth + (hasPreview ? PREVIEW_GAP + PREVIEW_WIDTH : 0);
  const cardX =
    inner.x + Math.max(1, Math.floor((inner.width - blockWidth) / 2));
  const legendY = board.rect.y + board.rect.height;
  return {
    frame,
    inner,
    titleY,
    progressY: titleY + 2,
    board,
    corridors: routeCorridors(matrix, board),
    legendY,
    cardX,
    cardY: legendY + BOARD_LEGEND.length + 1,
    cardWidth,
    previewX: hasPreview ? cardX + cardWidth + PREVIEW_GAP : null,
    footerY,
  };
}

/** The controls footer names what ENTER does now (ADR-0250 decision 5): a
 * target with unresolved ICE is entered as an encounter, a free target is
 * travel, and at rest Enter enters unresolved ICE here. ESC is JACK OUT on
 * the board, which ends the run. `target` is null at rest. */
export function matrixFooter(
  innerWidth: number,
  hereGates: boolean,
  target: boolean | null,
): string {
  const [short, long] =
    target === null
      ? hereGates
        ? [
            "ENTER ICE | ↑↓ route | ESC jack out",
            "ENTER: enter ICE | ↑↓: pick route | ESC: jack out",
          ]
        : ["↑↓ pick route | ESC jack out", "↑↓: pick route | ESC: jack out"]
      : target
        ? [
            "ENTER ICE | ↑↓ route | ESC jack out",
            "ENTER: enter ICE | ↑↓: route | ESC: jack out",
          ]
        : [
            "ENTER travel | ↑↓ | ESC jack out",
            "ENTER: travel | ↑↓: route | ESC: jack out",
          ];
  // The footer starts one cell inside the frame.
  return innerWidth < 40 || long.length > innerWidth - 1 ? short : long;
}

/** Render the Matrix operation board. Pure: same inputs, same grid.
 *
 * Content is clipped to the frame's inner rectangle and the frame is drawn
 * last, so nothing can erase a rail. `travel` is one frame of the visual
 * traversal into `currentNodeIndex` (the state has already moved); a frame
 * for any other destination is ignored, and null draws the static board.
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
  entryHint = false,
  travel: MatrixTravelFrame | null = null,
  bypassed: readonly number[] = [],
): Grid {
  const gates = (i: number): boolean =>
    (matrix.nodes[i]?.iceIds.length ?? 0) > 0 &&
    !cleared.includes(i) &&
    !bypassed.includes(i);
  let grid = makeGrid(cols, rows);
  const layout = matrixLayout(grid, matrix);
  const { inner, footerY } = layout;
  const position: MatrixPosition = {
    matrix,
    current: currentNodeIndex,
    visited,
    cleared,
    selected: selectedNodeIndex,
  };
  const put = (x: number, y: number, text: string, fg: string): void => {
    if (y < footerY) grid = putInside(grid, inner, x, y, text, fg);
  };

  const title = "MATRIX — CYBERSPACE";
  put(
    inner.x + Math.max(1, Math.floor((inner.width - title.length) / 2)),
    layout.titleY,
    title,
    PALETTE.GREEN_NEON,
  );
  const progress = `${visited.length}/${matrix.nodes.length} nodes`;
  const right = Math.max(
    layout.board.rect.x + layout.board.rect.width,
    layout.cardX + layout.cardWidth,
  );
  put(
    Math.max(
      inner.x + 1,
      Math.min(inner.x + inner.width - 1, right) - progress.length,
    ),
    layout.progressY,
    progress,
    PALETTE.GRAY_LIGHT,
  );

  const clip: PanelRect = { ...inner, height: Math.max(0, footerY - inner.y) };
  grid =
    travel !== null && travel.to === currentNodeIndex
      ? drawTravelBoard(
          grid,
          clip,
          layout.board,
          layout.corridors,
          position,
          travel,
        )
      : drawBoard(grid, clip, layout.board, layout.corridors, position);
  BOARD_LEGEND.forEach((line, k) =>
    put(layout.cardX, layout.legendY + k, line, PALETTE.GRAY_LIGHT),
  );
  // While `@` is still in the corridor the card must agree with the board:
  // it shows the move as confirmed (origin `@`, destination targeted).
  const cardPosition: MatrixPosition =
    travel?.phase === "transit" && travel.to === currentNodeIndex
      ? { ...position, current: travel.from, selected: travel.to }
      : position;
  matrixCardLines(cardPosition, layout.cardWidth).forEach((line, k) =>
    put(layout.cardX, layout.cardY + k, line.text, line.fg),
  );

  // One-time entry hint: one blank row under the card when there is room,
  // else flush above the footer; never over the card.
  if (entryHint) {
    const first = Math.min(
      layout.cardY + CARD_ROWS + 1,
      footerY - MATRIX_ENTRY_HINT_LINES.length,
    );
    MATRIX_ENTRY_HINT_LINES.forEach((line, k) => {
      if (first + k >= layout.cardY + CARD_ROWS)
        put(layout.cardX, first + k, line, PALETTE.YELLOW_AMBER);
    });
  }

  // Optional ICE preview for a cleared current node (run_screen decides).
  if (icePreview && layout.previewX !== null) {
    const x = layout.previewX;
    const y = layout.cardY;
    const node = matrix.nodes[currentNodeIndex];
    put(x, y, "── CURRENT NODE ──", PALETTE.GRAY_LIGHT);
    put(x, y + 1, icePreview.name.slice(0, PREVIEW_WIDTH), PALETTE.ICE_BLUE);
    put(
      x,
      y + 2,
      `HP:  ${node?.iceHp[0]?.toString() ?? "—"}`,
      PALETTE.GREEN_NEON,
    );
    if (node) {
      const eventKind: MatrixEventKind = node.eventKind ?? "combat";
      put(x, y + 3, `Evt: ${EVENT_LABELS[eventKind]}`, PALETTE.YELLOW_AMBER);
      put(x, y + 4, `Rew: ${node.reward.credits}cr`, PALETTE.CYAN_LIGHT);
    }
  }

  const status = matrixFooter(
    inner.width,
    gates(currentNodeIndex),
    selectedNodeIndex === null ? null : gates(selectedNodeIndex),
  );
  grid = putInside(
    grid,
    inner,
    inner.x + 1,
    footerY,
    status,
    PALETTE.YELLOW_AMBER,
  );

  // Frame last, so an overlong label can never erase a rail.
  return drawPanel(grid, layout.frame).grid;
}
