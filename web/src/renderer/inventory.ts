import type { Grid } from "../core/types.ts";
import type { State } from "../core/types.ts";
import { makeGrid } from "../core/grid.ts";

export function renderInventoryScreen(_state: State | null): Grid {
    return makeGrid(0, 0);
}