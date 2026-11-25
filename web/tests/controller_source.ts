/** The controller's source, as text, for the wiring tests.
 *
 * Several tests assert on source text rather than behaviour because `main.ts`
 * self-boots on import (see `tests/onboarding.test.ts`). After the 2026-11-25
 * refactoring stages, the controller is no longer one file: the input, render
 * and life-cycle layers moved to `src/app/`. Those tests read the whole
 * controller here instead of pinning one path, so a later move does not break
 * a wiring assertion that is still true.
 *
 * Returns the raw concatenation — each test applies its own normalization.
 */
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";

export function readControllerSource(): string {
  const mainPath = fileURLToPath(new URL("../src/main.ts", import.meta.url));
  const appDir = fileURLToPath(new URL("../src/app", import.meta.url));
  const parts = [readFileSync(mainPath, "utf-8")];
  for (const name of readdirSync(appDir).sort()) {
    if (name.endsWith(".ts")) parts.push(readFileSync(`${appDir}/${name}`, "utf-8"));
  }
  return parts.join("\n");
}
