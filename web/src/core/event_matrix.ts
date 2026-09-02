/** Matrix event system (Tier 5.5, Stage 1).
 *
 * Adds 6 event kinds per matrix node (combat, discovery, trap, cache, rest,
 * merchant) on top of the linear combat-only matrix. Deterministic per seed.
 *
 * Distribution (mirrors Python matrix/event_matrix.py logic at MVP scope):
 * - surface (node 0): combat 90%, discovery 10%
 * - mid     (node 1): combat 70%, trap 20%, discovery 10%
 * - deep    (node 2): combat 60%, trap 30%, cache 10%
 * - core    (node 3): combat 60%, rest 20%, cache 20%
 * - boss    (node 4): combat 100% (boss)
 */
import type { Ice, MatrixNode, Program } from "./types.ts";

export type MatrixEventKind =
  | "combat"
  | "discovery"
  | "trap"
  | "cache"
  | "rest"
  | "merchant";

export interface MatrixEventData {
  // trap: damage dealt to player
  readonly damage?: number;
  // cache: program id offered (from programs catalog)
  readonly programId?: string;
  // discovery: bonus credits
  readonly creditsBonus?: number;
  // rest: heal percent (0..1)
  readonly healPct?: number;
  // merchant: programs for sale (catalog ids)
  readonly forSale?: ReadonlyArray<string>;
}

export interface EventedMatrixNode extends MatrixNode {
  readonly eventKind: MatrixEventKind;
  readonly eventData: MatrixEventData | null;
}

/** Deterministic weighted pick based on a seed-derived rng. */
export function pickEventKind(zone: MatrixNode["zone"], rng: () => number): MatrixEventKind {
  const r = rng();
  switch (zone) {
    case "surface":
      return r < 0.9 ? "combat" : "discovery";
    case "mid":
      if (r < 0.7) return "combat";
      if (r < 0.9) return "trap";
      return "discovery";
    case "deep":
      if (r < 0.6) return "combat";
      if (r < 0.9) return "trap";
      return "cache";
    case "core":
      if (r < 0.6) return "combat";
      if (r < 0.8) return "rest";
      return "cache";
    case "core-deep":
      return "combat"; // boss
    default:
      return "combat";
  }
}

/** Generate eventData for a given event kind. */
function generateEventData(
  kind: MatrixEventKind,
  _iceCatalog: Readonly<Record<string, Ice>>,
  programCatalog: Readonly<Record<string, Program>>,
  rng: () => number,
): MatrixEventData | null {
  switch (kind) {
    case "trap":
      return { damage: 10 + Math.floor(rng() * 11) }; // 10..20
    case "discovery":
      return { creditsBonus: 25 + Math.floor(rng() * 26) }; // 25..50
    case "cache":
      // Pick a random program that exists in the catalog.
      const programIds = Object.keys(programCatalog);
      if (programIds.length === 0) return null;
      const idx = Math.floor(rng() * programIds.length);
      const programId = programIds[idx] ?? programIds[0];
      return { programId };
    case "rest":
      return { healPct: 0.25 }; // 25% heal
    case "merchant":
      // Offer 2 random programs at 50% off (placeholder pricing).
      const allIds = Object.keys(programCatalog);
      if (allIds.length < 2) return null;
      const offers: string[] = [];
      for (let i = 0; i < 2 && i < allIds.length; i++) {
        const offerIdx = Math.floor(rng() * allIds.length);
        offers.push(allIds[offerIdx] ?? allIds[0]);
      }
      return { forSale: offers };
    case "combat":
    default:
      return null;
  }
}

/** Simple seedable RNG (Mulberry32) for deterministic events. */
export function makeRng(seed: number): () => number {
  let a = seed | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Build a 5-node matrix with varied event kinds (combat-heavy, some non-combat). */
export function buildEventMatrix(
  iceCatalog: Readonly<Record<string, Ice>>,
  programCatalog: Readonly<Record<string, Program>>,
  seed: number = 42,
): EventedMatrixNode[] {
  const rng = makeRng(seed);
  const zones: ReadonlyArray<MatrixNode["zone"]> = [
    "surface", "mid", "deep", "core", "core-deep",
  ];
  const fallbackIce = Object.values(iceCatalog)[0];
  const nodes: EventedMatrixNode[] = [];
  for (let i = 0; i < zones.length; i++) {
    const zone = zones[i] ?? "surface";
    const isLast = i === 4;
    const eventKind: MatrixEventKind = isLast ? "combat" : pickEventKind(zone, rng);
    const eventData = generateEventData(eventKind, iceCatalog, programCatalog, rng);
    const defaultIce = isLast ? "wintermute" : "watchdog";
    const ice = iceCatalog[defaultIce] ?? fallbackIce;
    const node: EventedMatrixNode = {
      id: i,
      zone,
      iceIds: ice ? [ice.id] : [],
      iceHp: ice ? [ice.hp] : [],
      reward: { credits: 50 + i * 25 },
      isBoss: isLast,
      adjacent: isLast ? [] : [i + 1],
      eventKind,
      eventData,
    };
    nodes.push(node);
  }
  return nodes;
}

/** Glyph for each event kind (matrix render). */
export const EVENT_GLYPHS: Readonly<Record<MatrixEventKind, string>> = {
  combat: "⚔",
  discovery: "★",
  trap: "✦",
  cache: "◆",
  rest: "♨",
  merchant: "⌘",
};

/** Short label for HUD. */
export const EVENT_LABELS: Readonly<Record<MatrixEventKind, string>> = {
  combat: "COMBAT",
  discovery: "DISCOVERY",
  trap: "TRAP",
  cache: "CACHE",
  rest: "REST",
  merchant: "MERCHANT",
};