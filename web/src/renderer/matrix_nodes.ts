/** Pure Matrix presentation: position, actionable frontier, objective and depth. */
import type { Matrix, MatrixNode, ZoneDepth } from "../core/types";
import { EVENT_GLYPHS, EVENT_LABELS } from "../core/event_matrix";
import { PALETTE } from "./palette";

export interface MatrixPosition {
  readonly matrix: Matrix;
  readonly current: number;
  readonly visited: readonly number[];
  readonly cleared: readonly number[];
  readonly selected: number | null;
}

export interface MatrixLine {
  readonly text: string;
  readonly fg: string;
}

const DEPTHS: readonly ZoneDepth[] = [
  "surface",
  "mid",
  "deep",
  "core",
  "core-deep",
];

/** Stable node identity, deliberately not an ordinal row number or shortcut. */
export function matrixNodeId(index: number): string {
  return `N${String(index + 1).padStart(2, "0")}`;
}

/** Build bounded text rows. Secondary map detail yields before the frontier. */
export function matrixNodeLines(
  position: MatrixPosition,
  width: number,
  height: number,
): readonly MatrixLine[] {
  const { matrix, current, visited, cleared, selected } = position;
  // Local output builder only; neither the matrix nor navigation state is mutated.
  const lines: MatrixLine[] = [];
  const add = (text: string, fg = PALETTE.GRAY_LIGHT): void => {
    lines.push({ text, fg });
  };
  const state = (i: number): string =>
    cleared.includes(i) ? "CLEAR" : visited.includes(i) ? "SEEN" : "NEW";
  const boss = (i: number): boolean =>
    i === matrix.bossNode || matrix.nodes[i]?.isBoss === true;
  const label = (node: MatrixNode, i: number): string => {
    const kind = node.eventKind ?? "combat";
    return `${EVENT_GLYPHS[kind]} ${matrixNodeId(i)} ${node.zone.toUpperCase()}${boss(i) ? " (BOSS)" : ""} · ${state(i)}`;
  };
  const detail = (node: MatrixNode): string =>
    `${node.iceIds.length} ICE · ${node.reward.credits}cr · ${EVENT_LABELS[node.eventKind ?? "combat"]}`;
  const here = matrix.nodes[current];
  const adjacent = (here?.adjacent ?? []).filter(
    (i) => i !== current && matrix.nodes[i] !== undefined,
  );
  const zones = DEPTHS.filter((zone) =>
    matrix.nodes.some((n) => n.zone === zone),
  );
  // Preserve two rows per offer on the supported grids; compact only when needed.
  const showDetails = 14 + adjacent.length * 2 + zones.length <= height;
  add("▸ YOU ARE HERE", PALETTE.GREEN_NEON);
  if (here) {
    add(`▸ ${label(here, current)}`, PALETTE.GREEN_NEON);
    if (showDetails) add(`  ${detail(here)}`);
  } else {
    add("No node here — ESC: back");
  }
  add("");
  const heading = `─ REACHABLE NOW (${adjacent.length}) `;
  add(`┌${heading}${"─".repeat(Math.max(0, width - heading.length - 2))}┐`);
  for (const i of adjacent) {
    const node = matrix.nodes[i];
    if (!node) continue;
    const marker = i === selected ? ">" : "→";
    const fg = i === selected ? PALETTE.GREEN_NEON : PALETTE.CYAN_LIGHT;
    const text = `${marker} ${label(node, i)}`;
    add(`│${text.slice(0, width - 2).padEnd(width - 2)}│`, fg);
    if (showDetails) {
      add(
        `│ ${detail(node)
          .slice(0, width - 3)
          .padEnd(width - 3)}│`,
      );
    }
  }
  if (adjacent.length === 0) {
    add(`│${"No routes — ENTER: ICE".slice(0, width - 2).padEnd(width - 2)}│`);
  }
  add(`└${"─".repeat(Math.max(0, width - 2))}┘`);
  add("");
  add("◆ OBJECTIVE: BOSS", PALETTE.MAGENTA_LIGHT);
  const objective = matrix.nodes[matrix.bossNode];
  if (objective) {
    const location =
      current === matrix.bossNode
        ? "HERE"
        : adjacent.includes(matrix.bossNode)
          ? "REACHABLE NOW"
          : "NOT ADJACENT";
    add(
      `${matrixNodeId(matrix.bossNode)} ${objective.zone.toUpperCase()} · ${location}`,
      PALETTE.MAGENTA_LIGHT,
    );
    add(`  ${state(matrix.bossNode)}`);
  } else {
    add("No objective in this matrix");
  }
  add("");
  add("DEPTH / ZONES (not routes)");
  add("Nxx = node ID, not travel order");
  add("▸ here → route ✓ seen + clear · new");
  // Each zone always gets its own heading. Extra rows show node identities,
  // never invented connections: adjacency is represented only by the frontier.
  let spare = Math.max(0, height - lines.length - zones.length);
  for (const [depth, zone] of zones.entries()) {
    const indices = matrix.nodes.flatMap((node, i) =>
      node.zone === zone ? [i] : [],
    );
    const indent = " ".repeat(Math.min(depth * 2, 8));
    const allSeen = indices.every((i) => visited.includes(i));
    add(
      `${indent}${allSeen ? "✓ " : ""}${zone.toUpperCase()} (${indices.length})`,
      PALETTE.CYAN_LIGHT,
    );
    const tokens = indices.map(
      (i) =>
        `${i === current ? "▸" : cleared.includes(i) ? "+" : visited.includes(i) ? "✓" : adjacent.includes(i) ? "→" : "·"}${matrixNodeId(i)}`,
    );
    const perRow = Math.max(1, Math.floor((width - indent.length - 2) / 5));
    const needed = Math.ceil(tokens.length / perRow);
    const available = Math.min(needed, spare);
    for (let row = 0; row < available; row++) {
      const start = row * perRow;
      const remaining = tokens.length - start;
      const last = row === available - 1 && remaining > perRow;
      const text = last
        ? `${tokens.slice(start, start + Math.max(0, perRow - 2)).join(" ")} … +${remaining - Math.max(0, perRow - 2)}`
        : tokens.slice(start, start + perRow).join(" ");
      add(`${indent}  ${text}`);
    }
    spare -= available;
  }
  return lines;
}
