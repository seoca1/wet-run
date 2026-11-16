/**
 * ADR-0300 — a line that does not fit must fail the build, not lose its digits.
 *
 * The loot screen shipped twice with prices cut mid-number ("+75 HP → 2") because
 * a line can only be checked against a width at the moment it is drawn. `setText`
 * now records what it had to cut, so a test can render every screen at every
 * layout and assert the list is empty.
 *
 * The first case proves the instrument works — a guard that can silently record
 * nothing is worse than no guard.
 */
import { describe, expect, it } from "vitest";
import { makeGrid, setText, takeClippedText } from "../src/core/grid";
import { setInnerText } from "../src/renderer/panel";
import { renderRunScreen } from "../src/renderer/run_screen";
import { renderMainMenu } from "../src/renderer/menu";
import { renderJockeySelect } from "../src/renderer/jockey_select";
import { renderMissionList } from "../src/renderer/mission_select";
import { renderMissionBriefing } from "../src/renderer/menu_dialogue";
import { renderRunIntro } from "../src/renderer/run_intro";
import { renderBeatCard } from "../src/renderer/beat_card";
import { renderEndingScreen } from "../src/renderer/ending";
import {
  dialogueBeat,
  endingSignoffBeat,
  firstFightWarningBeat,
  iceIntroBeat,
} from "../src/core/state/event_beats";
import { runState } from "./view_fixtures";

const LAYOUTS = [
  [40, 60],
  [60, 40],
  [80, 50],
] as const;

function lootState() {
  const base = runState({
    runPhase: "loot",
    message: "Recovered +500 credits. Loot: ice_shard x2",
  });
  return {
    ...base,
    player: { ...base.player, alarm: 80, hp: 150, maxHp: 300 },
  };
}

/** ADR-0311: the free unique pick renders in the same panel. */
function uniquePickState() {
  const base = runState({ runPhase: "loot", message: "wisp defeated!" });
  return {
    ...base,
    iceRoster: [{ ...base.iceRoster[0], tier: 6 }],
    uniquePickDone: false,
  };
}

describe("ADR-0300 · the cut recorder", () => {
  it("records a line that runs past the right edge", () => {
    // Given: a 10-column grid.
    const grid = makeGrid(10, 3);
    takeClippedText();

    // When: 16 characters are drawn at x = 0.
    setText(grid, 0, 0, "0123456789ABCDEF");

    // Then: the whole string is recorded, so the caller can name it.
    expect(takeClippedText()).toEqual(["0123456789ABCDEF"]);
  });

  it("records nothing when the line fits, and drains on read", () => {
    // Given
    const grid = makeGrid(20, 3);
    takeClippedText();

    // When
    setText(grid, 2, 0, "fits fine");

    // Then: empty, and the record stays empty on the next read.
    expect(takeClippedText()).toEqual([]);
    expect(takeClippedText()).toEqual([]);
  });

  // ADR-0300 (2026-11-16): the recorder used to watch only the right edge. A
  // line pushed off the bottom of the screen was lost just as silently, so the
  // instrument has to see both.
  it("records a line drawn past the bottom edge", () => {
    const grid = makeGrid(20, 3);
    takeClippedText();

    setText(grid, 0, 7, "off the bottom");

    expect(takeClippedText()).toEqual(["off the bottom"]);
  });

  it("records a line a panel drops off its bottom", () => {
    const grid = makeGrid(20, 10);
    const inner = { x: 1, y: 1, width: 18, height: 4 };
    takeClippedText();

    setInnerText(grid, inner, 2, 9, "ESC: jack out");

    expect(takeClippedText()).toEqual(["ESC: jack out"]);
  });
});

describe.each([
  ["loot with a full trace", lootState()],
  ["unique pick", uniquePickState()],
  ["loot with no trace", runState({ runPhase: "loot", message: "No rewards" })],
  ["matrix", runState({ runPhase: "matrix" })],
  ["ending", runState({ runPhase: "ending", endingChoice: "arc4_liberation_front" })],
] as const)("ADR-0300 · %s", (_name, state) => {
  it.each(LAYOUTS)("draws nothing past the edge at %ix%i", (w, h) => {
    // Given / When
    takeClippedText();
    renderRunScreen(state as never, w, h);

    // Then
    expect(takeClippedText()).toEqual([]);
  });
});

// ADR-0315: the menu is a panel screen too, and its rows are the longest in
// the game — the redesign put a description on every line, so the guard must
// cover it or a 40-column layout can eat the right edge silently.
describe("ADR-0300 · main menu", () => {
  it.each(LAYOUTS)("draws nothing past the edge at %ix%i", (w, h) => {
    takeClippedText();
    renderMainMenu(0, w, h, true, { missionId: "aleph_fragment", turnCount: 3 });
    expect(takeClippedText()).toEqual([]);
  });
});

