/** Story trace — one full run, written down in the game's own words.
 *
 * ADR-0277 changed what the curated deck holds, and a balance table cannot say
 * whether the run *reads*. This plays one run with real key presses against
 * the real build and records every line the game prints.
 *
 * Output goes to `web/test-results/story/` (gitignored). It used to overwrite
 * five tracked files under `docs/design/`, so every run dirtied the tree; and
 * because the page's `Math.random` was unseeded, a fresh capture never matched
 * the committed one (the same cell came out 53/60/58 steps on three runs).
 *
 * Rules it holds itself to (same as the soak, ADR-0265):
 *   - real keys only; it never writes `wetrun.state`.
 *   - one run, one policy: the most expensive affordable program, BREACH over
 *     BYPASS, take the first reward. That is a plausible player, not an
 *     optimiser, so the trace is a story rather than a best case.
 *
 * Run it:
 *   npm run story
 */
import { test, expect, type Page } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { enterForScreen, gotoMenuOption } from "./menu-nav";
import { ENDINGS } from "../src/core/combat/ending_resolver";
import missionsJson from "../src/data/missions.json" with { type: "json" };

/** The easiest Sprawl mission's index in the board order the trace walks.
 * The board lists sprawl-universe missions only (ADR-0213), in catalog order. */
const EASIEST_MISSION: number = (() => {
  const all = Object.values(
    missionsJson as Record<string, { id?: string; grade_max?: number; source_universe?: string }>,
  ).filter((m) => m.source_universe !== "far-grid");
  const lowest = Math.min(...all.map((m) => m.grade_max ?? 99));
  const at = all.findIndex((m) => (m.grade_max ?? 99) === lowest);
  return at < 0 ? 0 : at;
})();

const JOCKEY = Number(process.env.STORY_JOCKEY ?? "0");
/** The easiest Sprawl mission, unless told otherwise.
 *
 * The default used to be index 0, which is `aleph_fragment` (grade 5) — a
 * mission a new player cannot pick. The trace's job is to show what a plausible
 * run reads like, and a grade-5 run mostly reads like a flatline: the run ended
 * on the defeat screen and never reached the ending, so the ending's beats were
 * never exercised. The easiest mission is what the first mission actually is. */
const MISSION = Number(process.env.STORY_MISSION ?? String(EASIEST_MISSION));
const MAX_STEPS = Number(process.env.STORY_MAX_STEPS ?? "400");
const SEED = Number(process.env.STORY_SEED ?? "20261108");
const OUT_DIR = fileURLToPath(new URL("../story-out/", import.meta.url));
const OUT = join(OUT_DIR, "story-trace.txt");


/** Install a seeded `Math.random` in the page before it boots. The game draws
 * combat dice from `Math.random`, and only the headless harnesses replace it. */
async function seedMathRandom(page: Page, seed: number): Promise<void> {
  await page.addInitScript((s: number) => {
    let a = s >>> 0;
    Math.random = () => {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }, seed);
}

type NodeMeta = { readonly adj: readonly number[]; readonly ice: number; readonly boss: boolean };

type Snap = {
  readonly screen: string;
  readonly state: {
    readonly runPhase: string;
    readonly phase: string;
    readonly cur: number;
    readonly sel: number | null;
    readonly hp: number;
    readonly maxHp: number;
    readonly alarm: number;
    readonly turn: number;
    readonly deck: readonly { readonly id: string; readonly tier: number; readonly cost: number }[];
    readonly ice: readonly number[];
    readonly nodes: readonly NodeMeta[];
    readonly visited: readonly number[];
    readonly cleared: readonly number[];
    readonly bypassed: readonly number[];
    readonly msg: string;
    readonly log: readonly string[];
    readonly taken: string | null;
    readonly verb: string | null;
    readonly decision: boolean;
    readonly mission: string;
    readonly arc: number;
    readonly ending: string | null;
    readonly credits: number;
    readonly baseCredits: number;
  } | null;
};

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
      player: { hp: number; maxHp: number; alarm: number; credits: number };
      turnCount: number;
      deck: { id: string; tier?: number; cost?: number }[];
      iceRoster: { hp: number }[];
      matrix?: {
        nodes: { adjacent: number[]; iceIds?: string[]; isBoss?: boolean }[];
      };
      message: string;
      combatLog?: string[];
      cardRewardTaken?: string | null;
      encounterDecision?: { selectedVerb: string | null } | null;
      visitedNodes?: number[];
      clearedEncounterNodes?: number[];
      bypassedEncounterNodes?: number[];
      mission?: { id?: string; title?: string; arc?: number; grade_max?: number };
      endingChoice?: string | null;
      inventory?: { credits?: number };
    };
    return {
      screen: w.wetrun.getScreen(),
      state: {
        runPhase: st.runPhase,
        phase: st.phase,
        cur: st.currentNodeIndex,
        sel: st.selectedMatrixNodeIndex ?? null,
        hp: st.player.hp,
        maxHp: st.player.maxHp,
        alarm: st.player.alarm,
        turn: st.turnCount,
        deck: st.deck.map((p) => ({
          id: p.id,
          tier: p.tier ?? 0,
          cost: p.cost ?? 0,
        })),
        ice: st.iceRoster.map((i) => i.hp),
        nodes: (st.matrix?.nodes ?? []).map((n) => ({
          adj: n.adjacent,
          ice: n.iceIds?.length ?? 0,
          boss: n.isBoss === true,
        })),
        visited: st.visitedNodes ?? [],
        cleared: st.clearedEncounterNodes ?? [],
        bypassed: st.bypassedEncounterNodes ?? [],
        msg: /^TRACE \d+\/\d+$/.test(st.message) ? "(trace)" : st.message,
        // The combat log is the record of what actually happened — `message`
        // is only the newest line, so a trace that reads only `message`
        // misses everything that came before it.
        log: st.combatLog ?? [],
        taken: st.cardRewardTaken ?? null,
        verb: st.encounterDecision?.selectedVerb ?? null,
        decision: st.encounterDecision != null,
        mission: st.mission?.title ?? st.mission?.id ?? "?",
        arc: st.mission?.arc ?? 0,
        ending: st.endingChoice ?? null,
        credits: st.player.credits,
        baseCredits: st.inventory?.credits ?? 0,
      },
    };
  });
}

