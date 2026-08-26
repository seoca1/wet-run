/** Virtual gamepad overlay for mobile/touch input (Tier 2c).
 *
 * Renders a translucent D-pad + ABXY + program-row buttons in HTML/CSS that
 * map to GameActions. Touch events → action dispatch via callback.
 *
 * Auto-shows on devices with `pointer: coarse` (touch); auto-hides on
 * devices with `pointer: fine` (mouse/trackpad).
 *
 * Layout: percentage-based positioning so it scales to any phone screen size.
 * - D-pad: bottom-left (anchor 18vw / 75vh).
 * - A/B buttons: bottom-right (anchor 82vw / 75vh).
 * - Program row: bottom-center (60-90vh from top), only in combat phase.
 *
 * The program row is rendered via `updateProgramRow(deck)` which main.ts
 * calls on every state change during combat. Outside combat the row is hidden.
 */

import type { GameAction } from "../core/types.ts";

interface ButtonConfig {
  readonly label: string;
  readonly left: string;
  readonly top: string;
  readonly size: string;
  readonly fontSize: string;
  readonly action: GameAction;
}

const DPAD_CENTER_X = 18;
const DPAD_CENTER_Y = 75;
const DPAD_BUTTON_SIZE = 12;
const DPAD_OFFSET = 6;

const DPAD_BUTTONS: ReadonlyArray<ButtonConfig> = [
  {
    label: "↑",
    left: `${DPAD_CENTER_X - DPAD_BUTTON_SIZE / 2}vw`,
    top: `${DPAD_CENTER_Y - DPAD_BUTTON_SIZE / 2 - DPAD_OFFSET}vh`,
    size: `${DPAD_BUTTON_SIZE}vw`,
    fontSize: `${Math.round(DPAD_BUTTON_SIZE * 0.5)}vw`,
    action: { type: "move_north" as const },
  },
  {
    label: "↓",
    left: `${DPAD_CENTER_X - DPAD_BUTTON_SIZE / 2}vw`,
    top: `${DPAD_CENTER_Y - DPAD_BUTTON_SIZE / 2 + DPAD_OFFSET}vh`,
    size: `${DPAD_BUTTON_SIZE}vw`,
    fontSize: `${Math.round(DPAD_BUTTON_SIZE * 0.5)}vw`,
    action: { type: "move_south" as const },
  },
  {
    label: "←",
    left: `${DPAD_CENTER_X - DPAD_BUTTON_SIZE / 2 - DPAD_OFFSET}vw`,
    top: `${DPAD_CENTER_Y - DPAD_BUTTON_SIZE / 2}vh`,
    size: `${DPAD_BUTTON_SIZE}vw`,
    fontSize: `${Math.round(DPAD_BUTTON_SIZE * 0.5)}vw`,
    action: { type: "move_west" as const },
  },
  {
    label: "→",
    left: `${DPAD_CENTER_X - DPAD_BUTTON_SIZE / 2 + DPAD_OFFSET}vw`,
    top: `${DPAD_CENTER_Y - DPAD_BUTTON_SIZE / 2}vh`,
    size: `${DPAD_BUTTON_SIZE}vw`,
    fontSize: `${Math.round(DPAD_BUTTON_SIZE * 0.5)}vw`,
    action: { type: "move_east" as const },
  },
];

const BTN_CENTER_X = 82;
const BTN_CENTER_Y = 75;

const BUTTONS: ReadonlyArray<ButtonConfig> = [
  {
    label: "A",
    left: `${BTN_CENTER_X - 7}vw`,
    top: `${BTN_CENTER_Y - 7}vh`,
    size: "14vw",
    fontSize: "7vw",
    action: { type: "confirm" as const },
  },
  {
    label: "B",
    left: `${BTN_CENTER_X - 22}vw`,
    top: `${BTN_CENTER_Y - 5}vh`,
    size: "10vw",
    fontSize: "5vw",
    action: { type: "cancel" as const },
  },
];

/** Inject CSS + DOM elements for the on-screen gamepad. */
export function mountVirtualGamepad(handler: (action: GameAction) => void): () => void {
  if (typeof document === "undefined") {
    return () => {}; // SSR / non-browser
  }
  const root = ensureOverlayRoot();
  renderOverlay(root, handler);
  return () => {
    root.innerHTML = "";
  };
}

