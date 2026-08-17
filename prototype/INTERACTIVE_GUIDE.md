# 🎮 Interactive Adventure Mode

**You control everything!** No auto-pilot, no pre-determined paths.

---

## 🚀 Quick Start - Play Now

```bash
cd Game/wet_run/prototype
make play
```

This starts the **full game in interactive mode**:
1. **Prologue** - Read it (any key to advance)
2. **Briefing** - Read it (any key to advance)
3. **Matrix (Dungeon)** - **YOU** navigate with arrow keys
4. **NPCs** - **YOU** choose dialogue options
5. **Combat** - **YOU** select skills and attack

**The story unfolds based on YOUR choices!**

---

## 🎯 Two Demo Modes

### 1. Auto Demo (Just Watch)
```bash
make demo
```
- Auto-navigates through everything
- Auto-selects NPC options
- Auto-fights combat
- **No player agency** - just see the flow

### 2. Interactive Play (You Play!)
```bash
make play
```
- **YOU** move with arrow keys
- **YOU** read NPC dialogue
- **YOU** choose NPC responses
- **YOU** select combat skills
- **Multiple paths** and outcomes
- **Adventurous!**

---

## 🗺️ Dungeon - Multiple Paths

### The 7×5 Grid (not linear!)

```
   0    1    2    3    4    5    6
   +----+----+----+----+----+----+----+
0  |    |    |    |    |    |    |    |
   +----+----+----+----+----+----+----+
1  |    | SR |    |    |    |    |    |
   +----+----+----+----+----+----+----+
2  | E--|--C-|--N-|--C-|--D-|--C-|--I--|
   +----+----+----+----+----+----+----+
3  |    |    |    |    |    | SR | >> |
   +----+----+----+----+----+----+----+
4  |    |    |    |    |    |    |    |
   +----+----+----+----+----+----+----+
```

**You can go multiple ways!**

### Path 1: Direct East
```
Entry → Cor1 → NPC(Dixie) → Cor2 → Data → Cor3 → ICE → Exit
```

### Path 2: Side Room First
```
Entry → Cor1 → Side1 (↑) → back to Cor1 → continue
```

### Path 3: Different Order
```
Entry → Cor1 → Side1
  → Cor1 → NPC(Dixie) [talk or skip]
  → Cor2 → Data [examine or skip]
  → Cor3 → ICE [FIGHT or skip]
  → Exit
```

**You choose!**

---

## 🎭 NPC Dialogue - Multiple Branches

### Dixie Flatline (3 dialogue lines, 9+ choices total)

**Line 1: Opening**
```
1. Yeah, I'm on a job...      [GAIN_INFO]
2. Who wants to know?          [CONTINUE]
3. Got any advice?            [GAIN_INFO]
```

**Line 2: ICE Warning** (reached after Line 1)
```
1. Thanks, I'm out.            [GOODBYE → returns to matrix]
2. What do you know about data? [GAIN_INFO]
3. Need any help?              [GAIN_INFO - new quest hint]
4. Tell me about the Matrix.   [GAIN_INFO - lore]
```

**Line 3: Side Room Hint** (reached after Line 2)
```
1. I appreciate the help.      [GOODBYE]
2. Anything about the ICE?     [GAIN_INFO - tactical]
```

### Different Choices = Different Info!

| Choice | Result |
|--------|--------|
| 1 (Job) | Basic acknowledgment |
| 2 (Who) | Learn Dixie's identity |
| 3 (Advice) | Tactical info about ICE |
| 3 (Help) | Hint at future quest |
| 4 (Matrix) | Lore about the Sprawl |

**All logged in your status panel!**

---

## 🆕 Phase 1-5 — Interactive Adventure 확장

Phase 1-5 (ADR-0060, ADR-0061) 가 추가한 인터랙티브 요소:

| Phase | 추가된 인터랙션 | 키 / 트리거 |
|---|---|---|
| 1 | `Dungeon Mode` 토글 — 2-D BSP 그리드로 미로 보기 | `D` |
| 1.5 | VFX 4종 (jackin_glitch / room_flash / data_acquired / jackout_whiteout) | 자동 트리거 (상태 천이) |
| 2 | 절차적 BSP 미로 — 시드별 다른 레이아웃 | 자동 생성 |
| 3 | 미션 → 룸 시퀀스 자동 매핑 | 데이터 시 (GameStart) |
| 4 | ECS `DungeonSystem` (populate / on_enter / on_exit / defeat) | 룸 진입 시 |
| 5 | Novel 자동 dispatch — 6종 `HookKind` | 상태 천이 시 자동 |

### 소설 (Novel) Hook — Phase 5

소설 단편(`Fiction/derivative/sprawl-trilogy/short-stories/`)은
`novel/` 서브패키지의 dispatcher 가 자동 노출합니다. 게임플레이
중 발생:

```
NARRATIVE  — 챕터/씬 진입 시          (narrative_yield)
EXCERPT    — 미션 브리핑/엔딩 시       (excerpt_yield)
EVENT      — 스토리 이벤트 발생 시    (event_yield)
COMBAT     — ICE 격파 후              (after_combat)
ITEM       — 아이템 획득 시           (after_item)
CINEMATIC  — 시네마틱 트리거 시       (cinematic_yield)
```

확장 가능 — `register_hook_action(kind, fn)` 으로 새 hook 등록:

```python
from wet_run.novel.hooks import register_hook_action, HookKind

def my_action(ctx, app_state):
    ...

register_hook_action(HookKind.COMBAT, my_action)
```

