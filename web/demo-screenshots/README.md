# demo-screenshots — 2026-10-13 snapshot (historical)

These 18 PNGs are a **historical snapshot** of the game's screens, captured
2026-10-13. They predate ADR-0231..0236 (combat-feel / audio / accessibility
work) and the 2026-10-31 UI overhaul that framed every screen, derived the canvas
geometry from the viewport, and decomposed `main.ts`.

> `05-combat.png` still shows the old `ICE HP: undefined` / `NaN/100` readout,
> which has since been fixed — a useful reminder that this set is stale.

## Provenance

`web/e2e/demo-screenshots.spec.ts` **no longer writes here.** Its `SCREENSHOT_DIR`
resolves to `web/test-results/demo-shots/`, which is gitignored
(`web/.gitignore:11`) — deliberate and correct for a CI gate, since a test must
not dirty tracked files. As a result this directory has no generator that
reproduces it in place.

## Where the current baseline lives

The post-overhaul visual baseline is
[`../../docs/design/before-after-2026-10-31/`](../../docs/design/before-after-2026-10-31/)
— before/after captures of the menu, mission select, combat, matrix, dungeon,
crafting, equipment and settings screens, plus the Manus A/B/C concept sheet in
`../../docs/design/manus-concepts-2026-10-31/`.

## Replacing this set

That is a deliberate decision, not routine: the spec covers only 8 of these 18
names, so a partial refresh would leave a mixed-age set that is harder to trust
than a uniformly stale one. Either point a spec at this directory and regenerate
all 18, or keep this as the historical record.
