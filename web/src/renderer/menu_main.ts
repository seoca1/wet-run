/** Main menu definition + renderer (Tier 4, ADR-0207+/ADR-0209).
 *
 * Split from the former 1039-LOC `menu.ts` monolith (2026-10-12). This module
 * owns the menu option table and the top-level main-menu / stub screens.
 * Mirrors Python's main_menu.py (9 options: NEW_RUN, GRAPHIC_NOVEL,
 * CONTINUE, SETTINGS, CREDITS, HALL_OF_DEAD, HELP, ENDINGS, STATS).
 * Web Tier 4 implements the 6 reachable + 3 deferred (rendered as
 * "Coming soon" stubs to keep the menu 1:1 with Python for design parity).
 *
 * Layout: Green Grid frame (renderer/panel.ts) around a centred title block,
 * the numbered options and a footer pinned to the bottom inner rows. Selected
 * option highlighted with ▸ marker (matches mission select convention).
 */
import type { Grid } from "../core/types";
import { makeGrid, setText } from "../core/grid";
import { t, type Language } from "../core/i18n";
import { PALETTE } from "./palette";
import { formatNavIndex } from "./nav_index";
import {
  drawPanel,
  panelInnerRect,
  screenFrameRect,
  setInnerText,
  type PanelRect,
} from "./panel";

export type MenuOption =
  | "new_run"
  | "continue"
  | "settings"
  | "craft"
  | "equipment"
  | "credits"
  | "hall_of_dead"
  | "help"
  | "endings"
  | "stats"
  | "tutorial"
  | "far_grid_hub"
  | "dungeon_crawl";

/** All 14 menu options, grouped, each with a one-line description.
 *
 * ADR-0315: the flat list of 14 was an enumeration the player could not read —
 * CRAFT, EQUIPMENT and STATS said nothing about what they do. Entries now carry
 * a `desc` and a `group`, and the renderer prints the group header and the
 * description, so the column is a set of choices rather than a list of words.
 * The order is still a flat index (digit keys and up/down are unchanged).
 */
export interface MenuEntry {
  readonly key: MenuOption;
  /** i18n key for the label. */
  readonly label: string;
  /** i18n key for the one-line description. */
  readonly desc: string;
  readonly available: boolean;
  /** i18n key for the group header printed ABOVE this entry (undefined =
   * same group as the previous entry). */
  readonly group?: string;
}

export const MENU_OPTIONS: ReadonlyArray<MenuEntry> = [
  // PLAY
  { key: "continue", label: "menu.continue", desc: "menu.desc.continue", available: true, group: "menu.group.play" },
  { key: "new_run", label: "menu.new_run", desc: "menu.desc.new_run", available: true },
  { key: "far_grid_hub", label: "menu.far_grid_hub", desc: "menu.desc.far_grid_hub", available: true },
  { key: "dungeon_crawl", label: "menu.dungeon_crawl", desc: "menu.desc.dungeon_crawl", available: true },
  { key: "tutorial", label: "menu.tutorial", desc: "menu.desc.tutorial", available: true },
  // WORKSHOP
  { key: "craft", label: "menu.craft", desc: "menu.desc.craft", available: true, group: "menu.group.workshop" },
  { key: "equipment", label: "menu.equipment", desc: "menu.desc.equipment", available: true },
  // ARCHIVE
  { key: "hall_of_dead", label: "menu.hall_of_dead", desc: "menu.desc.hall_of_dead", available: true, group: "menu.group.archive" },
  { key: "endings", label: "menu.endings", desc: "menu.desc.endings", available: true },
  { key: "stats", label: "menu.stats", desc: "menu.desc.stats", available: true },
  // SYSTEM
  { key: "settings", label: "menu.settings", desc: "menu.desc.settings", available: true, group: "menu.group.system" },
  { key: "help", label: "menu.help", desc: "menu.desc.help", available: true },
  { key: "credits", label: "menu.credits", desc: "menu.desc.credits", available: true },
] as const;

/** What the menu knows about the player (ADR-0315).
 *
 * The menu grows with the player: an entry appears when it has something to
 * offer. A brand-new profile never even sees the menu (the boot goes straight
 * into a run), and the archive/workshop entries wait until a run has actually
 * been finished — otherwise they are rows that open onto nothing. */
export interface MenuReveal {
  /** A save exists, so CONTINUE has somewhere to go. */
  readonly hasSave: boolean;
  /** Far Grid is unlocked (Arc 1 cleared). */
  readonly farGridUnlocked: boolean;
  /** Runs finished at least once (deaths and endings both count). */
  readonly runsFinished: number;
  /** The tutorial has been completed. */
  readonly tutorialCompleted: boolean;
}

