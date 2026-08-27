/** Matrix generation + node lookup (Tier 5).
 *
 * Mirrors Python `matrix/procgen.py` + `matrix/node.py` at the level
 * needed for the wet_run-web multi-stage run MVP. Generates a 5-node
 * linear+branching matrix per run: Surface → Mid → Deep → Core → Boss.
 *
 * Deterministic per seed (no Math.random at module load). ICE selection
 * per node uses the iceTypes lookup passed by the caller (we don't import
 * iceTypes here to keep this module pure / unit-testable).
 */
import type { Matrix, MatrixNode, ZoneDepth, Ice } from "./types.ts";

export const NUM_NODES = 5;
export const ZONE_BY_NODE_INDEX: ReadonlyArray<ZoneDepth> = [
  "surface",  // node 0: start
  "mid",      // node 1
  "deep",     // node 2
  "core",     // node 3
  "core-deep", // node 4: boss
];

/** Build a 5-node matrix: Surface → Mid → Deep → Core → Boss.
 *
 * Linear adjacency: node[i].adjacent = [i+1] (except last).
 * Boss at node 4. Each non-boss node has 1 ICE; boss node has 1 boss ICE.
 * ICE ids are placeholders resolved by main.ts against the iceTypes catalog.
 */
export function buildMatrix(
  iceCatalog: Readonly<Record<string, Ice>>,
): Matrix {
  const nodes: MatrixNode[] = [];
  const startNode = 0;
  const bossNode = NUM_NODES - 1;

  for (let i = 0; i < NUM_NODES; i++) {
    const isLast = i === bossNode;
    const isFirst = i === startNode;
    // Pick a default ICE id per zone (main.ts can override per run).
    const defaultIceId = isLast ? "wintermute" : "watchdog";
    const defaultIce = iceCatalog[defaultIceId] ?? Object.values(iceCatalog)[0];
    const iceIds = defaultIce ? [defaultIce.id] : [];
    const iceHp = defaultIce ? [defaultIce.hp] : [];
    const node: MatrixNode = {
      id: i,
      zone: ZONE_BY_NODE_INDEX[i] ?? "surface",
      iceIds,
      iceHp,
      reward: { credits: 50 + i * 25 },
      isBoss: isLast,
      adjacent: isLast ? [] : [i + 1],
    };
    nodes.push(node);
    // Suppress unused-var warning for isFirst (kept for future branching).
    void isFirst;
  }

  return { nodes, startNode, bossNode };
}

/** Linear advance: move to current node's adjacent (boss → final). */
export function advanceNode(matrix: Matrix, fromIndex: number): number {
  const node = matrix.nodes[fromIndex];
  if (!node || node.adjacent.length === 0) return fromIndex; // boss or invalid
  const next = node.adjacent[0];
  return next ?? fromIndex;
}

/** Check if a node index is the final (boss) node. */
export function isBossNode(matrix: Matrix, nodeIndex: number): boolean {
  const node = matrix.nodes[nodeIndex];
  return node?.isBoss ?? false;
}

/** Resolve iceIds in a matrix node to actual Ice objects from the catalog.
 * Returns parallel arrays of Ice + starting HP. If an iceId is missing,
 * falls back to the first available ICE in the catalog.
 */
export function resolveMatrixRoster(
  matrix: Matrix,
  nodeIndex: number,
  iceCatalog: Readonly<Record<string, Ice>>,
): { ice: ReadonlyArray<Ice>; hp: ReadonlyArray<number> } {
  const node = matrix.nodes[nodeIndex];
  if (!node) return { ice: [], hp: [] };
  const fallback = Object.values(iceCatalog)[0];
  if (!fallback) return { ice: [], hp: [] };
  const ice: Ice[] = [];
  const hp: number[] = [];
  for (let i = 0; i < node.iceIds.length; i++) {
    const id = node.iceIds[i];
    const entry = (id && iceCatalog[id]) || fallback;
    const hpVal = node.iceHp[i] ?? entry.hp;
    ice.push(entry);
    hp.push(hpVal);
  }
  return { ice, hp };
}