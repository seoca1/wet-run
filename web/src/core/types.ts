import type { EquipmentLoadout } from "./state/equipment";

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
  readonly [x: number]: ReadonlyArray<Cell> | undefined;
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
  readonly grade?: number; // Current mission grade (1-5) for procedural generation
  readonly seed?: number; // RNG seed for deterministic dungeon generation
  readonly source_universe?: "sprawl" | "far-grid"; // Universe tag (ADR-0213); absent means "sprawl"
  readonly story?: {
    readonly source: string; // Fiction stem, display-only (ADR-0213)
    readonly title?: string;
  };
  readonly briefing?: string; // Far Grid mission briefing (ADR-0213 Wave 2); English, display-only
  readonly title_ko?: string; // Korean translation of `title` (Tier 4 follow-up KO content); display-only
  readonly briefing_ko?: string; // Korean translation of `briefing` (Tier 4 follow-up KO content); display-only
  runPhase?: "matrix" | "approach" | "combat" | "loot" | "ending" | "dead"; // Current phase for dungeon mode
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
  /**
   * What the program actually does in the web tier.
   *
   * ADR-0251 rule 5: the text must state what the screen does. The web
   * reducer gives every program the same damage path (`tier * 5`), so the
   * catalog's design intent lives in `plannedDescription` instead — the
   * per-program shield / buff / decoy effects are not wired yet.
   */
  readonly description: string;
  /** The designed effect, not yet implemented in the web tier. */
  readonly plannedDescription?: string;
  readonly aoe: boolean;
}

