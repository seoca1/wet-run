/** Hub/Base System — safe zone with NPCs, shops, and services.
 *
 * The Hub is the player's home base between missions. Players can
 * rest, talk to NPCs, buy equipment, and prepare for the next run.
 */

export type HubLocation = "bar" | "shop" | "workshop" | "medbay" | "command" | "dormitory";

export interface HubNpc {
  readonly id: string;
  readonly name: string;
  readonly location: HubLocation;
  readonly role: "fixer" | "merchant" | "medic" | "instructor" | "informant";
  readonly dialogueId?: string;
}

export interface HubShop {
  readonly id: string;
  readonly name: string;
  readonly location: HubLocation;
  readonly inventory: ReadonlyArray<string>;
  readonly markup: number;
}

export interface HubService {
  readonly id: string;
  readonly name: string;
  readonly location: HubLocation;
  readonly cost: number;
  readonly effect: "heal" | "repair" | "upgrade" | "rest";
  readonly value: number;
}

export interface HubState {
  readonly active: boolean;
  readonly currentLocation: HubLocation;
  readonly visitedLocations: ReadonlyArray<HubLocation>;
}

export const DEFAULT_HUB_STATE: HubState = Object.freeze({
  active: false,
  currentLocation: "command",
  visitedLocations: Object.freeze([]),
});

export const HUB_NPCS: ReadonlyArray<HubNpc> = Object.freeze([
  Object.freeze({ id: "finn", name: "Finn the Fixer", location: "bar", role: "fixer", dialogueId: "finn_intro" }),
  Object.freeze({ id: "molly", name: "Molly Millions", location: "workshop", role: "instructor", dialogueId: "molly_intro" }),
  Object.freeze({ id: "doc", name: "Dr. Delete", location: "medbay", role: "medic" }),
  Object.freeze({ id: "vendor", name: "The Vendor", location: "shop", role: "merchant" }),
  Object.freeze({ id: "intel", name: "Intel Broker", location: "command", role: "informant" }),
]);

export const HUB_SHOPS: ReadonlyArray<HubShop> = Object.freeze([
  Object.freeze({ id: "main_shop", name: "Equipment Depot", location: "shop", inventory: Object.freeze(["basic_deck", "combat_program_v1", "ice_picker"]), markup: 1.0 }),
  Object.freeze({ id: "black_market", name: "Black Market", location: "bar", inventory: Object.freeze(["enhanced_deck", "viral_program", "stealth_chip"]), markup: 1.5 }),
  Object.freeze({ id: "medbay_supplies", name: "Medical Supplies", location: "medbay", inventory: Object.freeze(["medkit", "stimpack", "nanobots"]), markup: 0.8 }),
]);

export const HUB_SERVICES: ReadonlyArray<HubService> = Object.freeze([
  Object.freeze({ id: "heal", name: "Medical Treatment", location: "medbay", cost: 500, effect: "heal", value: 50 }),
  Object.freeze({ id: "full_heal", name: "Full Recovery", location: "medbay", cost: 1500, effect: "heal", value: 100 }),
  Object.freeze({ id: "upgrade_deck", name: "Deck Upgrade", location: "workshop", cost: 3000, effect: "upgrade", value: 1 }),
  Object.freeze({ id: "rest", name: "Rest", location: "dormitory", cost: 200, effect: "rest", value: 25 }),
]);

export function enterHub(): HubState {
  return Object.freeze({
    active: true,
    currentLocation: "command" as HubLocation,
    visitedLocations: Object.freeze(["command" as HubLocation]),
  });
}

export function moveToLocation(state: HubState, location: HubLocation): HubState {
  if (!state.active) return state;
  const visited: ReadonlyArray<HubLocation> = state.visitedLocations.includes(location)
    ? state.visitedLocations
    : Object.freeze([...state.visitedLocations, location]);
  return Object.freeze({
    active: true,
    currentLocation: location,
    visitedLocations: visited,
  });
}

export function getNpcsAtLocation(location: HubLocation): ReadonlyArray<HubNpc> {
  return Object.freeze(HUB_NPCS.filter(n => n.location === location));
}

export function getShopsAtLocation(location: HubLocation): ReadonlyArray<HubShop> {
  return Object.freeze(HUB_SHOPS.filter(s => s.location === location));
}

export function getServicesAtLocation(location: HubLocation): ReadonlyArray<HubService> {
  return Object.freeze(HUB_SERVICES.filter(s => s.location === location));
}

export function useService(
  serviceId: string,
  currentCredits: number,
): { readonly success: boolean; readonly cost: number; readonly effect: string; readonly value: number } | null {
  const service = HUB_SERVICES.find(s => s.id === serviceId);
  if (!service) return null;
  if (currentCredits < service.cost) return null;
  return Object.freeze({
    success: true,
    cost: service.cost,
    effect: service.effect,
    value: service.value,
  });
}

export function leaveHub(state: HubState): HubState {
  return Object.freeze({
    active: false,
    currentLocation: "command" as HubLocation,
    visitedLocations: state.visitedLocations,
  });
}

export function getHubSummary(state: HubState): {
  readonly location: HubLocation;
  readonly npcs: number;
  readonly shops: number;
  readonly services: number;
} {
  return Object.freeze({
    location: state.currentLocation,
    npcs: getNpcsAtLocation(state.currentLocation).length,
    shops: getShopsAtLocation(state.currentLocation).length,
    services: getServicesAtLocation(state.currentLocation).length,
  });
}
