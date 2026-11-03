/** Combat grid rendering — the in-game (combat) ASCII layout.
 *
 * Extracted from `main.ts` so the layout, including the per-target status
 * glyph placement of proposal P14, is unit-testable without booting the
 * canvas renderer.
 *
 * ADR-0237 §2: the combat grid sits in a Green Grid frame (panel.ts) inset one
 * cell from the grid edge. Its right rail is the divider between the combat
 * area and the canvas HUD column, and a ╠═╣ rule separates the header
 * (mission, message, player HP) from the ICE field. Header and hand text are
 * placed relative to the inner rectangle; proportional rows/columns that would
 * land on a rail are clamped to it.
 */
import { makeGrid, type Grid } from "../core/grid";
import type { GameState } from "../core/types";
import { PALETTE, iceColor } from "./palette";
import {
  COMPACT_HAND_HEADER,
  FULL_ROW_WIDTH,
  combatHandRow,
  formatAffordanceRow,
  formatCompactAffordanceRow,
  programAffordances,
} from "../core/combat/program_affordance";
import {
  drawPanel,
  drawPanelSeparator,
  panelInnerRect,
  screenFrameRect,
  SCREEN_FRAME_INSET,
  setInnerText,
} from "./panel";
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
  const ruleY = SCREEN_FRAME_INSET + 1 + HEADER_RULE_OFFSET;
  const rosterStartRow = Math.floor(rows * 0.44);
  const handRow = combatHandRow(rows);
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
  handOnOverlay = false,
): Grid {
  let grid = makeGrid(cols, rows);
  const frame = screenFrameRect(grid);
  const inner = panelInnerRect(grid, frame);
  const innerRight = inner.x + inner.width;
  const innerBottom = inner.y + inner.height;
  const textX = inner.x + 1;
  const headerY = inner.y;
  // Layout-relative anchors: ICE block centered horizontally; HUD bars near top-left.
  const iceCol = Math.max(20, Math.floor(cols * 0.45));
  const iceNameCol = iceCol + 1;
  const iceStatusCol = iceCol + Math.min(20, innerRight - iceCol - 6);
  const turnCol = Math.max(iceNameCol, cols - Math.floor(cols * 0.25));
  const statusArtCol = Math.max(20, Math.floor(cols * 0.45));
  const showHand = state.phase === "combat" && state.deck.length > 0;
  const handRow = Math.min(
    innerBottom - 1,
    combatHandRow(rows, state.deck.length),
  );
  // ICE rows stop above the hand so a long roster can never cover a slot.
  const rosterBottom = showHand ? handRow : innerBottom;
  const artWidth = Math.min(32, innerRight - statusArtCol - 1);

  grid = setInnerText(
    grid,
    inner,
    textX,
    headerY,
    `Mission: ${state.mission.title}`,
    PALETTE.GREEN_NEON,
  );
  grid = setInnerText(
    grid,
    inner,
    textX,
    headerY + 2,
    state.message,
    PALETTE.GRAY_LIGHT,
  );

  grid = setInnerText(
    grid,
    inner,
    turnCol,
    headerY,
    `T${state.turnCount + 1}`,
    PALETTE.GRAY_LIGHT,
  );

  const playerHpText = `P ${healthBar(state.player.hp, state.player.maxHp)} ${state.player.hp}/${state.player.maxHp}`;
  grid = setInnerText(
    grid,
    inner,
    textX,
    headerY + 4,
    playerHpText,
    playerHpDelta !== null
      ? hitFlashColor(playerHpDelta)
      : healthColor(state.player.hp, state.player.maxHp),
  );

  grid = drawTargetStatus(
    grid,
    textX + playerHpText.length + 1,
    headerY + 4,
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
      if (row + 2 >= rosterBottom) break;
      const isTarget = i === state.activeIceIndex;
      const marker = isTarget ? ">" : " ";
      const alive = ice.hp > 0;
      const iceHp = Math.max(0, ice.hp);
      const iceMaxHp =
        ice.maxHp !== undefined && Number.isFinite(ice.maxHp) && ice.maxHp > 0
          ? ice.maxHp
          : 100;

      // Name line: "> [1] ICE_NAME" or "  [1] ICE_NAME"
      const nameText = `${marker} [${i + 1}] ${ice.name.slice(0, 10)}`;
      grid = setInnerText(
        grid,
        inner,
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
        grid = setInnerText(
          grid,
          inner,
          iceCol,
          row + 2,
          `${healthBar(iceHp, iceMaxHp)} ${iceHp}/${iceMaxHp}`,
          delta !== null ? hitFlashColor(delta) : healthColor(iceHp, iceMaxHp),
        );
      } else {
        grid = setInnerText(
          grid,
          inner,
          iceCol,
          row + 2,
          "[DEAD]",
          PALETTE.GRAY_MID,
        );
      }
    }
  }

  const statusLabel = formatStatusLabel(state.phase);
  if (statusLabel !== "") {
    const statusColor =
      state.phase === "victory" ? PALETTE.GREEN_NEON : PALETTE.RED_BRIGHT;
    const statusRow = Math.floor(rows * 0.52);
    grid = setInnerText(
      grid,
      inner,
      statusArtCol,
      statusRow,
      statusLabel,
      statusColor,
    );
    if (state.phase === "victory") {
      const art = centerArt(ICE_DEFEAT_ART, artWidth);
      let y = statusRow + 2;
      for (const line of art) {
        if (y >= innerBottom) break;
        grid = setInnerText(
          grid,
          inner,
          statusArtCol,
          y,
          line,
          PALETTE.GRAY_MID,
        );
        y += 1;
      }
    } else if (state.phase === "defeat") {
      const art = centerArt(PLAYER_DEFEAT_ART, artWidth);
      let y = statusRow + 2;
      for (const line of art) {
        if (y >= innerBottom) break;
        grid = setInnerText(
          grid,
          inner,
          statusArtCol,
          y,
          line,
          PALETTE.GRAY_MID,
        );
        y += 1;
      }
    }
  }

  if (showHand && !handOnOverlay) grid = drawHand(grid, inner, state, handRow);
  else if (state.phase === "defeat") {
    // ADR-0263: a screen with no way out is a trap, and ADR-0251 rule 5 says
    // a screen must state what it does. The prompt goes where the hand would
    // be — free on the defeat screen, which shows art there instead.
    grid = setInnerText(
      grid,
      inner,
      textX,
      handRow,
      "ENTER / ESC: return to title",
      PALETTE.GRAY_LIGHT,
    );
  }

  // Frame last, so an overlong message line can never erase a rail.
  grid = drawPanel(grid, frame).grid;
  const ruleY = combatHeaderRuleRow(rows);
  return ruleY === null ? grid : drawPanelSeparator(grid, frame, ruleY);
}

/** ADR-0251: one numbered row per slot, built only from runtime fields
 * (`programAffordances`): the digit that plays it, its name, the COST it
 * charges and the COST after it (or BLOCKED past the cap), and whether it
 * hits the targeted ICE or all of them. Narrow grids use the short row under
 * a column legend. */
function drawHand(
  grid: Grid,
  inner: ReturnType<typeof panelInnerRect>,
  state: GameState,
  handRow: number,
): Grid {
  const textX = inner.x + 1;
  const width = inner.x + inner.width - textX;
  const wide = width >= FULL_ROW_WIDTH;
  let out = setInnerText(
    grid,
    inner,
    textX,
    handRow,
    wide ? "HAND" : COMPACT_HAND_HEADER,
    PALETTE.YELLOW_AMBER,
  );
  for (const row of programAffordances(state)) {
    const y = handRow + row.slot;
    if (y >= inner.y + inner.height) break;
    out = setInnerText(
      out,
      inner,
      textX,
      y,
      wide ? formatAffordanceRow(row) : formatCompactAffordanceRow(row),
      row.blocked ? PALETTE.GRAY_MID : PALETTE.CYAN_LIGHT,
    );
  }
  return out;
}
