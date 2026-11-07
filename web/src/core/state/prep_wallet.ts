/** The runner's own money for prep (ADR-0284).
 *
 * ADR-0282 added a `SALVAGE` slot to the loot screen that paid credits, and
 * credits had nowhere to go: the prep budget (ADR-0283) comes from the mission's
 * advance, not from the run ledger. So SALVAGE was close to a trap — strictly
 * worse than a card or a repair.
 *
 * This is where those credits go: a small persistent stockpile the *next* run's
 * prep can draw on. It is deliberately capped in two places so it cannot defeat
 * the curve ADR-0283 tuned:
 *
 *   - a share of the grade's table value (so banking is worth at most +50% prep),
 *   - a floor for the grades whose table is zero, which is what makes "nothing
 *     offered" at grades 1-2 turn into something.
 *
 * Using prep **spends** the stockpile: it is a hoard, not a permanent bonus.
 * Stored in localStorage, like the far-grid unlock and the completion record —
 * not in `SaveSlot`, so there is no save-schema change.
 */
const WALLET_STORAGE_KEY = "wetrun_prep_wallet";

/** Most the stockpile can contribute to one prep, as a share of the table.
 *
 * **Zero, and that is a measurement.** At 0.5 the stockpile was worth +50% prep,
 * and a full one moved grade 5 from 31.9% to 51.4% (+19.5pp) and grade 6 from
 * 18.8% to 29.2% — it broke the curve ADR-0283 tuned, because those tables are
 * already fitted to the targets and have no headroom.
 *
 * So the stockpile does not stack on a tuned grant. It fills the gap where the
 * advance offers NOTHING (see `prepWalletContribution`), which is the one place
 * a surplus can be spent without moving a grade off its target.
 */
export const PREP_WALLET_SHARE = 0;

/** What the stockpile can buy where the table itself is zero, so the grades the
 * advance skips at least offer something to a returning runner. */
export const PREP_WALLET_FLOOR_HP = 15;
export const PREP_WALLET_FLOOR_SHIELD = 30;

/** Share of a SALVAGE payout that is banked for the next prep. Half, so the
 * slot pays now and later without turning into a farming engine. */
export const PREP_WALLET_BANK_SHARE = 0.5;

/** Read the stockpile. Returns 0 when storage is unavailable or malformed. */
export function readPrepWallet(): number {
  if (typeof localStorage === "undefined") return 0;
  try {
    const raw = localStorage.getItem(WALLET_STORAGE_KEY);
    if (raw === null) return 0;
    const value = Number.parseInt(raw, 10);
    return Number.isFinite(value) && value > 0 ? value : 0;
  } catch {
    return 0;
  }
}

/** Add to the stockpile; returns the new balance. */
export function addPrepWallet(amount: number): number {
  const next = readPrepWallet() + Math.max(0, Math.floor(amount));
  if (typeof localStorage === "undefined") return next;
  try {
    localStorage.setItem(WALLET_STORAGE_KEY, String(next));
  } catch {
    // Storage full or blocked: the stockpile is a bonus, never a blocker.
  }
  return next;
}

/** Spend from the stockpile; returns the new balance. */
export function spendPrepWallet(amount: number): number {
  const next = Math.max(0, readPrepWallet() - Math.max(0, Math.floor(amount)));
  if (typeof localStorage === "undefined") return next;
  try {
    localStorage.setItem(WALLET_STORAGE_KEY, String(next));
  } catch {
    // ignore
  }
  return next;
}

/** What the stockpile can add to one prep, given the grade's own value. */
export function prepWalletContribution(
  tableValue: number,
  balance: number,
  floor: number,
): number {
  if (balance <= 0) return 0;
  // A grade the advance already covers gets nothing extra: its table is fitted
  // to a target and a top-up would push it off. The stockpile is for the grades
  // the advance skips, which is what "nothing offered" was.
  if (tableValue > 0) return 0;
  return Math.min(balance, Math.max(floor, Math.floor(tableValue * PREP_WALLET_SHARE)));
}
