/** Wet Run Web MVP — entry point.
 *
 * Tier 2a (2026-08-25): supports mission select screen (5 missions).
 * Tier 2b (2026-08-26): Howler.js BGM (single track, M to mute).
 * Tier 3 (2026-09-01): Physical gamepad support + responsive layout.
 * Boots the ASCII renderer, mounts keyboard/gamepad input, loads MVP game data,
 * and renders the initial frame.
 */
import { AsciiRenderer } from "./renderer/canvas.ts";
import { KeyboardInput } from "./input/keyboard.ts";
import { GamepadInput, isGamepadConnected } from "./input/gamepad.ts";
import { mountVirtualGamepad, updateProgramRow, isTouchDevice } from "./input/touch.ts";
import { MENU_OPTIONS, renderMainMenu, renderStubScreen, type MenuOption } from "./renderer/menu.ts";
import { renderMatrix } from "./renderer/matrix.ts";
import { renderEndingScreen, renderLootScreen } from "./renderer/ending.ts";
import { composeCombatVfx, advanceVfxListBy, WEB_TICK_MS } from "./renderer/combat_vfx.ts";
import { createTutorialOverlay } from "./renderer/tutorial.ts";
import {
    healthBar,
    healthColor,
    hitFlashColor,
    formatStatusLabel,
    formatStatusGlyph,
    ICE_DEFEAT_ART,
    PLAYER_DEFEAT_ART,
    centerArt,
} from "./renderer/vfx.ts";
import type { GameState, GameAction, GamePhase, Ice, Mission, Program, ScreenKind, GraphicNovelState, Inventory, EquipmentLoadout } from "./core/types.ts";
import { applyAction, buildHudLines, makeInitialState, resolveProgramSelection, slotToGameState, stateToSaveSlot } from "./core/state.ts";
import { makeGrid, setText } from "./core/grid.ts";
import { PALETTE, iceColor } from "./renderer/palette.ts";
import { save as saveToSlot, load as loadFromSlot, hasSave as slotHasSave, getSaveMeta } from "./save/storage.ts";
import { getLayout, watchLayout, type Layout } from "./core/layout.ts";
import { craftItem, makeRecipesFromData, makeMaterialsFromData, type Recipe, type MaterialDef, makeInfoMarket } from "./core/crafting.ts";
import { equipOn, DEFAULT_REGISTRY, EQUIP_SLOTS, makeLoadout } from "./core/equipment.ts";
import type { InfoMarket } from "./core/info_market.ts";

const loadStorySystem = () => import("./core/graphic_novel.ts");
const loadAudioSystem = () => import("./audio/manager.ts");
const loadSettingsRenderer = () => import("./renderer/settings.ts");

import missionsData from "./data/missions.json" with { type: "json" };
import programsData from "./data/programs.json" with { type: "json" };
import iceTypesData from "./data/ice_types.json" with { type: "json" };

type MissionsFile = Readonly<Record<string, Mission>>;
type ProgramsFile = Readonly<Record<string, Program>>;

/** Mission catalog (Tier 2a: 5 curated). */
const MISSIONS: ReadonlyArray<Mission> = Object.values(missionsData as MissionsFile);

/** Pick the ICE type best matched to the mission's `ice_id` (fallback: first). */
function loadIce(mission: Mission, iceTypes: Readonly<Record<string, Ice>>): Ice {
    const keys = Object.keys(iceTypes);
    const preferred = (mission as { ice_id?: string }).ice_id;
    if (preferred && preferred in iceTypes) {
        const ice = iceTypes[preferred];
        if (ice) return ice;
    }
    const first = keys[0];
    if (!first) throw new Error("No ICE types in ice_types.json");
    const fallback = iceTypes[first];
    if (!fallback) throw new Error("ICE entry empty");
    return fallback;
}

/** Build the first 5 programs for the deck (deterministic order from program id). */
function loadDeck(programs: Readonly<Record<string, Program>>, count = 5): ReadonlyArray<Program> {
    const ids = Object.keys(programs)
        .sort()
        .slice(0, count);
    return ids
        .map((id) => {
            const p = programs[id];
            if (!p) return undefined;
            // programs.json entries are keyed by id but don't carry id in the
            // value (legacy schema). Inject it so save/load round-trip works.
            return { ...p, id } as Program;
        })
        .filter((p): p is Program => p !== undefined);
}

/** Format a mission for the select screen (Tier 2a). */
function formatMissionOption(mission: Mission, index: number): string {
    const grade = `T${mission.grade_max}`;
    const credits = mission.rewards.credits.toLocaleString();
    return `${index + 1}. ${mission.title}  [${grade} | ${credits}cr]`;
}

/** Render the mission select screen. */
function renderMissionSelect(
    missions: ReadonlyArray<Mission>,
    selected: number,
    cols: number,
    rows: number,
): ReturnType<typeof makeGrid> {
    let grid = makeGrid(cols, rows);
    grid = setText(grid, 2, 1, "WET RUN — Select Mission", PALETTE.GREEN_NEON);
    grid = setText(grid, 2, 3, "↑↓: navigate | ENTER: launch | ESC: back", PALETTE.GRAY_LIGHT);
    let y = 6;
    for (let i = 0; i < missions.length; i++) {
        const m = missions[i];
        if (!m) continue;
        const isSelected = i === selected;
        const fg = isSelected ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
        const marker = isSelected ? "▸" : " ";
        grid = setText(grid, 4, y, `${marker} ${formatMissionOption(m, i)}`, fg);
        y += 1;
    }
    return grid;
}

