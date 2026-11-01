/** Corridor routing for the Matrix board (ADR-0249).
 *
 * One corridor per undirected adjacency, and nothing else: `MatrixNode.adjacent`
 * is the only authority. Corridors are orthogonal A* paths that never enter a
 * room, never point into a room that is not one of their two endpoints, never
 * run along another corridor and only cross one at a right angle away from
 * rooms. Routing reads only the plan, so a matrix keeps the same corridors
 * whatever the player's position or knowledge.
 */
import type { Matrix } from "../core/types";
import { heapPop, heapPush } from "./min_heap";
import {
  matrixEdges,
  type BoardPlan,
  type BoardSite,
} from "./matrix_board_layout";

/** Direction bits: N, E, S, W. A cell's `links` is the set it connects. */
export const N = 1;
export const E = 2;
export const S = 4;
export const W = 8;
const DIRS = [N, E, S, W] as const;
const STEP: Readonly<Record<number, readonly [number, number]>> = {
  [N]: [0, -1],
  [E]: [1, 0],
  [S]: [0, 1],
  [W]: [-1, 0],
};
const opposite = (d: number): number =>
  d === N ? S : d === S ? N : d === E ? W : E;

export interface CorridorCell {
  readonly x: number;
  readonly y: number;
  readonly links: number;
}

export interface Corridor {
  readonly a: number;
  readonly b: number;
  readonly cells: readonly CorridorCell[];
}

export interface CorridorSet {
  readonly corridors: readonly Corridor[];
  /** Adjacencies with no legal path; expected empty on supported layouts. */
  readonly unrouted: ReadonlyArray<readonly [number, number]>;
}

const TURN = 1;
const CROSS = 6;
const NEAR_ROOM = 2;
const SHARE = 40;

interface Port {
  readonly x: number;
  readonly y: number;
  /** Travel direction leaving the room through this port. */
  readonly out: number;
}

/** The eight cells beside a token through which a corridor may attach. */
export function portsOf(site: BoardSite): readonly Port[] {
  const { cx, cy } = site;
  return [
    { x: cx - 2, y: cy, out: W },
    { x: cx + 2, y: cy, out: E },
    ...[-1, 0, 1].map((k) => ({ x: cx + k, y: cy - 1, out: N })),
    ...[-1, 0, 1].map((k) => ({ x: cx + k, y: cy + 1, out: S })),
  ];
}

class Board {
  readonly occupied = new Map<number, number>();
  readonly rooms = new Map<number, number>();
  constructor(readonly plan: BoardPlan) {
    for (const site of plan.sites)
      for (let dx = -1; dx <= 1; dx++)
        this.rooms.set(this.key(site.cx + dx, site.cy), site.index);
  }
  key(x: number, y: number): number {
    return y * 4096 + x;
  }
  inside(x: number, y: number): boolean {
    const r = this.plan.rect;
    return x >= r.x && y >= r.y && x < r.x + r.width && y < r.y + r.height;
  }
  roomAt(x: number, y: number): number | undefined {
    return this.rooms.get(this.key(x, y));
  }
  nearRoom(x: number, y: number): boolean {
    return DIRS.some((d) => {
      const [dx, dy] = STEP[d] ?? [0, 0];
      return this.roomAt(x + dx, y + dy) !== undefined;
    });
  }
  /** Extra cost of drawing `links` at a cell, or null when it is illegal. */
  cost(
    x: number,
    y: number,
    links: number,
    terminal: number,
    ends: readonly number[],
    relaxed: boolean,
  ): number | null {
    if (!this.inside(x, y) || this.roomAt(x, y) !== undefined) return null;
    for (const d of DIRS) {
      if ((links & d) === 0) continue;
      const [dx, dy] = STEP[d] ?? [0, 0];
      const room = this.roomAt(x + dx, y + dy);
      if (room === undefined) continue;
      if ((terminal & d) === 0 || !ends.includes(room)) return null;
    }
    const near = this.nearRoom(x, y);
    const used = this.occupied.get(this.key(x, y)) ?? 0;
    const base = near && terminal === 0 ? NEAR_ROOM : 0;
    if (used === 0) return base;
    const crossing =
      (links === (N | S) && used === (E | W)) ||
      (links === (E | W) && used === (N | S));
    if (crossing && !near) return base + CROSS;
    return relaxed ? base + SHARE : null;
  }
}

interface State {
  readonly x: number;
  readonly y: number;
  readonly dir: number;
  readonly g: number;
  readonly f: number;
  readonly parent: State | null;
  /** Links of this cell's predecessor side: toward the room for a start. */
  readonly back: number;
  readonly terminal: number;
}

