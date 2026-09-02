/** Achievement definitions — extracted from achievements.ts per ADR-0110.
 *
 * Contains all ACH_* constant definitions (28 entries across 5 categories
 * and 4 tiers), catalog arrays, and lookup functions.
 *
 * Categories: COMBAT, EXPLORATION, STORY, MASTERY, HIDDEN
 * Tiers: BRONZE, SILVER, GOLD, PLATINUM
 */

import type { Achievement, AchievementCategory } from "./achievements.ts";

// COMBAT (7)
export const ACH_FIRST_BLOOD: Achievement = {
  id: "first_blood",
  name: "First Blood",
  nameKo: "첫 피",
  description: "첫 번째 ICE를 처치하세요.",
  category: "combat",
  tier: "bronze",
  icon: "\u{1F5E1}",
  rewardCredits: 50,
  hidden: false,
};

export const ACH_SHARPSHOOTER: Achievement = {
  id: "sharpshooter",
  name: "Sharpshooter",
  nameKo: "정밀 사격",
  description: "한 전투에서 10회의 크리티컬 히트를 달성하세요.",
  category: "combat",
  tier: "silver",
  icon: "\u2726",
  rewardCredits: 200,
  hidden: false,
};

export const ACH_COMBO_MASTER: Achievement = {
  id: "combo_master",
  name: "Combo Master",
  nameKo: "콤보 마스터",
  description: "ANNIHILATION 단계의 콤보를 달성하세요.",
  category: "combat",
  tier: "gold",
  icon: "\u2726\u2726\u2726",
  rewardCredits: 500,
  hidden: false,
};

export const ACH_UNDEFEATED: Achievement = {
  id: "undefeated",
  name: "Undefeated",
  nameKo: "무패",
  description: "10번의 전투에서 단 한 번도 쓰러지지 않고 승리하세요.",
  category: "combat",
  tier: "silver",
  icon: "\u2727",
  rewardCredits: 300,
  hidden: false,
};

export const ACH_BOSS_SLAYER: Achievement = {
  id: "boss_slayer",
  name: "Boss Slayer",
  nameKo: "보스 슬레이어",
  description: "첫 BOSS ICE를 처치하세요.",
  category: "combat",
  tier: "gold",
  icon: "\u2620",
  rewardCredits: 1000,
  hidden: false,
};

export const ACH_GOLIATH_SLAYER: Achievement = {
  id: "goliath_slayer",
  name: "Goliath Conqueror",
  nameKo: "골리앗 정복자",
  description: "GOLIATH PRIME를 처치하세요.",
  category: "combat",
  tier: "platinum",
  icon: "\u2605",
  rewardCredits: 2000,
  hidden: false,
};

export const ACH_CENTURION: Achievement = {
  id: "centurion",
  name: "Centurion",
  nameKo: "100 킬",
  description: "누적 100 ICE 처치.",
  category: "combat",
  tier: "gold",
  icon: "\u2726",
  rewardCredits: 1500,
  hidden: false,
};

// EXPLORATION (6)
export const ACH_FIRST_JACKIN: Achievement = {
  id: "first_jackin",
  name: "First Jack-In",
  nameKo: "첫 잭인",
  description: "매트릭스에 처음 진입하세요.",
  category: "exploration",
  tier: "bronze",
  icon: "\u25CE",
  rewardCredits: 50,
  hidden: false,
};

export const ACH_WORLD_WALKER: Achievement = {
  id: "world_walker",
  name: "World Walker",
  nameKo: "월드 워커",
  description: "두 월드(Chiba, Night City) 모두 방문.",
  category: "exploration",
  tier: "silver",
  icon: "\u2295",
  rewardCredits: 300,
  hidden: false,
};

export const ACH_SERVER_DOMINATION: Achievement = {
  id: "server_domination",
  name: "Server Domination",
  nameKo: "서버 점령",
  description: "모든 6개 서버 방문.",
  category: "exploration",
  tier: "gold",
  icon: "\u229E",
  rewardCredits: 1000,
  hidden: false,
};

