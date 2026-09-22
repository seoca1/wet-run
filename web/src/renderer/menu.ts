/** Main menu renderer (Tier 4, ADR-0207+/ADR-0209).
 *
 * Mirrors Python's main_menu.py (9 options: NEW_RUN, GRAPHIC_NOVEL,
 * CONTINUE, SETTINGS, CREDITS, HALL_OF_DEAD, HELP, ENDINGS, STATS).
 * Web Tier 4 implements the 6 reachable + 3 deferred (rendered as
 * "Coming soon" stubs to keep the menu 1:1 with Python for design parity).
 *
 * Layout: title block + 9 numbered options + footer. Selected option
 * highlighted with ▸ marker (matches mission select convention).
 */
import type { Grid } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";

export type MenuOption =
  | "new_run"
  | "graphic_novel"
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
  | "dungeon_crawl";

/** All 13 menu options in display order. Order matches Python OPTION_* constants. */
export const MENU_OPTIONS: ReadonlyArray<{ key: MenuOption; label: string; available: boolean }> = [
  { key: "new_run", label: "NEW RUN", available: true },
  { key: "dungeon_crawl", label: "DUNGEON CRAWL", available: true },
  { key: "graphic_novel", label: "GRAPHIC NOVEL", available: true },
  { key: "continue", label: "CONTINUE", available: true },
  { key: "settings", label: "SETTINGS", available: true },
  { key: "craft", label: "CRAFT", available: true },
  { key: "equipment", label: "EQUIPMENT", available: true },
  { key: "credits", label: "CREDITS", available: true },
  { key: "hall_of_dead", label: "HALL OF DEAD", available: true },
  { key: "help", label: "HELP", available: true },
  { key: "endings", label: "ENDINGS", available: true },
  { key: "stats", label: "STATS", available: true },
  { key: "tutorial", label: "TUTORIAL", available: true },
] as const;

/** Render the main menu screen with the selected option highlighted.
 *
 * CONTINUE option is grayed out (GRAY_DARK + " (no save)") when hasSave=false.
 * Pass hasSave=true and saveMeta (optional) for full continue hint.
 */
export function renderMainMenu(
  selected: number,
  cols: number,
  rows: number,
  hasSave: boolean = false,
  saveMeta: { missionId: string; turnCount: number } | null = null,
  statusMessage: string = "",
): Grid {
  let grid = makeGrid(cols, rows);

  // Title block (top)
  grid = setText(grid, Math.max(2, Math.floor((cols - 8) / 2)), 2, "WET RUN", PALETTE.GREEN_NEON);
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 40) / 2)),
    4,
    "A cyberpunk roguelike based on Gibson's Sprawl trilogy",
    PALETTE.GRAY_LIGHT,
  );

  // Divider
  grid = setText(grid, 2, 6, "─".repeat(Math.min(cols - 4, 60)), PALETTE.GRAY_MID);

  // Options list (starting at row 8)
  const startY = 8;
  for (let i = 0; i < MENU_OPTIONS.length; i++) {
    const opt = MENU_OPTIONS[i];
    if (!opt) continue;
    const isSelected = i === selected;
    const marker = isSelected ? "▸" : " ";
    const num = (i + 1).toString();
    const fg = isSelected ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
    const row = startY + i;
    if (row >= rows - 1) break;
    let label = `[${num}] ${opt.label}`;
    // CONTINUE option gating — gray out + suffix when no save.
    if (opt.key === "continue" && !hasSave) {
      label = `[${num}] CONTINUE    (no save)`;
      grid = setText(grid, 4, row, `${marker} ${label}`, PALETTE.GRAY_DARK);
      continue;
    }
    grid = setText(grid, 4, row, `${marker} ${label}`, fg);
  }

  // Continue hint sub-line (when save exists). Place below all menu items
  // (MENU_OPTIONS.length + 1 row after startY) to avoid overlap.
  if (hasSave && saveMeta) {
    const hintRow = startY + MENU_OPTIONS.length + 1;
    if (hintRow < rows - 2) {
      const hint = `→ ${saveMeta.missionId} (turn ${saveMeta.turnCount + 1})`;
      grid = setText(grid, 6, hintRow, hint, PALETTE.YELLOW_AMBER);
    }
  }

  // Status message line (shown after save hint, before footer).
  if (statusMessage) {
    const msgRow = startY + MENU_OPTIONS.length + 2;
    if (msgRow < rows - 2) {
      grid = setText(grid, 2, msgRow, statusMessage, PALETTE.YELLOW_AMBER);
    }
  }

  // Footer
  const footerRow = rows - 2;
  grid = setText(
    grid,
    2,
    footerRow,
    "↑↓: navigate | ENTER: select | ESC: back",
    PALETTE.GRAY_DARK,
  );
  grid = setText(
    grid,
    2,
    footerRow + 1,
    "Tier 4 · v0.1.0 · ADR-0209 IDB",
    PALETTE.GRAY_DARK,
  );

  return grid;
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

