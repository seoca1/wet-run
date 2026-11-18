import { describe, it, expect } from "vitest";
import {
  DEFAULT_HUB_STATE,
  HUB_NPCS,
  HUB_SHOPS,
  HUB_SERVICES,
  enterHub,
  moveToLocation,
  getNpcsAtLocation,
  getShopsAtLocation,
  getServicesAtLocation,
  useService,
  leaveHub,
  getHubSummary,
  type HubLocation,
} from "../src/core/hub.ts";

describe("Hub System", () => {
  describe("DEFAULT_HUB_STATE", () => {
    it("is frozen", () => {
      expect(Object.isFrozen(DEFAULT_HUB_STATE)).toBe(true);
    });

    it("has correct defaults", () => {
      expect(DEFAULT_HUB_STATE.active).toBe(false);
      expect(DEFAULT_HUB_STATE.currentLocation).toBe("command");
      expect(DEFAULT_HUB_STATE.visitedLocations).toEqual([]);
    });

    it("has frozen arrays", () => {
      expect(Object.isFrozen(DEFAULT_HUB_STATE.visitedLocations)).toBe(true);
    });
  });

  describe("HUB_NPCS", () => {
    it("is frozen", () => {
      expect(Object.isFrozen(HUB_NPCS)).toBe(true);
    });

    it("contains exactly 5 NPCs", () => {
      expect(HUB_NPCS.length).toBe(5);
    });

    it("all NPCs are frozen", () => {
      for (const npc of HUB_NPCS) {
        expect(Object.isFrozen(npc)).toBe(true);
      }
    });

    it("has unique NPC IDs", () => {
      const ids = HUB_NPCS.map(n => n.id);
      expect(new Set(ids).size).toBe(ids.length);
    });

    it("finn has correct properties", () => {
      const finn = HUB_NPCS.find(n => n.id === "finn");
      expect(finn).toBeDefined();
      expect(finn?.name).toBe("Finn the Fixer");
      expect(finn?.location).toBe("bar");
      expect(finn?.role).toBe("fixer");
      expect(finn?.dialogueId).toBe("finn_intro");
    });

    it("molly has correct properties", () => {
      const molly = HUB_NPCS.find(n => n.id === "molly");
      expect(molly).toBeDefined();
      expect(molly?.name).toBe("Molly Millions");
      expect(molly?.location).toBe("workshop");
      expect(molly?.role).toBe("instructor");
      expect(molly?.dialogueId).toBe("molly_intro");
    });

    it("doc has correct properties", () => {
      const doc = HUB_NPCS.find(n => n.id === "doc");
      expect(doc).toBeDefined();
      expect(doc?.name).toBe("Dr. Delete");
      expect(doc?.location).toBe("medbay");
      expect(doc?.role).toBe("medic");
    });

    it("all NPCs have valid locations", () => {
      const validLocations: HubLocation[] = ["bar", "shop", "workshop", "medbay", "command", "dormitory"];
      for (const npc of HUB_NPCS) {
        expect(validLocations).toContain(npc.location);
      }
    });

    it("all NPCs have valid roles", () => {
      const validRoles = ["fixer", "merchant", "medic", "instructor", "informant"];
      for (const npc of HUB_NPCS) {
        expect(validRoles).toContain(npc.role);
      }
    });
  });

  describe("HUB_SHOPS", () => {
    it("is frozen", () => {
      expect(Object.isFrozen(HUB_SHOPS)).toBe(true);
    });

    it("contains exactly 3 shops", () => {
      expect(HUB_SHOPS.length).toBe(3);
    });

    it("all shops are frozen", () => {
      for (const shop of HUB_SHOPS) {
        expect(Object.isFrozen(shop)).toBe(true);
        expect(Object.isFrozen(shop.inventory)).toBe(true);
      }
    });

    it("has unique shop IDs", () => {
      const ids = HUB_SHOPS.map(s => s.id);
      expect(new Set(ids).size).toBe(ids.length);
    });

    it("main_shop has correct markup", () => {
      const shop = HUB_SHOPS.find(s => s.id === "main_shop");
      expect(shop?.markup).toBe(1.0);
    });

    it("black_market has markup above 1.0", () => {
      const shop = HUB_SHOPS.find(s => s.id === "black_market");
      expect(shop?.markup).toBeGreaterThan(1.0);
    });

    it("medbay_supplies has markup below 1.0", () => {
      const shop = HUB_SHOPS.find(s => s.id === "medbay_supplies");
      expect(shop?.markup).toBeLessThan(1.0);
    });

    it("all shops have non-empty inventory", () => {
      for (const shop of HUB_SHOPS) {
        expect(shop.inventory.length).toBeGreaterThan(0);
      }
    });

    it("all shops have valid locations", () => {
      const validLocations: HubLocation[] = ["bar", "shop", "workshop", "medbay", "command", "dormitory"];
      for (const shop of HUB_SHOPS) {
        expect(validLocations).toContain(shop.location);
      }
    });
  });

  describe("HUB_SERVICES", () => {
    it("is frozen", () => {
      expect(Object.isFrozen(HUB_SERVICES)).toBe(true);
    });

    it("contains exactly 4 services", () => {
      expect(HUB_SERVICES.length).toBe(4);
    });

    it("all services are frozen", () => {
      for (const service of HUB_SERVICES) {
        expect(Object.isFrozen(service)).toBe(true);
      }
    });

    it("has unique service IDs", () => {
      const ids = HUB_SERVICES.map(s => s.id);
      expect(new Set(ids).size).toBe(ids.length);
    });

    it("all services have positive costs", () => {
      for (const service of HUB_SERVICES) {
        expect(service.cost).toBeGreaterThan(0);
      }
    });

    it("all services have positive values", () => {
      for (const service of HUB_SERVICES) {
        expect(service.value).toBeGreaterThan(0);
      }
    });

    it("heal service has correct properties", () => {
      const heal = HUB_SERVICES.find(s => s.id === "heal");
      expect(heal).toBeDefined();
      expect(heal?.name).toBe("Medical Treatment");
      expect(heal?.location).toBe("medbay");
      expect(heal?.cost).toBe(500);
      expect(heal?.effect).toBe("heal");
      expect(heal?.value).toBe(50);
    });

    it("full_heal costs more than heal", () => {
      const heal = HUB_SERVICES.find(s => s.id === "heal");
      const fullHeal = HUB_SERVICES.find(s => s.id === "full_heal");
      expect(fullHeal?.cost).toBeGreaterThan(heal?.cost ?? 0);
    });

    it("all services have valid effects", () => {
      const validEffects = ["heal", "repair", "upgrade", "rest"];
      for (const service of HUB_SERVICES) {
        expect(validEffects).toContain(service.effect);
      }
    });

    it("all services have valid locations", () => {
      const validLocations: HubLocation[] = ["bar", "shop", "workshop", "medbay", "command", "dormitory"];
      for (const service of HUB_SERVICES) {
        expect(validLocations).toContain(service.location);
      }
    });
  });

  describe("enterHub", () => {
    it("returns active state", () => {
      const state = enterHub();
      expect(state.active).toBe(true);
    });

    it("starts at command location", () => {
      const state = enterHub();
      expect(state.currentLocation).toBe("command");
    });

    it("marks command as visited", () => {
      const state = enterHub();
      expect(state.visitedLocations).toContain("command");
      expect(state.visitedLocations.length).toBe(1);
    });

    it("returns frozen state", () => {
      const state = enterHub();
      expect(Object.isFrozen(state)).toBe(true);
      expect(Object.isFrozen(state.visitedLocations)).toBe(true);
    });

    it("creates new state each call", () => {
      const state1 = enterHub();
      const state2 = enterHub();
      expect(state1).not.toBe(state2);
    });
  });

  describe("moveToLocation", () => {
    it("updates current location", () => {
      const state = enterHub();
      const next = moveToLocation(state, "bar");
      expect(next.currentLocation).toBe("bar");
    });

    it("adds location to visited list", () => {
      const state = enterHub();
      const next = moveToLocation(state, "bar");
      expect(next.visitedLocations).toContain("bar");
      expect(next.visitedLocations.length).toBe(2);
    });

    it("does not duplicate visited locations", () => {
      const state = enterHub();
      const next1 = moveToLocation(state, "bar");
      const next2 = moveToLocation(next1, "bar");
      expect(next2.visitedLocations.filter(l => l === "bar").length).toBe(1);
    });

    it("returns same state when hub is inactive", () => {
      const state = DEFAULT_HUB_STATE;
      const next = moveToLocation(state, "bar");
      expect(next).toBe(state);
    });

    it("returns frozen state", () => {
      const state = enterHub();
      const next = moveToLocation(state, "bar");
      expect(Object.isFrozen(next)).toBe(true);
      expect(Object.isFrozen(next.visitedLocations)).toBe(true);
    });

    it("preserves active status", () => {
      const state = enterHub();
      const next = moveToLocation(state, "workshop");
      expect(next.active).toBe(true);
    });

    it("can visit all locations", () => {
      const locations: HubLocation[] = ["bar", "shop", "workshop", "medbay", "dormitory"];
      let state = enterHub();
      for (const loc of locations) {
        state = moveToLocation(state, loc);
        expect(state.currentLocation).toBe(loc);
      }
      expect(state.visitedLocations.length).toBe(6);
    });
  });

  describe("getNpcsAtLocation", () => {
    it("returns NPCs at bar", () => {
      const npcs = getNpcsAtLocation("bar");
      expect(npcs.length).toBeGreaterThan(0);
      for (const npc of npcs) {
        expect(npc.location).toBe("bar");
      }
    });

    it("returns NPCs at workshop", () => {
      const npcs = getNpcsAtLocation("workshop");
      expect(npcs.length).toBeGreaterThan(0);
      for (const npc of npcs) {
        expect(npc.location).toBe("workshop");
      }
    });

    it("returns NPCs at medbay", () => {
      const npcs = getNpcsAtLocation("medbay");
      expect(npcs.length).toBeGreaterThan(0);
      for (const npc of npcs) {
        expect(npc.location).toBe("medbay");
      }
    });

    it("returns NPCs at command", () => {
      const npcs = getNpcsAtLocation("command");
      expect(npcs.length).toBeGreaterThan(0);
      for (const npc of npcs) {
        expect(npc.location).toBe("command");
      }
    });

    it("returns empty array when no NPCs at location", () => {
      const npcs = getNpcsAtLocation("dormitory");
      expect(npcs).toEqual([]);
    });

    it("returns frozen array", () => {
      const npcs = getNpcsAtLocation("bar");
      expect(Object.isFrozen(npcs)).toBe(true);
    });

    it("returns different arrays per location", () => {
      const bar = getNpcsAtLocation("bar");
      const workshop = getNpcsAtLocation("workshop");
      expect(bar).not.toEqual(workshop);
    });
  });

  describe("getShopsAtLocation", () => {
    it("returns shops at shop location", () => {
      const shops = getShopsAtLocation("shop");
      expect(shops.length).toBeGreaterThan(0);
      for (const shop of shops) {
        expect(shop.location).toBe("shop");
      }
    });

    it("returns shops at bar", () => {
      const shops = getShopsAtLocation("bar");
      expect(shops.length).toBeGreaterThan(0);
      for (const shop of shops) {
        expect(shop.location).toBe("bar");
      }
    });

    it("returns shops at medbay", () => {
      const shops = getShopsAtLocation("medbay");
      expect(shops.length).toBeGreaterThan(0);
      for (const shop of shops) {
        expect(shop.location).toBe("medbay");
      }
    });

    it("returns empty array when no shops at location", () => {
      const shops = getShopsAtLocation("command");
      expect(shops).toEqual([]);
    });

    it("returns frozen array", () => {
      const shops = getShopsAtLocation("shop");
      expect(Object.isFrozen(shops)).toBe(true);
    });
  });

  describe("getServicesAtLocation", () => {
    it("returns services at medbay", () => {
      const services = getServicesAtLocation("medbay");
      expect(services.length).toBe(2);
      for (const service of services) {
        expect(service.location).toBe("medbay");
      }
    });

    it("returns services at workshop", () => {
      const services = getServicesAtLocation("workshop");
      expect(services.length).toBeGreaterThan(0);
      for (const service of services) {
        expect(service.location).toBe("workshop");
      }
    });

    it("returns services at dormitory", () => {
      const services = getServicesAtLocation("dormitory");
      expect(services.length).toBeGreaterThan(0);
      for (const service of services) {
        expect(service.location).toBe("dormitory");
      }
    });

    it("returns empty array when no services at location", () => {
      const services = getServicesAtLocation("bar");
      expect(services).toEqual([]);
    });

    it("returns frozen array", () => {
      const services = getServicesAtLocation("medbay");
      expect(Object.isFrozen(services)).toBe(true);
    });
  });

  describe("useService", () => {
    it("returns null for invalid service ID", () => {
      const result = useService("invalid_service", 1000);
      expect(result).toBe(null);
    });

    it("returns null when insufficient credits", () => {
      const result = useService("heal", 100);
      expect(result).toBe(null);
    });

    it("returns success when enough credits for heal", () => {
      const result = useService("heal", 500);
      expect(result).not.toBe(null);
      expect(result?.success).toBe(true);
      expect(result?.cost).toBe(500);
      expect(result?.effect).toBe("heal");
      expect(result?.value).toBe(50);
    });

    it("returns success when enough credits for full_heal", () => {
      const result = useService("full_heal", 1500);
      expect(result).not.toBe(null);
      expect(result?.success).toBe(true);
      expect(result?.cost).toBe(1500);
      expect(result?.effect).toBe("heal");
      expect(result?.value).toBe(100);
    });

    it("returns success when enough credits for upgrade_deck", () => {
      const result = useService("upgrade_deck", 3000);
      expect(result).not.toBe(null);
      expect(result?.success).toBe(true);
      expect(result?.cost).toBe(3000);
      expect(result?.effect).toBe("upgrade");
      expect(result?.value).toBe(1);
    });

    it("returns success when enough credits for rest", () => {
      const result = useService("rest", 200);
      expect(result).not.toBe(null);
      expect(result?.success).toBe(true);
      expect(result?.cost).toBe(200);
      expect(result?.effect).toBe("rest");
      expect(result?.value).toBe(25);
    });

    it("returns frozen result", () => {
      const result = useService("heal", 500);
      expect(result).not.toBe(null);
      expect(Object.isFrozen(result)).toBe(true);
    });

    it("works with exact credit amount", () => {
      const result = useService("heal", 500);
      expect(result?.success).toBe(true);
    });

    it("works with more than required credits", () => {
      const result = useService("heal", 1000);
      expect(result?.success).toBe(true);
    });

    it("fails with one credit less", () => {
      const result = useService("heal", 499);
      expect(result).toBe(null);
    });
  });

  describe("leaveHub", () => {
    it("returns inactive state", () => {
      const state = enterHub();
      const next = leaveHub(state);
      expect(next.active).toBe(false);
    });

    it("resets to command location", () => {
      const state = enterHub();
      const moved = moveToLocation(state, "bar");
      const next = leaveHub(moved);
      expect(next.currentLocation).toBe("command");
    });

    it("preserves visited locations", () => {
      const state = enterHub();
      const moved = moveToLocation(state, "bar");
      const next = leaveHub(moved);
      expect(next.visitedLocations).toEqual(moved.visitedLocations);
    });

    it("returns frozen state", () => {
      const state = enterHub();
      const next = leaveHub(state);
      expect(Object.isFrozen(next)).toBe(true);
      expect(Object.isFrozen(next.visitedLocations)).toBe(true);
    });

    it("can leave and re-enter", () => {
      const state1 = enterHub();
      leaveHub(state1);
      const state2 = enterHub();
      expect(state2.active).toBe(true);
      expect(state2.currentLocation).toBe("command");
    });
  });

  describe("getHubSummary", () => {
    it("returns correct summary for command", () => {
      const state = enterHub();
      const summary = getHubSummary(state);
      expect(summary.location).toBe("command");
      expect(summary.npcs).toBe(getNpcsAtLocation("command").length);
      expect(summary.shops).toBe(getShopsAtLocation("command").length);
      expect(summary.services).toBe(getServicesAtLocation("command").length);
    });

    it("returns correct summary for bar", () => {
      const state = moveToLocation(enterHub(), "bar");
      const summary = getHubSummary(state);
      expect(summary.location).toBe("bar");
      expect(summary.npcs).toBe(getNpcsAtLocation("bar").length);
      expect(summary.shops).toBe(getShopsAtLocation("bar").length);
      expect(summary.services).toBe(getServicesAtLocation("bar").length);
    });

    it("returns correct summary for medbay", () => {
      const state = moveToLocation(enterHub(), "medbay");
      const summary = getHubSummary(state);
      expect(summary.location).toBe("medbay");
      expect(summary.npcs).toBe(getNpcsAtLocation("medbay").length);
      expect(summary.shops).toBe(getShopsAtLocation("medbay").length);
      expect(summary.services).toBe(getServicesAtLocation("medbay").length);
    });

    it("returns frozen summary", () => {
      const state = enterHub();
      const summary = getHubSummary(state);
      expect(Object.isFrozen(summary)).toBe(true);
    });

    it("summary changes when location changes", () => {
      const state = enterHub();
      const summary1 = getHubSummary(state);
      const moved = moveToLocation(state, "bar");
      const summary2 = getHubSummary(moved);
      expect(summary1.location).not.toBe(summary2.location);
    });
  });
});
