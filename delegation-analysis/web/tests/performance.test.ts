/** Performance monitoring tests. */
import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  FpsCounter,
  getMemoryUsage,
  measureRender,
  getMetrics,
  BUDGETS,
  isWithinBudget,
  formatMetrics,
  type PerformanceMetrics,
} from "../src/core/performance.js";

describe("FpsCounter", () => {
  beforeEach(() => {
    vi.spyOn(performance, "now").mockReturnValue(0);
  });

  it("starts with 0 fps", () => {
    const counter = new FpsCounter();
    expect(counter.getFps()).toBe(0);
  });

  it("increments frames on tick", () => {
    const counter = new FpsCounter();
    const mockNow = vi.spyOn(performance, "now");
    mockNow.mockReturnValue(0);
    counter.tick();
    mockNow.mockReturnValue(500);
    counter.tick();
    mockNow.mockReturnValue(1000);
    counter.tick();
    expect(counter.getFps()).toBe(3);
  });

  it("calculates fps after 1 second", () => {
    const counter = new FpsCounter();
    const mockNow = vi.spyOn(performance, "now");

    mockNow.mockReturnValue(0);
    for (let i = 0; i < 60; i++) {
      counter.tick();
    }

    mockNow.mockReturnValue(1000);
    counter.tick();

    expect(counter.getFps()).toBe(61);
  });

  it("resets counter", () => {
    const counter = new FpsCounter();
    const mockNow = vi.spyOn(performance, "now");

    mockNow.mockReturnValue(0);
    counter.tick();
    counter.tick();

    mockNow.mockReturnValue(1000);
    counter.tick();

    expect(counter.getFps()).toBeGreaterThan(0);

    counter.reset();
    expect(counter.getFps()).toBe(0);
  });

  it("handles multiple second intervals", () => {
    const counter = new FpsCounter();
    const mockNow = vi.spyOn(performance, "now");

    mockNow.mockReturnValue(0);
    for (let i = 0; i < 60; i++) {
      counter.tick();
    }

    mockNow.mockReturnValue(1000);
    counter.tick();
    const firstFps = counter.getFps();

    mockNow.mockReturnValue(1000);
    for (let i = 0; i < 30; i++) {
      counter.tick();
    }

    mockNow.mockReturnValue(2000);
    counter.tick();
    const secondFps = counter.getFps();

    expect(firstFps).toBe(61);
    expect(secondFps).toBe(31);
  });
});

describe("getMemoryUsage", () => {
  it("returns object with used and total properties", () => {
    const memory = getMemoryUsage();
    expect(memory).toHaveProperty("used");
    expect(memory).toHaveProperty("total");
    expect(typeof memory.used).toBe("number");
    expect(typeof memory.total).toBe("number");
  });

  it("returns 0 values when memory API unavailable", () => {
    const memory = getMemoryUsage();
    expect(memory.used).toBeGreaterThanOrEqual(0);
    expect(memory.total).toBeGreaterThanOrEqual(0);
  });
});

describe("measureRender", () => {
  it("measures execution time and returns result", () => {
    const mockNow = vi.spyOn(performance, "now");
    mockNow.mockReturnValueOnce(0);
    mockNow.mockReturnValueOnce(10);

    const result = measureRender(() => 42);

    expect(result.result).toBe(42);
    expect(result.duration).toBe(10);
  });

  it("works with complex functions", () => {
    const mockNow = vi.spyOn(performance, "now");
    mockNow.mockReturnValueOnce(0);
    mockNow.mockReturnValueOnce(5.5);

    const result = measureRender(() => {
      return [1, 2, 3].reduce((a, b) => a + b, 0);
    });

    expect(result.result).toBe(6);
    expect(result.duration).toBe(5.5);
  });

  it("returns 0 duration for instant execution", () => {
    const mockNow = vi.spyOn(performance, "now");
    mockNow.mockReturnValue(100);

    const result = measureRender(() => "fast");

    expect(result.result).toBe("fast");
    expect(result.duration).toBe(0);
  });
});

describe("getMetrics", () => {
  it("returns frozen PerformanceMetrics object", () => {
    const metrics = getMetrics(60, 5.5);

    expect(Object.isFrozen(metrics)).toBe(true);
    expect(metrics.fps).toBe(60);
    expect(metrics.renderTime).toBe(5.5);
  });

  it("calculates frameTime from fps", () => {
    const metrics = getMetrics(60, 5);

    expect(metrics.frameTime).toBe(17);
  });

  it("handles zero fps", () => {
    const metrics = getMetrics(0, 10);

    expect(metrics.frameTime).toBe(0);
    expect(metrics.fps).toBe(0);
  });

  it("includes memory data", () => {
    const metrics = getMetrics(60, 5);

    expect(metrics).toHaveProperty("memoryUsed");
    expect(metrics).toHaveProperty("memoryTotal");
    expect(typeof metrics.memoryUsed).toBe("number");
    expect(typeof metrics.memoryTotal).toBe("number");
  });

  it("rounds renderTime to 2 decimal places", () => {
    const metrics = getMetrics(60, 5.567);

    expect(metrics.renderTime).toBe(5.57);
  });
});

