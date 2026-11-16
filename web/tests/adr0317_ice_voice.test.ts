/** ADR-0317 (3b) — the ICE speaks its tagline once you have looked at it.
 *
 * The design file gives a few ICE a tagline and leaves the rest silent. The
 * voice is shown on the encounter screen only after the threat is revealed,
 * because the ICE's identity is what PROBE sells — the tagline must not hand it
 * over for free.
 */
import { describe, expect, it } from "vitest";
import { makeInitialState } from "../src/core/state/state";
import { renderRunScreen } from "../src/renderer/run_screen";
import { iceIntroBeat, type DialogueBeat } from "../src/core/state/event_beats";
import type { GameState } from "../src/core/types";

function onIce(iceId: string, probed: boolean, iceCount = 1): GameState {
  const initial = makeInitialState(
    {
      id: "voice",
      title: "Voice",
      fixer: "test",
      zone: "surface",
      arc: 1,
      grade_min: 1,
      grade_max: 1,
      rewards: { credits: 0, materials: {} },
    },
    { id: iceId, name: iceId, hp: 20, armor: 0, tier: 1 },
    [],
  );
  const iceIds = Array.from({ length: iceCount }, () => iceId);
  return {
    ...initial,
    currentNodeIndex: 0,
    encounterDecision: { selectedVerb: null, probed },
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
}

/** The encounter screen's text, with the given voice drawn on it. */
function screenText(
  state: GameState,
  voice: DialogueBeat | null,
  cols = 80,
  rows = 50,
): string {
  const screen = renderRunScreen(state, cols, rows, false, null, null, { iceVoice: voice });
  return (screen?.grid.cells ?? [])
    .map((row) => row.map((cell) => cell.char).join(""))
    .join("\n");
}

describe("ADR-0317 (3b) — the ICE voice", () => {
  it("speaks the ICE's tagline on the revealed encounter screen", () => {
    const text = screenText(onIce("wisp", true), iceIntroBeat("wisp"));
    expect(text).toContain("Wisp ICE");
    expect(text).toContain("subversion");
    expect(text).toContain("protocol");
  });

  it("stays silent before the threat is revealed", () => {
    // The identity is what PROBE sells; the tagline would give it away. The
    // controller passes no voice here, and the screen must not invent one.
    const text = screenText(onIce("wisp", false), null);
    expect(text).not.toContain("subversion");
    expect(text).toContain("Threat hidden");
  });

  it("adds nothing for a silent ICE", () => {
    const text = screenText(onIce("goliath", true), iceIntroBeat("goliath"));
    expect(text).not.toContain("subversion");
    expect(text).not.toContain("Wisp ICE");
  });

  it("wraps the tagline instead of cutting it at 40 columns", () => {
    const text = screenText(onIce("wisp", true), iceIntroBeat("wisp"), 40, 60);
    expect(text).toContain("subversion");
    expect(text).toContain("protocol");
    for (const row of text.split("\n")) expect(row.length).toBeLessThanOrEqual(40);
  });

  it("keeps the key hints on screen with a voice and a full roster", () => {
    // The footer names the keys that act. A voice that pushes it off the panel
    // would hide the affordance (ADR-0251 rule 5), so it must survive the
    // worst case: three ICE on the node and Black ICE's three-voice tagline.
    for (const [cols, rows] of [
      [40, 60],
      [60, 40],
      [80, 50],
    ] as const) {
      const text = screenText(
        onIce("black", true, 3),
        iceIntroBeat("black"),
        cols,
        rows,
      );
      expect(text, `${cols}x${rows} lost the footer`).toContain("jack out");
      expect(text, `${cols}x${rows} lost the act hint`).toContain("ENTER/SPACE");
    }
  });
});
