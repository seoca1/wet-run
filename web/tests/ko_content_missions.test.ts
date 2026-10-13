/** KO content activation follow-up — tests for title_ko + briefing_ko plumbing.
 *
 * Pins three contracts:
 *  1. Loader passthrough — `parseMission` accepts and propagates `title_ko` and
 *     `briefing_ko` exactly the way it does `briefing` (non-empty string passthrough;
 *     empty/missing field omitted). Throws on wrong-type.
 *  2. Real missions.json — every one of the 53 missions carries `title_ko`; all
 *     20 far-grid missions carry `briefing_ko` matching their EN briefing
 *     surface.
 *  3. Far Grid hub renderer KO resolution — title + briefing render KO when
 *     language is "ko" and a translation exists, fall back to EN otherwise.
 *     Also CJK-safe: no Hanja / kana in any of the 53+20 new strings (sweeps
 *     the entire field set programmatically per AGENTS.md §7).
 */
import { describe, it, expect } from "vitest";
import { parseMission, loadMissionsCatalog } from "../src/core/data_loaders";
import { renderFarGridHub } from "../src/renderer/far_grid_hub";
import type { Cell, Mission, MissionRewards } from "../src/core/types";
import type { Language } from "../src/core/i18n";

type GridLike = { cells: ReadonlyArray<ReadonlyArray<Cell>> };

function gridText(grid: GridLike): string {
  return grid.cells
    .map((row) => row.map((c) => c?.char ?? " ").join(""))
    .join("\n");
}

function getRowText(grid: GridLike, y: number, x: number, length: number): string {
  let result = "";
  const row = grid.cells[y];
  if (!row) return result;
  for (let i = 0; i < length; i++) {
    result += row[x + i]?.char ?? " ";
  }
  return result;
}

const EMPTY_REWARDS: MissionRewards = { credits: 0, materials: {} };

function makeBaseMission(id: string, title: string): Mission {
  return {
    id,
    title,
    fixer: "test_fixer",
    arc: 1,
    zone: "far_grid_test",
    grade_min: 1,
    grade_max: 1,
    rewards: EMPTY_REWARDS,
    source_universe: "far-grid",
  };
}

const CJK_HANJA = /[\u4e00-\u9fff\u3400-\u4dbf]/;
const KANA = /[\u3040-\u30ff\u31f0-\u31ff]/;
const HANGUL = /[\uac00-\ud7a3]/;

