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
    // Ignore key events that originate from form inputs.
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
      return;
    }
    const action = KEYBOARD_MAPPING[event.key];
    if (action !== undefined && this.handler !== null) {
      event.preventDefault();
      this.handler(action);
    }
  }
}
