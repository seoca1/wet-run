/** Virtual gamepad overlay for mobile/touch input (Tier 2c).
 *
 * Renders a translucent D-pad + ABXY + program-row buttons in HTML/CSS that
 * map to GameActions. Touch events → action dispatch via callback.
 *
 * Auto-shows on devices with `pointer: coarse` (touch); auto-hides on
 * devices with `pointer: fine` (mouse/trackpad).
 *
 * Responsive layout:
 * - Portrait: D-pad bottom-left, AB buttons bottom-right, program row above
 * - Landscape: D-pad left-center, AB buttons right-center, program row bottom
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

interface LayoutConfig {
  readonly dpadCenterX: number;
  readonly dpadCenterY: number;
  readonly dpadButtonSize: number;
  readonly dpadOffset: number;
  readonly btnCenterX: number;
  readonly btnCenterY: number;
}

const LAYOUTS: Record<string, LayoutConfig> = {
  portrait: {
    dpadCenterX: 18,
    dpadCenterY: 75,
    dpadButtonSize: 12,
    dpadOffset: 6,
    btnCenterX: 82,
    btnCenterY: 75,
  },
  landscape: {
    dpadCenterX: 12,
    dpadCenterY: 50,
    dpadButtonSize: 10,
    dpadOffset: 5,
    btnCenterX: 88,
    btnCenterY: 50,
  },
};

function getLayoutConfig(): LayoutConfig {
  if (typeof window === "undefined") return LAYOUTS.landscape;
  const isPortrait = window.matchMedia("(orientation: portrait)").matches;
  return isPortrait ? LAYOUTS.portrait : LAYOUTS.landscape;
}

function buildDpadButtons(config: LayoutConfig): ReadonlyArray<ButtonConfig> {
  const { dpadCenterX, dpadCenterY, dpadButtonSize, dpadOffset } = config;
  return [
    {
      label: "↑",
      left: `${dpadCenterX - dpadButtonSize / 2}vw`,
      top: `${dpadCenterY - dpadButtonSize / 2 - dpadOffset}vh`,
      size: `${dpadButtonSize}vw`,
      fontSize: `${Math.round(dpadButtonSize * 0.5)}vw`,
      action: { type: "move_north" as const },
    },
    {
      label: "↓",
      left: `${dpadCenterX - dpadButtonSize / 2}vw`,
      top: `${dpadCenterY - dpadButtonSize / 2 + dpadOffset}vh`,
      size: `${dpadButtonSize}vw`,
      fontSize: `${Math.round(dpadButtonSize * 0.5)}vw`,
      action: { type: "move_south" as const },
    },
    {
      label: "←",
      left: `${dpadCenterX - dpadButtonSize / 2 - dpadOffset}vw`,
      top: `${dpadCenterY - dpadButtonSize / 2}vh`,
      size: `${dpadButtonSize}vw`,
      fontSize: `${Math.round(dpadButtonSize * 0.5)}vw`,
      action: { type: "move_west" as const },
    },
    {
      label: "→",
      left: `${dpadCenterX - dpadButtonSize / 2 + dpadOffset}vw`,
      top: `${dpadCenterY - dpadButtonSize / 2}vh`,
      size: `${dpadButtonSize}vw`,
      fontSize: `${Math.round(dpadButtonSize * 0.5)}vw`,
      action: { type: "move_east" as const },
    },
  ];
}

function buildActionButtons(config: LayoutConfig): ReadonlyArray<ButtonConfig> {
  const { btnCenterX, btnCenterY } = config;
  return [
    {
      label: "A",
      left: `${btnCenterX - 7}vw`,
      top: `${btnCenterY - 7}vh`,
      size: "14vw",
      fontSize: "7vw",
      action: { type: "confirm" as const },
    },
    {
      label: "B",
      left: `${btnCenterX - 22}vw`,
      top: `${btnCenterY - 5}vh`,
      size: "10vw",
      fontSize: "5vw",
      action: { type: "jack_out" as const },
    },
  ];
}

/** Inject CSS + DOM elements for the on-screen gamepad. */
export function mountVirtualGamepad(handler: (action: GameAction) => void): () => void {
  if (typeof document === "undefined") {
    return () => {};
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
  row.querySelectorAll("button").forEach((btn) => {
    const idx = Number((btn as HTMLElement).dataset.handIndex);
    if (Number.isFinite(idx) && idx > 0) {
      btn.addEventListener("pointerdown", (e) => {
        e.preventDefault();
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
    const row = document.createElement("div");
    row.id = "wetrun-program-row";
    document.body.appendChild(row);
  }
  return root;
}

function renderOverlay(root: HTMLElement, handler: (action: GameAction) => void): void {
  const config = getLayoutConfig();
  const dpadButtons = buildDpadButtons(config);
  const actionButtons = buildActionButtons(config);

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
  for (const btn of dpadButtons) {
    appendButton(root, btn, handler);
  }
  for (const btn of actionButtons) {
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