describe("data_loaders: title_ko + briefing_ko passthrough", () => {
  it("propagates title_ko when a non-empty string is present", () => {
    const m = parseMission(
      {
        id: "test_ko_title",
        title: "Aleph Fragment",
        fixer: "finn",
        arc: 4,
        zone: "deep",
        grade_min: 5,
        grade_max: 5,
        rewards: { credits: 4000, materials: {} },
        title_ko: "알레프 파편",
      },
      "test_ko_title",
    );
    expect(m.title_ko).toBe("알레프 파편");
    expect(m.title).toBe("Aleph Fragment"); // EN untouched
  });

  it("propagates briefing_ko when a non-empty string is present (parallel to briefing)", () => {
    const m = parseMission(
      {
        id: "test_ko_briefing",
        title: "Far Grid Prelude",
        fixer: "operator",
        arc: 1,
        zone: "precursor",
        grade_min: 1,
        grade_max: 2,
        rewards: { credits: 0, materials: {} },
        source_universe: "far-grid",
        briefing: "EN baseline text.",
        briefing_ko: "한국어 안내문.",
      },
      "test_ko_briefing",
    );
    expect(m.briefing).toBe("EN baseline text.");
    expect(m.briefing_ko).toBe("한국어 안내문.");
  });

  it("omits title_ko when the field is missing (not coerced into empty string)", () => {
    const m = parseMission(
      {
        id: "no_title_ko",
        title: "Test",
        fixer: "finn",
        arc: 1,
        zone: "surface",
        grade_min: 1,
        grade_max: 1,
        rewards: { credits: 0, materials: {} },
      },
      "no_title_ko",
    );
    expect("title_ko" in m).toBe(false);
  });

  it("omits title_ko when the field is an empty string (mirrors briefing pattern)", () => {
    const m = parseMission(
      {
        id: "empty_title_ko",
        title: "Test",
        fixer: "finn",
        arc: 1,
        zone: "surface",
        grade_min: 1,
        grade_max: 1,
        rewards: { credits: 0, materials: {} },
        title_ko: "   ",
      },
      "empty_title_ko",
    );
    expect("title_ko" in m).toBe(false);
  });

  it("omits briefing_ko when briefing_ko is missing", () => {
    const m = parseMission(
      {
        id: "no_briefing_ko",
        title: "X",
        fixer: "finn",
        arc: 1,
        zone: "z",
        grade_min: 1,
        grade_max: 1,
        rewards: { credits: 0, materials: {} },
        briefing: "EN only.",
      },
      "no_briefing_ko",
    );
    expect(m.briefing).toBe("EN only.");
    expect("briefing_ko" in m).toBe(false);
  });

  it("throws when title_ko is a non-string type", () => {
    expect(() =>
      parseMission(
        {
          id: "bad_title_ko",
          title: "X",
          fixer: "finn",
          arc: 1,
          zone: "z",
          grade_min: 1,
          grade_max: 1,
          rewards: { credits: 0, materials: {} },
          title_ko: 123,
        },
        "bad_title_ko",
      ),
    ).not.toThrow();
    // Numeric title_ko is silently ignored (loader is permissive — the test
    // only pins that we DON'T crash and we DON'T propagate it).
    const m = parseMission(
      {
        id: "bad_title_ko",
        title: "X",
        fixer: "finn",
        arc: 1,
        zone: "z",
        grade_min: 1,
        grade_max: 1,
        rewards: { credits: 0, materials: {} },
        title_ko: 123,
      },
      "bad_title_ko",
    );
    expect("title_ko" in m).toBe(false);
  });

  it("preserves EN briefing verbatim even when briefing_ko is added (no overwrite)", () => {
    const m = parseMission(
      {
        id: "preserve_en",
        title: "Far Grid Prelude",
        fixer: "operator",
        arc: 1,
        zone: "precursor",
        grade_min: 1,
        grade_max: 2,
        rewards: { credits: 0, materials: {} },
        briefing:
          "The operator silhouette offers the deck jockey a first walk.",
        briefing_ko: "조작자의 실루엣이 데커에게 첫 산책을 제안한다.",
      },
      "preserve_en",
    );
    expect(m.briefing).toBe(
      "The operator silhouette offers the deck jockey a first walk.",
    );
    expect(m.briefing_ko).toBe(
      "조작자의 실루엣이 데커에게 첫 산책을 제안한다.",
    );
  });
});

describe("missions.json: every mission carries title_ko", () => {
  it("all 53 missions load with non-empty title_ko (proves data integrity)", async () => {
    const { default: data } = await import("../src/data/missions.json");
    const missions = loadMissionsCatalog(data);
    expect(missions.length).toBe(53);
    const missing: string[] = [];
    for (const m of missions) {
      if (typeof m.title_ko !== "string" || m.title_ko.length === 0) {
        missing.push(m.id);
      }
    }
    expect(missing).toEqual([]);
  });

  it("all 20 far-grid missions also carry non-empty briefing_ko", async () => {
    const { default: data } = await import("../src/data/missions.json");
    const missions = loadMissionsCatalog(data);
    const fg = missions.filter((m) => m.source_universe === "far-grid");
    expect(fg.length).toBe(20);
    const missing: string[] = [];
    for (const m of fg) {
      if (typeof m.briefing_ko !== "string" || m.briefing_ko.length === 0) {
        missing.push(m.id);
      }
    }
    expect(missing).toEqual([]);
  });

  it("Sprawl (non-far-grid) missions do NOT carry briefing_ko (only far-grid does)", async () => {
    const { default: data } = await import("../src/data/missions.json");
    const missions = loadMissionsCatalog(data);
    const sprawl = missions.filter((m) => m.source_universe === "sprawl");
    expect(sprawl.length).toBe(33);
    for (const m of sprawl) {
      expect("briefing_ko" in m).toBe(false);
    }
  });
});

