import { describe, it, expect } from "vitest";
import {
  buildMatrix,
  generateProceduralMatrix,
  advanceNode,
  isBossNode,
  resolveMatrixRoster,
  NUM_NODES,
  ZONE_BY_NODE_INDEX,
} from "../src/core/matrix.ts";
import type { Ice, Matrix } from "../src/core/types.ts";

const sampleIceCatalog: Record<string, Ice> = {
  watchdog: {
    id: "watchdog",
    name: "Watchdog",
    hp: 10,
    armor: 1,
    tier: 1,
  },
  wintermute: {
    id: "wintermute",
    name: "Wintermute",
    hp: 50,
    armor: 5,
    tier: 5,
  },
  guardian: {
    id: "guardian",
    name: "Guardian",
    hp: 20,
    armor: 3,
    tier: 2,
  },
};

describe("matrix", () => {
  describe("constants", () => {
    it("NUM_NODES is 5", () => {
      expect(NUM_NODES).toBe(5);
    });

    it("ZONE_BY_NODE_INDEX has correct zones", () => {
      expect(ZONE_BY_NODE_INDEX[0]).toBe("surface");
      expect(ZONE_BY_NODE_INDEX[1]).toBe("mid");
      expect(ZONE_BY_NODE_INDEX[2]).toBe("deep");
      expect(ZONE_BY_NODE_INDEX[3]).toBe("core");
      expect(ZONE_BY_NODE_INDEX[4]).toBe("core-deep");
    });

    it("ZONE_BY_NODE_INDEX length matches NUM_NODES", () => {
      expect(ZONE_BY_NODE_INDEX.length).toBe(NUM_NODES);
    });
  });

  describe("buildMatrix", () => {
    it("creates matrix with 5 nodes", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      expect(matrix.nodes.length).toBe(5);
    });

    it("sets startNode to 0", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      expect(matrix.startNode).toBe(0);
    });

    it("sets bossNode to 4", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      expect(matrix.bossNode).toBe(4);
    });

    it("assigns correct zones", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      expect(matrix.nodes[0]?.zone).toBe("surface");
      expect(matrix.nodes[4]?.zone).toBe("core-deep");
    });

    it("non-boss nodes have 1 ICE", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      for (let i = 0; i < 4; i++) {
        const node = matrix.nodes[i];
        expect(node?.iceIds.length).toBe(1);
      }
    });

    it("boss node has 1 ICE", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      const boss = matrix.nodes[4];
      expect(boss?.iceIds.length).toBe(1);
    });

    it("nodes have linear adjacency", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      expect(matrix.nodes[0]?.adjacent).toEqual([1]);
      expect(matrix.nodes[1]?.adjacent).toEqual([2]);
      expect(matrix.nodes[2]?.adjacent).toEqual([3]);
      expect(matrix.nodes[3]?.adjacent).toEqual([4]);
    });

    it("boss node has empty adjacent", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      expect(matrix.nodes[4]?.adjacent).toEqual([]);
    });

    it("nodes have rewards", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      for (const node of matrix.nodes) {
        expect(node.reward).toBeDefined();
        expect(node.reward.credits).toBeGreaterThan(0);
      }
    });

    it("marks boss node correctly", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      expect(matrix.nodes[4]?.isBoss).toBe(true);
      expect(matrix.nodes[0]?.isBoss).toBe(false);
    });

    it("uses watchdog for non-boss nodes", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      expect(matrix.nodes[0]?.iceIds[0]).toBe("watchdog");
    });

    it("uses wintermute for boss node", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      expect(matrix.nodes[4]?.iceIds[0]).toBe("wintermute");
    });

    it("handles empty catalog gracefully", () => {
      const matrix = buildMatrix({});
      expect(matrix.nodes.length).toBe(5);
      expect(matrix.nodes[0]?.iceIds.length).toBe(0);
    });
  });

  describe("advanceNode", () => {
    const matrix = buildMatrix(sampleIceCatalog);

    it("advances from node 0 to 1", () => {
      expect(advanceNode(matrix, 0)).toBe(1);
    });

    it("advances from node 1 to 2", () => {
      expect(advanceNode(matrix, 1)).toBe(2);
    });

    it("advances from node 3 to 4", () => {
      expect(advanceNode(matrix, 3)).toBe(4);
    });

    it("stays at boss node", () => {
      expect(advanceNode(matrix, 4)).toBe(4);
    });

    it("stays at invalid node", () => {
      expect(advanceNode(matrix, 99)).toBe(99);
    });

    it("handles negative node", () => {
      expect(advanceNode(matrix, -1)).toBe(-1);
    });
  });

  describe("isBossNode", () => {
    const matrix = buildMatrix(sampleIceCatalog);

    it("returns true for boss node", () => {
      expect(isBossNode(matrix, 4)).toBe(true);
    });

    it("returns false for non-boss nodes", () => {
      expect(isBossNode(matrix, 0)).toBe(false);
      expect(isBossNode(matrix, 1)).toBe(false);
      expect(isBossNode(matrix, 2)).toBe(false);
      expect(isBossNode(matrix, 3)).toBe(false);
    });

    it("returns false for invalid node", () => {
      expect(isBossNode(matrix, 99)).toBe(false);
    });
  });

  describe("resolveMatrixRoster", () => {
    const matrix = buildMatrix(sampleIceCatalog);

    it("resolves ICE for node", () => {
      const result = resolveMatrixRoster(matrix, 0, sampleIceCatalog);
      expect(result.ice.length).toBe(1);
      expect(result.ice[0]?.id).toBe("watchdog");
      expect(result.hp[0]).toBe(10);
    });

    it("returns HP values", () => {
      const result = resolveMatrixRoster(matrix, 0, sampleIceCatalog);
      expect(result.hp.length).toBe(1);
      expect(result.hp[0]).toBe(10);
      expect(result.ice.length).toBe(result.hp.length);
    });

    it("resolves boss ICE", () => {
      const { ice, hp } = resolveMatrixRoster(matrix, 4, sampleIceCatalog);
      expect(ice[0]?.id).toBe("wintermute");
      expect(hp[0]).toBe(50);
    });

    it("returns empty for invalid node", () => {
      const result = resolveMatrixRoster(matrix, 99, sampleIceCatalog);
      expect(result.ice.length).toBe(0);
      expect(result.hp.length).toBe(0);
    });

    it("uses fallback for missing ICE", () => {
      const matrix2: Matrix = {
        nodes: [
          {
            id: 0,
            zone: "surface",
            iceIds: ["missing_ice"],
            iceHp: [100],
            reward: { credits: 50 },
            isBoss: false,
            adjacent: [],
          },
        ],
        startNode: 0,
        bossNode: 0,
      };
      const result = resolveMatrixRoster(matrix2, 0, sampleIceCatalog);
      expect(result.ice.length).toBe(1);
      expect(result.ice[0]).toBeDefined();
    });

    it("handles empty catalog", () => {
      const result = resolveMatrixRoster(matrix, 0, {});
      expect(result.ice.length).toBe(0);
      expect(result.hp.length).toBe(0);
    });

    it("returns parallel arrays", () => {
      const { ice, hp } = resolveMatrixRoster(matrix, 0, sampleIceCatalog);
      expect(ice.length).toBe(hp.length);
    });
  });

  describe("generateProceduralMatrix", () => {
    it("generates matrix from seed", () => {
      const matrix = generateProceduralMatrix(1, 42);
      expect(matrix.nodes.length).toBeGreaterThan(0);
    });

    it("has startNode", () => {
      const matrix = generateProceduralMatrix(1, 42);
      expect(matrix.startNode).toBeGreaterThanOrEqual(0);
    });

    it("has bossNode", () => {
      const matrix = generateProceduralMatrix(1, 42);
      expect(matrix.bossNode).toBeGreaterThanOrEqual(0);
    });

    it("deterministic for same seed", () => {
      const m1 = generateProceduralMatrix(1, 42);
      const m2 = generateProceduralMatrix(1, 42);
      expect(m1.nodes.length).toBe(m2.nodes.length);
    });

    it("different for different seeds", () => {
      const m1 = generateProceduralMatrix(1, 42);
      const m2 = generateProceduralMatrix(1, 99);
      expect(m1).not.toEqual(m2);
    });

    it("scales with mission grade", () => {
      const m1 = generateProceduralMatrix(1, 42);
      const m2 = generateProceduralMatrix(5, 42);
      expect(m1.nodes.length).toBeLessThanOrEqual(m2.nodes.length);
    });
  });

  describe("edge cases", () => {
    it("buildMatrix with single catalog entry", () => {
      const catalog = { only: sampleIceCatalog.watchdog };
      const matrix = buildMatrix(catalog);
      expect(matrix.nodes.length).toBe(5);
    });

    it("resolveMatrixRoster with multiple ICE", () => {
      const matrix: Matrix = {
        nodes: [
          {
            id: 0,
            zone: "surface",
            iceIds: ["watchdog", "guardian"],
            iceHp: [10, 20],
            reward: { credits: 50 },
            isBoss: false,
            adjacent: [],
          },
        ],
        startNode: 0,
        bossNode: 0,
      };
      const { ice, hp } = resolveMatrixRoster(matrix, 0, sampleIceCatalog);
      expect(ice.length).toBe(2);
      expect(hp.length).toBe(2);
    });

    it("advanceNode completing full path", () => {
      const matrix = buildMatrix(sampleIceCatalog);
      let node = 0;
      for (let i = 0; i < 5; i++) {
        node = advanceNode(matrix, node);
      }
      expect(node).toBe(4);
    });
  });
});
