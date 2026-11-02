/** ADR-0252 — the autosave reflects committed state, and a finished run ends.
 *
 * Owner: "맵에서 보스를 쓰러뜨린후 이동하려니 또 보스가 나와서 회복 못하고
 * 패배하게 되던데." Boot mission Aleph Fragment: 0 → 25 → 16 → 18 (ICE) →
 * 20 (boss; its only exit is 18).
 *
 * Input is real keys throughout. The one assist: after BREACH the ICE are
 * left on 1 HP before the first program key, so a win does not depend on
 * the combat dice (the save timing is what is under test, not the fight).
 * The autosave is read straight from IndexedDB and decoded here.
 */
import { expect, test, type Page } from "@playwright/test";
import LZString from "lz-string";
import { gotoMenuOption } from "./menu-nav";

interface Snap {
  readonly runPhase: string;
  readonly phase: string;
  readonly cur: number;
  readonly hp: number;
  readonly credits: number;
  readonly cleared: readonly number[];
  readonly decision: string | null;
  readonly selected: number | null;
}
interface Slot {
  readonly currentNodeIndex?: number;
  readonly clearedEncounterNodes?: readonly number[];
  readonly playerHp: number;
  readonly playerCredits: number;
}
interface Hook {
  state: {
    runPhase: string;
    phase: string;
    currentNodeIndex: number;
    selectedMatrixNodeIndex?: number | null;
    encounterDecision?: { selectedVerb: string | null } | null;
    player: { hp: number; credits: number };
    clearedEncounterNodes?: number[];
    iceRoster: Array<{ hp: number }>;
    deck: unknown[];
  } | null;
  getScreen(): string;
  getPhase(): string | null;
}
const hook = (): Hook => (window as unknown as { wetrun: Hook }).wetrun;

async function snap(page: Page): Promise<Snap | null> {
  return page.evaluate(() => {
    const s = (window as unknown as { wetrun: Hook }).wetrun.state;
    if (!s) return null;
    return {
      runPhase: s.runPhase,
      phase: s.phase,
      cur: s.currentNodeIndex,
      hp: s.player.hp,
      credits: s.player.credits,
      cleared: s.clearedEncounterNodes ?? [],
      decision: s.encounterDecision ? (s.encounterDecision.selectedVerb ?? "open") : null,
      selected: s.selectedMatrixNodeIndex ?? null,
    };
  });
}

/** The autosave slot exactly as stored (IndexedDB `slots` / `slot_0`). */
async function readSlot(page: Page): Promise<Slot | null> {
  const raw = await page.evaluate(
    () =>
      new Promise<string | null>((resolve) => {
        const req = indexedDB.open("wetrun_save_v1");
        req.onsuccess = () => {
          const db = req.result;
          if (!db.objectStoreNames.contains("slots")) {
            db.close();
            resolve(null);
            return;
          }
          const get = db.transaction("slots", "readonly").objectStore("slots").get("slot_0");
          get.onsuccess = () => {
            db.close();
            const v = get.result as { json?: string } | undefined;
            resolve(v?.json ?? null);
          };
          get.onerror = () => {
            db.close();
            resolve(null);
          };
        };
        req.onerror = () => resolve(null);
      }),
  );
  if (raw === null) return null;
  const env = JSON.parse(raw) as { v?: number; c?: boolean; d?: string };
  const json = env.v === 2 ? (env.c ? LZString.decompressFromEncodedURIComponent(env.d ?? "") : env.d) : raw;
  return JSON.parse(json ?? "null") as Slot | null;
}

async function travel(page: Page, to: number): Promise<void> {
  for (let i = 0; i < 8; i += 1) {
    if ((await snap(page))?.selected === to) break;
    await page.keyboard.press("ArrowDown");
  }
  expect((await snap(page))?.selected).toBe(to);
  await page.keyboard.press("Enter");
  await expect.poll(async () => (await snap(page))?.cur).toBe(to);
}

