/** Matrix node graph renderer (Tier 5).
 *
 * Renders the run's matrix as a vertical ASCII layout:
 * - Each node on its own row (top to bottom = surface to boss)
 * - Highlight current node (▸ marker) + visited nodes (✓ marker)
 * - Show zone + ICE count + reward
 *
 * Layout adapts to grid dimensions (portrait 50×80, landscape 80×50).
 */
import type { Grid, Matrix } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";

/** Render the matrix navigation screen. */
import { EVENT_GLYPHS, EVENT_LABELS, type MatrixEventKind } from "../core/event_matrix.ts";

export function renderMatrix(
  matrix: Matrix,
  currentNodeIndex: number,
  visited: ReadonlyArray<number>,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(grid, Math.max(2, Math.floor((cols - 22) / 2)), 2, "MATRIX — CYBERSPACE", PALETTE.GREEN_NEON);

  // Subtitle: progress
  const progress = `${visited.length}/${matrix.nodes.length} nodes`;
  grid = setText(grid, Math.max(2, cols - progress.length - 2), 4, progress, PALETTE.GRAY_LIGHT);

  // Node list (start at row 6)
  const startY = 6;
  for (let i = 0; i < matrix.nodes.length; i++) {
    const node = matrix.nodes[i];
    if (!node) continue;
    const row = startY + i * 2;
    if (row >= rows - 4) break;
    const isCurrent = i === currentNodeIndex;
    const isVisited = visited.includes(i);
    const isBoss = node.isBoss;
    const eventKind = (node.eventKind ?? "combat") as MatrixEventKind;
    const glyph = EVENT_GLYPHS[eventKind];
    const marker = isCurrent ? "▸" : isVisited ? "✓" : " ";
    const label = `${glyph} [${i}] ${node.zone.toUpperCase()}${isBoss ? " (BOSS)" : ""}`;
    const iceCount = node.iceIds.length;
    const eventLabel = eventKind === "combat" ? "" : ` · ${EVENT_LABELS[eventKind]}`;
    const detail = `${iceCount} ICE · ${node.reward.credits}cr${eventLabel}`;
    const fg = isCurrent ? PALETTE.GREEN_NEON : isVisited ? PALETTE.GRAY_MID : PALETTE.GRAY_LIGHT;
    grid = setText(grid, 4, row, `${marker} ${label}`, fg);
    grid = setText(grid, 8, row + 1, detail, PALETTE.GRAY_DARK);
  }

  // Footer
  const footerRow = rows - 2;
  const status = isCurrentInAdjacent(matrix, currentNodeIndex)
    ? "ENTER: enter | ESC: jack out"
    : "ESC: jack out";
  grid = setText(grid, 2, footerRow, status, PALETTE.YELLOW_AMBER);

  return grid;
}

function isCurrentInAdjacent(matrix: Matrix, idx: number): boolean {
  const node = matrix.nodes[idx];
  return node != null && node.adjacent.length > 0;
}