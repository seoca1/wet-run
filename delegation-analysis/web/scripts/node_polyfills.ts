/**
 * Browser API polyfills for running game code under Node.
 *
 * The combat reducer reaches `AudioManager`, whose constructor reads
 * `localStorage`. Tests get this polyfill from `vitest.setup.ts`; CLI tools
 * such as `balance_harness.ts` install it themselves.
 */

class MemoryStorage {
  private store = new Map<string, string>();
  getItem(key: string): string | null {
    return this.store.get(key) ?? null;
  }
  setItem(key: string, value: string): void {
    this.store.set(key, value);
  }
  removeItem(key: string): void {
    this.store.delete(key);
  }
  clear(): void {
    this.store.clear();
  }
  length = 0;
  key(): string | null {
    return null;
  }
}

/** Install an in-memory `localStorage` on globalThis, replacing any existing one. */
export function installLocalStoragePolyfill(): void {
  const g = globalThis as unknown as { localStorage?: Storage };
  try {
    delete g.localStorage;
  } catch {
    // ignore
  }
  g.localStorage = new MemoryStorage() as unknown as Storage;
}
