/** Expanded Sound System unit tests (25+ tests). */
import { describe, it, expect } from "vitest";
import {
  TRACKS,
  TRANSITION_RULES,
  DEFAULT_SOUND_STATE,
  getTrackForEvent,
  shouldTransition,
  calculateVolume,
  getAllSfxIds,
  getAllBgmTrackIds,
  getTrackInfo,
  type BgmTrackId,
} from "../src/core/sound_system.ts";

describe("TRACKS", () => {
  it("defines all 15 BGM tracks", () => {
    expect(Object.keys(TRACKS)).toHaveLength(15);
  });

  it("title track has correct metadata", () => {
    expect(TRACKS.title).toEqual({
      id: "title",
      volume: 0.7,
      fadeIn: 1000,
      fadeOut: 500,
      loop: true,
    });
  });

  it("menu track has correct metadata", () => {
    expect(TRACKS.menu).toEqual({
      id: "menu",
      volume: 0.5,
      fadeIn: 500,
      fadeOut: 300,
      loop: true,
    });
  });

  it("exploration track has correct metadata", () => {
    expect(TRACKS.exploration).toEqual({
      id: "exploration",
      volume: 0.6,
      fadeIn: 800,
      fadeOut: 500,
      loop: true,
    });
  });

  it("combat_normal track has correct metadata", () => {
    expect(TRACKS.combat_normal).toEqual({
      id: "combat_normal",
      volume: 0.8,
      fadeIn: 200,
      fadeOut: 200,
      loop: true,
    });
  });

  it("combat_boss track has correct metadata", () => {
    expect(TRACKS.combat_boss).toEqual({
      id: "combat_boss",
      volume: 0.9,
      fadeIn: 100,
      fadeOut: 300,
      loop: true,
    });
  });

  it("combat_multi track has correct metadata", () => {
    expect(TRACKS.combat_multi).toEqual({
      id: "combat_multi",
      volume: 0.85,
      fadeIn: 150,
      fadeOut: 200,
      loop: true,
    });
  });

  it("shop track has correct metadata", () => {
    expect(TRACKS.shop).toEqual({
      id: "shop",
      volume: 0.5,
      fadeIn: 600,
      fadeOut: 400,
      loop: true,
    });
  });

  it("ending_good track does not loop", () => {
    expect(TRACKS.ending_good.loop).toBe(false);
    expect(TRACKS.ending_good.volume).toBe(0.8);
  });

  it("ending_bad track does not loop", () => {
    expect(TRACKS.ending_bad.loop).toBe(false);
    expect(TRACKS.ending_bad.fadeOut).toBe(1500);
  });

  it("ending_neutral track does not loop", () => {
    expect(TRACKS.ending_neutral.loop).toBe(false);
  });

  it("death track does not loop", () => {
    expect(TRACKS.death.loop).toBe(false);
    expect(TRACKS.death.fadeOut).toBe(2000);
  });

  it("victory track does not loop", () => {
    expect(TRACKS.victory.loop).toBe(false);
  });

  it("event_special track does not loop", () => {
    expect(TRACKS.event_special.loop).toBe(false);
  });

  it("ambient_low track has low volume", () => {
    expect(TRACKS.ambient_low.volume).toBe(0.3);
    expect(TRACKS.ambient_low.loop).toBe(true);
  });

  it("ambient_high track has low volume", () => {
    expect(TRACKS.ambient_high.volume).toBe(0.4);
    expect(TRACKS.ambient_high.loop).toBe(true);
  });
});

describe("TRANSITION_RULES", () => {
  it("defines 15 transition rules", () => {
    expect(TRANSITION_RULES).toHaveLength(15);
  });

  it("game_start maps to title", () => {
    const rule = TRANSITION_RULES.find((r) => r.event === "game_start");
    expect(rule?.track).toBe("title");
    expect(rule?.priority).toBe(10);
  });

  it("boss_encounter has highest combat priority", () => {
    const rule = TRANSITION_RULES.find((r) => r.event === "boss_encounter");
    expect(rule?.track).toBe("combat_boss");
    expect(rule?.priority).toBe(20);
  });

  it("ending events have highest priority", () => {
    const goodRule = TRANSITION_RULES.find((r) => r.event === "ending_good");
    const badRule = TRANSITION_RULES.find((r) => r.event === "ending_bad");
    const neutralRule = TRANSITION_RULES.find((r) => r.event === "ending_neutral");
    expect(goodRule?.priority).toBe(30);
    expect(badRule?.priority).toBe(30);
    expect(neutralRule?.priority).toBe(30);
  });

  it("player_death has priority 25", () => {
    const rule = TRANSITION_RULES.find((r) => r.event === "player_death");
    expect(rule?.priority).toBe(25);
  });
});

describe("DEFAULT_SOUND_STATE", () => {
  it("starts with null track", () => {
    expect(DEFAULT_SOUND_STATE.currentTrack).toBeNull();
  });

  it("starts unmuted at full volume", () => {
    expect(DEFAULT_SOUND_STATE.volume).toBe(1.0);
    expect(DEFAULT_SOUND_STATE.muted).toBe(false);
  });

  it("starts with no queued track", () => {
    expect(DEFAULT_SOUND_STATE.queue).toBeNull();
  });
});