class Game {
    private state: GameState | null = null;
    private screen: ScreenKind = "menu";
    private selectedMenuIndex = 0;
    private selectedMission = 0;
    private renderer: AsciiRenderer;
    private input: KeyboardInput;
    private gamepad: GamepadInput;
    private iceTypes: Readonly<Record<string, Ice>>;
    private programs: Readonly<Record<string, Program>>;
    private missions: ReadonlyArray<Mission>;
    private hasSaveCache: boolean = false;
    private saveMetaCache: { missionId: string; turnCount: number; savedAt: string } | null = null;
    private unmountTouch: () => void = () => {};
    private unwatchLayout: () => void = () => {};
    private _lastPhase: GamePhase | null = null;
    private _lastIceHp: number | null = null;
    private _lastFrameMs: number = 0;
    private _lastPlayerHp: number | null = null;
    private inventory: Inventory;
    private equipmentLoadout: EquipmentLoadout;
    private recipes: ReadonlyArray<Recipe>;
    private materials: ReadonlyArray<MaterialDef>;
    private infoMarket: InfoMarket;
    private layout: Layout;
    private tutorialActive = false;
    private tutorialOverlay: ReturnType<typeof createTutorialOverlay> | null = null;
    private graphicNovelPlayer: import("./core/graphic_novel.ts").GraphicNovelPlayer | null = null;
    private graphicNovelState: GraphicNovelState | null = null;
    private gnLanguage: import("./core/graphic_novel_types.ts").Language = "en";
    private settingsState: import("./renderer/settings.ts").SettingsState | null = null;
    private _message: string = "";

    constructor(canvas: HTMLCanvasElement, iceTypes: Readonly<Record<string, Ice>>) {
        this.iceTypes = iceTypes;
        this.programs = programsData as unknown as ProgramsFile;
        this.missions = MISSIONS;
        this.layout = getLayout();
        this.renderer = new AsciiRenderer(canvas, { cellWidth: 8, cellHeight: 16 });
        this.renderer.resizeGrid(this.layout.cols, this.layout.rows, this.layout.hudCols, this.layout.orientation, this.layout.breakpoint);
        this.input = new KeyboardInput();
        this.gamepad = new GamepadInput();
        this.inventory = { credits: 0, materials: {}, programs: [] };
        this.equipmentLoadout = makeLoadout();
        this.recipes = makeRecipesFromData({});
        this.materials = makeMaterialsFromData({});
        this.infoMarket = makeInfoMarket({});
        this.settingsState = null;
        void this.refreshSaveCache();
        const handler = (action: GameAction): void => {
            if (
                this.screen !== "menu" &&
                this.screen !== "mission_select" &&
                this.screen !== "tutorial" &&
                this.screen !== "settings" &&
                this.state === null
            ) {
                this.handleStubInput(action);
                return;
            }
            if (this.tutorialActive && this.tutorialOverlay) {
                const result = this.tutorialOverlay.handleInput(
                    action.type === "jack_out" || action.type === "cancel"
                        ? "Escape"
                        : action.type === "confirm"
                            ? "Enter"
                            : action.type,
                );
                if (result.action === "next" || result.action === "skip") {
                    if (result.action === "skip" || this.tutorialOverlay.state.currentStep >= 6) {
                        this.tutorialActive = false;
                        this.tutorialOverlay = null;
                        this.screen = "menu";
                    }
                    this.draw();
                }
                return;
            }
            if (this.state === null) {
                this.handlePreGameInput(action);
                return;
            }
            if (this.screen === "crafting" || this.screen === "equipment") {
                if (this.screen === "crafting") this.handleCraftingInput(action);
                else this.handleEquipmentInput(action);
                this.draw();
                return;
            }
            const resolved: GameAction = (() => {
                if (this.state === null) return action;
                const r = resolveProgramSelection(this.state, action);
                return r ?? action;
            })();
            const previous = this.state;
            this.state = applyAction(this.state, resolved);
            void loadAudioSystem().then((audio) => {
                const manager = audio.AudioManager.getInstance();
                if (resolved.type === "use_program" && previous.phase === "combat" && this.state?.phase === "combat") {
                    const iceDelta = this.state.ice.hp - previous.ice.hp;
                    if (iceDelta < 0) {
                        manager.playSfx(audio.SFX_IDS.COMBAT_HIT);
                        if (previous.bossPhase > 0 && this.state.bossPhase > previous.bossPhase) {
                            manager.playSfx(audio.SFX_IDS.VICTORY);
                        }
                        this._lastIceHp = this.state.ice.hp;
                        this._lastPlayerHp = this.state.player.hp;
                    }
                    if (previous.runPhase === "matrix" && this.state.runPhase === "combat") {
                        manager.playSfx(audio.SFX_IDS.COMBAT_HIT);
                    }
                    const burnTickDmg = this.state.player.hp - previous.player.hp;
                    if (burnTickDmg > 0 && previous.runPhase === "combat" && this.state.runPhase === "combat") {
                        manager.playSfx(audio.SFX_IDS.DEFEAT);
                    }
                }
            });
            this.draw();
        };
        this.input.setHandler(handler);
        this.input.start();
        if (isTouchDevice()) {
            this.unmountTouch = mountVirtualGamepad(handler);
        }
        this.gamepad.setHandler(handler);
        this.gamepad.start();
        this.unwatchLayout = watchLayout((next) => {
            this.layout = next;
            this.renderer.resizeGrid(next.cols, next.rows, next.hudCols, next.orientation, next.breakpoint);
            this.draw();
        });
    }