/** ICE (enemy) — subset of wet_run IceType schema. */
export interface Ice {
  readonly id: string;
  readonly name: string;
  readonly hp: number;
  readonly maxHp?: number;
  readonly armor: number;
  readonly tier: number;
  readonly hpBase?: number;
  readonly hpPerGrade?: number;
  readonly personality?: "aggressive" | "defensive" | "stealth" | "support";
  readonly aggression?: "passive" | "standard" | "aggressive" | "boss";
  readonly skills?: ReadonlyArray<{
    id: string;
    name: string;
    effect: string;
    cooldownMs: number;
    damage: number;
    /** Effect magnitude (ADR-0219 Option A) — see `IceSkillDef.magnitude`. */
    magnitude?: number;
  }>;
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
 * Tier 5.5: adds TUTORIAL for first-run onboarding.
 */
export type ScreenKind =
  | "menu" // Main menu (9 options, current screen on boot)
  | "mission_select" // NEW RUN → mission select (Tier 3 curated 30 missions)
  | "briefing" // Mission briefing (Finn's office) — NEW
  | "travel" // Travel to jack-in point animation — NEW
  | "bypass_security" // Bypass corporate security — NEW
  | "graphic_novel" // GRAPHIC NOVEL → auto-play (stub for Tier 4)
  | "saved_progress" // CONTINUE → load saved (stub for Tier 4)
  | "settings" // SETTINGS screen (stub)
  | "credits" // CREDITS screen (stub)
  | "help" // HELP screen (stub)
  | "hall_of_dead" // HALL OF DEAD (stub, deferred)
  | "death_summary" // DEATH SUMMARY — jockey report after flatline
  | "hall_of_dead_list" // HALL OF DEAD — deceased jockey archive (populated)
  | "endings" // ENDINGS browser (stub, deferred)
  | "stats" // STATS / Telemetry (stub, deferred)
  | "tutorial" // Tutorial overlay (Tier 5.5+ first-run onboarding)
  | "crafting" // CRAFT — recipe/material consumption screen
  | "equipment" // EQUIPMENT — equip/unequip gear screen
  | "pause" // PAUSED screen
  | "bypass_security" // Bypass corporate security — NEW
  | "black_market" // BLACK MARKET — hub vendor
  | "ghost_encounter" // GHOST ENCOUNTER — Loa event
  | "death_restart" // DEATH RESTART — flatline recovery
  | "failed" // FAILED — flatline terminal state
  | "meet_npc" // MEET NPC — construct dialogue
  | "extract_data" // EXTRACT DATA — data extraction
  | "dungeon" // NetHack-style dungeon crawler mode
  | "far_grid_hub" // FAR GRID hub (ADR-0213)
  | "dungeon_debug"; // DEBUG: dungeon graph visualization

/** Graphic novel live state (Tier 5+).
 *
 * Lives on GameState so the screen manager, renderer, and tick loop share a
 * single source of truth. `null` whenever the player isn't in a GN screen.
 */
export interface GraphicNovelState {
  readonly player: import("./graphic_novel/graphic_novel.ts").GraphicNovelPlayer;
  readonly currentScene:
    import("./graphic_novel/graphic_novel.ts").SceneData | null;
  readonly currentText: string;
  readonly isPaused: boolean;
}

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
  /** Recent combat log lines, NEWEST first (index 0 = newest), capped at
   * `COMBAT_LOG_CAP`. `message` is the most recent line, i.e. `combatLog[0]`
   * whenever the log is non-empty. Display-only — not persisted in
   * `SaveSlot` (no schema bump). */
  readonly combatLog: ReadonlyArray<string>;
  readonly turnCount: number;
  /** Active graphic novel session, or null when not on the GN screen. */
  readonly graphicNovel: GraphicNovelState | null;
  // === Tier 5 multi-stage run extensions ===
  readonly runPhase: RunPhase;
  readonly statusEffects: ReadonlyArray<StatusEffectInstance>;
  readonly iceRoster: ReadonlyArray<Ice>; // 1..N ICE in current combat (multi-enemy)
  readonly activeIceIndex: number;
  readonly currentNodeIndex: number;
  /** Transient route highlight; omitted by old states/saves, never auto-selected. */
  readonly selectedMatrixNodeIndex?: number | null;
  /** Transient encounter menu/intel; omitted from saves, reset on travel. */
  readonly encounterDecision?: {
    readonly selectedVerb:
      import("./state/encounter_verbs").EncounterVerb | null;
    readonly probed: boolean;
  } | null;
  readonly matrix: Matrix | null;
  readonly visitedNodes: ReadonlyArray<number>;
  /** Resolved encounters, not visits: travel visits a node before combat.
   * Optional for legacy states/saves; missing means no recorded clears. */
  readonly clearedEncounterNodes?: ReadonlyArray<number>;
  /** Nodes passed by paid BYPASS this run (ADR-0250): resolved for travel, but
   * never cleared, rewarded or healed. Optional; missing means none. */
  readonly bypassedEncounterNodes?: ReadonlyArray<number>;
  readonly bossPhase: BossPhase; // 0 = no boss active, 1..4 = boss phase
  readonly endingChoice: EndingChoice | null;
  // Tier 5.5: active combat VFX (animation overlay).
  readonly vfxInstances: ReadonlyArray<
    import("../renderer/combat_vfx.ts").CombatVfxInstance
  >;
  // Combat engine state (Python parity damage system)
  readonly playerCombo: number;
  readonly comboLastHitMs: number;
  readonly alarmLevel: number;
  readonly lastAlarmTickMs: number;
  readonly counterWindowOpenMs: number;
  readonly lastEnemyAttackMs: number;
  /** Unused legacy timestamp (ADR-0244); retained for state compatibility. */
  readonly dixieLastAttackMs: number;
  /** Successful player program plays since Dixie fired; starts ready at N-1. */
  readonly dixiePlayerTurnsSinceAttack: number;
  readonly skillCooldowns: Readonly<Record<string, number>>;
  // Tier 8: crafting + equipment — driven by the inventory/loadout systems.
  readonly inventory: Inventory;
  readonly equipmentLoadout: EquipmentLoadout;
  // Tier 9: run mutators — optional modifiers applied at run start.
  readonly activeMutators: ReadonlyArray<
    import("./state/run_mutators.ts").RunMutator
  >;
  // Achievement tracking (string IDs of unlocked achievements)
  readonly unlockedAchievements: ReadonlyArray<string>;
  readonly achievementCredits: number;
  // Death cycle (ADR-0040)
  readonly deceasedJockeys: ReadonlyArray<
    import("./state/death_cycle.ts").DeceasedJockey
  >;
  readonly lastDeathSummary:
    import("./state/death_cycle.ts").DeathSummary | null;
  readonly totalRuns: number;
  readonly totalDeaths: number;
  readonly longestRunMinutes: number;
  // Faction reputation (Phase 2-2)
  readonly factionScores: import("./state/faction_reputation.ts").FactionScores;
}

/** Top-level run cycle phase (Tier 5+). */
export type RunPhase = "matrix" | "combat" | "loot" | "ending" | "dead";