describe("getTrackForEvent", () => {
  it("returns title track for game_start", () => {
    expect(getTrackForEvent("game_start")).toBe("title");
  });

  it("returns combat_boss for boss_encounter", () => {
    expect(getTrackForEvent("boss_encounter")).toBe("combat_boss");
  });

  it("returns null for unknown event", () => {
    expect(getTrackForEvent("unknown_event")).toBeNull();
  });

  it("handles empty string event", () => {
    expect(getTrackForEvent("")).toBeNull();
  });

  it("returns highest priority when multiple rules match event", () => {
    expect(getTrackForEvent("boss_encounter")).toBe("combat_boss");
  });
});

describe("shouldTransition", () => {
  it("triggers transition when event changes track", () => {
    const result = shouldTransition("title", "combat_start");
    expect(result).toEqual({
      track: "combat_normal",
      immediate: true,
    });
  });

  it("returns null when same track", () => {
    const result = shouldTransition("title", "game_start");
    expect(result).toBeNull();
  });

  it("returns null for unknown event", () => {
    const result = shouldTransition("title", "unknown_event");
    expect(result).toBeNull();
  });

  it("marks quick transitions as immediate", () => {
    const result = shouldTransition(null, "combat_start");
    expect(result?.immediate).toBe(true);
  });

  it("marks slow transitions as not immediate", () => {
    const result = shouldTransition(null, "shop_open");
    expect(result?.immediate).toBe(false);
  });

  it("returns null when currentTrack is null and no event match", () => {
    const result = shouldTransition(null, "nonexistent");
    expect(result).toBeNull();
  });
});

describe("calculateVolume", () => {
  it("multiplies track volume by master volume", () => {
    expect(calculateVolume("title", 1.0)).toBe(0.7);
    expect(calculateVolume("menu", 1.0)).toBe(0.5);
  });

  it("applies master volume scaling", () => {
    expect(calculateVolume("title", 0.5)).toBe(0.35);
    expect(calculateVolume("combat_boss", 0.5)).toBe(0.45);
  });

  it("clamps to 0 minimum", () => {
    expect(calculateVolume("title", 0)).toBe(0);
  });

  it("clamps to 1 maximum", () => {
    expect(calculateVolume("combat_boss", 2.0)).toBe(1);
  });

  it("handles zero master volume", () => {
    expect(calculateVolume("combat_boss", 0)).toBe(0);
  });

  it("returns 0 for invalid track", () => {
    expect(calculateVolume("invalid_track" as BgmTrackId, 1.0)).toBe(0);
  });
});

describe("getAllSfxIds", () => {
  it("returns 15 SFX IDs", () => {
    const ids = getAllSfxIds();
    expect(ids).toHaveLength(15);
  });

  it("includes all expected SFX", () => {
    const ids = getAllSfxIds();
    expect(ids).toContain("click");
    expect(ids).toContain("confirm");
    expect(ids).toContain("back");
    expect(ids).toContain("equip");
    expect(ids).toContain("heal");
    expect(ids).toContain("damage");
    expect(ids).toContain("attack");
    expect(ids).toContain("ice_break");
    expect(ids).toContain("loot_drop");
    expect(ids).toContain("credit_gain");
    expect(ids).toContain("credit_spend");
    expect(ids).toContain("death");
    expect(ids).toContain("victory");
    expect(ids).toContain("boss_intro");
    expect(ids).toContain("phase_change");
  });

  it("returns frozen array", () => {
    const ids = getAllSfxIds();
    expect(Object.isFrozen(ids)).toBe(true);
  });
});

describe("getAllBgmTrackIds", () => {
  it("returns 15 BGM track IDs", () => {
    const ids = getAllBgmTrackIds();
    expect(ids).toHaveLength(15);
  });

  it("includes all expected tracks", () => {
    const ids = getAllBgmTrackIds();
    expect(ids).toContain("title");
    expect(ids).toContain("menu");
    expect(ids).toContain("exploration");
    expect(ids).toContain("combat_normal");
    expect(ids).toContain("combat_boss");
    expect(ids).toContain("combat_multi");
    expect(ids).toContain("shop");
    expect(ids).toContain("ending_good");
    expect(ids).toContain("ending_bad");
    expect(ids).toContain("ending_neutral");
    expect(ids).toContain("death");
    expect(ids).toContain("victory");
    expect(ids).toContain("event_special");
    expect(ids).toContain("ambient_low");
    expect(ids).toContain("ambient_high");
  });

  it("returns frozen array", () => {
    const ids = getAllBgmTrackIds();
    expect(Object.isFrozen(ids)).toBe(true);
  });
});

describe("getTrackInfo", () => {
  it("returns info for valid track", () => {
    const info = getTrackInfo("title");
    expect(info?.volume).toBe(0.7);
    expect(info?.loop).toBe(true);
  });

  it("returns undefined for invalid track", () => {
    const info = getTrackInfo("invalid_track" as BgmTrackId);
    expect(info).toBeUndefined();
  });

  it("returns correct info for all tracks", () => {
    const ids = getAllBgmTrackIds();
    ids.forEach((id) => {
      const info = getTrackInfo(id);
      expect(info).toBeDefined();
      expect(info?.id).toBe(id);
    });
  });
});
