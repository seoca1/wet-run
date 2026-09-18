import { makeGrid } from "../core/grid.ts";
import { GameState as State } from "../core/state.ts";

export function renderCreditsScreen(state: State | null): Grid {
    return makeGrid(0, 0);
}