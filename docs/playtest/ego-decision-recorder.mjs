import { writeFile } from "node:fs/promises";
import { isAbsolute } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { captureSnapshot } from "./ego-decision-state.mjs";

/** Mutable accumulator; accepts detached snapshots, never live game objects. */
export class DecisionRecorder {
  rows = [];
  previous = null;
  visit = [];

  observe(s) {
    const p = this.previous;
    if (!s || (p && (p.run !== s.run || s.turn < p.turn))) {
      this.visit = [];
      this.previous = s;
      return;
    }
    if (p && s.node !== p.node) {
      for (const row of this.visit) {
        row.continued = "yes (travel observed)";
        if (row.outcome === "pending")
          row.outcome = "incomplete (resolution missed)";
      }
      this.visit = [];
    }
    if (p?.decision && s.node === p.node) {
      let verb = null;
      if (!p.decision.probed && s.decision?.probed) verb = "PROBE";
      if (!s.decision) {
        if (["menu", "exit"].includes(s.phase)) verb = "JACK OUT";
        else if (s.runPhase === "combat" || s.cleared.includes(s.node))
          verb = "BREACH";
        else if (s.bypassed === s.node) verb = "BYPASS";
        else verb = "UNKNOWN";
      }
      if (verb) {
        const row = {
          at: s.at,
          run: s.run,
          node: p.node,
          zone: p.zone,
          iceCount: p.iceCount,
          reward: p.reward,
          eventKind: p.eventKind,
          verb,
          highlighted: p.decision.selectedVerb,
          probedBefore: p.decision.probed,
          intel: s.intel.length ? s.intel : p.intel,
          before: {
            cost: p.cost,
            hp: p.hp,
            credits: p.credits,
            inventoryCredits: p.inventoryCredits,
          },
          delta: null,
          combatEntered: s.runPhase === "combat",
          combatStarted: s.phase === "combat",
          cleared: false,
          bypassed: false,
          outcome: verb === "BREACH" ? "pending" : "observed",
          continued: "unknown (recording ended before travel)",
          note: "Last sampled before/after; intermediate actions may be missed.",
        };
        this.rows.push(row);
        this.visit.push(row);
        this.updateOutcome(row, s);
      }
    }
    for (const row of this.visit) {
      row.cleared ||= s.cleared.includes(row.node);
      row.bypassed ||= s.bypassed === row.node;
      if (row.verb === "BREACH" && row.outcome === "pending") {
        this.updateOutcome(row, s);
        if (row.cleared || s.runPhase === "loot")
          row.outcome = "cleared (before loot confirm)";
        else if (
          s.hp <= 0 ||
          ["dead", "ending"].includes(s.runPhase) ||
          ["menu", "exit", "defeat"].includes(s.phase)
        )
          row.outcome = "run stopped";
      }
      if (
        s.hp <= 0 ||
        ["dead", "ending"].includes(s.runPhase) ||
        ["menu", "exit", "defeat"].includes(s.phase)
      )
        row.continued = "no (run stopped)";
    }
    this.previous = s;
  }

  updateOutcome(row, s) {
    row.delta = {
      cost: s.cost - row.before.cost,
      hp: s.hp - row.before.hp,
      credits: s.credits - row.before.credits,
      inventoryCredits: s.inventoryCredits - row.before.inventoryCredits,
    };
    row.combatEntered ||= s.runPhase === "combat";
    row.combatStarted ||= s.phase === "combat";
    row.cleared ||= s.cleared.includes(row.node);
    row.bypassed ||= s.bypassed === row.node;
  }
}

