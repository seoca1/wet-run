/** Tests for PWA Manager — install prompt, update detection, offline status. */
// @vitest-environment jsdom

import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  INITIAL_PWA_STATE,
  isStandalone,
  isServiceWorkerRegistered,
  hasWaitingWorker,
  promptInstall,
  applyUpdate,
  getOnlineStatus,
  type PwaState,
} from "../src/core/pwa_manager.ts";

describe("PWA Manager", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("INITIAL_PWA_STATE", () => {
    it("exports frozen initial state", () => {
      expect(INITIAL_PWA_STATE).toBeDefined();
      expect(Object.isFrozen(INITIAL_PWA_STATE)).toBe(true);
    });

    it("has correct shape", () => {
      const state: PwaState = INITIAL_PWA_STATE;
      expect(state.canInstall).toBe(false);
      expect(state.isInstalled).toBe(false);
      expect(state.hasUpdate).toBe(false);
      expect(state.deferredPrompt).toBeNull();
    });

    it("isOffline reflects navigator.onLine", () => {
      expect(INITIAL_PWA_STATE.isOffline).toBe(!navigator.onLine);
    });
  });

  describe("isStandalone", () => {
    it("returns true when display-mode is standalone", () => {
      vi.spyOn(window, "matchMedia").mockImplementation((query: string) => {
        if (query === "(display-mode: standalone)") {
          return {
            matches: true,
            media: query,
            onchange: null,
            addEventListener: vi.fn(),
            removeEventListener: vi.fn(),
            dispatchEvent: vi.fn(),
            addListener: vi.fn(),
            removeListener: vi.fn(),
          } as unknown as MediaQueryList;
        }
        return {
          matches: false,
          media: query,
          onchange: null,
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
          addListener: vi.fn(),
          removeListener: vi.fn(),
        } as unknown as MediaQueryList;
      });
      expect(isStandalone()).toBe(true);
    });

    it("returns false when display-mode is not standalone", () => {
      vi.spyOn(window, "matchMedia").mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
      }) as unknown as MediaQueryList);
      (window.navigator as unknown as Record<string, unknown>).standalone = false;
      expect(isStandalone()).toBe(false);
    });

    it("returns true for iOS standalone mode", () => {
      vi.spyOn(window, "matchMedia").mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
      }) as unknown as MediaQueryList);
      (window.navigator as unknown as Record<string, unknown>).standalone = true;
      expect(isStandalone()).toBe(true);
    });
  });

  describe("getOnlineStatus", () => {
    it("returns current navigator.onLine value", () => {
      const originalOnLine = navigator.onLine;
      Object.defineProperty(navigator, "onLine", {
        writable: true,
        configurable: true,
        value: true,
      });
      expect(getOnlineStatus()).toBe(true);
      Object.defineProperty(navigator, "onLine", {
        writable: true,
        configurable: true,
        value: false,
      });
      expect(getOnlineStatus()).toBe(false);
      Object.defineProperty(navigator, "onLine", {
        writable: true,
        configurable: true,
        value: originalOnLine,
      });
    });
  });

  describe("isServiceWorkerRegistered", () => {
    it("returns false when serviceWorker is not supported", async () => {
      const original = (navigator as { serviceWorker?: unknown }).serviceWorker;
      delete (navigator as { serviceWorker?: unknown }).serviceWorker;
      expect(await isServiceWorkerRegistered()).toBe(false);
      (navigator as { serviceWorker?: unknown }).serviceWorker = original;
    });

    it("returns true when registration exists", async () => {
      const mockReg = { active: {}, waiting: null };
      const original = (navigator as { serviceWorker?: unknown }).serviceWorker;
      (navigator as { serviceWorker?: { getRegistration: () => Promise<unknown> } }).serviceWorker = {
        getRegistration: vi.fn().mockResolvedValue(mockReg),
      };
      expect(await isServiceWorkerRegistered()).toBe(true);
      (navigator as { serviceWorker?: unknown }).serviceWorker = original;
    });

    it("returns false when no registration exists", async () => {
      const original = (navigator as { serviceWorker?: unknown }).serviceWorker;
      (navigator as { serviceWorker?: { getRegistration: () => Promise<unknown> } }).serviceWorker = {
        getRegistration: vi.fn().mockResolvedValue(undefined),
      };
      expect(await isServiceWorkerRegistered()).toBe(false);
      (navigator as { serviceWorker?: unknown }).serviceWorker = original;
    });
  });

  describe("hasWaitingWorker", () => {
    it("returns false when serviceWorker is not supported", async () => {
      const original = (navigator as { serviceWorker?: unknown }).serviceWorker;
      delete (navigator as { serviceWorker?: unknown }).serviceWorker;
      expect(await hasWaitingWorker()).toBe(false);
      (navigator as { serviceWorker?: unknown }).serviceWorker = original;
    });

    it("returns true when waiting worker exists", async () => {
      const mockReg = { waiting: { state: "installed" } };
      const original = (navigator as { serviceWorker?: unknown }).serviceWorker;
      (navigator as { serviceWorker?: { getRegistration: () => Promise<unknown> } }).serviceWorker = {
        getRegistration: vi.fn().mockResolvedValue(mockReg),
      };
      expect(await hasWaitingWorker()).toBe(true);
      (navigator as { serviceWorker?: unknown }).serviceWorker = original;
    });

    it("returns false when waiting is null", async () => {
      const mockReg = { waiting: null };
      const original = (navigator as { serviceWorker?: unknown }).serviceWorker;
      (navigator as { serviceWorker?: { getRegistration: () => Promise<unknown> } }).serviceWorker = {
        getRegistration: vi.fn().mockResolvedValue(mockReg),
      };
      expect(await hasWaitingWorker()).toBe(false);
      (navigator as { serviceWorker?: unknown }).serviceWorker = original;
    });

    it("returns false when no registration", async () => {
      const original = (navigator as { serviceWorker?: unknown }).serviceWorker;
      (navigator as { serviceWorker?: { getRegistration: () => Promise<unknown> } }).serviceWorker = {
        getRegistration: vi.fn().mockResolvedValue(undefined),
      };
      expect(await hasWaitingWorker()).toBe(false);
      (navigator as { serviceWorker?: unknown }).serviceWorker = original;
    });
  });

  describe("promptInstall", () => {
    it("returns false for null prompt", async () => {
      expect(await promptInstall(null)).toBe(false);
    });

    it("returns false for non-object prompt", async () => {
      expect(await promptInstall("not-an-object")).toBe(false);
      expect(await promptInstall(123)).toBe(false);
      expect(await promptInstall(true)).toBe(false);
    });

    it("returns false when prompt method is missing", async () => {
      const invalidPrompt = { userChoice: Promise.resolve({ outcome: "accepted" }) };
      expect(await promptInstall(invalidPrompt)).toBe(false);
    });

    it("returns true when install prompt is accepted", async () => {
      const mockPrompt = {
        prompt: vi.fn().mockResolvedValue(undefined),
        userChoice: Promise.resolve({ outcome: "accepted" }),
      };
      expect(await promptInstall(mockPrompt)).toBe(true);
      expect(mockPrompt.prompt).toHaveBeenCalledOnce();
    });

    it("returns false when install prompt is dismissed", async () => {
      const mockPrompt = {
        prompt: vi.fn().mockResolvedValue(undefined),
        userChoice: Promise.resolve({ outcome: "dismissed" }),
      };
      expect(await promptInstall(mockPrompt)).toBe(false);
      expect(mockPrompt.prompt).toHaveBeenCalledOnce();
    });
  });

  describe("applyUpdate", () => {
    it("returns false when serviceWorker is not supported", async () => {
      const original = (navigator as { serviceWorker?: unknown }).serviceWorker;
      delete (navigator as { serviceWorker?: unknown }).serviceWorker;
      expect(await applyUpdate()).toBe(false);
      (navigator as { serviceWorker?: unknown }).serviceWorker = original;
    });

    it("returns false when no registration exists", async () => {
      const original = (navigator as { serviceWorker?: unknown }).serviceWorker;
      (navigator as { serviceWorker?: { getRegistration: () => Promise<unknown> } }).serviceWorker = {
        getRegistration: vi.fn().mockResolvedValue(undefined),
      };
      expect(await applyUpdate()).toBe(false);
      (navigator as { serviceWorker?: unknown }).serviceWorker = original;
    });

    it("returns false when no waiting worker", async () => {
      const mockReg = { waiting: null };
      const original = (navigator as { serviceWorker?: unknown }).serviceWorker;
      (navigator as { serviceWorker?: { getRegistration: () => Promise<unknown> } }).serviceWorker = {
        getRegistration: vi.fn().mockResolvedValue(mockReg),
      };
      expect(await applyUpdate()).toBe(false);
      (navigator as { serviceWorker?: unknown }).serviceWorker = original;
    });

    it("posts SKIP_WAITING message when waiting worker exists", async () => {
      const postMessage = vi.fn();
      const mockReg = { waiting: { postMessage } };
      const original = (navigator as { serviceWorker?: unknown }).serviceWorker;
      (navigator as { serviceWorker?: { getRegistration: () => Promise<unknown> } }).serviceWorker = {
        getRegistration: vi.fn().mockResolvedValue(mockReg),
      };
      expect(await applyUpdate()).toBe(true);
      expect(postMessage).toHaveBeenCalledOnce();
      expect(postMessage).toHaveBeenCalledWith({ type: "SKIP_WAITING" });
      (navigator as { serviceWorker?: unknown }).serviceWorker = original;
    });
  });
});
