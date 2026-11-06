/** Selected-node detail card for the Matrix board (ADR-0249).
 *
 * The former node list is demoted to this card: it details the targeted
 * neighbour (or the current node when nothing is targeted), names the
 * destinations in arrow order and keeps the objective in words.
 */
import type { Matrix, MatrixNode } from "../core/types";
import { EVENT_GLYPHS, EVENT_LABELS } from "../core/event_matrix";
import { routePreview, routePreviewLine } from "../core/dungeon/route_preview";
import { PALETTE } from "./palette";
import { frontierOf, isBossNode, nodeState } from "./matrix_board";

export interface MatrixPosition {
  readonly matrix: Matrix;
  readonly current: number;
  readonly visited: readonly number[];
  readonly cleared: readonly number[];
  readonly selected: number | null;
  /** Nodes the runner walked past instead of fighting (ADR-0281 route pricing). */
  readonly bypassed?: readonly number[];
}

export interface MatrixLine {
  readonly text: string;
  readonly fg: string;
}

/** Event glyphs for the card. `◆` is reserved for the boss on this screen
 * (ADR-0249 rule 7), so a cache shows `¤` here instead. */
const CARD_GLYPHS = { ...EVENT_GLYPHS, cache: "¤" } as const;

/** Rows the card always occupies, so the board never shifts between nodes. */
export const CARD_ROWS = 8;

/** Stable node identity, deliberately not an ordinal row number or shortcut. */
export function matrixNodeId(index: number): string {
  return `N${String(index + 1).padStart(2, "0")}`;
}

/** At-rest action line. Names no room, so it can never read as a target. */
export const MATRIX_ROUTE_PROMPT = "▸ PRESS ↓ OR ↑ TO PICK A ROUTE";

/** ArrowDown presses that target `node`, mirroring the reducer's cycle over
 * `adjacent`: from rest the k-th neighbour takes k presses; with a target,
 * presses count on from it. */
function pressesTo(position: MatrixPosition, node: number): number {
  const adjacent = position.matrix.nodes[position.current]?.adjacent ?? [];
  const from =
    position.selected === null ? -1 : adjacent.indexOf(position.selected);
  const to = adjacent.indexOf(node);
  return from < 0 ? to + 1 : (to - from + adjacent.length) % adjacent.length;
}

/** `ROUTES (n): ↓1 N01  ↓2 N08` in two rows; entries wrap under the first
 * entry instead of clipping (the generator's frontier is at most 5). */
function routeRows(
  position: MatrixPosition,
  frontier: readonly number[],
  width: number,
): readonly [string, string] {
  const head = `ROUTES (${frontier.length}): `;
  const entries = frontier.map((i) =>
    i === position.selected
      ? `>${matrixNodeId(i)}`
      : `↓${pressesTo(position, i)} ${matrixNodeId(i)}`,
  );
  if (entries.length === 0) return [`${head}none`, ""];
  const rows = [head];
  for (const entry of entries) {
    const last = rows.length - 1;
    const row = rows[last] ?? "";
    const fresh = row.trim().length === 0 || row === head;
    if (fresh || row.length + 2 + entry.length <= width)
      rows[last] = fresh ? row + entry : `${row}  ${entry}`;
    else rows.push(" ".repeat(head.length) + entry);
  }
  return [rows[0] ?? head, rows.slice(1).join("  ")];
}

/** Card rows, each clipped to `width` columns. */
export function matrixCardLines(
  position: MatrixPosition,
  width: number,
): readonly MatrixLine[] {
  const { matrix, current, selected } = position;
  const frontier = frontierOf(position);
  const name = (node: MatrixNode, i: number): string =>
    `${CARD_GLYPHS[node.eventKind ?? "combat"]} ${matrixNodeId(i)} ${node.zone.toUpperCase()}${isBossNode(matrix, i) ? " (BOSS)" : ""} · ${nodeState(position, i)}`;
  const detail = (node: MatrixNode): string =>
    `  ${node.iceIds.length} ICE · ${node.reward.credits}cr · ${EVENT_LABELS[node.eventKind ?? "combat"]}`;
  const lines: MatrixLine[] = [];
  const add = (text: string, fg: string = PALETTE.GRAY_LIGHT): void => {
    lines.push({ text: text.slice(0, Math.max(0, width)), fg });
  };

  // First line = what to do next: the prompt at rest, the target once one is
  // chosen. The node it details sits directly under it (ADR-0249 affordance).
  const here = matrix.nodes[current];
  const atHere = here
    ? `@ ${name(here, current)}`
    : "@ No node here — ESC: back";
  const target =
    selected !== null && selected !== current
      ? matrix.nodes[selected]
      : undefined;
  const shown = target ?? here;
  if (target && selected !== null) {
    add(`> ${name(target, selected)}`, PALETTE.GREEN_NEON);
    // ADR-0281: the card already priced ONE node; the player's actual decision
    // is the route, so say what it costs from here to the end and what is left
    // on offer. This is the run's shape, before committing to it.
    add(
      routePreviewLine(
        routePreview(
          position.matrix,
          position.cleared,
          position.bypassed ?? [],
          selected,
        ),
      ),
      PALETTE.CYAN_LIGHT,
    );
  } else
    add(
      frontier.length > 0 ? MATRIX_ROUTE_PROMPT : "▸ NO ROUTES — ENTER: ICE",
      PALETTE.YELLOW_AMBER,
    );
  if (!target) add(atHere, PALETTE.GREEN_NEON);
  add(shown ? detail(shown) : "");
  add(shown?.site?.label ? `  ${shown.site.label}` : "");
  if (target) add(atHere, PALETTE.GREEN_NEON);
  for (const row of routeRows(position, frontier, width))
    add(row, PALETTE.CYAN_LIGHT);
  const boss = matrix.nodes[matrix.bossNode];
  if (boss) {
    const where =
      current === matrix.bossNode
        ? "HERE"
        : frontier.includes(matrix.bossNode)
          ? "REACHABLE NOW"
          : "NOT ADJACENT";
    add(
      `◆ OBJECTIVE: BOSS · ${nodeState(position, matrix.bossNode)}`,
      PALETTE.MAGENTA_LIGHT,
    );
    add(
      `  ${matrixNodeId(matrix.bossNode)} ${boss.zone.toUpperCase()} · ${where}`,
      PALETTE.MAGENTA_LIGHT,
    );
  } else {
    add("◆ No objective in this matrix", PALETTE.MAGENTA_LIGHT);
    add("");
  }
  return lines;
}