    private handleCraftingInput(action: GameAction): void {
        if (action.type === "jack_out" || action.type === "cancel") {
            this.screen = "menu";
            this._message = "";
            this.draw();
            return;
        }
        if (action.type === "select_program") {
            const index = action.handIndex - 1;
            if (index < 0) return;
            // Build list of craftable recipes (those with sufficient materials).
            const craftable: Recipe[] = [];
            for (const recipe of this.recipes) {
                let canCraft = true;
                for (const [mat, qty] of Object.entries(recipe.materials)) {
                    if (this.inventory.materials[mat] ?? 0 < qty) {
                        canCraft = false;
                        break;
                    }
                }
                if (canCraft) craftable.push(recipe);
            }
            if (index >= craftable.length) {
                this._message = "No craftable recipe at that slot.";
                this.draw();
                return;
            }
            const recipe = craftable[index];
            if (!recipe) {
                this.draw();
                return;
            }
            // Use real craftItem API: (recipes, itemId, inventory).
            const result = craftItem(this.recipes, recipe.itemId, this.inventory.materials);
            if (result.ok) {
                // Update inventory: deduct materials + grant credits back is unchanged.
                // Crafting yields a virtual program entry; map craftedItemId back into inventory.programs.
                const craftedProgram: Program = {
                    id: result.craftedItemId,
                    name: recipe.name,
                    tier: recipe.tierLevel,
                    cost: 0,
                    effect: "craft",
                    description: `Crafted from recipe ${recipe.name}`,
                    aoe: false,
                };
                this.inventory = {
                    ...this.inventory,
                    materials: result.newInventory,
                    programs: [...this.inventory.programs, craftedProgram],
                };
                this._message = `Crafted ${recipe.name}!`;
            } else {
                this._message = `Failed to craft ${recipe.name}: ${result.reason}`;
            }
            this.draw();
            return;
        }
    }

    private handleEquipmentInput(action: GameAction): void {
        if (action.type === "jack_out" || action.type === "cancel") {
            this.screen = "menu";
            this._message = "";
            this.draw();
            return;
        }
        if (action.type === "select_program") {
            const slotIndex = action.handIndex - 1;
            if (slotIndex < 0 || slotIndex >= EQUIP_SLOTS.length) return;
            const slot = EQUIP_SLOTS[slotIndex];
            if (!slot) {
                this.draw();
                return;
            }
            // Find the first equipment for this slot in the default registry that isn't already equipped.
            const candidate = DEFAULT_REGISTRY.all.find(
                (e) => e.slot === slot && this.equipmentLoadout.get(slot) === null,
            );
            if (!candidate) {
                this._message = `No available equipment for slot ${slot}`;
                this.draw();
                return;
            }
            const result = equipOn(this.equipmentLoadout, candidate);
            this.equipmentLoadout = result.loadout;
            this._message = `Equipped ${candidate.name} to ${slot}`;
            this.draw();
            return;
        }
    }

    private renderCraftingScreen(): void {
        let grid = makeGrid(this.layout.cols, this.layout.rows);
        let y = 1;
        grid = setText(grid, 2, y, "CRAFTING", PALETTE.GREEN_NEON);
        y += 2;

        // Inventory
        grid = setText(grid, 2, y, `Credits: ${this.inventory.credits}`, PALETTE.GRAY_LIGHT);
        y += 1;
        grid = setText(grid, 2, y, "Materials:", PALETTE.GRAY_LIGHT);
        y += 1;
        const materials = this.inventory.materials;
        if (Object.keys(materials).length === 0) {
            grid = setText(grid, 4, y, "(none)", PALETTE.GRAY_LIGHT);
            y += 1;
        } else {
            for (const [mat, qty] of Object.entries(materials)) {
                grid = setText(grid, 4, y, `- ${mat}: ${qty}`, PALETTE.GRAY_LIGHT);
                y += 1;
            }
        }
        y += 1;

        // Programs in inventory
        grid = setText(grid, 2, y, "Programs in inventory:", PALETTE.GRAY_LIGHT);
        y += 1;
        const programs = this.inventory.programs;
        if (programs.length === 0) {
            grid = setText(grid, 4, y, "(none)", PALETTE.GRAY_LIGHT);
            y += 1;
        } else {
            for (const p of programs) {
                grid = setText(grid, 4, y, `- ${p.name} (T${p.tier})`, PALETTE.CYAN_LIGHT);
                y += 1;
            }
        }
        y += 1;

        // Craftable recipes
        grid = setText(grid, 2, y, "Craftable recipes:", PALETTE.GRAY_LIGHT);
        y += 1;
        let recipeIndex = 1;
        for (const recipe of this.recipes) {
            let canCraft = true;
            for (const [mat, qty] of Object.entries(recipe.materials)) {
                if (this.inventory.materials[mat] ?? 0 < qty) {
                    canCraft = false;
                    break;
                }
            }
            const color = canCraft ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
            const prefix = canCraft ? `${recipeIndex}. ` : "   ";
            grid = setText(grid, 2, y, `${prefix}${recipe.name} (T${recipe.tierLevel})`, color);
            y += 1;
            if (canCraft) {
                const costStr = Object.entries(recipe.materials)
                    .map(([k, v]) => `${k} x${v}`)
                    .join(", ");
                grid = setText(grid, 4, y, `  Cost: ${costStr}`, PALETTE.GRAY_LIGHT);
                y += 1;
                recipeIndex += 1;
            }
        }
        if (recipeIndex === 1) {
            grid = setText(grid, 4, y, "(none)", PALETTE.GRAY_LIGHT);
            y += 1;
        }
        y += 1;

        // Instructions
        grid = setText(grid, 2, y, "Press 1-9 to craft a recipe, ESC to go back", PALETTE.GRAY_LIGHT);
        y += 1;
        if (this.materials.length > 0) {
            const names = this.materials.map((m) => `${m.id} (${m.name})`).join(", ");
            grid = setText(grid, 2, y, `Materials: ${names}`.slice(0, this.layout.cols - 4), PALETTE.GRAY_DARK);
            y += 1;
        }
        if (this.infoMarket.allItems().length > 0) {
            grid = setText(grid, 2, y, `Market items: ${this.infoMarket.allItems().length}`, PALETTE.GRAY_DARK);
            y += 1;
        }
        if (this._message !== "") {
            grid = setText(grid, 2, y, this._message, PALETTE.YELLOW_AMBER);
        }

        this.renderer.render(grid, ["CRAFTING", "", ""]);
    }

