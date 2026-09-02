/** Global localStorage polyfill loaded before all test modules.
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
  length: number = 0;
  key(): string | null {
    return null;
  }
}

const memoryStorage = new MemoryStorage();
try {
  // @ts-expect-error — jsdom may have non-configurable property
  delete (globalThis as Record<string, unknown>).localStorage;
} catch {
  // ignore
}
(globalThis as unknown as { localStorage: Storage }).localStorage =
  memoryStorage as unknown as Storage;