/** Render the mission briefing screen (Finn's office).
 *
 * Stage: briefing — Finn's office ASCII with fixer dialogue.
 * Player presses any key to advance to travel animation.
 */
export function renderBriefingScreen(
  cols: number,
  rows: number,
  missionTitle: string,
  _fixerName: string,
  fixerDialogue: string[],
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 14) / 2)),
    1,
    "MISSION BRIEFING",
    PALETTE.GREEN_NEON,
  );

  // Finn's office ASCII art
  const asciiOffice = [
    "  ┌──────────────────────────┐",
    "  │  ♠F♠ THE FINN'S OFFICE   │",
    "  │  ────────────────────    │",
    "  │                          │",
    "  │  'Pay's in the credstick │",
    "  │   when the data's in     │",
    "  │   my hand. Don't die.'   │",
    "  └──────────────────────────┘",
  ];
  const startY = 3;
  for (let i = 0; i < asciiOffice.length; i++) {
    grid = setText(grid, Math.max(2, Math.floor((cols - 28) / 2)), startY + i, asciiOffice[i], PALETTE.GRAY_LIGHT);
  }

  // Mission title
  const missionY = startY + asciiOffice.length + 1;
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - missionTitle.length) / 2)),
    missionY,
    `Mission: ${missionTitle}`,
    PALETTE.YELLOW_AMBER,
  );

  // Fixer dialogue
  const dialogueY = missionY + 2;
  for (let i = 0; i < fixerDialogue.length; i++) {
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - fixerDialogue[i].length) / 2)),
      dialogueY + i,
      fixerDialogue[i],
      PALETTE.GRAY_LIGHT,
    );
  }

  // Footer
  const footerY = rows - 2;
  grid = setText(
    grid,
    2,
    footerY,
    "ENTER: jack in | ESC: back to mission select",
    PALETTE.GRAY_DARK,
  );

  return grid;
}

/** Render travel animation screen (Chiba street → jack-in point).
 *
 * Stage: travel — atmospheric transition to matrix.
 * Auto-advances after a few seconds or key press.
 */
export function renderTravelScreen(
  cols: number,
  rows: number,
  step: number = 0,
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 18) / 2)),
    1,
    "JACKING IN...",
    PALETTE.GREEN_NEON,
  );

  // Animated Chiba street scenes
  const scenes = [
    [
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
      "  ░  ◢◣  CHIBA SECTOR  ░░░  ░",
      "  ░  ──  NEON RAIN  ──────  ░",
      "  ░  ░▒▓  LEVEL 11  ▓▒░ ░░  ░",
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
    ],
    [
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
      "  ░  ◢◣  STREET LEVEL  ░░░  ░",
      "  ░  ──  HOLO-ADS FLICKER  ░",
      "  ░  ░▒▓  APPROACHING... ▓▒░ ░",
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
    ],
    [
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
      "  ░  ◢◣  JACK-IN POINT  ░░░  ░",
      "  ░  ──  INITIALIZING...  ───  ░",
      "  ░  ░▒▓  SYNC COMPLETE ▓▒░ ░",
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
    ],
  ];

  const scene = scenes[Math.min(step, scenes.length - 1)];
  const startY = 4;
  for (let i = 0; i < scene.length; i++) {
    grid = setText(grid, Math.max(2, Math.floor((cols - 30) / 2)), startY + i, scene[i], PALETTE.GRAY_LIGHT);
  }

  // Progress indicator
  const progressY = startY + scenes[0].length + 1;
  grid = setText(
    grid,
    2,
    progressY,
    `Stage ${step + 1}/${scenes.length} — Press any key to continue`,
    PALETTE.YELLOW_AMBER,
  );

  // Footer
  const footerY = rows - 2;
  grid = setText(
    grid,
    2,
    footerY,
    "Auto-advances in 3s | Press any key to continue",
    PALETTE.GRAY_DARK,
  );

  return grid;
}

