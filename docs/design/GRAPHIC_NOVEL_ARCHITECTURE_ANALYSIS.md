# Graphic Novel System — Architecture Analysis

**Date**: 2026-07-10  
**Analyst**: AI Agent (Sisyphus-Junior)  
**Purpose**: Comprehensive review of the graphic novel mode system architecture, rendering approach, data structures, and fundamental limitations.

---

## Executive Summary

The graphic novel system is a **novel-style book layout renderer** built on ASCII art, with:
- ✅ **Sound architecture**: Clean separation (view/audio/save), well-tested (100+ tests)
- ✅ **Rich content**: 81 scenes across 9 characters, 18 portraits, 13 backgrounds
- ⚠️ **ASCII limitations**: Hard to read, no visual hierarchy, limited artistic expression
- ⚠️ **Novel-first design**: Optimized for prose reading, not graphic storytelling

**Recommendation**: The ASCII approach is **viable for text-heavy visual novels** but **fundamentally limited for graphic storytelling**. Consider hybrid or replacement approaches if visual impact is a priority.

---

## 1. System Architecture

### 1.1 Module Structure

| Module | Lines | Purpose | Status |
|--------|-------|---------|--------|
| `graphic_novel_view.py` | 1,448 | Core rendering (scenes, dialogue, chapter cards, menus) | ✅ Stable |
| `graphic_novel_audio.py` | 144 | Sound cue mapping (scene → SoundManager) | ✅ Stable |
| `graphic_novel_save.py` | 556 | Save/load progress (3 slots, versioned) | ✅ Stable |
| **Total** | **2,148** | | |

**Design Pattern**: Clean separation of concerns
- **View**: Rendering logic only (no state mutation)
- **Audio**: Declarative sound mapping (no playback logic)
- **Save**: Versioned persistence (migration chain for forward-compat)

### 1.2 Data Architecture

```
prototype/data/
├── scenes/              # 81 JSON files (9 characters × ~9 scenes each)
│   ├── case/           # Novice (Case) — 4 scenes
│   ├── sil/            # Veteran (Sil) — 4 scenes
│   ├── kas/            # Heretic (Kas) — 4 scenes
│   ├── suit/           # Corporate fixer (3rd person)
│   ├── wigan/          # Vodou construct
│   ├── angie/          # Loa receiver
│   ├── sally/          # Market operator
│   ├── 3jane/          # T-A family heir
│   └── neuromancer/    # Merged AI
├── art/
│   ├── portraits/portraits.json    # 18 portraits (10×14 ASCII)
│   └── backgrounds/backgrounds.json # 13 backgrounds (40×16 ASCII)
└── saves/
    └── gn_progress_slot_{1,2,3}.json  # 3 save slots
```

**Scene JSON Structure**:
```json
{
  "id": "scene_case_intro",
  "character": "novice",
  "order": 1,
  "ending": "A",
  "title_en": "CHATTO'S 24/7",
  "title_ko": "챠토 24/7",
  "background_id": "bg_chat_room",
  "portrait_left": "art:case_think",
  "portrait_right": null,
  "dialogue": [
    {
      "speaker": "case",
      "speaker_ko": "케이",
      "portrait": "art:case_think",
      "text_en": "30 seconds. The Ono-Sendai electrodes...",
      "text_ko": "30초. Ono-Sendai 전극이 두피에서...",
      "duration_ms": 12000,
      "sound": "chiba_rain_loop"
    }
  ],
  "next_scene": "scene_case_jackin"
}
```

**Key Observations**:
- ✅ **Extensible**: Easy to add new scenes/characters
- ✅ **Localized**: EN/KO dual-language support
- ✅ **Versioned**: `ending` field supports A/B/C variants (ADR-0048, 0049)
- ⚠️ **Art embedded in JSON**: Portraits/backgrounds are 469+378 lines of JSON (not separate image files)

---

## 2. Rendering Approach

### 2.1 Layout: Novel-Style Book Page

The system renders a **book page layout**, not a traditional visual novel:

```
┌─────────────────────────────────────────────────────────┐
│ [1/12]  CHATTO'S 24/7  ·  CASE      [S] skip [P] pause │ ← Top bar
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ ← Background art
│  ░  11th level, Chiba  11:42 PM ░░                     │   (y=2..13, dimmed)
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  ┌─────────┐                                           │
│  │ HOSAKA  │   ░▒▓ HEADSON ▓▒░                         │
│  │ ▓▓▓▓▓▓▓ │                                           │
│  │ ▓▓▓▓▓▓▓ │   rainbow shards                          │
│  └────┬────┘                                           │
│                                                         │
│                ── Case ──                              │ ← Speaker heading
│                                                         │
│  30 seconds. The Ono-Sendai electrodes lift from my    │ ← Prose body
│  scalp in that slow way they have, like a hand         │   (y=16..HEIGHT-4)
│  releasing a fist, and my fingers keep typing. Hands   │   ~30 lines of text
│  that hit a screen. The fingertips tremble. Slumped    │   Cream color (232,230,220)
│  in the chair, I stare at the console and try to       │   Word-wrapped, paginated
│  remember what I was doing.                            │
│                                                         │
│  Chiba. Eleventh level. The room smells of old         │
│  circuits and the synthetic melon flavor they sell in  │
│  vending machines on every floor of the Freeside       │
│  arcology. The Cherrimatti on the table is wet — rain, │
│  no, the air conditioning. The Headson Hotel TV is     │
│  showing a thirty-second loop of wherever I just was.  │
│                                                         │
│                                                         │
│                      PAGE 1/2                          │ ← Page counter
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ ← Progress bar
│  [Space] next  [P] pause  [S] skip  [ESC] menu         │
└─────────────────────────────────────────────────────────┘
```

**Design Philosophy**: "Open book page" (ADR-0047)
- Background art is **atmospheric** (dimmed, upper band only)
- Prose is **full-width** (left/right margins, ~30 lines)
- Portrait is **small corner inset** (10×14, dimmed backdrop)
- Typing effect is **per-character** (30ms/char)
- Pagination is **automatic** (follows typing cursor)

### 2.2 ASCII Art Conventions

**Portraits** (10×14 cells):
```
  ╭─────╮  
  │ ◉   │  
  │  ‿  │  
  │ ─── │  
  ╰──┬──╯  
     │     
   ┌─┴─┐   
   │   │   
   │ ▎ │   
   │ ▎ │   
   │ ▎ │   
   │ ▎ │   
   ╰───╯   
  [chiba]  
```
- **Box-drawing characters**: `╭╮╰╯─│┌┐└┘┬┴`
- **Shading**: `░▒▓█`
- **Symbols**: `◉◎○●▎▌▐`
- **Size**: 10 columns × 14 rows (fixed)

**Backgrounds** (40×16 cells):
```
┌──────────────────────────────────────┐
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  ░  11th level, Chiba  11:42 PM ░░ │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  ┌─────────┐                  ┌────┐│
│  │ HOSAKA  │   ░▒▓ HEADSON ▓▒░ │TV ││
│  │ ▓▓▓▓▓▓▓ │                  │░░ ││
│  │ ▓▓▓▓▓▓▓ │   rainbow shards  │░░ ││
│  │ ▓▓▓▓▓▓▓ │                  └────┘│
│  └────┬────┘   tangled cables       │
│       │║║║║║    ░░░░░░░░░░░░░░░░░░  │
│    [deck]                             │
│       │     rain on window  ░▒▓▒░    │
│  ┌─────────┐                          │
│  │  ▒░ CHATTO'S 24/7 ICE-FREE ░▒  │
└──┴──────────────────────────────────┴─┘
```
- **Size**: 40 columns × 16 rows (fixed)
- **Style**: Cyberpunk ASCII (neon signs, terminals, rain)
- **Technique**: Box-drawing + shading + labels

### 2.3 Graphic Effects

**Implemented**:
1. **Typing effect** (30ms/char) — `dialogue_typed_chars()`
2. **Chapter title cards** (ADR-0042) — Roman numerals, fade-in (1.5s)
3. **Blank transitions** (ADR-0042) — Fade-out to black (800ms)
4. **Progress bar** — Scene counter (1/12) + percentage
5. **Cream prose color** (ADR-0047) — `(232, 230, 220)` for readability
6. **Dimmed portrait backdrop** — `░` shading behind portrait

