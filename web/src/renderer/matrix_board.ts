/** Draw the Matrix operation board (ADR-0249): rooms, corridors, `@`, `◆`.
 *
 * Every meaning has a glyph as well as a colour: `@` position, `◆` boss,
 * `>` `<` target, `#` walls for uncleared ICE, `·` / `✓` / `+` for
 * NEW / SEEN / CLEAR, and three corridor styles for target / route / link.
 */
import type { Grid, Matrix } from "../core/types";
import { setText } from "../core/grid";
import { PALETTE } from "./palette";
import type { PanelRect } from "./panel";
import type { BoardPlan } from "./matrix_board_layout";
import { E, N, S, W, type CorridorSet } from "./matrix_board_routes";
import type { MatrixPosition } from "./matrix_nodes";

export type CorridorStyle = "link" | "route" | "target";
type Style = CorridorStyle;

const GLYPHS: Readonly<Record<Style, Readonly<Record<number, string>>>> = {
  link: {
    [N | S]: "┆",
    [E | W]: "┄",
    [S | E]: "╭",
    [S | W]: "╮",
    [N | E]: "╰",
    [N | W]: "╯",
    15: "┼",
  },
  route: {
    [N | S]: "│",
    [E | W]: "─",
    [S | E]: "┌",
    [S | W]: "┐",
    [N | E]: "└",
    [N | W]: "┘",
    15: "┼",
  },
  target: {
    [N | S]: "┃",
    [E | W]: "━",
    [S | E]: "┏",
    [S | W]: "┓",
    [N | E]: "┗",
    [N | W]: "┛",
    15: "╋",
  },
};
const COLOURS: Readonly<Record<Style, string>> = {
  link: PALETTE.GRAY_MID,
  route: PALETTE.CYAN_LIGHT,
  target: PALETTE.GREEN_NEON,
};
const RANK: Readonly<Record<Style, number>> = { link: 0, route: 1, target: 2 };

/** The glyph a corridor cell takes in `style` for its `links`. */
export function corridorGlyph(style: Style, links: number): string {
  return GLYPHS[style][links] ?? GLYPHS[style][15] ?? "+";
}

/** Board legend, two rows of at most 33 columns (fits the 40x60 frame). */
export const BOARD_LEGEND: readonly string[] = [
  "@ you ◆ boss >·< target #·# ICE",
  "· NEW ✓ SEEN + CLEAR ─route ┄link",
];

export type NodeState = "NEW" | "SEEN" | "CLEAR";

export function nodeState(position: MatrixPosition, i: number): NodeState {
  return position.cleared.includes(i)
    ? "CLEAR"
    : position.visited.includes(i)
      ? "SEEN"
      : "NEW";
}

export function isBossNode(matrix: Matrix, i: number): boolean {
  return i === matrix.bossNode || matrix.nodes[i]?.isBoss === true;
}

/** The three characters of a node's room token. */
export function roomToken(position: MatrixPosition, i: number): string {
  const { matrix, current, selected } = position;
  const node = matrix.nodes[i];
  const boss = isBossNode(matrix, i);
  const state = nodeState(position, i);
  const centre =
    i === current
      ? "@"
      : boss
        ? "◆"
        : state === "CLEAR"
          ? "+"
          : state === "SEEN"
            ? "✓"
            : "·";
  const ice = (node?.iceIds.length ?? 0) > 0 && state !== "CLEAR";
  const [l, r] =
    i === selected && i !== current
      ? [">", "<"]
      : i === current && boss
        ? ["◆", "◆"]
        : ice
          ? ["#", "#"]
          : ["[", "]"];
  return `${l}${centre}${r}`;
}

export function tokenColour(
  position: MatrixPosition,
  i: number,
  frontier: readonly number[],
): string {
  if (i === position.current || i === position.selected)
    return PALETTE.GREEN_NEON;
  if (isBossNode(position.matrix, i)) return PALETTE.MAGENTA_LIGHT;
  return frontier.includes(i) ? PALETTE.CYAN_LIGHT : PALETTE.GRAY_LIGHT;
}

/** Destinations the arrows cycle through, in the reducer's own order. */
export function frontierOf(position: MatrixPosition): readonly number[] {
  const here = position.matrix.nodes[position.current];
  return (here?.adjacent ?? []).filter(
    (i, k, all) =>
      i !== position.current &&
      position.matrix.nodes[i] !== undefined &&
      all.indexOf(i) === k,
  );
}

/** Corridor style: only edges the player can travel from here are routes. */
export function corridorStyle(
  position: MatrixPosition,
  a: number,
  b: number,
): Style {
  const frontier = frontierOf(position);
  const other = a === position.current ? b : b === position.current ? a : null;
  if (other === null || !frontier.includes(other)) return "link";
  return other === position.selected ? "target" : "route";
}

/** Write text clipped on every side to `rect`, so nothing reaches a rail. */
export function putInside(
  grid: Grid,
  rect: PanelRect,
  x: number,
  y: number,
  text: string,
  fg: string,
): Grid {
  if (y < rect.y || y >= rect.y + rect.height) return grid;
  const skip = Math.max(0, rect.x - x);
  const visible = [...text].slice(
    skip,
    Math.max(skip, rect.x + rect.width - x),
  );
  return visible.length === 0
    ? grid
    : setText(grid, x + skip, y, visible.join(""), fg);
}

/** Draw corridors, then rooms, clipped to `clip`. */
export function drawBoard(
  grid: Grid,
  clip: PanelRect,
  plan: BoardPlan,
  routes: CorridorSet,
  position: MatrixPosition,
): Grid {
  const cells = new Map<
    string,
    { x: number; y: number; style: Style; links: number }
  >();
  for (const corridor of routes.corridors) {
    const style = corridorStyle(position, corridor.a, corridor.b);
    for (const c of corridor.cells) {
      const key = `${c.x},${c.y}`;
      const prior = cells.get(key);
      if (!prior || RANK[style] > RANK[prior.style])
        cells.set(key, { x: c.x, y: c.y, style, links: c.links });
      else if (prior.style === style) prior.links |= c.links;
    }
  }
  let out = grid;
  for (const c of cells.values()) {
    const glyph = corridorGlyph(c.style, c.links);
    out = putInside(out, clip, c.x, c.y, glyph, COLOURS[c.style]);
  }
  const frontier = frontierOf(position);
  for (const site of plan.sites) {
    const token = roomToken(position, site.index);
    const x = site.cx - 1;
    out = putInside(
      out,
      clip,
      x,
      site.cy,
      token,
      tokenColour(position, site.index, frontier),
    );
  }
  return out;
}
