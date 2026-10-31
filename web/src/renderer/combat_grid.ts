/** Combat grid rendering — the in-game (combat) ASCII layout.
 *
 * Extracted from `main.ts` so the layout, including the per-target status
 * glyph placement of proposal P14, is unit-testable without booting the
 * canvas renderer.
 *
 * ADR-0237 §2: the whole combat grid sits in a Green Grid frame (panel.ts).
 * Its right rail is the divider between the combat area and the canvas HUD
 * column, and a ╠═╣ rule separates the header (mission, message, player HP)
 * from the ICE field. Content positions are unchanged; only rows/columns that
 * would now land on a rail are clamped to the inner rectangle.
 */
import { makeGrid, setText, type Grid } from "../core/grid";
import type { GameState } from "../core/types";
import { PALETTE, iceColor } from "./palette";
import { drawPanel, drawPanelSeparator, panelInnerRect } from "./panel";
import {
  centerArt,
  formatStatusLabel,
  healthBar,
  healthColor,
  hitFlashColor,
  ICE_DEFEAT_ART,
  PLAYER_DEFEAT_ART,
} from "./vfx";
import {
  drawTargetStatus,
  statusGroupForTarget,
  type TargetStatusGroup,
} from "./status_hud";

/** Rows below the frame's top rail that the combat header occupies (1, 3, 5),
 * plus one blank row; the header rule is drawn on the next row. */
const HEADER_RULE_OFFSET = 6;

/** Row of the ╠═╣ header rule, or null when the grid is too short for the
 * rule to sit clear of the ICE roster and the combat-entry hint rows. */
export function combatHeaderRuleRow(rows: number): number | null {
  const ruleY = 1 + HEADER_RULE_OFFSET;
  const rosterStartRow = Math.floor(rows * 0.44);
  const handRow = Math.max(8, rows - Math.floor(rows * 0.16));
  return ruleY < Math.min(rosterStartRow, handRow - 2) - 1 ? ruleY : null;
}

/** Build the framed combat grid (header, ICE roster, phase art, hand). */
export function renderGrid(
  state: GameState,
  iceHpDelta: number | null = null,
  playerHpDelta: number | null = null,
  statusGroups: readonly TargetStatusGroup[] = [],
  cols = 80,
  rows = 50,
): Grid {
  let grid = makeGrid(cols, rows);
  const frame = { x: 0, y: 0, width: cols, height: rows };
  const inner = panelInnerRect(grid, frame);
  const innerRight = inner.x + inner.width;
  const innerBottom = inner.y + inner.height;
  // Layout-relative anchors: ICE block centered horizontally; HUD bars near top-left.
  const iceCol = Math.max(20, Math.floor(cols * 0.45));
  const iceNameCol = iceCol + 1;
  const iceStatusCol = iceCol + Math.min(20, innerRight - iceCol - 6);
  const turnCol = Math.max(iceNameCol, cols - Math.floor(cols * 0.25));
  const statusArtCol = Math.max(20, Math.floor(cols * 0.45));
  const handRow = Math.max(8, rows - Math.floor(rows * 0.16));
  const artWidth = Math.min(32, innerRight - statusArtCol - 1);

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
      if (row + 2 >= innerBottom) break;
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
        if (y >= innerBottom) break;
        grid = setText(grid, statusArtCol, y, line, PALETTE.GRAY_MID);
        y += 1;
      }
    } else if (state.phase === "defeat") {
      const art = centerArt(PLAYER_DEFEAT_ART, artWidth);
      let y = statusRow + 2;
      for (const line of art) {
        if (y >= innerBottom) break;
        grid = setText(grid, statusArtCol, y, line, PALETTE.GRAY_MID);
        y += 1;
      }
    }
  }

  if (state.phase === "combat" && state.deck.length > 0) {
    grid = setText(grid, 2, handRow, "HAND:", PALETTE.YELLOW_AMBER);
    let x = 9;
    for (const p of state.deck) {
      if (x >= innerRight - 5) break;
      const label = `[${p.id.slice(0, 4)}]`;
      grid = setText(grid, x, handRow, label, PALETTE.CYAN_LIGHT);
      x += label.length + 1;
    }
  }

  // Frame last, so an overlong message line can never erase a rail.
  grid = drawPanel(grid, frame).grid;
  const ruleY = combatHeaderRuleRow(rows);
  return ruleY === null ? grid : drawPanelSeparator(grid, frame, ruleY);
}
