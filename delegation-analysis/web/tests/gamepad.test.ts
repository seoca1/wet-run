/**
 * Tests for physical gamepad input support.
 */
// @vitest-environment jsdom

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { GamepadInput, isGamepadConnected, getGamepadName } from "../src/input/gamepad.ts";
import type { GameAction } from "../src/core/types.ts";

function mockGamepads(gamepads: Array<{ id: string; buttons: Array<{ pressed: boolean; value: number }>; axes: number[] } | null>): void {
  Object.defineProperty(navigator, "getGamepads", {
    value: vi.fn(() => gamepads),
    writable: true,
    configurable: true,
  });
}

describe("GamepadInput", () => {
  let gamepad: GamepadInput;
  let actions: GameAction[];

  beforeEach(() => {
    actions = [];
    mockGamepads([]);
    gamepad = new GamepadInput();
    gamepad.setHandler((action) => actions.push(action));
  });

  afterEach(() => {
    gamepad.stop();
  });

  it("isSupported returns false when navigator.getGamepads is not available", () => {
    const original = navigator.getGamepads;
    delete (navigator as { getGamepads?: typeof navigator.getGamepads }).getGamepads;
    expect(gamepad.isSupported()).toBe(false);
    navigator.getGamepads = original;
  });

  it("isSupported returns true when navigator.getGamepads is available", () => {
    expect(gamepad.isSupported()).toBe(true);
  });

  it("getConnectedCount returns 0 when no gamepads connected", () => {
    expect(gamepad.getConnectedCount()).toBe(0);
  });

  it("start and stop are idempotent", () => {
    gamepad.start();
    gamepad.start();
    gamepad.stop();
    gamepad.stop();
  });
});

describe("isGamepadConnected", () => {
  beforeEach(() => {
    mockGamepads([]);
  });

  it("returns false when no gamepads connected", () => {
    expect(isGamepadConnected()).toBe(false);
  });
});

describe("getGamepadName", () => {
  beforeEach(() => {
    mockGamepads([]);
  });

  it("returns null when no gamepads connected", () => {
    expect(getGamepadName()).toBeNull();
  });
});