    private renderEquipmentScreen(): void {
        let grid = makeGrid(this.layout.cols, this.layout.rows);
        let y = 1;
        grid = setText(grid, 2, y, "EQUIPMENT", PALETTE.GREEN_NEON);
        y += 2;

        // Equipped items
        grid = setText(grid, 2, y, "Equipped:", PALETTE.GRAY_LIGHT);
        y += 1;
        for (const slot of EQUIP_SLOTS) {
            const equip = this.equipmentLoadout.get(slot);
            const name = equip ? equip.name : "(empty)";
            grid = setText(grid, 4, y, `- ${slot}: ${name}`, PALETTE.GRAY_LIGHT);
            y += 1;
        }
        y += 1;

        // Instructions
        grid = setText(grid, 2, y, "Press 1-8 to select slot to auto-equip from registry", PALETTE.GRAY_LIGHT);
        y += 1;
        grid = setText(grid, 2, y, "Press ESC to go back", PALETTE.GRAY_LIGHT);
        if (this._message !== "") {
            y += 2;
            grid = setText(grid, 2, y, this._message, PALETTE.YELLOW_AMBER);
        }

        this.renderer.render(grid, ["EQUIPMENT", "", ""]);
    }

    private initGraphicNovel(): void {
        void loadStorySystem().then((gn) => {
            const player = gn.createPlayer({ mode: "novice" });
            this.graphicNovelPlayer = player;
            this.graphicNovelState = {
                player,
                currentScene: gn.currentScene(player),
                currentText: gn.currentText(player, this.gnLanguage),
                isPaused: false,
            };
            this.draw();
        });
    }

    private renderGraphicNovel(): void {
        if (!this.graphicNovelState || !this.graphicNovelPlayer) return;
        void loadStorySystem().then((gn) => {
            void import("./core/graphic_novel_text.ts").then((gnText) => {
                if (!this.graphicNovelState || !this.graphicNovelPlayer) return;
                const state = this.graphicNovelState;
                const player = this.graphicNovelPlayer;
                const scene = state.currentScene;

                let grid = makeGrid(this.layout.cols, this.layout.rows);

                grid = setText(grid, 2, 1, "GRAPHIC NOVEL", PALETTE.GREEN_NEON);

                if (scene) {
                    const title = gn.currentTitle(player, this.gnLanguage);
                    const speaker = gn.currentSpeaker(player, this.gnLanguage);
                    grid = setText(grid, 2, 3, `Chapter: ${gnText.toRoman(scene.order)}`, PALETTE.GRAY_LIGHT);
                    grid = setText(grid, 2, 4, `Speaker: ${speaker}`, PALETTE.YELLOW_AMBER);
                    grid = setText(grid, 2, 5, `Title: ${title}`, PALETTE.GRAY_LIGHT);
                }

                const wrapped = gnText.wrapTextForNovel(state.currentText, { width: this.layout.cols - 4 });
                const paginated = gnText.paginateLines(wrapped, 15);
                const dialogueText = gn.currentDialogue(player)?.text_en ?? null;
                const typedChars = dialogueText !== null ? dialogueText.length : 0;
                const pageIndex = gnText.computeTypedPageIndex(paginated, typedChars);
                const page = paginated[pageIndex] ?? [];

                let y = 8;
                for (const line of page) {
                    if (y >= this.layout.rows - 2) break;
                    grid = setText(grid, 2, y, line, PALETTE.FOREGROUND);
                    y += 1;
                }

                const progressValue = gn.progress(player);
                const statusText = state.isPaused ? "PAUSED" : "PLAYING";
                grid = setText(
                    grid,
                    2,
                    this.layout.rows - 2,
                    `[${statusText}] Progress: ${Math.round(progressValue * 100)}%`,
                    PALETTE.GRAY_DARK,
                );
                grid = setText(
                    grid,
                    2,
                    this.layout.rows - 1,
                    "ENTER: skip dialogue | P: pause | ESC: exit",
                    PALETTE.GRAY_DARK,
                );

                this.renderer.render(grid, ["GRAPHIC NOVEL", "", ""]);
            });
        });
    }