**NOT Implemented**:
- ❌ Particle effects
- ❌ Glitch/distortion
- ❌ Layered compositing
- ❌ Camera movement
- ❌ Dynamic lighting
- ❌ Sprite animation

**Fade Implementation** (Chapter Cards):
```python
def _apply_card_fade(console, width, card_y_start, fade: float):
    """Substitute ornament glyphs with dimmer characters when fading in."""
    if fade >= 1.0:
        return
    dim_level = int(fade * 100)
    for y in range(card_y_start, card_y_start + 10):
        line = "".join(chr(int(console.ch[x, y])) for x in range(width))
        if dim_level < 33:
            # Heavy fade: ═ → ▒, ─ → ░, · → space
            line = line.replace("═", "▒").replace("─", "░").replace("·", " ")
        elif dim_level < 66:
            # Mid fade: ═ → ▓, ─ → ▒
            line = line.replace("═", "▓").replace("─", "▒")
        for x, ch in enumerate(line):
            console.print(x, y, ch)
```
- **Technique**: Character substitution (heavy → light shading)
- **Limitation**: Only 3 fade levels (0-33%, 33-66%, 66-100%)
- **No color interpolation**: ASCII characters only

---

## 3. Current Capabilities

### 3.1 Content Scale

| Asset Type | Count | Total Lines | Format |
|------------|-------|-------------|--------|
| Scenes | 81 | ~3,240 | JSON (dialogue + metadata) |
| Portraits | 18 | 469 | JSON (ASCII art arrays) |
| Backgrounds | 13 | 378 | JSON (ASCII art arrays) |
| Characters | 9 | — | novice/veteran/heretic/suit/wigan/angie/sally/3jane/neuromancer |
| Endings | 3 per char | — | A/B/C variants (ADR-0048, 0049) |

**Scene Distribution**:
- **Core trio** (Case/Sil/Kas): 4 scenes each = 12 scenes
- **Extended cast** (Suit/Wigan/Angie/Sally/3Jane/Neuromancer): ~69 scenes
- **Total**: 81 scenes

### 3.2 Features

**Playback**:
- ✅ Auto-advance (duration_ms per dialogue)
- ✅ Manual advance (Space/Enter)
- ✅ Skip scene (S key)
- ✅ Pause/resume (P key)
- ✅ Exit to menu (ESC)

**Modes**:
- ✅ Prologue (all 9 characters, shuffled)
- ✅ Single character (4 scenes each)
- ✅ Ending variants (A/B/C per character)

**Save System** (ADR-0044, 0051):
- ✅ 3 save slots
- ✅ Resume from last position (scene/dialogue/typing cursor)
- ✅ Versioned format (1.2.0, migration chain)
- ✅ Atomic writes (temp file + rename)

**Audio** (ADR-0043):
- ✅ Scene-level sound cues (46 WAV files)
- ✅ Theme/ambient loops (chiba_rain, matrix_rain, loa_drum)
- ✅ SFX (jack_in_zap, data_extract, black_ice_roar)

**Localization**:
- ✅ EN/KO dual-language (all scenes, UI)
- ✅ Speaker names localized
- ✅ Title cards localized

### 3.3 Test Coverage

| Test Suite | Tests | Coverage |
|------------|-------|----------|
| `test_graphic_novel_view.py` | 40 | Scene rendering, pagination, chapter cards |
| `test_graphic_novel_audio.py` | 16 | Sound cue mapping |
| `test_graphic_novel_save.py` | 16 | Save/load, versioning, migration |
| `test_graphic_novel_endings.py` | 12 | Ending A/B/C variants |
| `test_graphic_novel_content_quality.py` | 8 | Scene data validation |
| `test_graphic_novel_ending_menu.py` | 6 | Ending selection UI |
| **Total** | **~100** | **Comprehensive** |

**Quality Gates**:
- ✅ pytest: 2,385 passed (100+ GN-specific)
- ✅ ruff check: All checks passed
- ✅ mypy strict: No issues
- ✅ Manual QA: `scripts/graphic_novel.py` demo