/** Render the NPC dialogue screen (meet_npc stage).
 *
 * Stage: meet_npc — construct NPC dialogue (e.g., Dixie Flatline).
 * Player advances through dialogue lines with ENTER.
 */
export function renderNPCDialogueScreen(
  cols: number,
  rows: number,
  npcName: string,
  npcPortrait: string[],
  dialogueLines: string[],
  currentLine: number,
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - npcName.length - 10) / 2)),
    1,
    `CONSTRUCT: ${npcName}`,
    PALETTE.CYAN_LIGHT,
  );

  // NPC Portrait (ASCII)
  const portraitStartY = 3;
  for (let i = 0; i < npcPortrait.length; i++) {
    grid = setText(grid, Math.max(2, Math.floor((cols - npcPortrait[i].length) / 2)), portraitStartY + i, npcPortrait[i], PALETTE.CYAN_LIGHT);
  }

  // Dialogue box
  const dialogueStartY = portraitStartY + npcPortrait.length + 1;
  const boxWidth = Math.min(cols - 4, 60);
  const boxLeft = Math.max(2, Math.floor((cols - boxWidth) / 2));

  // Top border
  grid = setText(grid, boxLeft, dialogueStartY, "╔" + "═".repeat(boxWidth - 2) + "╗", PALETTE.CYAN_LIGHT);

  // Dialogue lines
  for (let i = 0; i < dialogueLines.length; i++) {
    const line = dialogueLines[i];
    const truncated = line.length > boxWidth - 4 ? line.slice(0, boxWidth - 7) + "..." : line;
    const padded = truncated.padEnd(boxWidth - 4);
    const isCurrent = i === currentLine;
    const color = isCurrent ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
    grid = setText(grid, boxLeft, dialogueStartY + 1 + i, `║ ${padded} ║`, color);
  }

  // Bottom border
  const bottomY = dialogueStartY + 1 + dialogueLines.length;
  grid = setText(grid, boxLeft, bottomY, "╚" + "═".repeat(boxWidth - 2) + "╝", PALETTE.CYAN_LIGHT);

  // Progress indicator
  grid = setText(
    grid,
    2,
    bottomY + 1,
    `Line ${currentLine + 1}/${dialogueLines.length}`,
    PALETTE.YELLOW_AMBER,
  );

  // Footer
  const footerY = rows - 2;
  grid = setText(
    grid,
    2,
    footerY,
    "ENTER: next line | ESC: skip dialogue",
    PALETTE.GRAY_DARK,
  );

  return grid;
}

/** Render the data extraction screen (extract_data stage).
 *
 * Stage: extract_data — locate and extract the target data node.
 * Player confirms extraction with ENTER.
 */
export function renderExtractDataScreen(
  cols: number,
  rows: number,
  dataNodeName: string,
  dataDescription: string,
  extractionProgress: number,
  maxProgress: number,
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 14) / 2)),
    1,
    "DATA EXTRACTION",
    PALETTE.CYAN_LIGHT,
  );

  // Data node info
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - dataNodeName.length) / 2)),
    4,
    `TARGET: ${dataNodeName}`,
    PALETTE.YELLOW_AMBER,
  );

  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - dataDescription.length) / 2)),
    6,
    dataDescription,
    PALETTE.GRAY_LIGHT,
  );

  // Progress bar
  const barWidth = Math.min(cols - 4, 50);
  const barLeft = Math.max(2, Math.floor((cols - barWidth) / 2));
  const filled = Math.floor((extractionProgress / maxProgress) * (barWidth - 2));
  const empty = barWidth - 2 - filled;
  const bar = "█".repeat(filled) + "░".repeat(empty);
  grid = setText(grid, barLeft, 10, "[" + bar + "]", PALETTE.GREEN_NEON);
  grid = setText(
    grid,
    barLeft,
    11,
    `${extractionProgress}/${maxProgress} segments`,
    PALETTE.GRAY_LIGHT,
  );

  // Status
  const status = extractionProgress >= maxProgress ? "EXTRACTION COMPLETE" : "EXTRACTING...";
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - status.length) / 2)),
    13,
    status,
    extractionProgress >= maxProgress ? PALETTE.GREEN_NEON : PALETTE.YELLOW_AMBER,
  );

  // Footer
  const footerY = rows - 2;
  grid = setText(
    grid,
    2,
    footerY,
    extractionProgress >= maxProgress
      ? "ENTER: confirm extraction | ESC: abort"
      : "Auto-extracting... | ESC: abort",
    PALETTE.GRAY_DARK,
  );

  return grid;
}