/** The entries to show for this player, in display order. */
export function visibleMenuOptions(
  reveal: MenuReveal,
): ReadonlyArray<MenuEntry> {
  return MENU_OPTIONS.filter((opt) => {
    switch (opt.key) {
      case "continue":
        return reveal.hasSave;
      case "far_grid_hub":
        return reveal.farGridUnlocked;
      case "tutorial":
        return !reveal.tutorialCompleted;
      case "dungeon_crawl":
      case "craft":
      case "equipment":
      case "hall_of_dead":
      case "endings":
      case "stats":
        return reveal.runsFinished > 0;
      default:
        return true;
    }
  });
}

/** Rows an option block needs: one per entry plus one per group header. */
export function menuBlockRows(
  options: ReadonlyArray<MenuEntry>,
): number {
  return options.length + options.filter((o) => o.group !== undefined).length;
}

/** Width of the label column, so descriptions line up under each other. */
function labelColumnWidth(language: Language): number {
  let widest = 0;
  for (const opt of MENU_OPTIONS) {
    widest = Math.max(widest, t(opt.label, language).length);
  }
  return widest;
}

/** Where the main menu places its content inside the Green Grid frame. */
export interface MainMenuLayout {
  readonly frame: PanelRect;
  readonly inner: PanelRect;
  readonly titleY: number;
  readonly optionsX: number;
  readonly optionsY: number;
  /** First of the two footer rows (controls hint, then version). */
  readonly footerY: number;
}

/** Widest option row in any gating state, so the column never jumps. */
function widestOptionRow(language: Language): number {
  const labelW = labelColumnWidth(language);
  // marker + space + [NN] + space (two-digit indices are the widest)
  const prefix = 5;
  let widestDesc = 0;
  for (const opt of MENU_OPTIONS) {
    widestDesc = Math.max(widestDesc, t(opt.desc, language).length);
  }
  const gated = Math.max(
    t("menu.no_save", language).length,
    t("menu.locked", language).length,
  );
  return prefix + labelW + 1 + Math.max(widestDesc, gated) + 2;
}

/** Compose the main menu inside a screen frame inset one cell from the grid
 * edge (ADR-0237 §2, `screenFrameRect`).
 *
 * The footer sits on the last two inner rows; the title-to-status block is
 * centred vertically in the space above it and the option column is centred
 * horizontally. Grids too small to centre fall back to the original offsets
 * relative to the inner box (title one row below its top, options three
 * columns in).
 */
export function mainMenuLayout(
  grid: Grid,
  language: Language = "en",
  options: ReadonlyArray<MenuEntry> = MENU_OPTIONS,
): MainMenuLayout {
  const frame = screenFrameRect(grid);
  const inner = panelInnerRect(grid, frame);
  const footerY = inner.y + inner.height - 2;
  const available = footerY - 1 - inner.y;
  // 6 title rows + the option block + 3 footer/hint rows.
  const blockRows = 6 + menuBlockRows(options) + 3;
  const titleY =
    inner.y + Math.max(1, Math.floor((available - blockRows) / 2));
  const optionsX =
    inner.x +
    Math.max(3, Math.floor((inner.width - widestOptionRow(language)) / 2));
  return { frame, inner, titleY, optionsX, optionsY: titleY + 6, footerY };
}

function centredX(inner: PanelRect, width: number): number {
  return inner.x + Math.max(1, Math.floor((inner.width - width) / 2));
}

/** Render the main menu screen with the selected option highlighted.
 *
 * CONTINUE option is grayed out (GRAY_DARK + " (no save)") when hasSave=false.
 * Pass hasSave=true and saveMeta (optional) for full continue hint.
 *
 * FAR GRID option is grayed out (GRAY_DARK + " (locked)") when
 * farGridUnlocked=false (ADR-0213 Phase 2 gate). Status messages from the
 * locked-selection path will surface on the existing `statusMessage` line —
 * main.ts owns the message text (no UI strings here).
 *
 * Content is placed by `mainMenuLayout` inside a `drawPanel` frame.
 */