---

## 4. Fundamental Limitations

### 4.1 ASCII Art Constraints

**Visual Fidelity**:
- ❌ **Low resolution**: 10×14 portraits, 40×16 backgrounds (vs. 1920×1080 images)
- ❌ **Monochrome-ish**: Only 3-4 shading levels (`░▒▓█`)
- ❌ **Hard to read**: Box-drawing characters are ambiguous at small sizes
- ❌ **No anti-aliasing**: Jagged edges, no smooth curves
- ❌ **Limited palette**: tcod supports RGB, but ASCII art is mostly grayscale

**Artistic Expression**:
- ❌ **No facial expressions**: Portraits are static symbols (◉ for eyes, ‿ for mouth)
- ❌ **No body language**: 10×14 is too small for gestures
- ❌ **No environmental detail**: Backgrounds are abstract (labels + shading)
- ❌ **No depth**: No layering, parallax, or perspective

**Example**: Case portrait (10×14)
```
  ╭─────╮     ← Head (box)
  │ ◉   │     ← Eyes (circles)
  │  ‿  │     ← Mouth (arc)
  │ ─── │     ← Neck (line)
  ╰──┬──╯     ← Shoulders (box)
     │        ← Torso (line)
   ┌─┴─┐      ← Body (box)
   │ ▎ │      ← Arms (bars)
   ╰───╯      ← Legs (box)
  [chiba]     ← Label
```
- **Readable?** Yes, as a **symbol** (like an icon)
- **Expressive?** No — cannot convey emotion, age, or personality
- **Scalable?** No — 10×14 is the minimum; smaller is illegible

### 4.2 Rendering Limitations

**Performance**:
- ✅ **Fast**: ASCII rendering is O(width × height) per frame (~80×50 = 4,000 cells)
- ✅ **No GPU**: tcod uses CPU-only rendering (libtcod)

**Effects**:
- ❌ **No shaders**: Cannot do blur, glow, distortion, chromatic aberration
- ❌ **No particles**: Cannot do rain, snow, sparks, smoke
- ❌ **No animation**: Portraits/backgrounds are static (no sprite sheets)
- ❌ **Limited transitions**: Only character substitution (═ → ▓ → ▒ → ░)

**Compositing**:
- ❌ **No layers**: Background + portrait + dialogue are drawn sequentially (no alpha blending)
- ❌ **No masking**: Portrait backdrop is a simple `░` fill (no soft edges)
- ❌ **No depth of field**: Everything is in focus

### 4.3 Content Creation Bottleneck

**Art Pipeline**:
1. **Manual ASCII art** — Each portrait/background is hand-drawn in a text editor
2. **JSON embedding** — Art is stored as JSON arrays (469+378 lines)
3. **No tooling** — No ASCII art editor, no preview, no version control for art

**Example**: Creating a new portrait
```json
{
  "case_think": {
    "id": "case_think",
    "title_en": "Case (thinking)",
    "title_ko": "케이 (사색)",
    "character": "case",
    "size": [10, 14],
    "art": [
      "  ╭─────╮  ",
      "  │ ◉   │  ",
      "  │  ‿  │  ",
      "  │ ─── │  ",
      "  ╰──┬──╯  ",
      "     │     ",
      "   ┌─┴─┐   ",
      "   │   │   ",
      "   │ ▎ │   ",
      "   │ ▎ │   ",
      "   │ ▎ │   ",
      "   │ ▎ │   ",
      "   ╰───╯   ",
      "  [chiba]  "
    ]
  }
}
```
- **Time**: ~30 minutes per portrait (trial and error)
- **Skill**: Requires ASCII art expertise
- **Iteration**: Hard to preview (must run game to see result)

**Scalability**:
- ❌ **Slow**: 18 portraits × 30 min = 9 hours of art work
- ❌ **Error-prone**: JSON syntax errors, alignment issues
- ❌ **Hard to maintain**: Changing a portrait requires editing JSON by hand

### 4.4 Novel-First Design Trade-offs

**Optimized For**:
- ✅ **Long prose** — 30 lines of text per page, word-wrapped
- ✅ **Reading flow** — Typing effect, pagination, auto-advance
- ✅ **Book aesthetics** — Cream color, margins, chapter cards

