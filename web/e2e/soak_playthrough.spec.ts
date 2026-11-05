/** Direct-control playthrough soak (ADR-0265).
 *
 * Both field reports so far were "the game froze": a dead-end defeat screen
 * (ADR-0263) and a combat freeze at the COST cap (ADR-0265). Each was found by
 * hand, one at a time. This spec is the systematic version: it plays the real
 * build in a real browser with real key presses across the mission list, and
 * reports where and how often a run cannot progress.
 *
 * The run is deterministic -- the matrix generator, the combat dice and the
 * program order are all seeded from the mission, and the policy is a pure
 * function of the observable state (except the seeded "random" policy). So
 * repeating one (mission, policy) cell reproduces the same run exactly;
 * variance comes from covering *different cells*, which is why this enumerates
 * missions instead of repeating a few. The reported rate is a census over
 * those cells, not a sample.
 *
 * Rules this harness holds itself to:
 *   - real keys only. It never writes `wetrun.state`; the reducer and the
 *     controller are exactly the ones a player drives.
 *   - the policy drives; the sweep only diagnoses. A full key sweep runs only
 *     when the policy's own action changed nothing, so the harness cannot
 *     wreck a healthy run by mashing keys at it.
 *   - a freeze is not "the policy got confused". Two classifications, because
 *     the owner's report is the second one:
 *       deadlocked        no key does anything at all
 *       only_escape_loses every progress key is inert, and Escape (JACK OUT)
 *                         does something -- and that something is losing the run
 *
 * Run it:
 *   npm run soak
 *   SOAK_RUNS=159 SOAK_POLICY=mixed npm run soak
 *
 * Skipped unless SOAK is set, so `npm run e2e` stays fast.
 */
import { test, type Page } from "@playwright/test";
import { gotoMenuOption } from "./menu-nav";

const RUNS = Number(process.env.SOAK_RUNS ?? "9");
const POLICY = process.env.SOAK_POLICY ?? "mixed";
const MAX_STEPS = Number(process.env.SOAK_MAX_STEPS ?? "320");
const SEED = Number(process.env.SOAK_SEED ?? "20261103");
const MISSION_COUNT = Number(process.env.SOAK_MISSION_COUNT ?? "53");
const MISSION_BASE = Number(process.env.SOAK_MISSION_BASE ?? "0");
const TRACE = process.env.SOAK_TRACE === "1";
const COST_LIMIT = 100;
/** Steps with no *progress* (nothing cleared, nobody hurt, no COST moved)
 * before a run is called "no end in reach" rather than played out. Without
 * this, a run that can no longer reach an ending burns the whole step ceiling. */
const STALL_STEPS = Number(process.env.SOAK_STALL ?? "40");

/** Keys that should make progress. The give-up keys are excluded on purpose:
 * Escape *and* q both map to jack_out (KEYBOARD_MAPPING), and "only giving up
 * works" is its own finding -- the first version of this sweep pressed q and
 * quietly abandoned every run it touched. */
const PROGRESS_KEYS: readonly string[] = [
  "Enter",
  " ",
  "Tab",
  "1",
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
  "0",
  "ArrowDown",
  "ArrowUp",
  "ArrowLeft",
  "ArrowRight",
  "w",
  "e",
  "z",
  "x",
];

/** Both jack_out keys: pressing either ends the run. */
const GIVE_UP_KEYS: readonly string[] = ["Escape", "q"];

type NodeMeta = {
  readonly adj: readonly number[];
  readonly ice: number;
  readonly boss: boolean;
};

type Run = {
  readonly runPhase: string;
  readonly phase: string;
  readonly cur: number;
  readonly sel: number | null;
  readonly hp: number;
  readonly alarm: number;
  readonly turn: number;
  readonly deck: readonly { readonly id: string; readonly cost: number }[];
  readonly ice: readonly number[];
  readonly nodes: readonly NodeMeta[];
  readonly visited: readonly number[];
  readonly cleared: readonly number[];
  readonly bypassed: readonly number[];
  readonly msg: string;
  readonly taken: string | null;
  readonly verb: string | null;
  readonly decision: boolean;
  readonly grade: number;
  readonly missionId: string;
  /** The ending the run reached, or null while the run is live. */
  readonly ending: string | null;
};

type Snap = { readonly screen: string; readonly state: Run | null };

type Outcome =
  | "completed"
  | "failed"
  | "deadlocked"
  | "only_escape_loses"
  | "no_end_in_steps";

