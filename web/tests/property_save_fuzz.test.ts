/** Property-based fuzzing of the SAVE/LOAD persistence layer (fast-check v4).
 *
 * METHOD: `src/save/` owns lz-string compression, a versioned envelope (v1
 * legacy / v2 compressed-or-plain), a legacy single-slot migration and a
 * localStorage fallback used when IndexedDB is unavailable. Existing tests
 * exercise only hand-written fixtures; this file uses property-based checking
 * instead — fast-check generates arbitrary inputs and the properties below ARE
 * the specification. A failing property is shrunk by fast-check to a minimal
 * counterexample, which is what makes a defect actionable.
 *
 * PROPERTIES: (1) lossless round-trip — serialize → deserialize is the
 * identity for every valid `SaveSlot` (unicode/CJK strings, empty arrays,
 * payloads crossing the 512-byte compression threshold); (2) corruption
 * resilience — garbage, random base64 and truncated payloads never throw and
 * never yield a malformed slot; (3) legacy migration — arbitrary legacy (v1,
 * envelope-less) payloads migrate or fail safely; (4) quota degradation — a
 * `QuotaExceededError` from `setItem` degrades gracefully.
 *
 * ENVIRONMENT: the vitest env is `node`, so `indexedDB` is undefined and the
 * save layer takes its documented localStorage fallback — the same
 * arrangement used by `tests/storage.test.ts` (which opts into jsdom). The
 * localStorage polyfill is installed globally by `vitest.setup.ts`.
 * RUNS are controlled by the `FUZZ_RUNS` env var (default 200).
 */
import { describe, it, expect, vi, afterEach } from "vitest";
import fc, { base64String } from "fast-check";
import { save, load, clear } from "../src/save/storage.ts";
import { encodeEnvelope, decodeEnvelope } from "../src/save/compress.ts";
import { slotToGameState } from "../src/core/state.ts";
import missionsData from "../src/data/missions.json";
import programsData from "../src/data/programs.json";
import iceTypesData from "../src/data/ice_types.json";
import type { Ice, Mission, Program, SaveSlot } from "../src/core/types.ts";

const NUM_RUNS = Number.parseInt(process.env.FUZZ_RUNS ?? "200", 10) || 200;

const missions = Object.values(missionsData) as Mission[];
const programs = programsData as unknown as Record<string, Program>;
const ices = Object.values(iceTypesData) as unknown as Ice[];

/** Unicode-ish identifier string (covers Hangul / CJK / emoji). */
const idArb = fc.string({ unit: "grapheme", minLength: 0, maxLength: 12 });

/** Program identifier array; empty arrays are explicitly included.
 *  `idArrayArb` covers the small (plain-JSON, <512B) path; `bigArrayArb`
 *  crosses the compression threshold so the lz-string path is fuzzed too. */
const idArrayArb = fc.array(idArb, { maxLength: 6 });
const bigArrayArb = fc.array(idArb, { minLength: 60, maxLength: 120 });

/** Arbitrary VALID SaveSlot: every field present and correctly typed. */
const saveSlotArb: fc.Arbitrary<SaveSlot> = fc.record({
  version: fc.constant(1),
  missionId: idArb,
  playerHp: fc.integer({ min: 0, max: 999 }),
  playerMaxHp: fc.integer({ min: 0, max: 999 }),
  playerAlarm: fc.integer({ min: 0, max: 100 }),
  playerCredits: fc.integer({ min: 0, max: 1_000_000 }),
  turnCount: fc.integer({ min: 0, max: 10_000 }),
  deckIds: fc.oneof(idArrayArb, bigArrayArb),
  discardIds: fc.oneof(idArrayArb, bigArrayArb),
  drawIds: fc.oneof(idArrayArb, bigArrayArb),
  savedAt: fc
    .tuple(
      fc.integer({ min: 1970, max: 2200 }),
      fc.integer({ min: 1, max: 12 }),
      fc.integer({ min: 1, max: 28 }),
    )
    .map(([y, m, d]) =>
      `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}T00:00:00.000Z`,
    ),
  graphicNovelProgress: fc.option(
    fc.record({
      chainId: idArb,
      sceneIndex: fc.integer({ min: 0, max: 100 }),
      dialogueIndex: fc.integer({ min: 0, max: 100 }),
    }),
    { nil: null },
  ),
});

/** Serialized form used by the storage layer (envelope wrapped in JSON). */
function serializeForStorage(data: SaveSlot): string {
  return JSON.stringify(encodeEnvelope(JSON.stringify(data)));
}

/** Strict `SaveSlot` type check: array ELEMENTS must be strings and
 *  `graphicNovelProgress` must be a well-formed object when present.
 *  (`isSaveSlot` in storage.ts now enforces the same contract — this helper
 *  stays as the independent oracle the fuzz properties assert against.) */
