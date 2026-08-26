/** Virtual gamepad overlay for mobile/touch input (Tier 2c).
 *
 * Renders a translucent D-pad + ABXY buttons in HTML/CSS that map to
 * GameActions. Touch events → keydown synth events on the document.
 *
 * Auto-shows on devices with `pointer: coarse` (touch); auto-hides on
 * devices with `pointer: fine` (mouse/trackpad).
 */

import type { GameAction } from "../core/types.ts";

interface ButtonConfig {
  readonly label: string;
  readonly rect: { x: number; y: number; w: number; h: number };
  readonly action: GameAction;
}

interface DpadConfig {
  readonly rect: { x: number; y: number; w: number; h: number };
  readonly up: ButtonConfig;
  readonly down: ButtonConfig;
  readonly left: ButtonConfig;
  readonly right: ButtonConfig;
}

interface GamepadLayout {
  readonly dpad: DpadConfig;
  readonly buttons: ReadonlyArray<ButtonConfig>;
}

const LAYOUT: GamepadLayout = {
  dpad: {
    rect: { x: 16, y: 240, w: 144, h: 144 },
    up: {
      label: "↑",
      rect: { x: 64, y: 240, w: 48, h: 48 },
      action: { type: "move_north" as const },
    },
    down: {
      label: "↓",
      rect: { x: 64, y: 336, w: 48, h: 48 },
      action: { type: "move_south" as const },
    },
    left: {
      label: "←",
      rect: { x: 16, y: 288, w: 48, h: 48 },
      action: { type: "move_west" as const },
    },
    right: {
      label: "→",
      rect: { x: 112, y: 288, w: 48, h: 48 },
      action: { type: "move_east" as const },
    },
  },
  buttons: [
    {
      label: "A",
      rect: { x: 440, y: 288, w: 64, h: 64 },
      action: { type: "confirm" as const },
    },
    {
      label: "B",
      rect: { x: 360, y: 336, w: 48, h: 48 },
      action: { type: "cancel" as const },
    },
  ],
};

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

function ensureOverlayRoot(): HTMLElement {
  let root = document.getElementById("wetrun-gamepad-root");
  if (!root) {
    root = document.createElement("div");
    root.id = "wetrun-gamepad-root";
    root.setAttribute("aria-label", "Virtual gamepad");
    document.body.appendChild(root);
  }
  return root;
}

function renderOverlay(root: HTMLElement, handler: (action: GameAction) => void): void {
  root.innerHTML = `
    <style>
      #wetrun-gamepad-root {
        position: fixed; inset: 0; pointer-events: none;
        font-family: monospace;
      }
      #wetrun-gamepad-root button {
        position: absolute; pointer-events: auto;
        background: rgba(0, 0, 0, 0.55); border: 1px solid #00ff41;
        color: #00ff41; font-size: 20px; font-weight: bold;
        padding: 0; margin: 0; line-height: 1;
        touch-action: none; user-select: none;
      }
      #wetrun-gamepad-root button:active { background: rgba(0, 255, 65, 0.4); }
    </style>
    ${LAYOUT.dpad.up.label ? "" : ""}
  `;
  appendButton(root, LAYOUT.dpad.up);
  appendButton(root, LAYOUT.dpad.down);
  appendButton(root, LAYOUT.dpad.left);
  appendButton(root, LAYOUT.dpad.right);
  for (const btn of LAYOUT.buttons) {
    appendButton(root, btn);
  }

  function appendButton(parent: HTMLElement, cfg: ButtonConfig): void {
    const btn = document.createElement("button");
    btn.textContent = cfg.label;
    btn.style.left = `${cfg.rect.x}px`;
    btn.style.top = `${cfg.rect.y}px`;
    btn.style.width = `${cfg.rect.w}px`;
    btn.style.height = `${cfg.rect.h}px`;
    btn.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      handler(cfg.action);
    });
    parent.appendChild(btn);
  }
}

/** Returns true when the device has a coarse pointer (touch). */
export function isTouchDevice(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(pointer: coarse)").matches;
}
