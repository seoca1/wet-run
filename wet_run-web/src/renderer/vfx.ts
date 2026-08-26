/** VFX helpers — ASCII combat visual effects.

Pure functions for HP bars, color thresholds, and status indicators.
No state, no side effects; testable in isolation.
 */

import { PALETTE } from "./palette.ts";

export function healthBar(filled: number, total: number, cells = 12): string {
  if (total <= 0) return "[" + " ".repeat(cells) + "]";
  const ratio = Math.max(0, Math.min(1, filled / total));
  const filledCount = Math.round(ratio * cells);
  return "[" + "█".repeat(filledCount) + "░".repeat(cells - filledCount) + "]";
}

export function healthColor(filled: number, total: number): string {
  if (total <= 0) return PALETTE.GRAY_LIGHT;
  const ratio = filled / total;
  if (ratio > 0.6) return PALETTE.GREEN_NEON;
  if (ratio > 0.3) return PALETTE.YELLOW_AMBER;
  return PALETTE.RED_BRIGHT;
}

export function formatStatusLabel(phase: string): string {
  switch (phase) {
    case "victory":
      return "[ VICTORY ]";
    case "defeat":
      return "[ DEFEATED ]";
    default:
      return "";
  }
}