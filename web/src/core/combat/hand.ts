/** Hand refill — one rule, used at both places a hand is dealt.
 *
 * ADR-0278. A turn passes only when the hand empties (ADR-0212), so the hand is
 * the run's clock. Two things follow:
 *
 *   - Inside a fight, an empty hand is recycled from draw + discard (the
 *     original `drawHand` behaviour).
 *   - Between fights, the hand is topped back up to `handSize` when the loot
 *     screen closes. Before this, leftovers carried over: a fight won with two
 *     cards still in hand made the next fight start with two, and a card reward
 *     taken in between never reached the hand at all because the hand never
 *     emptied.
 *
 * The refill runs at loot, not at BREACH, so a SCAN spent on the encounter
 * screen stays spent for that fight (ADR-0247's cost).
 *
 * Order is preserved (draw pile first, then discard) and no RNG is consumed, so
 * a run stays deterministic and the balance harness is unaffected.
 */
import type { GameState } from "../types";

/** Top the hand up to `player.handSize`, or return the state unchanged. */
export function refillHand(state: GameState): GameState {
  const size = state.player.handSize;
  const need = size - state.deck.length;
  if (need <= 0) return state;
  const pool = [...state.drawPile, ...state.discardPile];
  if (pool.length === 0) return state;
  return {
    ...state,
    deck: [...state.deck, ...pool.slice(0, need)],
    drawPile: pool.slice(need),
    discardPile: [],
  };
}