/** Update the program row (only visible during combat). Pass deck array from state.
 * Each program gets a button labeled with its short-id (first 4 chars), positioned
 * in a horizontal row at the bottom-center of the viewport.
 */
export function updateProgramRow(deck: ReadonlyArray<{ readonly id: string }>): void {
  const row = document.getElementById("wetrun-program-row");
  if (!row) return;
  if (deck.length === 0) {
    row.innerHTML = "";
    return;
  }
  const buttons = deck.map((p, i) => {
    const shortId = p.id.slice(0, 4);
    const num = i + 1;
    return `<button data-hand-index="${num}" style="font-size:3vw;padding:1vw 2vw;">${num}.${shortId}</button>`;
  });
  row.innerHTML = `
    <style>
      #wetrun-program-row {
        position: fixed; left: 50%; transform: translateX(-50%);
        bottom: 2vh;
        display: flex; gap: 1.5vw;
        pointer-events: none;
        font-family: monospace;
        z-index: 6;
      }
      #wetrun-program-row button {
        pointer-events: auto;
        background: rgba(0, 0, 0, 0.7); border: 2px solid #00ff41;
        color: #00ff41; font-weight: bold;
        border-radius: 6px;
        touch-action: none; user-select: none;
      }
      #wetrun-program-row button:active { background: rgba(0, 255, 65, 0.4); }
    </style>
    ${buttons.join("")}
  `;
  // Wire pointerdown handlers.
  row.querySelectorAll("button").forEach((btn) => {
    const idx = Number((btn as HTMLElement).dataset.handIndex);
    if (Number.isFinite(idx) && idx > 0) {
      btn.addEventListener("pointerdown", (e) => {
        e.preventDefault();
        // Defer to the same handler via window.wetrun.
        const w = window as unknown as { wetrun?: { handleProgramButton(handIndex: number): void } };
        w.wetrun?.handleProgramButton(idx);
      });
    }
  });
}

function ensureOverlayRoot(): HTMLElement {
  let root = document.getElementById("wetrun-gamepad-root");
  if (!root) {
    root = document.createElement("div");
    root.id = "wetrun-gamepad-root";
    root.setAttribute("aria-label", "Virtual gamepad");
    document.body.appendChild(root);
    // Separate element for program row (different z-index + position scheme).
    const row = document.createElement("div");
    row.id = "wetrun-program-row";
    document.body.appendChild(row);
  }
  return root;
}

function renderOverlay(root: HTMLElement, handler: (action: GameAction) => void): void {
  root.innerHTML = `
    <style>
      #wetrun-gamepad-root {
        position: fixed; inset: 0; pointer-events: none;
        font-family: monospace;
        z-index: 5;
      }
      #wetrun-gamepad-root button {
        position: absolute; pointer-events: auto;
        background: rgba(0, 0, 0, 0.55); border: 2px solid #00ff41;
        color: #00ff41; font-weight: bold;
        padding: 0; margin: 0; line-height: 1;
        border-radius: 8px;
        touch-action: none; user-select: none;
        display: flex; align-items: center; justify-content: center;
      }
      #wetrun-gamepad-root button:active { background: rgba(0, 255, 65, 0.4); }
    </style>
  `;
  for (const btn of DPAD_BUTTONS) {
    appendButton(root, btn, handler);
  }
  for (const btn of BUTTONS) {
    appendButton(root, btn, handler);
  }
}

function appendButton(parent: HTMLElement, cfg: ButtonConfig, handler: (action: GameAction) => void): void {
  const btn = document.createElement("button");
  btn.textContent = cfg.label;
  btn.style.left = cfg.left;
  btn.style.top = cfg.top;
  btn.style.width = cfg.size;
  btn.style.height = cfg.size;
  btn.style.fontSize = cfg.fontSize;
  btn.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    handler(cfg.action);
  });
  parent.appendChild(btn);
}

/** Returns true when the device has a coarse pointer (touch). */
export function isTouchDevice(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(pointer: coarse)").matches;
}
