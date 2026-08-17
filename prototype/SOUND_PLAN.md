# 🔊 Sound Integration Plan - Wet Run

## Overview

This plan adds sound effects to the game in **6 phases** over multiple sessions, starting with zero-dependency approaches and upgrading as needed. Each phase includes validation tools to ensure the implementation works.

**Approach**: Subprocess-based playback using system tools (`afplay` on macOS, `aplay`/`paplay` on Linux) for zero dependencies. Can be upgraded to `simpleaudio` or `pygame` for richer features later.

---

## Phase 1: Research & Library Evaluation

**Goal**: Determine the best sound library for our needs

**Tasks**:
- [x] Test 3 candidate libraries (`playsound`, `simpleaudio`, `afplay` subprocess)
- [x] Document which works on each platform (macOS, Linux, Windows)
- [x] Create validation script: `scripts/test_sound_libraries.py`

**Validation tool** (`scripts/test_sound_libraries.py`):
- Tests if each library is available
- Plays a test sound with each
- Measures latency
- Reports compatibility

**Success criteria**:
- At least one method works on each platform
- Documentation of method chosen

---

## Phase 2: Sound Asset Preparation

**Goal**: Create/find sound files for the game

**Tasks**:
- [x] Create `data/sounds/` directory (data/sounds_test/ for generated placeholders)
- [x] Define sound categories:
  - `ui/` - Menu navigation, confirmation, error
  - `combat/` - Attacks, damage, victory, defeat
  - `story/` - Typing effect, dialogue, event trigger
  - `movement/` - Walk, jack-in, jack-out
  - `items/` - Equipment, pickup
- [x] Generate placeholder sounds (synthesized via wave module, 27 files)
- [x] Document each sound file with: inline metadata in DEFAULT_SOUNDS

**Sound design philosophy** (Gibson-inspired):
- Minimal, atmospheric sounds
- Cyberpunk: synthetic, electronic tones
- Short duration (50-500ms typical)
- Optional layer system (multiple sounds at once)

**Success criteria**:
- Sound directory structure exists
- At least 3 placeholder sounds playable
- Documentation for each sound

---

## Phase 3: Sound Manager Core

**Goal**: Create a centralized sound playback system

**Tasks**:
- [x] Create `src/wet_run/audio/sound_manager.py` (267 lines)
- [x] Implement `SoundManager` class:
  - `play(sound_name: str)` - Play a sound
  - `stop_all()` - Stop all sounds
  - `set_volume(volume: float)` - Master volume
  - `set_mute(muted: bool)` - Mute toggle
  - `is_available()` - Check if sound is available
  - `toggle_mute()` - Toggle and return new state
  - `list_sounds()` - List available sounds
- [x] Use `afplay` (macOS) / `aplay` (Linux) / `winsound` (Windows) via abstraction
- [x] Threading for non-blocking playback
- [x] Process handle management with lock

**Validation tool** (`scripts/test_sound_manager.py`):
- Plays 5 test sounds in sequence
- Verifies non-blocking playback
- Tests volume/mute controls
- Reports errors gracefully

**Success criteria**:
- Sounds play without blocking game
- Volume/mute works
- No memory leaks

---

## Phase 4: First Sounds (UI & Story)

**Goal**: Add sounds to story and menu (high visibility)

**Tasks**:
- [x] Hook into `story_cinematic.py` - typing sound (text_typing, event_trigger)
- [x] Hook into `cyberspace_browser.py` - jack-in sound
- [x] Hook into `hub.py` - mission select sound (helper added)
- [x] Hook into `action_menu.py` - menu open/close (select, cancel)
- [x] Hook into `npc_view.py` - dialogue advance (select, confirm, advance)

**Sounds to add**:
- `text_typing` - Per character in cinematic (or every 2-3 chars)
- `menu_select` - On ↑↓ navigation
- `menu_confirm` - On ENTER/SPACE
- `menu_cancel` - On ESC
- `dialogue_advance` - On dialogue continue

**Validation tool** (`scripts/test_story_sounds.py`):
- Plays test story with sounds
- Verifies timing (not too fast/slow)
- Tests integration without errors

**Success criteria**:
- Sounds play at correct game events
- No performance degradation
- Sounds can be muted

---

## Phase 5: Combat Sounds

**Goal**: Add combat sound effects

**Tasks**:
- [x] Hook into `combat_view.py` - skill effects (mapped by SkillEffect)
- [x] Hook into `step_combat` - auto-attack sounds (handled by use_skill)
- [x] Hook into `use_skill` - skill use sounds (14 effect types mapped)
- [x] Hook into status effects - buff/debuff sounds
- [x] Hook into victory/defeat - end sounds (combat/victory, combat/defeat)

**Sounds to add**:
- `combat_hit` - Normal attack lands
- `combat_crit` - Critical hit (more impactful)
- `combat_miss` - Dodge/miss
- `skill_physical` - Physical skill (jackhammer, goliath)
- `skill_magic` - Magical skill (viral, etc)
- `skill_heal` - Heal/buff
- `skill_buff` - Self buff
- `skill_debuff` - Enemy debuff
- `combat_block` - Shield absorbs damage
- `combat_victory` - Win
- `combat_defeat` - Lose
- `combat_dodge` - Dodge attack

