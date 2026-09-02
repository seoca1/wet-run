/** BSP tree partitioning primitives (ADR-0110 split).
 *
 * Pure functions operating on `BspNode` / `BspRoom` records. The
 * procedural generator (`ProceduralDungeonGenerator` in
 * `dungeon_layout.ts`) wires these together to build the spanning
 * tree, assign room types, and emit a complete `DungeonGraph`.
 *
 * Split from `dungeon.ts` to keep the per-module size under the
 * 250-LOC ceiling (programming skill smell 1).
 */
import type { Rng, RngInt } from "./dungeon.ts";

/** Room placement record for a BSP leaf. */
export interface BspRoom {
  x: number;
  y: number;
  w: number;
  h: number;
  roomId: string;
}

/** Recursive BSP partition node. */
export class BspNode {
  readonly x: number;
  readonly y: number;
  readonly w: number;
  readonly h: number;
  left: BspNode | null = null;
  right: BspNode | null = null;
  room: BspRoom | null = null;

  constructor(x: number, y: number, w: number, h: number) {
    this.x = x;
    this.y = y;
    this.w = w;
    this.h = h;
  }

  get isLeaf(): boolean {
    return this.left === null && this.right === null;
  }

  /** Center of the leaf's room, or of the region if no room is placed. */
  center(): readonly [number, number] {
    if (this.room !== null) {
      return [
        this.room.x + Math.floor(this.room.w / 2),
        this.room.y + Math.floor(this.room.h / 2),
      ] as const;
    }
    return [this.x + Math.floor(this.w / 2), this.y + Math.floor(this.h / 2)] as const;
  }
}

/** Recursively split a region until leaves are small enough. */
export function bspPartition(
  rngInt: RngInt,
  rng: Rng,
  minLeafSize: number,
  x: number,
  y: number,
  w: number,
  h: number,
): BspNode {
  const node = new BspNode(x, y, w, h);

  if (w < minLeafSize * 2 && h < minLeafSize * 2) {
    return node;
  }

  const canVertical = w >= 2 * minLeafSize;
  const canHorizontal = h >= 2 * minLeafSize;
  if (!canVertical && !canHorizontal) {
    return node;
  }

  let splitVertical: boolean;
  if (canVertical && (!canHorizontal || w >= h * 1.25)) {
    splitVertical = true;
  } else if (canHorizontal && (!canVertical || h > w * 1.25)) {
    splitVertical = false;
  } else {
    splitVertical = rng() < 0.5;
  }

  if (splitVertical) {
    const cut = rngInt(minLeafSize, w - minLeafSize);
    node.left = bspPartition(rngInt, rng, minLeafSize, x, y, cut, h);
    node.right = bspPartition(rngInt, rng, minLeafSize, x + cut, y, w - cut, h);
  } else {
    const cut = rngInt(minLeafSize, h - minLeafSize);
    node.left = bspPartition(rngInt, rng, minLeafSize, x, y, w, cut);
    node.right = bspPartition(rngInt, rng, minLeafSize, x, y + cut, w, h - cut);
  }
  return node;
}

/** Place one room inside each leaf. Returns the number of rooms placed. */
export function placeRooms(
  rngInt: RngInt,
  roomPadding: number,
  node: BspNode,
): number {
  let counter = 0;
  const walk = (n: BspNode): void => {
    if (n.isLeaf) {
      const maxW = Math.max(1, n.w - 2 * roomPadding);
      const maxH = Math.max(1, n.h - 2 * roomPadding);
      const roomW = Math.max(1, Math.min(maxW, rngInt(2, Math.max(2, maxW))));
      const roomH = Math.max(1, Math.min(maxH, rngInt(2, Math.max(2, maxH))));
      const rxMin = n.x + roomPadding;
      const rxMax = n.x + n.w - roomPadding - roomW;
      const ryMin = n.y + roomPadding;
      const ryMax = n.y + n.h - roomPadding - roomH;
      const rx = rxMax <= rxMin ? rxMin : rngInt(rxMin, rxMax);
      const ry = ryMax <= ryMin ? ryMin : rngInt(ryMin, ryMax);
      n.room = {
        x: rx,
        y: ry,
        w: roomW,
        h: roomH,
        roomId: `r${counter}`,
      };
      counter += 1;
      return;
    }
    if (n.left !== null) walk(n.left);
    if (n.right !== null) walk(n.right);
  };
  walk(node);
  return counter;
}

/** Walk the BSP and collect every leaf (depth-first, pre-order). */
export function collectLeaves(node: BspNode): BspNode[] {
  const out: BspNode[] = [];
  const walk = (n: BspNode): void => {
    if (n.isLeaf) {
      out.push(n);
      return;
    }
    if (n.left !== null) walk(n.left);
    if (n.right !== null) walk(n.right);
  };
  walk(node);
  return out;
}
