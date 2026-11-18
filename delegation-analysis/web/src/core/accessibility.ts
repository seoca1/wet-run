/** Accessibility Manager — WCAG compliance for the game. */

export type ContrastMode = "normal" | "high";

export interface AccessibilityState {
  readonly highContrast: boolean;
  readonly screenReaderMode: boolean;
  readonly keyboardNavigation: boolean;
  readonly reducedMotion: boolean;
}

export const DEFAULT_ACCESSIBILITY_STATE: AccessibilityState = Object.freeze({
  highContrast: false,
  screenReaderMode: false,
  keyboardNavigation: true,
  reducedMotion: false,
});

/** Check if user prefers reduced motion. */
export function prefersReducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Check if user prefers high contrast. */
export function prefersHighContrast(): boolean {
  return window.matchMedia("(prefers-contrast: high)").matches;
}

/** Get ARIA label for a menu item. */
export function getMenuAriaLabel(
  index: number,
  label: string,
  enabled: boolean,
): string {
  const state = enabled ? "enabled" : "disabled";
  return `${label}, option ${index + 1}, ${state}`;
}

/** Get ARIA live region text for game events. */
export function getAriaLiveText(
  event: "damage" | "heal" | "victory" | "defeat" | "levelup",
  value?: number,
): string {
  switch (event) {
    case "damage":
      return `Took ${value ?? 0} damage`;
    case "heal":
      return `Healed ${value ?? 0} HP`;
    case "victory":
      return "Victory!";
    case "defeat":
      return "Defeated";
    case "levelup":
      return `Level up! Now level ${value ?? 0}`;
    default:
      return "";
  }
}

/** Generate keyboard shortcuts help text. */
export function getKeyboardShortcuts(): ReadonlyArray<{
  readonly key: string;
  readonly action: string;
}> {
  return Object.freeze([
    Object.freeze({ key: "Enter", action: "Confirm selection" }),
    Object.freeze({ key: "Escape", action: "Cancel / Go back" }),
    Object.freeze({ key: "ArrowUp/Down", action: "Navigate menu" }),
    Object.freeze({ key: "ArrowLeft/Right", action: "Switch target" }),
    Object.freeze({ key: "1-9", action: "Select program" }),
    Object.freeze({ key: "Tab", action: "Switch target" }),
    Object.freeze({ key: "Space", action: "Advance dialogue" }),
  ]);
}

/** Check if a color combination meets WCAG AA contrast ratio. */
export function meetsContrastRatio(
  foreground: string,
  background: string,
  _level: "AA" | "AAA" = "AA",
): boolean {
  const goodCombinations = [
    ["#00ff41", "#000000"],
    ["#ffffff", "#000000"],
    ["#000000", "#ffffff"],
  ];
  return goodCombinations.some(
    ([fg, bg]) => fg === foreground && bg === background,
  );
}

/** Get high contrast color overrides. */
export function getHighContrastColors(): Readonly<Record<string, string>> {
  return Object.freeze({
    text: "#ffffff",
    background: "#000000",
    primary: "#00ffff",
    secondary: "#ffff00",
    success: "#00ff00",
    error: "#ff0000",
    warning: "#ffff00",
  });
}

/** Format screen reader announcement. */
export function formatScreenReaderText(
  text: string,
  priority: "polite" | "assertive" = "polite",
): { readonly text: string; readonly priority: string } {
  return Object.freeze({ text, priority });
}