    private handlePreGameInput(action: GameAction): void {
        // Digit keys 1-9 → menu selection on menu screen (otherwise → combat program select).
        if (action.type === "select_program" && this.screen === "menu") {
            const idx = action.handIndex - 1;
            if (idx >= 0 && idx < MENU_OPTIONS.length) {
                this.selectedMenuIndex = idx;
                const opt = MENU_OPTIONS[idx];
                this.selectMenuOption(opt ? opt.key : undefined);
            }
            return;
        }
        if (this.screen === "menu") {
            if (action.type === "move_south") {
                this.selectedMenuIndex = (this.selectedMenuIndex + 1) % MENU_OPTIONS.length;
                this.draw();
            } else if (action.type === "move_north") {
                this.selectedMenuIndex = (this.selectedMenuIndex - 1 + MENU_OPTIONS.length) % MENU_OPTIONS.length;
                this.draw();
            } else if (action.type === "confirm") {
                const opt = MENU_OPTIONS[this.selectedMenuIndex];
                this.selectMenuOption(opt ? opt.key : undefined);
            } else if (action.type === "jack_out") {
                // No-op: already at top-level menu
                this.draw();
            }
            return;
        }
        if (this.screen === "mission_select") {
            if (action.type === "move_south") {
                this.selectedMission = (this.selectedMission + 1) % MISSIONS.length;
                this.draw();
            } else if (action.type === "move_north") {
                this.selectedMission = (this.selectedMission - 1 + MISSIONS.length) % MISSIONS.length;
                this.draw();
            } else if (action.type === "confirm") {
                this.launchSelected();
            } else if (action.type === "jack_out") {
                this.screen = "menu";
                this.draw();
            }
            return;
        }
        if (this.screen === "settings") {
            void loadAudioSystem().then(async (audio) => {
                const manager = audio.AudioManager.getInstance();
                const settingsModule = await loadSettingsRenderer();
                if (this.settingsState === null) {
                    this.settingsState = settingsModule.getInitialSettingsState();
                }
                const fields: ReadonlyArray<"bgm" | "sfx" | "mute"> = ["bgm", "sfx", "mute"];
                const idx = fields.indexOf(this.settingsState.selectedField);
                if (action.type === "move_south") {
                    const nextIdx = (idx + 1) % fields.length;
                    const nextField = fields[nextIdx] ?? fields[0];
                    if (nextField) this.settingsState = { ...this.settingsState, selectedField: nextField };
                    this.draw();
                } else if (action.type === "move_north") {
                    const prevIdx = (idx - 1 + fields.length) % fields.length;
                    const prevField = fields[prevIdx] ?? fields[0];
                    if (prevField) this.settingsState = { ...this.settingsState, selectedField: prevField };
                    this.draw();
                } else if (action.type === "move_east") {
                    if (this.settingsState.selectedField === "bgm") {
                        const v = (this.settingsState.bgmVolume + 0.1 > 1 ? 1 : Math.round((this.settingsState.bgmVolume + 0.1) * 10) / 10);
                        this.settingsState = { ...this.settingsState, bgmVolume: v };
                        manager.setBgmVolume(v);
                    } else if (this.settingsState.selectedField === "sfx") {
                        const v = (this.settingsState.sfxVolume + 0.1 > 1 ? 1 : Math.round((this.settingsState.sfxVolume + 0.1) * 10) / 10);
                        this.settingsState = { ...this.settingsState, sfxVolume: v };
                        manager.setSfxVolume(v);
                    }
                    this.draw();
                } else if (action.type === "move_west") {
                    if (this.settingsState.selectedField === "bgm") {
                        const v = (this.settingsState.bgmVolume - 0.1 < 0 ? 0 : Math.round((this.settingsState.bgmVolume - 0.1) * 10) / 10);
                        this.settingsState = { ...this.settingsState, bgmVolume: v };
                        manager.setBgmVolume(v);
                    } else if (this.settingsState.selectedField === "sfx") {
                        const v = (this.settingsState.sfxVolume - 0.1 < 0 ? 0 : Math.round((this.settingsState.sfxVolume - 0.1) * 10) / 10);
                        this.settingsState = { ...this.settingsState, sfxVolume: v };
                        manager.setSfxVolume(v);
                    }
                    this.draw();
                } else if (action.type === "confirm") {
                    if (this.settingsState.selectedField === "mute") {
                        const muted = manager.toggleMute();
                        this.settingsState = { ...this.settingsState, muted };
                    }
                    this.draw();
                } else if (action.type === "jack_out") {
                    this.screen = "menu";
                    this.draw();
                }
            });
            return;
        }
    }

    private handleStubInput(action: GameAction): void {
        // Stub screens: ENTER/ESC/Q all return to main menu.
        if (action.type === "confirm" || action.type === "jack_out") {
            this.screen = "menu";
            this.draw();
        }
    }

    private selectMenuOption(option: MenuOption | undefined): void {
        if (!option) return;
        switch (option) {
            case "new_run":
                this.screen = "mission_select";
                this.draw();
                break;
            case "continue":
                void this.handleContinue();
                break;
            case "craft":
                this.screen = "crafting";
                this._message = "";
                this.draw();
                break;
            case "equipment":
                this.screen = "equipment";
                this._message = "";
                this.draw();
                break;
            case "graphic_novel":
                this.screen = "graphic_novel";
                this.initGraphicNovel();
                this.draw();
                break;
            default:
                // Other options (settings, credits, etc.) handled elsewhere.
                this.draw();
                break;
        }
    }

    /** Reload hasSave + meta caches from storage. Call after save/load/clear. */
    private async refreshSaveCache(): Promise<void> {
        this.hasSaveCache = await slotHasSave(0);
        this.saveMetaCache = await getSaveMeta(0);
        // Re-draw menu to reflect availability change (if on menu screen).
        if (this.screen === "menu") this.draw();
    }

