import type { Grid } from "../core/types.ts";
import type { Mission } from "../core/types.ts";
import { makeGrid } from "../core/grid.ts";

export function renderMissionBriefing(_mission: Mission | null): Grid {
    return makeGrid(0, 0);
}