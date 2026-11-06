/** What a route costs and what it pays — the run's shape, before committing.
 *
 * ADR-0281. The matrix has always offered a genuine choice: in `first_jack` the
 * routes out of the start are `0 -> 2 -> 5` (boss only, no fight on the way) and
 * `0 -> 1 -> 3 -> 5` (through the encounter at node 1). Which one you take
 * decides how long the mission is, and therefore how much the deck grows and how
 * likely the run is to finish. Nothing showed that.
 *
 * ADR-0280 measured the wall that makes this matter: at grades 4-6 a runner dies
 * in its FIRST fight (0.6-0.8 fights/run), so it never collects a card reward —
 * "you need cards to win, and wins to get cards". Healing, a softer curve and a
 * stronger deck all failed to open grades 5-6; the mission's LENGTH is the lever
 * that is left, and length is a choice the player can make.
 *
 * Pure reads over the matrix. No RNG, no clock; nothing here is state.
 */
import type { Matrix } from "../types";

export interface RoutePreview {
  /** Encounters on the shortest route from the destination to the boss,
   * counting the destination if it holds one and always counting the boss. */
  readonly fightsToBoss: number;
  /** Every unresolved encounter still reachable from the destination — the
   * most a runner could choose to take. Equal to `fightsToBoss` when the graph
   * forces the route. */
  readonly fightsAvailable: number;
  /** Credits on the nodes counted by `fightsAvailable`. */
  readonly creditsAvailable: number;
  /** True when the destination is itself the boss. */
  readonly destinationIsBoss: boolean;
}

/** Is this node an encounter the runner has not resolved? */
function unresolved(
  matrix: Matrix,
  cleared: ReadonlySet<number>,
  bypassed: ReadonlySet<number>,
  index: number,
): boolean {
  const node = matrix.nodes[index];
  if (!node || node.iceIds.length === 0) return false;
  return !cleared.has(index) && !bypassed.has(index);
}

/**
 * Preview a route from `destination`.
 *
 * `fightsToBoss` walks outward and stops at the first reachable boss, so it
 * answers "if I go this way, how many fights until the end". `fightsAvailable`
 * counts everything still open beyond it, so the two differ exactly where the
 * graph branches — which is where the choice lives.
 */
export function routePreview(
  matrix: Matrix,
  clearedNodes: readonly number[],
  bypassedNodes: readonly number[],
  destination: number,
): RoutePreview {
  const cleared = new Set(clearedNodes);
  const bypassed = new Set(bypassedNodes);
  const { nodes, bossNode } = matrix;

  if (!nodes[destination]) {
    return {
      fightsToBoss: 0,
      fightsAvailable: 0,
      creditsAvailable: 0,
      destinationIsBoss: false,
    };
  }

  // Reachability, for "what is still on offer beyond this route".
  const seen = new Set<number>([destination]);
  const queue: number[] = [destination];
  while (queue.length > 0) {
    const at = queue.shift() as number;
    for (const next of nodes[at]?.adjacent ?? []) {
      if (seen.has(next)) continue;
      seen.add(next);
      queue.push(next);
    }
  }
  const reachable = [...seen].filter((i) =>
    unresolved(matrix, cleared, bypassed, i),
  );
  const creditsAvailable = reachable.reduce(
    (sum, i) => sum + (nodes[i]?.reward.credits ?? 0),
    0,
  );

  // Fewest fights from the destination to the boss: a 0-1 BFS where landing on
  // an unresolved encounter costs one. That is the honest answer to "if I go
  // this way, how many fights until the end", including a branching graph where
  // some nodes can be walked past.
  // Arriving at an encounter means fighting it, so the destination itself costs
  // one when it holds an unresolved ICE (moving onto a node opens its gate).
  const cost = new Map<number, number>([
    [destination, unresolved(matrix, cleared, bypassed, destination) ? 1 : 0],
  ]);
  const deque: number[] = [destination];
  while (deque.length > 0) {
    const at = deque.shift() as number;
    const atCost = cost.get(at) ?? 0;
    for (const next of nodes[at]?.adjacent ?? []) {
      const step = unresolved(matrix, cleared, bypassed, next) ? 1 : 0;
      const cand = atCost + step;
      const known = cost.get(next);
      if (known !== undefined && known <= cand) continue;
      cost.set(next, cand);
      if (step === 0) deque.unshift(next);
      else deque.push(next);
    }
  }
  const fightsToBoss = cost.get(bossNode) ?? 0;

  return {
    fightsToBoss,
    fightsAvailable: reachable.length,
    creditsAvailable,
    destinationIsBoss: destination === bossNode,
  };
}

/** One short line for the route card, or "" when there is nothing to say. */
export function routePreviewLine(preview: RoutePreview): string {
  const { fightsToBoss, fightsAvailable, creditsAvailable } = preview;
  if (fightsAvailable === 0) return "route: clear — no ICE left";
  // Kept inside CARD_WIDTH (36) so the matrix card never clips the choice.
  if (fightsAvailable > fightsToBoss) {
    return `route: ${fightsToBoss} to boss · ${fightsAvailable} open · ${creditsAvailable}cr`;
  }
  return `route: ${fightsToBoss} fight${fightsToBoss === 1 ? "" : "s"} · ${creditsAvailable}cr`;
}

/** The next hop from `from` that leads to the boss in the fewest fights.
 *
 * The counterpart to the route line: `routePreview` says what a route costs,
 * this walks the cheapest one. Used by the run policy to model a player who
 * skips encounters on purpose (ADR-0281 measurement), so the spread between
 * "take every fight" and "take the shortest line" can be measured.
 */
export function fewestFightsNextHop(
  matrix: Matrix,
  clearedNodes: readonly number[],
  bypassedNodes: readonly number[],
  from: number,
): number | null {
  const cleared = new Set(clearedNodes);
  const bypassed = new Set(bypassedNodes);
  const { nodes, bossNode } = matrix;
  if (!nodes[from]) return null;

  const cost = new Map<number, number>([
    [from, unresolved(matrix, cleared, bypassed, from) ? 1 : 0],
  ]);
  const next = new Map<number, number>();
  const deque: number[] = [from];
  while (deque.length > 0) {
    const at = deque.shift() as number;
    const atCost = cost.get(at) ?? 0;
    for (const to of nodes[at]?.adjacent ?? []) {
      const step = unresolved(matrix, cleared, bypassed, to) ? 1 : 0;
      const cand = atCost + step;
      const known = cost.get(to);
      if (known !== undefined && known <= cand) continue;
      cost.set(to, cand);
      next.set(to, at === from ? to : (next.get(at) ?? to));
      if (step === 0) deque.unshift(to);
      else deque.push(to);
    }
  }
  if (from === bossNode) return null;
  return next.get(bossNode) ?? null;
}
