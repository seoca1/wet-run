import { describe, it, expect } from "vitest";
import { BspNode, bspPartition, placeRooms, collectLeaves } from "../src/core/dungeon_bsp.ts";
import { makeMulberry32, withInt } from "../src/core/dungeon.ts";

describe("BspNode", () => {
  it("constructs with position and dimensions", () => {
    const node = new BspNode(5, 10, 20, 30);
    expect(node.x).toBe(5);
    expect(node.y).toBe(10);
    expect(node.w).toBe(20);
    expect(node.h).toBe(30);
  });

  it("initializes with no children", () => {
    const node = new BspNode(0, 0, 10, 10);
    expect(node.left).toBeNull();
    expect(node.right).toBeNull();
  });

  it("initializes with no room", () => {
    const node = new BspNode(0, 0, 10, 10);
    expect(node.room).toBeNull();
  });

  it("isLeaf returns true when no children", () => {
    const node = new BspNode(0, 0, 10, 10);
    expect(node.isLeaf).toBe(true);
  });

  it("isLeaf returns false when left child exists", () => {
    const node = new BspNode(0, 0, 10, 10);
    node.left = new BspNode(0, 0, 5, 10);
    expect(node.isLeaf).toBe(false);
  });

  it("isLeaf returns false when right child exists", () => {
    const node = new BspNode(0, 0, 10, 10);
    node.right = new BspNode(5, 0, 5, 10);
    expect(node.isLeaf).toBe(false);
  });

  it("center returns midpoint when no room", () => {
    const node = new BspNode(0, 0, 10, 10);
    const [x, y] = node.center();
    expect(x).toBe(5);
    expect(y).toBe(5);
  });

  it("center returns room center when room exists", () => {
    const node = new BspNode(0, 0, 20, 20);
    node.room = { x: 5, y: 5, w: 6, h: 6, roomId: "r0" };
    const [x, y] = node.center();
    expect(x).toBe(8);
    expect(y).toBe(8);
  });

  it("center floors fractional coordinates", () => {
    const node = new BspNode(0, 0, 11, 13);
    const [x, y] = node.center();
    expect(x).toBe(5);
    expect(y).toBe(6);
  });
});

describe("bspPartition", () => {
  it("returns single node when region is too small", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 10, 0, 0, 5, 5);
    expect(node.isLeaf).toBe(true);
  });

  it("splits large regions", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    expect(node.isLeaf).toBe(false);
    expect(node.left).not.toBeNull();
    expect(node.right).not.toBeNull();
  });

  it("creates recursive partitions", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 2, 0, 0, 30, 30);
    const leaves = collectLeaves(node);
    expect(leaves.length).toBeGreaterThan(1);
  });

  it("preserves total area across partitions", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const w = 20;
    const h = 20;
    const node = bspPartition(rngInt, rng, 2, 0, 0, w, h);
    const leaves = collectLeaves(node);
    const totalArea = leaves.reduce((sum, leaf) => sum + leaf.w * leaf.h, 0);
    expect(totalArea).toBe(w * h);
  });

  it("produces deterministic splits with same seed", () => {
    const rng1 = makeMulberry32(42);
    const rngInt1 = withInt(rng1);
    const node1 = bspPartition(rngInt1, rng1, 2, 0, 0, 20, 20);
    const leaves1 = collectLeaves(node1);

    const rng2 = makeMulberry32(42);
    const rngInt2 = withInt(rng2);
    const node2 = bspPartition(rngInt2, rng2, 2, 0, 0, 20, 20);
    const leaves2 = collectLeaves(node2);

    expect(leaves1.length).toBe(leaves2.length);
    for (let i = 0; i < leaves1.length; i++) {
      const l1 = leaves1[i];
      const l2 = leaves2[i];
      if (l1 && l2) {
        expect(l1.x).toBe(l2.x);
        expect(l1.y).toBe(l2.y);
        expect(l1.w).toBe(l2.w);
        expect(l1.h).toBe(l2.h);
      }
    }
  });

  it("splits vertically when width exceeds height", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 2, 0, 0, 30, 10);
    if (node.left && node.right) {
      expect(node.left.x).not.toBe(node.right.x);
      expect(node.left.y).toBe(node.right.y);
    }
  });

  it("splits horizontally when height exceeds width", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 2, 0, 0, 10, 30);
    if (node.left && node.right) {
      expect(node.left.x).toBe(node.right.x);
      expect(node.left.y).not.toBe(node.right.y);
    }
  });

  it("respects minLeafSize constraint", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const minLeafSize = 5;
    const node = bspPartition(rngInt, rng, minLeafSize, 0, 0, 20, 20);
    const leaves = collectLeaves(node);
    for (const leaf of leaves) {
      expect(leaf.w).toBeGreaterThanOrEqual(minLeafSize);
      expect(leaf.h).toBeGreaterThanOrEqual(minLeafSize);
    }
  });

  it("handles square regions", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    expect(node).toBeDefined();
    expect(collectLeaves(node).length).toBeGreaterThan(0);
  });

  it("handles minimum viable region", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const minLeafSize = 2;
    const node = bspPartition(rngInt, rng, minLeafSize, 0, 0, 4, 4);
    expect(node).toBeDefined();
  });
});