검증:
```bash
PYTHONPATH=src .venv/bin/python scripts/play_novel_runtime.py
```

---

## ⚔️ Combat - Real Strategy

### When you reach ICE, the action menu opens:

```
╔════════════════════════════════════════╗
║ === ICE Barrier ===                    ║
║ Kind: ice                              ║
║                                        ║
║ > [S] SCAN — analyze defenses         ║
║   [E] ENGAGE — combat                  ║
║                                        ║
║ ↑↓ Select  ENTER Confirm  ESC Cancel  ║
╚════════════════════════════════════════╝
```

**Choose ENGAGE** to start combat.

### In Combat - YOU Pick Skills

```
=== SKILLS ===

> [1] ATTACK [2 AP]        ← Selected (Cyan)
  [2] ICE BREAKER [3 AP]
  [3] SCAN [1 AP]
  [4] DEFEND [1 AP]

↑↓ Select  ENTER Use
```

**Strategy**:
- Use **1** (ATTACK) often
- Save **2** (ICE BREAKER) for tough moments (cooldown 2s)
- Use **3** (SCAN) to check enemy HP
- Use **4** (DEFEND) when low HP

### Multiple Outcomes

**Victory**:
```
>>> VICTORY!
>>> Gained: 1x ICE Shard
>>> Returned to matrix
```

**Defeat** (if you lose):
```
>>> DEFEAT
>>> Returned to Hub
```

**Flee** (ESC):
```
>>> Disengaged from combat
```

**You can choose!**

---

## 🏆 Multiple Endings

### 1. Skip Everything (Speed-run)
```
Prologue → Briefing → Matrix → Exit (skip NPC, skip Data, skip ICE)
```
**Reward**: 0 materials, 0 combat XP

### 2. Talk to NPC Only
```
Prologue → Briefing → Matrix → Dixie (full dialogue) → Exit
```
**Reward**: Lots of info, no materials

### 3. Get Data + Skip Combat
```
Prologue → Briefing → Matrix → Dixie → Data → Exit
```
**Reward**: Some materials, no combat XP

### 4. Full Adventure (Recommended)
```
Prologue → Briefing → Matrix → Dixie → Data → ICE (combat) → Exit
```
**Reward**: ICE Shard, credits, XP

### 5. Explorer Mode
```
Prologue → Briefing → Matrix → visit all side rooms → NPC → Data → ICE
```
**Reward**: Maximum info, full clear

---

## 🕹️ Full Controls Reference

### Matrix (Dungeon)
| Key | Action |
|-----|--------|
| **↑** | Move NORTH (up) |
| **↓** | Move SOUTH (down) |
| **←** | Move WEST (left) |
| **→** | Move EAST (right) |
| **SPACE** | Open action menu |
| **ESC** | Leave matrix |
| **Q** | Quit |

### Action Menu
| Key | Action |
|-----|--------|
| **↑↓** | Select action |
| **ENTER** | Confirm |
| **S/E/J** | Quick select |
| **ESC** | Cancel |

### NPC Dialogue
| Key | Action |
|-----|--------|
| **↑↓** | Select choice |
| **ENTER** | Confirm |
| **1-9** | Quick select |
| **ESC** | Leave conversation |

### Combat
| Key | Action |
|-----|--------|
| **↑↓** | Select skill |
| **ENTER** | Use skill |
| **1-4** | Quick use |
| **ESC** | Flee/disengage |

---

## 💡 Pro Tips

### Exploration
- **Side rooms** may have secrets (Phase 6+)
- **NPCs** give hints about what's ahead
- **Re-visit** rooms - some change after events

### NPC Strategy
- **Read everything** - info is logged
- **Ask questions** - get tactical intel
- **Try multiple branches** - see all outcomes

### Combat Strategy
- **Watch AP** - don't waste it
- **Save ICE BREAKER** for emergencies
- **Use DEFEND** when low HP
- **Auto-attack happens** - skills are bonus

---

## 🎮 Try All Paths!

### Suggested Playthroughs

**Path A: Speed-run**
1. Prologue (any key × 6)
2. Briefing (any key × 5)
3. Matrix: press → → → → → (skip NPC, skip Data)
4. Reach Exit

**Path B: Full Adventure** (Recommended first)
1. Prologue (read it!)
2. Briefing (read it!)
3. Matrix: → → [talk to Dixie] → → [get data] → → [FIGHT!]
4. Combat: Use skills to win
5. Win → Return to matrix

**Path C: Explorer**
1. Prologue + Briefing
2. Matrix: visit every room
3. Talk to all NPCs (future)
4. Find all secrets

---

## 📊 What You Can Do

| Action | Demo Mode | Play Mode |
|--------|-----------|-----------|
| Skip Prologue | ✓ | ✓ (press any key) |
| Read Briefing | Auto-advance | ✓ (any key) |
| Move in Dungeon | Auto | ✓ (arrow keys) |
| Choose NPC option | Auto | ✓ (↑↓+ENTER) |
| Skip NPC | Auto | ✓ (ESC anytime) |
| Use combat skill | Auto | ✓ (↑↓+ENTER) |
| Flee combat | Auto | ✓ (ESC) |
| Visit side rooms | Auto | ✓ (manually) |
| Explore freely | ✗ | ✓ |

---

## 🎯 The Adventure Awaits!

```bash
make play
```

**You are Case. A console cowboy. The Sprawl awaits.**

Will you be cautious? Reckless? Curious? It's your call. 🌃⚡
