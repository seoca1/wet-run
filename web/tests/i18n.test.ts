/** i18n tests (Korean internationalization support). */
import { describe, it, expect } from "vitest";
import {
  t,
  getTranslations,
  getAvailableLanguages,
  isLanguageSupported,
  DEFAULT_I18N_STATE,
  createI18nState,
  type Language,
} from "../src/core/i18n.ts";

describe("t() - translation lookup", () => {
  it("returns English translation for valid key", () => {
    expect(t("menu.new_run", "en")).toBe("NEW RUN");
    expect(t("combat.attack", "en")).toBe("ATTACK");
    expect(t("common.yes", "en")).toBe("YES");
  });

  it("returns Korean translation for valid key", () => {
    expect(t("menu.new_run", "ko")).toBe("새 런");
    expect(t("combat.attack", "ko")).toBe("공격");
    expect(t("common.yes", "ko")).toBe("예");
  });

  it("defaults to English when language not specified", () => {
    expect(t("menu.settings")).toBe("SETTINGS");
  });

  it("falls back to English when Korean translation missing", () => {
    expect(t("missing.key", "ko")).toBe(t("missing.key", "en"));
  });

  it("returns key when no translation exists", () => {
    expect(t("completely.missing", "en")).toBe("completely.missing");
    expect(t("completely.missing", "ko")).toBe("completely.missing");
  });
});

describe("getTranslations()", () => {
  it("returns all English translations", () => {
    const en = getTranslations("en");
    expect(en["menu.new_run"]).toBe("NEW RUN");
    expect(en["combat.attack"]).toBe("ATTACK");
    expect(Object.keys(en).length).toBeGreaterThan(30);
  });

  it("returns all Korean translations", () => {
    const ko = getTranslations("ko");
    expect(ko["menu.new_run"]).toBe("새 런");
    expect(ko["combat.attack"]).toBe("공격");
    expect(Object.keys(ko).length).toBeGreaterThan(30);
  });

  it("returns frozen objects", () => {
    const en = getTranslations("en");
    expect(Object.isFrozen(en)).toBe(true);
  });
});

describe("getAvailableLanguages()", () => {
  it("returns en and ko", () => {
    const langs = getAvailableLanguages();
    expect(langs).toEqual(["en", "ko"]);
  });

  it("returns frozen array", () => {
    const langs = getAvailableLanguages();
    expect(Object.isFrozen(langs)).toBe(true);
  });
});

describe("isLanguageSupported()", () => {
  it("returns true for en", () => {
    expect(isLanguageSupported("en")).toBe(true);
  });

  it("returns true for ko", () => {
    expect(isLanguageSupported("ko")).toBe(true);
  });

  it("returns false for unsupported languages", () => {
    expect(isLanguageSupported("fr")).toBe(false);
    expect(isLanguageSupported("ja")).toBe(false);
    expect(isLanguageSupported("")).toBe(false);
  });

  it("narrows type correctly", () => {
    const lang = "en" as string;
    if (isLanguageSupported(lang)) {
      const typed: Language = lang;
      expect(typed).toBe("en");
    }
  });
});

describe("DEFAULT_I18N_STATE", () => {
  it("has English as default language", () => {
    expect(DEFAULT_I18N_STATE.language).toBe("en");
  });

  it("has English translations", () => {
    expect(DEFAULT_I18N_STATE.translations["menu.new_run"]).toBe("NEW RUN");
  });

  it("is frozen", () => {
    expect(Object.isFrozen(DEFAULT_I18N_STATE)).toBe(true);
    expect(Object.isFrozen(DEFAULT_I18N_STATE.translations)).toBe(true);
  });
});

describe("createI18nState()", () => {
  it("creates English state", () => {
    const state = createI18nState("en");
    expect(state.language).toBe("en");
    expect(state.translations["menu.new_run"]).toBe("NEW RUN");
  });

  it("creates Korean state", () => {
    const state = createI18nState("ko");
    expect(state.language).toBe("ko");
    expect(state.translations["menu.new_run"]).toBe("새 런");
  });

  it("returns frozen state", () => {
    const state = createI18nState("en");
    expect(Object.isFrozen(state)).toBe(true);
    expect(Object.isFrozen(state.translations)).toBe(true);
  });
});