/** Render the bypass security screen (bypass_security stage).
 *
 * Stage: bypass_security — Stealth minigame to slip past corporate security.
 * Player must time their movements to avoid detection (Watchdog patrols).
 * Space to move when safe, wait when patrol passes.
 */
export function renderBypassSecurityScreen(
  cols: number,
  rows: number,
  patrolPhase: number,
  detectionRisk: number,
  progress: number,
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 16) / 2)),
    1,
    "BYPASS SECURITY",
    PALETTE.YELLOW_AMBER,
  );

  // Security system info
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 28) / 2)),
    3,
    "CORPORATE SECURITY LAYER DETECTED",
    PALETTE.RED_BRIGHT,
  );

  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 22) / 2)),
    4,
    "WATCHDOG PATROL ACTIVE",
    PALETTE.YELLOW_AMBER,
  );

  // Patrol visualization
  const patrolY = 7;
  const patrolWidth = Math.min(cols - 4, 50);
  const patrolLeft = Math.max(2, Math.floor((cols - patrolWidth) / 2));

  // Draw patrol path
  for (let i = 0; i < patrolWidth; i++) {
    grid = setText(grid, patrolLeft + i, patrolY, "─", PALETTE.GRAY_DARK);
  }

  // Watchdog position (moves back and forth)
  const watchdogPos = (patrolPhase % (patrolWidth * 2 - 2));
  const watchdogX = patrolLeft + (watchdogPos < patrolWidth - 1 ? watchdogPos : patrolWidth * 2 - 2 - watchdogPos);
  grid = setText(grid, watchdogX, patrolY, "▲", PALETTE.RED_BRIGHT);

  // Player position (fixed at left, waiting to move)
  const playerX = patrolLeft + 1;
  grid = setText(grid, playerX, patrolY + 1, "█", PALETTE.GREEN_NEON);

  // Detection risk bar
  const riskY = patrolY + 3;
  const barWidth = Math.min(cols - 4, 40);
  const barLeft = Math.max(2, Math.floor((cols - barWidth) / 2));
  const filled = Math.floor((detectionRisk / 100) * (barWidth - 2));
  const empty = barWidth - 2 - filled;
  const bar = "█".repeat(filled) + "░".repeat(empty);
  grid = setText(grid, barLeft, riskY, "[" + bar + "]", detectionRisk >= 80 ? PALETTE.RED_BRIGHT : PALETTE.YELLOW_AMBER);
  grid = setText(
    grid,
    barLeft,
    riskY + 1,
    `DETECTION: ${detectionRisk}%`,
    detectionRisk >= 80 ? PALETTE.RED_BRIGHT : PALETTE.YELLOW_AMBER,
  );

  // Progress
  const progY = riskY + 3;
  const progBarWidth = Math.min(cols - 4, 40);
  const progBarLeft = Math.max(2, Math.floor((cols - progBarWidth) / 2));
  const progFilled = Math.floor((progress / 3) * (progBarWidth - 2));
  const progEmpty = progBarWidth - 2 - progFilled;
  const progBar = "█".repeat(progFilled) + "░".repeat(progEmpty);
  grid = setText(grid, progBarLeft, progY, "[" + progBar + "]", PALETTE.GREEN_NEON);
  grid = setText(
    grid,
    progBarLeft,
    progY + 1,
    `BYPASSED: ${progress}/${3} LAYERS`,
    PALETTE.GRAY_LIGHT,
  );

  // Instructions
  const instructionY = rows - 4;
  grid = setText(
    grid,
    2,
    instructionY,
    "SPACE: MOVE (when safe) | ENTER: CONFIRM | ESC: ABORT",
    PALETTE.GRAY_DARK,
  );

  // Status
  const status = detectionRisk >= 95 ? "DETECTED!" : progress >= 3 ? "BYPASS COMPLETE" : "WAITING FOR CLEAR PATH...";
  const statusColor = detectionRisk >= 95 ? PALETTE.RED_BRIGHT : progress >= 3 ? PALETTE.GREEN_NEON : PALETTE.YELLOW_AMBER;
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - status.length) / 2)),
    rows - 1,
    status,
    statusColor,
  );

  return grid;
}
/** Render the black market screen (black_market stage).
 *
 * Stage: black_market — Hub-side vendor for trading credits/materials for programs,
 * deck upgrades, and intel. Accessible from Hub between runs.
 */
