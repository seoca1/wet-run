import type { Grid } from "../core/types";
import type { State } from "../core/types";
import { makeGrid } from "../core/grid";

export function renderCharacterStatus(_state: State | null): Grid {
  // Return an empty grid for now
  return makeGrid(0, 0);
}
