import { test } from "node:test";
import assert from "node:assert/strict";
import { runInNewContext } from "node:vm";
import { captureSnapshot } from "./ego-decision-state.mjs";
import {
  DecisionRecorder,
  markdown,
  recordDecisions,
} from "./ego-decision-recorder.mjs";

const snapshot = (overrides = {}) => ({
  at: "2026-11-01T00:00:00Z",
  run: "run-a",
  turn: 1,
  node: 2,
  zone: "surface",
  iceCount: 1,
  reward: 75,
  eventKind: "cache",
  cost: 0,
  hp: 100,
  credits: 0,
  inventoryCredits: 0,
  decision: { selectedVerb: null, probed: false },
  bypassed: null,
  cleared: [],
  runPhase: "matrix",
  phase: "approach",
  intel: [],
  ...overrides,
});

test("records paid PROBE and BYPASS separately, not highlights or rejected confirms", () => {
  // Given
  const recorder = new DecisionRecorder();
  const states = [
    snapshot(),
    snapshot({ decision: { selectedVerb: "BREACH", probed: false } }),
    snapshot({ decision: { selectedVerb: "PROBE", probed: false } }),
    snapshot({
      cost: 8,
      decision: { selectedVerb: "PROBE", probed: true },
      intel: [{ id: "watchdog", hp: 50 }],
    }),
    snapshot({
      cost: 8,
      decision: { selectedVerb: "BYPASS", probed: true },
      intel: [{ id: "watchdog", hp: 50 }],
    }),
    snapshot({ cost: 38, decision: null, bypassed: 2 }),
    snapshot({ node: 3, turn: 2, cost: 38, decision: null }),
  ];
  // When
  states.forEach((state) => recorder.observe(state));
  // Then
  assert.deepEqual(
    recorder.rows.map((r) => [r.verb, r.before.cost, r.delta.cost, r.delta.hp]),
    [
      ["PROBE", 0, 8, 0],
      ["BYPASS", 8, 30, 0],
    ],
  );
  assert.equal(recorder.rows[1].continued, "yes (travel observed)");
  assert.equal(recorder.rows[1].bypassed, true);
  assert.equal(recorder.rows[1].cleared, false);
  assert.match(markdown(recorder.rows), /watchdog HP 50/);
});

test("freezes BREACH deltas at clear before loot healing and later spending", () => {
  // Given
  const recorder = new DecisionRecorder();
  const states = [
    snapshot({ decision: { selectedVerb: "BREACH", probed: false } }),
    snapshot({ decision: null, runPhase: "combat" }),
    snapshot({
      decision: null,
      runPhase: "combat",
      phase: "combat",
      hp: 90,
      cost: 12,
    }),
    snapshot({
      decision: null,
      runPhase: "loot",
      phase: "victory",
      hp: 80,
      cost: 20,
      cleared: [2],
      credits: 75,
      inventoryCredits: 75,
    }),
    snapshot({
      decision: null,
      cleared: [2],
      hp: 95,
      cost: 20,
      credits: 75,
      inventoryCredits: 75,
    }),
    snapshot({ node: 3, turn: 2, decision: null, hp: 95, cost: 30 }),
  ];
  // When
  states.forEach((state) => recorder.observe(state));
  // Then
  assert.equal(recorder.rows.length, 1);
  assert.deepEqual(recorder.rows[0].delta, {
    cost: 20,
    hp: -20,
    credits: 75,
    inventoryCredits: 75,
  });
  assert.equal(recorder.rows[0].combatStarted, true);
  assert.equal(recorder.rows[0].cleared, true);
});

test("JACK OUT wins over a stale bypass marker on a reopened encounter", () => {
  // Given
  const recorder = new DecisionRecorder();
  recorder.observe(
    snapshot({
      bypassed: 2,
      decision: { selectedVerb: "JACK OUT", probed: false },
    }),
  );
  // When
  recorder.observe(snapshot({ bypassed: 2, decision: null, phase: "menu" }));
  // Then
  assert.equal(recorder.rows[0].verb, "JACK OUT");
  assert.equal(recorder.rows[0].continued, "no (run stopped)");
});

test("does not combine observations across restart or synthesize pre-attachment PROBE", () => {
  // Given
  const recorder = new DecisionRecorder();
  recorder.observe(
    snapshot({ cost: 8, decision: { selectedVerb: "PROBE", probed: true } }),
  );
  // When
  recorder.observe(null);
  recorder.observe(snapshot({ run: "run-b" }));
  // Then
  assert.equal(recorder.rows.length, 0);
});

test("missing Space exits without creating or attaching a Space", async () => {
  // Given
  const browser = { listTaskSpaces: async () => [] };
  // When
  const result = await recordDecisions(
    { spaceId: 999999, outputPath: "/tmp/unused.md" },
    browser,
  );
  // Then
  assert.equal(result, null);
});

test("captures revealed fallback HP and mutator copies without leaking pre-probe intel", async () => {
  // Given: real GameState field shape, including a node with no authored HP.
  const state = {
    mission: { id: "fixture", grade_max: 4, seed: 555 },
    totalRuns: 1,
    turnCount: 1,
    currentNodeIndex: 0,
    runPhase: "matrix",
    phase: "approach",
    player: { hp: 100, alarm: 0, credits: 0 },
    inventory: { credits: 4000 },
    matrix: {
      nodes: [
        {
          zone: "mid",
          iceIds: ["yakuza_enforcer"],
          iceHp: [],
          reward: { credits: 75 },
        },
      ],
    },
    iceRoster: [{ id: "base", hp: 154, hpBase: 100, hpPerGrade: 18 }],
    activeIceIndex: 0,
    activeMutators: ["ice_x2"],
    encounterDecision: { selectedVerb: "PROBE", probed: false },
  };
  const pageFor = (s) => ({
    evaluate: async (fn) =>
      JSON.parse(
        JSON.stringify(
          runInNewContext(`(${fn.toString()})()`, {
            window: { wetrun: { state: s } },
          }),
        ),
      ),
  });
  // When
  const hidden = await captureSnapshot(pageFor(state));
  const revealed = await captureSnapshot(
    pageFor({
      ...state,
      encounterDecision: { selectedVerb: "PROBE", probed: true },
    }),
  );
  // Then
  assert.deepEqual(hidden.intel, []);
  assert.equal("probeBasis" in hidden, false);
  assert.deepEqual(revealed.intel, [
    { id: "yakuza_enforcer", hp: 154 },
    { id: "yakuza_enforcer", hp: 154 },
  ]);
  assert.equal(state.player.alarm, 0);
  assert.equal(state.encounterDecision.probed, false);
});