type RunReport = {
  readonly run: number;
  readonly mission: number;
  readonly policy: string;
  readonly grade?: number;
  readonly missionId?: string;
  readonly outcome: Outcome;
  readonly steps: number;
  readonly ms: number;
  readonly endPhase?: string;
  readonly endAlarm?: number;
  readonly endTurn?: number;
  readonly endIceHp?: readonly number[];
  readonly endHand?: number;
  readonly endAffordable?: number;
  readonly maxAlarm?: number;
  readonly minAffordable?: number;
  readonly endMsg?: string;
  readonly endBusiness?: number;
  readonly escapeResult?: string;
  /** The ending id — the run's outcome as a story beat, not just a phase. */
  readonly ending?: string | null;
};

/** Semantic projection: the fields that mean "something happened". Volatile
 * render-only fields (vfx, animation clocks, the grid) are excluded so a
 * redraw is not mistaken for progress. */
async function snap(page: Page): Promise<Snap> {
  return page.evaluate(() => {
    const w = window as unknown as {
      wetrun: { state: Record<string, unknown> | null; getScreen(): string };
    };
    const s = w.wetrun.state;
    if (!s) return { screen: w.wetrun.getScreen(), state: null };
    const st = s as {
      runPhase: string;
      phase: string;
      currentNodeIndex: number;
      selectedMatrixNodeIndex: number | null;
      player: { hp: number; alarm: number };
      turnCount: number;
      deck: { id: string; cost?: number }[];
      iceRoster: { hp: number }[];
      matrix?: {
        nodes: { adjacent: number[]; iceIds?: string[]; isBoss?: boolean }[];
      };
      message: string;
      cardRewardTaken?: string | null;
      encounterDecision?: { selectedVerb: string | null } | null;
      visitedNodes?: number[];
      clearedEncounterNodes?: number[];
      bypassedEncounterNodes?: number[];
      mission?: { id?: string; grade_max?: number; grade?: number };
      endingChoice?: string | null;
    };
    const node = st.matrix?.nodes[st.currentNodeIndex];
    return {
      screen: w.wetrun.getScreen(),
      state: {
        runPhase: st.runPhase,
        phase: st.phase,
        cur: st.currentNodeIndex,
        sel: st.selectedMatrixNodeIndex ?? null,
        hp: st.player.hp,
        alarm: st.player.alarm,
        turn: st.turnCount,
        deck: st.deck.map((p) => ({ id: p.id, cost: p.cost ?? 0 })),
        ice: st.iceRoster.map((i) => i.hp),
        nodes: (st.matrix?.nodes ?? []).map((n) => ({
          adj: n.adjacent,
          ice: n.iceIds?.length ?? 0,
          boss: n.isBoss === true,
        })),
        visited: st.visitedNodes ?? [],
        cleared: st.clearedEncounterNodes ?? [],
        bypassed: st.bypassedEncounterNodes ?? [],
        // The idle alarm rewrites its own TRACE line on a wall clock, with no
        // key pressed. Normalising it keeps a self-driven change from masking
        // a real freeze (this is what hid the COST-cap freeze below).
        msg: /^TRACE \d+\/\d+$/.test(st.message) ? "(trace)" : st.message,
        taken: st.cardRewardTaken ?? null,
        verb: st.encounterDecision?.selectedVerb ?? null,
        decision: st.encounterDecision != null,
        grade: st.mission?.grade_max ?? st.mission?.grade ?? 0,
        missionId: st.mission?.id ?? "?",
        ending: st.endingChoice ?? null,
      },
    };
  });
}

const hash = (s: Snap): string => JSON.stringify(s);

/** The same snapshot without the message text. A freeze is about whether the
 * *state* can move; refusal text is not progress, and worse, two refusals can
 * alternate ("Cost too high" / "Hand slot 6 is empty"), which made a frozen
 * fight look alive on every sweep. The idle alarm's own TRACE line is text
 * too, so leaving the message out covers that as well. */
const structural = (s: Snap): string => {
  if (s.state === null)
    return JSON.stringify({ screen: s.screen, state: null });
  const st = s.state;
  return JSON.stringify([
    s.screen,
    st.runPhase,
    st.phase,
    st.cur,
    st.sel,
    st.hp,
    st.alarm,
    st.turn,
    st.deck,
    st.ice,
    st.visited,
    st.cleared,
    st.bypassed,
    st.taken,
    st.verb,
    st.decision,
  ]);
};

