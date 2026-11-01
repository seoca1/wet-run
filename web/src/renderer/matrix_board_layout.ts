/** Matrix board placement (ADR-0249): where each node's room sits on screen.
 *
 * Generated matrices carry their room geometry (`MatrixNode.site`), which is
 * scaled into the board rectangle. Hand-built matrices have none and get a
 * deterministic layout from the graph itself. Pure: no state is read or kept.
 */
import type { Matrix } from "../core/types";
import type { PanelRect } from "./panel";

/** A node's room on the board: the token spans `cx - 1 .. cx + 1` on row `cy`. */
export interface BoardSite {
  readonly index: number;
  readonly cx: number;
  readonly cy: number;
}

export interface BoardPlan {
  /** Board rectangle, including a one-cell routing margin on every side. */
  readonly rect: PanelRect;
  readonly sites: readonly BoardSite[];
  readonly sx: number;
  readonly sy: number;
  readonly source: "generated" | "fallback";
}

/** Token width; rooms are drawn as `[·]`. */
export const TOKEN_WIDTH = 3;
const MAX_SX = 5;
const MAX_SY = 3;

interface Unit {
  readonly x: number;
  readonly y: number;
}

/** Undirected, de-duplicated edge list in ascending pair order. */
export function matrixEdges(
  matrix: Matrix,
): ReadonlyArray<readonly [number, number]> {
  const seen = new Set<string>();
  const edges: Array<readonly [number, number]> = [];
  matrix.nodes.forEach((node, a) => {
    for (const b of node.adjacent) {
      if (b === a || matrix.nodes[b] === undefined) continue;
      const pair = a < b ? ([a, b] as const) : ([b, a] as const);
      const key = `${pair[0]}-${pair[1]}`;
      if (seen.has(key)) continue;
      seen.add(key);
      edges.push(pair);
    }
  });
  return edges.sort((p, q) => p[0] - q[0] || p[1] - q[1]);
}

/** Generator room centres, when every node has one and no two coincide. */
function generatedUnits(matrix: Matrix): Unit[] | null {
  const units: Unit[] = [];
  const taken = new Set<string>();
  for (const node of matrix.nodes) {
    const site = node.site;
    if (!site) return null;
    const unit = {
      x: site.x + Math.floor(site.w / 2),
      y: site.y + Math.floor(site.h / 2),
    };
    const key = `${unit.x},${unit.y}`;
    if (taken.has(key)) return null;
    taken.add(key);
    units.push(unit);
  }
  return units;
}

/** Deterministic layout for matrices without geometry: breadth-first layers
 * from the entry as columns, falling back to a serpentine walk when the
 * layers would not fit the generator's own 15x10 space. Units are spaced two
 * apart, like generated rooms. */
function fallbackUnits(matrix: Matrix): Unit[] {
  const count = matrix.nodes.length;
  const linked = matrix.nodes.map(() => [] as number[]);
  for (const [a, b] of matrixEdges(matrix)) {
    linked[a]?.push(b);
    linked[b]?.push(a);
  }
  const layer = new Array<number>(count).fill(-1);
  const order: number[] = [];
  const start = matrix.nodes[matrix.startNode] ? matrix.startNode : 0;
  for (const root of [start, ...matrix.nodes.keys()]) {
    if (root >= count || layer[root] !== -1) continue;
    const base = order.length === 0 ? 0 : Math.max(...layer) + 1;
    layer[root] = base;
    const queue = [root];
    for (const at of queue) {
      order.push(at);
      for (const next of linked[at] ?? []) {
        if (layer[next] !== -1) continue;
        layer[next] = (layer[at] ?? 0) + 1;
        queue.push(next);
      }
    }
  }
  const rank = new Array<number>(count).fill(0);
  const filled = new Map<number, number>();
  for (const i of order) {
    const l = layer[i] ?? 0;
    rank[i] = filled.get(l) ?? 0;
    filled.set(l, (rank[i] ?? 0) + 1);
  }
  const layers = Math.max(0, ...layer) + 1;
  const tallest = Math.max(0, ...filled.values());
  if (layers <= 8 && tallest <= 5) {
    return matrix.nodes.map((_, i) => ({
      x: (layer[i] ?? 0) * 2,
      y: (rank[i] ?? 0) * 2,
    }));
  }
  const columns = 8;
  const units = new Array<Unit>(count);
  order.forEach((node, k) => {
    const row = Math.floor(k / columns);
    const col = k % columns;
    units[node] = {
      x: (row % 2 === 0 ? col : columns - 1 - col) * 2,
      y: row * 2,
    };
  });
  return units;
}

/** Board size for a unit extent at the given scale (with routing margin). */
export function boardSize(
  extentX: number,
  extentY: number,
  sx: number,
  sy: number,
): { readonly width: number; readonly height: number } {
  return { width: extentX * sx + TOKEN_WIDTH + 2, height: extentY * sy + 3 };
}

/** Largest scale (capped) whose board fits the budget; never below 1. */
function fitScale(
  extent: number,
  budget: number,
  fixed: number,
  cap: number,
): number {
  if (extent <= 0) return cap;
  return Math.max(1, Math.min(cap, Math.floor((budget - fixed) / extent)));
}

/** Place every node inside a board centred horizontally in `area`, with
 * its top row at `top` and at most `maxHeight` rows. */
export function planBoard(
  matrix: Matrix,
  area: PanelRect,
  top: number,
  maxHeight: number,
): BoardPlan {
  const generated = generatedUnits(matrix);
  const units = generated ?? fallbackUnits(matrix);
  const xs = units.map((u) => u.x);
  const ys = units.map((u) => u.y);
  const minX = units.length === 0 ? 0 : Math.min(...xs);
  const minY = units.length === 0 ? 0 : Math.min(...ys);
  const extentX = units.length === 0 ? 0 : Math.max(...xs) - minX;
  const extentY = units.length === 0 ? 0 : Math.max(...ys) - minY;
  const sx = fitScale(extentX, area.width - 2, TOKEN_WIDTH + 2, MAX_SX);
  const sy = fitScale(extentY, maxHeight, 3, MAX_SY);
  const size = boardSize(extentX, extentY, sx, sy);
  const rect: PanelRect = {
    x: area.x + Math.floor((area.width - size.width) / 2),
    y: top,
    width: size.width,
    height: size.height,
  };
  const sites = units.map((u, index) => ({
    index,
    cx: rect.x + 2 + (u.x - minX) * sx,
    cy: rect.y + 1 + (u.y - minY) * sy,
  }));
  return { rect, sites, sx, sy, source: generated ? "generated" : "fallback" };
}