function satisfiesSaveSlotType(value: unknown): boolean {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  const nums = ["version", "playerHp", "playerMaxHp", "playerAlarm", "playerCredits", "turnCount"];
  const strs = ["missionId", "savedAt"];
  if (!nums.every((k) => typeof v[k] === "number")) return false;
  if (!strs.every((k) => typeof v[k] === "string")) return false;
  const arrays = ["deckIds", "discardIds", "drawIds"].map((k) => v[k]);
  if (!arrays.every((a) => Array.isArray(a) && (a as unknown[]).every((e) => typeof e === "string")))
    return false;
  const gn = v.graphicNovelProgress;
  if (gn === undefined || gn === null) return true;
  if (typeof gn !== "object") return false;
  const g = gn as Record<string, unknown>;
  return (
    typeof g.chainId === "string" &&
    typeof g.sceneIndex === "number" &&
    typeof g.dialogueIndex === "number"
  );
}

/** Arbitrary garbage that must never crash the decoder. */
const garbageArb = fc.oneof(
  fc.string({ unit: "binary", maxLength: 200 }),
  base64String(),
  fc.constantFrom("", "{", "{}", "null", "[]", "42", '{"v":2}', '{"v":2,"c":true}'),
);

/** Minimal payload that violates the `SaveSlot` type via non-string array
 *  elements. See the "known violation" describe blocks below. */
function badElementSlot(): SaveSlot {
  return {
    version: 1,
    missionId: "",
    playerHp: 0,
    playerMaxHp: 0,
    playerAlarm: 0,
    playerCredits: 0,
    turnCount: 0,
    deckIds: [1] as unknown as ReadonlyArray<string>,
    discardIds: [],
    drawIds: [],
    savedAt: "2026-01-01T00:00:00.000Z",
  };
}

function check<T>(prop: fc.IRawProperty<T>, runs: number = NUM_RUNS): void {
  fc.assert(prop, { numRuns: runs });
}

async function checkAsync<Ts extends [unknown, ...unknown[]]>(
  arbitraries: { [K in keyof Ts]: fc.Arbitrary<Ts[K]> },
  predicate: (...args: Ts) => Promise<void>,
  runs: number = NUM_RUNS,
): Promise<void> {
  await fc.assert(fc.asyncProperty(...arbitraries, predicate), { numRuns: runs });
}

describe("property: save layer fuzz (fast-check)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ---------------------------------------------------------------- 1
  it("lossless round-trip: serialize → deserialize is the identity", () => {
    // Both envelope branches must be exercised: c=false (plain, <512B) and c=true (lz-string).
    let sawPlain = false;
    let sawCompressed = false;
    check(
      fc.property(saveSlotArb, (slot) => {
        const env = encodeEnvelope(JSON.stringify(slot));
        if (env.c) sawCompressed = true;
        else sawPlain = true;
        const decoded = decodeEnvelope(serializeForStorage(slot));
        expect(decoded).not.toBeNull();
        expect(JSON.parse(decoded as string)).toEqual(slot);
      }),
    );
    expect(sawPlain).toBe(true);
    expect(sawCompressed).toBe(true);
  });

  it("lossless round-trip through the real storage layer (save → load)", async () => {
    await checkAsync([saveSlotArb], async (slot) => {
      await clear(1);
      await save(1, slot);
      expect(await load(1)).toEqual(slot);
    });
  });

  // ---------------------------------------------------------------- 2
  it("corruption resilience: garbage and truncated payloads never crash or corrupt", async () => {
    check(
      fc.property(garbageArb, (garbage) => {
        let decoded: string | null = null;
        expect(() => {
          decoded = decodeEnvelope(garbage);
        }).not.toThrow();
        // Envelope contract: null (rejected) or a string (legacy v1 payloads are
        // validated separately by the storage layer).
        expect(decoded === null || typeof decoded === "string").toBe(true);
      }),
    );
    await checkAsync([garbageArb], async (garbage) => {
      localStorage.setItem("wetrun_mvp_save_v1_slot_3", garbage);
      const loaded = await load(3);
      expect(loaded === null || satisfiesSaveSlotType(loaded)).toBe(true);
    });
    await checkAsync(
      [saveSlotArb, fc.integer({ min: 0, max: 1000 })],
      async (slot, cut) => {
        const stored = serializeForStorage(slot);
        localStorage.setItem(
          "wetrun_mvp_save_v1_slot_2",
          stored.slice(0, Math.min(stored.length, cut)),
        );
        const loaded = await load(2);
        // Either rejected (null) or fully valid — never a partial object.
        if (loaded !== null) expect(satisfiesSaveSlotType(loaded)).toBe(true);
      },
    );
  });

  // ---------------------------------------------------------------- 3
  it("legacy migration: arbitrary legacy payloads migrate or fail safely", async () => {
    await checkAsync(
      [saveSlotArb, fc.string({ unit: "binary", maxLength: 40 })],
      async (slot, noise) => {
        localStorage.clear();
        // Legacy v1 = raw SaveSlot JSON, no envelope.
        localStorage.setItem("wetrun_mvp_save_v1", JSON.stringify(slot));
        expect(await load(0)).toEqual(slot);
        // The legacy key is migrated away after a successful read.
        expect(localStorage.getItem("wetrun_mvp_save_v1")).toBeNull();
        // A legacy payload with trailing noise must not crash the loader.
        localStorage.setItem("wetrun_mvp_save_v1", JSON.stringify(slot) + noise);
        const second = await load(0);
        expect(second === null || satisfiesSaveSlotType(second)).toBe(true);
      },
    );
  });

  // ---------------------------------------------------------------- 4
  it("quota degradation: a QuotaExceededError does not crash the save path", async () => {
    await checkAsync([saveSlotArb], async (slot) => {
      // The vitest.setup.ts polyfill is a plain class instance (NOT a `Storage`
      // subclass), so the spy must target the instance method.
      const spy = vi
        .spyOn(localStorage, "setItem")
        .mockImplementation(() => {
          const err = new Error("simulated quota exhaustion");
          err.name = "QuotaExceededError";
          throw err;
        });
      const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
      try {
        // Observed contract: `save` swallows the error (console.warn) and
        // resolves — it does NOT reject and does NOT throw.
        await expect(save(1, slot)).resolves.toBeUndefined();
        expect(warn).toHaveBeenCalled();
      } finally {
        spy.mockRestore();
        warn.mockRestore();
      }
      // The slot that failed to persist must read back as absent.
      expect(await load(1)).toBeNull();
    }, Math.max(10, Math.floor(NUM_RUNS / 10)));
  });
});

