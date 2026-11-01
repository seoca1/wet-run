/** Minimal binary min-heap keyed on `f`, for the board's corridor search. */
export interface Ranked {
  readonly f: number;
}

/** Insert `item`, keeping the smallest `f` at index 0. */
export function heapPush<T extends Ranked>(heap: T[], item: T): void {
  heap.push(item);
  let i = heap.length - 1;
  while (i > 0) {
    const parent = (i - 1) >> 1;
    const above = heap[parent];
    if (above === undefined || above.f <= item.f) break;
    heap[i] = above;
    i = parent;
  }
  heap[i] = item;
}

/** Remove and return the item with the smallest `f`. */
export function heapPop<T extends Ranked>(heap: T[]): T | undefined {
  const top = heap[0];
  const last = heap.pop();
  if (heap.length === 0 || last === undefined) return top;
  let i = 0;
  for (;;) {
    let m = i;
    let fm = last.f;
    for (const c of [2 * i + 1, 2 * i + 2]) {
      const f = heap[c]?.f;
      if (f !== undefined && f < fm) {
        m = c;
        fm = f;
      }
    }
    const child = heap[m];
    if (m === i || child === undefined) break;
    heap[i] = child;
    i = m;
  }
  heap[i] = last;
  return top;
}
