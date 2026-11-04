/** Story trace — one full run, written down in the game's own words.
 *
 * ADR-0277 changed what the curated deck holds, and a balance table cannot say
 * whether the run *reads*. This plays one run with real key presses against
 * the real build, records every line the game prints, and writes the result to
 * `docs/design/jockey-identity-2026-11-04/story-trace.txt` so the narration can
 * be checked against something that actually happened.
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
import { test, type Page } from "@playwright/test";
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { gotoMenuOption } from "./menu-nav";

const JOCKEY = Number(process.env.STORY_JOCKEY ?? "0");
const MISSION = Number(process.env.STORY_MISSION ?? "0");
const MAX_STEPS = Number(process.env.STORY_MAX_STEPS ?? "400");
const OUT = fileURLToPath(
  new URL(
    "../../docs/design/jockey-identity-2026-11-04/story-trace.txt",
    import.meta.url,
  ),
);

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

/** NEW RUN → jockey → mission → launch. */
async function startRun(page: Page, jockey: number, mission: number): Promise<void> {
  await gotoMenuOption(page, "new_run");
  await page.keyboard.press("Enter");
  await page.waitForFunction(
    () =>
      ["jockey_select", "mission_select"].includes(
        (window as unknown as { wetrun: { getScreen(): string } }).wetrun.getScreen(),
      ),
    undefined,
    { timeout: 10000 },
  );
  await page.screenshot({
    path: fileURLToPath(
      new URL(
        "../../docs/design/jockey-identity-2026-11-04/00-jockey-select.png",
        import.meta.url,
      ),
    ),
  });
  for (let i = 0; i < jockey; i += 1) {
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(80);
  }
  await page.keyboard.press("Enter");
  await page.waitForFunction(
    () =>
      (window as unknown as { wetrun: { getScreen(): string } }).wetrun.getScreen() ===
      "mission_select",
    undefined,
    { timeout: 10000 },
  );
  for (let i = 0; i < mission; i += 1) {
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(80);
  }
  await page.keyboard.press("Enter");
  await page.waitForFunction(
    () =>
      (window as unknown as { wetrun: { state?: { runPhase?: string } | null } }).wetrun
        .state?.runPhase === "matrix",
    undefined,
    { timeout: 10000 },
  );
}

test.describe("story trace", () => {
  test.skip(!process.env.STORY, "story trace runs only via `npm run story`");
  test.setTimeout(0);

  test("plays one run and writes down every line", async ({ page }) => {
    await page.addInitScript(() =>
      localStorage.setItem("wetrun_tutorial_completed", "true"),
    );
    await page.goto("./");
    await page.waitForFunction(
      () => (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
    );

    await startRun(page, JOCKEY, MISSION);

    const lines: string[] = [];
    const shots = new Set<string>();
    let step = 0;
    let lastMsg = "";
    let lastPhase = "";
    let ending: string | null = null;
    let summary = "";

    /** One still per beat, so the narration can be checked against a frame. */
    const shoot = async (name: string): Promise<void> => {
      if (shots.has(name)) return;
      shots.add(name);
      await page.screenshot({
        path: fileURLToPath(
          new URL(
            `../../docs/design/jockey-identity-2026-11-04/${name}.png`,
            import.meta.url,
          ),
        ),
      });
    };

    await shoot("01-run-intro");

    for (; step < MAX_STEPS; step += 1) {
      const s = await snap(page);
      const st = s.state;

      if (st === null && s.screen === "menu") break;

      if (st !== null) {
        const phase = `${st.runPhase}/${st.phase}`;
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
        if (st.runPhase === "ending") {
          ending = st.ending;
          summary = `mission ${st.mission} · arc ${st.arc} · HP ${st.hp}/${st.maxHp} · ${st.credits}cr earned (base ${st.baseCredits}) · ${st.turn} turns`;
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
      "",
    ];
    writeFileSync(OUT, [...header, ...lines, ""].join("\n"), "utf-8");
    // eslint-disable-next-line no-console
    console.log(`STORY ending=${ending ?? "none"} steps=${step} lines=${lines.length} -> ${OUT}`);
  });
});
