/** Pure, immutable Green Grid panels (ADR-0237 §2).
 *
 * Double-line glyphs follow tutorial.ts and menu_dialogue.ts. Clipping crops
 * the requested frame; it never moves its borders or reflows its labels.
 */
import type { Grid } from "../core/types";
import { setText } from "../core/grid";
import { PALETTE } from "./palette";

/** Grid-space rectangle; dimensions include the border when used as a frame. */
export interface PanelRect {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
}

/** Optional labels embedded in the top border. */
export interface PanelOptions {
  readonly title?: string;
  readonly status?: string;
}

/** Updated grid and the visible content area, excluding the one-cell border. */
export interface PanelResult {
  readonly grid: Grid;
  readonly inner: PanelRect;
}

function validRect(frame: PanelRect): boolean {
  return (
    [frame.x, frame.y, frame.width, frame.height].every(Number.isSafeInteger) &&
    frame.width >= 0 &&
    frame.height >= 0
  );
}

/** Compute the border-free content area intersected with the supplied grid.
 * Empty areas have nonnegative dimensions and an origin clamped to the grid.
 * Non-integer/non-finite geometry is invalid and returns an empty rectangle.
 */
export function panelInnerRect(grid: Grid, frame: PanelRect): PanelRect {
  if (!validRect(frame)) return { x: 0, y: 0, width: 0, height: 0 };
  const x = Math.min(
    grid.width,
    Math.max(0, frame.x + Math.min(1, frame.width)),
  );
  const y = Math.min(
    grid.height,
    Math.max(0, frame.y + Math.min(1, frame.height)),
  );
  const right = Math.min(grid.width, Math.max(0, frame.x + frame.width - 1));
  const bottom = Math.min(grid.height, Math.max(0, frame.y + frame.height - 1));
  return {
    x,
    y,
    width: Math.max(0, right - x),
    height: Math.max(0, bottom - y),
  };
}

interface PanelRule {
  readonly y: number;
  readonly left: string;
  readonly right: string;
}

function drawRule(grid: Grid, frame: PanelRect, rule: PanelRule): Grid {
  if (rule.y < 0 || rule.y >= grid.height) return grid;
  const start = Math.max(0, frame.x);
  const end = Math.min(grid.width, frame.x + frame.width);
  let text = "";
  for (let x = start; x < end; x++) {
    text +=
      x === frame.x
        ? rule.left
        : x === frame.x + frame.width - 1
          ? rule.right
          : "═";
  }
  return setText(grid, start, rule.y, text, PALETTE.GREEN_NEON);
}

/** Draw a double-line frame without clearing its content or mutating the input.
 * Returns the new grid and its clipped inner rectangle. Boxes smaller than 2×2
 * or with invalid geometry draw nothing. Labels leave one rail cell at each
 * corner; status is right-aligned and takes priority, with a rail between labels.
 * Overlong labels truncate on the right. Colours resolve at call time.
 */
export function drawPanel(
  grid: Grid,
  frame: PanelRect,
  options: PanelOptions = {},
): PanelResult {
  const inner = panelInnerRect(grid, frame);
  if (!validRect(frame) || frame.width < 2 || frame.height < 2)
    return { grid, inner };

  let next = drawRule(grid, frame, { y: frame.y, left: "╔", right: "╗" });
  next = drawRule(next, frame, {
    y: frame.y + frame.height - 1,
    left: "╚",
    right: "╝",
  });
  const bottom = Math.min(grid.height, frame.y + frame.height - 1);
  for (let y = Math.max(0, frame.y + 1); y < bottom; y++) {
    next = setText(next, frame.x, y, "║", PALETTE.GREEN_NEON);
    next = setText(next, frame.x + frame.width - 1, y, "║", PALETTE.GREEN_NEON);
  }

  if (frame.y >= 0 && frame.y < grid.height) {
    const capacity = Math.max(0, frame.width - 4);
    const status = (options.status ?? "").slice(0, capacity);
    const titleCapacity = Math.max(
      0,
      capacity - status.length - (status ? 1 : 0),
    );
    const title = (options.title ?? "").slice(0, titleCapacity);
    next = setText(next, frame.x + 2, frame.y, title, PALETTE.GREEN_NEON);
    next = setText(
      next,
      frame.x + frame.width - 2 - status.length,
      frame.y,
      status,
      PALETTE.GRAY_LIGHT,
    );
  }
  return { grid: next, inner };
}

/** Draw a ╠═╣ separator at an absolute grid row strictly inside the frame.
 * Invalid/outside rows and degenerate frames are no-ops. Like the frame border,
 * the separator uses the current GREEN_NEON foreground and BACKGROUND colour.
 */
export function drawPanelSeparator(
  grid: Grid,
  frame: PanelRect,
  y: number,
): Grid {
  if (
    !validRect(frame) ||
    frame.width < 2 ||
    frame.height < 3 ||
    !Number.isSafeInteger(y) ||
    y <= frame.y ||
    y >= frame.y + frame.height - 1
  ) {
    return grid;
  }
  return drawRule(grid, frame, { y, left: "╠", right: "╣" });
}
