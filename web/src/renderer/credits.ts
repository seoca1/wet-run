import type { Grid } from "../core/types.ts";
import { makeGrid } from "../core/grid.ts";

export function renderCreditsScreen(_state: import("../core/state.ts").GameState | null): Grid {
    return makeGrid(0, 0);
}