/** Default equipment catalog (Gibson-inspired cyberpunk).
 *
 * Pure data — 18 Equipment records across 7 tiers (T0..T6).
 * Mirrors Python STARTER_DECK, STREET_DECK, ..., MASTER_DECK from
 * `prototype/src/wet_run/equipment/equipment.py`.
 *
 * Split from `equipment.ts` so the core types + registry + loadout
 * logic stays under the 250 LOC ceiling. SIZE_OK (data table).
 *
 * Note: stats are constructed inline (via the local `s()` helper)
 * rather than importing `makeEquipStats` from equipment.ts — that
 * would create an import cycle since equipment.ts re-exports from
 * this file. The inline construction is pure data and the helper
 * produces the same frozen shape as `makeEquipStats`.
 */
import type { EquipStats, Equipment } from "./equipment.ts";

// =============================================================================
// Default Equipment Catalog
// =============================================================================
//
// All values copied verbatim from equipment.py so combat stats match exactly.

function s(p: {
  attackBonus?: number;
  critBonusPct?: number;
  damageBonusPct?: number;
  defense?: number;
  hpBonus?: number;
  shieldBonus?: number;
  apBonus?: number;
  apRegenBonusPct?: number;
  programPower?: number;
  iceResistance?: number;
  grantsSkillId?: string | null;
  extraEffect?: string;
}): EquipStats {
  return Object.freeze({
    attackBonus: p.attackBonus ?? 0,
    critBonusPct: p.critBonusPct ?? 0,
    damageBonusPct: p.damageBonusPct ?? 0,
    defense: p.defense ?? 0,
    hpBonus: p.hpBonus ?? 0,
    shieldBonus: p.shieldBonus ?? 0,
    apBonus: p.apBonus ?? 0,
    apRegenBonusPct: p.apRegenBonusPct ?? 0,
    programPower: p.programPower ?? 0,
    iceResistance: p.iceResistance ?? 0,
    grantsSkillId: p.grantsSkillId ?? null,
    extraEffect: p.extraEffect ?? "",
  });
}

export const STARTER_DECK: Equipment = Object.freeze({
  id: "deck_basic",
  name: "Ono-Sendai Cyberspace 7",
  slot: "deck",
  category: "hardware",
  tier: "T0",
  stats: s({ programPower: 5 }),
  description: "A battered Ono-Sendai 7 cyberdeck. The jack plate is worn smooth.",
  asciiGlyph: "[D]",
  asciiColor: [100, 100, 150],
  upgradeSlots: 0,
  requiredMaterials: {},
  setId: "ono_sendai",
} as Equipment);

export const STARTER_HEADWARE: Equipment = Object.freeze({
  id: "head_basic",
  name: "Trodes (Stock)",
  slot: "headware",
  category: "wetware",
  tier: "T0",
  stats: s({ apBonus: 1 }),
  description: "Basic trodes. Brings the Matrix into focus, mostly.",
  asciiGlyph: "^H^",
  asciiColor: [180, 180, 200],
  upgradeSlots: 0,
  requiredMaterials: {},
  setId: null,
} as Equipment);

export const STREET_DECK: Equipment = Object.freeze({
  id: "deck_street",
  name: "Ono-Sendai 11 (Hot Rod)",
  slot: "deck",
  category: "hardware",
  tier: "T1",
  stats: s({ programPower: 12, critBonusPct: 5 }),
  description: "Hot-rodded Ono-Sendai with custom cooling. Burns through ICE like butter.",
  asciiGlyph: "[D+]",
  asciiColor: [200, 100, 0],
  upgradeSlots: 2,
  requiredMaterials: { ice_shard: 1, data_fragment: 2 },
  setId: "ono_sendai",
} as Equipment);

export const MILITECH_EYES: Equipment = Object.freeze({
  id: "eyes_militech",
  name: "Militech Eagle Eye",
  slot: "eyeware",
  category: "cybernetic",
  tier: "T1",
  stats: s({ attackBonus: 3, critBonusPct: 10 }),
  description: "Targeting reticle overlays. Highlights weak points in red.",
  asciiGlyph: "[E]",
  asciiColor: [255, 50, 50],
  upgradeSlots: 1,
  requiredMaterials: { data_fragment: 2, wetware_chip: 1 },
  setId: "militech",
} as Equipment);

export const CHROME_GLOVES: Equipment = Object.freeze({
  id: "gloves_chrome",
  name: "Chrome Surgical Gloves",
  slot: "gloves",
  category: "cybernetic",
  tier: "T1",
  stats: s({ attackBonus: 5, programPower: 3 }),
  description: "Fingers reinforced with chrome. Plug-compatible.",
  asciiGlyph: "[G]",
  asciiColor: [180, 180, 200],
  upgradeSlots: 1,
  requiredMaterials: { combat_module: 1 },
  setId: "militech",
} as Equipment);

