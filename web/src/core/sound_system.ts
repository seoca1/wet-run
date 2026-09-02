/** Expanded Sound System — 12+ BGM tracks with situation-based transitions.
 *
 * Ports Python's full soundtrack: menu, combat, boss, shop, ending,
 * exploration, and special event tracks. Auto-transitions based on
 * game state changes.
 */

export type BgmTrackId =
  | "title"
  | "menu"
  | "exploration"
  | "combat_normal"
  | "combat_boss"
  | "combat_multi"
  | "shop"
  | "ending_good"
  | "ending_bad"
  | "ending_neutral"
  | "death"
  | "victory"
  | "event_special"
  | "ambient_low"
  | "ambient_high";

export type SfxId =
  | "click"
  | "confirm"
  | "back"
  | "equip"
  | "heal"
  | "damage"
  | "attack"
  | "ice_break"
  | "loot_drop"
  | "credit_gain"
  | "credit_spend"
  | "death"
  | "victory"
  | "boss_intro"
  | "phase_change";

export interface TrackInfo {
  readonly id: BgmTrackId;
  readonly volume: number;
  readonly fadeIn: number;
  readonly fadeOut: number;
  readonly loop: boolean;
}

export const TRACKS: Readonly<Record<BgmTrackId, TrackInfo>> = Object.freeze({
  title: { id: "title", volume: 0.7, fadeIn: 1000, fadeOut: 500, loop: true },
  menu: { id: "menu", volume: 0.5, fadeIn: 500, fadeOut: 300, loop: true },
  exploration: { id: "exploration", volume: 0.6, fadeIn: 800, fadeOut: 500, loop: true },
  combat_normal: { id: "combat_normal", volume: 0.8, fadeIn: 200, fadeOut: 200, loop: true },
  combat_boss: { id: "combat_boss", volume: 0.9, fadeIn: 100, fadeOut: 300, loop: true },
  combat_multi: { id: "combat_multi", volume: 0.85, fadeIn: 150, fadeOut: 200, loop: true },
  shop: { id: "shop", volume: 0.5, fadeIn: 600, fadeOut: 400, loop: true },
  ending_good: { id: "ending_good", volume: 0.8, fadeIn: 500, fadeOut: 1000, loop: false },
  ending_bad: { id: "ending_bad", volume: 0.7, fadeIn: 500, fadeOut: 1500, loop: false },
  ending_neutral: { id: "ending_neutral", volume: 0.6, fadeIn: 500, fadeOut: 800, loop: false },
  death: { id: "death", volume: 0.7, fadeIn: 100, fadeOut: 2000, loop: false },
  victory: { id: "victory", volume: 0.8, fadeIn: 100, fadeOut: 1500, loop: false },
  event_special: { id: "event_special", volume: 0.6, fadeIn: 800, fadeOut: 500, loop: false },
  ambient_low: { id: "ambient_low", volume: 0.3, fadeIn: 1500, fadeOut: 1000, loop: true },
  ambient_high: { id: "ambient_high", volume: 0.4, fadeIn: 1000, fadeOut: 800, loop: true },
});

export interface TransitionRule {
  readonly event: string;
  readonly track: BgmTrackId;
  readonly priority: number;
}

export const TRANSITION_RULES: ReadonlyArray<TransitionRule> = Object.freeze([
  Object.freeze({ event: "game_start", track: "title", priority: 10 }),
  Object.freeze({ event: "character_select", track: "menu", priority: 10 }),
  Object.freeze({ event: "exploration_start", track: "exploration", priority: 10 }),
  Object.freeze({ event: "combat_start", track: "combat_normal", priority: 15 }),
  Object.freeze({ event: "boss_encounter", track: "combat_boss", priority: 20 }),
  Object.freeze({ event: "multi_enemy_encounter", track: "combat_multi", priority: 18 }),
  Object.freeze({ event: "shop_open", track: "shop", priority: 12 }),
  Object.freeze({ event: "player_death", track: "death", priority: 25 }),
  Object.freeze({ event: "combat_victory", track: "victory", priority: 15 }),
  Object.freeze({ event: "special_event", track: "event_special", priority: 14 }),
  Object.freeze({ event: "safe_zone", track: "ambient_low", priority: 8 }),
  Object.freeze({ event: "danger_zone", track: "ambient_high", priority: 8 }),
  Object.freeze({ event: "ending_good", track: "ending_good", priority: 30 }),
  Object.freeze({ event: "ending_bad", track: "ending_bad", priority: 30 }),
  Object.freeze({ event: "ending_neutral", track: "ending_neutral", priority: 30 }),
]);

export interface SoundState {
  readonly currentTrack: BgmTrackId | null;
  readonly volume: number;
  readonly muted: boolean;
  readonly queue: BgmTrackId | null;
}

export const DEFAULT_SOUND_STATE: SoundState = Object.freeze({
  currentTrack: null,
  volume: 1.0,
  muted: false,
  queue: null,
});

export function getTrackForEvent(event: string): BgmTrackId | null {
  const matching = TRANSITION_RULES
    .filter((r) => r.event === event)
    .sort((a, b) => b.priority - a.priority);
  return matching[0]?.track ?? null;
}

export function shouldTransition(
  currentTrack: BgmTrackId | null,
  newEvent: string,
): { readonly track: BgmTrackId; readonly immediate: boolean } | null {
  const target = getTrackForEvent(newEvent);
  if (!target) return null;
  if (currentTrack === target) return null;
  const targetInfo = TRACKS[target];
  const immediate = targetInfo.fadeOut <= 300;
  return { track: target, immediate };
}

export function calculateVolume(trackId: BgmTrackId, masterVolume: number): number {
  const track = TRACKS[trackId];
  if (!track) return 0;
  return Math.max(0, Math.min(1, track.volume * masterVolume));
}

export function getAllSfxIds(): ReadonlyArray<SfxId> {
  return Object.freeze([
    "click",
    "confirm",
    "back",
    "equip",
    "heal",
    "damage",
    "attack",
    "ice_break",
    "loot_drop",
    "credit_gain",
    "credit_spend",
    "death",
    "victory",
    "boss_intro",
    "phase_change",
  ]);
}

export function getAllBgmTrackIds(): ReadonlyArray<BgmTrackId> {
  return Object.freeze(Object.keys(TRACKS) as BgmTrackId[]);
}

export function getTrackInfo(trackId: BgmTrackId): TrackInfo | undefined {
  return TRACKS[trackId];
}
