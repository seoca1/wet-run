/** Storage quota helper tests (Tier 7).
 *
 * Verifies pure helper functions (formatBytes, renderUsageBar, quotaLevel,
 * summarizeQuota) and the async getStorageQuota() graceful-degradation
 * when navigator.storage.estimate() is unavailable (jsdom).
 */
import { describe, it, expect } from "vitest";
import {
  formatBytes,
  renderUsageBar,
  quotaLevel,
  summarizeQuota,
  getStorageQuota,
  STORAGE_QUOTA_WARNING_PERCENT,
  STORAGE_QUOTA_CRITICAL_PERCENT,
  type StorageQuota,
} from "../src/save/storage_quota.js";

describe("formatBytes", () => {
  it("returns '0 B' for zero or negative", () => {
    expect(formatBytes(0)).toBe("0 B");
    expect(formatBytes(-1)).toBe("0 B");
  });

  it("formats sub-KB as B", () => {
    expect(formatBytes(512)).toBe("512 B");
  });

  it("formats KB with 2 decimals under 10KB", () => {
    expect(formatBytes(2048)).toBe("2.00 KB");
  });

  it("formats KB with 1 decimal over 10KB", () => {
    expect(formatBytes(15360)).toBe("15.0 KB");
  });

  it("formats MB and GB", () => {
    expect(formatBytes(2 * 1024 * 1024)).toBe("2.00 MB");
    expect(formatBytes(3 * 1024 * 1024 * 1024)).toBe("3.00 GB");
  });

  it("handles NaN by returning 0 B", () => {
    expect(formatBytes(Number.NaN)).toBe("0 B");
  });
});

describe("renderUsageBar", () => {
  it("renders 20-cell bar default", () => {
    expect(renderUsageBar(0)).toBe("░".repeat(20));
    expect(renderUsageBar(100)).toBe("█".repeat(20));
  });

  it("renders partial fill correctly", () => {
    const bar = renderUsageBar(50);
    expect(bar).toBe("█".repeat(10) + "░".repeat(10));
    expect(bar.length).toBe(20);
  });

  it("clamps percent to [0, 100]", () => {
    expect(renderUsageBar(-10)).toBe("░".repeat(20));
    expect(renderUsageBar(150)).toBe("█".repeat(20));
  });

  it("supports custom width", () => {
    expect(renderUsageBar(50, 10)).toBe("█".repeat(5) + "░".repeat(5));
  });
});

describe("quotaLevel", () => {
  it("returns 'ok' below warning threshold", () => {
    expect(quotaLevel(0)).toBe("ok");
    expect(quotaLevel(STORAGE_QUOTA_WARNING_PERCENT - 1)).toBe("ok");
  });

  it("returns 'warning' at or above warning threshold", () => {
    expect(quotaLevel(STORAGE_QUOTA_WARNING_PERCENT)).toBe("warning");
    expect(quotaLevel(STORAGE_QUOTA_CRITICAL_PERCENT - 1)).toBe("warning");
  });

  it("returns 'critical' at or above critical threshold", () => {
    expect(quotaLevel(STORAGE_QUOTA_CRITICAL_PERCENT)).toBe("critical");
    expect(quotaLevel(100)).toBe("critical");
  });
});

describe("summarizeQuota", () => {
  it("formats ok state with usage / quota / percent", () => {
    const ok: StorageQuota = { state: "ok", usageBytes: 1024, quotaBytes: 10240, percent: 10 };
    expect(summarizeQuota(ok)).toBe("Storage: 1.00 KB / 10.0 KB (10%)");
  });

  it("formats unavailable state with reason", () => {
    const u: StorageQuota = { state: "unavailable", reason: "browser too old" };
    expect(summarizeQuota(u)).toBe("Storage: browser too old");
  });
});

describe("getStorageQuota (async, graceful degradation)", () => {
  /** Stub navigator.storage on the global for tests that need it.
   * Uses Object.defineProperty to bypass jsdom's read-only navigator. */
  function stubStorage(estimate: () => Promise<{ usage?: number; quota?: number }>): void {
    Object.defineProperty(globalThis, "navigator", {
      value: { storage: { estimate } },
      configurable: true,
      writable: true,
    });
  }

  function restoreNavigator(): void {
    Object.defineProperty(globalThis, "navigator", {
      value: undefined,
      configurable: true,
      writable: true,
    });
  }

  it("returns unavailable state in jsdom (no navigator.storage)", async () => {
    restoreNavigator();
    const result = await getStorageQuota();
    expect(result.state).toBe("unavailable");
    if (result.state === "unavailable") {
      expect(typeof result.reason).toBe("string");
      expect(result.reason.length).toBeGreaterThan(0);
    }
  });

  it("handles zero quota from browser", async () => {
    stubStorage(async () => ({ usage: 100, quota: 0 }));
    try {
      const result = await getStorageQuota();
      expect(result.state).toBe("unavailable");
    } finally {
      restoreNavigator();
    }
  });

  it("returns ok state when estimate returns valid numbers", async () => {
    stubStorage(async () => ({ usage: 1024, quota: 10240 }));
    try {
      const result = await getStorageQuota();
      expect(result.state).toBe("ok");
      if (result.state === "ok") {
        expect(result.usageBytes).toBe(1024);
        expect(result.quotaBytes).toBe(10240);
        expect(result.percent).toBe(10);
      }
    } finally {
      restoreNavigator();
    }
  });

  it("clamps percent to [0, 100] even with weird browser data", async () => {
    stubStorage(async () => ({ usage: 20000, quota: 10000 }));
    try {
      const result = await getStorageQuota();
      expect(result.state).toBe("ok");
      if (result.state === "ok") {
        expect(result.percent).toBeLessThanOrEqual(100);
      }
    } finally {
      restoreNavigator();
    }
  });

  it("catches estimate() rejection and returns unavailable", async () => {
    stubStorage(async () => {
      throw new Error("SecurityError");
    });
    try {
      const result = await getStorageQuota();
      expect(result.state).toBe("unavailable");
      if (result.state === "unavailable") {
        expect(result.reason).toContain("SecurityError");
      }
    } finally {
      restoreNavigator();
    }
  });
});