/** Deterministic PRNG so the "random" policy reproduces from SEED. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Press one key and wait (briefly) for the projection to move. */
async function pressAndWatch(
  page: Page,
  key: string,
  before: string,
): Promise<boolean> {
  await page.keyboard.press(key);
  // The reducer is synchronous, so one short settle window is enough: the
  // animation layers (matrix travel, VFX) are excluded from the projection.
  await page.waitForTimeout(18);
  return hash(await snap(page)) !== before;
}

/** Does *no* progress key move the state? Compared structurally (see
 * `structural`), so a message that only rewrites itself is not a move. Two
 * passes so a one-shot result cannot be mistaken for progress. The give-up
 * keys are not in this set. */
async function inertProgressKeys(page: Page): Promise<boolean> {
  const press = async (key: string): Promise<boolean> => {
    const before = structural(await snap(page));
    await page.keyboard.press(key);
    await page.waitForTimeout(18);
    return structural(await snap(page)) !== before;
  };
  for (const key of PROGRESS_KEYS) await press(key);
  for (const key of PROGRESS_KEYS) {
    if (await press(key)) return false;
  }
  return true;
}

/** Is this node still worth visiting: unresolved ICE, or a boss not cleared?
 * Bypassed nodes count as resolved -- otherwise a policy that BYPASSes keeps
 * routing back to the node it just bypassed, forever. */
function hasBusiness(st: Run, i: number): boolean {
  const n = st.nodes[i];
  if (!n) return false;
  if (st.cleared.includes(i) || st.bypassed.includes(i)) return false;
  return n.ice > 0 || n.boss;
}

/** First step of a BFS from the current node toward the nearest node that
 * still has business. Purposeful routing keeps a run ending; the policy under
 * test is how a run is *played*, not whether the harness can navigate. */
function nextHop(st: Run, rng: () => number): number {
  const prev = new Map<number, number>();
  const queue: number[] = [st.cur];
  const seen = new Set<number>([st.cur]);
  while (queue.length > 0) {
    const at = queue.shift() as number;
    if (at !== st.cur && hasBusiness(st, at)) {
      let step = at;
      while ((prev.get(step) ?? st.cur) !== st.cur) {
        step = prev.get(step) as number;
      }
      return step;
    }
    for (const nx of st.nodes[at]?.adj ?? []) {
      if (seen.has(nx)) continue;
      seen.add(nx);
      prev.set(nx, at);
      queue.push(nx);
    }
  }
  const pool = st.nodes[st.cur]?.adj ?? [];
  if (pool.length === 0) return st.cur;
  return pool[Math.floor(rng() * pool.length)] as number;
}

/** One policy step. Keys are pressed *interleaved* with reads: a key list
 * computed up front cannot observe its own effect, which is exactly what made
 * the first version mash arrows at the verb list and wander the board. */
async function play(
  page: Page,
  policy: string,
  rng: () => number,
): Promise<boolean> {
  let last = hash(await snap(page));
  let moved = false;
  const doKey = async (k: string): Promise<void> => {
    if (await pressAndWatch(page, k, last)) moved = true;
    last = hash(await snap(page));
  };

  const s0 = await snap(page);
  const st0 = s0.state;
  if (!st0) {
    await doKey("Enter");
    return moved;
  }
  if (st0.runPhase === "ending" || st0.runPhase === "dead") {
    await doKey("Enter");
    return moved;
  }

  if (st0.runPhase === "loot") {
    const node = st0.nodes[st0.cur];
    const terminal = (node?.adj.length ?? 0) === 0 || node?.boss === true;
    if (st0.taken === null && !terminal && policy !== "skip_rewards") {
      await doKey("1"); // take the first program
    } else {
      await doKey("Enter");
    }
    return moved;
  }

  if (st0.runPhase === "matrix" && st0.decision) {
    const want = policy === "random" && rng() < 0.3 ? "BYPASS" : "BREACH";
    for (let i = 0; i < 8; i += 1) {
      if ((await snap(page)).state?.verb === want) break;
      await doKey("ArrowDown");
    }
    await doKey("Enter");
    return moved;
  }

  if (st0.runPhase === "matrix") {
    const target = nextHop(st0, rng);
    if (target === st0.cur) {
      await doKey("Enter");
      return moved;
    }
    const adj = st0.nodes[st0.cur]?.adj ?? [];
    for (let i = 0; i < adj.length + 1; i += 1) {
      if ((await snap(page)).state?.sel === target) break;
      await doKey("ArrowDown");
    }
    await doKey("Enter");
    return moved;
  }

  if (st0.runPhase === "combat") {
    const affordable = st0.deck
      .map((p, i) => ({ ...p, slot: i + 1 }))
      .filter((p) => st0.alarm + p.cost <= COST_LIMIT);
    if (affordable.length === 0) {
      // Nothing playable: the turn cannot advance (that is the freeze under
      // test), so just probe once and let the caller diagnose.
      await doKey("Enter");
      return moved;
    }
    affordable.sort((a, b) => a.cost - b.cost);
    const pick =
      policy === "expensive"
        ? affordable[affordable.length - 1]
        : policy === "random"
          ? affordable[Math.floor(rng() * affordable.length)]
          : affordable[0];
    await doKey(String(pick.slot));
    return moved;
  }

  await doKey("Enter");
  return moved;
}