**Validation tool** (`scripts/test_combat_sounds.py`):
- Simulates a full combat
- Verifies each skill type plays correct sound
- Tests volume layering

**Success criteria**:
- Each combat action has appropriate sound
- Combat feels more dynamic
- No audio glitches

---

## Phase 6: UI / Navigation & Polish

**Goal**: Polish the audio experience

**Tasks**:
- [x] Add navigation sounds (movement in cyberspace) - cyberspace_view: nav_step/nav_block
- [x] Add equipment equip/unequip sounds (helpers added in equipment_view)
- [x] Add item pickup sounds (data/sounds_test/items_pickup.wav ready)
- [ ] Add level-up / achievement sounds (future)
- [x] Add error/warning sounds (ui/error.wav ready)
- [x] Add volume control in game settings - status panel shows Vol:%, +/- keys
- [x] Add mute toggle - M key (global hotkey) + status panel display

**Sounds to add**:
- `nav_step` - Movement between rooms
- `nav_block` - Movement blocked
- `equip_item` - Equip gear
- `item_pickup` - Pick up material
- `error` - Invalid action
- `notification` - New item/achievement
- `jack_in` - Enter cyberspace
- `jack_out` - Exit cyberspace
- `combat_stun` - Stun effect
- `combat_heal` - Heal

**Validation tool** (`scripts/test_full_audio.py`):
- Plays a complete game session
- Logs all audio events
- Reports coverage % (how many game events have audio)

**Success criteria**:
- All major game events have audio
- User can mute easily
- Settings persist

---

## 🎯 Implementation Order & Effort Estimate

| Phase | Description | Estimated Time | Risk |
|-------|-------------|----------------|------|
| 1 | Research & Library Test | 30 min | Low |
| 2 | Sound Asset Prep | 1 hour | Low |
| 3 | Sound Manager Core | 2 hours | Medium |
| 4 | First Sounds (UI/Story) | 2 hours | Low |
| 5 | Combat Sounds | 3 hours | Medium |
| 6 | Polish & Settings | 2 hours | Low |

**Total**: ~10 hours of work spread over 3-4 sessions

---

## 🛠️ Technical Architecture

### Sound Manager Design

```python
class SoundManager:
    """Centralized sound playback."""

    def __init__(self):
        self.muted = False
        self.volume = 0.5
        self.active_processes = []  # Popen handles
        self.sound_cache = {}  # Loaded sounds (future)

    def play(self, name: str, volume: float | None = None) -> None:
        """Play sound by name (non-blocking)."""
        if self.muted:
            return
        # ... implementation

    def stop_all(self) -> None:
        """Stop all active sounds."""
        # ... implementation
```

### Sound Categories & Files

```
data/sounds/
├── README.md                  # Sound design doc
├── ui/
│   ├── menu_select.wav
│   ├── menu_confirm.wav
│   ├── menu_cancel.wav
│   └── error.wav
├── combat/
│   ├── attack_normal.wav
│   ├── attack_crit.wav
│   ├── skill_physical.wav
│   ├── skill_magic.wav
│   ├── skill_heal.wav
│   ├── combat_victory.wav
│   └── combat_defeat.wav
├── story/
│   ├── text_typing.wav
│   ├── dialogue_advance.wav
│   └── event_trigger.wav
├── movement/
│   ├── nav_step.wav
│   ├── jack_in.wav
│   └── jack_out.wav
└── items/
    ├── equip.wav
    ├── pickup.wav
    └── notification.wav
```

### Integration Pattern

In each game state, add hooks:
```python
# Before
def handle_action(self):
    do_something()

# After
def handle_action(self):
    sound.play("action_name")
    do_something()
```

---

## 🧪 Validation Tools Summary

| Tool | Purpose | Phase |
|------|---------|-------|
| `test_sound_libraries.py` | Find working library | 1 |
| `test_sound_manager.py` | Test sound manager | 3 |
| `test_story_sounds.py` | Test story integration | 4 |
| `test_combat_sounds.py` | Test combat integration | 5 |
| `test_full_audio.py` | Full game session | 6 |

Each tool will:
- Run independently: `uv run python scripts/test_XXX.py`
- Print clear pass/fail
- Log all audio events
- Report timing/metrics

---

## 🎵 Sound Generation Strategy

For placeholder sounds, use:
1. **System beeps** - Cross-platform, instant
2. **festival / espeak** - Text-to-speech for testing
3. **SoX (Sound eXchange)** - Generate tones with sine waves
4. **Audacity / online generators** - Custom sounds

Example SoX command for a "type" sound:
```bash
sox -n -r 44100 beep.wav synth 0.05 sine 800-400 vol 0.3
```

For final sounds:
- Find free cyberpunk sounds on freesound.org
- Or use generative audio (Python)
- License: CC0 / Public Domain preferred

