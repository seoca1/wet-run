import type { Grid } from "../core/types.ts";
import type { State } from "../core/types.ts";
import { makeGrid } from "../core/grid.ts";

export function renderCharacterStatus(_state: State | null): Grid {
    // Return an empty grid for now
    return makeGrid(0, 0);
}