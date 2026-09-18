import { makeGrid } from "../core/grid.ts";
import { GameState as State } from "../core/state.ts";

export function renderLoadingScreen(state: State | null): Grid {
    return makeGrid(0, 0);
}