    /** Load autosave (slot 0) and resume from saved state.
     *
     * Returns silently if no save exists (gated by hasSaveCache). On success,
     * transitions to the in-game state and resets _lastIceHp/_lastPlayerHp
     * so hit-flash VFX doesn't trigger immediately on resume.
     */
    private async handleContinue(): Promise<void> {
        if (!this.hasSaveCache) {
            // No save — show stub message (should be unreachable from menu but safe).
            this.draw();
            return;
        }
        const slot = await loadFromSlot(0);
        if (!slot) {
            // Stale cache: hasSave said true but load failed. Refresh + stub.
            await this.refreshSaveCache();
            this.draw();
            return;
        }
        const fallbackIce = Object.values(this.iceTypes)[0];
        if (!fallbackIce) {
            this.draw();
            return;
        }
        const restored = slotToGameState(slot, this.missions, this.programs, fallbackIce);
        if (!restored) {
            // Mission no longer in catalog or all programs disappeared.
            this.draw();
            return;
        }
        this.state = restored;
        this.screen = "menu"; // game-internal state; main screen renderer picks up state != null
        this._lastIceHp = restored.ice.hp;
        this._lastPlayerHp = restored.player.hp;
        this.draw();
    }

    private launchSelected(): void {
        const mission = MISSIONS[this.selectedMission];
        if (!mission) return;
        const programs = programsData as unknown as ProgramsFile;
        const deck = loadDeck(programs);
        const ice = loadIce(mission, this.iceTypes);
        const initial = makeInitialState(mission, ice, deck);
        this.state = {
            ...initial,
            grid: makeGrid(this.layout.cols, this.layout.rows),
            currentNodeIndex: 0,
            runPhase: "matrix",
            phase: "approach",
        };
        this.inventory = initial.inventory;
        this.equipmentLoadout = initial.equipmentLoadout;
        this.recipes = makeRecipesFromData({});
        this.materials = makeMaterialsFromData({});
        this.infoMarket = makeInfoMarket({});
        this.draw();
    }

    private autosave(): void {
        if (this.state === null) return;
        // saveToSlot is async (Tier 3 IDB backend). Fire-and-forget: autosave is best-effort.
        saveToSlot(0, stateToSaveSlot(this.state))
            .then(() => {
                // Refresh save metadata so menu reflects current save state.
                void this.refreshSaveCache();
            })
            .catch(() => {
                // Autosave is best-effort; user can manually save later.
            });
    }

    private draw(): void {
        // Tier 5: matrix / loot / ending screens render with a real GameState
        // but their UI is non-combat. Route by runPhase.
        if (this.state !== null && this.state.runPhase === "matrix") {
            updateProgramRow([]);
            const matrix = this.state.matrix;
            if (matrix) {
                this.renderer.render(
                    renderMatrix(
                        matrix,
                        this.state.currentNodeIndex,
                        this.state.visitedNodes,
                        this.layout.cols,
                        this.layout.rows,
                        this.state.iceRoster[this.state.activeIceIndex] ?? null,
                    ),
                    ["MATRIX", "", `Node ${this.state.currentNodeIndex + 1}/${matrix.nodes.length}`],
                );
            }
            return;
        }
        if (this.state !== null && this.state.runPhase === "ending") {
            updateProgramRow([]);
            this.renderer.render(
                renderEndingScreen(this.state.endingChoice, this.layout.cols, this.layout.rows),
                ["ENDING", "", `Choice: ${this.state.endingChoice ?? "?"}`],
            );
            return;
        }
        if (this.state !== null && this.state.runPhase === "loot") {
            updateProgramRow([]);
            this.renderer.render(
                renderLootScreen(
                    this.state.player.hp,
                    this.state.player.maxHp,
                    this.layout.cols,
                    this.layout.rows,
                ),
                ["LOOT", "", "↑↓: navigate | ENTER: continue | ESC: back"],
            );
            return;
        }
        // In-game graphic novel screen (graphicNovel state populated).
        if (this.state !== null && this.screen === "graphic_novel") {
            this.renderGraphicNovel();
            return;
        }
        if (this.state === null) {
            // Pre-game screen routing
            updateProgramRow([]); // hide row outside combat
            if (this.tutorialActive && this.tutorialOverlay) {
                // Tutorial overlay takes priority
                const tutorialGrid = this.tutorialOverlay.render(this.layout.cols, this.layout.rows);
                this.renderer.render(tutorialGrid, ["TUTORIAL", "", ""]);
                this.syncPhase("menu");
                return;
            }
            if (this.screen === "menu") {
                this.renderer.render(
                    renderMainMenu(
                        this.selectedMenuIndex,
                        this.layout.cols,
                        this.layout.rows,
                        this.hasSaveCache,
                        this.saveMetaCache,
                    ),
                    [
                        "MAIN MENU",
                        "",
                        `Selected: ${this.selectedMenuIndex + 1}/${MENU_OPTIONS.length}`,
                    ],
                );
            } else if (this.screen === "mission_select") {
                this.renderer.render(
                    renderMissionSelect(MISSIONS, this.selectedMission, this.layout.cols, this.layout.rows),
                    [
                        "MISSION SELECT",
                        "",
                        `Selected: ${this.selectedMission + 1}/${MISSIONS.length}`,
                    ],
                );
            } else if (this.screen === "settings") {
                void loadSettingsRenderer().then((settingsModule) => {
                    if (this.settingsState === null) {
                        this.settingsState = settingsModule.getInitialSettingsState();
                    }
                    this.renderer.render(
                        settingsModule.renderSettingsScreen(this.settingsState, this.layout.cols, this.layout.rows),
                        [
                            "SETTINGS",
                            "",
                            "Audio controls — volumes persist",
                        ],
                    );
                });
            } else if (this.screen === "crafting") {
                this.renderCraftingScreen();
            } else if (this.screen === "equipment") {
                this.renderEquipmentScreen();
            } else if (this.screen === "graphic_novel") {
                this.renderGraphicNovel();
            } else {
                const opt = MENU_OPTIONS[this.selectedMenuIndex];
                const label = opt ? opt.label.toUpperCase() : "WET RUN";
                this.renderer.render(
                    renderStubScreen(label, this.layout.cols, this.layout.rows),
                    ["STUB", "", "Coming soon — Tier 5+"],
                );
            }
            this.syncPhase("menu");
            return;
        }
        // In-game (combat) rendering path.
        const previous = this.state;
        const iceDelta = this._lastIceHp !== null ? previous.ice.hp - this._lastIceHp : null;
        const playerDelta = this._lastPlayerHp !== null ? previous.player.hp - this._lastPlayerHp : null;
        const mockStatusEffects = mockStatusEffectsForTurn(previous.turnCount);
        this.state = {
            ...this.state,
            grid: renderGrid(
                this.state,
                iceDelta,
                playerDelta,
                mockStatusEffects,
                this.layout.cols,
                this.layout.rows,
            ),
        };
        this.renderer.render(this.state.grid, buildHudLines(this.state));
        // Tier 7: ms-precision advance — exact expiry matching schema duration_ms.
        const now = (typeof performance !== "undefined" ? performance.now() : Date.now());
        const deltaMs = this._lastFrameMs > 0 ? now - this._lastFrameMs : WEB_TICK_MS;
        this._lastFrameMs = now;
        this.state = {
            ...this.state,
            vfxInstances: advanceVfxListBy(this.state.vfxInstances, deltaMs),
        };
        if (this.state.vfxInstances.length > 0) {
            const composed = composeCombatVfx(
                this.state.grid,
                this.state.vfxInstances,
                this.layout.cols,
                this.layout.rows,
            );
            this.renderer.render(composed, buildHudLines(this.state));
        }
        updateProgramRow(this.state.phase === "combat" ? this.state.deck : []);
        this.autosave();
        this.syncPhase(this.state.phase);
    }

