/** Combat grid rendering — the in-game (combat) ASCII layout.
 *
 * Extracted from `main.ts` so the layout, including the per-target status
 * glyph placement of proposal P14, is unit-testable without booting the
 * canvas renderer.
 */
import { makeGrid, setText, type Grid } from "../core/grid.ts";
import type { GameState } from "../core/types.ts";
import { PALETTE, iceColor } from "./palette.ts";
import {
  centerArt,
  formatStatusLabel,
  healthBar,
  healthColor,
  hitFlashColor,
  ICE_DEFEAT_ART,
  PLAYER_DEFEAT_ART,
} from "./vfx.ts";
import {
  drawTargetStatus,
  statusGroupForTarget,
  type TargetStatusGroup,
} from "./status_hud.ts";

export function renderGrid(
  state: GameState,
  iceHpDelta: number | null = null,
  playerHpDelta: number | null = null,
  statusGroups: readonly TargetStatusGroup[] = [],
  cols = 80,
  rows = 50,
): Grid {
  let grid = makeGrid(cols, rows);
  // Layout-relative anchors: ICE block centered horizontally; HUD bars near top-left.
  const iceCol = Math.max(20, Math.floor(cols * 0.45));
  const iceNameCol = iceCol + 1;
  const iceStatusCol = iceCol + Math.min(20, cols - iceCol - 6);
  const turnCol = Math.max(iceNameCol, cols - Math.floor(cols * 0.25));
  const statusArtCol = Math.max(20, Math.floor(cols * 0.45));
  const handRow = Math.max(8, rows - Math.floor(rows * 0.16));
  const artWidth = Math.min(32, cols - statusArtCol - 2);

  grid = setText(
    grid,
    2,
    1,
    `Mission: ${state.mission.title}`,
    PALETTE.GREEN_NEON,
  );
  grid = setText(grid, 2, 3, state.message, PALETTE.GRAY_LIGHT);

  grid = setText(
    grid,
    turnCol,
    1,
    `T${state.turnCount + 1}`,
    PALETTE.GRAY_LIGHT,
  );

  const playerHpText = `P ${healthBar(state.player.hp, state.player.maxHp)} ${state.player.hp}/${state.player.maxHp}`;
  grid = setText(
    grid,
    2,
    5,
    playerHpText,
    playerHpDelta !== null
      ? hitFlashColor(playerHpDelta)
      : healthColor(state.player.hp, state.player.maxHp),
  );

  grid = drawTargetStatus(
    grid,
    2 + playerHpText.length + 1,
    5,
    statusGroupForTarget(statusGroups, "player"),
    PALETTE.YELLOW_AMBER,
  );

  if (
    state.phase === "combat" ||
    state.phase === "victory" ||
    state.phase === "defeat"
  ) {
    const rosterStartRow = Math.floor(rows * 0.44);
    for (let i = 0; i < state.iceRoster.length; i++) {
      const ice = state.iceRoster[i];
      const row = rosterStartRow + i * 3;
      if (row + 2 >= rows) break;
      const isTarget = i === state.activeIceIndex;
      const marker = isTarget ? ">" : " ";
      const alive = ice.hp > 0;
      const iceHp = Math.max(0, ice.hp);

      // Name line: "> [1] ICE_NAME" or "  [1] ICE_NAME"
      const nameText = `${marker} [${i + 1}] ${ice.name.slice(0, 10)}`;
      grid = setText(
        grid,
        iceCol - 2,
        row,
        nameText,
        alive ? iceColor(ice.tier) : PALETTE.GRAY_MID,
      );

      // Status effects for this roster slot only (P14): each ICE shows the
      // effects it carries, not the merged set of every effect on the roster.
      grid = drawTargetStatus(
        grid,
        iceStatusCol,
        row,
        statusGroupForTarget(statusGroups, "ice", i),
        PALETTE.YELLOW_AMBER,
      );

      // HP bar line
      if (alive) {
        const delta = isTarget && iceHpDelta !== null ? iceHpDelta : null;
        grid = setText(
          grid,
          iceCol,
          row + 2,
          `${healthBar(iceHp, 100)} ${iceHp}/100`,
          delta !== null ? hitFlashColor(delta) : healthColor(iceHp, 100),
        );
      } else {
        grid = setText(grid, iceCol, row + 2, "[DEAD]", PALETTE.GRAY_MID);
      }
    }
  }

  const statusLabel = formatStatusLabel(state.phase);
  if (statusLabel !== "") {
    const statusColor =
      state.phase === "victory" ? PALETTE.GREEN_NEON : PALETTE.RED_BRIGHT;
    const statusRow = Math.floor(rows * 0.52);
    grid = setText(grid, statusArtCol, statusRow, statusLabel, statusColor);
    if (state.phase === "victory") {
      const art = centerArt(ICE_DEFEAT_ART, artWidth);
      let y = statusRow + 2;
      for (const line of art) {
        if (y >= rows) break;
        grid = setText(grid, statusArtCol, y, line, PALETTE.GRAY_MID);
        y += 1;
      }
    } else if (state.phase === "defeat") {
      const art = centerArt(PLAYER_DEFEAT_ART, artWidth);
      let y = statusRow + 2;
      for (const line of art) {
        if (y >= rows) break;
        grid = setText(grid, statusArtCol, y, line, PALETTE.GRAY_MID);
        y += 1;
      }
    }
  }

  if (state.phase === "combat" && state.deck.length > 0) {
    grid = setText(grid, 2, handRow, "HAND:", PALETTE.YELLOW_AMBER);
    let x = 9;
    for (const p of state.deck) {
      if (x >= cols - 6) break;
      const label = `[${p.id.slice(0, 4)}]`;
      grid = setText(grid, x, handRow, label, PALETTE.CYAN_LIGHT);
      x += label.length + 1;
    }
  }
  return grid;
}