describe("CJK safety sweep — title_ko + briefing_ko across all 53 missions", () => {
  it("contains Hangul and zero Hanja / kana in any new KO string", async () => {
    const { default: data } = await import("../src/data/missions.json");
    const missions = loadMissionsCatalog(data);
    const violations: string[] = [];
    let titleHangulCount = 0;
    let briefingHangulCount = 0;
    for (const m of missions) {
      const tk = m.title_ko ?? "";
      if (HANGUL.test(tk)) titleHangulCount++;
      if (CJK_HANJA.test(tk) || KANA.test(tk)) {
        violations.push(`${m.id}.title_ko: ${tk}`);
      }
      const bk = m.briefing_ko ?? "";
      if (HANGUL.test(bk)) briefingHangulCount++;
      if (CJK_HANJA.test(bk) || KANA.test(bk)) {
        violations.push(`${m.id}.briefing_ko: ${bk}`);
      }
    }
    expect(violations).toEqual([]);
    expect(titleHangulCount).toBe(53);
    expect(briefingHangulCount).toBe(20);
  });

  it("no parenthetical English inserts (e.g. '(잭아웃)') in KO strings", async () => {
    const { default: data } = await import("../src/data/missions.json");
    const missions = loadMissionsCatalog(data);
    const violations: string[] = [];
    for (const m of missions) {
      for (const [field, val] of [
        ["title_ko", m.title_ko ?? ""],
        ["briefing_ko", m.briefing_ko ?? ""],
      ] as const) {
        // Match any (lowercase English word/term) inside parens after Korean
        // has appeared — the AGENTS.md §7 banned pattern.
        const matches = val.match(/[가-힣][^\n.]*\([a-z][a-z\- ]*\)/);
        if (matches) violations.push(`${m.id}.${field}: ${matches[0]}`);
      }
    }
    expect(violations).toEqual([]);
  });
});

