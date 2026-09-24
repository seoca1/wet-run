/**
 * Starter Deck — minimal default programs used by main.ts on NEW RUN.
 *
 * The full catalog lives in `data/programs.json` (hand-maintained since the
 * Python prototype export pipeline was retired 2026-09-15). That data file uses a slightly
 * different schema (`ap_cost`, `shield`, `damage`, `role`) targeting the
 * round-based Python combat, so it isn't a drop-in for the web tier 1 MVP.
 *
 * To keep `main.ts.createInitialState()` bootable without an async data fetch,
 * this module defines an 8-card starting hand tuned for tier 1:
 *
 * - 3× Strike (basic attack, cheap AP, low damage)
 * - 2× Shield (block, defense)
 * - 1× Probe (intel, AP-efficient)
 * - 1× Wisp (shield buff)
 * - 1× Cloak (alarm reduction)
 *
 * First 5 are the opening hand; remaining 3 form the draw pile.
 *
 * If you replace this with a loader for `data/programs.json`, keep the public
 * exports stable: `STARTER_DECK` (read-only `Program[]`) and `STARTER_HAND_SIZE`.
 */
import type { Program } from "./types.ts";

/**
 * Frozen array; callers must not mutate. Use `.slice()` to derive a hand.
 */
export const STARTER_DECK: readonly Program[] = Object.freeze([
  {
    id: "strike_a",
    name: "Strike",
    tier: 1,
    cost: 3,
    effect: "attack",
    description: "Basic attack. Cheap, weak, reliable.",
    aoe: false,
  },
  {
    id: "strike_b",
    name: "Strike",
    tier: 1,
    cost: 3,
    effect: "attack",
    description: "Basic attack. Cheap, weak, reliable.",
    aoe: false,
  },
  {
    id: "strike_c",
    name: "Strike",
    tier: 1,
    cost: 3,
    effect: "attack",
    description: "Basic attack. Cheap, weak, reliable.",
    aoe: false,
  },
  {
    id: "shield_a",
    name: "Shield",
    tier: 1,
    cost: 2,
    effect: "defense",
    description: "Block one incoming attack.",
    aoe: false,
  },
  {
    id: "shield_b",
    name: "Shield",
    tier: 1,
    cost: 2,
    effect: "defense",
    description: "Block one incoming attack.",
    aoe: false,
  },
  {
    id: "wisp_a",
    name: "Wisp",
    tier: 1,
    cost: 4,
    effect: "buff",
    description: "Adds a temporary shield buff.",
    aoe: false,
  },
  {
    id: "probe_a",
    name: "Probe",
    tier: 1,
    cost: 1,
    effect: "intel",
    description: "Reveals ICE weakness. Cheap recon.",
    aoe: false,
  },
  {
    id: "cloak_a",
    name: "Cloak",
    tier: 1,
    cost: 5,
    effect: "stealth",
    description: "Reduces alarm; passive ICE may lose aggro.",
    aoe: false,
  },
] as Program[]);

/** Number of cards dealt to the player's hand at run start. */
export const STARTER_HAND_SIZE = 5;
