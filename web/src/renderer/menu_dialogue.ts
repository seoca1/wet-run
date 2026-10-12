/** Narrative / dialogue menu screens (Tier 4).
 *
 * Split from the former 1039-LOC `menu.ts` monolith (2026-10-12). This module
 * owns the story-beat screens that present narrative text: mission briefing,
 * travel transition, NPC construct dialogue, and the Loa ghost encounter.
 */
import type { Grid } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";

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
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - 28) / 2)),
      startY + i,
      asciiOffice[i],
      PALETTE.GRAY_LIGHT,
    );
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
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - 30) / 2)),
      startY + i,
      scene[i],
      PALETTE.GRAY_LIGHT,
    );
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
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - npcPortrait[i].length) / 2)),
      portraitStartY + i,
      npcPortrait[i],
      PALETTE.CYAN_LIGHT,
    );
  }

  // Dialogue box
  const dialogueStartY = portraitStartY + npcPortrait.length + 1;
  const boxWidth = Math.min(cols - 4, 60);
  const boxLeft = Math.max(2, Math.floor((cols - boxWidth) / 2));

  // Top border
  grid = setText(
    grid,
    boxLeft,
    dialogueStartY,
    "╔" + "═".repeat(boxWidth - 2) + "╗",
    PALETTE.CYAN_LIGHT,
  );

  // Dialogue lines
  for (let i = 0; i < dialogueLines.length; i++) {
    const line = dialogueLines[i];
    const truncated =
      line.length > boxWidth - 4 ? line.slice(0, boxWidth - 7) + "..." : line;
    const padded = truncated.padEnd(boxWidth - 4);
    const isCurrent = i === currentLine;
    const color = isCurrent ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
    grid = setText(
      grid,
      boxLeft,
      dialogueStartY + 1 + i,
      `║ ${padded} ║`,
      color,
    );
  }

  // Bottom border
  const bottomY = dialogueStartY + 1 + dialogueLines.length;
  grid = setText(
    grid,
    boxLeft,
    bottomY,
    "╚" + "═".repeat(boxWidth - 2) + "╝",
    PALETTE.CYAN_LIGHT,
  );

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
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - loaPortrait[i].length) / 2)),
      portraitStartY + i,
      loaPortrait[i],
      PALETTE.MAGENTA_NEON,
    );
  }

  // Dialogue
  const dialogueStartY = portraitStartY + loaPortrait.length + 1;
  const boxWidth = Math.min(cols - 4, 50);
  const boxLeft = Math.max(2, Math.floor((cols - boxWidth) / 2));

  // Top border
  grid = setText(
    grid,
    boxLeft,
    dialogueStartY,
    "╔" + "═".repeat(boxWidth - 2) + "╗",
    PALETTE.MAGENTA_NEON,
  );

  // Dialogue text (wrapped)
  const words = dialogue.split(" ");
  let line = "";
  let lineY = dialogueStartY + 1;
  for (const word of words) {
    if ((line + word).length > boxWidth - 4) {
      grid = setText(
        grid,
        boxLeft,
        lineY,
        `║ ${line.padEnd(boxWidth - 4)} ║`,
        PALETTE.GRAY_LIGHT,
      );
      line = word + " ";
      lineY++;
    } else {
      line += word + " ";
    }
  }
  if (line.length > 0) {
    grid = setText(
      grid,
      boxLeft,
      lineY,
      `║ ${line.padEnd(boxWidth - 4)} ║`,
      PALETTE.GRAY_LIGHT,
    );
    lineY++;
  }

  // Bottom border
  const bottomY = lineY;
  grid = setText(
    grid,
    boxLeft,
    bottomY,
    "╚" + "═".repeat(boxWidth - 2) + "╝",
    PALETTE.MAGENTA_NEON,
  );

  // Options
  for (let i = 0; i < options.length; i++) {
    const opt = options[i];
    const isSelected = i === selectedOption;
    const marker = isSelected ? "▸" : " ";
    const color = isSelected ? PALETTE.MAGENTA_NEON : PALETTE.GRAY_LIGHT;
    grid = setText(
      grid,
      boxLeft + 1,
      bottomY + 1 + i,
      `${marker} ${opt.label}`,
      color,
    );
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
