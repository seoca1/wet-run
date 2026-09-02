/** i18n Manager — internationalization support for English/Korean. */

export type Language = "en" | "ko";

export interface I18nState {
  readonly language: Language;
  readonly translations: Readonly<Record<string, string>>;
}

const EN_TRANSLATIONS: Readonly<Record<string, string>> = Object.freeze({
  // Menu
  "menu.new_run": "NEW RUN",
  "menu.graphic_novel": "GRAPHIC NOVEL",
  "menu.continue": "CONTINUE",
  "menu.settings": "SETTINGS",
  "menu.credits": "CREDITS",
  "menu.hall_of_dead": "HALL OF DEAD",
  "menu.help": "HELP",
  "menu.back": "BACK",
  
  // Game
  "game.credits": "CREDITS",
  "game.hp": "HP",
  "game.ap": "AP",
  "game.level": "LEVEL",
  "game.mission": "MISSION",
  
  // Combat
  "combat.attack": "ATTACK",
  "combat.defend": "DEFEND",
  "combat.skill": "SKILL",
  "combat.item": "ITEM",
  "combat.flee": "FLEE",
  "combat.victory": "VICTORY",
  "combat.defeat": "DEFEAT",
  
  // Settings
  "settings.language": "LANGUAGE",
  "settings.volume": "VOLUME",
  "settings.sfx": "SFX",
  "settings.bgm": "BGM",
  "settings.difficulty": "DIFFICULTY",
  "settings.easy": "EASY",
  "settings.normal": "NORMAL",
  "settings.hard": "HARD",
  
  // Hub
  "hub.bar": "BAR",
  "hub.shop": "SHOP",
  "hub.workshop": "WORKSHOP",
  "hub.medbay": "MEDBAY",
  "hub.command": "COMMAND",
  "hub.dormitory": "DORMITORY",
  
  // Generic
  "common.yes": "YES",
  "common.no": "NO",
  "common.ok": "OK",
  "common.cancel": "CANCEL",
  "common.confirm": "CONFIRM",
  "common.save": "SAVE",
  "common.load": "LOAD",
  "common.delete": "DELETE",
});

const KO_TRANSLATIONS: Readonly<Record<string, string>> = Object.freeze({
  // Menu
  "menu.new_run": "새 런",
  "menu.graphic_novel": "그래픽 노블",
  "menu.continue": "이어서 하기",
  "menu.settings": "설정",
  "menu.credits": "크레딧",
  "menu.hall_of_dead": "죽은 자의 전당",
  "menu.help": "도움말",
  "menu.back": "뒤로",
  
  // Game
  "game.credits": "크레딧",
  "game.hp": "체력",
  "game.ap": "행동력",
  "game.level": "레벨",
  "game.mission": "미션",
  
  // Combat
  "combat.attack": "공격",
  "combat.defend": "방어",
  "combat.skill": "스킬",
  "combat.item": "아이템",
  "combat.flee": "도망",
  "combat.victory": "승리",
  "combat.defeat": "패배",
  
  // Settings
  "settings.language": "언어",
  "settings.volume": "볼륨",
  "settings.sfx": "효과음",
  "settings.bgm": "배경음악",
  "settings.difficulty": "난이도",
  "settings.easy": "쉬움",
  "settings.normal": "보통",
  "settings.hard": "어려움",
  
  // Hub
  "hub.bar": "술집",
  "hub.shop": "상점",
  "hub.workshop": "공방",
  "hub.medbay": "의무실",
  "hub.command": "지휘실",
  "hub.dormitory": "기숙사",
  
  // Generic
  "common.yes": "예",
  "common.no": "아니오",
  "common.ok": "확인",
  "common.cancel": "취소",
  "common.confirm": "확인",
  "common.save": "저장",
  "common.load": "불러오기",
  "common.delete": "삭제",
});

const TRANSLATIONS: Readonly<Record<Language, Readonly<Record<string, string>>>> = Object.freeze({
  en: EN_TRANSLATIONS,
  ko: KO_TRANSLATIONS,
});

/** Get translation for a key. Falls back to English if not found. */
export function t(key: string, language: Language = "en"): string {
  const translations = TRANSLATIONS[language];
  return translations[key] ?? TRANSLATIONS.en[key] ?? key;
}

/** Get all translations for a language. */
export function getTranslations(language: Language): Readonly<Record<string, string>> {
  return TRANSLATIONS[language];
}

const AVAILABLE_LANGUAGES: ReadonlyArray<Language> = Object.freeze(["en", "ko"]);

/** Get available languages. */
export function getAvailableLanguages(): ReadonlyArray<Language> {
  return AVAILABLE_LANGUAGES;
}

/** Check if a language is supported. */
export function isLanguageSupported(lang: string): lang is Language {
  return lang === "en" || lang === "ko";
}

/** Default i18n state. */
export const DEFAULT_I18N_STATE: I18nState = Object.freeze({
  language: "en",
  translations: EN_TRANSLATIONS,
});

/** Create i18n state for a language. */
export function createI18nState(language: Language): I18nState {
  return Object.freeze({
    language,
    translations: TRANSLATIONS[language],
  });
}