/** Status effect kinds (13 effects: 5 from ADR-0207 + 4 from Python + 4 new).
 *
 * From Python combat system:
 * - stagger: Skips target's next auto-attack (duration: 1500ms = one attack window)
 * - regen: Heals target healPerTick HP each tick
 * - powered: Buffs attacker's attack by attackBonus (positive)
 * - weakened: Debuffs target's attack by attackBonus (negative)
 *
 * New effects (migration plan):
 * - bleed: DoT that increases damage taken (burn + vulnerability combo)
 * - fatigue: Reduces AP regen speed
 * - confused: 50% chance to attack self/allies
 * - terrified: Reduces attack damage
 *
 * ADR-0219 Option A adds one member:
 * - shield: an absorbing damage pool on an ICE. `magnitude` holds the
 *   remaining HP the pool can still absorb; `remaining` holds its lifetime
 *   in enemy ticks. Applied only by ICE skills (never by the player side).
 */
export type StatusEffectKind =
  | "burn"
  | "stun"
  | "slow"
  | "silence"
  | "vulnerable"
  | "stagger"
  | "regen"
  | "powered"
  | "weakened"
  | "bleed"
  | "fatigue"
  | "confused"
  | "terrified"
  | "shield"
  /** Player-only: incoming damage is reduced by `magnitude` percent. */
  | "evasive";

/** Active status effect instance (Tier 5 state machine).
 *
 * Optional fields support effect-specific parameters (all from Python combat system):
 * - dotDamage: extra damage per tick for bleed
 * - healPerTick: HP restored per tick for regen
 * - attackBonus: attack modifier for powered (+) / weakened (-)
 * - defenseBonus: defense modifier (future use)
 * - slowPct: percentage slow for slow effect
 * - vulnerabilityPct: extra damage % for vulnerable
 * - apRegenReduction: AP regen penalty for fatigue
 *
 * ADR-0219 Option A adds two optional fields so the ICE-side effect state
 * can live on the existing `statusEffects` array instead of a parallel
 * collection on `GameState`:
 * - iceIndex: which roster slot the effect is attached to. Required for
 *   ICE-cast effects because a roster can hold several ICE — including two
 *   with the same catalog id — and `target: "ice"` alone means "the active
 *   ICE" for the player-side effects (burn / slow) that already use it.
 * - tickSource: which side's turn advances this effect's timer. Defaults to
 *   `"player"` (the historical behavior — every effect ticked with the
 *   player program). ICE-cast effects set `"enemy"` so their lifetime is
 *   measured in enemy turns (one enemy turn = one `AUTO_ATTACK_INTERVAL_MS`
 *   window) and is not shortened by the player-side tick.
 */
export interface StatusEffectInstance {
  readonly kind: StatusEffectKind;
  readonly remaining: number;
  readonly magnitude: number;
  readonly target: "player" | "ice";
  readonly dotDamage?: number;
  readonly healPerTick?: number;
  readonly attackBonus?: number;
  readonly defenseBonus?: number;
  readonly slowPct?: number;
  readonly vulnerabilityPct?: number;
  readonly apRegenReduction?: number;
  /** Owning roster slot index (ADR-0219 Option A). */
  readonly iceIndex?: number;
  /** Which side's turn advances `remaining` (ADR-0219 Option A). */
  readonly tickSource?: "player" | "enemy";
}

/** Zone depth — mirrored from Python matrix/node.py ZoneDepth. */
export type ZoneDepth = "surface" | "mid" | "deep" | "core" | "core-deep";

/** Presentation-only room geometry kept from the dungeon generator (ADR-0249).
 *
 * Units are generator cells, not screen cells. Gameplay never reads it: the
 * Matrix board scales it to draw rooms where they were generated.
 */
export interface MatrixSite {
  readonly x: number;
  readonly y: number;
  readonly w: number;
  readonly h: number;
  readonly label: string;
}

/** Matrix node (one encounter in a run). */
export interface MatrixNode {
  readonly id: number;
  readonly zone: ZoneDepth;
  readonly iceIds: ReadonlyArray<string>;
  readonly iceHp: ReadonlyArray<number>;
  readonly reward: { credits: number };
  readonly isBoss: boolean;
  readonly adjacent: ReadonlyArray<number>;
  /** Generated room geometry; absent on hand-built matrices and older data,
   * which the board lays out deterministically instead (ADR-0249). */
  readonly site?: MatrixSite;
  // Tier 5.5: event kind (default "combat" for backward compat).
  readonly eventKind?:
    "combat" | "discovery" | "trap" | "cache" | "rest" | "merchant";
  readonly eventData?: {
    readonly damage?: number;
    readonly creditsBonus?: number;
    readonly programId?: string;
    readonly healPct?: number;
    readonly forSale?: ReadonlyArray<string>;
  } | null;
}

/** Generated matrix for one run. */
export interface Matrix {
  readonly nodes: ReadonlyArray<MatrixNode>;
  readonly startNode: number;
  readonly bossNode: number;
  readonly grade?: number;
}

