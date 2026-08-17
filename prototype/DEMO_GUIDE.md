# 🎮 Wet Run - Demo Playthrough Guide

Welcome to **Wet Run**, a cyberpunk roguelike inspired by William Gibson's Sprawl Trilogy.

This guide will walk you through playing the full demo from prologue to first combat.

---

## 📋 Quick Start

```bash
cd Game/wet_run/prototype
make demo
```

That's it! The demo will launch and take you through the complete game flow.

---

## 🎬 Demo Flow Overview

The demo consists of 4 main stages:

1. **Prologue** - Gibson's iconic opening scene (6 story lines)
2. **Briefing** - The Finn gives you your first job (5 story lines)
3. **Matrix** - Jack into cyberspace and explore the network
4. **Combat** - Engage ICE in real-time tactical combat

**Total playtime**: ~5-10 minutes

---

## 🕹️ Stage 1: Prologue

### What You'll See

```
═══════════════════════════════════════════════════════════════════════════════
  PROLOGUE — The Sprawl
═══════════════════════════════════════════════════════════════════════════════

  The sky above the port was the color of television, tuned to a dead channel.
```

### Features
- **Typing effect**: Text appears character by character
- **Glitch effects**: Random cyberpunk visual glitches
- **6 story lines**: Gibson's atmospheric world-building

### Controls
- **Any key**: Advance to next line
- **ESC**: Skip to next scene (Briefing)

### What to Expect
The prologue sets the mood with Gibson's iconic prose. Text will type out slowly with occasional glitches. Just sit back and enjoy the atmosphere, or press any key to speed through.

---

## 💼 Stage 2: Briefing - The Finn

### What You'll See

```
  ♠F♠ FINN:

  Got something for you.

  Sense/Net subsidiary. Demo file. Easy run. In and out.
```

### Features
- **NPC portrait**: The Finn appears with `♠F♠` ASCII portrait
- **Mission details**: Your first job - steal a demo file from Sense/Net
- **5 dialogue lines**: Quick briefing

### Controls
- **Any key**: Advance to next line
- **ESC**: Skip to Matrix

### What to Expect
The Finn gives you your mission. 500 credits for a simple data grab. Standard ICE, nothing fancy. You in?

---

## 🌐 Stage 3: Matrix Exploration

### What You'll See

```
MATRIX │ Sense/Net Grid 7G                                            CHROME: 500
────────────────────────────────────────────────────────────────────────────────

     [i]          [i]
                             [D]
         [!]
                       [@]              [i]


────────────────────────────────────────────────────────────────────────────────
← → ↑ ↓ Move   SPACE Action   Q Quit
────────────────────────────────────────────────────────────────────────────────
```

### Node Types
- `[@]` - **You** (player position)
- `[i]` - **Info Node** (documents, clues)
- `[D]` - **Data Node** (mission objective - extract this!)
- `[!]` - **ICE Node** (enemy - engage in combat)

### Controls
- **Arrow keys (← → ↑ ↓)**: Move between connected nodes
- **SPACE**: Open action menu at current node
- **Q**: Quit demo

### Action Menu
When you press SPACE at a node, you'll see:

```
+======================================+
| === DATA NODE ===                    |
| Kind: data                           |
|                                      |
| > [S] SCAN — analyze node            |
|   [E] EXTRACT — retrieve data        |
|                                      |
| ↑↓ Select  ENTER Confirm  ESC Cancel |
+======================================+
```

**Navigation**:
- **↑/↓ (Arrow keys)**: Select action (highlighted with `>`)
- **ENTER**: Confirm selected action
- **S/E/J/M** (Legacy): Direct key shortcuts still work
- **ESC**: Close menu

**Visual Indicators**:
- `>` - Currently selected (cyan color)
- Normal text (white) - Available
- `[LOCKED]` (dark gray) - Unavailable (Phase 6+ features)

### Strategy
1. **Move around** the grid using arrow keys
2. **SCAN** info nodes `[i]` for intel
3. **Find the Data node** `[D]` (your objective)
4. **EXTRACT** the file to complete the mission
5. **Or ENGAGE** an ICE node `[!]` to start combat