export const CORPORATE_DECK: Equipment = Object.freeze({
  id: "deck_corporate",
  name: "Sakura Cybermod 'Samurai'",
  slot: "deck",
  category: "cybernetic",
  tier: "T2",
  stats: s({ programPower: 20, defense: 2, apRegenBonusPct: 20 }),
  description: "Japanese craftsmanship meets cutting-edge cybernetics.",
  asciiGlyph: "[D]",
  asciiColor: [200, 0, 100],
  upgradeSlots: 3,
  requiredMaterials: { ice_shard: 3, wetware_data: 1 },
  setId: "ono_sendai",
} as Equipment);

export const SUBDERMAL: Equipment = Object.freeze({
  id: "bodysuit_subdermal",
  name: "Subdermal Weave Mk.II",
  slot: "bodysuit",
  category: "bioware",
  tier: "T2",
  stats: s({ defense: 8, hpBonus: 20, iceResistance: 10 }),
  description: "Kevlar subdermal layer. Stops most small-caliber rounds.",
  asciiGlyph: "[B]",
  asciiColor: [100, 150, 100],
  upgradeSlots: 2,
  requiredMaterials: { wetware_data: 2, data_fragment: 1 },
  setId: null,
} as Equipment);

export const MILITECH_DECK: Equipment = Object.freeze({
  id: "deck_militech",
  name: "Militech Centurion",
  slot: "deck",
  category: "hardware",
  tier: "T3",
  stats: s({ programPower: 35, defense: 5, critBonusPct: 15, grantsSkillId: "jackhammer" }),
  description: "Military-grade hardware. Comes pre-loaded with combat programs.",
  asciiGlyph: "[D]",
  asciiColor: [0, 200, 0],
  upgradeSlots: 3,
  requiredMaterials: { ice_construct: 1, combat_module: 2 },
  setId: "militech",
} as Equipment);

export const TACTICAL_BODY: Equipment = Object.freeze({
  id: "bodysuit_tactical",
  name: "M-31 Combat Armor",
  slot: "bodysuit",
  category: "hardware",
  tier: "T3",
  stats: s({ defense: 20, hpBonus: 50, shieldBonus: 10, iceResistance: 25 }),
  description: "Full ballistic plating. Made the Arasaka tremble.",
  asciiGlyph: "[B]",
  asciiColor: [150, 150, 150],
  upgradeSlots: 3,
  requiredMaterials: { combat_module: 3, ice_construct: 2 },
  setId: null,
} as Equipment);

export const ARASAKA_DECK: Equipment = Object.freeze({
  id: "deck_arasaka",
  name: "Arasaka 'Onikiri'",
  slot: "deck",
  category: "cybernetic",
  tier: "T4",
  stats: s({ programPower: 60, defense: 10, critBonusPct: 20, grantsSkillId: "viral" }),
  description: "Top-tier Arasaka deck. Sleek, deadly, expensive.",
  asciiGlyph: "[D]",
  asciiColor: [255, 0, 0],
  upgradeSlots: 4,
  requiredMaterials: { ice_construct: 3, biosoft_agent: 2 },
  setId: "arasaka",
} as Equipment);

export const KEREZNIKOV: Equipment = Object.freeze({
  id: "head_kereznikov",
  name: "Kereznikov Boost",
  slot: "headware",
  category: "cybernetic",
  tier: "T4",
  stats: s({ apBonus: 3, apRegenBonusPct: 50, programPower: 15 }),
  description: "Russian implant. AP regenerates like you mainline stims.",
  asciiGlyph: "[K]",
  asciiColor: [200, 0, 0],
  upgradeSlots: 2,
  requiredMaterials: { biosoft_agent: 2, rom_echo: 1 },
  setId: "arasaka",
} as Equipment);

export const GHOST_DECK: Equipment = Object.freeze({
  id: "deck_ghost",
  name: "Ghost Cartographer",
  slot: "deck",
  category: "daemon",
  tier: "T5",
  stats: s({ programPower: 100, critBonusPct: 30, defense: 15, grantsSkillId: "bloodlust" }),
  description: "Experimental AI-assisted deck. Thinks for itself.",
  asciiGlyph: "[G]",
  asciiColor: [100, 255, 200],
  upgradeSlots: 5,
  requiredMaterials: { biosoft_agent: 5, rom_echo: 3, ice_construct: 5 },
  setId: null,
} as Equipment);

