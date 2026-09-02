/** Death & Restart Cycle (ADR-0040).
 *
 * Manages the flatline → death summary → restart options flow.
 * Ports Python engine/death.py + engine/jockey_history.py.
 */

/** Record of a jockey who flatlined. */
export interface DeceasedJockey {
  readonly jockeyId: string;
  readonly name: string;
  readonly characterId: string;
  readonly grade: number;
  readonly diedAtMission: string;
  readonly diedAtTimestamp: number;
  readonly inventorySnapshot: ReadonlyArray<string>;
  readonly missionsCompleted: number;
  readonly dataRecovered: number;
  readonly playtimeMinutes: number;
  readonly epitaph: string;
}

/** Epitaph pools — Gibson-toned epitaphs per character archetype. */
export const EPITAPHS: Readonly<Record<string, ReadonlyArray<string>>> = Object.freeze({
  novice: Object.freeze([
    "You died a wage slave.",
    "Sprawl is short on memory.",
    "Cash for the next, then.",
  ]),
  veteran: Object.freeze([
    "Old scores die hard.",
    "Mara's not waiting.",
    "T-A doesn't forget.",
  ]),
  heretic: Object.freeze([
    "The wheel keeps turning.",
    "Loa hears you still.",
    "One spoke, not the wheel.",
  ]),
});

/** Select a random epitaph for a character archetype. */
export function selectEpitaph(characterId: string, rng: () => number = Math.random): string {
  const pool = EPITAPHS[characterId] ?? EPITAPHS["novice"];
  if (!pool) return "The Sprawl remembers.";
  return pool[Math.floor(rng() * pool.length)] ?? "The Sprawl remembers.";
}

/** Create a DeceasedJockey record from current game state. */
export function createDeceasedJockey(params: {
  name: string;
  characterId: string;
  grade: number;
  missionId: string;
  inventory: ReadonlyArray<string>;
  missionsCompleted: number;
  dataRecovered: number;
  playtimeMinutes: number;
  rng?: () => number;
}): DeceasedJockey {
  return {
    jockeyId: `${params.characterId}_${Date.now()}`,
    name: params.name,
    characterId: params.characterId,
    grade: params.grade,
    diedAtMission: params.missionId,
    diedAtTimestamp: Date.now(),
    inventorySnapshot: Object.freeze([...params.inventory]),
    missionsCompleted: params.missionsCompleted,
    dataRecovered: params.dataRecovered,
    playtimeMinutes: params.playtimeMinutes,
    epitaph: selectEpitaph(params.characterId, params.rng),
  };
}

/** Death summary displayed after flatline. */
export interface DeathSummary {
  readonly jockey: DeceasedJockey;
  readonly totalRuns: number;
  readonly totalDeaths: number;
  readonly longestRunMinutes: number;
}

/** Generate a death summary from game state. */
export function generateDeathSummary(
  jockey: DeceasedJockey,
  totalRuns: number,
  totalDeaths: number,
  longestRunMinutes: number,
): DeathSummary {
  return { jockey, totalRuns, totalDeaths, longestRunMinutes };
}

/** Restart option chosen by the player after death summary. */
export type RestartChoice = "new_jockey" | "same_jockey" | "hall_of_dead" | "main_menu";