export function renderBlackMarketScreen(
  cols: number,
  rows: number,
  categories: ReadonlyArray<{ name: string; items: ReadonlyArray<{ name: string; price: number; currency: "credits" | "materials"; quantity?: number }> }>,
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 14) / 2)),
    1,
    "BLACK MARKET",
    PALETTE.YELLOW_AMBER,
  );

  // Vendor ASCII
  const vendorArt = [
    "  ┌──────────────────────────┐",
    "  │  ░▒▓█  BLACK MARKET  █▓▒░  │",
    "  │  ────────────────────     │",
    "  │  'Cash, credits, code'    │",
    "  │   — the silent menu       │",
    "  │   of the Sprawl.         │",
    "  └──────────────────────────┘",
  ];
  const startY = 3;
  for (let i = 0; i < vendorArt.length; i++) {
    grid = setText(grid, Math.max(2, Math.floor((cols - 28) / 2)), startY + i, vendorArt[i], PALETTE.GRAY_LIGHT);
  }

  // Categories
  let y = startY + vendorArt.length + 1;
  for (const cat of categories) {
    if (y >= rows - 4) break;
    grid = setText(grid, 2, y, `▼ ${cat.name}`, PALETTE.YELLOW_AMBER);
    y++;
    for (const item of cat.items) {
      if (y >= rows - 4) break;
      const priceStr = item.currency === "credits" ? `${item.price}cr` : `${item.price}mat`;
      const qtyStr = item.quantity ? ` x${item.quantity}` : "";
      grid = setText(grid, 4, y, `  ${item.name}${qtyStr} — ${priceStr}`, PALETTE.GRAY_LIGHT);
      y++;
    }
    y++; // spacing between categories
  }

  // Footer
  const footerY = rows - 2;
  grid = setText(
    grid,
    2,
    footerY,
    "↑↓: navigate | ENTER: buy | ESC: leave market",
    PALETTE.GRAY_DARK,
  );

  return grid;
}

/** Render the Loa encounter screen (ghost_encounter stage).
 *
 * Stage: ghost_encounter — Rare matrix event in deep architecture.
 * Encounter a ghost-god (Loa) of the matrix. Choose: talk, fight, or leave.
 */
export function renderGhostEncounterScreen(
  cols: number,
  rows: number,
  loaName: string,
  loaPortrait: string[],
  dialogue: string,
  options: ReadonlyArray<{ label: string; action: "talk" | "fight" | "leave" }>,
  selectedOption: number,
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 14 - loaName.length) / 2)),
    1,
    `LOA ENCOUNTER: ${loaName}`,
    PALETTE.MAGENTA_NEON,
  );

  // Loa ASCII portrait
  const portraitStartY = 3;
  for (let i = 0; i < loaPortrait.length; i++) {
    grid = setText(grid, Math.max(2, Math.floor((cols - loaPortrait[i].length) / 2)), portraitStartY + i, loaPortrait[i], PALETTE.MAGENTA_NEON);
  }

  // Dialogue
  const dialogueStartY = portraitStartY + loaPortrait.length + 1;
  const boxWidth = Math.min(cols - 4, 50);
  const boxLeft = Math.max(2, Math.floor((cols - boxWidth) / 2));

  // Top border
  grid = setText(grid, boxLeft, dialogueStartY, "╔" + "═".repeat(boxWidth - 2) + "╗", PALETTE.MAGENTA_NEON);

  // Dialogue text (wrapped)
  const words = dialogue.split(" ");
  let line = "";
  let lineY = dialogueStartY + 1;
  for (const word of words) {
    if ((line + word).length > boxWidth - 4) {
      grid = setText(grid, boxLeft, lineY, `║ ${line.padEnd(boxWidth - 4)} ║`, PALETTE.GRAY_LIGHT);
      line = word + " ";
      lineY++;
    } else {
      line += word + " ";
    }
  }
  if (line.length > 0) {
    grid = setText(grid, boxLeft, lineY, `║ ${line.padEnd(boxWidth - 4)} ║`, PALETTE.GRAY_LIGHT);
    lineY++;
  }

  // Bottom border
  const bottomY = lineY;
  grid = setText(grid, boxLeft, bottomY, "╚" + "═".repeat(boxWidth - 2) + "╝", PALETTE.MAGENTA_NEON);

  // Options
  for (let i = 0; i < options.length; i++) {
    const opt = options[i];
    const isSelected = i === selectedOption;
    const marker = isSelected ? "▸" : " ";
    const color = isSelected ? PALETTE.MAGENTA_NEON : PALETTE.GRAY_LIGHT;
    grid = setText(grid, boxLeft + 1, bottomY + 1 + i, `${marker} ${opt.label}`, color);
  }

  // Footer
  const footerY = rows - 2;
  grid = setText(
    grid,
    2,
    footerY,
    "↑↓: select | ENTER: confirm | ESC: leave",
    PALETTE.GRAY_DARK,
  );

  return grid;
}

