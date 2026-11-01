# Wet Run Playtest — Tester Onboarding Guide

**Version**: 2.0 | **Date**: 2026-11-01
**Status**: Current. The active build is the browser version in `web/` (TypeScript + Vite).

> **Revision note (2026-11-01).** Version 1.0 (2026-09-01) told testers to install a
> Python CLI (`uvx` / `pipx`) and to enable Supabase cloud sync. Both are gone: the
> Python prototype was retired on 2026-09-15 when it was merged into `web/` (commit
> `1b3cff4`), and there is no Supabase dependency anywhere in the code — saves are
> IndexedDB with a localStorage fallback. The demo URL also moved from `play.html`
> to `wetrun-web/`. Those instructions would have sent testers to a build that no
> longer exists.

---

## 1. What is Wet Run?

A cyberpunk roguelike built on William Gibson's **Sprawl Trilogy** (Neuromancer,
Count Zero, Mona Lisa Overdrive). You are a **console cowboy** jacking into
cyberspace to crack ICE, pull data, and get out alive.

- **Browser build (the playtest target)**: runs in a tab, desktop keyboard and
  mobile touch, ASCII Canvas2D rendering, Gibson green-on-black palette.
- **One build only.** There is no CLI and no desktop build to cross-check.

---

## 2. How to play

### Web (recommended)

👉 **https://seoca1.github.io/wet-run/wetrun-web/**

No install. Auto-deploys from `main` via `.github/workflows/pages.yml`. On touch
devices a virtual gamepad mounts automatically (`pointer: coarse`).

### Local build (for developers and repeatable checks)

```bash
cd web
npm install
npm run dev                     # Vite dev server (HMR)
# or the production bundle:
npm run build && npx vite preview --port 5195 --strictPort --host 127.0.0.1
```

**Note**: `--host 127.0.0.1` is required for `vite preview`. Without it the server
binds IPv6 only and `http://127.0.0.1:...` will not connect.

---

## 3. Saving

- **IndexedDB first, localStorage fallback** (ADR-0209), 4 slots: 1 autosave + 3 manual.
- **There is no cloud sync.** Nothing syncs between devices or browsers; a save stays
  in the browser profile that created it.
- Clearing site data deletes your runs. Reproduce a bug before clearing.

---

## 4. Test scenarios

| # | Scenario | Time | Goal |
| --- | --- | --- | --- |
| **TW-01** | New Run → mission select → launch a mission | 5 min | Reaches the matrix and an ICE encounter without getting stuck |
| **TW-02** | Fight one encounter to the end | 5 min | Win or loss resolves; hand, HP and log all update |
| **TW-03** | Idle in combat for ~30 seconds, then resume | 3 min | TRACE rises while you do nothing and stops rising once you act again |
| **TW-04** | Play slowly, then play fast, in the same encounter | 5 min | Your input *speed* should not change how hard the fight is |
| **TW-05** | Mobile portrait and landscape | 10 min | Touch works; nothing is clipped or overlapping |
| **TW-06** | Settings → volume / colourblind mode / text size | 3 min | Changes apply immediately and survive a reload |
| **TW-07** | Save → reload the page → Continue | 3 min | State restores, including progress through a run |
| **TW-08** | Graphic Novel mode → auto-play | 5 min | Scenes play through; you can skip and exit cleanly |
| **TW-09** | Die → death summary → Hall of Dead → new jockey | 5 min | The archive keeps the dead jockey; a new run starts clean |
| **TW-10** | Play at the smallest and largest window sizes you use | 5 min | The frame and HUD stay inside the viewport; text does not clip |

TW-03 and TW-04 matter most right now: TRACE is driven by **idle time** and the
Dixie companion is driven by **player turns**. Both changed recently, and the way to
catch a regression is to feel whether the *timing* of a fight behaves the way the
descriptions say.

---

## 5. Controls

### Desktop (keyboard)

| Key | Action |
| --- | --- |
| `Arrow keys` / `WASD` | Navigate menus; move in the matrix |
| `Enter` / `Space` | Confirm / select |
| `1`–`9` | Play the program at that hand position |
| `Esc` | Cancel / back |
| `Q` | Jack out |
| `M` | Mute / unmute BGM and SFX |

### Mobile (touch)

- A virtual gamepad mounts automatically on touch devices.
- Tap the program row to play a program; use the D-pad to move.

---

## 6. How to report feedback

```
## Bug report
- Repro steps: 1. ... 2. ... 3. ...
- Expected: ...
- Actual: ...
- Severity: Critical / Major / Minor / Cosmetic
- Env: OS, browser (+ version), screen size, and whether it reproduces on reload

## Improvement suggestion
- Area: Combat / UI / Sound / Save / Balance / Other
- Description: ...
- Priority: High / Medium / Low

## Highlight (what worked well)
- ...
```

Include a screenshot when the problem is visual. Several real defects were found by
looking at the rendered screen while every automated test passed.

---

## 7. Links

- **Play (web)**: https://seoca1.github.io/wet-run/wetrun-web/
- **Repository**: https://github.com/seoca1/wet-run
- **Issues**: https://github.com/seoca1/wet-run/issues

---

## 8. Tips

1. **The opening hand** is `backdoor`, `barrier`, `boost`, `cloak`, `decoy`. Work out
   what each one does before the first real fight.
2. **COST is for acting; TRACE is for idling.** The right panel's `COST N/100` is
   the program-cost accumulator: an expensive program pushes it up, and a program that
   would take it past 100 fails. The `TRACE N/5` row is idle pressure: it rises while
   you do nothing and makes ICE hit harder.
3. **Idling is meant to cost you.** If sitting still feels free, that is worth
   reporting (TW-03).
4. **Graphic Novel mode** is the fastest way to absorb the Gibson tone — it auto-plays
   the story scenes.
5. **Report feel, not win rates.** The numbers that matter (win rate per grade) are
   measured by `web/scripts/balance_sim.ts`. Tell us how a fight *felt* and whether
   anything looked wrong.

---

## 9. For automated and repeatable checks

Playwright drives the deterministic regression suite (`cd web && npm run e2e`). For a
real-browser pass where a human watches the render, see
[EGO_LITE_PLAY_CHECK.md](EGO_LITE_PLAY_CHECK.md) — a complement to Playwright, not a
replacement, because it has no fake-clock control.

---

**Questions?** Open a GitHub Issue.

**Thank you for testing Wet Run.**