    private syncPhase(current: GamePhase): void {
        if (this._lastPhase === current) return;
        const previous = this._lastPhase;
        this._lastPhase = current;
        void loadAudioSystem().then((audio) => {
            const manager = audio.AudioManager.getInstance();
            manager.playPhase(current);
            if (current === "victory" && previous !== "victory") {
                manager.playSfx(audio.SFX_IDS.VICTORY);
            } else if (current === "defeat" && previous !== "defeat") {
                manager.playSfx(audio.SFX_IDS.DEFEAT);
            } else if (current === "exit") {
                manager.stopAllSfx();
            }
        });
    }

    start(): void {
        this.draw();
    }

    /** Read-only phase accessor for e2e/integration tests. */
    getPhase(): GamePhase | null {
        return this.state?.phase ?? null;
    }

    /** Read-only screen accessor for e2e/integration tests. */
    getScreen(): ScreenKind {
        return this.screen;
    }

    /** External entry point for touch gamepad program buttons.
     * Resolves hand index → programId via resolveProgramSelection, then applies.
     */
    handleProgramButton(handIndex: number): void {
        if (this.state === null) return;
        const action: GameAction = { type: "select_program", handIndex };
        const resolved = resolveProgramSelection(this.state, action);
        if (resolved === null) return;
        const previous = this.state;
        this.state = applyAction(this.state, resolved);
        if (previous.phase === "combat" && this.state.phase === "combat") {
            const iceDelta = this.state.ice.hp - previous.ice.hp;
            if (iceDelta < 0) {
                void loadAudioSystem().then((audio) => {
                    audio.AudioManager.getInstance().playSfx(audio.SFX_IDS.COMBAT_HIT);
                });
            }
            this._lastIceHp = this.state.ice.hp;
            this._lastPlayerHp = this.state.player.hp;
        }
        this.draw();
    }

    stop(): void {
        this.input.stop();
        this.gamepad.stop();
        this.unmountTouch();
        this.unwatchLayout();
    }
}

function mockStatusEffectsForTurn(turn: number): readonly string[] {
    const pool = ["burn", "stun", "slow", "silence", "vulnerable"];
    const start = turn % pool.length;
    const count = (turn % 3) + 1;
    return pool.slice(start, start + count);
}

