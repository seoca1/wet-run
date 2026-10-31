/** Matrix node graph renderer (Tier 5.5+).
 *
 * Renders the run's matrix as a vertical ASCII layout:
 * - Each node on its own row (top to bottom = surface to boss)
 * - Highlight current node (▸ marker) + visited nodes (✓ marker)
 * - Zone color coding (surface=green, mid=yellow, deep=red, core=magenta, boss=purple)
 * - Current node shows ICE preview (name + HP) in right HUD panel
 * - Layout adapts to grid dimensions (portrait 50×80, landscape 80×50)
 * - ADR-0237 §2: content composed inside an inset Green Grid frame (panel.ts)
 */
import type { Grid, Matrix, ZoneDepth, Ice } from "../core/types";
import { makeGrid, setText } from "../core/grid";
import { PALETTE } from "./palette";
import { formatNavIndex } from "./nav_index";
import {
  clipToInner,
  drawPanel,
  panelInnerRect,
  screenFrameRect,
  type PanelRect,
} from "./panel";
import {
  EVENT_GLYPHS,
  EVENT_LABELS,
  type MatrixEventKind,
} from "../core/event_matrix";

/** Zone-to-color mapping for visual differentiation.
 *
 * - surface (low danger): green (safe)
 * - mid (moderate): yellow (caution)
 * - deep (danger): red (warning)
 * - core (high danger): magenta (intense)
 * - core-deep (boss): boss-pulse color (high intensity)
 */
function zoneColor(zone: ZoneDepth): string {
  switch (zone) {
    case "surface":
      return PALETTE.GREEN_NEON;
    case "mid":
      return PALETTE.YELLOW_AMBER;
    case "deep":
      return PALETTE.RED_BRIGHT;
    case "core":
      return PALETTE.MAGENTA_NEON;
    case "core-deep":
      return PALETTE.MAGENTA_NEON;
    default:
      return PALETTE.GRAY_LIGHT;
  }
}

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
  /** Column of the node marker; node detail lines sit four columns right. */
  readonly listX: number;
  /** Row of the first node; each node takes two rows (label, detail). */
  readonly listY: number;
  /** CURRENT NODE column, or null on grids narrower than 50 columns. */
  readonly previewX: number | null;
  /** Exclusive right edge of the composed block (progress right-aligns here). */
  readonly blockRight: number;
  /** Last inner row, holding the controls footer. */
  readonly footerY: number;
}

interface NodeRow {
  readonly label: string;
  readonly detail: string;
}

function nodeRows(matrix: Matrix): NodeRow[] {
  return matrix.nodes.map((node, i) => {
    const eventKind = (node.eventKind ?? "combat") as MatrixEventKind;
    const glyph = EVENT_GLYPHS[eventKind];
    const label = `${glyph} ${formatNavIndex(i)} ${node.zone.toUpperCase()}${node.isBoss ? " (BOSS)" : ""}`;
    const eventLabel =
      eventKind === "combat" ? "" : ` · ${EVENT_LABELS[eventKind]}`;
    const detail = `${node.iceIds.length} ICE · ${node.reward.credits}cr${eventLabel}`;
    return { label, detail };
  });
}

/** Compose the matrix screen inside an inset frame (ADR-0237 §2).
 *
 * The frame leaves a one-cell gutter to the canvas edge. The node list and
 * the CURRENT NODE column are centred together horizontally; the column is
 * reserved on every grid of 50+ columns so the list does not shift between
 * nodes with and without ICE. The title-to-last-node block is centred
 * vertically above the footer, which sits on the last inner row.
 */
export function matrixLayout(grid: Grid, matrix: Matrix): MatrixLayout {
  const frame = screenFrameRect(grid);
  const inner = panelInnerRect(grid, frame);
  const innerRight = inner.x + inner.width;
  const footerY = inner.y + inner.height - 1;

  const listWidth = nodeRows(matrix).reduce(
    (widest, row) =>
      Math.max(widest, row.label.length + 2, row.detail.length + 4),
    0,
  );
  const hasPreview = grid.width >= 50;
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

  const blockRows = HEADER_ROWS + matrix.nodes.length * 2;
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

/** Render the matrix navigation screen with zone color coding + ICE preview.
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

  // Node list (2 rows per node), kept one blank row clear of the footer
  const labels = nodeRows(matrix);
  for (let i = 0; i < matrix.nodes.length; i++) {
    const node = matrix.nodes[i];
    const text = labels[i];
    if (!node || !text) continue;
    const row = listY + i * 2;
    if (row + 1 >= footerY - 1) break;
    const isCurrent = i === currentNodeIndex;
    const isVisited = visited.includes(i);
    // Adjacent = graph neighbours of the current node (the matrix is a
    // graph, not a linear chain).
    const isAdjacent =
      !isCurrent &&
      !isVisited &&
      (matrix.nodes[currentNodeIndex]?.adjacent.includes(i) ?? false);
    // Marker: ▸ current, ✓ visited, → adjacent (caret), space otherwise
    const marker = isCurrent ? "▸" : isVisited ? "✓" : isAdjacent ? "→" : " ";
    // Color: current=highlighted, visited=faded, adjacent=zone (available), rest=zone faded
    const baseColor = zoneColor(node.zone);
    const fg = isCurrent
      ? PALETTE.GREEN_NEON
      : isVisited
        ? PALETTE.GRAY_MID
        : isAdjacent
          ? baseColor
          : PALETTE.GRAY_DARK;
    grid = put(grid, inner, listX, row, `${marker} ${text.label}`, fg);
    grid = put(
      grid,
      inner,
      listX + 4,
      row + 1,
      text.detail,
      isVisited ? PALETTE.GRAY_DARK : baseColor,
    );
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
      const eventKind = (node.eventKind ?? "combat") as MatrixEventKind;
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
  const status = isCurrentInAdjacent(matrix, currentNodeIndex)
    ? "ENTER: enter node | ESC: back"
    : "ESC: back";
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

function isCurrentInAdjacent(matrix: Matrix, idx: number): boolean {
  const node = matrix.nodes[idx];
  return node != null && node.adjacent.length > 0;
}
