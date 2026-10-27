/** Graph-directed navigation for the Tier 5 matrix node graph.
 *
 * The matrix is a *graph* (`MatrixNode.adjacent`), not a linear array. The
 * old reducer walked it as if it were a chain — it followed `adjacent[0]`
 * for every forward move — which degenerated into a 2-cycle between the
 * first two nodes and made the boss (and therefore every mission
 * completion) unreachable.
 *
 * These helpers replace that with breadth-first search over `adjacent`:
 * a forward move is the neighbour of the current node that lies on a
 * shortest path to the objective, so repeatedly pressing "forward"
 * always terminates at the objective.
 *
 * Both functions are pure and deterministic: they depend only on
 * `(matrix, from, target)`, never on module state, wall-clock time or
 * randomness. Neighbour iteration follows the `adjacent` array order, so
 * two matrices with the same shape always produce the same hop.
 */
import type { Matrix } from "./types.ts";

/** Sentinel returned when no hop exists toward the requested target. */
export const NO_HOP = -1;

/**
 * Breadth-first search over `MatrixNode.adjacent` recording, for every
 * reachable node, the first neighbour that leads toward the target.
 *
 * The returned map holds `hop[target] === target` and, for every other
 * reachable node, the neighbour to step to next. Iterating `adjacent` in
 * array order keeps the chosen shortest path deterministic.
 *
 * @param matrix - The run matrix to traverse.
 * @param from - Node index the search starts at.
 * @param target - Node index the search aims for.
 * @returns Map of node index to its next hop toward `target`, or an empty
 *   map when `from` is out of range.
 */
function bfsToward(
  matrix: Matrix,
  from: number,
  target: number,
): Map<number, number> {
  const hops = new Map<number, number>();
  const nodeCount = matrix.nodes.length;
  if (from < 0 || from >= nodeCount) return hops;
  if (target < 0 || target >= nodeCount) return hops;
  if (from === target) return hops;

  const visited = new Set<number>([from]);
  let frontier: number[] = [from];

  while (frontier.length > 0) {
    const nextFrontier: number[] = [];
    for (const current of frontier) {
      const node = matrix.nodes[current];
      if (!node) continue;
      for (const neighbour of node.adjacent) {
        if (neighbour < 0 || neighbour >= nodeCount) continue;
        if (visited.has(neighbour)) continue;
        visited.add(neighbour);
        hops.set(neighbour, current);
        if (neighbour === target) {
          // Reconstruct the chain from `target` back to `from`. `hops` maps a
          // node to the node it was reached FROM, so the forward hop out of
          // `from` is the child whose parent is `from`.
          const chain = new Map<number, number>();
          let cursor = target;
          while (cursor !== from) {
            const parent = hops.get(cursor);
            if (parent === undefined) break;
            chain.set(parent, cursor);
            cursor = parent;
          }
          return chain;
        }
        nextFrontier.push(neighbour);
      }
    }
    frontier = nextFrontier;
  }
  return hops;
}

/**
 * The next node to step to when travelling from `from` toward `target`.
 *
 * Returns the *neighbour* of `from` on a shortest path — never `target`
 * itself, unless `from === target` (in which case there is nothing to
 * step to and `-1` is returned).
 *
 * @param matrix - The run matrix to traverse.
 * @param from - Node index the traveller is currently on.
 * @param target - Node index the traveller aims for.
 * @returns The next node index, or `-1` when `target` is unreachable from
 *   `from` (or the indices are out of range).
 */
export function nextHopToward(
  matrix: Matrix,
  from: number,
  target: number,
): number {
  if (from === target) return NO_HOP;
  const chain = bfsToward(matrix, from, target);
  const hop = chain.get(from);
  return hop ?? NO_HOP;
}

/**
 * Number of hops on a shortest path from `from` to `target`.
 *
 * @param matrix - The run matrix to traverse.
 * @param from - Node index the traveller starts at.
 * @param target - Node index the traveller aims for.
 * @returns The hop count, `0` when `from === target`, or `-1` when
 *   `target` is unreachable from `from`.
 */
export function pathLengthBetween(
  matrix: Matrix,
  from: number,
  target: number,
): number {
  if (from === target) return 0;
  const nodeCount = matrix.nodes.length;
  if (from < 0 || from >= nodeCount) return NO_HOP;
  if (target < 0 || target >= nodeCount) return NO_HOP;

  const visited = new Set<number>([from]);
  let frontier: number[] = [from];
  let depth = 0;

  while (frontier.length > 0) {
    const nextFrontier: number[] = [];
    for (const current of frontier) {
      const node = matrix.nodes[current];
      if (!node) continue;
      for (const neighbour of node.adjacent) {
        if (neighbour < 0 || neighbour >= nodeCount) continue;
        if (visited.has(neighbour)) continue;
        if (neighbour === target) return depth + 1;
        visited.add(neighbour);
        nextFrontier.push(neighbour);
      }
    }
    frontier = nextFrontier;
    depth += 1;
  }
  return NO_HOP;
}