**NOT Optimized For**:
- ❌ **Visual storytelling** — Art is secondary (dimmed, small)
- ❌ **Cinematic impact** — No camera, no dramatic framing
- ❌ **Character focus** — Portraits are corner insets (not center stage)

**Comparison**:

| Feature | Traditional VN | Wet Run GN |
|---------|----------------|---------------------|
| Art size | 1920×1080 (full screen) | 10×14 (corner inset) |
| Art style | Anime/realistic | ASCII symbols |
| Text layout | Bottom box (3-5 lines) | Full-width prose (30 lines) |
| Focus | Character art | Prose text |
| Transitions | Fade, slide, dissolve | Character substitution |
| Effects | Particles, shaders | None |

**Verdict**: This is a **text-first visual novel** (like a kinetic novel), not a **graphic-first visual novel** (like Steins;Gate or Doki Doki Literature Club).

---

## 5. Architectural Strengths

### 5.1 Clean Separation

**View** (`graphic_novel_view.py`):
- ✅ Pure rendering functions (no state mutation)
- ✅ Dataclasses for all data (`SceneData`, `DialogueLine`, `Portrait`, `Background`)
- ✅ Frozen, slotted dataclasses (immutable, memory-efficient)
- ✅ Type hints + docstrings (100% coverage)

**Audio** (`graphic_novel_audio.py`):
- ✅ Declarative mapping (scene sound → SoundManager key)
- ✅ No playback logic (delegates to `SoundManager`)
- ✅ Play-once cache (avoids sound spam)

**Save** (`graphic_novel_save.py`):
- ✅ Versioned format (1.2.0, migration chain)
- ✅ Atomic writes (temp file + rename)
- ✅ 3 save slots (ADR-0051)
- ✅ Forward-compatible (unknown `ending` values default to "A")

### 5.2 Extensibility

**Adding a new character**:
1. Create `data/scenes/{character}/` directory
2. Add 4-9 scene JSON files
3. Add portraits to `data/art/portraits/portraits.json`
4. Add backgrounds to `data/art/backgrounds/backgrounds.json`
5. Update `list_scenes_for_character()` mapping
6. Update `_character_label()` for chapter cards
7. Update `get_gn_menu_options()` for menu

**Effort**: ~2-3 hours (mostly art creation)

**Adding a new ending**:
1. Add scenes with `"ending": "D"` field
2. Update `available_endings()` to return `["A", "B", "C", "D"]`
3. Update `_ENDING_DESCRIPTIONS` dict
4. Bump save version (1.2.0 → 1.3.0) + add migration

**Effort**: ~1 hour (mostly scene writing)

### 5.3 Testability

**Unit tests** (100+):
- ✅ Scene loading (JSON parsing, validation)
- ✅ Rendering (chapter cards, pagination, typing)
- ✅ Save/load (versioning, migration, corruption)
- ✅ Audio (sound cue mapping)
- ✅ Endings (A/B/C variants)

**Integration tests** (scripts):
- ✅ `scripts/graphic_novel.py` — Full playback demo
- ✅ `scripts/demo_all.py` — Game + GN integration
- ✅ `scripts/visual_demo.py` — 8-system visual QA

**Manual QA**:
- ✅ Playable in-game (MENU → GRAPHIC NOVEL)
- ✅ Save/load works (3 slots)
- ✅ Audio works (46 sound cues)
- ✅ Localization works (EN/KO)

---

## 6. Viability Assessment

### 6.1 Is ASCII Viable Long-Term?

**For Text-Heavy Visual Novels**: ✅ **Yes**
- If the goal is **prose-first storytelling** (like a kinetic novel), ASCII is sufficient
- The current system is **well-architected** and **extensible**
- Adding new scenes/characters is **straightforward**

**For Graphic-Heavy Visual Novels**: ❌ **No**
- If the goal is **visual impact** (like Steins;Gate), ASCII is too limited
- No facial expressions, no body language, no environmental detail
- Art creation is **slow** and **error-prone**