export function markdown(rows) {
  const cell = (v) => String(v).replaceAll("|", "\\|").replaceAll("\n", " ");
  const lines = rows.map((r) =>
    [
      r.node,
      r.zone,
      r.iceCount,
      `${r.reward}cr / ${r.eventKind}`,
      r.intel.length
        ? r.intel.map((ice) => `${ice.id} HP ${ice.hp ?? "unknown"}`).join(", ")
        : "hidden",
      r.before.cost,
      r.before.hp,
      r.verb,
      r.delta.cost,
      r.delta.hp,
      `${r.delta.credits} / ${r.delta.inventoryCredits}`,
      `${r.combatEntered} / ${r.combatStarted}`,
      `${r.cleared} / ${r.bypassed}`,
      r.outcome,
      r.continued,
    ]
      .map(cell)
      .join(" | "),
  );
  return [
    "# Encounter decision observations",
    "",
    "Node indices are 0-based (UI adds 1). COST = player.alarm; credits = player / inventory.",
    "One row per accepted verb; PROBE is separate from its following choice. Highlights are not choices.",
    "Deltas span sampled intervals, not causal/counterfactual estimates. BREACH stops at first observed clear/stop.",
    "Clear/bypass flags describe this visit; continuation means later travel. Unknown is not a failed run.",
    "Polling can miss fast actions, menu openings, clears, and restarts. Pending means censored combat.",
    "",
    "| Node | Zone | ICE count | Reward / event | Probed ICE | COST before | HP before | Verb | ΔCOST | ΔHP | Δcredits P/I | Combat entered / started | Cleared / bypassed | Outcome | Continued |",
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ...lines.map((line) => `| ${line} |`),
    "",
  ].join("\n");
}

/** Run inside ego-browser nodejs; all paths/arguments must be explicit, not env/cwd. */
export async function recordDecisions(options, browser) {
  const {
    spaceId,
    outputPath,
    pageLabel = "p1",
    durationMs = 60000,
    intervalMs = 100,
  } = options;
  const recorder = new DecisionRecorder();
  if (
    !Number.isInteger(spaceId) ||
    typeof outputPath !== "string" ||
    !isAbsolute(outputPath) ||
    !Number.isFinite(durationMs) ||
    durationMs <= 0 ||
    !Number.isFinite(intervalMs) ||
    intervalMs < 25
  ) {
    console.error(
      "Recorder: supply numeric spaceId, absolute outputPath, positive durationMs and intervalMs >= 25.",
    );
    return null;
  }
  try {
    const space = (await browser.listTaskSpaces()).find(
      (entry) => entry.id === spaceId,
    );
    if (!space) {
      console.error(
        `Recorder: Space ${spaceId} not found; use an existing Space ID. Nothing created.`,
      );
      return null;
    }
    if (space.ownership !== "agent") {
      console.error(
        `Recorder: Space ${spaceId} is user-owned/inactive. No claim or takeover attempted. Use an already authorized agent Space.`,
      );
      return null;
    }
    const task = await browser.taskSpace(spaceId);
    const pages = await task.pages();
    if (!pages.some((page) => page.label === pageLabel)) {
      console.error(
        `Recorder: Page ${pageLabel} not found in Space ${spaceId}.`,
      );
      return null;
    }
    const page = task.page(pageLabel);
    const first = await captureSnapshot(page);
    if (!first) {
      console.error(
        "Recorder: game not loaded or no active run (window.wetrun.state is null). Start playing, then retry; no navigation/input sent.",
      );
      return null;
    }
    recorder.observe(first);
    console.log(
      `Recorder polling Space ${spaceId}/${pageLabel} for ${durationMs}ms. Drive the game yourself; leave >= ${intervalMs * 3}ms between actions.`,
    );
    const deadline = Date.now() + durationMs;
    while (Date.now() < deadline) {
      await delay(intervalMs);
      recorder.observe(await captureSnapshot(page));
    }
  } catch (error) {
    if (!(error instanceof Error)) throw error;
    console.error(
      `Recorder stopped; partial observations retained: ${error.message}`,
    );
  }
  // Exclusive writes prevent accidentally overwriting an existing report.
  try {
    await writeFile(outputPath, markdown(recorder.rows), { flag: "wx" });
    await writeFile(
      `${outputPath}.json`,
      JSON.stringify(recorder.rows, null, 2) + "\n",
      { flag: "wx" },
    );
  } catch (error) {
    if (!(error instanceof Error)) throw error;
    console.error(
      `Recorder output failed (use a fresh path in an existing directory): ${error.message}`,
    );
    return null;
  }
  const counts = Object.fromEntries(
    ["PROBE", "BYPASS", "BREACH", "JACK OUT", "UNKNOWN"].map((verb) => [
      verb,
      recorder.rows.filter((row) => row.verb === verb).length,
    ]),
  );
  console.log(
    JSON.stringify({
      rows: recorder.rows.length,
      counts,
      outputPath,
      jsonPath: `${outputPath}.json`,
      pending: recorder.rows.filter((r) => r.outcome === "pending").length,
    }),
  );
  // Intentionally no finish/handOff/claim: the observer does not own the play session.
  return recorder.rows;
}
