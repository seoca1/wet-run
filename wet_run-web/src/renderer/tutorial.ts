/** Tutorial Overlay (Tier 5.5+).
 *
 * First-run onboarding overlay that guides new players through:
 * 1. Key mappings (movement, combat, menu)
 * 2. Matrix overview (nodes, zones, events)
 * 3. Combat basics (cards, programs, ICE, alarm)
 * 3. Progression (loot, upgrades, endings)
 *
 * Shown once on first boot (localStorage flag 'tutorial_completed').
 * Skippable via ESC.
 */
import type { Grid } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";

interface TutorialStep {
  readonly title: string;
  readonly body: string[];
  readonly action?: string; // key to press to advance
}

const TUTORIAL_STEPS: readonly TutorialStep[] = [
  {
    title: "Welcome to Wet Run",
    body: [
      "A cyberpunk roguelike set in Gibson's Sprawl universe.",
      "You are a console cowboy jacking into the matrix.",
    ],
  },
  {
    title: "Movement & Navigation",
    body: [
      "Arrow keys / WASD: Move cursor / select",
      "Enter / Space: Confirm / Select",
      "ESC / Q: Back / Cancel / Jack Out",
      "M: Mute/Unmute BGM + SFX",
    ],
    action: "Enter",
  },
  {
    title: "The Matrix (Stage Map)",
    body: [
      "Nodes represent missions. Each has a zone, ICE, and reward.",
      "Zones: Surface → Mid → Deep → Core → Boss",
      "Events: ⚔ Combat, ★ Discovery, ✦ Trap, ◆ Cache, ♨ Rest, ⌘ Merchant",
      "▸ = Current node, ✓ = Visited, → = Next node",
    ],
    action: "Enter",
  },
  {
    title: "Combat Basics",
    body: [
      "1-9: Use program from hand (programs cost Alarm)",
      "M: Mute/Unmute BGM + SFX",
      "ICE has HP — reduce to 0 to defeat",
      "Cards go to discard, draw from deck",
      "Alarm 100 = Flatline (Game Over)",
    ],
    action: "Enter",
  },
  {
    title: "Progression & Win",
    body: [
      "Defeat ICE → Loot (HEAL + Credits)",
      "Advance to next node via Enter",
      "Boss at final node (4 phases)",
      "Win: Reach Ending A/B/C",
    ],
    action: "Enter",
  },
  {
    title: "You're Ready, Console Cowboy",
    body: [
      "Jack in. The matrix awaits.",
      "Press Enter to jack in...",
    ],
    action: "Enter",
  },
] as const;

export interface TutorialOverlayState {
  currentStep: number;
  visible: boolean;
}

/** Render the tutorial overlay for the current step. */
export function renderTutorialOverlay(
  stepIndex: number,
  cols: number,
  rows: number,
): Grid {
  const grid = makeGrid(cols, rows);
  const step = TUTORIAL_STEPS[Math.min(stepIndex, TUTORIAL_STEPS.length - 1)];

  // Semi-transparent background
  let g = setText(grid, 2, 1, "╔════════════════════════════════════════════╗", PALETTE.CYAN_LIGHT);
  g = setText(g, 2, 2, `║  ${step.title.padEnd(50)} ║`, PALETTE.CYAN_LIGHT);
  g = setText(g, 2, 3, "╠═════════════════════════════════════════════╣", PALETTE.CYAN_LIGHT);

  // Body text
  let y = 5;
  for (const line of step.body) {
    g = setText(g, 4, y, line, PALETTE.GRAY_LIGHT);
    y++;
  }

  // Progress indicator
  const progress = `${stepIndex + 1}/${TUTORIAL_STEPS.length}`;
  g = setText(g, 4, rows - 4, `Step ${progress}`, PALETTE.GRAY_MID);

  // Action hint
  if (step.action) {
    g = setText(g, 4, rows - 3, `Press ${step.action} to continue`, PALETTE.YELLOW_AMBER);
  } else {
    g = setText(g, 4, rows - 3, "Press ESC to skip tutorial", PALETTE.GRAY_DARK);
  }

  // Border
  g = setText(g, 2, rows - 1, "╚═════════════════════════════════════════════╝", PALETTE.CYAN_LIGHT);

  return g;
}

function getTutorialState(): { currentStep: number; visible: boolean } {
  if (typeof window !== "undefined") {
    try {
      const done = localStorage.getItem("wetrun_tutorial_completed");
      if (done === "true") {
        return { currentStep: TUTORIAL_STEPS.length, visible: false };
      }
      const stepStr = localStorage.getItem("wetrun_tutorial_step");
      if (stepStr) {
        const parsed = parseInt(stepStr, 10);
        if (!isNaN(parsed)) {
          return { currentStep: Math.min(parsed, TUTORIAL_STEPS.length - 1), visible: true };
        }
      }
    } catch {
      // ignore
    }
  }
  return { currentStep: 0, visible: true };
}

function completeTutorial(): void {
  if (typeof window !== "undefined") {
    try {
      localStorage.setItem("wetrun_tutorial_completed", "true");
    } catch {
      // ignore
    }
  }
}

export function createTutorialOverlay(): {
  readonly state: TutorialOverlayState;
  readonly render: (cols: number, rows: number) => Grid;
  readonly handleInput: (key: string) => { action: "next" | "skip" | "none" };
} {
  let stepIndex = 0;

  return {
    get state() {
      return getTutorialState();
    },
    render: (cols: number, rows: number) => {
      // Check completion on each render
      if (typeof window !== "undefined") {
        try {
          const done = localStorage.getItem("wetrun_tutorial_completed");
          if (done === "true") {
            return makeGrid(1, 1);
          }
        } catch {
          // ignore
        }
      }
      return renderTutorialOverlay(stepIndex, cols, rows);
    },
    handleInput: (key: string) => {
      if (key === "Escape") {
        // Skip tutorial
        completeTutorial();
        return { action: "skip" };
      }
      if (TUTORIAL_STEPS[stepIndex]?.action === key) {
        stepIndex++;
        if (stepIndex >= TUTORIAL_STEPS.length) {
          completeTutorial();
          return { action: "skip" };
        }
        return { action: "next" };
      }
      return { action: "none" };
    },
  };
}