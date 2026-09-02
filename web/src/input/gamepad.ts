/** Physical gamepad input handler (Tier 3).
 *
 * Uses the Gamepad API to map physical controller buttons/sticks to GameActions.
 * Standard mapping follows Xbox/PlayStation layout:
 *   - D-pad: move_north/south/east/west
 *   - A/Cross: confirm
 *   - B/Circle: jack_out (back)
 *   - X/Square: not mapped (reserved)
 *   - Y/Triangle: not mapped (reserved)
 *   - Left stick: move (analog → digital threshold)
 *   - Shoulder buttons: program select (L1/R1 = prev/next in hand)
 *
 * Polls gamepad state via requestAnimationFrame and emits actions on
 * button press (not hold) to prevent repeated triggers.
 */
import type { GameAction } from "../core/types.ts";

export type GamepadActionHandler = (action: GameAction) => void;

interface GamepadState {
  readonly id: string;
  readonly index: number;
  readonly axes: ReadonlyArray<number>;
  readonly buttons: ReadonlyArray<boolean>;
}

const GAMEPAD_DEADZONE = 0.5;

/** Standard gamepad button indices (matches navigator.getGamepads mapping). */
const BUTTON = {
  A: 0,      // Cross (PS) / A (Xbox)
  B: 1,      // Circle (PS) / B (Xbox)
  X: 2,      // Square (PS) / X (Xbox)
  Y: 3,      // Triangle (PS) / Y (Xbox)
  LB: 4,     // L1 / Left Bumper
  RB: 5,     // R1 / Right Bumper
  LT: 6,     // L2 / Left Trigger
  RT: 7,     // R2 / Right Trigger
  BACK: 8,   // Select / Back / Share
  START: 9,  // Start / Options
  LS: 10,    // Left Stick Press
  RS: 11,    // Right Stick Press
  DPAD_UP: 12,
  DPAD_DOWN: 13,
  DPAD_LEFT: 14,
  DPAD_RIGHT: 15,
} as const;

export class GamepadInput {
  private handler: GamepadActionHandler | null = null;
  private isActive = false;
  private animFrameId: number | null = null;
  private lastState: Map<number, GamepadState> = new Map();

  constructor(private readonly windowRef: Window = window) {}

  setHandler(handler: GamepadActionHandler): void {
    this.handler = handler;
  }

  start(): void {
    if (this.isActive) return;
    if (!this.isSupported()) {
      console.warn("[gamepad] Gamepad API not supported in this browser");
      return;
    }
    this.isActive = true;
    this.poll();
  }

  stop(): void {
    this.isActive = false;
    if (this.animFrameId !== null) {
      this.windowRef.cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    this.lastState.clear();
  }

  isSupported(): boolean {
    return typeof this.windowRef.navigator?.getGamepads === "function";
  }

  getConnectedCount(): number {
    if (!this.isSupported()) return 0;
    const gamepads = this.windowRef.navigator.getGamepads();
    let count = 0;
    for (const gp of gamepads) {
      if (gp) count++;
    }
    return count;
  }

  private poll(): void {
    if (!this.isActive) return;

    const gamepads = this.windowRef.navigator.getGamepads();
    for (let i = 0; i < gamepads.length; i++) {
      const gp = gamepads[i];
      if (!gp) continue;

      const prevState = this.lastState.get(i);
      const currentState: GamepadState = {
        id: gp.id,
        index: gp.index,
        axes: Array.from(gp.axes),
        buttons: gp.buttons.map((b) => b.pressed),
      };

      if (prevState) {
        this.detectChanges(prevState, currentState);
      }

      this.lastState.set(i, currentState);
    }

    this.animFrameId = this.windowRef.requestAnimationFrame(() => this.poll());
  }

  private detectChanges(prev: GamepadState, curr: GamepadState): void {
    if (!this.handler) return;

    // Check button presses (transition from not pressed to pressed)
    for (let i = 0; i < curr.buttons.length; i++) {
      if (curr.buttons[i] && !prev.buttons[i]) {
        const action = this.mapButton(i);
        if (action) {
          this.handler(action);
        }
      }
    }

    // Check D-pad via axes (for controllers that report D-pad as axes)
    this.checkDpadAxes(prev.axes, curr.axes);
  }

  private checkDpadAxes(prevAxes: ReadonlyArray<number>, currAxes: ReadonlyArray<number>): void {
    if (!this.handler) return;

    // Some controllers map D-pad to axes[6] (horizontal) and axes[7] (vertical)
    if (currAxes.length > 7) {
      const horizontal = currAxes[6] ?? 0;
      const vertical = currAxes[7] ?? 0;
      const prevHorizontal = prevAxes[6] ?? 0;
      const prevVertical = prevAxes[7] ?? 0;

      // Horizontal: -1 = left, +1 = right
      if (horizontal < -GAMEPAD_DEADZONE && prevHorizontal >= -GAMEPAD_DEADZONE) {
        this.handler({ type: "move_west" });
      } else if (horizontal > GAMEPAD_DEADZONE && prevHorizontal <= GAMEPAD_DEADZONE) {
        this.handler({ type: "move_east" });
      }

      // Vertical: -1 = up, +1 = down
      if (vertical < -GAMEPAD_DEADZONE && prevVertical >= -GAMEPAD_DEADZONE) {
        this.handler({ type: "move_north" });
      } else if (vertical > GAMEPAD_DEADZONE && prevVertical <= GAMEPAD_DEADZONE) {
        this.handler({ type: "move_south" });
      }
    }
  }

  private mapButton(buttonIndex: number): GameAction | null {
    switch (buttonIndex) {
      case BUTTON.A:
        return { type: "confirm" };
      case BUTTON.B:
        return { type: "jack_out" };
      case BUTTON.DPAD_UP:
        return { type: "move_north" };
      case BUTTON.DPAD_DOWN:
        return { type: "move_south" };
      case BUTTON.DPAD_LEFT:
        return { type: "move_west" };
      case BUTTON.DPAD_RIGHT:
        return { type: "move_east" };
      case BUTTON.LB:
        return { type: "select_program", handIndex: 1 };
      case BUTTON.RB:
        return { type: "select_program", handIndex: 2 };
      case BUTTON.BACK:
        return { type: "jack_out" };
      case BUTTON.START:
        return { type: "confirm" };
      default:
        return null;
    }
  }
}

/** Check if a physical gamepad is connected. */
export function isGamepadConnected(): boolean {
  if (typeof navigator?.getGamepads !== "function") return false;
  const gamepads = navigator.getGamepads();
  for (const gp of gamepads) {
    if (gp) return true;
  }
  return false;
}

/** Get gamepad display name for UI. */
export function getGamepadName(): string | null {
  if (typeof navigator?.getGamepads !== "function") return null;
  const gamepads = navigator.getGamepads();
  for (const gp of gamepads) {
    if (gp) return gp.id;
  }
  return null;
}