export function renderMainMenu(
  selected: number,
  cols: number,
  rows: number,
  hasSave: boolean = false,
  saveMeta: { missionId: string; turnCount: number } | null = null,
  statusMessage: string = "",
  farGridUnlocked: boolean = true,
  language: Language = "en",
  /** ADR-0315: the entries this player has unlocked. Defaults to all of them
   * so a caller that does not care about the reveal still works. */
  options: ReadonlyArray<MenuEntry> = MENU_OPTIONS,
): Grid {
  let grid = makeGrid(cols, rows);
  const layout = mainMenuLayout(grid, language, options);
  const { inner, titleY, optionsX, optionsY: startY, footerY } = layout;

  // Title block
  const title = t("menu.title", language);
  grid = setInnerText(
    grid,
    inner,
    centredX(inner, title.length),
    titleY,
    title,
    PALETTE.GREEN_NEON,
  );
  const subtitle = t("menu.subtitle", language);
  grid = setInnerText(
    grid,
    inner,
    centredX(inner, subtitle.length),
    titleY + 2,
    subtitle,
    PALETTE.GRAY_LIGHT,
  );

  // Divider
  const dividerWidth = Math.max(0, Math.min(inner.width - 2, 60));
  grid = setInnerText(
    grid,
    inner,
    centredX(inner, dividerWidth),
    titleY + 4,
    "─".repeat(dividerWidth),
    PALETTE.GRAY_MID,
  );

  // Options list — grouped, each entry with its one-line description so the
  // column reads as choices rather than a list of words (ADR-0315).
  const labelW = labelColumnWidth(language);
  let row = startY;
  let lastRow = startY;
  for (let i = 0; i < options.length; i++) {
    const opt = options[i];
    if (!opt) continue;
    if (row >= footerY) break;
    if (opt.group !== undefined) {
      grid = setInnerText(
        grid,
        inner,
        optionsX,
        row,
        t(opt.group, language),
        PALETTE.GRAY_MID,
      );
      row += 1;
      if (row >= footerY) break;
    }
    const isSelected = i === selected;
    const marker = isSelected ? "▸" : " ";
    const num = formatNavIndex(i);
    const label = t(opt.label, language).padEnd(labelW);
    // Gating replaces the description with the reason, so the row still says
    // what is wrong instead of going quiet (ADR-0251 rule 5).
    let suffix = t(opt.desc, language);
    let gated = false;
    if (opt.key === "continue" && !hasSave) {
      suffix = t("menu.no_save", language);
      gated = true;
    }
    if (opt.key === "far_grid_hub" && !farGridUnlocked) {
      suffix = t("menu.locked", language);
      gated = true;
    }
    const fg = gated
      ? PALETTE.GRAY_DARK
      : isSelected
        ? PALETTE.GREEN_NEON
        : PALETTE.GRAY_LIGHT;
    const head = `${marker} ${num} ${label} `;
    grid = setInnerText(grid, inner, optionsX, row, head, fg);
    grid = setInnerText(
      grid,
      inner,
      optionsX + head.length,
      row,
      suffix,
      gated ? PALETTE.GRAY_DARK : PALETTE.GRAY_MID,
    );
    lastRow = row;
    row += 1;
  }

  // Continue hint sub-line (when save exists). Place below the option block.
  if (hasSave && saveMeta) {
    const hintRow = lastRow + 2;
    if (hintRow < footerY) {
      const hint = `→ ${saveMeta.missionId} (turn ${saveMeta.turnCount + 1})`;
      grid = setInnerText(
        grid,
        inner,
        optionsX + 2,
        hintRow,
        hint,
        PALETTE.YELLOW_AMBER,
      );
    }
  }

  // Status message line (shown after save hint, before footer).
  if (statusMessage) {
    const msgRow = lastRow + 3;
    if (msgRow < footerY) {
      const msgX = Math.max(inner.x + 1, optionsX - 2);
      grid = setInnerText(
        grid,
        inner,
        msgX,
        msgRow,
        statusMessage,
        PALETTE.YELLOW_AMBER,
      );
    }
  }

  // Footer
  grid = setInnerText(
    grid,
    inner,
    inner.x + 1,
    footerY,
    t("menu.footer", language),
    PALETTE.GRAY_DARK,
  );
  grid = setInnerText(
    grid,
    inner,
    inner.x + 1,
    footerY + 1,
    t("menu.version", language),
    PALETTE.GRAY_DARK,
  );

  // Frame last, so an overlong status line can never erase a rail.
  return drawPanel(grid, layout.frame).grid;
}

/** Render a stub screen for options not yet implemented (Tier 5+).
 *
 * Shows the option name + "Coming soon" message so the user gets
 * immediate feedback when selecting a deferred menu item.
 */
export function renderStubScreen(
  optionLabel: string,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - optionLabel.length) / 2)),
    Math.floor(rows / 2) - 2,
    optionLabel,
    PALETTE.GREEN_NEON,
  );
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 20) / 2)),
    Math.floor(rows / 2),
    "[ Coming soon — Tier 5+ ]",
    PALETTE.YELLOW_AMBER,
  );
  grid = setText(
    grid,
    2,
    rows - 2,
    "ESC: back to main menu",
    PALETTE.GRAY_DARK,
  );
  return grid;
}
