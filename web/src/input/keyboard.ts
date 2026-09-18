/** Keyboard input → game action mapper.
 *
 * Listens to keydown events on the document, translates them to GameActions
 * using the KEYBOARD_MAPPING table, and forwards to a registered callback.
 *
 * MVP scope: keyboard only. Mobile touch UI is Tier 2 (per ADR-0199).
 */
import type { GameAction } from "../core/types.ts";
import { KEYBOARD_MAPPING } from "../core/types.ts";

export type ActionHandler = (action: GameAction) => void;
export interface InputAction {
  type: string;
  payload?: any;
}

/**
 * Code-based action lookup for keys whose `event.code` is locale-independent
 * (physical key position). Used as a fallback when `event.key` doesn't match
 * the label in KEYBOARD_MAPPING — e.g. AZERTY users where physical `q`
 * produces `event.key === "a"`. Keys here are the smallest set required to
 * keep jack-out (`Q`) and program selection (`1`..`9`) layout-agnostic.
 */
const CODE_MAPPING: Readonly<Record<string, GameAction>> = Object.freeze({
  KeyQ: KEYBOARD_MAPPING["q"]!,
  Digit1: KEYBOARD_MAPPING["1"]!,
  Digit2: KEYBOARD_MAPPING["2"]!,
  Digit3: KEYBOARD_MAPPING["3"]!,
  Digit4: KEYBOARD_MAPPING["4"]!,
  Digit5: KEYBOARD_MAPPING["5"]!,
  Digit6: KEYBOARD_MAPPING["6"]!,
  Digit7: KEYBOARD_MAPPING["7"]!,
  Digit8: KEYBOARD_MAPPING["8"]!,
  Digit9: KEYBOARD_MAPPING["9"]!,
});

export class KeyboardInput {
  private handler: ActionHandler | null = null;
  private isActive = false;

  constructor(private readonly documentRef: Document = document) {
    this.onKeyDown = this.onKeyDown.bind(this);
  }

  /** Register the action handler. Replaces any previous handler. */
  setHandler(handler: ActionHandler): void {
    this.handler = handler;
  }

  /** Begin listening for keydown events. Idempotent. */
  start(): void {
    if (this.isActive) return;
    this.documentRef.addEventListener("keydown", this.onKeyDown);
    this.isActive = true;
  }

  /** Stop listening. Safe to call even if not started. */
  stop(): void {
    if (!this.isActive) return;
    this.documentRef.removeEventListener("keydown", this.onKeyDown);
    this.isActive = false;
  }

  private onKeyDown(event: KeyboardEvent): void {
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
      return;
    }
    // Ignore OS auto-repeat on modifier-bearing keystrokes — Enter held, etc.
    if (event.repeat && (event.ctrlKey || event.metaKey)) {
      return;
    }
    // Don't swallow Cmd+Tab / Cmd+R / similar OS shortcuts.
    if ((event.ctrlKey || event.metaKey) && event.key !== "Enter") {
      return;
    }
    const action = KEYBOARD_MAPPING[event.key] ?? CODE_MAPPING[event.code];
    if (action !== undefined && this.handler !== null) {
      event.preventDefault();
      this.handler(action);
    }
  }
}