export const ACH_DATA_EXTRACTOR: Achievement = {
  id: "data_extractor",
  name: "Data Extractor",
  nameKo: "데이터 추출",
  description: "10개의 데이터 노드 추출.",
  category: "exploration",
  tier: "silver",
  icon: "\u25A4",
  rewardCredits: 400,
  hidden: false,
};

export const ACH_JACKOUT_SURVIVOR: Achievement = {
  id: "jackout_survivor",
  name: "Jack-Out Survivor",
  nameKo: "잭아웃 서바이버",
  description: "10번의 잭아웃 생존.",
  category: "exploration",
  tier: "bronze",
  icon: "\u25EF",
  rewardCredits: 200,
  hidden: false,
};

export const ACH_MATRIX_EXPLORER: Achievement = {
  id: "matrix_explorer",
  name: "Matrix Explorer",
  nameKo: "매트릭스 탐험가",
  description: "50개 노드 방문.",
  category: "exploration",
  tier: "gold",
  icon: "\u25C7",
  rewardCredits: 800,
  hidden: false,
};

// STORY (5)
export const ACH_CASE_JOURNEY: Achievement = {
  id: "case_journey",
  name: "Case's Journey",
  nameKo: "케이의 여정",
  description: "케이(초보자) 프롤로그 완료.",
  category: "story",
  tier: "bronze",
  icon: "\u25C9P",
  rewardCredits: 100,
  hidden: false,
};

export const ACH_SIL_AWAKENING: Achievement = {
  id: "sil_awakening",
  name: "Sil's Awakening",
  nameKo: "실의 자각",
  description: "실(베테랑) 프롤로그 완료.",
  category: "story",
  tier: "silver",
  icon: "\u25C9V",
  rewardCredits: 200,
  hidden: false,
};

export const ACH_KAS_RISE: Achievement = {
  id: "kas_rise",
  name: "Kas's Rise",
  nameKo: "카스의 각성",
  description: "카스(헤레틱) 프롤로그 완료.",
  category: "story",
  tier: "gold",
  icon: "\u25C9H",
  rewardCredits: 300,
  hidden: false,
};

export const ACH_FIVE_TALES: Achievement = {
  id: "five_tales",
  name: "Five Tales",
  nameKo: "다섯 단편",
  description: "모든 5개 단편 소설 읽기.",
  category: "story",
  tier: "silver",
  icon: "\u2766",
  rewardCredits: 500,
  hidden: false,
};

export const ACH_THE_TRUTH: Achievement = {
  id: "the_truth",
  name: "The Truth",
  nameKo: "진실",
  description: "모든 3 엔딩 해금.",
  category: "story",
  tier: "platinum",
  icon: "\u2727",
  rewardCredits: 3000,
  hidden: false,
};

// MASTERY (6)
export const ACH_PPL_10: Achievement = {
  id: "ppl_10",
  name: "Apprentice",
  nameKo: "견습생",
  description: "PPL 10 도달.",
  category: "mastery",
  tier: "bronze",
  icon: "\u25B0",
  rewardCredits: 100,
  hidden: false,
};

export const ACH_PPL_20: Achievement = {
  id: "ppl_20",
  name: "Adept",
  nameKo: "숙련자",
  description: "PPL 20 도달.",
  category: "mastery",
  tier: "silver",
  icon: "\u25B0\u25B0",
  rewardCredits: 500,
  hidden: false,
};

export const ACH_PPL_30: Achievement = {
  id: "ppl_30",
  name: "Master",
  nameKo: "달인",
  description: "PPL 30 도달.",
  category: "mastery",
  tier: "gold",
  icon: "\u25B0\u25B0\u25B0",
  rewardCredits: 1500,
  hidden: false,
};

export const ACH_MATRIX_MASTER: Achievement = {
  id: "matrix_master",
  name: "Matrix Master",
  nameKo: "매트릭스 정통",
  description: "PPL 30 + ZDR 30 전투 승리.",
  category: "mastery",
  tier: "platinum",
  icon: "\u25C8",
  rewardCredits: 5000,
  hidden: false,
};

export const ACH_COMBO_QUANT: Achievement = {
  id: "combo_quant",
  name: "Combo Quant",
  nameKo: "콤보 콰이언",
  description: "최대 50 콤보 달성.",
  category: "mastery",
  tier: "gold",
  icon: "\u26A1",
  rewardCredits: 2000,
  hidden: false,
};

