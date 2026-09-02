/** Matrix node graph renderer (Tier 5.5+).
 *
 * Renders the run's matrix as a vertical ASCII layout:
 * - Each node on its own row (top to bottom = surface to boss)
 * - Highlight current node (▸ marker) + visited nodes (✓ marker)
 * - Zone color coding (surface=green, mid=yellow, deep=red, core=magenta, boss=purple)
 * - Current node shows ICE preview (name + HP) in right HUD panel
 * - Layout adapts to grid dimensions (portrait 50×80, landscape 80×50)
 */
import type { Grid, Matrix, ZoneDepth, Ice } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";
import { EVENT_GLYPHS, EVENT_LABELS, type MatrixEventKind } from "../core/event_matrix.ts";

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

/** Render the matrix navigation screen with zone color coding + ICE preview. */
export function renderMatrix(
  matrix: Matrix,
  currentNodeIndex: number,
  visited: ReadonlyArray<number>,
  cols: number,
  rows: number,
  icePreview: Ice | null = null,
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(grid, Math.max(2, Math.floor((cols - 22) / 2)), 2, "MATRIX — CYBERSPACE", PALETTE.GREEN_NEON);

  // Subtitle: progress
  const progress = `${visited.length}/${matrix.nodes.length} nodes`;
  grid = setText(grid, Math.max(2, cols - progress.length - 2), 4, progress, PALETTE.GRAY_LIGHT);

  // Node list (start at row 6, 2 rows per node)
  const startY = 6;
  for (let i = 0; i < matrix.nodes.length; i++) {
    const node = matrix.nodes[i];
    if (!node) continue;
    const row = startY + i * 2;
    if (row >= rows - 6) break;
    const isCurrent = i === currentNodeIndex;
    const isVisited = visited.includes(i);
    // Adjacent = next step (i = current + 1) or previous step (i = current - 1).
    // Linear matrix: each node connects to i+1 forward.
    const isAdjacent = !isCurrent && !isVisited &&
      (i === currentNodeIndex + 1 || (i === currentNodeIndex - 1 && visited.includes(currentNodeIndex - 1)));
    const isBoss = node.isBoss;
    const eventKind = (node.eventKind ?? "combat") as MatrixEventKind;
    const glyph = EVENT_GLYPHS[eventKind];
    // Marker: ▸ current, ✓ visited, → adjacent (caret), space otherwise
    const marker = isCurrent ? "▸" : isVisited ? "✓" : isAdjacent ? "→" : " ";
    const label = `${glyph} [${i}] ${node.zone.toUpperCase()}${isBoss ? " (BOSS)" : ""}`;
    const iceCount = node.iceIds.length;
    const eventLabel = eventKind === "combat" ? "" : ` · ${EVENT_LABELS[eventKind]}`;
    const detail = `${iceCount} ICE · ${node.reward.credits}cr${eventLabel}`;
    // Color: current=highlighted, visited=faded, adjacent=zone (available), rest=zone faded
    const baseColor = zoneColor(node.zone);
    const fg = isCurrent
      ? PALETTE.GREEN_NEON
      : isVisited
        ? PALETTE.GRAY_MID
        : isAdjacent
          ? baseColor
          : PALETTE.GRAY_DARK;
    grid = setText(grid, 4, row, `${marker} ${label}`, fg);
    grid = setText(grid, 8, row + 1, detail, isVisited ? PALETTE.GRAY_DARK : baseColor);
  }

  // ICE preview panel (right side, current node)
  if (icePreview && cols >= 50) {
    const previewX = cols - 28;
    const previewY = 6;
    grid = setText(grid, previewX, previewY, "── CURRENT NODE ──", PALETTE.GRAY_LIGHT);
    const iceName = icePreview.name.slice(0, 12);
    grid = setText(grid, previewX, previewY + 1, `ICE: ${iceName}`, PALETTE.ICE_BLUE);
    const node = matrix.nodes[currentNodeIndex];
    const hpStr = node?.iceHp[0]?.toString() ?? "?";
    grid = setText(grid, previewX, previewY + 2, `HP:  ${hpStr}`, PALETTE.GREEN_NEON);
    if (node) {
      const eventKind = (node.eventKind ?? "combat") as MatrixEventKind;
      grid = setText(grid, previewX, previewY + 3, `Evt: ${EVENT_LABELS[eventKind]}`, PALETTE.YELLOW_AMBER);
      grid = setText(grid, previewX, previewY + 4, `Rew: ${node.reward.credits}cr`, PALETTE.CYAN_LIGHT);
    }
  }

  // Footer
  const footerRow = rows - 2;
  const status = isCurrentInAdjacent(matrix, currentNodeIndex)
    ? "ENTER: enter node | ESC: back"
    : "ESC: back";
  grid = setText(grid, 2, footerRow, status, PALETTE.YELLOW_AMBER);

  return grid;
}

function isCurrentInAdjacent(matrix: Matrix, idx: number): boolean {
  const node = matrix.nodes[idx];
  return node != null && node.adjacent.length > 0;
}