function search(
  board: Board,
  from: BoardSite,
  to: BoardSite,
  relaxed: boolean,
): CorridorCell[] | null {
  const ends = [from.index, to.index];
  const goals = portsOf(to);
  const h = (x: number, y: number) =>
    Math.min(...goals.map((p) => Math.abs(p.x - x) + Math.abs(p.y - y)));
  const goalAt = new Map(
    goals.map((p) => [board.key(p.x, p.y), opposite(p.out)]),
  );
  const best = new Map<number, number>();
  const heap: State[] = [];
  for (const p of portsOf(from)) {
    if (!board.inside(p.x, p.y) || board.roomAt(p.x, p.y) !== undefined)
      continue;
    const back = opposite(p.out);
    heapPush(heap, {
      x: p.x,
      y: p.y,
      dir: p.out,
      g: 0,
      f: h(p.x, p.y),
      parent: null,
      back,
      terminal: back,
    });
  }
  for (let s = heapPop(heap); s; s = heapPop(heap)) {
    const id = board.key(s.x, s.y) * 16 + s.dir;
    if ((best.get(id) ?? Infinity) < s.g) continue;
    const into = goalAt.get(board.key(s.x, s.y));
    if (into !== undefined && into !== s.back) {
      const extra = board.cost(
        s.x,
        s.y,
        s.back | into,
        s.terminal | into,
        ends,
        relaxed,
      );
      if (extra !== null) return trace(s, into);
    }
    for (const d of DIRS) {
      if (d === s.back) continue;
      const extra = board.cost(s.x, s.y, s.back | d, s.terminal, ends, relaxed);
      if (extra === null) continue;
      const [dx, dy] = STEP[d] ?? [0, 0];
      const nx = s.x + dx;
      const ny = s.y + dy;
      if (!board.inside(nx, ny) || board.roomAt(nx, ny) !== undefined) continue;
      const g = s.g + 1 + extra + (d === s.dir ? 0 : TURN);
      const nid = board.key(nx, ny) * 16 + d;
      if ((best.get(nid) ?? Infinity) <= g) continue;
      best.set(nid, g);
      heapPush(heap, {
        x: nx,
        y: ny,
        dir: d,
        g,
        f: g + h(nx, ny),
        parent: s,
        back: opposite(d),
        terminal: 0,
      });
    }
  }
  return null;
}

function trace(end: State, into: number): CorridorCell[] {
  const cells: CorridorCell[] = [];
  let next = into;
  for (let s: State | null = end; s; s = s.parent) {
    cells.push({ x: s.x, y: s.y, links: s.back | next });
    next = s.dir;
  }
  return cells.reverse();
}

const cache = new WeakMap<Matrix, Map<string, CorridorSet>>();

/** Route every adjacency of `matrix` on `plan`. Deterministic and memoised
 * per matrix and plan geometry, so re-rendering the same screen is cheap. */
export function routeCorridors(matrix: Matrix, plan: BoardPlan): CorridorSet {
  const key = `${plan.rect.x},${plan.rect.y},${plan.rect.width},${plan.rect.height},${plan.sx},${plan.sy}`;
  const known = cache.get(matrix)?.get(key);
  if (known) return known;
  const board = new Board(plan);
  const distance = ([a, b]: readonly [number, number]): number => {
    const p = plan.sites[a];
    const q = plan.sites[b];
    return p && q ? Math.abs(p.cx - q.cx) + Math.abs(p.cy - q.cy) : 0;
  };
  const edges = [...matrixEdges(matrix)].sort(
    (p, q) => distance(p) - distance(q) || p[0] - q[0] || p[1] - q[1],
  );
  const corridors: Corridor[] = [];
  const unrouted: Array<readonly [number, number]> = [];
  for (const [a, b] of edges) {
    const from = plan.sites[a];
    const to = plan.sites[b];
    const cells =
      from && to
        ? (search(board, from, to, false) ?? search(board, from, to, true))
        : null;
    if (!cells) {
      unrouted.push([a, b]);
      continue;
    }
    for (const c of cells) {
      const k = board.key(c.x, c.y);
      board.occupied.set(k, (board.occupied.get(k) ?? 0) | c.links);
    }
    corridors.push({ a, b, cells });
  }
  const result = { corridors, unrouted };
  const perMatrix = cache.get(matrix) ?? new Map<string, CorridorSet>();
  perMatrix.set(key, result);
  cache.set(matrix, perMatrix);
  return result;
}