describe("BUDGETS", () => {
  it("is immutable via as const", () => {
    expect(BUDGETS).toBeDefined();
    expect(typeof BUDGETS).toBe("object");
  });

  it("has correct target values", () => {
    expect(BUDGETS.targetFps).toBe(60);
    expect(BUDGETS.maxFrameTime).toBe(16.67);
    expect(BUDGETS.maxMemory).toBe(512);
    expect(BUDGETS.maxRenderTime).toBe(10);
  });
});

describe("isWithinBudget", () => {
  it("checks fps threshold (90% of target)", () => {
    const goodMetrics: PerformanceMetrics = {
      fps: 60,
      frameTime: 16,
      memoryUsed: 100,
      memoryTotal: 200,
      renderTime: 5,
    };
    const result = isWithinBudget(goodMetrics);
    expect(result.fps).toBe(true);

    const badMetrics: PerformanceMetrics = {
      fps: 50,
      frameTime: 20,
      memoryUsed: 100,
      memoryTotal: 200,
      renderTime: 5,
    };
    const result2 = isWithinBudget(badMetrics);
    expect(result2.fps).toBe(false);
  });

  it("checks memory threshold", () => {
    const goodMetrics: PerformanceMetrics = {
      fps: 60,
      frameTime: 16,
      memoryUsed: 400,
      memoryTotal: 1000,
      renderTime: 5,
    };
    const result = isWithinBudget(goodMetrics);
    expect(result.memory).toBe(true);

    const badMetrics: PerformanceMetrics = {
      fps: 60,
      frameTime: 16,
      memoryUsed: 600,
      memoryTotal: 1000,
      renderTime: 5,
    };
    const result2 = isWithinBudget(badMetrics);
    expect(result2.memory).toBe(false);
  });

  it("passes memory check when memory is 0", () => {
    const metrics: PerformanceMetrics = {
      fps: 60,
      frameTime: 16,
      memoryUsed: 0,
      memoryTotal: 0,
      renderTime: 5,
    };
    const result = isWithinBudget(metrics);
    expect(result.memory).toBe(true);
  });

  it("checks render time threshold", () => {
    const goodMetrics: PerformanceMetrics = {
      fps: 60,
      frameTime: 16,
      memoryUsed: 100,
      memoryTotal: 200,
      renderTime: 8,
    };
    const result = isWithinBudget(goodMetrics);
    expect(result.render).toBe(true);

    const badMetrics: PerformanceMetrics = {
      fps: 60,
      frameTime: 16,
      memoryUsed: 100,
      memoryTotal: 200,
      renderTime: 15,
    };
    const result2 = isWithinBudget(badMetrics);
    expect(result2.render).toBe(false);
  });

  it("returns frozen object", () => {
    const metrics: PerformanceMetrics = {
      fps: 60,
      frameTime: 16,
      memoryUsed: 100,
      memoryTotal: 200,
      renderTime: 5,
    };
    const result = isWithinBudget(metrics);
    expect(Object.isFrozen(result)).toBe(true);
  });
});

describe("formatMetrics", () => {
  it("formats metrics with check marks", () => {
    const metrics: PerformanceMetrics = {
      fps: 60,
      frameTime: 17,
      memoryUsed: 100,
      memoryTotal: 200,
      renderTime: 5,
    };

    const formatted = formatMetrics(metrics);

    expect(formatted).toContain("FPS: 60");
    expect(formatted).toContain("Frame: 17ms");
    expect(formatted).toContain("Memory: 100MB/200MB");
    expect(formatted).toContain("Render: 5ms");
  });

  it("shows check marks for good performance", () => {
    const metrics: PerformanceMetrics = {
      fps: 60,
      frameTime: 17,
      memoryUsed: 100,
      memoryTotal: 200,
      renderTime: 5,
    };

    const formatted = formatMetrics(metrics);

    expect(formatted).toContain("✓");
  });

  it("shows cross marks for bad performance", () => {
    const metrics: PerformanceMetrics = {
      fps: 30,
      frameTime: 33,
      memoryUsed: 600,
      memoryTotal: 800,
      renderTime: 15,
    };

    const formatted = formatMetrics(metrics);

    expect(formatted).toContain("✗");
  });

  it("separates sections with pipe", () => {
    const metrics: PerformanceMetrics = {
      fps: 60,
      frameTime: 17,
      memoryUsed: 100,
      memoryTotal: 200,
      renderTime: 5,
    };

    const formatted = formatMetrics(metrics);

    expect(formatted.split(" | ")).toHaveLength(4);
  });

  it("handles zero memory gracefully", () => {
    const metrics: PerformanceMetrics = {
      fps: 60,
      frameTime: 17,
      memoryUsed: 0,
      memoryTotal: 0,
      renderTime: 5,
    };

    const formatted = formatMetrics(metrics);

    expect(formatted).toContain("Memory: 0MB/0MB ✓");
  });
});
