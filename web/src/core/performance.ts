/** Performance Monitor — FPS counter, memory tracking, render timing. */

export interface PerformanceMetrics {
  readonly fps: number;
  readonly frameTime: number;
  readonly memoryUsed: number;
  readonly memoryTotal: number;
  readonly renderTime: number;
}

/** FPS counter using requestAnimationFrame. */
export class FpsCounter {
  private frames = 0;
  private lastTime = performance.now();
  private currentFps = 0;

  /** Call once per frame. */
  tick(): void {
    this.frames++;
    const now = performance.now();
    const delta = now - this.lastTime;

    if (delta >= 1000) {
      this.currentFps = Math.round((this.frames * 1000) / delta);
      this.frames = 0;
      this.lastTime = now;
    }
  }

  /** Get current FPS. */
  getFps(): number {
    return this.currentFps;
  }

  /** Reset counter. */
  reset(): void {
    this.frames = 0;
    this.lastTime = performance.now();
    this.currentFps = 0;
  }
}

/** Memory usage tracker (Chrome-only). */
export function getMemoryUsage(): { used: number; total: number } {
  const perf = performance as unknown as {
    memory?: { usedJSHeapSize: number; totalJSHeapSize: number };
  };
  if (perf.memory) {
    return {
      used: Math.round(perf.memory.usedJSHeapSize / 1024 / 1024),
      total: Math.round(perf.memory.totalJSHeapSize / 1024 / 1024),
    };
  }
  return { used: 0, total: 0 };
}

/** Render timing helper. */
export function measureRender<T>(fn: () => T): { result: T; duration: number } {
  const start = performance.now();
  const result = fn();
  const duration = performance.now() - start;
  return { result, duration };
}

/** Get current performance metrics. */
export function getMetrics(
  fps: number,
  renderTime: number
): PerformanceMetrics {
  const memory = getMemoryUsage();
  return Object.freeze({
    fps,
    frameTime: fps > 0 ? Math.round(1000 / fps) : 0,
    memoryUsed: memory.used,
    memoryTotal: memory.total,
    renderTime: Math.round(renderTime * 100) / 100,
  });
}

/** Performance budget thresholds. */
export const BUDGETS = {
  targetFps: 60,
  maxFrameTime: 16.67,
  maxMemory: 512,
  maxRenderTime: 10,
} as const;

/** Check if performance is within budget. */
export function isWithinBudget(metrics: PerformanceMetrics): {
  readonly fps: boolean;
  readonly memory: boolean;
  readonly render: boolean;
} {
  return Object.freeze({
    fps: metrics.fps >= BUDGETS.targetFps * 0.9,
    memory: metrics.memoryUsed <= BUDGETS.maxMemory || metrics.memoryUsed === 0,
    render: metrics.renderTime <= BUDGETS.maxRenderTime,
  });
}

/** Format metrics for display. */
export function formatMetrics(metrics: PerformanceMetrics): string {
  const budget = isWithinBudget(metrics);
  const fpsColor = budget.fps ? "✓" : "✗";
  const memColor = budget.memory ? "✓" : "✗";
  const renderColor = budget.render ? "✓" : "✗";

  return [
    `FPS: ${metrics.fps} ${fpsColor}`,
    `Frame: ${metrics.frameTime}ms`,
    `Memory: ${metrics.memoryUsed}MB/${metrics.memoryTotal}MB ${memColor}`,
    `Render: ${metrics.renderTime}ms ${renderColor}`,
  ].join(" | ");
}
