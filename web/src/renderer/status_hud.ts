/** Per-target status-effect HUD (proposal P14).
 *
 * The status HUD used to merge every effect on the roster into one flat
 * bracket drawn next to the *active* ICE only, so a player-side `burn` and
 * an ICE-side `burn` were indistinguishable, and the ADR-0226 ICE effects
 * were invisible because they had no glyph at all.
 *
 * This module groups the live status effects by who carries them, renders
 * each group as `[GLYPH<turns>]` and draws it onto the grid.
 */
import type { StatusEffectInstance } from "../core/types.ts";
import { setText, type Grid } from "../core/grid.ts";
import { STATUS_GLYPHS } from "./vfx.ts";

/** One status effect reduced to what the HUD needs to draw it. */
export interface StatusGlyphEntry {
  readonly kind: StatusEffectInstance["kind"];
  readonly glyph: string;
  readonly remaining: number;
}

/** The status effects carried by one target. */
export interface TargetStatusGroup {
  readonly target: "player" | "ice";
  /** Roster slot for ICE targets; `-1` for the player. */
  readonly iceIndex: number;
  readonly entries: readonly StatusGlyphEntry[];
}

export function statusGlyphFor(kind: string): string | undefined {
  return STATUS_GLYPHS[kind];
}

/** Group the live status effects by the target that carries them.
 *
 * An ICE-targeted effect without an `iceIndex` belongs to the active ICE —
 * that is how the player-side burn / slow effects are recorded (see the
 * `StatusEffectInstance` contract in `core/types.ts`).
 */
export function groupStatusByTarget(
  effects: readonly StatusEffectInstance[],
  activeIceIndex: number,
): readonly TargetStatusGroup[] {
  const player: StatusGlyphEntry[] = [];
  const byIce = new Map<number, StatusGlyphEntry[]>();

  for (const effect of effects) {
    const glyph = statusGlyphFor(effect.kind);
    if (glyph === undefined) continue;
    const entry: StatusGlyphEntry = {
      kind: effect.kind,
      glyph,
      remaining: effect.remaining,
    };
    if (effect.target === "player") {
      player.push(entry);
      continue;
    }
    const slot = effect.iceIndex ?? activeIceIndex;
    const bucket = byIce.get(slot);
    if (bucket === undefined) byIce.set(slot, [entry]);
    else bucket.push(entry);
  }

  const groups: TargetStatusGroup[] = [];
  if (player.length > 0) {
    groups.push({ target: "player", iceIndex: -1, entries: player });
  }
  for (const iceIndex of [...byIce.keys()].sort((a, b) => a - b)) {
    groups.push({
      target: "ice",
      iceIndex,
      entries: byIce.get(iceIndex) ?? [],
    });
  }
  return groups;
}

/** Look up the group for one target. */
export function statusGroupForTarget(
  groups: readonly TargetStatusGroup[],
  target: "player" | "ice",
  iceIndex = -1,
): TargetStatusGroup | undefined {
  return groups.find(
    (g) => g.target === target && (target === "player" || g.iceIndex === iceIndex),
  );
}

/** Render the entries as one bracket, each glyph carrying its turn count. */
export function formatStatusEntries(entries: readonly StatusGlyphEntry[]): string {
  const glyphs = entries
    .filter((entry) => entry.glyph !== "")
    .map((entry) => `${entry.glyph}${entry.remaining}`);
  if (glyphs.length === 0) return "";
  return "[" + glyphs.join("") + "]";
}

/** Render one target group. */
export function formatTargetStatus(group: TargetStatusGroup | undefined): string {
  if (group === undefined) return "";
  return formatStatusEntries(group.entries);
}

/** Draw a target group's glyphs onto the grid. No-op when there is nothing
 * to draw, so the grid instance is returned unchanged. */
export function drawTargetStatus(
  grid: Grid,
  x: number,
  y: number,
  group: TargetStatusGroup | undefined,
  color: string,
): Grid {
  const text = formatTargetStatus(group);
  if (text === "") return grid;
  return setText(grid, x, y, text, color);
}
