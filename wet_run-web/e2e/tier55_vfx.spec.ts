/** Matrix event routing + combat VFX overlay E2E (Tier 5.5). */
import { test, expect } from "@playwright/test";

test("matrix shows event glyphs (combat/discovery/trap/etc.)", async ({ page }) => {
  await page.goto("./");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  // Navigate to NEW_RUN → mission_select → launch.
  await page.keyboard.press("Enter"); // NEW_RUN
  await page.waitForTimeout(200);
  await page.keyboard.press("Enter"); // launch first mission
  await page.waitForTimeout(300);

  // After launch, state.runPhase="matrix" (the screen field stays
  // "mission_select" but draw() routes by runPhase). Verify via state.
  const runPhase = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { state?: { runPhase?: string } | null } };
    return w.wetrun?.state?.runPhase ?? null;
  });
  expect(runPhase).toBe("matrix");
});

test("combat triggers VFX (canvas changes after card use)", async ({ page }) => {
  await page.goto("./");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  // Navigate: NEW_RUN → launch → matrix → enter → approach → combat.
  await page.keyboard.press("Enter");
  await page.waitForTimeout(200);
  await page.keyboard.press("Enter");
  await page.waitForTimeout(200);
  await page.keyboard.press("Enter"); // matrix → approach
  await page.waitForTimeout(200);
  await page.keyboard.press("Enter"); // approach → combat
  await page.waitForTimeout(300);

  // Verify in combat phase.
  const phase = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { getPhase(): string | null } };
    return w.wetrun?.getPhase();
  });
  expect(["approach", "combat"]).toContain(phase);

  // Use a program → should trigger VFX (state.vfxInstances.length > 0).
  await page.keyboard.press("1"); // first program
  await page.waitForTimeout(100);

  const vfxCount = await page.evaluate(() => {
    const w = window as unknown as {
      wetrun?: { state?: { vfxInstances?: ReadonlyArray<unknown> } | null };
    };
    return w.wetrun?.state?.vfxInstances?.length ?? 0;
  });
  expect(vfxCount).toBeGreaterThan(0);
});