export const MASTER_DECK: Equipment = Object.freeze({
  id: "deck_master",
  name: "Wintermute / Neuromancer (Merged)",
  slot: "deck",
  category: "daemon",
  tier: "T6",
  stats: s({
    programPower: 150,
    defense: 25,
    critBonusPct: 40,
    apRegenBonusPct: 75,
    grantsSkillId: "omniscient",
    extraEffect: "Sees through all ICE. Love is the algorithm.",
  }),
  description: "The merged AI given physical form. Only the greatest jockey can hold it.",
  asciiGlyph: "[*]",
  asciiColor: [255, 255, 255],
  upgradeSlots: 0,
  requiredMaterials: {},
  setId: null,
} as Equipment);

export const MASTER_BODY: Equipment = Object.freeze({
  id: "bodysuit_master",
  name: "Full-Body Cyborg Conversion",
  slot: "bodysuit",
  category: "nanoware",
  tier: "T6",
  stats: s({
    defense: 40,
    hpBonus: 120,
    shieldBonus: 30,
    iceResistance: 50,
    apBonus: 4,
    extraEffect: "Immune to flatline (one revive per run)",
  }),
  description: "More machine than human. Most jockeys don't survive the operation.",
  asciiGlyph: "[#]",
  asciiColor: [255, 200, 100],
  upgradeSlots: 0,
  requiredMaterials: {},
  setId: null,
} as Equipment);

export const ZION_TRODES: Equipment = Object.freeze({
  id: "trodes_zion",
  name: "Zion Direct-Neural Link",
  slot: "trodes",
  category: "wetware",
  tier: "T6",
  stats: s({
    apBonus: 5,
    apRegenBonusPct: 100,
    programPower: 40,
    extraEffect: "Connects to Zion mainframe for support",
  }),
  description: "Maelcum's handiwork. Tunes the deck into your spinal cord directly.",
  asciiGlyph: "[Z]",
  asciiColor: [100, 255, 100],
  upgradeSlots: 0,
  requiredMaterials: {},
  setId: null,
} as Equipment);

export const NANO_HIVE: Equipment = Object.freeze({
  id: "implant_nanohive",
  name: "Nano-Hive",
  slot: "implant",
  category: "nanoware",
  tier: "T3",
  stats: s({ extraEffect: "Heals 2 HP per turn (poison immune)" }),
  description: "Billions of nanobots in your bloodstream. Maintenance nightmare.",
  asciiGlyph: "[N]",
  asciiColor: [0, 255, 100],
  upgradeSlots: 2,
  requiredMaterials: { wetware_data: 3, data_fragment: 5 },
  setId: null,
} as Equipment);

export const TRODES_NINJA: Equipment = Object.freeze({
  id: "trodes_ninja",
  name: "Stealth Trodes",
  slot: "trodes",
  category: "wetware",
  tier: "T2",
  stats: s({
    programPower: 10,
    critBonusPct: 15,
    extraEffect: "+Stealth in Matrix",
  }),
  description: "Silent connection. ICE can't trace you.",
  asciiGlyph: "[~]",
  asciiColor: [150, 100, 200],
  upgradeSlots: 1,
  requiredMaterials: {},
  setId: null,
} as Equipment);

export const BOOTS_GHOST: Equipment = Object.freeze({
  id: "boots_ghost",
  name: "Chameleon Boots",
  slot: "boots",
  category: "cybernetic",
  tier: "T2",
  stats: s({ defense: 3, hpBonus: 10, extraEffect: "+Movement speed (Matrix)" }),
  description: "Adaptive camouflage. Silent when you want to be.",
  asciiGlyph: "[B]",
  asciiColor: [100, 100, 150],
  upgradeSlots: 0,
  requiredMaterials: {},
  setId: null,
} as Equipment);

/** Default Gibson-inspired equipment set (16 pieces, T0..T6). */
export const DEFAULT_EQUIPMENT: ReadonlyArray<Equipment> = Object.freeze([
  // Tier 0
  STARTER_DECK,
  STARTER_HEADWARE,
  // Tier 1
  STREET_DECK,
  MILITECH_EYES,
  CHROME_GLOVES,
  // Tier 2
  CORPORATE_DECK,
  SUBDERMAL,
  TRODES_NINJA,
  BOOTS_GHOST,
  // Tier 3
  MILITECH_DECK,
  TACTICAL_BODY,
  NANO_HIVE,
  // Tier 4
  ARASAKA_DECK,
  KEREZNIKOV,
  // Tier 5
  GHOST_DECK,
  // Tier 6 (master)
  MASTER_DECK,
  MASTER_BODY,
  ZION_TRODES,
]);
