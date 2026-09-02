/** Graphic novel — scene loading.
 *
 * Mirrors wet_run/prototype/src/wet_run/engine/graphic_novel_loaders.py:
 *   - listScenesForCharacter
 *   - loadSceneChain
 *   - loadPrologueChain
 *
 * Determinism: seeded shuffles use Mulberry32 so reloading the same scene
 * catalog with the same seed always produces the same order.
 */

import scenesJson from "../data/scenes.json" with { type: "json" };
import type { CharacterId, Ending, SceneData, ScenesFile } from "./graphic_novel_types.ts";

const SCENES: ScenesFile = scenesJson as unknown as ScenesFile;

/** Map character id → data/scenes subdirectory name. */
export const CHAR_TO_DIR: Readonly<Record<string, string>> = Object.freeze({
  novice: "case",
  veteran: "sil",
  heretic: "kas",
  suit: "suit",
  wigan: "wigan",
  angie: "angie",
  sally: "sally",
  "3jane": "3jane",
  neuromancer: "neuromancer",
});

/** Return all scenes for a character, sorted by order asc. */
export function listScenesForCharacter(
  character: CharacterId,
  scenes: Readonly<Record<string, SceneData>> = SCENES.scenes,
): ReadonlyArray<SceneData> {
  const filtered = Object.values(scenes).filter((s) => s.character === character);
  return Object.freeze([...filtered].sort((a, b) => a.order - b.order));
}

/** Load a chain of scenes for a character, optionally filtered + shuffled. */
export function loadSceneChain(
  character: CharacterId,
  options: {
    readonly shuffle?: boolean;
    readonly seed?: number;
    readonly ending?: Ending;
    readonly maxOrder?: number;
    readonly scenes?: Readonly<Record<string, SceneData>>;
  } = {},
): ReadonlyArray<SceneData> {
  const scenes = options.scenes ?? SCENES.scenes;
  const ending: Ending = options.ending ?? "A";
  const maxOrder = options.maxOrder ?? Number.MAX_SAFE_INTEGER;
  let chain = listScenesForCharacter(character, scenes).filter(
    (s) => s.ending === ending && s.order <= maxOrder,
  );
  if (options.shuffle === true) {
    chain = seededShuffle(chain, options.seed);
  }
  return Object.freeze([...chain]);
}

/** Load prologue — characters × scenes, character order shuffled. */
export function loadPrologueChain(options: {
  readonly seed?: number;
  readonly ending?: Ending;
  readonly maxOrder?: number;
  readonly scenes?: Readonly<Record<string, SceneData>>;
  readonly characters?: ReadonlyArray<CharacterId>;
} = {}): ReadonlyArray<SceneData> {
  const characters = options.characters ?? (Object.keys(CHAR_TO_DIR) as CharacterId[]);
  const shuffled = seededShuffle(characters, options.seed);
  const out: SceneData[] = [];
  for (const ch of shuffled) {
    out.push(
      ...loadSceneChain(ch, {
        ending: options.ending,
        maxOrder: options.maxOrder,
        scenes: options.scenes,
      }),
    );
  }
  return Object.freeze(out);
}

/** Fisher–Yates shuffle with optional deterministic seeding. */
function seededShuffle<T>(items: ReadonlyArray<T>, seed?: number): T[] {
  const arr = [...items];
  const rng = makeRng(seed);
  for (let i = arr.length - 1; i > 0; i--) {
    const j = rng(0, i + 1);
    const a = arr[i] as T;
    const b = arr[j] as T;
    arr[i] = b;
    arr[j] = a;
  }
  return arr;
}

/** Mulberry32 PRNG seeded by number; falls back to Math.random when seed is undefined. */
function makeRng(seed?: number): (min: number, maxExclusive: number) => number {
  if (seed === undefined) return (min, max) => Math.floor(Math.random() * (max - min)) + min;
  let s = seed >>> 0;
  return (min, max) => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    const r = ((t ^ (t >>> 14)) >>> 0) / 0x100000000;
    return Math.floor(r * (max - min)) + min;
  };
}

/** Sound id → logical sound key map. Mirrors graphic_novel_audio.SCENE_SOUND_MAP. */
export const SCENE_SOUND_MAP: Readonly<Record<string, string>> = Object.freeze({
  // Theme ambient
  chiba_rain_loop: "theme/chiba",
  matrix_rain: "theme/matrix_rain",
  finn_office: "theme/finn_office",
  loa_drum: "theme/loa_drum",
  loa_drum_fade: "theme/loa_drum_fade",
  loa_channel: "theme/loa_channel",
  manarase_drone: "theme/manarase_drone",
  industrial: "theme/industrial",
  broadcast: "theme/broadcast",
  hammer_alert: "theme/hammer_alert",
  shibuya_traffic: "theme/sense_net",
  // ADR-0049 prefixed aliases
  theme_broadcast: "theme/broadcast",
  theme_hammer_alert: "theme/hammer_alert",
  theme_industrial: "theme/industrial",
  theme_loa_drum: "theme/loa_drum",
  theme_loa_drum_fade: "theme/loa_drum_fade",
  theme_manarase_drone: "theme/manarase_drone",
  movement_neon_hum: "movement/neon_hum",
  // Atmospheric SFX
  neon_hum: "movement/neon_hum",
  hvac_hum: "movement/neon_hum",
  // Jack-in/out
  jack_in_zap: "movement/jack_in_zap",
  jack_out_buzz: "movement/jack_out_buzz",
  // Data extraction
  data_extract: "movement/data_extract",
  // ICE / boss
  black_ice_roar: "movement/black_ice_roar",
  // Broadcast
  broadcast_static: "movement/broadcast_static",
  broadcast_out: "movement/broadcast_out",
});

/** Map a scene sound id to a resolved key, or null if unmapped. */
export function resolveSound(sceneSound: string | null | undefined): string | null {
  if (sceneSound == null) return null;
  const mapped = SCENE_SOUND_MAP[sceneSound];
  if (mapped !== undefined) return mapped;
  if (sceneSound.includes("/")) return sceneSound;
  return null;
}

/** Pull out the category prefix ("theme", "movement", ...) from a resolved key. */
export function soundCategory(resolved: string | null): string | null {
  if (resolved == null) return null;
  const slash = resolved.indexOf("/");
  return slash > 0 ? resolved.slice(0, slash) : null;
}