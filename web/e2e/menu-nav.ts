import type { Page } from "@playwright/test";

/** Resolve a menu option's live index and walk to it. Position-independent:
 *  hardcoded ArrowDown counts broke when FAR GRID et al. were inserted. */
export async function gotoMenuOption(page: Page, key: string): Promise<void> {
  const nav = await page.evaluate((k: string) => {
    const w = window as unknown as {
      wetrun?: { getMenuOptionKeys(): string[]; getSelectedMenuIndex(): number };
    };
    const keys = w.wetrun?.getMenuOptionKeys?.() ?? [];
    const cur = w.wetrun?.getSelectedMenuIndex?.() ?? 0;
    return { idx: keys.indexOf(k), cur, len: keys.length };
  }, key);
  if (nav.idx < 0 || nav.len === 0) throw new Error(`menu option not found: ${key}`);
  const downs = (nav.idx - nav.cur + nav.len) % nav.len;
  for (let i = 0; i < downs; i += 1) {
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(120);
  }
}

/** Press Enter until a phase predicate holds (absorbs CI-load latency).
 *  Matches either getPhase() or state.runPhase: launch lands in runPhase
 *  "matrix" while getPhase() already reports "approach". */
export async function enterForPhase(page: Page, want: string, tries = 6): Promise<void> {
  // getPhase()-only on purpose: runPhase leads by one confirm (node entry
  // sets runPhase combat while getPhase stays approach), so an OR-probe
  // false-positives here. Use enterForRunPhase for entry steps.
  const probe = (w: string) => {
    const h = window as unknown as { wetrun?: { getPhase(): string | null } };
    return h.wetrun?.getPhase?.() === w;
  };
  for (let i = 0; i < tries; i += 1) {
    if (await page.evaluate(probe, want)) return;
    await page.keyboard.press("Enter");
    try {
      await page.waitForFunction(probe, want, { timeout: 2500 });
      return;
    } catch {
      // Transition not yet visible — retry the keypress.
    }
  }
  throw new Error(`enterForPhase: phase ${want} not reached`);
}

/** Walk the matrix to an ICE-bearing node, then Enter into combat.
 *  Node 0 is not guaranteed to hold an encounter — Blind Enters stall
 *  with "No ICE here". Follows adjacent[0] forward, capped. Note the
 *  two-track phase model: entering a node sets runPhase "combat" while
 *  getPhase() stays "approach" until a second confirm engages — so this
 *  helper Enters twice (entry, then engage). */
export async function gotoIceNode(page: Page): Promise<void> {
  for (let i = 0; i < 30; i += 1) {
    const hasIce = await page.evaluate(() => {
      const w = window as unknown as {
        wetrun?: { state?: { matrix?: { nodes?: Array<{ iceIds?: unknown[] }> } | null; currentNodeIndex?: number } | null };
      };
      const s = w.wetrun?.state;
      const n = s?.matrix?.nodes?.[s?.currentNodeIndex ?? -1];
      return (n?.iceIds?.length ?? 0) > 0;
    });
    if (hasIce) break;
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(150);
    if (i === 29) throw new Error("gotoIceNode: no ICE node reached in 30 moves");
  }
  await enterForRunPhase(page, "combat");
  await enterForPhase(page, "combat");
}

/** Press Enter until runPhase matches (matrix/combat entry live in
 *  runPhase while getPhase() lags one action behind). */
export async function enterForRunPhase(page: Page, want: string, tries = 6): Promise<void> {
  const probe = (w: string) => {
    const h = window as unknown as {
      wetrun?: { state?: { runPhase?: string } | null };
    };
    return h.wetrun?.state?.runPhase === w;
  };
  for (let i = 0; i < tries; i += 1) {
    if (await page.evaluate(probe, want)) return;
    await page.keyboard.press("Enter");
    try {
      await page.waitForFunction(probe, want, { timeout: 2500 });
      return;
    } catch {
      // Transition not yet visible — retry the keypress.
    }
  }
  throw new Error(`enterForRunPhase: runPhase ${want} not reached`);
}
export async function enterForScreen(page: Page, want: string, tries = 6): Promise<void> {
  const probe = (w: string) => {
    const h = window as unknown as { wetrun?: { getScreen(): string } };
    return h.wetrun?.getScreen?.() === w;
  };
  for (let i = 0; i < tries; i += 1) {
    if (await page.evaluate(probe, want)) return;
    await page.keyboard.press("Enter");
    try {
      await page.waitForFunction(probe, want, { timeout: 2500 });
      return;
    } catch {
      // Transition not yet visible — retry the keypress.
    }
  }
  throw new Error(`enterForScreen: screen ${want} not reached`);
}
