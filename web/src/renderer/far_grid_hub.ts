/** Far Grid hub renderer (ADR-0213, Phase 1).
 *
 * Mirrors the mission select layout convention (header / intro / list /
 * footer) so the player gets the same navigation muscle memory. Renders
 * Far Grid-tagged missions as a separate list, framing the Far Grid as
 * a destination set apart from the Sprawl's regular mission board.
 *
 * Wave 2 (ADR-0213): also shows the SELECTED mission's `briefing` (if any)
 * in a detail block below the list. The block is omitted entirely when no
 * mission is selected, the mission has no `briefing`, or the grid is too
 * short to fit even one line of detail.
 */
import type { Grid, Mission } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { t, type Language } from "../core/i18n.ts";
import { PALETTE } from "./palette.ts";

/** Word-wrap a string to lines no longer than `width` columns.
 *
 * Words longer than `width` are hard-broken (per-character) so output never
 * exceeds the cap; any line that would still exceed the cap after wrapping
 * (i.e. an over-long word) is sliced and suffixed with "..." to mirror the
 * truncation style of `renderNPCDialogueScreen` (renderer/menu.ts).
 */
function wrapBriefing(text: string, width: number): ReadonlyArray<string> {
  if (width <= 0) return [];
  const cap = Math.max(1, width);
  const out: string[] = [];
  const words = text.split(/\s+/).filter((w) => w.length > 0);
  let line = "";
  for (const word of words) {
    if (word.length > cap) {
      // Flush any accumulated line first.
      if (line.length > 0) {
        out.push(line);
        line = "";
      }
      // Slice the over-long word and ellipsize the final piece.
      let i = 0;
      while (i + cap < word.length) {
        out.push(word.slice(i, i + cap));
        i += cap;
      }
      const tail = word.slice(i);
      out.push(tail.length === cap ? tail : tail + "…");
      continue;
    }
    if (line.length === 0) {
      line = word;
    } else if (line.length + 1 + word.length <= cap) {
      line = `${line} ${word}`;
    } else {
      out.push(line);
      line = word;
    }
  }
  if (line.length > 0) out.push(line);
  return out;
}

/** Render the Far Grid hub screen.
 *
 * Layout (matches mission_select convention from main.ts):
 *   row 1           : header "FAR GRID HUB"
 *   row 3           : intro line framing Far Grid as set apart from Sprawl
 *   row 5..         : mission list (title per row, ▸ marker on selected)
 *   row N           : empty-list message when missions array is empty
 *   below list      : briefing of selected mission (Wave 2, optional)
 *   status line     : optional statusMessage at rows-3 (unchanged)
 *   footer          : ESC/ENTER hints at rows-2 (unchanged)
 */
export function renderFarGridHub(
  missions: ReadonlyArray<Mission>,
  selected: number,
  cols: number,
  rows: number,
  statusMessage: string = "",
  language: Language = "en",
): Grid {
  let grid = makeGrid(cols, rows);

  // Header (mirrors mission_select's "WET RUN — Select Mission" line)
  grid = setText(
    grid,
    2,
    1,
    t("far_grid.header", language),
    PALETTE.GREEN_NEON,
  );

  // Intro — frame the Far Grid as set apart from Sprawl's mission board
  grid = setText(grid, 2, 3, t("far_grid.intro", language), PALETTE.GRAY_LIGHT);

  // Mission list — start at row 5 to mirror mission_select's spacing
  const listStartY = 5;
  if (missions.length === 0) {
    grid = setText(
      grid,
      2,
      listStartY,
      t("far_grid.empty", language),
      PALETTE.GRAY_DARK,
    );
  } else {
    let y = listStartY;
    for (let i = 0; i < missions.length; i++) {
      const m = missions[i];
      if (!m) continue;
      const isSelected = i === selected;
      const fg = isSelected ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
      const marker = isSelected ? "▸" : " ";
      const source = m.story?.source
        ? ` [Source: ${m.story.source.slice(0, 60)}]`
        : "";
      const titleText =
        language === "ko" && m.title_ko !== undefined && m.title_ko.length > 0
          ? m.title_ko
          : m.title;
      grid = setText(grid, 4, y, `${marker} ${titleText}${source}`, fg);
      y += 1;
    }
  }

  // Optional status line — placed just above the footer, only when given.
  if (statusMessage) {
    const statusY = rows - 3;
    if (statusY > listStartY) {
      grid = setText(grid, 2, statusY, statusMessage, PALETTE.YELLOW_AMBER);
    }
  }

  // Footer — mirror mission_select's "↑↓: navigate | ENTER: launch | ESC: back"
  const footerY = rows - 2;
  grid = setText(
    grid,
    2,
    footerY,
    t("far_grid.footer", language),
    PALETTE.GRAY_DARK,
  );

  // Briefing block (Wave 2, ADR-0213) — selected mission's briefing,
  // wrapped to (cols - 4) columns (matching the 2-col indent of the intro),
  // rendered between the list and the status/footer band. Skipped silently
  // when no selection, no briefing, or insufficient room.
  const selectedMission = missions[selected];
  if (selectedMission !== undefined && selectedMission.briefing !== undefined) {
    const briefText =
      language === "ko" &&
      selectedMission.briefing_ko !== undefined &&
      selectedMission.briefing_ko.length > 0
        ? selectedMission.briefing_ko
        : selectedMission.briefing;
    const maxWidth = Math.max(1, cols - 4);
    const lines = wrapBriefing(briefText, maxWidth);
    // Reserve: footer at footerY; if statusMessage present the visible band
    // shrinks to rows - 4. We always leave 1 blank line of headroom before
    // the status line / footer.
    const reserveRows = statusMessage ? 4 : 2;
    const lastAllowedY = rows - reserveRows;
    const startY = listStartY + missions.length + 1;
    const maxLines = Math.max(0, lastAllowedY - startY);
    const toRender = lines.slice(0, maxLines);
    for (let i = 0; i < toRender.length; i++) {
      grid = setText(
        grid,
        2,
        startY + i,
        toRender[i] ?? "",
        PALETTE.GRAY_LIGHT,
      );
    }
  }

  return grid;
}