function renderGrid(
    state: GameState,
    iceHpDelta: number | null = null,
    playerHpDelta: number | null = null,
    statusEffects: readonly string[] = [],
    cols = 80,
    rows = 50,
) {
    let grid = makeGrid(cols, rows);
    // Layout-relative anchors: ICE block centered horizontally; HUD bars near top-left.
    const iceCol = Math.max(20, Math.floor(cols * 0.45));
    const iceNameCol = iceCol + 1;
    const iceStatusCol = iceCol + Math.min(20, cols - iceCol - 6);
    const turnCol = Math.max(iceNameCol, cols - Math.floor(cols * 0.25));
    const statusArtCol = Math.max(20, Math.floor(cols * 0.45));
    const handRow = Math.max(8, rows - Math.floor(rows * 0.16));
    const artWidth = Math.min(32, cols - statusArtCol - 2);

    grid = setText(grid, 2, 1, `Mission: ${state.mission.title}`, PALETTE.GREEN_NEON);
    grid = setText(grid, 2, 3, state.message, PALETTE.GRAY_LIGHT);

    grid = setText(grid, turnCol, 1, `T${state.turnCount + 1}`, PALETTE.GRAY_LIGHT);

    grid = setText(
        grid,
        2,
        5,
        `P ${healthBar(state.player.hp, state.player.maxHp)} ${state.player.hp}/${state.player.maxHp}`,
        playerHpDelta !== null ? hitFlashColor(playerHpDelta) : healthColor(state.player.hp, state.player.maxHp),
    );

    if (state.phase === "combat" || state.phase === "victory" || state.phase === "defeat") {
        const rosterStartRow = Math.floor(rows * 0.44);
        for (let i = 0; i < state.iceRoster.length; i++) {
            const ice = state.iceRoster[i];
            const row = rosterStartRow + i * 3;
            if (row + 2 >= rows) break;
            const isTarget = i === state.activeIceIndex;
            const marker = isTarget ? ">" : " ";
            const alive = ice.hp > 0;
            const iceHp = Math.max(0, ice.hp);
            
            // Name line: "> [1] ICE_NAME" or "  [1] ICE_NAME"
            const nameText = `${marker} [${i + 1}] ${ice.name.slice(0, 10)}`;
            grid = setText(grid, iceCol - 2, row, nameText, alive ? iceColor(ice.tier) : PALETTE.GRAY_MID);
            
            // Status effects only for target
            if (isTarget) {
                const statusSuffix = formatStatusGlyph(statusEffects);
                if (statusSuffix !== "") {
                    grid = setText(grid, iceStatusCol, row, statusSuffix, PALETTE.YELLOW_AMBER);
                }
            }
            
            // HP bar line
            if (alive) {
                const delta = (isTarget && iceHpDelta !== null) ? iceHpDelta : null;
                grid = setText(
                    grid,
                    iceCol,
                    row + 2,
                    `${healthBar(iceHp, 100)} ${iceHp}/100`,
                    delta !== null ? hitFlashColor(delta) : healthColor(iceHp, 100),
                );
            } else {
                grid = setText(grid, iceCol, row + 2, "[DEAD]", PALETTE.GRAY_MID);
            }
        }
    }

    const statusLabel = formatStatusLabel(state.phase);
    if (statusLabel !== "") {
        const statusColor = state.phase === "victory" ? PALETTE.GREEN_NEON : PALETTE.RED_BRIGHT;
        const statusRow = Math.floor(rows * 0.52);
        grid = setText(grid, statusArtCol, statusRow, statusLabel, statusColor);
        if (state.phase === "victory") {
            const art = centerArt(ICE_DEFEAT_ART, artWidth);
            let y = statusRow + 2;
            for (const line of art) {
                if (y >= rows) break;
                grid = setText(grid, statusArtCol, y, line, PALETTE.GRAY_MID);
                y += 1;
            }
        } else if (state.phase === "defeat") {
            const art = centerArt(PLAYER_DEFEAT_ART, artWidth);
            let y = statusRow + 2;
            for (const line of art) {
                if (y >= rows) break;
                grid = setText(grid, statusArtCol, y, line, PALETTE.GRAY_MID);
                y += 1;
            }
        }
    }

    if (state.phase === "combat" && state.deck.length > 0) {
        grid = setText(grid, 2, handRow, "HAND:", PALETTE.YELLOW_AMBER);
        let x = 9;
        for (const p of state.deck) {
            if (x >= cols - 6) break;
            const label = `[${p.id.slice(0, 4)}]`;
            grid = setText(grid, x, handRow, label, PALETTE.CYAN_LIGHT);
            x += label.length + 1;
        }
    }
    return grid;
}

function boot(): void {
    const loading = document.getElementById("loading");
    const canvas = document.getElementById("game-canvas");
    const gamepadStatus = document.getElementById("gamepad-status");
    if (!canvas || !(canvas instanceof HTMLCanvasElement)) {
        console.error("Canvas element not found");
        return;
    }

    let game: Game;
    try {
        const iceTypes = iceTypesData as unknown as Record<string, Ice>;
        game = new Game(canvas, iceTypes);
    } catch (err) {
        console.error("Failed to boot Wet Run:", err);
        if (loading) loading.textContent = `Error: ${(err as Error).message}`;
        return;
    }

    if (loading) loading.style.display = "none";
    game.start();
    (window as unknown as { wetrun: Game }).wetrun = game;

    void loadAudioSystem().then((audio) => {
        const manager = audio.AudioManager.getInstance();
        audio.AudioManager.unlockOnFirstGesture(() => {
            manager.play();
        });
        document.addEventListener("keydown", (ev: KeyboardEvent) => {
            if (ev.key === "m" || ev.key === "M") {
                const muted = manager.toggleMute();
                console.info(`[audio] BGM ${muted ? "muted" : "unmuted"} (M to toggle)`);
            }
        });
    });

    // Gamepad connection monitoring
    const updateGamepadStatus = (): void => {
        if (!gamepadStatus) return;
        if (isGamepadConnected()) {
            gamepadStatus.textContent = "🎮 Gamepad Connected";
            gamepadStatus.classList.add("connected");
        } else {
            gamepadStatus.textContent = "";
            gamepadStatus.classList.remove("connected");
        }
    };

    if (typeof window !== "undefined") {
        window.addEventListener("gamepadconnected", updateGamepadStatus);
        window.addEventListener("gamepaddisconnected", updateGamepadStatus);
        updateGamepadStatus();
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
} else {
    boot();
}