/** Boss phase 0..4 (0 = no boss active). */
export type BossPhase = 0 | 1 | 2 | 3 | 4;

/** Ending variant (29 total across 5 arcs). */
export type EndingChoice =
  | "arc1_wage_slave"
  | "arc1_first_blood"
  | "arc1_cowboy_up"
  | "arc1_cheap_death"
  | "arc1_data_miner"
  | "arc1_ice_breaker"
  | "arc1_flatlined"
  | "arc2_ghost_dancer"
  | "arc2_corporate_tool"
  | "arc2_silent_runner"
  | "arc2_data_thief"
  | "arc2_construct_friend"
  | "arc2_flatlined_deep"
  | "arc3_wintermute_agent"
  | "arc3_ta_insider"
  | "arc3_neutrality"
  | "arc3_double_agent"
  | "arc3_zealot"
  | "arc3_sacrifice_play"
  | "arc4_liberation_front"
  | "arc4_new_order"
  | "arc4_digital_exile"
  | "arc4_corporate_victory"
  | "arc4_ai_merger"
  | "arc5_neuromancer"
  | "arc5_sprawl_free"
  | "arc5_last_jockey"
  | "arc5_sprawl_slave"
  | "arc5_unknown";

/** Player inventory — credits, materials, and crafted/purchased programs. */
export interface Inventory {
  readonly credits: number;
  readonly materials: Readonly<Record<string, number>>;
  readonly programs: ReadonlyArray<Program>;
}

/** Re-export of the equipment loadout type alias (defined in equipment.ts). */
export type { EquipmentLoadout } from "./state/equipment";

/** Re-export dialogue system types (defined in dialogue.ts). */
export type {
  DialogueNode,
  DialogueChoice,
  DialogueEffect,
  DialogueCondition,
  DialogueTree,
  DialogueState,
  DialogueContext,
} from "./dialogue";

/** Re-export i18n types (defined in i18n.ts). */
export type { Language } from "./i18n";

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
  readonly graphicNovelProgress?: {
    readonly chainId: string;
    readonly sceneIndex: number;
    readonly dialogueIndex: number;
  } | null;
  /** Index of the matrix node the player stood on when the run was saved.
   *
   * Optional for backward compatibility: saves written before this field
   * existed omit it, and the restore path falls back to the matrix entry
   * node (`matrix.startNode`). When present it MUST be a finite number.
   */
  readonly currentNodeIndex?: number;
  /** Persist encounter clears without invalidating older version-1 slots. */
  readonly clearedEncounterNodes?: ReadonlyArray<number>;
  /** ADR-0250 run memory of BYPASS; older version-1 slots omit it. */
  readonly bypassedEncounterNodes?: ReadonlyArray<number>;
}

/** Game action — keyboard input → state mutation. */
export type GameAction =
  | { readonly type: "idle_tick"; readonly idleSinceMs: number }
  | { readonly type: "move_north" }
  | { readonly type: "move_south" }
  | { readonly type: "move_east" }
  | { readonly type: "move_west" }
  | { readonly type: "use_program"; readonly programId: string }
  | { readonly type: "select_program"; readonly handIndex: number }
  | { readonly type: "confirm" }
  | { readonly type: "cancel" }
  | { readonly type: "jack_out" }
  | { readonly type: "cycle_target" }
  | { readonly type: "trigger_death" }
  | {
      readonly type: "select_restart";
      readonly choice: import("./state/death_cycle.ts").RestartChoice;
    }
  | { readonly type: "view_hall_of_dead" };

/** Input mapping — keyboard event → game action.
 *
 * Per ADR-0197 gamepad mapping parity (commitment: same semantics across
 * desktop keyboard, desktop gamepad, and (Tier 2) web browser).
 *
 * Standard conventions:
 *   - Enter/Space: confirm/advance
 *   - ESC/q: jack out (exit current run)
 *   - Arrow keys: navigate
 *   - 1-9: select menu item or use program in combat
 */
export const KEYBOARD_MAPPING: Readonly<Record<string, GameAction>> =
  Object.freeze({
    ArrowUp: { type: "move_north" },
    ArrowDown: { type: "move_south" },
    ArrowLeft: { type: "move_west" },
    ArrowRight: { type: "move_east" },
    Enter: { type: "confirm" },
    " ": { type: "confirm" },
    Escape: { type: "jack_out" },
    q: { type: "jack_out" },
    Tab: { type: "cycle_target" },
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

/** Type alias for GameState — convenience for renderers. */
export type State = GameState;