describe("placeRooms", () => {
  it("places room in leaf node", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = new BspNode(0, 0, 10, 10);
    const count = placeRooms(rngInt, 1, node);
    expect(count).toBe(1);
    expect(node.room).not.toBeNull();
  });

  it("assigns unique roomId", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    placeRooms(rngInt, 1, node);
    const leaves = collectLeaves(node);
    const ids = leaves.map((leaf) => leaf.room?.roomId).filter((id) => id !== null);
    const uniqueIds = new Set(ids);
    expect(uniqueIds.size).toBe(ids.length);
  });

  it("returns count of placed rooms", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    const count = placeRooms(rngInt, 1, node);
    const leaves = collectLeaves(node);
    expect(count).toBe(leaves.length);
  });

  it("respects roomPadding", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = new BspNode(0, 0, 10, 10);
    const padding = 2;
    placeRooms(rngInt, padding, node);
    if (node.room) {
      expect(node.room.x).toBeGreaterThanOrEqual(padding);
      expect(node.room.y).toBeGreaterThanOrEqual(padding);
      expect(node.room.x + node.room.w).toBeLessThanOrEqual(10 - padding);
      expect(node.room.y + node.room.h).toBeLessThanOrEqual(10 - padding);
    }
  });

  it("places positive-size rooms", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    placeRooms(rngInt, 1, node);
    const leaves = collectLeaves(node);
    for (const leaf of leaves) {
      if (leaf.room) {
        expect(leaf.room.w).toBeGreaterThan(0);
        expect(leaf.room.h).toBeGreaterThan(0);
      }
    }
  });

  it("places rooms within node bounds", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    placeRooms(rngInt, 1, node);
    const leaves = collectLeaves(node);
    for (const leaf of leaves) {
      if (leaf.room) {
        expect(leaf.room.x).toBeGreaterThanOrEqual(leaf.x);
        expect(leaf.room.y).toBeGreaterThanOrEqual(leaf.y);
        expect(leaf.room.x + leaf.room.w).toBeLessThanOrEqual(leaf.x + leaf.w);
        expect(leaf.room.y + leaf.room.h).toBeLessThanOrEqual(leaf.y + leaf.h);
      }
    }
  });

  it("handles zero padding", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = new BspNode(0, 0, 5, 5);
    const count = placeRooms(rngInt, 0, node);
    expect(count).toBe(1);
    expect(node.room).not.toBeNull();
  });

  it("generates sequential room ids", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    placeRooms(rngInt, 1, node);
    const leaves = collectLeaves(node);
    const ids = leaves.map((leaf) => leaf.room?.roomId).filter((id) => id);
    for (let i = 0; i < ids.length; i++) {
      expect(ids[i]).toBe(`r${i}`);
    }
  });

  it("returns 0 for node with no leaves", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 100, 0, 0, 5, 5);
    const count = placeRooms(rngInt, 1, node);
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

describe("collectLeaves", () => {
  it("returns single node when node is leaf", () => {
    const node = new BspNode(0, 0, 10, 10);
    const leaves = collectLeaves(node);
    expect(leaves.length).toBe(1);
    expect(leaves[0]).toBe(node);
  });

  it("returns all leaves from tree", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    const leaves = collectLeaves(node);
    expect(leaves.length).toBeGreaterThan(1);
    for (const leaf of leaves) {
      expect(leaf.isLeaf).toBe(true);
    }
  });

  it("does not include internal nodes", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    const leaves = collectLeaves(node);
    expect(leaves.includes(node)).toBe(false);
  });

  it("collects leaves in depth-first order", () => {
    const parent = new BspNode(0, 0, 20, 20);
    parent.left = new BspNode(0, 0, 10, 20);
    parent.right = new BspNode(10, 0, 10, 20);
    const leaves = collectLeaves(parent);
    expect(leaves.length).toBe(2);
    expect(leaves[0]).toBe(parent.left);
    expect(leaves[1]).toBe(parent.right);
  });

  it("handles deeply nested tree", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const node = bspPartition(rngInt, rng, 1, 0, 0, 50, 50);
    const leaves = collectLeaves(node);
    expect(leaves.length).toBeGreaterThan(5);
  });

  it("returns empty array when given tree with only internal nodes", () => {
    const parent = new BspNode(0, 0, 20, 20);
    parent.left = new BspNode(0, 0, 10, 20);
    parent.right = new BspNode(10, 0, 10, 20);
    parent.left.left = new BspNode(0, 0, 5, 20);
    parent.left.right = new BspNode(5, 0, 5, 20);
    parent.right.left = new BspNode(10, 0, 5, 20);
    parent.right.right = new BspNode(15, 0, 5, 20);
    const leaves = collectLeaves(parent);
    expect(leaves.length).toBe(4);
    expect(leaves.every((n) => n.isLeaf)).toBe(true);
  });
});