**For Hybrid Approaches**: ⚠️ **Maybe**
- ASCII could work as a **stylistic choice** (retro/cyberpunk aesthetic)
- But it requires **exceptional ASCII art skills** (current art is functional, not exceptional)
- Consider **procedural ASCII art** (e.g., face generation from parameters) to scale

### 6.2 Fundamental Rendering Limitations

**Cannot Be Fixed Without Replacing ASCII**:
1. **Low resolution** — 10×14 portraits are too small for detail
2. **No anti-aliasing** — Jagged edges are inherent to ASCII
3. **Limited palette** — Only 3-4 shading levels
4. **No animation** — Static art only
5. **No effects** — No particles, shaders, or compositing

**Can Be Improved Within ASCII**:
1. **Better art** — Hire an ASCII artist (or use AI-generated ASCII art)
2. **Larger portraits** — 20×28 instead of 10×14 (but requires layout redesign)
3. **Color** — Use tcod RGB colors (but ASCII art is mostly grayscale)
4. **Transitions** — More sophisticated character substitution (but still limited)

### 6.3 Alternative Approaches

**Option 1: Hybrid ASCII + Raster Images**
- **Concept**: Keep ASCII for UI/text, use PNG/JPG for portraits/backgrounds
- **Pros**: Best of both worlds (ASCII aesthetic + visual fidelity)
- **Cons**: Breaks the "pure ASCII" aesthetic, requires image pipeline
- **Effort**: ~2-3 weeks (image loader, layout redesign, art creation)

**Option 2: Procedural ASCII Art**
- **Concept**: Generate ASCII portraits from parameters (age, emotion, clothing)
- **Pros**: Scalable (no manual art), dynamic (can change expressions)
- **Cons**: Requires AI/algorithm (complex), may look generic
- **Effort**: ~4-6 weeks (research, implementation, tuning)

**Option 3: Pre-Rendered Pixel Art**
- **Concept**: Replace ASCII with low-res pixel art (e.g., 64×64 portraits)
- **Pros**: More expressive than ASCII, retro aesthetic fits cyberpunk
- **Cons**: Requires pixel artist, breaks ASCII purity
- **Effort**: ~3-4 weeks (art pipeline, layout redesign, art creation)

**Option 4: Layered ASCII Effects**
- **Concept**: Keep ASCII, but add layered compositing (background + portrait + effects)
- **Pros**: Stays within ASCII, adds depth
- **Cons**: Still limited by ASCII resolution, complex to implement
- **Effort**: ~2-3 weeks (compositing engine, effect library)

**Option 5: Keep ASCII, Improve Art Quality**
- **Concept**: Hire an ASCII artist to create exceptional art
- **Pros**: Minimal code changes, stays true to ASCII aesthetic
- **Cons**: Art is still limited by ASCII constraints, expensive
- **Effort**: ~1-2 weeks (art commission, integration)

---

## 7. Recommendations

### 7.1 Short-Term (Keep ASCII)

**If the goal is to ship quickly**:
1. ✅ **Keep the current system** — It works, it's tested, it's extensible
2. ✅ **Improve art quality** — Commission better ASCII art (or use AI tools)
3. ✅ **Add more scenes** — The system can handle 100+ scenes easily
4. ✅ **Polish transitions** — Add more sophisticated fade effects (within ASCII limits)

**Estimated effort**: 1-2 weeks (art + polish)

### 7.2 Medium-Term (Hybrid Approach)

**If the goal is to improve visual impact**:
1. ⚠️ **Add raster images** — Use PNG/JPG for portraits/backgrounds
2. ⚠️ **Keep ASCII for UI** — Menus, dialogue boxes, chapter cards stay ASCII
3. ⚠️ **Redesign layout** — Center portraits (not corner insets), reduce prose dominance
4. ⚠️ **Add effects** — Particles, shaders, transitions (requires GPU rendering)

**Estimated effort**: 3-4 weeks (image pipeline + layout redesign + art creation)

### 7.3 Long-Term (Replace ASCII)

