/** Main menu renderer barrel (Tier 4, ADR-0207+/ADR-0209).
 *
 * Formerly a 1039-LOC monolith; split 2026-10-12 into focused modules along
 * concern seams. This file is a thin re-export barrel so every existing import
 * path (`./renderer/menu.ts`) and public symbol is preserved:
 *
 *   - menu_main.ts     — MenuOption, MENU_OPTIONS, renderMainMenu, renderStubScreen
 *   - menu_dialogue.ts — renderBriefingScreen, renderTravelScreen,
 *                        renderNPCDialogueScreen, renderGhostEncounterScreen
 *   - menu_stages.ts   — renderExtractDataScreen, renderBypassSecurityScreen,
 *                        renderBlackMarketScreen
 *   - menu_endings.ts  — renderDeathRestartScreen, renderFailedScreen
 */
export * from "./menu_main.ts";
export * from "./menu_dialogue.ts";
export * from "./menu_stages.ts";
export * from "./menu_endings.ts";
