# Wet Run Playtest — Tester Onboarding Guide

**Version**: 1.0 | **Date**: 2026-09-01

---

## 🎮 What is Wet Run?

A cyberpunk roguelike based on William Gibson's **Sprawl Trilogy** (Neuromancer, Count Zero, Mona Lisa Overdrive). You play a **console cowboy** jacking into cyberspace to crack ICE, steal data, and survive.

- **Python CLI**: Full game with 9 characters, 47 missions, 5 chapters
- **Web (Tier 5)**: Browser-playable, mobile-friendly, cloud sync via Supabase

---

## 📥 How to Play

### Option A: Python CLI (Full Game)
```bash
# Quick test (no install)
uvx --from https://github.com/seoca1/wet-run/releases/download/v1.4.0/wet_run-1.4.0-py3-none-any.whl wet-run

# Or install via pipx
pipx install https://github.com/seoca1/wet-run/releases/download/v1.4.0/wet_run-1.4.0-py3-none-any.whl
wet-run
```
**Requires**: Python 3.11+, terminal with 80×50+ cols/rows

### Option B: Web (Tier 5) — **Recommended for Playtest**
👉 **https://seoca1.github.io/wet-run/play.html**

- Works on **desktop** (keyboard) + **mobile** (touch)
- **Cloud save** via Supabase (enable in Settings → Sync)
- No install, runs in browser

---

## 🎯 Test Scenarios (Your Mission)

| # | Scenario | Time | Goal |
|---|----------|------|------|
| **TC-01** | New Run → Character Select → Complete Chapter 1 | 10 min | Reach Chapter 2 without flatline |
| **TC-02** | Full 5-Chapter Run → Choose Ending → Read Coda | 30 min | Complete all 5 chapters, see Ending A or B |
| **TC-03** | Graphic Novel Mode → Auto-play 3 Jockeys | 5 min | 12 scenes play, Save/Continue works |
| **TC-04** | Save → Quit → Load → Continue | 3 min | State perfectly restored |
| **TC-05** | Settings → Volume/Colorblind/Keymap | 3 min | Changes apply instantly, persist after reload |
| **TC-06** | Die → Death Summary → Hall of Dead → New Jockey | 5 min | Meta progression preserved |

**Web-Only (if testing browser):**
| # | Scenario | Time | Goal |
|---|----------|------|------|
| **TW-01** | Mobile portrait/landscape | 10 min | Touch works, no layout breaks |
| **TW-02** | Volume sliders (Master/Music/SFX) | 3 min | Sliders work, persist on reload |
| **TW-03** | SFX on click/select/error/victory/defeat | 2 min | Each action plays sound |
| **TW-04** | IndexedDB save → compress → load | 5 min | 40%+ compression, full restore |

---

## 🎮 Controls

### Desktop (Keyboard)
| Key | Action |
|-----|--------|
| `Arrow Keys` / `WASD` | Navigate menus, move in matrix |
| `Enter` / `Space` | Confirm / Select |
| `1-9` | Use program (1=first in hand) |
| `Esc` / `Q` | Cancel / Jack out |
| `M` | Mute/unmute all audio |
| `S` | (Web) Manual sync now |

### Mobile (Touch)
- **Virtual gamepad** auto-appears on touch devices
- Tap program buttons to use
- Swipe to navigate matrix

---

## 🐛 How to Report Feedback

**Use the Google Form** (link provided separately) or document in this format:

```
## Bug Report
- **Repro Steps**: 1. ... 2. ... 3. ...
- **Expected**: ...
- **Actual**: ...
- **Severity**: Critical / Major / Minor / Cosmetic
- **Env**: OS, Browser/Terminal, Python version

## Improvement Suggestion
- **Area**: Combat / UI / Sound / Save / Web / Other
- **Description**: ...
- **Priority**: High / Medium / Low

## Highlight (What worked well)
- ...
```

---

## ⏱ Timeline

| Phase | Dates |
|-------|-------|
| **Testing Window** | Sep 8 – Sep 21, 2026 |
| **Feedback Due** | Sep 22, 2026 |
| **Report/Analysis** | Sep 23 – Sep 27 |

---

## 🔗 Links

- **Web Demo**: https://seoca1.github.io/wet-run/play.html
- **GitHub Repo**: https://github.com/seoca1/wet-run
- **Issues**: https://github.com/seoca1/wet-run/issues
- **Python Wheel**: GitHub Releases v1.4.0

---

## 💡 Tips

1. **First run**: Pick **K (Novice)** — easiest learning curve
2. **Programs**: `strike` (damage), `ward` (defense), `virus` (DoT), `hammer` (armor pierce)
3. **Alarm**: Keep under 100 or ICE gets reinforcements
4. **Graphic Novel**: Great for lore — auto-plays 12 scenes
5. **Web Sync**: Enable in Settings → Cloud Sync (requires Supabase config)

---

**Questions?** Open a GitHub Issue or reply to the playtest coordination message.

**Thank you for testing Wet Run!** 🖤