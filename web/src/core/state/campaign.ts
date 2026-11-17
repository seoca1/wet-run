/** The campaign — a run is a contract of missions, not one (ADR-0315 slice 2).
 *
 * Before this, a run was one mission: `mission select → prep → one mission →
 * ending`. `missionsCompleted` was hardcoded to 1 and the `liberation` ending
 * (`missionsCompleted >= 3`) could never fire. A contract is now the run's
 * shape: the chosen mission, then the rest of its arc in grade order.
 *
 * **Why the arc, and why grade order.** A contract is a job for a fixer about a
 * piece of the Sprawl, and an arc is exactly that piece — ADR-0316 briefs every
 * mission from its arc's story. Grade order keeps the chain from spiking: the
 * player picked a mission at one grade, and the next legs stay in that band
 * instead of jumping to the arc's hardest.
 *
 * **Why the ICE rides along.** The reducer is pure and has no catalog to look
 * an ICE up in, so each leg carries the mission and the ICE it is built from.
 * The save keeps only ids and rebuilds the legs (the same way it stores
 * `missionId` rather than the mission).
 */
import type { Ice, Mission } from "../types";
import { missionGradeOf } from "../combat/ice_scaling";

/** How many missions one contract holds.
 *
 * Three, and the number comes from the resolver: `resolveEnding` opens the
 * `liberation` ending at `missionsCompleted >= 3`. A shorter contract could
 * never reach it and a longer one would make the ending arrive late. Every arc
 * has at least four sprawl missions, so a contract always fills.
 */
export const CONTRACT_LENGTH = 3;

/** One mission of the contract, with the ICE it is built from. */
export interface CampaignLeg {
  readonly mission: Mission;
  readonly ice: Ice;
}

export interface Campaign {
  /** The contract's missions, in the order they are played. */
  readonly legs: readonly CampaignLeg[];
  /** Missions finished so far. The run is on `legs[completed]`. */
  readonly completed: number;
}

/** The contract for a chosen mission: that mission, then the rest of its arc in
 * grade order, up to `CONTRACT_LENGTH`.
 *
 * The chain wraps to the start of the arc when the chosen mission is near its
 * end, so a contract always fills. Far Grid is a separate universe (ADR-0213)
 * and never joins a Sprawl contract. */
export function contractFor(
  chosen: Mission,
  catalog: ReadonlyArray<Mission>,
  iceFor: (mission: Mission) => Ice,
): Campaign {
  const inArc = catalog
    .filter((m) => m.arc === chosen.arc && m.source_universe !== "far-grid")
    .slice()
    .sort(
      (a, b) =>
        missionGradeOf(a) - missionGradeOf(b) || a.id.localeCompare(b.id),
    );
  const start = Math.max(
    0,
    inArc.findIndex((m) => m.id === chosen.id),
  );
  const ordered = [...inArc.slice(start), ...inArc.slice(0, start)];
  return {
    legs: ordered
      .slice(0, CONTRACT_LENGTH)
      .map((mission) => ({ mission, ice: iceFor(mission) })),
    completed: 0,
  };
}

/** Is there another mission after the one the run is on? */
export function campaignContinues(campaign: Campaign | undefined): boolean {
  return (
    campaign !== undefined && campaign.completed + 1 < campaign.legs.length
  );
}

/** How many missions the contract holds. 0 when the run is not a campaign. */
export function campaignLength(campaign: Campaign | undefined): number {
  return campaign?.legs.length ?? 0;
}

/** The mission the run is on, or null when it is not a campaign. */
export function campaignMission(campaign: Campaign | undefined): Mission | null {
  return campaign?.legs[campaign.completed]?.mission ?? null;
}
