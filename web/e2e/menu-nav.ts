import type { Page } from "@playwright/test";

/** Resolve a menu option's live index and walk to it. Position-independent:
 *  hardcoded ArrowDown counts broke when FAR GRID et al. were inserted. */
export async function gotoMenuOption(page: Page, key: string): Promise<void> {
  const nav = await page.evaluate(() => {
    const w = window as unknown as {
      wetrun?: { getMenuOptionKeys(): string[]; getSelectedMenuIndex(): number };
    };
    const keys = w.wetrun?.getMenuOptionKeys?.() ?? [];
    const cur = w.wetrun?.getSelectedMenuIndex?.() ?? 0;
    return { idx: keys.indexOf(key), cur, len: keys.length };
  });
  if (nav.idx < 0 || nav.len === 0) throw new Error(`menu option not found: ${key}`);
  const downs = (nav.idx - nav.cur + nav.len) % nav.len;
  for (let i = 0; i < downs; i += 1) {
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(120);
  }
}