export const ACH_FLAWLESS: Achievement = {
  id: "flawless",
  name: "Flawless",
  nameKo: "완벽한 자",
  description: "데미지 없이 50 전투 승리.",
  category: "mastery",
  tier: "platinum",
  icon: "\u2727",
  rewardCredits: 4000,
  hidden: false,
};

// HIDDEN (4)
export const ACH_GHOST_PROTOCOL: Achievement = {
  id: "ghost_protocol",
  name: "Ghost Protocol",
  nameKo: "고스트 프로토콜",
  description: "한 번의 매트릭스 진입에서 단 한 번의 전투도 하지 않고 데이터 3개 추출.",
  category: "hidden",
  tier: "platinum",
  icon: "\u25C7",
  rewardCredits: 3000,
  hidden: true,
};

export const ACH_PHOENIX: Achievement = {
  id: "phoenix",
  name: "Phoenix",
  nameKo: "불사조",
  description: "사망 후 1 HP로 부활.",
  category: "hidden",
  tier: "gold",
  icon: "\u2726",
  rewardCredits: 2000,
  hidden: true,
};

export const ACH_VOID_WALKER: Achievement = {
  id: "void_walker",
  name: "Void Walker",
  nameKo: "보이드 워커",
  description: "BLACK ICE LORD 처치.",
  category: "hidden",
  tier: "platinum",
  icon: "\u2593",
  rewardCredits: 3500,
  hidden: true,
};

export const ACH_TRUE_HACKER: Achievement = {
  id: "true_hacker",
  name: "True Hacker",
  nameKo: "진정한 해커",
  description: "모든 업적 해금.",
  category: "hidden",
  tier: "platinum",
  icon: "\u2605",
  rewardCredits: 10000,
  hidden: true,
};

// Catalog arrays
export const ALL_ACHIEVEMENTS: ReadonlyArray<Achievement> = [
  // Combat
  ACH_FIRST_BLOOD,
  ACH_SHARPSHOOTER,
  ACH_COMBO_MASTER,
  ACH_UNDEFEATED,
  ACH_BOSS_SLAYER,
  ACH_GOLIATH_SLAYER,
  ACH_CENTURION,
  // Exploration
  ACH_FIRST_JACKIN,
  ACH_WORLD_WALKER,
  ACH_SERVER_DOMINATION,
  ACH_DATA_EXTRACTOR,
  ACH_JACKOUT_SURVIVOR,
  ACH_MATRIX_EXPLORER,
  // Story
  ACH_CASE_JOURNEY,
  ACH_SIL_AWAKENING,
  ACH_KAS_RISE,
  ACH_FIVE_TALES,
  ACH_THE_TRUTH,
  // Mastery
  ACH_PPL_10,
  ACH_PPL_20,
  ACH_PPL_30,
  ACH_MATRIX_MASTER,
  ACH_COMBO_QUANT,
  ACH_FLAWLESS,
  // Hidden
  ACH_GHOST_PROTOCOL,
  ACH_PHOENIX,
  ACH_VOID_WALKER,
  ACH_TRUE_HACKER,
];

export const ACHIEVEMENT_BY_ID: Readonly<Record<string, Achievement>> = Object.freeze(
  Object.fromEntries(ALL_ACHIEVEMENTS.map((a) => [a.id, a])),
);

export const ACHIEVEMENT_CATEGORIES: ReadonlyArray<AchievementCategory> = [
  "combat",
  "exploration",
  "story",
  "mastery",
  "hidden",
];

/** Get an achievement by ID, or null if unknown. */
export function getAchievement(achId: string): Achievement | null {
  return ACHIEVEMENT_BY_ID[achId] ?? null;
}

/** Get all achievements in a category (hidden omitted unless requested). */
export function getAchievementsByCategory(
  category: AchievementCategory,
  includeHidden = false,
): ReadonlyArray<Achievement> {
  return ALL_ACHIEVEMENTS.filter(
    (a) => a.category === category && (includeHidden || !a.hidden),
  );
}