/** NEW RUN, pick a jockey, pick a mission, launch. */
async function startRun(
  page: Page,
  missionOffset: number,
  jockey = 0,
): Promise<void> {
  await gotoMenuOption(page, "new_run");
  await page.keyboard.press("Enter");
  // ADR-0274: NEW RUN opens the jockey select first. Without this the harness
  // waited for a mission list that the jockey screen was covering.
  await page.waitForFunction(
    () =>
      ["jockey_select", "mission_select"].includes(
        (
          window as unknown as { wetrun: { getScreen(): string } }
        ).wetrun.getScreen(),
      ),
    undefined,
    { timeout: 10000 },
  );
  const screen = (): Promise<string> =>
    page.evaluate(
      () =>
        (window as unknown as { wetrun: { getScreen(): string } }).wetrun.getScreen(),
    );
  if ((await screen()) === "jockey_select") {
    for (let i = 0; i < jockey; i += 1) await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Enter");
  }
  await page.waitForFunction(
    () =>
      (
        window as unknown as { wetrun: { getScreen(): string } }
      ).wetrun.getScreen() === "mission_select",
    undefined,
    { timeout: 10000 },
  );
  for (let i = 0; i < missionOffset; i += 1) {
    await page.keyboard.press("ArrowDown");
  }
  await page.keyboard.press("Enter");
  await page.waitForFunction(
    () =>
      (
        window as unknown as {
          wetrun: { state?: { runPhase?: string } | null };
        }
      ).wetrun.state?.runPhase === "matrix",
    undefined,
    { timeout: 10000 },
  );
}

