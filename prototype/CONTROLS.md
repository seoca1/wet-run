# 🎮 Wet Run - Controls Reference

Quick reference for all game controls.

---

## 🌟 Universal Controls

| Key | Action |
|-----|--------|
| **↑↓** | Navigate menus (select items) |
| **ENTER** or **SPACE** | Confirm / Use selected item (either works!) |
| **ESC** | Cancel / Back / Close menu |
| **Q** | Quit game |

> 💡 **Tip**: Both `ENTER` and `SPACE` work the same way for all confirmation actions. Use whichever is more comfortable!

---

## 📺 Cinematic Scenes (Story)

| Key | Action |
|-----|--------|
| **ENTER** or **SPACE** | Advance to next line |
| **ESC** | Skip to next scene |

**What you'll see**: Typing effects, glitch effects, NPC portraits, Korean subtitles

---

## 🌐 Matrix Exploration

### Movement
| Key | Action |
|-----|--------|
| **← → ↑ ↓** | Move between nodes |
| **D** | Toggle **Dungeon Mode** (Phase 1) — 2-D BSP 그리드 보기 |
| **ENTER** or **SPACE** | Open action menu at current node |
| **Q** | Quit to menu |

### Action Menu
When you press ENTER/SPACE at a node:

| Key | Action |
|-----|--------|
| **↑↓** | Select action |
| **ENTER** or **SPACE** | Confirm selected action |
| **S** | SCAN (quick shortcut) |
| **E** | EXTRACT/ENGAGE (quick shortcut) |
| **J** | JACK OUT (quick shortcut) |
| **ESC** | Close menu |

**Visual Indicators**:
- `>` = Selected item (cyan)
- Normal text = Available
- `[LOCKED]` (dark gray) = Unavailable

---

## ⚔️ Combat (RT-MS)

### Skill Selection
| Key | Action |
|-----|--------|
| **↑↓** | Select skill |
| **ENTER** or **SPACE** | Use selected skill |
| **1-4** | Quick use skill (number shortcut) |
| **ESC** | Disengage / Flee |

### Skill Status Colors
- **>** = Currently selected
- **Cyan** = Selected and ready to use
- **White** = Available (enough AP, no cooldown)
- **Dark gray** = Unavailable (not enough AP or on cooldown)

### Status Display
- `[X AP]` = Action Point cost
- `[X.Xs]` = Cooldown remaining in seconds

**Example**:
```
=== SKILLS ===

> [1] ATTACK [2 AP]        ← Selected, ready (cyan)
  [2] ICE BREAKER [1.5s]   ← Cooldown active (gray)
  [3] SCAN [3 AP]          ← Not enough AP (gray)
  [4] DEFEND [1 AP]        ← Available (white)

↑↓ Select  ENTER Use  1-4 Quick use  ESC Disengage
```

---

## 🎯 Control Philosophy

### Unified Confirm Keys
**All confirmation actions accept both `ENTER` and `SPACE`**:
- Menu selection
- Skill use
- Action menu
- NPC choice
- Server jack-in
- Continue after combat
- Advance dialogue

**No more confusion** - press whichever is natural!

### Arrow Key Navigation (Primary)
All menus support **arrow key navigation** for intuitive control:
1. **↑↓** to browse options
2. **ENTER** or **SPACE** to confirm
3. Visual feedback (cursor `>` and color coding)

### Number Key Shortcuts (Secondary)
Expert players can use **1-9 number keys** for quick access without navigation.

### Visual Feedback
- **Cursor (`>`)**: Shows selected item
- **Color coding**: 
  - Cyan = Selected
  - White = Available
  - Dark gray = Disabled/Locked
- **Status text**: `[AP cost]`, `[cooldown]`, `[LOCKED]`

---

## 💡 Quick Tips

### New Players
- Use **arrow keys** exclusively - no memorization needed
- Watch the color: gray = can't use, cyan = ready
- Read the footer for context-specific controls

### Experienced Players
- Use **number keys** for faster skill/action selection
- **S** key for quick SCAN in Matrix
- **E** key for quick EXTRACT/ENGAGE
- **D** key for quick **Dungeon Mode** toggle (Phase 1)
- Muscle memory: 1=Attack, 2=Power skill, 3=Utility, 4=Defense

### Novel Hooks (Phase 5 — ADR-0061)

소설 통합 레이어는 자동 트리거되며 별도 키가 없습니다. 6종 `HookKind`
(`narrative` / `excerpt` / `event` / `combat` / `item` / `cinematic`) 가
상태 천이 시 자동 dispatch 됩니다. 등록/확장은 Python API 만 사용:

```python
from wet_run.novel.hooks import register_hook_action, HookKind

def my_action(ctx, app_state):
    ...

register_hook_action(HookKind.COMBAT, my_action)
```

---

## 🔄 Migration from Phase 4

**Old system** (Phase 4 and earlier):
- Only number keys (1-9) or letter shortcuts
- No visual selection
- Hard to remember which key does what

**New system** (Phase 5+):
- ✅ Arrow key navigation with visual cursor
- ✅ Color-coded availability
- ✅ Real-time status (AP, cooldowns)
- ✅ Legacy shortcuts still work

**You can use both!** Arrow keys for exploration, number keys when you know what you want.

---

## 🎮 Platform Notes

- **macOS**: All controls tested and working
- **Arrow keys**: Standard terminal arrow keys
- **ENTER**: Return key
- **Number keys**: Top row number keys (not numpad)

---

**Made for maximum accessibility and intuitive gameplay**

*No complex combos, no memorization required - just arrow keys and ENTER!*
