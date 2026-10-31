import type { Grid } from "../core/types";
import type { State } from "../core/types";
import { makeGrid } from "../core/grid";

export function renderCodexScreen(_state: State | null): Grid {
  return makeGrid(0, 0);
}
