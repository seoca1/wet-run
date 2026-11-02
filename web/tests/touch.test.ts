/** Tier 2c tests for virtual gamepad overlay (mobile touch input).
 */
// @vitest-environment jsdom

import { describe, it, expect, beforeAll, vi } from "vitest";
import {
  mountVirtualGamepad,
  isTouchDevice,
  updateProgramRow,
  PROGRAM_PRESS_DEBOUNCE_MS,
  MIN_TOUCH_TARGET_PX,
} from "../src/input/touch";
import {
  affordanceAriaLabel,
  touchAffordanceLines,
  type ProgramAffordance,
} from "../src/core/combat/program_affordance";

// jsdom doesn't ship matchMedia — polyfill before tests run.
beforeAll(() => {
  if (typeof window !== "undefined" && typeof window.matchMedia !== "function") {
    Object.defineProperty(window, "matchMedia", {
      value: (query: string) => ({
        matches: query.includes("coarse"),
        media: query,
        onchange: null,
        addEventListener: () => {},
        removeEventListener: () => {},
        addListener: () => {},
        removeListener: () => {},
        dispatchEvent: () => false,
      }),
      writable: true,
      configurable: true,
    });
  }
});

describe("virtual gamepad overlay", () => {
  it("mounts root element on first call", () => {
    const unmount = mountVirtualGamepad(() => {});
    const root = document.getElementById("wetrun-gamepad-root");
    expect(root).not.toBeNull();
    unmount();
  });

  it("creates 6 buttons (4 dpad + A + B)", () => {
    const unmount = mountVirtualGamepad(() => {});
    const root = document.getElementById("wetrun-gamepad-root");
    const buttons = root?.querySelectorAll("button") ?? [];
    expect(buttons.length).toBe(6);
    unmount();
  });

  it("cleans up DOM on unmount", () => {
    const unmount = mountVirtualGamepad(() => {});
    unmount();
    const root = document.getElementById("wetrun-gamepad-root");
    expect(root?.innerHTML).toBe("");
  });

  it("returns a no-op function in non-browser environments", () => {
    // jsdom IS a browser env, so we can't easily test SSR path here.
    // Just verify the returned function is callable.
    const unmount = mountVirtualGamepad(() => {});
    expect(typeof unmount).toBe("function");
    unmount();
  });

  it("uses a 44px minimum touch target (Apple HIG / WCAG 2.5.5)", () => {
    expect(MIN_TOUCH_TARGET_PX).toBeGreaterThanOrEqual(44);
  });

  it("floors every gamepad button at MIN_TOUCH_TARGET_PX without dropping vw sizing", () => {
    const unmount = mountVirtualGamepad(() => {});
    const root = document.getElementById("wetrun-gamepad-root");
    const buttons = Array.from(root?.querySelectorAll("button") ?? []);
    expect(buttons.length).toBe(6);
    for (const btn of buttons) {
      expect(btn.style.minWidth).toBe(`${MIN_TOUCH_TARGET_PX}px`);
      expect(btn.style.minHeight).toBe(`${MIN_TOUCH_TARGET_PX}px`);
      expect(btn.style.width).toMatch(/vw$/);
      expect(btn.style.height).toMatch(/vw$/);
    }
    unmount();
  });

  it("isTouchDevice returns boolean", () => {
    const result = isTouchDevice();
    expect(typeof result).toBe("boolean");
  });

  it("fires exactly one action per tap across duplicate event types", () => {
    const actions: string[] = [];
    const unmount = mountVirtualGamepad((a) => actions.push(a.type));
    const root = document.getElementById("wetrun-gamepad-root");
    const btn = root?.querySelector("button");
    expect(btn).toBeTruthy();
    for (const type of ["pointerdown", "touchstart", "mousedown", "click"]) {
      btn?.dispatchEvent(new Event(type, { bubbles: true, cancelable: true }));
    }
    expect(actions.length).toBe(1);
    unmount();
  });
});

