/** Selected-node detail card for the Matrix board (ADR-0249).
 *
 * The former node list is demoted to this card: it details the targeted
 * neighbour (or the current node when nothing is targeted), names the
 * destinations in arrow order and keeps the objective in words.
 */
import type { Matrix, MatrixNode } from "../core/types";
import { EVENT_GLYPHS, EVENT_LABELS } from "../core/event_matrix";
import { PALETTE } from "./palette";
import { frontierOf, isBossNode, nodeState } from "./matrix_board";

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

/** Event glyphs for the card. `◆` is reserved for the boss on this screen
 * (ADR-0249 rule 7), so a cache shows `¤` here instead. */
const CARD_GLYPHS = { ...EVENT_GLYPHS, cache: "¤" } as const;

/** Rows the card always occupies, so the board never shifts between nodes. */
export const CARD_ROWS = 8;

/** Stable node identity, deliberately not an ordinal row number or shortcut. */
export function matrixNodeId(index: number): string {
  return `N${String(index + 1).padStart(2, "0")}`;
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

  const here = matrix.nodes[current];
  add(
    here ? `@ ${name(here, current)}` : "@ No node here — ESC: back",
    PALETTE.GREEN_NEON,
  );
  const target =
    selected !== null && selected !== current
      ? matrix.nodes[selected]
      : undefined;
  const shown = target ?? here;
  if (target && selected !== null)
    add(`> ${name(target, selected)}`, PALETTE.GREEN_NEON);
  else
    add(
      frontier.length > 0
        ? "> no target — ↑↓ choose a route"
        : "> no routes — ENTER: ICE",
      PALETTE.CYAN_LIGHT,
    );
  add(shown ? detail(shown) : "");
  add(shown?.site?.label ? `  ${shown.site.label}` : "");
  const ids = frontier
    .map((i) => `${i === selected ? ">" : ""}${matrixNodeId(i)}`)
    .join(" ");
  add(`ROUTES (${frontier.length}): ${ids || "none"}`, PALETTE.CYAN_LIGHT);
  add("");
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
