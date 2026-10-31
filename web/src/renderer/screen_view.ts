import type { Grid } from "../core/types";

export interface ScreenView {
  readonly grid: Grid;
  readonly hud: readonly string[];
  readonly colorFor?: (line: string) => string | undefined;
}
