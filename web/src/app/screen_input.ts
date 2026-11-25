/** Screen-owned input handlers that are not the pre-game ladder.
 *
 * Refactoring Stage 3a-1b (2026-11-25). These six handlers each own one
 * screen's keys and nothing else — they were `Game` methods only because the
 * class grew that way. `main.ts` is outside the balance harness's import
 * graph, so e2e is the guard (desktop + mobile).
 *
 * Behaviour is preserved exactly, including the two draws the dispatcher and
 * the dungeon handler each perform on their own.
 *
 * Naming note: `handleSettingsStubInput` is the *run-time* settings screen
 * (the run state is live behind it, so it only backs out). The pre-game
 * settings screen — the one with every toggle — is `app/settings_input.ts`.
 */
import type { GameAction, EquipmentLoadout, Inventory, ScreenKind } from "../core/types";
import type { DungeonCrawler } from "../core/dungeon/dungeon_crawler";
import { craftItem, type Recipe } from "../core/state/crafting";
import { DEFAULT_REGISTRY, EQUIP_SLOTS, equipOn } from "../core/state/equipment";
import { isOwned, ownEquipment, writeOwnedIds, type OwnedSet } from "../core/state/owned_equipment";
import { writeEquippedIds } from "../core/state/equipment_store";
import { writeWalletMaterials } from "../core/state/wallet";

/** What the screen handlers need from the game controller. */
export interface ScreenInputHost {
  screen: ScreenKind;
  _message: string;
  inventory: Inventory;
  equipmentLoadout: EquipmentLoadout;
  ownedEquipment: OwnedSet;
  recipes: ReadonlyArray<Recipe>;
  dungeonCrawler: DungeonCrawler | null;
  draw(): void;
}

/** The crafting screen: ESC backs out, a digit crafts the nth affordable recipe. */
export function handleCraftingInput(host: ScreenInputHost, action: GameAction): void {
  if (action.type === "jack_out" || action.type === "cancel") {
    host.screen = "menu";
    host._message = "";
    host.draw();
    return;
  }
  if (action.type === "select_program") {
    const index = action.handIndex - 1;
    if (index < 0) return;
    // Build list of craftable recipes (those with sufficient materials).
    const craftable: Recipe[] = [];
    for (const recipe of host.recipes) {
      let canCraft = true;
      for (const [mat, qty] of Object.entries(recipe.materials)) {
        if (host.inventory.materials[mat] ?? 0 < qty) {
          canCraft = false;
          break;
        }
      }
      if (canCraft) craftable.push(recipe);
    }
    if (index >= craftable.length) {
      host._message = "No craftable recipe at that slot.";
      host.draw();
      return;
    }
    const recipe = craftable[index];
    if (!recipe) {
      host.draw();
      return;
    }
    // ADR-0325: one transaction — spend the materials AND take ownership of
    // the piece. The recipe's itemId is a catalog equipment id.
    const result = craftItem(host.recipes, recipe.itemId, host.inventory.materials);
    if (result.ok) {
      host.inventory = { ...host.inventory, materials: result.newInventory };
      writeWalletMaterials(host.inventory.materials);
      host.ownedEquipment = ownEquipment(host.ownedEquipment, recipe.itemId);
      writeOwnedIds(host.ownedEquipment);
      host._message = `Crafted ${recipe.name} — it's yours now.`;
    } else {
      host._message = `Failed to craft ${recipe.name}: ${result.reason}`;
    }
    host.draw();
    return;
  }
}

/** The equipment screen: ESC backs out, a digit fills the nth empty slot. */
export function handleEquipmentInput(host: ScreenInputHost, action: GameAction): void {
  if (action.type === "jack_out" || action.type === "cancel") {
    host.screen = "menu";
    host._message = "";
    host.draw();
    return;
  }
  if (action.type === "select_program") {
    const slotIndex = action.handIndex - 1;
    if (slotIndex < 0 || slotIndex >= EQUIP_SLOTS.length) return;
    const slot = EQUIP_SLOTS[slotIndex];
    if (!slot) {
      host.draw();
      return;
    }
    // ADR-0325: equip only what the runner owns — tier-0 starters plus
    // anything crafted. Crafting is what makes the menu grow.
    const candidate = DEFAULT_REGISTRY.all.find(
      (e) =>
        e.slot === slot &&
        isOwned(host.ownedEquipment, e.id) &&
        host.equipmentLoadout.get(slot) === null,
    );
    if (!candidate) {
      host._message = `No owned equipment for slot ${slot}`;
      host.draw();
      return;
    }
    const result = equipOn(host.equipmentLoadout, candidate);
    host.equipmentLoadout = result.loadout;
    writeEquippedIds(host.equipmentLoadout);
    host._message = `Equipped ${candidate.name} to ${slot}`;
    host.draw();
    return;
  }
}

/** The dungeon crawl screen: movement drives a turn; ESC abandons the crawl. */
export function handleDungeonInput(host: ScreenInputHost, action: GameAction): void {
  if (!host.dungeonCrawler) return;

  switch (action.type) {
    case "move_north":
    case "move_south":
    case "move_east":
    case "move_west": {
      const dx = action.type === "move_east" ? 1 : action.type === "move_west" ? -1 : 0;
      const dy = action.type === "move_south" ? 1 : action.type === "move_north" ? -1 : 0;
      host.dungeonCrawler.tryMovePlayer(dx, dy);
      // Drive monster AI + FOV update each player turn.
      host.dungeonCrawler.processTurn();
      if (host.dungeonCrawler.isGameOver()) {
        host._message = "FLATLINE — dungeon crawl failed";
        host.screen = "menu";
        host.dungeonCrawler = null;
      }
      break;
    }
    case "confirm":
      host.dungeonCrawler.confirm();
      break;
    case "cancel":
      host.dungeonCrawler.cancel();
      break;
    case "jack_out":
      host.screen = "menu";
      host.dungeonCrawler = null;
      host.draw();
      return;
    default:
      break;
  }
  host.draw();
}

/** The run-time settings screen (see the naming note above). */
export function handleSettingsStubInput(host: ScreenInputHost, action: GameAction): void {
  if (action.type === "cancel" || action.type === "jack_out") {
    host.screen = "menu";
    host.draw();
    return;
  }
  if (action.type === "confirm") {
    // Toggle settings
    host.draw();
  }
}

/** The pause screen: ESC leaves the run's menus, ENTER opens settings. */
export function handlePauseInput(host: ScreenInputHost, action: GameAction): void {
  if (action.type === "cancel" || action.type === "jack_out") {
    host.screen = "menu";
    host.draw();
    return;
  }
  if (action.type === "confirm") {
    host.screen = "settings";
    host.draw();
  }
}

/** Stub screens: ENTER/ESC/Q all return to main menu. */
export function handleStubInput(host: ScreenInputHost, action: GameAction): void {
  if (action.type === "confirm" || action.type === "jack_out") {
    host.screen = "menu";
    host.draw();
  }
}