async function breachAndWin(page: Page): Promise<void> {
  for (let i = 0; i < 6; i += 1) {
    const verb = await page.evaluate(() => (window as unknown as { wetrun: Hook }).wetrun.state?.encounterDecision?.selectedVerb);
    if (verb === "BREACH") break;
    await page.keyboard.press("ArrowDown");
  }
  await page.keyboard.press("Enter");
  await expect.poll(async () => (await snap(page))?.runPhase).toBe("combat");
  await page.keyboard.press("Enter");
  await expect.poll(async () => (await snap(page))?.phase).toBe("combat");
  for (let i = 0; i < 20 && (await snap(page))?.runPhase === "combat"; i += 1) {
    await page.evaluate(() => {
      const game = (window as unknown as { wetrun: Hook }).wetrun;
      const s = game.state;
      if (!s) return;
      game.state = { ...s, iceRoster: s.iceRoster.map((ice) => ({ ...ice, hp: Math.min(ice.hp, 1) })) };
    });
    for (let row = 1; row <= 5 && (await snap(page))?.runPhase === "combat"; row += 1) {
      await page.keyboard.press(String(row));
    }
  }
  await expect.poll(async () => (await snap(page))?.runPhase).toBe("loot");
}

async function launch(page: Page): Promise<void> {
  await page.addInitScript(() => {
    localStorage.setItem("wetrun_tutorial_completed", "true");
    localStorage.setItem("wetrun_reduced_motion", "1");
  });
  await page.goto("./");
  await page.waitForFunction(() => (window as unknown as { wetrun?: Hook }).wetrun !== undefined);
  await page.evaluate(
    () =>
      new Promise<void>((resolve) => {
        const q = indexedDB.deleteDatabase("wetrun_save_v1");
        q.onsuccess = q.onerror = q.onblocked = () => resolve();
      }),
  );
  await page.reload();
  await page.waitForFunction(() => (window as unknown as { wetrun?: Hook }).wetrun !== undefined);
  await page.waitForTimeout(300);
  await gotoMenuOption(page, "new_run");
  await page.keyboard.press("Enter");
  await expect.poll(() => page.evaluate(() => (window as unknown as { wetrun: Hook }).wetrun.getScreen())).toBe("mission_select");
  await page.keyboard.press("Enter");
  await expect.poll(async () => (await snap(page))?.runPhase).toBe("matrix");
}

test("a committed move is in the next autosave", async ({ page }) => {
  await launch(page);
  await travel(page, 25);
  await expect.poll(async () => (await readSlot(page))?.currentNodeIndex, { timeout: 5000 }).toBe(25);
});

test("a combat win is in the autosave: cleared node, HP, credits", async ({ page }) => {
  await launch(page);
  for (const to of [25, 16, 18]) await travel(page, to);
  await breachAndWin(page);
  const live = await snap(page);
  expect(live?.cleared).toContain(18);
  await expect
    .poll(async () => {
      const slot = await readSlot(page);
      return slot && { cleared: slot.clearedEncounterNodes, hp: slot.playerHp, credits: slot.playerCredits };
    }, { timeout: 5000 })
    .toEqual({ cleared: [18], hp: live?.hp, credits: live?.credits });
});

test("the ending returns to the title, ends the run, and CONTINUE cannot reopen it", async ({ page }) => {
  await launch(page);
  for (const to of [25, 16, 18]) await travel(page, to);
  await breachAndWin(page);
  await page.keyboard.press("Enter"); // loot → route selection
  await expect.poll(async () => (await snap(page))?.runPhase).toBe("matrix");
  await travel(page, 20);
  expect((await snap(page))?.decision).toBe("open");
  await breachAndWin(page);
  await page.keyboard.press("Enter"); // boss loot → ending
  await expect.poll(async () => (await snap(page))?.runPhase).toBe("ending");
  // Reaching the ending retires the autosave.
  await expect.poll(() => readSlot(page), { timeout: 5000 }).toBeNull();
  await page.keyboard.press("Enter");
  await expect.poll(() => page.evaluate(() => (window as unknown as { wetrun: Hook }).wetrun.getScreen())).toBe("menu");
  expect(await snap(page)).toBeNull();
  // No input reaches the ending afterwards.
  for (const k of ["Escape", "ArrowDown", "ArrowUp"]) {
    await page.keyboard.press(k);
    expect(await snap(page)).toBeNull();
  }
  // Reload: CONTINUE offers nothing.
  await page.reload();
  await page.waitForFunction(() => (window as unknown as { wetrun?: Hook }).wetrun !== undefined);
  await page.waitForTimeout(500);
  expect(await readSlot(page)).toBeNull();
  await gotoMenuOption(page, "continue");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(500);
  expect(await page.evaluate(() => (window as unknown as { wetrun: Hook }).wetrun.getScreen())).toBe("menu");
  expect(await snap(page)).toBeNull();
});
