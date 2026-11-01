/** Matrix travel animation (ADR-0249 follow-up): a committed move is drawn as
 * `@` running the corridor it already crossed, then landing on the room.
 *
 * Purely visual. The reducer has already moved `@` (`applyMatrixAction`
 * changes `currentNodeIndex` in the confirming action); this module only
 * decides how the next ~220 ms of frames look. It reads the wall clock that
 * the caller passes in, never `Math.random`, and its state lives on the
 * controller, never on `GameState`, so nothing here is saved, replayed or
 * seen by the balance harness. Reduced motion (ADR-0236) means no travel.
 */
import type { GameState, Grid } from "../core/types";
import { setCell } from "../core/grid";
import { PALETTE } from "./palette";
import type { PanelRect } from "./panel";
import type { BoardPlan } from "./matrix_board_layout";
import type { CorridorSet } from "./matrix_board_routes";
import type { MatrixPosition } from "./matrix_nodes";
import { suppressMotion } from "./accessibility_modes";
import {
  corridorGlyph,
  drawBoard,
  frontierOf,
  putInside,
  roomToken,
  tokenColour,
} from "./matrix_board";

/** `@` runs the corridor for this long. */
export const TRAVEL_TRANSIT_MS = 160;
/** Then the destination flashes as it receives `@`. */
export const TRAVEL_ARRIVAL_MS = 60;
export const TRAVEL_TOTAL_MS = TRAVEL_TRANSIT_MS + TRAVEL_ARRIVAL_MS;

/** A traversal in progress. Controller-owned and transient: it is never put
 * on `GameState`, so it cannot reach a save, the reducer or the harness. */
export interface MatrixTravel {
  readonly from: number;
  readonly to: number;
  /** Wall-clock start (the caller's clock, e.g. `performance.now()`). */
  readonly startedMs: number;
}

/** What one frame of a traversal draws. `progress` is 0..1 along the
 * corridor during `transit` and 1 during `arrival`. */
export interface MatrixTravelFrame {
  readonly from: number;
  readonly to: number;
  readonly phase: "transit" | "arrival";
  readonly progress: number;
}

/** Start a traversal when `previous -> next` is one confirmed move along one
 * adjacency; otherwise null. Null when reduced motion suppresses travel, so
 * the board shows the arrival at once with no intermediate frame. */
export function beginMatrixTravel(
  previous: GameState,
  next: GameState,
  nowMs: number,
  reducedMotion: boolean,
): MatrixTravel | null {
  if (suppressMotion("travel", reducedMotion)) return null;
  if (previous.runPhase !== "matrix" || next.runPhase !== "matrix") return null;
  const matrix = next.matrix;
  if (matrix == null || matrix !== previous.matrix) return null;
  const from = previous.currentNodeIndex;
  const to = next.currentNodeIndex;
  // Only the confirmed target, one edge away (rules 3 and 8).
  if (from === to || previous.selectedMatrixNodeIndex !== to) return null;
  if (!matrix.nodes[from]?.adjacent.includes(to)) return null;
  return { from, to, startedMs: nowMs };
}

/** The frame to draw at `nowMs`, or null once the traversal is over. */
export function matrixTravelFrame(
  travel: MatrixTravel | null,
  nowMs: number,
): MatrixTravelFrame | null {
  if (travel === null) return null;
  const t = Math.max(0, nowMs - travel.startedMs);
  if (t >= TRAVEL_TOTAL_MS) return null;
  const { from, to } = travel;
  if (t >= TRAVEL_TRANSIT_MS)
    return { from, to, phase: "arrival", progress: 1 };
  const x = t / TRAVEL_TRANSIT_MS;
  // Ease out: quick departure, settling into the destination.
  return { from, to, phase: "transit", progress: 1 - (1 - x) * (1 - x) };
}

/** The cells of the one corridor routed for `from`-`to`, ordered from
 * `from`. Empty when the adjacency has no routed corridor. */
export function travelPath(
  routes: CorridorSet,
  from: number,
  to: number,
): CorridorSet["corridors"][number]["cells"] {
  const corridor = routes.corridors.find(
    (c) => (c.a === from && c.b === to) || (c.a === to && c.b === from),
  );
  if (!corridor) return [];
  return corridor.a === from ? corridor.cells : [...corridor.cells].reverse();
}

/** Arrival: the static board, with the destination token inverted for the
 * beat in which it receives `@`. */
function drawArrival(
  board: Grid,
  clip: PanelRect,
  plan: BoardPlan,
  to: number,
): Grid {
  const site = plan.sites[to];
  if (!site || site.cy < clip.y || site.cy >= clip.y + clip.height)
    return board;
  let out = board;
  for (let x = site.cx - 1; x <= site.cx + 1; x += 1) {
    const cell = out.get(x, site.cy);
    if (cell && x >= clip.x && x < clip.x + clip.width)
      out = setCell(
        out,
        { x, y: site.cy },
        { char: cell.char, fg: PALETTE.BACKGROUND, bg: PALETTE.GREEN_NEON },
      );
  }
  return out;
}

/** Draw the board for one traversal frame. `position` is the real (already
 * moved) state. Transit frames show the board as the player confirmed it,
 * with `@` lifted off the origin and running the committed corridor. */
export function drawTravelBoard(
  grid: Grid,
  clip: PanelRect,
  plan: BoardPlan,
  routes: CorridorSet,
  position: MatrixPosition,
  frame: MatrixTravelFrame,
): Grid {
  const { from, to } = frame;
  const path = travelPath(routes, from, to);
  if (frame.phase === "arrival" || path.length === 0) {
    const board = drawBoard(grid, clip, plan, routes, position);
    return frame.phase === "arrival"
      ? drawArrival(board, clip, plan, to)
      : board;
  }
  const before: MatrixPosition = { ...position, current: from, selected: null };
  let out = drawBoard(grid, clip, plan, routes, before);
  const step = Math.min(
    path.length - 1,
    Math.floor(frame.progress * path.length),
  );
  // The corridor lights up behind `@` as it runs toward the destination.
  for (const c of path.slice(0, step))
    out = putInside(
      out,
      clip,
      c.x,
      c.y,
      corridorGlyph("target", c.links),
      PALETTE.GREEN_NEON,
    );
  const here = path[step];
  if (here) out = putInside(out, clip, here.x, here.y, "@", PALETTE.GREEN_NEON);
  const origin = plan.sites[from];
  if (origin)
    out = putInside(
      out,
      clip,
      origin.cx - 1,
      origin.cy,
      roomToken(position, from),
      tokenColour(position, from, frontierOf(position)),
    );
  const destination = plan.sites[to];
  if (destination)
    out = putInside(
      out,
      clip,
      destination.cx - 1,
      destination.cy,
      roomToken({ ...before, selected: to }, to),
      PALETTE.GREEN_NEON,
    );
  return out;
}
