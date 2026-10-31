import type { Grid } from "../core/types";
import { makeGrid } from "../core/grid";

export function renderLoadingScreen(
  _state: import("../core/state/state.ts").GameState | null,
): Grid {
  return makeGrid(0, 0);
}
