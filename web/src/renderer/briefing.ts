import type { Grid } from "../core/types";
import type { Mission } from "../core/types";
import { makeGrid } from "../core/grid";

export function renderMissionBriefing(_mission: Mission | null): Grid {
  return makeGrid(0, 0);
}