### What to Expect
You'll navigate a 5x5 network of nodes. The demo auto-progresses when you ENGAGE an ICE node or after exploring a bit.

---

## ⚔️ Stage 4: Combat (RT-MS System)

### What You'll See

```
════════════════════════════════════════════════════════════════════════════════
  COMBAT │ vs ICE-Sentinel
════════════════════════════════════════════════════════════════════════════════

  ICE-Sentinel                                                              
  [████████████████████████████████████████░░░░░░░░░░] 120/150 HP

  YOU — Console Cowboy
  [██████████████████████████████████████████████████] 100/100 HP

────────────────────────────────────────────────────────────────────────────────
  ACTIONS
────────────────────────────────────────────────────────────────────────────────
  1. ATTACK      [Ready]  Basic attack (15 dmg)
  2. ICE BREAKER [Ready]  Heavy hit (30 dmg, 2s cooldown)
  3. SCAN        [Ready]  Reveal weak point (5s cooldown)
  4. DEFEND      [Ready]  Reduce damage (10s cooldown)

────────────────────────────────────────────────────────────────────────────────
  LOG
────────────────────────────────────────────────────────────────────────────────
  > You attack ICE-Sentinel for 15 damage!
  > ICE-Sentinel attacks you for 8 damage!
  > You use ICE BREAKER on ICE-Sentinel for 30 damage!

────────────────────────────────────────────────────────────────────────────────
ESC Exit
────────────────────────────────────────────────────────────────────────────────
```

### Combat System: RT-MS (Real-Time with Menu Skills)

**Real-Time**: 
- Combat flows continuously
- Auto-attacks happen automatically every 2 seconds
- Enemy attacks in real-time

**Menu Skills**:
- Press **1-4** to use skills
- Skills have cooldowns (shown on button)
- `[Ready]` = can use now
- `[2.5s]` = cooldown remaining

### Available Skills
1. **ATTACK** - Basic melee (15 damage, instant)
2. **ICE BREAKER** - Power attack (30 damage, 2s cooldown)
3. **SCAN** - Reveal enemy stats (5s cooldown)
4. **DEFEND** - Reduce next damage (10s cooldown)

### Controls (Arrow Key Navigation)
- **↑/↓**: Select skill (highlighted with `>`)
- **ENTER**: Use selected skill
- **1-4** (Legacy): Quick use skill by number
- **ESC**: Exit combat (demo ends)

### Visual Indicators
The skills menu shows real-time status:
```
=== SKILLS ===

> [1] ATTACK [2 AP]        ← Selected (cyan)
  [2] ICE BREAKER [1.5s]   ← Cooldown (dark gray)
  [3] SCAN [3 AP]          ← Not enough AP (dark gray)
  [4] DEFEND [1 AP]        ← Available (white)
```

- `>` - Currently selected
- **Cyan** - Selected and ready
- **White** - Available (enough AP, no cooldown)
- **Dark gray** - Unavailable (cooldown or not enough AP)
- `[X AP]` - AP cost
- `[X.Xs]` - Cooldown remaining

### Strategy Tips
- **Auto-attacks** keep pressure on the enemy
- **Save ICE BREAKER** for when enemy HP is low
- **SCAN** early to see enemy stats
- **DEFEND** when enemy is about to attack
- **Watch cooldowns** - don't spam skills!

### What to Expect
Combat is fast-paced! The demo will run for ~20 seconds, then auto-progress to show the full combat system. You can press ESC anytime to end.

---

## ⚡ Demo Variants

### Standard Demo
```bash
make demo
```
- Normal typing speed
- Full cinematic experience
- ~5-10 minutes

### Fast Demo
```bash
make demo-fast
```
- **3x faster typing**
- Same content, quicker pace
- ~3-5 minutes

### Skip Prologue
```bash
make demo-skip
```
- **Starts at Briefing**
- Skip Gibson's intro
- Jump straight to the mission
- ~3-5 minutes

---

## 🎯 Demo Objectives Checklist

Follow this checklist to experience all features:

### Prologue
- [ ] Watch typing effect
- [ ] See at least one glitch effect
- [ ] Read all 6 story lines