**If the goal is to compete with commercial VNs**:
1. ❌ **Replace ASCII entirely** — Use pixel art or vector art
2. ❌ **Rebuild rendering engine** — Use a VN framework (Ren'Py, Unity, Godot)
3. ❌ **Hire artists** — Commission professional art (portraits, backgrounds, CGs)
4. ❌ **Add full VN features** — Choices, branching, save/load, gallery, etc.

**Estimated effort**: 3-6 months (full rewrite)

### 7.4 Recommended Path

**For Wet Run**:
- ✅ **Keep ASCII for now** — The system is solid, and ASCII fits the cyberpunk aesthetic
- ✅ **Improve art quality** — Commission better ASCII art (or use AI tools)
- ⚠️ **Consider hybrid approach later** — If visual impact becomes a priority

**Rationale**:
- The game is a **roguelike first**, not a visual novel
- ASCII fits the **retro cyberpunk** aesthetic (Neuromancer was written in 1984)
- The current system is **well-architected** and **extensible**
- Replacing ASCII would be a **major rewrite** (3-6 months)

---

## 8. Conclusion

### 8.1 Summary

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Architecture** | ✅ Excellent | Clean separation, well-tested, extensible |
| **Content Scale** | ✅ Good | 81 scenes, 18 portraits, 13 backgrounds |
| **Rendering Quality** | ⚠️ Adequate | ASCII is readable but not expressive |
| **Art Pipeline** | ❌ Slow | Manual JSON editing, no tooling |
| **Visual Impact** | ❌ Limited | Low resolution, no effects, no animation |
| **Long-Term Viability** | ⚠️ Depends | Good for text-first VNs, limited for graphic-first VNs |

### 8.2 Final Verdict

**The ASCII approach is viable for text-heavy visual novels, but fundamentally limited for graphic storytelling.**

**Strengths**:
- ✅ Clean, testable, extensible architecture
- ✅ Rich content (81 scenes, 9 characters, 3 endings per character)
- ✅ Fits the retro cyberpunk aesthetic
- ✅ Fast rendering (no GPU required)

**Weaknesses**:
- ❌ Low visual fidelity (10×14 portraits, 40×16 backgrounds)
- ❌ No facial expressions, body language, or environmental detail
- ❌ Slow art pipeline (manual JSON editing)
- ❌ Limited effects (no particles, shaders, or animation)

**Recommendation**:
- **Keep ASCII for now** — The system is solid and fits the game's aesthetic
- **Improve art quality** — Commission better ASCII art or use AI tools
- **Consider hybrid approach later** — If visual impact becomes a priority

---

## Appendix A: Key Files

| File | Purpose |
|------|---------|
| `src/wet_run/engine/graphic_novel_view.py` | Core rendering (1,448 lines) |
| `src/wet_run/engine/graphic_novel_audio.py` | Sound cue mapping (144 lines) |
| `src/wet_run/engine/graphic_novel_save.py` | Save/load (556 lines) |
| `data/scenes/{character}/*.json` | Scene data (81 files) |
| `data/art/portraits/portraits.json` | Portrait art (18 portraits, 469 lines) |
| `data/art/backgrounds/backgrounds.json` | Background art (13 backgrounds, 378 lines) |
| `tests/unit/test_graphic_novel_*.py` | Unit tests (100+ tests) |
| `scripts/graphic_novel.py` | Playback demo |
| `decisions/0032-graphic-novel-mode.md` | Original ADR |
| `decisions/0047-text-visibility-typed-messages.md` | Prose color ADR |
| `design/scenario/graphic-novel.md` | Design spec |

---

## Appendix B: ADR References

| ADR | Title | Impact |
|-----|-------|--------|
| ADR-0032 | Graphic Novel Mode | Core system design |
| ADR-0041 | Content Expansion | 4 scenes → 81 scenes |
| ADR-0042 | Chapter Title Cards | Roman numerals, fade-in |
| ADR-0043 | Sound Cue Integration | 46 WAV files |
| ADR-0044 | Graphic Novel Save | Save/load progress |
| ADR-0047 | Text Visibility | Cream prose color |
| ADR-0048 | Ending Menu + Save Migration | A/B endings |
| ADR-0049 | Ending C | A/B/C endings |
| ADR-0051 | GN Save Slots | 3 save slots |

---

**End of Analysis**