---

## 📊 Success Metrics

Each phase should achieve:
- [ ] All validation tools pass
- [ ] No new test failures in existing 124 tests
- [ ] No performance regression (game still runs smoothly)
- [ ] No memory leaks (long sessions stable)
- [ ] Sounds are appropriate (atmospheric, not annoying)
- [ ] Sounds can be muted / volume controlled

---

## 🚀 Quick Start (First Session)

**Today**: Complete Phase 1 + 2 + 3

```bash
# Phase 1: Test libraries
cd Game/wet_run/prototype
uv run python scripts/test_sound_libraries.py

# Phase 2: Create directory
mkdir -p data/sounds/{ui,combat,story,movement,items}

# Phase 3: Implement SoundManager
# (write code, test with)
uv run python scripts/test_sound_manager.py
```

If Phase 1-3 work, move to Phase 4 (story/UI sounds) which has highest player visibility.

---

## 📊 Current Status (2026-06-18)

### Phase Completion
- [x] **Phase 1**: Library Evaluation — `afplay` (5.3ms latency) selected for macOS
- [x] **Phase 2**: Sound Assets — 27 placeholder WAVs auto-generated via wave module
- [x] **Phase 3**: SoundManager Core — `src/wet_run/audio/sound_manager.py` (267 lines)
- [x] **Phase 4**: UI/Story Sounds — hooks in 6 engine modules
- [x] **Phase 5**: Combat Sounds — 14 SkillEffect types mapped
- [x] **Phase 6**: UI/Nav Polish — nav_step, nav_block, jack_in wired

### Validation Results
- **mypy strict**: 0 errors (60 source files)
- **ruff check**: 0 issues
- **pytest**: 124/124 passing
- **sound_manager tests**: 7/7 passing
- **sound assets**: 27/27 generated in `data/sounds_test/`

### Sound Coverage Map
| Game Event | Sound | Hook Location |
|-----------|-------|---------------|
| Menu navigate | ui/menu_select | action_menu.py, npc_view.py, hub.py |
| Menu confirm | ui/menu_confirm | npc_view.py, action_menu.py |
| Menu cancel | ui/menu_cancel | action_menu.py |
| Cinematic text | story/text_typing | story_cinematic.py |
| Dialogue advance | story/dialogue_advance | npc_view.py |
| Event trigger | story/event_trigger | story_cinematic.py |
| Skill (physical) | combat/skill_physical | combat_view.py |
| Skill (magic) | combat/skill_magic | combat_view.py |
| Skill (heal) | combat/skill_heal | combat_view.py |
| Skill (buff) | combat/skill_buff | combat_view.py |
| Skill (debuff) | combat/skill_debuff | combat_view.py |
| Block | combat/block | combat_view.py |
| Stun | combat/stun | combat_view.py |
| Victory | combat/victory | combat_view.py |
| Defeat | combat/defeat | combat_view.py |
| Nav step | movement/nav_step | cyberspace_view.py |
| Nav blocked | movement/nav_block | cyberspace_view.py |
| Jack in | movement/jack_in | cyberspace_browser.py |

### Future Work (Post-Phase 6)
1. **Settings UI**: Volume slider, mute toggle (M key)
2. **Real audio assets**: Replace synthesized placeholders with Gibson-inspired cyberpunk tones
3. **Ambient music**: Cyberspace ambient (drone/synth)
4. **Voice acting**: NPC dialogue (The Finn, Dixie)
5. **3D audio positioning**: Directional sounds in cyberspace
6. **Pitch variation**: Random ±5% pitch for combat hits (no two sound identical)

---

## 🆕 Phase 1.5 — VFX 4종 사운드 큐

`combat/effects.py` 의 4 종 시네마틱 스포너는 단독 VFX 만 트리거하지만,
사운드 큐는 별도 hook 이 필요합니다 (`combat_view.py:on_jack_in` 등).

| VFX | 사운드 큐 (제안) | Hook 위치 |
|---|---|---|
| `spawn_jackin_glitch` | `movement/jack_in` (기존) + `combat/modulation_slow` | cyberspace → combat 진입 시 |
| `spawn_room_flash` | `combat/victory` (기존) | ICE 처치 후 |
| `spawn_data_acquired` | `ui/item_get` (신규) | DATA 픽업 후 |
| `spawn_jackout_whiteout` | `movement/jack_out` (신규) | JAC-OUT 시 |

Phase 1.5 스포너는 단일 위치 인자 `CombatEffects` 만 받기 때문에,
사운드 트리거는 `combat_view.py` 에서 VFX 호출 직후 직접 큐에 넣는
방식이 권장됩니다. Phase 5 의 `NovelDispatcher.dispatch()` 도 동일한
패턴 — `HookContext` 의 `app_state` 에 사운드 핸들 노출 시 동기화.

**관련 ADR**:
- `decisions/0060-dungeon-exploration-redesign.md` (Phase 1.5 VFX)
- `decisions/0061-novel-integration-architecture.md` (Phase 5 dispatcher)