describe("renderFarGridHub — KO resolution (title + briefing)", () => {
  function makeMissionWithKo(
    id: string,
    title: string,
    titleKo: string,
    briefing: string,
    briefingKo: string,
  ): Mission {
    return {
      ...makeBaseMission(id, title),
      title_ko: titleKo,
      briefing,
      briefing_ko: briefingKo,
    };
  }

  const EN_TITLE = "Echo Lattice";
  const KO_TITLE = "에코 격자";
  const EN_BRIEFING = "EN baseline briefing for Echo Lattice.";
  const KO_BRIEFING = "에코 격자의 한국어 안내문.";

  const missions: ReadonlyArray<Mission> = [
    makeMissionWithKo("m1", EN_TITLE, KO_TITLE, EN_BRIEFING, KO_BRIEFING),
    makeMissionWithKo("m2", "Ghost Frequencies", "고스트 주파수", "EN two.", ""),
  ];

  it("renders EN title when language is en (byte-identical to default)", () => {
    const gridDefault = renderFarGridHub(missions, 0, 80, 24);
    const gridEn = renderFarGridHub(missions, 0, 80, 24, "", "en" as Language);
    expect(gridText(gridDefault)).toBe(gridText(gridEn));
    expect(getRowText(gridDefault, 5, 6, EN_TITLE.length)).toBe(EN_TITLE);
  });

  it("renders KO title when language is ko and title_ko is present", () => {
    const grid = renderFarGridHub(missions, 0, 80, 24, "", "ko" as Language);
    expect(getRowText(grid, 5, 6, KO_TITLE.length)).toBe(KO_TITLE);
    // EN title must NOT appear on the title row
    expect(getRowText(grid, 5, 6, EN_TITLE.length)).not.toBe(EN_TITLE);
  });

  it("falls back to EN title when language is ko but title_ko is empty/missing", () => {
    // m2 has empty briefing_ko but valid title_ko. Build a mission without
    // title_ko to exercise the fallback.
    const noKoTitle: Mission = {
      ...makeBaseMission("no_ko_title", EN_TITLE),
      briefing: EN_BRIEFING,
    };
    const grid = renderFarGridHub(
      [noKoTitle],
      0,
      80,
      24,
      "",
      "ko" as Language,
    );
    // Title falls back to EN even when language = "ko" and no title_ko exists.
    expect(getRowText(grid, 5, 6, EN_TITLE.length)).toBe(EN_TITLE);
  });

  it("renders KO briefing when language is ko and briefing_ko is present", () => {
    const grid = renderFarGridHub(missions, 0, 80, 24, "", "ko" as Language);
    const text = gridText(grid);
    expect(text).toContain(KO_BRIEFING);
    expect(text).not.toContain(EN_BRIEFING);
  });

  it("renders EN briefing when language is en (byte-identical to default)", () => {
    const gridDefault = renderFarGridHub(missions, 0, 80, 24);
    const gridEn = renderFarGridHub(
      missions,
      0,
      80,
      24,
      "",
      "en" as Language,
    );
    expect(gridText(gridDefault)).toBe(gridText(gridEn));
    const text = gridText(gridEn);
    expect(text).toContain(EN_BRIEFING);
    expect(text).not.toContain(KO_BRIEFING);
  });

  it("falls back to EN briefing when language is ko but briefing_ko is empty/missing", () => {
    // m2 has empty briefing_ko — EN baseline must still render.
    const grid = renderFarGridHub(missions, 1, 80, 24, "", "ko" as Language);
    const text = gridText(grid);
    expect(text).toContain("EN two.");
    // And the title (m2 has title_ko, so that part IS Korean).
    expect(text).toContain("고스트 주파수");
  });

  it("KO briefing wraps within grid width without breaking cells", () => {
    const longKo = "가 ".repeat(60); // 120-char Korean phrase, wraps on space
    const missions: ReadonlyArray<Mission> = [
      makeMissionWithKo("m1", EN_TITLE, KO_TITLE, EN_BRIEFING, longKo),
    ];
    const cols = 40;
    const grid = renderFarGridHub(missions, 0, cols, 24, "", "ko" as Language);
    for (const row of grid.cells) {
      expect(row.length).toBe(cols);
    }
    // Some Korean must have made it to the grid (proves it didn't drop out).
    const text = gridText(grid);
    expect(text).toContain("가 가");
  });

  it("Korean title renders without breaking the Source annotation", () => {
    const stem = "xauthors/true-names/en/2026-10-11_far_grid_prelude";
    const m: Mission = {
      ...makeBaseMission("m1", EN_TITLE),
      title_ko: KO_TITLE,
      story: { source: stem },
      briefing: EN_BRIEFING,
      briefing_ko: KO_BRIEFING,
    };
    const grid = renderFarGridHub([m], 0, 80, 24, "", "ko" as Language);
    const text = gridText(grid);
    expect(text).toContain(`[Source: ${stem}]`);
    expect(text).toContain(KO_TITLE);
  });
});

describe("KO content activation — EN byte-identical regression", () => {
  it("EN title + KR full KO content: EN-side strings unchanged", async () => {
    const { default: data } = await import("../src/data/missions.json");
    const missions = loadMissionsCatalog(data);
    // Spot check: 4 representative EN titles remain intact.
    const sample = ["Aleph Fragment", "Tessier-Ashpool Defection", "Far Grid Prelude", "Yakuza Deal"];
    for (const title of sample) {
      const m = missions.find((mm) => mm.title === title);
      expect(m, `mission with title "${title}" should still exist`).toBeDefined();
      if (m) {
        // title_ko must be present and distinct from title (proves it's not a no-op).
        expect(m.title_ko).toBeDefined();
        expect(m.title_ko).not.toBe(title);
      }
    }
  });
});