describe("regressions: SaveSlot type is enforced on load", () => {
  /*
   * REGRESSION 1 (was VIOLATION 1) — `isSaveSlot` in `src/save/storage.ts`
   * used to check only `Array.isArray(...)` for deckIds/discardIds/drawIds,
   * never that the *elements* are strings, so `deckIds: [1]` loaded as a
   * "valid" `SaveSlot` although the declared type is `ReadonlyArray<string>`.
   * The guard now validates every element; this block is regression-locked.
   * MINIMAL COUNTEREXAMPLE (fast-check shrunk): { version: 1, missionId: "",
   *   playerHp: 0, playerMaxHp: 0, playerAlarm: 0, playerCredits: 0,
   *   turnCount: 0, deckIds: [1], discardIds: [], drawIds: [],
   *   savedAt: "2026-01-01T00:00:00.000Z" }
   *   → load(1) must now return null (rejected), not an object with deckIds [1].
   */
  it("load() must reject slots whose array elements are not strings", async () => {
    localStorage.setItem(
      "wetrun_mvp_save_v1_slot_1",
      JSON.stringify(badElementSlot()),
    );
    const loaded = await load(1);
    expect(loaded === null || satisfiesSaveSlotType(loaded)).toBe(true);
  });

  /*
   * REGRESSION 2 (was VIOLATION 2) — higher severity: the unvalidated
   * `graphicNovelProgress` used to reach `slotToGameState` in
   * `src/core/state.ts`, which calls
   * `slot.graphicNovelProgress.chainId.split("_")` unguarded, so a stored
   * slot with a non-object `graphicNovelProgress` made resume throw an
   * uncaught `TypeError`. `isSaveSlot` now validates the optional progress
   * object; this block is regression-locked.
   * MINIMAL COUNTEREXAMPLE (fast-check shrunk):
   *   graphicNovelProgress: "not-an-object"
   *   → TypeError: Cannot read properties of undefined (reading 'split')
   */
  it("a loaded slot must never make slotToGameState throw", async () => {
    localStorage.setItem(
      "wetrun_mvp_save_v1_slot_1",
      JSON.stringify({
        ...badElementSlot(),
        missionId: missions[0]!.id,
        deckIds: [],
        graphicNovelProgress: "not-an-object",
      }),
    );
    const loaded = await load(1);
    // The malformed slot must be rejected outright: `load` never hands a
    // malformed `graphicNovelProgress` to `slotToGameState`.
    expect(loaded).toBeNull();
    // Defensive: even a slot that slipped through must not crash the resume
    // path (guarded by the `loaded !== null` branch).
    if (loaded !== null) {
      expect(() =>
        slotToGameState(loaded, missions, programs, ices[0]!),
      ).not.toThrow();
    }
  });
});
