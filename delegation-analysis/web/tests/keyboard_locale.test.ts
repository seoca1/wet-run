/**
 * Tests for keyboard input behavior — particularly locale-independent layout
 * support (Fix #4). Regression coverage for: AZERTY/Dvorak jack-out and
 * digit-key program selection via event.code, modifier key filtering, and
 * OS auto-repeat handling.
 *
 * @vitest-environment jsdom
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { KeyboardInput } from "../src/input/keyboard.ts";

function dispatchKey(options: KeyboardEventInit & { code?: string }): void {
  const event = new KeyboardEvent("keydown", {
    bubbles: true,
    cancelable: true,
    ...options,
  });
  // jsdom doesn't always populate `code` from KeyboardEventInit; force it.
  if (options.code) {
    Object.defineProperty(event, "code", { value: options.code });
  }
  document.dispatchEvent(event);
}

describe("KeyboardInput — locale independence", () => {
  let input: KeyboardInput;
  let actions: Array<{ type: string; payload?: unknown }>;

  beforeEach(() => {
    actions = [];
    input = new KeyboardInput();
    input.setHandler((action) => actions.push(action));
    input.start();
  });

  afterEach(() => {
    input.stop();
  });

  it("physical Q triggers jack_out even if event.key is remapped (AZERTY)", () => {
    dispatchKey({ key: "a", code: "KeyQ" });
    expect(actions).toEqual([{ type: "jack_out" }]);
  });

  it("physical Digit1 triggers select_program even if event.key is remapped", () => {
    dispatchKey({ key: "&", code: "Digit1" });
    expect(actions).toEqual([{ type: "select_program", handIndex: 1 }]);
  });

  it("event.key lookup still works for QWERTY users", () => {
    dispatchKey({ key: "q", code: "KeyQ" });
    expect(actions).toEqual([{ type: "jack_out" }]);
  });

  it("Enter still maps to confirm", () => {
    dispatchKey({ key: "Enter", code: "Enter" });
    expect(actions).toEqual([{ type: "confirm" }]);
  });

  it("Space still maps to confirm", () => {
    dispatchKey({ key: " ", code: "Space" });
    expect(actions).toEqual([{ type: "confirm" }]);
  });

  it("ArrowUp still maps to move_north", () => {
    dispatchKey({ key: "ArrowUp", code: "ArrowUp" });
    expect(actions).toEqual([{ type: "move_north" }]);
  });

  it("is a no-op for unrecognized keys", () => {
    dispatchKey({ key: "F12", code: "F12" });
    expect(actions).toEqual([]);
  });
});

describe("KeyboardInput — modifiers and repeat", () => {
  let input: KeyboardInput;
  let actions: Array<{ type: string; payload?: unknown }>;

  beforeEach(() => {
    actions = [];
    input = new KeyboardInput();
    input.setHandler((action) => actions.push(action));
    input.start();
  });

  afterEach(() => {
    input.stop();
  });

  it("Cmd+R does not fire a game action", () => {
    dispatchKey({ key: "r", code: "KeyR", metaKey: true });
    expect(actions).toEqual([]);
  });

  it("Ctrl+T does not fire a game action", () => {
    dispatchKey({ key: "t", code: "KeyT", ctrlKey: true });
    expect(actions).toEqual([]);
  });

  it("repeat Enter+Cmd is swallowed (avoids auto-fire storms)", () => {
    dispatchKey({ key: "Enter", code: "Enter", metaKey: true, repeat: true });
    expect(actions).toEqual([]);
  });

  it("bare (non-modifier) Enter on repeat still fires confirm", () => {
    dispatchKey({ key: "Enter", code: "Enter", repeat: true });
    expect(actions).toEqual([{ type: "confirm" }]);
  });
});
