/** Matrix exploration state + fog of war (ADR-0020).
 *
 * Ports the Python `wet_run.matrix.exploration` module to TypeScript.
 * Tracks which nodes the player has discovered / scanned / is currently
 * on, and computes a `Visibility` class for every node (CURRENT /
 * ADJACENT / DISCOVERED / UNKNOWN) so the renderer can paint fog of war.
 *
 * The graph is described by a tiny `MatrixGraphView` interface so this
 * module is decoupled from the `DungeonGraph` type and can be unit
 * tested with synthetic graphs (see `tests/exploration.test.ts`).
 *
 * Determinism: no RNG; all operations are pure state mutations.
 */

// ============================================================================
//  Graph view (minimal contract for visibility / adjacency queries)
// ============================================================================

/** Minimal graph contract used by exploration logic.
 *
 *  Both the procedural `DungeonGraph` and hand-rolled test fixtures
 *  implement this shape — keeping the dependency one-way so exploration
 *  is testable in isolation. */
export interface MatrixGraphView {
  /** Return ids of nodes directly reachable from `nodeId`. */
  neighbors(nodeId: string): ReadonlyArray<string>;
  /** Return True if there's a direct edge `src -> dst`. */
  isConnected(src: string, dst: string): boolean;
}

/** Build a `MatrixGraphView` from a flat edge list (test helper). */
export function graphViewFromEdges(edges: ReadonlyArray<readonly [string, string]>): MatrixGraphView {
  const adj = new Map<string, Set<string>>();
  for (const [a, b] of edges) {
    if (!adj.has(a)) adj.set(a, new Set());
    if (!adj.has(b)) adj.set(b, new Set());
    adj.get(a)!.add(b);
    adj.get(b)!.add(a);
  }
  return {
    neighbors: (nodeId) => Array.from(adj.get(nodeId) ?? []),
    isConnected: (src, dst) => (adj.get(src)?.has(dst) ?? false),
  };
}

// ============================================================================
//  Visibility
// ============================================================================

/** How visible a node is to the player (ADR-0020). */
export type Visibility = "current" | "adjacent" | "discovered" | "unknown";

/** Convenience ordering for fog-of-war rendering (least → most revealed). */
export const VISIBILITY_ORDER: Readonly<Record<Visibility, number>> = {
  unknown: 0,
  discovered: 1,
  adjacent: 2,
  current: 3,
};

// ============================================================================
//  Node kind helpers (mirrors Python `node.NodeKind`)
// ============================================================================

/** Node kind for visibility rules (entry/exit always visible). */
export type ExplorationNodeKind =
  | "entry"
  | "data"
  | "system"
  | "ice"
  | "construct"
  | "router"
  | "core"
  | "exit";

/** Whether a node of this kind should be visible from the start. */
export function isAlwaysVisibleKind(kind: ExplorationNodeKind): boolean {
  return kind === "entry" || kind === "exit";
}

// ============================================================================
//  Exploration state
// ============================================================================

/** Player progress through the matrix (ADR-0020).
 *
 *  - `current` — the node the player is on right now.
 *  - `discovered` — nodes the player has ever seen (entry, current, or
 *    previously visited).
 *  - `scanned` — nodes the player has explicitly probed (full ZDR info).
 *  - `path` — append-only visit history (used by the renderer to draw
 *    breadcrumb trails). The last entry is always equal to `current`. */
export class ExplorationState {
  current: string;
  readonly discovered: Set<string>;
  readonly scanned: Set<string>;
  readonly path: string[];

  constructor(current: string) {
    this.current = current;
    this.discovered = new Set<string>();
    this.scanned = new Set<string>();
    this.path = [];

    if (this.current !== "") {
      this.discovered.add(this.current);
    }
    if (this.current !== "" && (this.path.length === 0 || this.path[this.path.length - 1] !== this.current)) {
      this.path.push(this.current);
    }
  }

  /** Move to a new node. Adds to discovered + path. */
  visit(nodeId: string): void {
    this.current = nodeId;
    this.discovered.add(nodeId);
    if (this.path.length === 0 || this.path[this.path.length - 1] !== nodeId) {
      this.path.push(nodeId);
    }
  }

  /** Probe a node — marks it as fully scanned (ZDR info available). */
  probe(nodeId: string): void {
    this.scanned.add(nodeId);
  }

  /** Return ids of all nodes adjacent to the current node. */
  adjacentToCurrent(graph: MatrixGraphView): string[] {
    return graph.neighbors(this.current).slice();
  }

  /** True if the player can see the node at all (any non-UNKNOWN class). */
  isVisible(graph: MatrixGraphView, nodeId: string): boolean {
    return this.visibility(graph, nodeId) !== "unknown";
  }

  /** Compute the visibility class for a given node. */
  visibility(graph: MatrixGraphView, nodeId: string): Visibility {
    if (this.current !== "" && nodeId === this.current) return "current";
    if (this.discovered.has(nodeId)) return "discovered";
    if (graph.isConnected(this.current, nodeId) || graph.isConnected(nodeId, this.current)) {
      return "adjacent";
    }
    return "unknown";
  }

  /** True if the player has probed/scanned this node. */
  isScanned(nodeId: string): boolean {
    return this.scanned.has(nodeId);
  }

  /** Ids of nodes the player could move to from here (excludes current). */
  discoverableNow(graph: MatrixGraphView): string[] {
    return this.adjacentToCurrent(graph).filter((nid) => nid !== this.current);
  }

  /** True if the player has ever visited this node. */
  hasDiscovered(nodeId: string): boolean {
    return this.discovered.has(nodeId);
  }

  /** Reset to a fresh start (keeps the same `current` node if non-empty). */
  reset(): void {
    this.discovered.clear();
    this.scanned.clear();
    this.path.length = 0;
    if (this.current !== "") {
      this.discovered.add(this.current);
      this.path.push(this.current);
    }
  }
}

// ============================================================================
//  Node-event helpers (used by run-level state machines)
// ============================================================================

/** An event triggered when the player enters a node. */
export type NodeEventKind =
  | "enter_combat"
  | "enter_data"
  | "discover_anomaly"
  | "rest_heal"
  | "find_cache"
  | "trigger_trap";

/** Pick an event kind for the given room type (deterministic, no RNG). */
export function eventForRoomType(roomType: string): NodeEventKind {
  switch (roomType) {
    case "entry":
    case "exit":
    case "router":
    case "empty":
    case "core":
      return "enter_data";
    case "data":
      return "discover_anomaly";
    case "ice":
      return "enter_combat";
    case "npc":
      return "enter_combat";
    case "dead_end":
      return "find_cache";
    default:
      return "enter_data";
  }
}
