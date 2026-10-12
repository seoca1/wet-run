/** Mission activity menu screens (Tier 4).
 *
 * Split from the former 1039-LOC `menu.ts` monolith (2026-10-12). This module
 * owns the interactive mission-stage screens: data extraction, security
 * bypass minigame, and the hub-side black market vendor.
 */
import type { Grid } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";

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
  const filled = Math.floor(
    (extractionProgress / maxProgress) * (barWidth - 2),
  );
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
  const status =
    extractionProgress >= maxProgress ? "EXTRACTION COMPLETE" : "EXTRACTING...";
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - status.length) / 2)),
    13,
    status,
    extractionProgress >= maxProgress
      ? PALETTE.GREEN_NEON
      : PALETTE.YELLOW_AMBER,
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
  const watchdogPos = patrolPhase % (patrolWidth * 2 - 2);
  const watchdogX =
    patrolLeft +
    (watchdogPos < patrolWidth - 1
      ? watchdogPos
      : patrolWidth * 2 - 2 - watchdogPos);
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
  grid = setText(
    grid,
    barLeft,
    riskY,
    "[" + bar + "]",
    detectionRisk >= 80 ? PALETTE.RED_BRIGHT : PALETTE.YELLOW_AMBER,
  );
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
  grid = setText(
    grid,
    progBarLeft,
    progY,
    "[" + progBar + "]",
    PALETTE.GREEN_NEON,
  );
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
  const status =
    detectionRisk >= 95
      ? "DETECTED!"
      : progress >= 3
        ? "BYPASS COMPLETE"
        : "WAITING FOR CLEAR PATH...";
  const statusColor =
    detectionRisk >= 95
      ? PALETTE.RED_BRIGHT
      : progress >= 3
        ? PALETTE.GREEN_NEON
        : PALETTE.YELLOW_AMBER;
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
  categories: ReadonlyArray<{
    name: string;
    items: ReadonlyArray<{
      name: string;
      price: number;
      currency: "credits" | "materials";
      quantity?: number;
    }>;
  }>,
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
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - 28) / 2)),
      startY + i,
      vendorArt[i],
      PALETTE.GRAY_LIGHT,
    );
  }

  // Categories
  let y = startY + vendorArt.length + 1;
  for (const cat of categories) {
    if (y >= rows - 4) break;
    grid = setText(grid, 2, y, `▼ ${cat.name}`, PALETTE.YELLOW_AMBER);
    y++;
    for (const item of cat.items) {
      if (y >= rows - 4) break;
      const priceStr =
        item.currency === "credits" ? `${item.price}cr` : `${item.price}mat`;
      const qtyStr = item.quantity ? ` x${item.quantity}` : "";
      grid = setText(
        grid,
        4,
        y,
        `  ${item.name}${qtyStr} — ${priceStr}`,
        PALETTE.GRAY_LIGHT,
      );
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
