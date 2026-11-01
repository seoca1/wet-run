import type { GameState } from "../src/core/types";
import { applyAction } from "../src/core/state/state";

export function breachEncounter(state: GameState): GameState {
  let selected = applyAction(state, { type: "confirm" });
  for (let index = 0; index < 3; index += 1) {
    selected = applyAction(selected, { type: "move_south" });
  }
  return applyAction(selected, { type: "confirm" });
}