test.describe("direct-control playthrough soak", () => {
  test.skip(!process.env.SOAK, "soak runs only via `npm run soak` (SOAK=1)");
  test.setTimeout(0);

  test("plays the mission list and reports freeze statistics", async ({
    page,
  }) => {
    const reports: RunReport[] = [];
    const rng = mulberry32(SEED);
    const policies =
      POLICY === "mixed" ? ["cheap", "expensive", "random"] : [POLICY];

    await page.addInitScript(() =>
      localStorage.setItem("wetrun_tutorial_completed", "true"),
    );
    await page.goto("./");
    await page.waitForFunction(
      () => (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
    );

    for (let run = 0; run < RUNS; run += 1) {
      const policy = policies[run % policies.length] as string;
      const mission = (MISSION_BASE + run) % MISSION_COUNT;
      const started = Date.now();
      let steps = 0;
      let outcome: Outcome = "no_end_in_steps";
      let detail: Partial<RunReport> = {};

      await startRun(page, mission);
      const launched = (await snap(page)).state;
      const marker = (s: Snap): string =>
        s.state === null
          ? "out"
          : [
              s.state.cleared.length,
              s.state.visited.length,
              s.state.hp,
              s.state.alarm,
              s.state.deck.length,
              s.state.ice.reduce((a, b) => a + b, 0),
            ].join(":");
      let lastMarker = marker(await snap(page));
      let stalled = 0;
      let maxAlarm = 0;
      let minAffordable = 99;

      for (; steps < MAX_STEPS; steps += 1) {
        const s = await snap(page);
        if (s.state !== null) {
          maxAlarm = Math.max(maxAlarm, s.state.alarm);
          if (s.state.runPhase === "combat") {
            minAffordable = Math.min(
              minAffordable,
              s.state.deck.filter((p) => s.state!.alarm + p.cost <= COST_LIMIT)
                .length,
            );
          }
        }
        if (s.state === null && s.screen === "menu") {
          outcome = "completed";
          break;
        }
        if (TRACE) {
          // eslint-disable-next-line no-console
          console.log(
            `SOAK-STEP ${JSON.stringify({
              step: steps,
              phase: `${s.state.runPhase}/${s.state.phase}`,
              cur: s.state.cur,
              sel: s.state.sel,
              ice: s.state.ice,
              hand: s.state.deck.length,
              alarm: s.state.alarm,
              decision: s.state.decision,
              verb: s.state.verb,
              cleared: s.state.cleared,
              visited: s.state.visited,
              msg: s.state.msg,
            })}`,
          );
        }

        const moved = await play(page, policy, rng);
        const now = await snap(page);

        if (
          now.state !== null &&
          (now.state.runPhase === "dead" || now.state.runPhase === "ending")
        ) {
          const reached = now.state.ending;
          await page.keyboard.press("Enter");
          await page.waitForTimeout(250);
          outcome = now.state.runPhase === "dead" ? "failed" : "completed";
          detail = { endPhase: `${now.state.runPhase}/${now.state.phase}`, ending: reached };
          steps += 1;
          break;
        }
        if (moved) {
          lastMarker = marker(now);
          stalled = 0;
          continue;
        }

        // Nothing the policy did moved the run. Two questions, in order that
        // matters: the freeze sweep first (it is the finding, and it answers
        // on the very first stuck step), then the stall guard (a run that can
        // no longer reach an ending must not burn the whole ceiling).
        if (await inertProgressKeys(page)) {
          // (classification below)
        } else {
          // Some other key still works: it was a bad choice, not a freeze.
          const nowMarker = marker(now);
          if (nowMarker === lastMarker) stalled += 1;
          else {
            lastMarker = nowMarker;
            stalled = 0;
          }
          if (stalled >= STALL_STEPS) break; // no end in reach
          continue;
        }
        const st = (await snap(page)).state;
        if (st === null) {
          outcome = "completed";
          break;
        }
        const escBefore = structural(await snap(page));
        let afterEsc = await snap(page);
        for (const giveUp of GIVE_UP_KEYS) {
          await page.keyboard.press(giveUp);
          await page.waitForTimeout(200);
          afterEsc = await snap(page);
          if (structural(afterEsc) !== escBefore) break;
        }
        outcome =
          structural(afterEsc) === escBefore
            ? "deadlocked"
            : "only_escape_loses";
        detail = {
          endPhase: `${st.runPhase}/${st.phase}`,
          endAlarm: st.alarm,
          endTurn: st.turn,
          endIceHp: st.ice,
          endHand: st.deck.length,
          endAffordable: st.deck.filter((p) => st.alarm + p.cost <= COST_LIMIT)
            .length,
          endMsg: st.msg,
          escapeResult: afterEsc.state
            ? `${afterEsc.state.runPhase}/${afterEsc.state.phase}`
            : `screen:${afterEsc.screen}`,
        };
        break;
      }

      if (detail.endPhase === undefined) {
        // The run hit the step ceiling: the state kept changing but never
        // reached an end. Its own finding, kept separate from a freeze.
        const end = (await snap(page)).state;
        detail = {
          endPhase: end ? `${end.runPhase}/${end.phase}` : "not-in-run",
          endAlarm: end?.alarm,
          endTurn: end?.turn,
          endIceHp: end?.ice,
          endHand: end?.deck.length,
          endMsg: end?.msg,
          endBusiness: end
            ? end.nodes
                .map((n, i) =>
                  !end.cleared.includes(i) &&
                  !end.bypassed.includes(i) &&
                  (n.ice > 0 || n.boss)
                    ? 1
                    : 0,
                )
                .reduce((a, b) => a + b, 0)
            : 0,
        };
      }

      reports.push({
        run,
        mission,
        policy,
        grade: launched?.grade,
        missionId: launched?.missionId,
        maxAlarm,
        minAffordable: minAffordable === 99 ? undefined : minAffordable,
        outcome,
        steps,
        ms: Date.now() - started,
        ...detail,
      });

      // eslint-disable-next-line no-console
      console.log(
        `SOAK-RUN ${JSON.stringify({
          run,
          mission: launched?.missionId,
          grade: launched?.grade,
          policy,
          outcome,
          steps,
          ms: Date.now() - started,
          maxAlarm,
          minAffordable: minAffordable === 99 ? undefined : minAffordable,
          ...detail,
        })}`,
      );

      // A frozen screen's only non-fatal exit is a reload.
      if ((await snap(page)).state !== null) {
        await page.goto("./");
        await page.waitForFunction(
          () =>
            (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
        );
      }
    }

    const frozen = reports.filter(
      (r) => r.outcome === "deadlocked" || r.outcome === "only_escape_loses",
    );
    const n = reports.length;
    const rate = n === 0 ? 0 : frozen.length / n;
    // Wilson 95% interval: a rate is a range, not a point.
    const z = 1.96;
    const centre = (rate + (z * z) / (2 * n)) / (1 + (z * z) / n);
    const half =
      (z * Math.sqrt((rate * (1 - rate)) / n + (z * z) / (4 * n * n))) /
      (1 + (z * z) / n);
    const count = (
      key: (r: RunReport) => string,
      pool: readonly RunReport[] = reports,
    ): Record<string, number> =>
      pool.reduce<Record<string, number>>((acc, r) => {
        const k = key(r);
        acc[k] = (acc[k] ?? 0) + 1;
        return acc;
      }, {});

    const summary = {
      harness: {
        seed: SEED,
        runs: n,
        missions: MISSION_COUNT,
        requestedPolicy: POLICY,
        maxSteps: MAX_STEPS,
        deterministic:
          "the run is seeded from the mission; the policy is a pure function of state (except the seeded 'random' policy)",
        classification: {
          deadlocked: "no key changes the state at all",
          only_escape_loses:
            "every progress key is inert; Escape changes it and that is a lost run",
          no_end_in_steps:
            "state kept changing but the run never ended within maxSteps",
        },
      },
      byOutcome: count((r) => r.outcome),
      byPolicy: policies.map((p) => ({
        policy: p,
        runs: reports.filter((r) => r.policy === p).length,
        frozen: reports.filter(
          (r) =>
            r.policy === p &&
            (r.outcome === "deadlocked" || r.outcome === "only_escape_loses"),
        ).length,
      })),
      frozenRate: Number(rate.toFixed(4)),
      frozenRate95: [
        Number(Math.max(0, centre - half).toFixed(4)),
        Number(Math.min(1, centre + half).toFixed(4)),
      ],
      costCap: {
        note: "COST (player.alarm) only rises from playing programs, and the turn only ends when the hand empties -- so the cap is where a fight can stop being playable",
        limit: COST_LIMIT,
        runsReachingCap: reports.filter((r) => (r.maxAlarm ?? 0) >= COST_LIMIT)
          .length,
        runsWithNoAffordableCard: reports.filter(
          (r) => (r.minAffordable ?? 1) === 0,
        ).length,
        capMissions: reports
          .filter((r) => (r.maxAlarm ?? 0) >= COST_LIMIT)
          .map((r) => ({
            mission: r.missionId,
            grade: r.grade,
            policy: r.policy,
            outcome: r.outcome,
            maxAlarm: r.maxAlarm,
            minAffordable: r.minAffordable,
          })),
      },
      runsByGrade: count((r) => `g${r.grade ?? "?"}`),
      frozenByGrade: count((r) => `g${r.grade ?? "?"}`, frozen),
      frozenByPhase: count((r) => r.endPhase ?? "unknown", frozen),
      frozenDetail: frozen.map((r) => ({
        run: r.run,
        mission: r.missionId,
        grade: r.grade,
        policy: r.policy,
        outcome: r.outcome,
        phase: r.endPhase,
        turn: r.endTurn,
        alarm: r.endAlarm,
        hand: r.endHand,
        affordable: r.endAffordable,
        iceHp: r.endIceHp,
        escape: r.escapeResult,
        msg: r.endMsg,
      })),
      noEndInSteps: reports
        .filter((r) => r.outcome === "no_end_in_steps")
        .map((r) => ({
          run: r.run,
          mission: r.missionId,
          grade: r.grade,
          policy: r.policy,
          phase: r.endPhase,
          turn: r.endTurn,
          alarm: r.endAlarm,
          businessLeft: r.endBusiness,
        })),
      meanSteps: Number(
        (reports.reduce((a, r) => a + r.steps, 0) / (n || 1)).toFixed(1),
      ),
      meanMs: Math.round(reports.reduce((a, r) => a + r.ms, 0) / (n || 1)),
    };

    // eslint-disable-next-line no-console
    console.log("SOAK-SUMMARY " + JSON.stringify(summary, null, 2));
    if (process.env.SOAK_REPORT) {
      const { writeFileSync } = await import("node:fs");
      writeFileSync(
        process.env.SOAK_REPORT,
        JSON.stringify({ summary, reports }, null, 2),
        "utf8",
      );
    }
    // The soak reports; it does not fail the build on a rate. Freezes are
    // findings, and the numbers are the deliverable.
  });
});
