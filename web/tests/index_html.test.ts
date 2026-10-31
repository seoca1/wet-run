/** Static-shell tests for `web/index.html` (UI triage V4).
 *
 * `#status-overlay` was a fixed top-right box with a green border that no
 * code in `src/` ever wrote to, so it always rendered as an empty frame.
 * It was removed together with its CSS; these assertions guard against it
 * coming back without a consumer.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const indexHtml = readFileSync(
  fileURLToPath(new URL("../index.html", import.meta.url)),
  "utf-8",
);

describe("index.html static shell", () => {
  it("has no #status-overlay element", () => {
    expect(indexHtml).not.toContain('id="status-overlay"');
  });

  it("has no #status-overlay CSS rule", () => {
    expect(indexHtml).not.toContain("#status-overlay");
  });

  it("keeps the live elements that src/ still uses", () => {
    expect(indexHtml).toContain('id="game-canvas"');
    expect(indexHtml).toContain('id="gamepad-status"');
    expect(indexHtml).toContain('id="loading"');
  });
});
