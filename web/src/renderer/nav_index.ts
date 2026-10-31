/** Shared list-numbering convention for navigable screens (UI triage U3).
 *
 * Main menu, mission select and matrix all label entries as 1-based `[N]`,
 * matching the digit keys (`1`..`9`) and the combat ICE list.
 */

/** Format a 0-based list index as the 1-based `[N]` navigation label. */
export function formatNavIndex(zeroBasedIndex: number): string {
  return `[${zeroBasedIndex + 1}]`;
}