async function press(page: Page, key: string): Promise<void> {
  await page.keyboard.press(key);
  await page.waitForTimeout(18);
}

function hasBusiness(st: NonNullable<Snap["state"]>, i: number): boolean {
  const n = st.nodes[i];
  if (!n) return false;
  if (st.cleared.includes(i) || st.bypassed.includes(i)) return false;
  return n.ice > 0 || n.boss;
}

function nextHop(st: NonNullable<Snap["state"]>): number {
  const prev = new Map<number, number>();
  const queue: number[] = [st.cur];
  const seen = new Set<number>([st.cur]);
  while (queue.length > 0) {
    const at = queue.shift() as number;
    if (at !== st.cur && hasBusiness(st, at)) {
      let step = at;
      while ((prev.get(step) ?? st.cur) !== st.cur) step = prev.get(step) as number;
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
  return pool.length === 0 ? st.cur : (pool[0] as number);
}

/** NEW RUN → jockey → prologue → mission list → briefing → prep → run.
 *
 * This used to hand-roll the walk and fell behind twice: the prologue (ADR-0317
 * step 2) and the briefing (step 3a) both landed between the screens it named,
 * so the trace timed out — and nobody saw it, because the spec is skipped
 * unless `STORY` is set. It walks the shared helpers now, which is the only
 * version of this that cannot drift again. */
async function startRun(page: Page, jockey: number, mission: number): Promise<void> {
  await gotoMenuOption(page, "new_run");
  await page.keyboard.press("Enter");
  await enterForScreen(page, "jockey_select");
  await page.screenshot({ path: join(OUT_DIR, "00-jockey-select.png") });
  for (let i = 0; i < jockey; i += 1) {
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(80);
  }
  await page.keyboard.press("Enter");
  // ADR-0317 step 2: the jockey's prologue opens the run. ESC skips the STORY,
  // not the run — the same door a player uses.
  await enterForScreen(page, "graphic_novel");
  await page.keyboard.press("Escape");
  await enterForScreen(page, "mission_select");
  for (let i = 0; i < mission; i += 1) {
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(80);
  }
  await page.keyboard.press("Enter");
  // ADR-0317 step 3a: the fixer briefs the job before the advance.
  await enterForScreen(page, "briefing");
  await page.keyboard.press("Enter");
  await enterForScreen(page, "prep");
  await page.keyboard.press("Enter");
  await page.waitForFunction(
    () =>
      (window as unknown as { wetrun: { state?: { runPhase?: string } | null } }).wetrun
        .state?.runPhase === "matrix",
    undefined,
    { timeout: 10000 },
  );
}

/** The beat card on screen, or null. Display-only, so it never moves `state`. */
async function beatCard(page: Page) {
  return page.evaluate(() => {
    const w = window as unknown as {
      wetrun?: { getBeatCard?(): { title: string; lines: string[] } | null };
    };
    return w.wetrun?.getBeatCard?.() ?? null;
  });
}

/** The run's opening beat, or null (ADR-0317 3b). */
async function runIntroBeat(page: Page) {
  return page.evaluate(() => {
    const w = window as unknown as {
      wetrun?: { getRunIntroBeat?(): { speaker: string; lines: string[] } | null };
    };
    return w.wetrun?.getRunIntroBeat?.() ?? null;
  });
}

test.describe("story trace", () => {
  // ADR-0317 (3b): this used to be skipped unless `STORY` was set, and that is
  // exactly why it drifted — two new screens landed between the screens its
  // driver named and nothing noticed. It runs in the suite now; on the easiest
  // mission it is a few seconds, and its assertions are what the narrative
  // wiring is verified by. `npm run story` still works for the verbose file.
  test.setTimeout(180_000);

  test("plays one run and writes down every line", async ({ page }) => {
    mkdirSync(OUT_DIR, { recursive: true });
    await page.addInitScript(() =>
      localStorage.setItem("wetrun_tutorial_completed", "true"),
    );
    await seedMathRandom(page, SEED);
    await page.goto("./");
    await page.waitForFunction(
      () => (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
    );

    await startRun(page, JOCKEY, MISSION);

    const lines: string[] = [];
    const shots = new Set<string>();
    const beatsSeen = new Set<string>();
    let signoffSeen = false;
    // What the run actually reached. The beat assertions are conditional on
    // these, so a balance change that makes the run lose does not read as a
    // broken narrative trigger.
    let enteredCombat = false;
    let sawLoot = false;
    let step = 0;
    let lastMsg = "";
    let lastPhase = "";
    let ending: string | null = null;
    let summary = "";
    // The combat log is newest-first and capped, so the trace records each
    // line once, in the order it was written.
    const logged = new Set<string>();

    /** One still per beat, so the narration can be checked against a frame. */
    const shoot = async (name: string): Promise<void> => {
      if (shots.has(name)) return;
      shots.add(name);
      await page.screenshot({ path: join(OUT_DIR, `${name}.png`) });
    };

    await shoot("01-run-intro");
    // ADR-0317 (3b): the run's opening beat is the migration's headline, so the
    // trace asserts it exists rather than only screenshotting the card.
    const introBeat = await runIntroBeat(page);
    expect(
      introBeat,
      "the run's opening beat never appeared",
    ).not.toBeNull();
    lines.push(`[0] run intro beat: ${introBeat?.speaker ?? "?"}`);

    for (; step < MAX_STEPS; step += 1) {
      const s = await snap(page);
      const st = s.state;

      if (st === null && s.screen === "menu") break;

      // ADR-0317 (3b): a mid-run beat card owns the screen until a key. Record
      // it and dismiss it — that is what a player does, and skipping it here is
      // how a beat could stop reaching the player without anyone noticing.
      const card = await beatCard(page);
      if (card !== null) {
        beatsSeen.add(card.title);
        lines.push(`[${step}] beat card "${card.title}"`);
        for (const line of card.lines) lines.push(`      beat: ${line}`);
        await press(page, "Enter");
        continue;
      }

      // ADR-0318 (a): legs 2+ open with the fixer's advance. Take it — it is
      // what a player does, and it eats a key the trace would spend on the
      // board.
      if (
        (await page.evaluate(
          () =>
            (window as unknown as { wetrun: { getScreen(): string } }).wetrun.getScreen(),
        )) === "contract_prep"
      ) {
        lines.push(`[${step}] between-leg advance`);
        await press(page, "Enter");
        continue;
      }
      if (st !== null) {
        const phase = `${st.runPhase}/${st.phase}`;
        if (st.runPhase === "combat" && st.phase === "combat") enteredCombat = true;
        if (st.runPhase === "loot") sawLoot = true;
        const ice = st.ice.reduce((a, b) => a + b, 0);
        if (
          process.env.STORY_VERBOSE === "1" ||
          st.msg !== lastMsg ||
          phase !== lastPhase
        ) {
          const hand = st.deck.map((p) => `${p.id}+${p.cost}`).join(" ");
          lines.push(
            [
              `[${step}] ${phase} @node${st.cur}`,
              `HP ${st.hp}/${st.maxHp} COST ${st.alarm} T${st.turn}`,
              ice > 0 ? `ICE ${ice}` : "",
              `hand ${hand || "(empty)"}`,
              `"${st.msg}"`,
            ]
              .filter(Boolean)
              .join(" | "),
          );
          lastMsg = st.msg;
          lastPhase = phase;
        }
        // Combat log lines, oldest first, each written once.
        for (const entry of [...st.log].reverse()) {
          if (logged.has(entry)) continue;
          logged.add(entry);
          lines.push(`      log: ${entry}`);
        }
        if (st.runPhase === "ending") {
          ending = st.ending;
          summary = `mission ${st.mission} · arc ${st.arc} · HP ${st.hp}/${st.maxHp} · ${st.credits}cr earned (base ${st.baseCredits}) · ${st.turn} turns`;
          // ADR-0317 (3b): the construct's last word lives on this screen.
          if (!signoffSeen) {
            const signoff = await page.evaluate(() => {
              const w = window as unknown as {
                wetrun?: {
                  getEndingSignoff?(): { speaker: string; lines: string[] } | null;
                };
              };
              return w.wetrun?.getEndingSignoff?.() ?? null;
            });
            if (signoff !== null) {
              signoffSeen = true;
              lines.push(`[${step}] ending sign-off: ${signoff.speaker}`);
              for (const line of signoff.lines) lines.push(`      beat: ${line}`);
            }
          }
        }
        if (st.runPhase === "combat" && st.phase === "combat") await shoot("02-combat");
        if (st.runPhase === "loot") await shoot("03-loot");
        if (st.runPhase === "ending") await shoot("04-ending");
      }

      // The policy: a plausible player, not an optimiser.
      if (st === null) {
        await press(page, "Enter");
        continue;
      }
      if (st.runPhase === "ending" || st.runPhase === "dead") {
        // Read the ending, then leave it (that transition is what retires the
        // save slot and returns to the title).
        lines.push(`[${step}] ending screen: ${st.ending ?? "?"}`);
        await press(page, "Enter");
        continue;
      }
      if (st.runPhase === "loot") {
        const node = st.nodes[st.cur];
        const terminal = (node?.adj.length ?? 0) === 0 || node?.boss === true;
        if (st.taken === null && !terminal) await press(page, "1");
        else await press(page, "Enter");
        continue;
      }
      if (st.runPhase === "matrix" && st.decision) {
        for (let i = 0; i < 8; i += 1) {
          if ((await snap(page)).state?.verb === "BREACH") break;
          await press(page, "ArrowDown");
        }
        await press(page, "Enter");
        continue;
      }
      if (st.runPhase === "matrix") {
        const target = nextHop(st);
        if (target !== st.cur) {
          const adj = st.nodes[st.cur]?.adj ?? [];
          for (let i = 0; i < adj.length + 1; i += 1) {
            if ((await snap(page)).state?.sel === target) break;
            await press(page, "ArrowDown");
          }
        }
        await press(page, "Enter");
        continue;
      }
      if (st.runPhase === "combat" && st.phase === "combat") {
        const affordable = st.deck
          .map((p, i) => ({ ...p, slot: i + 1 }))
          .filter((p) => st.alarm + p.cost <= 100)
          .sort((a, b) => b.tier - a.tier || a.cost - b.cost);
        if (affordable.length === 0) await press(page, "Enter");
        else await press(page, String((affordable[0] as { slot: number }).slot));
        continue;
      }
      await press(page, "Enter");
    }

    const header = [
      "wet_run — one run, written down in the game's own words",
      `build: ${process.env.STORY_BUILD ?? "local dist"}`,
      `jockey index ${JOCKEY}, mission index ${MISSION}`,
      `steps: ${step}`,
      `ending: ${ending ?? "(none reached)"}`,
      `summary: ${summary || "(none)"}`,
      `beats: ${[...beatsSeen].join(", ") || "(none)"}${signoffSeen ? ", ending sign-off" : ""}`,
      "",
    ];
    writeFileSync(OUT, [...header, ...lines, ""].join("\n"), "utf-8");

    // ADR-0317 (3b): the beats are the point of the migration, so the trace
    // asserts they reached the player — but only for the states the run actually
    // reached, so a balance change that ends the run early reads as a short run
    // rather than a broken trigger.
    if (enteredCombat) {
      expect(
        beatsSeen,
        "the run fought but the first-fight warning never reached the player",
      ).toContain("ICE AHEAD");
    }
    if (sawLoot) {
      expect(
        beatsSeen,
        "the run won a fight but the first-victory beat never reached the player",
      ).toContain("FIRST BLOOD");
    }
    if (ending !== null) {
      expect(
        signoffSeen,
        "the run reached the ending but the sign-off never reached the player",
      ).toBe(true);
      // ADR-0315 slice 2 + ADR-0318: the run is a contract, and the ending
      // screen is only reachable once that contract is finished. So the ending
      // must be a liberation — whatever the run earned. A campaign that ends on
      // "you got rich" means the resolver's order went back the wrong way.
      const category = ENDINGS.find((e) => e.id === ending)?.category;
      expect(
        category,
        `a finished contract ended on ${ending} (${category ?? "?"})`,
      ).toBe("liberation");
      expect(
        beatsSeen,
        "the contract never handed over a second mission",
      ).toContain("CONTRACT 2/3");
    }

    // eslint-disable-next-line no-console
    console.log(`STORY ending=${ending ?? "none"} steps=${step} lines=${lines.length} -> ${OUT}`);
  });
});
