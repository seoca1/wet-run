/** Faction Reputation System.
 *
 * Tracks player standing with 4 factions. Scores change based on
 * mission completion and ICE kills. Connected to Info Market pricing.
 */

export type FactionId = "hosaka" | "maas" | "sense_net" | "ta";

export type ReputationTier =
  | "ALLIED"
  | "FRIENDLY"
  | "TRUSTED"
  | "NEUTRAL"
  | "HOSTILE"
  | "ENEMY"
  | "OUTCAST";

export const TIER_THRESHOLDS: ReadonlyArray<{ readonly tier: ReputationTier; readonly min: number }> = Object.freeze([
  { tier: "ALLIED", min: 80 },
  { tier: "FRIENDLY", min: 50 },
  { tier: "TRUSTED", min: 20 },
  { tier: "NEUTRAL", min: -19 },
  { tier: "HOSTILE", min: -49 },
  { tier: "ENEMY", min: -79 },
  { tier: "OUTCAST", min: -100 },
]);

export const TIER_MULTIPLIERS: Readonly<Record<ReputationTier, number>> = Object.freeze({
  ALLIED: 0.5,
  FRIENDLY: 0.65,
  TRUSTED: 0.85,
  NEUTRAL: 1.0,
  HOSTILE: 1.15,
  ENEMY: 1.35,
  OUTCAST: 1.5,
});

export type FactionScores = Readonly<Record<FactionId, number>>;

export const DEFAULT_FACTION_SCORES: FactionScores = Object.freeze({
  hosaka: 0,
  maas: 0,
  sense_net: 0,
  ta: 0,
});

export function scoreToTier(score: number): ReputationTier {
  const clamped = Math.max(-100, Math.min(100, score));
  if (clamped >= 80) return "ALLIED";
  if (clamped >= 50) return "FRIENDLY";
  if (clamped >= 20) return "TRUSTED";
  if (clamped > -20) return "NEUTRAL";
  if (clamped > -50) return "HOSTILE";
  if (clamped > -80) return "ENEMY";
  return "OUTCAST";
}

export function getMultiplier(score: number): number {
  return TIER_MULTIPLIERS[scoreToTier(score)];
}

export function applyScoreChange(
  scores: FactionScores,
  faction: FactionId,
  change: number,
): FactionScores {
  const current = scores[faction] ?? 0;
  const newScore = Math.max(-100, Math.min(100, current + change));
  return { ...scores, [faction]: newScore };
}

export const MISSION_REWARD_MAP: Readonly<Record<FactionId, number>> = Object.freeze({
  hosaka: 10,
  maas: 10,
  sense_net: 10,
  ta: 10,
});

export const KILL_PENALTY_MAP: Readonly<Record<FactionId, number>> = Object.freeze({
  hosaka: -5,
  maas: -5,
  sense_net: -5,
  ta: -5,
});

export function onMissionComplete(
  scores: FactionScores,
  faction: FactionId,
): FactionScores {
  const change = MISSION_REWARD_MAP[faction] ?? 10;
  return applyScoreChange(scores, faction, change);
}

export function onIceKill(
  scores: FactionScores,
  faction: FactionId,
): FactionScores {
  const change = KILL_PENALTY_MAP[faction] ?? -5;
  return applyScoreChange(scores, faction, change);
}

export function getFactionSummary(scores: FactionScores): ReadonlyArray<{
  readonly faction: FactionId;
  readonly score: number;
  readonly tier: ReputationTier;
  readonly multiplier: number;
}> {
  return (Object.keys(scores) as FactionId[]).map(faction => ({
    faction,
    score: scores[faction],
    tier: scoreToTier(scores[faction]),
    multiplier: getMultiplier(scores[faction]),
  }));
}