/** Render the death restart screen (death_restart stage).
 *
 * Stage: death_restart — After death screen. Player chooses to restart or quit.
 */
export function renderDeathRestartScreen(
  cols: number,
  rows: number,
  summary: { jockeyName: string; mission: string; grade: number; playtimeMinutes: number; totalRuns: number; totalDeaths: number },
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 14) / 2)),
    1,
    "⚠ FLATLINE",
    PALETTE.RED_BRIGHT,
  );

  // ASCII art
  const asciiArt = [
    "  ┌──────────────────────┐",
    "  │  ⚠ FLATLINE         │",
    "  │  ◢◣◢◣◢◣◢◣◢◣◢◣◢◣◢◣  │",
    "  │  ░▒▓ Equipment LOST ▓▒░  │",
    "  │  ░▒▓ Grade kept     ▓▒░  │",
    "  └──────────────────────┘",
  ];
  const startY = 3;
  for (let i = 0; i < asciiArt.length; i++) {
    grid = setText(grid, Math.max(2, Math.floor((cols - 28) / 2)), startY + i, asciiArt[i], PALETTE.RED_BRIGHT);
  }

  // Jockey summary
  const summaryY = startY + asciiArt.length + 1;
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 20) / 2)),
    summaryY,
    `Jockey: ${summary.jockeyName}`,
    PALETTE.GRAY_LIGHT,
  );
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 20) / 2)),
    summaryY + 1,
    `Mission: ${summary.mission} (Grade ${summary.grade})`,
    PALETTE.GRAY_LIGHT,
  );
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 25) / 2)),
    summaryY + 2,
    `Playtime: ${summary.playtimeMinutes} min | Runs: ${summary.totalRuns} | Deaths: ${summary.totalDeaths}`,
    PALETTE.GRAY_LIGHT,
  );

  // Options
  const optionsY = summaryY + 4;
  const options = [
    { label: "[ENTER] Restart — New Jockey", action: "restart" },
    { label: "[ESC] Quit to Menu", action: "quit" },
  ];
  for (let i = 0; i < options.length; i++) {
    const opt = options[i];
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - opt.label.length) / 2)),
      optionsY + i,
      opt.label,
      PALETTE.GRAY_LIGHT,
    );
  }

  // Footer
  const footerY = rows - 2;
  grid = setText(
    grid,
    2,
    footerY,
    "ENTER: restart | ESC: quit to menu",
    PALETTE.GRAY_DARK,
  );

  return grid;
}

/** Render the failed/flatline screen (failed stage).
 *
 * Stage: failed — Terminal flatline state. No recovery, only acknowledgment.
 */
export function renderFailedScreen(
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 14) / 2)),
    1,
    "✗ FLATLINE",
    PALETTE.RED_BRIGHT,
  );

  // ASCII art
  const asciiArt = [
    "  ┌──────────────────────┐",
    "  │  ✗ FLATLINE          │",
    "  │  ◢◣◢◣◢◣◢◣◢◣◢◣◢◣◢◣  │",
    "  │  ░▒▓ Equipment LOST ▓▒░  │",
    "  │  ░▒▓ Grade kept     ▓▒░  │",
    "  └──────────────────────┘",
  ];
  const startY = 3;
  for (let i = 0; i < asciiArt.length; i++) {
    grid = setText(grid, Math.max(2, Math.floor((cols - 28) / 2)), startY + i, asciiArt[i], PALETTE.RED_BRIGHT);
  }

  // Footer
  const footerY = rows - 2;
  grid = setText(
    grid,
    2,
    footerY,
    "ENTER: return to menu | ESC: quit",
    PALETTE.GRAY_DARK,
  );

  return grid;
}
