# ⚡ Quick Start - Get to Combat in 30 Seconds

Fast track to experiencing combat in Wet Run.

---

## 🚀 Fastest Method (Auto-pilot)

```bash
cd Game/wet_run/prototype
make demo
```

**Just wait!** The demo will automatically:
1. Show prologue → auto-advance
2. Show briefing → auto-advance
3. Enter Matrix → auto-move to ICE
4. **Start Combat** ⚔️

**Total wait time**: ~10-15 seconds

---

## 🎮 Manual Speed-run (15 seconds)

```bash
make demo
```

**Press these keys in order**:

1. **ESC** (skip Prologue)
2. **ESC** (skip Briefing) 
3. **Wait 2 seconds** (Matrix loads)
4. **→ → ↑** (or any arrow keys to find ICE node)
5. Watch Side Panel until you see: **"Type: ICE"**
6. **SPACE** (open action menu)
7. **E** (ENGAGE)
8. **Combat starts!** ⚔️

---

## 🔍 Finding ICE Node Quickly

### Visual Method
Look for this in your current node box:
```
#===========#
║ ICE      ║  ← The word "ICE"
║ !ZDR:8   ║  ← "!" symbol
#===========#
```

### Side Panel Method (Recommended)
Move with arrow keys and watch the Side Panel:

```
=== CURRENT NODE ===
Name: Entry
Type: Entry      ← Keep moving until this says "ICE"
```

When you see **"Type: ICE"**:
```
=== CURRENT NODE ===
Name: ICE-Guardian
Type: ICE              ← Found it!

=== WHAT TO DO ===
→ SPACE: Engage ICE    ← This confirms it
```

Press **SPACE** → **E**

---

## 📋 Complete Key Sequence

Copy-paste this checklist:

```
[ ] make demo
[ ] ESC (skip prologue)
[ ] ESC (skip briefing)
[ ] Arrow keys until Side Panel shows "Type: ICE"
[ ] SPACE (action menu)
[ ] E (engage)
[ ] Combat! ⚔️
```

**Time**: 15-30 seconds depending on how many moves to find ICE.

---

## 🆕 Phase 1-5 Quick Look (D 키 · BSP · 미션매핑 · ECS · Novel)

Phase 1-5 (ADR-0060, ADR-0061) 가 추가한 핵심 게임플레이를 **창 없이** 빠르게 검증:

```bash
cd Game/wet_run/prototype

# Phase 1 — Dungeon Mode toggle (D 키) + BSP 절차적 미로
PYTHONPATH=src .venv/bin/python scripts/play_dungeon_mode.py

# Phase 1.5 — VFX 4종 (jackin_glitch / room_flash / data_acquired / jackout_whiteout)
PYTHONPATH=src .venv/bin/python scripts/play_vfx_overlay.py

# Phase 3 — 16 미션 → 룸 시퀀스 매핑
PYTHONPATH=src .venv/bin/python scripts/play_mission_mapping.py

# Phase 4 — ECS DungeonSystem (populate / on_enter / defeat)
PYTHONPATH=src .venv/bin/python scripts/play_ecs_dungeon.py

# Phase 5 — Novel runtime (catalog / manifest / dispatcher)
PYTHONPATH=src .venv/bin/python scripts/play_novel_runtime.py
```

전부 0 종료 + 한 줄 요약. 자세한 설명: `scripts/README.md` 섹션 6.

---

## 🎯 What to Do in Combat

Once combat starts, try these:

### Basic Actions
```
↑↓     Select skill
ENTER  Use selected skill
1-4    Quick use (number keys)
```

### Skills to Try
```
1  ATTACK      - Basic damage
2  ICE BREAKER - Heavy damage (wait for cooldown)
3  SCAN        - See enemy HP
4  DEFEND      - Create shield
```

### Watch For
- **HP bars** (yours and enemy)
- **Auto-attacks** (every 2 seconds)
- **Cooldowns** `[1.5s]` on skills
- **AP cost** `[2 AP]` on skills
- **Combat log** (bottom of main area)

---

## 💡 Tips

### If You Get Lost
**Check 3 places**:
1. **Title bar** (top): Shows current node name
2. **Side Panel** (right): Shows "Type: ICE" when you find it
3. **Footer** (bottom): Shows your last action

### If ICE is Hard to Find
- Matrix has 5-7 nodes total
- Just move around with arrows
- Check Side Panel after each move
- You'll find ICE within 3-5 moves

### If ESC Doesn't Work
- You might be in a menu already
- Try pressing ESC again
- Or press any key to advance

---

## 🐛 Troubleshooting

### "Unknown screen: menu" error
**Fixed!** Update to latest version:
```bash
cd prototype
git pull  # if in git repo
make all
```

### "Can't find ICE node"
**Matrix layout is randomized**, but ICE is always there:
- Keep moving with arrow keys
- Watch Side Panel's "Type" field
- Try all 4 directions (← → ↑ ↓)

### "ESC closes the game"
ESC from Prologue/Briefing = skip to next scene ✅  
ESC from Matrix = leave Matrix (goes to Hub)  
ESC from Combat = flee (goes to Hub)

**To get to combat**: ESC twice (skip scenes), then find ICE in Matrix

---

## 🎬 Video Walkthrough (Text)

```
00:00 - Terminal: make demo
00:01 - Prologue appears (typing animation)
00:02 - Press ESC
00:03 - Briefing appears (Finn talking)
00:04 - Press ESC
00:05 - Matrix screen loads
00:06 - See cyan box (current node)
00:07 - Press → (move right)
00:08 - Side Panel updates
00:09 - Press ↑ (move up)
00:10 - Side Panel shows "Type: ICE" ← Found it!
00:11 - Press SPACE
00:12 - Action menu opens
00:13 - Press E (ENGAGE)
00:14 - Combat screen loads
00:15 - ⚔️ You're in combat!
```

---

## 🏁 Success Checklist

You've successfully reached combat when you see:

```
✅ Title bar: "COMBAT │ vs ICE-Sentinel"
✅ Enemy HP bar at top
✅ Your HP bar below enemy
✅ Skills menu on right side
✅ Controls: "↑↓ Select Skill ENTER Use"
```

**Now you can test all the combat features!**

---

## 🔄 Quick Restart

To try again:
```bash
make demo
```

To skip straight to Matrix (faster):
```bash
make demo-skip
```

To speed up typing (faster scenes):
```bash
make demo-fast
```

---

**Happy hunting, cowboy! The Matrix awaits.** 🌃⚡
