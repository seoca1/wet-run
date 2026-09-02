import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { join } from "path";

describe("PWA service worker", () => {
  it("sw.js exists in public directory", () => {
    const swPath = join(import.meta.dirname, "../public/sw.js");
    const swContent = readFileSync(swPath, "utf-8");
    expect(swContent).toContain("CACHE_NAME");
    expect(swContent).toContain("addEventListener");
  });

  it("manifest.json is valid PWA manifest", () => {
    const manifestPath = join(import.meta.dirname, "../public/manifest.json");
    const manifest = JSON.parse(readFileSync(manifestPath, "utf-8"));
    expect(manifest.name).toBeDefined();
    expect(manifest.short_name).toBeDefined();
    expect(manifest.display).toBe("standalone");
    expect(manifest.icons).toBeDefined();
    expect(manifest.icons.length).toBeGreaterThan(0);
  });

  it("index.html registers service worker", () => {
    const htmlPath = join(import.meta.dirname, "../index.html");
    const html = readFileSync(htmlPath, "utf-8");
    expect(html).toContain("serviceWorker");
    expect(html).toContain("sw.js");
  });
});