### Briefing
- [ ] See Finn's ASCII portrait `♠F♠`
- [ ] Read mission details
- [ ] Understand the objective (steal demo file)

### Matrix
- [ ] Move with arrow keys
- [ ] Press SPACE to open action menu
- [ ] SCAN an info node `[i]`
- [ ] Find the data node `[D]`
- [ ] ENGAGE an ICE node `[!]` (triggers combat)

### Combat
- [ ] Watch auto-attacks happen
- [ ] Press **1** to use basic attack
- [ ] Press **2** to use ICE BREAKER
- [ ] See skill cooldowns
- [ ] Read action log
- [ ] Watch HP bars change

---

## 🐛 Troubleshooting

### Text looks garbled or unreadable

**Solution**: Font charmap issue (already fixed in latest version)
```bash
# Verify fix is applied
grep "CHARMAP_TCOD" src/wet_run/engine/app.py
```

### Window doesn't open

**Check font file exists**:
```bash
ls data/fonts/terminal10x10_gs_tc.png
```

If missing:
```bash
make download-font
```

### Want to verify content without graphics

**Run text-only demo**:
```bash
make text-demo
```
Shows all story text in plain terminal.

### Test font rendering

```bash
make test-tcod
```
Opens test window with alphabet and sample text.

---

## 📊 What's Implemented (Phase 5 Complete)

✅ **Cinematic System**
- Typing effects (3 speed levels)
- Glitch effects (random)
- NPC portraits
- Bilingual support (English + Korean placeholders)

✅ **Story Scenes**
- Prologue (Gibson's opening)
- Finn briefing (first mission)

✅ **Matrix Exploration**
- 5x5 grid network
- 3 node types (Info, Data, ICE)
- Movement system
- Action menu
- Node interactions

✅ **RT-MS Combat**
- Real-time auto-attacks
- Menu-based skills (4 abilities)
- Cooldown system
- HP bars
- Action log (10 recent events)

✅ **Full Demo Flow**
- Auto-progression between scenes
- Seamless transitions
- 124 unit tests passing

---

## 🎬 Enjoy the Demo!

You're now ready to experience the full Wet Run demo.

**"The sky above the port was the color of television, tuned to a dead channel."**

Jack in, cowboy. The Finn's got a job for you.

```bash
make demo
```

---

## 🆕 Phase 1-5 신규 데모 (Dungeon · VFX · 미션매핑 · ECS · Novel)

기존 데모(`make demo`) 와 별개로, Phase 1-5 가 추가한 핵심 게임플레이를
**헤드리스** (창 불필요) 로 빠르게 검증하는 5종:

```bash
PYTHONPATH=src .venv/bin/python scripts/play_dungeon_mode.py     # Phase 1
PYTHONPATH=src .venv/bin/python scripts/play_vfx_overlay.py      # Phase 1.5
PYTHONPATH=src .venv/bin/python scripts/play_mission_mapping.py  # Phase 3
PYTHONPATH=src .venv/bin/python scripts/play_ecs_dungeon.py      # Phase 4
PYTHONPATH=src .venv/bin/python scripts/play_novel_runtime.py    # Phase 5
```

각 데모는 5초 안에 끝나고 한 줄 요약을 출력합니다. 자세한 가이드:
`scripts/README.md` 의 "## 6. Phase 1-5 신규 데모" 섹션.

---

## 📝 Feedback

After playing, consider:
- Did the typing effects enhance the atmosphere?
- Was the Matrix navigation intuitive?
- Did the RT-MS combat feel responsive?
- Any bugs or unexpected behavior?

Share your thoughts to help improve the game!

---

## 🔜 Coming Next (Phase 6)

- More NPC scenes (Ratz, Molly, Armitage)
- Combat victory/defeat outcomes
- Salvage system (loot parts after combat)
- Hub upgrades (buy better gear)
- Mission completion → Debriefing → Rewards
- Full Korean font support (optional)

---

**Made with ❤️ and ASCII**

*Inspired by William Gibson's Sprawl Trilogy (Neuromancer, Count Zero, Mona Lisa Overdrive)*