// ADR-0315: the jockey screen carries a tagline and a deck line per entry, and
// the first boot now lands here — it must not cut a word at 40 columns.
describe("ADR-0300 · jockey select", () => {
  it.each(LAYOUTS)("draws nothing past the edge at %ix%i", (w, h) => {
    takeClippedText();
    renderJockeySelect(0, w, h);
    expect(takeClippedText()).toEqual([]);
  });
});

// ADR-0316: the mission select shows the selected mission's briefing under the
// list — the longest free text on a pre-game screen.
describe("ADR-0300 · mission select", () => {
  it.each(LAYOUTS)("draws nothing past the edge at %ix%i", (w, h) => {
    takeClippedText();
    renderMissionList(
      ["[1] First Jack   T1  500cr", "[2] Data Retrieval   T2  800cr"],
      0,
      w,
      h,
      "Case experiences the thirty seconds after jack-out — the shaking hands, the matrix.",
    );
    expect(takeClippedText()).toEqual([]);
  });
});

// ADR-0317: the briefing screen carries the mission's story as the fixer's
// words — free text again, and the footer must fit.
describe("ADR-0300 · mission briefing", () => {
  it.each(LAYOUTS)("draws nothing past the edge at %ix%i", (w, h) => {
    takeClippedText();
    renderMissionBriefing(
      "First Jack",
      "finn",
      "Case experiences the thirty seconds after jack-out — the shaking hands, the matrix.",
      w,
      h,
    );
    expect(takeClippedText()).toEqual([]);
  });
});

// ADR-0317 (3b): the run's opening card now carries the companion's beat — the
// longest free text on the card, and it must wrap rather than cut.
describe("ADR-0300 · run intro with a beat", () => {
  it.each(LAYOUTS)("draws nothing past the edge at %ix%i", (w, h) => {
    takeClippedText();
    renderRunIntro(1, w, h, "CASE", dialogueBeat("dixie_intro"));
    expect(takeClippedText()).toEqual([]);
  });
});

// ADR-0317 (3b): the mid-run beats are full-screen cards — the same "longest
// free text on the screen" risk as the run intro.
describe("ADR-0300 · beat card", () => {
  it.each(LAYOUTS)("draws nothing past the edge at %ix%i", (w, h) => {
    takeClippedText();
    renderBeatCard("ICE AHEAD", firstFightWarningBeat()!, w, h);
    expect(takeClippedText()).toEqual([]);
  });
});

// ADR-0317 (3b): the ending screen carries the construct's sign-off under the
// verdict, above the run's numbers.
describe("ADR-0300 · ending with a sign-off", () => {
  it.each(LAYOUTS)("draws nothing past the edge at %ix%i", (w, h) => {
    takeClippedText();
    renderEndingScreen(
      "arc2_status_quo",
      w,
      h,
      {
        mission: "First Jack",
        jockey: "CASE",
        hp: 40,
        maxHp: 100,
        credits: 1234,
        turns: 12,
      },
      endingSignoffBeat(),
    );
    expect(takeClippedText()).toEqual([]);
  });
});
// ADR-0317 (3b): the ICE's tagline is free text on the encounter screen, and it
// must wrap rather than cut. The worst case is deliberate: the 60x40 layout
// with three ICE on the node and Black ICE's three-voice tagline is what pushed
// the "ESC: jack out" footer off the bottom (2026-11-16) — the guard has to
// watch the bottom edge too, or that loss is silent.
describe("ADR-0300 · encounter with an ICE voice", () => {
  it.each(LAYOUTS)("draws nothing past the edge at %ix%i", (w, h) => {
    const base = runState({ runPhase: "matrix" });
    const iceIds = ["black", "black", "black"];
    const state = {
      ...base,
      currentNodeIndex: 0,
      encounterDecision: { selectedVerb: null, probed: true },
      matrix: {
        startNode: 0,
        bossNode: 1,
        nodes: [
          {
            id: 0,
            zone: "surface",
            iceIds,
            iceHp: iceIds.map(() => 20),
            reward: { credits: 75 },
            adjacent: [1],
            isBoss: false,
          },
          {
            id: 1,
            zone: "mid",
            iceIds: [],
            iceHp: [],
            reward: { credits: 0 },
            adjacent: [0],
            isBoss: true,
          },
        ],
      },
    };
    takeClippedText();
    renderRunScreen(state as never, w, h, false, null, null, {
      iceVoice: iceIntroBeat("black"),
    });
    expect(takeClippedText()).toEqual([]);
  });
});
