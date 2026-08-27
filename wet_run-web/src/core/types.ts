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

/** Screen state — top-level UI surface (mirrors Python ScreenKind, wet_run-web subset).
 *
 * Tier 4 implements 6 of the 11 options: MENU + NEW_RUN (→ MISSION_SELECT) +
 * GRAPHIC_NOVEL (stub) + CONTINUE (stub) + SETTINGS (stub) + CREDITS (stub).
 * The remaining options (HALL_OF_DEAD, HELP, ENDINGS, STATS) are deferred
 * until Tier 5+ per the README "Out of scope" list.
 */
export type ScreenKind =
  | "menu" // Main menu (9 options, current screen on boot)
  | "mission_select" // NEW RUN → mission select (Tier 3 curated 30 missions)
  | "graphic_novel" // GRAPHIC NOVEL → auto-play (stub for Tier 4)
  | "saved_progress" // CONTINUE → load saved (stub for Tier 4)
  | "settings" // SETTINGS screen (stub)
  | "credits" // CREDITS screen (stub)
  | "help" // HELP screen (stub)
  | "hall_of_dead" // HALL OF DEAD (stub, deferred)
  | "endings" // ENDINGS browser (stub, deferred)
  | "stats" // STATS / Telemetry (stub, deferred);

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
  // === Tier 5 multi-stage run extensions ===
  readonly runPhase: RunPhase;
  readonly statusEffects: ReadonlyArray<StatusEffectInstance>;
  readonly iceRoster: ReadonlyArray<Ice>; // 1..N ICE in current combat (multi-enemy)
  readonly activeIceIndex: number;
  readonly currentNodeIndex: number;
  readonly matrix: Matrix | null;
  readonly visitedNodes: ReadonlyArray<number>;
  readonly bossPhase: BossPhase; // 0 = no boss active, 1..4 = boss phase
  readonly endingChoice: EndingChoice | null;
}

/** Top-level run cycle phase (Tier 5+). */
export type RunPhase = "matrix" | "combat" | "loot" | "ending" | "dead";

/** Status effect kinds (5 effects from ADR-0207). */
export type StatusEffectKind = "burn" | "stun" | "slow" | "silence" | "vulnerable";

/** Active status effect instance (Tier 5 state machine). */
export interface StatusEffectInstance {
  readonly kind: StatusEffectKind;
  readonly remaining: number;
  readonly magnitude: number;
  readonly target: "player" | "ice";
}

/** Zone depth — mirrored from Python matrix/node.py ZoneDepth. */
export type ZoneDepth = "surface" | "mid" | "deep" | "core" | "core-deep";

/** Matrix node (one encounter in a run). */
export interface MatrixNode {
  readonly id: number;
  readonly zone: ZoneDepth;
  readonly iceIds: ReadonlyArray<string>;
  readonly iceHp: ReadonlyArray<number>;
  readonly reward: { credits: number };
  readonly isBoss: boolean;
  readonly adjacent: ReadonlyArray<number>;
}

/** Generated matrix for one run. */
export interface Matrix {
  readonly nodes: ReadonlyArray<MatrixNode>;
  readonly startNode: number;
  readonly bossNode: number;
}

/** Boss phase 0..4 (0 = no boss active). */
export type BossPhase = 0 | 1 | 2 | 3 | 4;

/** Ending variant chosen at run completion (29 total in Python, 3 here for MVP). */
export type EndingChoice = "A" | "B" | "C";

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
