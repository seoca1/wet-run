/** Shared type definitions for wetrun-web MVP.
 *
 * Ports the core game state model from wet_run/prototype/src/wet_run.
 * Goal: keep types minimal for MVP — only what 1 playable mission needs.
 */

/** 2D grid coordinates. */
export interface Position {
  readonly x: number;
  readonly y: number;
}

/** ASCII cell — single character + foreground/background colors. */
export interface Cell {
  readonly char: string;
  readonly fg: string; // hex color, e.g. "#00ff41"
  readonly bg: string; // hex color, e.g. "#000000"
}

/** Grid is immutable per render frame — replaced by next-tick grid. */
export interface Grid {
  readonly width: number;
  readonly height: number;
  readonly cells: ReadonlyArray<ReadonlyArray<Cell>>;
  get(x: number, y: number): Cell | null;
}

/** Mission metadata (subset of wet_run Mission schema). */
export interface Mission {
  readonly id: string;
  readonly title: string;
  readonly fixer: string;
  readonly arc: number;
  readonly zone: string;
  readonly grade_min: number;
  readonly grade_max: number;
  readonly rewards: MissionRewards;
}

export interface MissionRewards {
  readonly credits: number;
  readonly materials: Readonly<Record<string, number>>;
}

/** Program (deck card) — subset of wet_run Program schema. */
export interface Program {
  readonly id: string;
  readonly name: string;
  readonly tier: number;
  readonly cost: number; // alarm cost
  readonly effect: string; // free-form effect identifier
  readonly description: string;
}

/** ICE (enemy) — subset of wet_run IceType schema. */
export interface Ice {
  readonly id: string;
  readonly name: string;
  readonly hp: number;
  readonly armor: number;
  readonly tier: number;
}

/** Player stats — ports wet_run AppState.player_loadout + combat state. */
export interface PlayerStats {
  readonly hp: number;
  readonly maxHp: number;
  readonly alarm: number; // 0-100
  readonly credits: number;
  readonly handSize: number; // cards in hand
}

/** Game phase state machine — drives renderer + input mapping. */
export type GamePhase =
  | "menu" // Title screen, mission select
  | "approach" // In matrix, ICE ahead
  | "combat" // Active ICE fight
  | "victory" // ICE defeated
  | "defeat" // Player defeated
  | "exit"; // Jacked out

/** Top-level game state — referenced by all subsystems. */
export interface GameState {
  readonly phase: GamePhase;
  readonly mission: Mission;
  readonly player: PlayerStats;
  readonly ice: Ice;
  readonly deck: ReadonlyArray<Program>; // hand
  readonly drawPile: ReadonlyArray<Program>;
  readonly discardPile: ReadonlyArray<Program>;
  readonly grid: Grid;
  readonly message: string; // Last status message (HUD)
  readonly turnCount: number;
}

/** Save slot — JSON-serializable subset of GameState. */
export interface SaveSlot {
  readonly version: number; // schema version, bump on breaking changes
  readonly missionId: string;
  readonly playerHp: number;
  readonly playerMaxHp: number;
  readonly playerAlarm: number;
  readonly playerCredits: number;
  readonly turnCount: number;
  readonly deckIds: ReadonlyArray<string>;
  readonly discardIds: ReadonlyArray<string>;
  readonly drawIds: ReadonlyArray<string>;
  readonly savedAt: string; // ISO timestamp
}

/** Game action — keyboard input → state mutation. */
export type GameAction =
  | { readonly type: "move_north" }
  | { readonly type: "move_south" }
  | { readonly type: "move_east" }
  | { readonly type: "move_west" }
  | { readonly type: "use_program"; readonly programId: string }
  | { readonly type: "select_program"; readonly handIndex: number }
  | { readonly type: "confirm" }
  | { readonly type: "cancel" }
  | { readonly type: "jack_out" };

/** Input mapping — keyboard event → game action.
 *
 * Per ADR-0197 gamepad mapping parity (commitment: same semantics across
 * desktop keyboard, desktop gamepad, and (Tier 2) web browser).
 *
 * Number keys 1-9 emit a select_program action with the 1-based hand index.
 * main.ts resolves programId from the current hand (where state is known).
 */
export const KEYBOARD_MAPPING: Readonly<Record<string, GameAction>> = Object.freeze({
  ArrowUp: { type: "move_north" },
  ArrowDown: { type: "move_south" },
  ArrowLeft: { type: "move_west" },
  ArrowRight: { type: "move_east" },
  Enter: { type: "confirm" },
  " ": { type: "confirm" },
  Escape: { type: "cancel" },
  q: { type: "jack_out" },
  "1": { type: "select_program", handIndex: 1 },
  "2": { type: "select_program", handIndex: 2 },
  "3": { type: "select_program", handIndex: 3 },
  "4": { type: "select_program", handIndex: 4 },
  "5": { type: "select_program", handIndex: 5 },
  "6": { type: "select_program", handIndex: 6 },
  "7": { type: "select_program", handIndex: 7 },
  "8": { type: "select_program", handIndex: 8 },
  "9": { type: "select_program", handIndex: 9 },
});
