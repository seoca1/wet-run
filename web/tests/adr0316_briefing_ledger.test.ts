/**
 * ADR-0316 — the briefing ledger: what the import decided, and what it passed
 * over.
 *
 * The pipeline had no intermediate file. `import_briefings.py` reads the
 * derivative fiction and writes straight into `missions.json`, so the game data
 * says only what a briefing IS — never where it came from or what else was on
 * the table. That is how a 150-character cut lived for a day, and how a
 * `watchdog_patrol` summary that is missing its middle clause shipped while its
 * own Korean twin held the whole sentence.
 *
 * `docs/design/story/briefing-ledger.json` is that intermediate file. This
 * holds it to two things:
 *
 *  1. it still describes the game data on disk (a stale ledger would report a
 *     decision that is no longer true), and
 *  2. it is internally honest — a "chosenFrom" that is not a real candidate, or
 *     a disagreement flag that does not match the candidates it lists.
 *
 * The lineage files themselves are checked by the importer's `--check`, which
 * needs the Fiction repo; CI checks out this repo alone, so that half cannot
 * live here.
 */
import { describe, expect, it } from "vitest";
import { loadMissionsCatalog } from "../src/core/data_loaders";
import missionsData from "../src/data/missions.json" with { type: "json" };
import ledgerData from "../../docs/design/story/briefing-ledger.json" with { type: "json" };

interface Candidate {
  readonly file: string;
  readonly chars: number;
  readonly declared: boolean;
  readonly body: string;
  readonly readable: boolean;
}
interface LedgerEntry {
  readonly briefing: string | null;
  readonly chosenFrom: string | null;
  readonly considered: readonly Candidate[];
  readonly notScanned: readonly Candidate[];
  readonly disagrees: boolean;
  readonly twinDiffers: boolean;
}
const LEDGER = ledgerData as unknown as {
  readonly scanLanguage: string;
  readonly missions: Readonly<Record<string, LedgerEntry>>;
  readonly orphanMissionIds: readonly string[];
};

const MISSIONS = loadMissionsCatalog(missionsData);
const SPRAWL = MISSIONS.filter((m) => m.source_universe !== "far-grid");

describe("ADR-0316 — the briefing ledger describes the game data", () => {
  it("every Sprawl mission's briefing is the one the ledger records", () => {
    for (const mission of SPRAWL) {
      const recorded = LEDGER.missions[mission.id];
      expect(recorded, `${mission.id} is missing from the ledger`).toBeDefined();
      expect(recorded?.briefing ?? null, `${mission.id} briefing`).toBe(
        mission.briefing ?? null,
      );
    }
  });

  it("names the scan language and lists the fiction ids the game does not ship", () => {
    expect(LEDGER.scanLanguage).toBe("en");
    const game = new Set(MISSIONS.map((m) => m.id));
    for (const orphan of LEDGER.orphanMissionIds) {
      expect(game.has(orphan), `${orphan} is shipped, so it is not an orphan`).toBe(
        false,
      );
    }
    expect(LEDGER.orphanMissionIds.length).toBeGreaterThan(0);
  });
});

describe("ADR-0316 — the ledger is internally honest", () => {
  it("every briefing it records came from a candidate it lists", () => {
    for (const [id, entry] of Object.entries(LEDGER.missions)) {
      if (entry.briefing === null) {
        expect(entry.chosenFrom, `${id} has no briefing but names a source`).toBeNull();
        continue;
      }
      expect(entry.chosenFrom, `${id} names no source file`).not.toBeNull();
      const source = entry.considered.find((c) => c.file === entry.chosenFrom);
      expect(source, `${id}: chosenFrom is not one of the candidates`).toBeDefined();
      // `brief()` keeps the leading whole sentences, so the chosen text is the
      // opening of its source, not the whole of it.
      expect(
        source?.body.startsWith(entry.briefing),
        `${id}: the briefing is not the opening of its source`,
      ).toBe(true);
    }
  });

  it("the disagreement flags match the candidates they list", () => {
    for (const [id, entry] of Object.entries(LEDGER.missions)) {
      const readable = entry.considered.filter((c) => c.readable);
      const distinct = new Set(readable.map((c) => c.body));
      expect(entry.disagrees, `${id}: disagrees flag`).toBe(distinct.size > 1);
      const twins = entry.notScanned.filter(
        (c) => c.readable && c.body !== entry.briefing,
      );
      expect(entry.twinDiffers, `${id}: twinDiffers flag`).toBe(twins.length > 0);
    }
  });

  it("shows the case that made the ledger worth building", () => {
    // The `en` summary is missing its middle clause; the `ko` twin has the
    // whole sentence. Nothing compared them, so nothing noticed.
    const entry = LEDGER.missions["watchdog_patrol"];
    expect(entry).toBeDefined();
    expect(entry?.twinDiffers).toBe(true);
    const twin = entry?.notScanned.find((c) => c.chars > 150);
    expect(twin, "the complete twin is recorded").toBeDefined();
    expect(twin?.body).toContain("ghost marks");
    expect(entry?.briefing).not.toContain("ghost marks");
  });
});
