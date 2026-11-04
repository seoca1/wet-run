// program_effects.ts — what each program actually does (ADR-0255).
//
// Single source of truth for the mechanic behind a card. The hand label,
// the tooltip and the reducer all read it, so a card's text cannot drift
// away from its behaviour (ADR-0251 rule 5: the affordance states what
// the screen will do).
//
// Every program deals `tier * 5` damage to the ICE — the web tier has one
// damage path (`baseDamage: program.tier * 5` in state_actions_programs.ts).
// What separates the cards is the effect below: a program that says
// "shield" actually grants a shield, and the text says so.

import type { Program } from "../types";

export type ProgramEffectKind =
  /** No extra effect — the plain tier * 5 attack. */
  | "damage"
  /** The attack ignores N points of the target's armor. */
  | "pierce"
  /** The attack ignores N percent of the target's armor (ADR-0277). */
  | "armor_ignore"
  /** A pool that absorbs incoming damage. */
  | "shield"
  /** The player's damage rises for a few turns. */
  | "empower"
  /** Incoming damage is reduced for a few turns. */
  | "evade"
  /** The next incoming hit is soaked entirely. */
  | "decoy";

export interface ProgramEffect {
  readonly kind: ProgramEffectKind;
  /**
   * Percent for pierce / evade, points for shield, flat damage for empower,
   * hits for decoy.
   */
  readonly amount: number;
  /** Player turns the effect lasts. 0 = the attack it was used on. */
  readonly turns: number;
}

export const NO_EFFECT: ProgramEffect = Object.freeze({
  kind: "damage",
  amount: 0,
  turns: 0,
});

/**
 * The programs whose mechanics are wired. These are the cards the jockey
 * decks actually hold (ADR-0260, ADR-0276), so their mechanics are the ones
 * that have to be real. Every other catalog program stays a plain tier * 5
 * attack and its designed effect stays in `plannedDescription`.
 */
export const PROGRAM_EFFECTS: Readonly<Record<string, ProgramEffect>> =
  Object.freeze({
    // Sized against the ICE armor curve (tier 1 avg 1.0 -> tier 6 avg 10.5)
    // against a tier*5 player hit: a 3-point pierce is a real gain on the
    // lightly armored ICEs without doubling the hit on the armored ones.
    backdoor: Object.freeze({ kind: "pierce", amount: 2, turns: 0 }),
    // ADR-0277: `exploit` is the generalist's answer to armor. A flat pierce
    // is worth nothing against an unarmored ICE and everything against a
    // heavily armored one; a share of the armor scales with the target, which
    // is the ICE tier curve itself (armor runs 1.0 at tier 1 to 10.5 at
    // tier 6). Half is sized so the card stays a tier-3 attack on light ICE
    // and turns into roughly a tier-4 hit on the armored ones.
    exploit: Object.freeze({ kind: "armor_ignore", amount: 50, turns: 0 }),
    barrier: Object.freeze({ kind: "shield", amount: 2, turns: 2 }),
    // `powered` adds a flat bonus to the player's attacks (combat_engine.ts
    // reads `attackerAttackBonus`), so the amount is points, not percent.
    boost: Object.freeze({ kind: "empower", amount: 2, turns: 2 }),
    cloak: Object.freeze({ kind: "evade", amount: 15, turns: 2 }),
    decoy: Object.freeze({ kind: "decoy", amount: 50, turns: 1 }),
  });

/** The effect of a program — the plain attack when it has no special one. */
export function programEffect(program: Pick<Program, "id">): ProgramEffect {
  return PROGRAM_EFFECTS[program.id] ?? NO_EFFECT;
}

/** The damage a program deals: one path, `tier * 5` (state_actions_programs.ts). */
export function programBaseDamage(program: Pick<Program, "tier">): number {
  return program.tier * 5;
}

/**
 * The program's description — built from the mechanic, so it cannot lie.
 * (The designed effect that is not wired yet stays in `plannedDescription`.)
 */
export function programEffectDescription(
  program: Pick<Program, "id" | "tier" | "aoe">,
): string {
  const effect = programEffect(program);
  const target = program.aoe ? "every ICE" : "the ICE";
  const damage = `Deals ${programBaseDamage(program)} damage to ${target}`;
  switch (effect.kind) {
    case "pierce":
      return `${damage} and ignores ${effect.amount} points of its armor.`;
    case "armor_ignore":
      return `${damage} and ignores ${effect.amount}% of its armor.`;
    case "shield":
      return `${damage} and grants a ${effect.amount}-point shield for ${effect.turns} turns.`;
    case "empower":
      return `${damage} and adds ${effect.amount} damage to your attacks for ${effect.turns} turns.`;
    case "evade":
      return `${damage} and cuts incoming damage by ${effect.amount}% for ${effect.turns} turns.`;
    case "decoy":
      return `${damage} and soaks ${effect.amount}% of the next hit.`;
    default:
      return `${damage}.`;
  }
}

/** Short effect tag for the hand row — the affordance must read without color. */
export function programEffectTag(program: Pick<Program, "id">): string {
  const effect = programEffect(program);
  switch (effect.kind) {
    case "pierce":
      return `PIERCE ${effect.amount}`;
    case "armor_ignore":
      return `ARMOR -${effect.amount}%`;
    case "shield":
      return `SHIELD ${effect.amount}`;
    case "empower":
      return `ATK +${effect.amount}`;
    case "evade":
      return `EVADE ${effect.amount}%`;
    case "decoy":
      return `DECOY ${effect.amount}%`;
    default:
      return "";
  }
}
