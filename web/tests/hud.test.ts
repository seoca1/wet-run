/** `renderer/hud.ts` dead-code guard (UI triage X3).
 *
 * `renderHUD()` had no non-test caller; the live combat HUD is built by
 * `buildHudLines` in `core/state/state.ts`. It was deleted, so the module
 * must no longer export it.
 */
import { describe, it, expect } from "vitest";
import * as hud from "../src/renderer/hud";

describe("renderer/hud module", () => {
  it("no longer exports the dead renderHUD()", () => {
    expect(Object.keys(hud)).not.toContain("renderHUD");
  });

  it("still exports shouldRenderHUD()", () => {
    expect(typeof hud.shouldRenderHUD).toBe("function");
  });
});
