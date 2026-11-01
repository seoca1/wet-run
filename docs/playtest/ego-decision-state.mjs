// Node 24+ native type stripping; imports only pure, read-only game calculations.
import {
  iceHpForGrade,
  missionGradeOf,
} from "../../web/src/core/combat/ice_scaling.ts";

/** Browser callback: reads only; no identity/HP leaves the page before PROBE. */
export function readSnapshot() {
  const s = window.wetrun?.state;
  if (!s) return null;
  const n = s.matrix?.nodes[s.currentNodeIndex];
  const probed = Boolean(s.encounterDecision?.probed && n);
  const activeIce = s.iceRoster[s.activeIceIndex] ?? s.ice;
  return {
    at: new Date().toISOString(),
    run: JSON.stringify([s.mission.id, s.mission.seed, s.totalRuns]),
    turn: s.turnCount,
    node: s.currentNodeIndex,
    zone: n?.zone ?? "unknown",
    iceCount: n?.iceIds.length ?? 0,
    reward: n?.reward.credits ?? 0,
    eventKind: n?.eventKind ?? "combat",
    cost: s.player.alarm,
    hp: s.player.hp,
    credits: s.player.credits,
    inventoryCredits: s.inventory.credits,
    decision: s.encounterDecision ? { ...s.encounterDecision } : null,
    bypassed: s.bypassedEncounterNodeIndex ?? null,
    cleared: [...(s.clearedEncounterNodes ?? [])],
    runPhase: s.runPhase,
    phase: s.phase,
    // Same fallback basis as encounterRoster; evaluated in Node with the real helper.
    probeBasis: probed
      ? {
          ice: {
            hp: activeIce.hp,
            hpBase: activeIce.hpBase,
            hpPerGrade: activeIce.hpPerGrade,
          },
          mission: {
            grade: s.mission.grade,
            grade_min: s.mission.grade_min,
            grade_max: s.mission.grade_max,
          },
        }
      : null,
    intel: probed
      ? Array.from(
          {
            length: Math.min(
              n.iceIds.length * (s.activeMutators.includes("ice_x2") ? 2 : 1),
              4,
            ),
          },
          (_, i) => ({
            id: n.iceIds[i % n.iceIds.length] ?? activeIce.id,
            hp: n.iceHp[i % n.iceHp.length] ?? null,
          }),
        )
      : [],
  };
}

/** Convert detached probe data using the same pure scaling function as the renderer. */
export async function captureSnapshot(page) {
  const raw = await page.evaluate(readSnapshot);
  if (!raw) return null;
  const { probeBasis, ...snapshot } = raw;
  if (!probeBasis) return snapshot;
  const hp = iceHpForGrade(probeBasis.ice, missionGradeOf(probeBasis.mission));
  return {
    ...snapshot,
    intel: snapshot.intel.map((ice) => ({ ...ice, hp: ice.hp ?? hp })),
  };
}
