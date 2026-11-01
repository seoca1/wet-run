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

/** Select and confirm adjacent routes to an ICE node, then engage both phases. */
export async function gotoIceNode(page: Page): Promise<void> {
  for (let i = 0; i < 30; i += 1) {
    const route = await page.evaluate(() => {
      const w = window as unknown as {
        wetrun?: { state?: { matrix?: { nodes: Array<{ iceIds: string[]; adjacent: number[] }> } | null; currentNodeIndex: number } | null };
      };
      const s = w.wetrun?.state;
      if (!s?.matrix) throw new Error("gotoIceNode: missing matrix");
      const { nodes } = s.matrix;
      const start = s.currentNodeIndex;
      if (nodes[start]?.iceIds.length) return { hasIce: true, slot: -1 };
      const queue = [{ index: start, first: -1 }];
      const seen = new Set([start]);
      for (const entry of queue) {
        for (const next of nodes[entry.index]?.adjacent ?? []) {
          if (seen.has(next)) continue;
          seen.add(next);
          const first = entry.first < 0 ? next : entry.first;
          if (nodes[next]?.iceIds.length) {
            return { hasIce: false, slot: nodes[start]?.adjacent.indexOf(first) ?? -1 };
          }
          queue.push({ index: next, first });
        }
      }
      throw new Error("gotoIceNode: no reachable ICE");
    });
    if (route.hasIce) break;
    if (route.slot < 0) throw new Error("gotoIceNode: route is not adjacent");
    for (let selection = 0; selection <= route.slot; selection += 1) {
      await page.keyboard.press("ArrowDown");
    }
    await page.keyboard.press("Enter");
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