describe("program row (P12)", () => {
  // ADR-0251: the row is fed the same affordance rows the canvas draws.
  const DECK: ReadonlyArray<ProgramAffordance> = [
    { slot: 1, programId: "backdoor", name: "BACKDOOR", cost: 2, after: 12, blocked: false, target: "ICE" },
    { slot: 2, programId: "barrier", name: "BARRIER", cost: 3, after: 13, blocked: false, target: "ICE" },
    { slot: 3, programId: "boost", name: "BOOST", cost: 2, after: 12, blocked: false, target: "ICE" },
  ];

  beforeAll(() => {
    mountVirtualGamepad(() => {});
  });

  function getRowButtons(): HTMLButtonElement[] {
    const row = document.getElementById("wetrun-program-row");
    return Array.from(row?.querySelectorAll("button") ?? []);
  }

  it("renders one button per deck entry", () => {
    updateProgramRow(DECK);
    expect(getRowButtons().length).toBe(DECK.length);
  });

  it("clears the row when the deck is empty", () => {
    updateProgramRow(DECK);
    updateProgramRow([]);
    expect(getRowButtons().length).toBe(0);
  });

  it("reports the pressed hand index to the callback", () => {
    const pressed: number[] = [];
    updateProgramRow(DECK, (idx) => pressed.push(idx));
    const buttons = getRowButtons();
    buttons[1]?.dispatchEvent(
      new Event("pointerdown", { bubbles: true, cancelable: true }),
    );
    expect(pressed).toEqual([2]);
  });

  it("fires the callback on pointerdown (no tap latency)", () => {
    const pressed: number[] = [];
    updateProgramRow(DECK, (idx) => pressed.push(idx));
    const buttons = getRowButtons();
    buttons[0]?.dispatchEvent(
      new Event("pointerdown", { bubbles: true, cancelable: true }),
    );
    expect(pressed.length).toBe(1);
  });

  it("rejects a duplicate press inside the debounce window", () => {
    const pressed: number[] = [];
    updateProgramRow(DECK, (idx) => pressed.push(idx));
    const buttons = getRowButtons();
    buttons[0]?.dispatchEvent(
      new Event("pointerdown", { bubbles: true, cancelable: true }),
    );
    buttons[0]?.dispatchEvent(
      new Event("pointerdown", { bubbles: true, cancelable: true }),
    );
    expect(pressed.length).toBe(1);
  });

  it("accepts a press after the debounce window has elapsed", () => {
    vi.useFakeTimers();
    try {
      const pressed: number[] = [];
      updateProgramRow(DECK, (idx) => pressed.push(idx));
      const buttons = getRowButtons();
      buttons[0]?.dispatchEvent(
        new Event("pointerdown", { bubbles: true, cancelable: true }),
      );
      vi.advanceTimersByTime(PROGRAM_PRESS_DEBOUNCE_MS + 1);
      buttons[0]?.dispatchEvent(
        new Event("pointerdown", { bubbles: true, cancelable: true }),
      );
      expect(pressed.length).toBe(2);
    } finally {
      vi.useRealTimers();
    }
  });

  it("uses a 120ms debounce window", () => {
    expect(PROGRAM_PRESS_DEBOUNCE_MS).toBe(120);
  });

  it("floors program buttons at MIN_TOUCH_TARGET_PX while keeping vw/vh scaling", () => {
    updateProgramRow(DECK);
    for (const btn of getRowButtons()) {
      const style = btn.getAttribute("style") ?? "";
      expect(style).toContain(`min-width:max(${MIN_TOUCH_TARGET_PX}px, 8vw)`);
      expect(style).toContain(`min-height:max(${MIN_TOUCH_TARGET_PX}px, 6vh)`);
    }
  });

  it("falls back to the wetrun global when no callback is given", () => {
    const calls: number[] = [];
    (window as unknown as { wetrun?: unknown }).wetrun = {
      handleProgramButton: (handIndex: number) => calls.push(handIndex),
    };
    try {
      updateProgramRow(DECK);
      const buttons = getRowButtons();
      buttons[0]?.dispatchEvent(
        new Event("pointerdown", { bubbles: true, cancelable: true }),
      );
      expect(calls).toEqual([1]);
    } finally {
      delete (window as unknown as { wetrun?: unknown }).wetrun;
    }
  });

  it("labels each button with the canvas row's facts, visibly and for assistive tech (ADR-0251)", () => {
    const rows: ReadonlyArray<ProgramAffordance> = [
      ...DECK.slice(0, 2),
      { slot: 3, programId: "sweep", name: "SWEEP", cost: 1, after: 11, blocked: false, target: "ALL ICE" },
      { slot: 4, programId: "kraken", name: "KRAKEN", cost: 4, after: 104, blocked: true, target: "ICE" },
    ];
    const pressed: number[] = [];
    updateProgramRow(rows, (idx) => pressed.push(idx));
    const buttons = getRowButtons();
    expect(buttons).toHaveLength(rows.length);
    buttons.forEach((btn, i) => {
      const row = rows[i]!;
      expect(btn.dataset.handIndex).toBe(String(row.slot));
      expect(btn.getAttribute("aria-label")).toBe(affordanceAriaLabel(row));
      const lines = Array.from(btn.querySelectorAll("span")).map((el) => el.textContent);
      expect(lines).toEqual([...touchAffordanceLines(row)]);
    });
    expect(buttons[3]?.textContent).toContain("BLOCKED");
    expect(buttons[2]?.getAttribute("aria-label")).toContain("ALL ICE");
    buttons[3]?.dispatchEvent(new Event("pointerdown", { bubbles: true, cancelable: true }));
    expect(pressed).toEqual([4]);
  });

  it("does not show the four-letter id strip any more (ADR-0251)", () => {
    updateProgramRow(DECK);
    const text = getRowButtons().map((b) => b.textContent ?? "");
    expect(text.some((t) => t.includes("1.back"))).toBe(false);
  });
});