describe("translation coverage - menu keys", () => {
  const menuKeys = [
    "menu.new_run",
    "menu.graphic_novel",
    "menu.continue",
    "menu.settings",
    "menu.credits",
    "menu.hall_of_dead",
    "menu.help",
    "menu.back",
  ];

  it("all menu keys have English translations", () => {
    const en = getTranslations("en");
    for (const key of menuKeys) {
      expect(en[key]).toBeDefined();
      expect(typeof en[key]).toBe("string");
      expect(en[key].length).toBeGreaterThan(0);
    }
  });

  it("all menu keys have Korean translations", () => {
    const ko = getTranslations("ko");
    for (const key of menuKeys) {
      expect(ko[key]).toBeDefined();
      expect(typeof ko[key]).toBe("string");
      expect(ko[key].length).toBeGreaterThan(0);
    }
  });
});

describe("translation coverage - combat keys", () => {
  const combatKeys = [
    "combat.attack",
    "combat.defend",
    "combat.skill",
    "combat.item",
    "combat.flee",
    "combat.victory",
    "combat.defeat",
  ];

  it("all combat keys have English translations", () => {
    const en = getTranslations("en");
    for (const key of combatKeys) {
      expect(en[key]).toBeDefined();
      expect(typeof en[key]).toBe("string");
      expect(en[key].length).toBeGreaterThan(0);
    }
  });

  it("all combat keys have Korean translations", () => {
    const ko = getTranslations("ko");
    for (const key of combatKeys) {
      expect(ko[key]).toBeDefined();
      expect(typeof ko[key]).toBe("string");
      expect(ko[key].length).toBeGreaterThan(0);
    }
  });
});

describe("translation coverage - settings keys", () => {
  const settingsKeys = [
    "settings.language",
    "settings.volume",
    "settings.sfx",
    "settings.bgm",
    "settings.difficulty",
    "settings.easy",
    "settings.normal",
    "settings.hard",
  ];

  it("all settings keys have English translations", () => {
    const en = getTranslations("en");
    for (const key of settingsKeys) {
      expect(en[key]).toBeDefined();
      expect(typeof en[key]).toBe("string");
      expect(en[key].length).toBeGreaterThan(0);
    }
  });

  it("all settings keys have Korean translations", () => {
    const ko = getTranslations("ko");
    for (const key of settingsKeys) {
      expect(ko[key]).toBeDefined();
      expect(typeof ko[key]).toBe("string");
      expect(ko[key].length).toBeGreaterThan(0);
    }
  });
});

describe("translation coverage - hub keys", () => {
  const hubKeys = [
    "hub.bar",
    "hub.shop",
    "hub.workshop",
    "hub.medbay",
    "hub.command",
    "hub.dormitory",
  ];

  it("all hub keys have English translations", () => {
    const en = getTranslations("en");
    for (const key of hubKeys) {
      expect(en[key]).toBeDefined();
      expect(typeof en[key]).toBe("string");
      expect(en[key].length).toBeGreaterThan(0);
    }
  });

  it("all hub keys have Korean translations", () => {
    const ko = getTranslations("ko");
    for (const key of hubKeys) {
      expect(ko[key]).toBeDefined();
      expect(typeof ko[key]).toBe("string");
      expect(ko[key].length).toBeGreaterThan(0);
    }
  });
});

describe("translation coverage - common keys", () => {
  const commonKeys = [
    "common.yes",
    "common.no",
    "common.ok",
    "common.cancel",
    "common.confirm",
    "common.save",
    "common.load",
    "common.delete",
  ];

  it("all common keys have English translations", () => {
    const en = getTranslations("en");
    for (const key of commonKeys) {
      expect(en[key]).toBeDefined();
      expect(typeof en[key]).toBe("string");
      expect(en[key].length).toBeGreaterThan(0);
    }
  });

  it("all common keys have Korean translations", () => {
    const ko = getTranslations("ko");
    for (const key of commonKeys) {
      expect(ko[key]).toBeDefined();
      expect(typeof ko[key]).toBe("string");
      expect(ko[key].length).toBeGreaterThan(0);
    }
  });
});

describe("translation coverage - game keys", () => {
  const gameKeys = [
    "game.credits",
    "game.hp",
    "game.ap",
    "game.level",
    "game.mission",
  ];

  it("all game keys have English translations", () => {
    const en = getTranslations("en");
    for (const key of gameKeys) {
      expect(en[key]).toBeDefined();
      expect(typeof en[key]).toBe("string");
      expect(en[key].length).toBeGreaterThan(0);
    }
  });

  it("all game keys have Korean translations", () => {
    const ko = getTranslations("ko");
    for (const key of gameKeys) {
      expect(ko[key]).toBeDefined();
      expect(typeof ko[key]).toBe("string");
      expect(ko[key].length).toBeGreaterThan(0);
    }
  });
});
