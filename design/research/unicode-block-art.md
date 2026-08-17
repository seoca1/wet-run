# Unicode Block Art Research — 2× Vertical Resolution for Graphic Novel Mode

**Date**: 2026-07-10
**Context**: Upgrade ASCII portraits from 10×14 cells to higher resolution using Unicode block characters
**Goal**: Double vertical resolution for character portraits in graphic novel mode

---

## 1. Unicode Block Characters for 2× Vertical Resolution

### 1.1 Core Block Characters

| Character | Unicode | Name | Use Case |
|-----------|---------|------|----------|
| `▀` | U+2580 | Upper Half Block | Top half of a cell |
| `▄` | U+2584 | Lower Half Block | Bottom half of a cell |
| `█` | U+2588 | Full Block | Solid fill |
| `▌` | U+258C | Left Half Block | Left half of a cell |
| `▐` | U+2590 | Right Half Block | Right half of a cell |
| `░` | U+2591 | Light Shade | 25% fill |
| `▒` | U+2592 | Medium Shade | 50% fill |
| `▓` | U+2593 | Dark Shade | 75% fill |

### 1.2 Additional Useful Blocks

| Character | Unicode | Name | Use Case |
|-----------|---------|------|----------|
| `▖` | U+2596 | Quadrant Lower Left | Quarter-cell precision |
| `▗` | U+2597 | Quadrant Lower Right | Quarter-cell precision |
| `▘` | U+2598 | Quadrant Upper Left | Quarter-cell precision |
| `▝` | U+2599 | Quadrant Upper Right | Quarter-cell precision |
| `▞` | U+259E | Quadrant Upper Right + Lower Left | Diagonal patterns |
| `▚` | U+259A | Quadrant Upper Left + Lower Right | Diagonal patterns |

### 1.3 How 2× Vertical Resolution Works

**Principle**: Each console cell can display TWO vertical pixels by using `▀` (upper) and `▄` (lower) with different foreground/background colors.

**Example — Single Cell Rendering**:
```
Cell (x, y):
  - Character: ▀ (upper half block)
  - Foreground color: (255, 0, 0)    # Red — upper pixel
  - Background color: (0, 0, 255)    # Blue — lower pixel
  
Result: Top half red, bottom half blue
```

**10×14 cell portrait → 10×28 pixel portrait**

---

## 2. python-tcod Compatibility

### 2.1 Console Rendering API

**tcod.console.Console** supports Unicode characters via:

```python
# Method 1: console.print() — string rendering
console.print(x=5, y=10, string="▀▄█", fg=(255, 255, 255))

# Method 2: console.ch — direct character array access
console.ch[y, x] = ord('▀')  # Set character by Unicode codepoint
console.fg[y, x] = (255, 0, 0)  # Set foreground color
console.bg[y, x] = (0, 0, 255)  # Set background color
```

**Verification**: Current codebase already uses Unicode block characters:
- `▌` (U+258C) in portraits: `case_decision`, `marly_smile`, `kumiko_sally`
- `▓` (U+2593) in portraits: `case_terminal`, `marly_data`, `armitage_suit`
- `░` (U+2591) in portraits: `case_hands`, `sally_neutral`
- `▒` (U+2592) in backgrounds: `bg_chat_room`

**Conclusion**: ✅ python-tcod fully supports Unicode block characters.

---

## 3. Current Portrait System Architecture

### 3.1 Portrait Manager (`portraits/manager.py`)

**Purpose**: Load and cache ASCII portraits from JSON

**Key Components**:
```python
class PortraitManager:
    def __init__(self, data_dir: Path | None = None):
        self._portraits: dict[str, dict[str, Any]] = {}
        if data_dir is not None:
            self._load(data_dir)
    
    def _load(self, data_dir: Path):
        path = data_dir / "portraits.json"
        # Load JSON, parse colors
    
    def get(self, entity_id: str) -> dict[str, Any]:
        # Returns {"ascii": "...", "color": (r, g, b), "name": "..."}
```

**Color Parsing**:
- Supports color names: `"red"`, `"green"`, `"cyan"`, etc.
- Supports RGB tuples: `[255, 0, 0]`
- Maps to `tuple[int, int, int]`

### 3.2 Portrait Data Format (`data/art/portraits/portraits.json`)

**Current Format** (10×14 ASCII):
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

**Key Observations**:
- `size`: `[width, height]` in cells
- `art`: Array of strings, one per row
- Already uses Unicode: `╭`, `╮`, `│`, `─`, `▎`, etc.
- No per-pixel color data — single color per portrait

### 3.3 Graphic Novel View (`engine/graphic_novel_view.py`)

**Portrait Rendering** (current):
```python
@dataclass(frozen=True, slots=True)
class Portrait:
    id: str
    title_en: str
    title_ko: str
    character: str
    width: int
    height: int
    art: tuple[str, ...]  # One string per row
```

**Rendering Flow**:
1. Load scene JSON → get `portrait_left` / `portrait_right` IDs
2. Load portrait art from `portraits.json`
3. Render each line of `art` array to console at (x, y + row)

**Current Limitation**: Single foreground color per portrait, no per-pixel color control.

---

## 4. Existing Unicode Block Usage in Codebase

### 4.1 Portraits

**Characters Used**:
- `▌` (U+258C) — Left half block: body/torso representation
- `▓` (U+2593) — Dark shade: terminals, screens, solid objects
- `░` (U+2591) — Light shade: transparency, mist, data streams
- `▒` (U+2592) — Medium shade: screens, interfaces

**Examples**:
```
case_decision:
   │ ▌ │   # Body torso (left half block)
   │ ▌ │

case_terminal:
  │▓▓▓▓ │  # Terminal screen (dark shade)
  │▓▓▓▓ │

case_hands:
   ░ ░      # Trembling hands (light shade)
   ░ ░
```

### 4.2 Backgrounds

**File**: `data/art/backgrounds/backgrounds.json`

**Usage**:
```
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  # Light shade for UI elements
│  ░  11th level, Chiba  11:42 PM ░░ │
│  │ ▓▓▓▓▓▓▓ │   ░▒▓ HEADSON ▓▒░ │TV ││  # Gradient: ░ → ▒ → ▓
```

**Observation**: Backgrounds already use shade characters for depth/texture.

---

## 5. Proposed Block Art Rendering Approach

### 5.1 Design Goals

1. **2× Vertical Resolution**: 10×14 cells → 10×28 pixels
2. **Per-Pixel Color Control**: Each half-cell can have different colors
3. **Backward Compatible**: Existing ASCII portraits still work
4. **Efficient**: Minimal memory overhead, fast rendering

### 5.2 Data Format — Block Art Portrait

**Option A: Pixel Array (10×28)**

```json
{
  "case_think_hires": {
    "id": "case_think_hires",
    "format": "block_art",
    "size": [10, 14],  // Cell dimensions
    "pixels": [
      // 28 rows × 10 columns = 280 pixels
      // Each pixel: [r, g, b] or color_index
      [[255, 255, 255], [255, 255, 255], ...],  // Row 0 (top half of cell 0)
      [[255, 255, 255], [255, 255, 255], ...],  // Row 1 (bottom half of cell 0)
      ...
    ]
  }
}
```

**Option B: Run-Length Encoded**

```json
{
  "case_think_hires": {
    "id": "case_think_hires",
    "format": "block_art_rle",
    "size": [10, 14],
    "palette": [
      [0, 0, 0],      // 0: black
      [255, 255, 255], // 1: white
      [0, 255, 0],    // 2: green
      [128, 128, 128] // 3: gray
    ],
    "rows": [
      "0:5,1:3,0:2",  // Row 0: 5 black, 3 white, 2 black
      "0:10",         // Row 1: 10 black
      ...
    ]
  }
}
```

**Option C: Hybrid — ASCII + Color Map**

```json
{
  "case_think_hires": {
    "id": "case_think_hires",
    "format": "block_art_hybrid",
    "size": [10, 14],
    "art": [
      "▀▀▀▀▀▀▀▀▀▀",  // Row 0: upper half blocks
      "▄▄▄▄▄▄▄▄▄▄",  // Row 1: lower half blocks
      ...
    ],
    "fg_colors": [
      [[255,255,255], [255,255,255], ...],  // Row 0 foreground
      [[0,0,0], [0,0,0], ...],              // Row 1 foreground
      ...
    ],
    "bg_colors": [
      [[0,0,0], [0,0,0], ...],  // Row 0 background
      [[255,255,255], [255,255,255], ...],  // Row 1 background
      ...
    ]
  }
}
```

### 5.3 Rendering Algorithm

**Pseudo-code** (Option A: Pixel Array):

```python
def render_block_art_portrait(console, x, y, portrait):
    """Render a 10×28 pixel portrait as 10×14 cells with block characters."""
    width, height = portrait["size"]  # 10, 14
    pixels = portrait["pixels"]  # 28 rows × 10 cols
    
    for cell_y in range(height):  # 0..13
        for cell_x in range(width):  # 0..9
            # Get two vertical pixels for this cell
            upper_pixel = pixels[cell_y * 2][cell_x]      # Even row
            lower_pixel = pixels[cell_y * 2 + 1][cell_x]  # Odd row
            
            # Determine character and colors
            if upper_pixel == lower_pixel:
                # Same color → use full block or space
                char = '█' if upper_pixel != [0,0,0] else ' '
                fg = tuple(upper_pixel)
                bg = (0, 0, 0)
            else:
                # Different colors → use half block
                char = '▀'  # Upper half block
                fg = tuple(upper_pixel)   # Foreground = upper pixel
                bg = tuple(lower_pixel)   # Background = lower pixel
            
            # Render to console
            console.ch[y + cell_y, x + cell_x] = ord(char)
            console.fg[y + cell_y, x + cell_x] = fg
            console.bg[y + cell_y, x + cell_x] = bg
```

**Optimization**: Pre-compute character/color arrays during load, cache in `PortraitManager`.

### 5.4 Backward Compatibility

**Strategy**: Detect format by JSON structure

```python
def load_portrait(data: dict) -> Portrait:
    if "format" in data and data["format"] == "block_art":
        return load_block_art_portrait(data)
    else:
        return load_ascii_portrait(data)  # Existing format
```

**Migration Path**:
1. Keep existing ASCII portraits for now
2. Add new block art portraits with `_hires` suffix
3. Graphic novel view checks for `_hires` variant first, falls back to ASCII

---

## 6. Implementation Roadmap

### Phase 1: Proof of Concept (1-2 days)
- [ ] Create single test portrait (10×28 pixels) in JSON
- [ ] Implement `render_block_art_portrait()` function
- [ ] Verify rendering in test script
- [ ] Measure performance (render time, memory)

### Phase 2: Tooling (2-3 days)
- [ ] Create pixel art editor script (CLI or simple GUI)
- [ ] Implement palette system (16-color or 256-color)
- [ ] Add export to JSON format
- [ ] Document art creation workflow

### Phase 3: Content Creation (3-5 days)
- [ ] Convert 3 existing portraits to block art (Case, Marly, Kumiko)
- [ ] Create 3 new high-res portraits
- [ ] Test in graphic novel mode
- [ ] Gather feedback on visual quality

### Phase 4: Integration (2-3 days)
- [ ] Update `PortraitManager` to support both formats
- [ ] Add format detection and fallback logic
- [ ] Update graphic novel view rendering
- [ ] Add unit tests for block art rendering
- [ ] Update documentation

### Phase 5: Full Migration (5-7 days)
- [ ] Convert all 15 existing portraits to block art
- [ ] Create additional portraits for new scenes
- [ ] Performance optimization (caching, pre-rendering)
- [ ] Visual QA pass
- [ ] Update design docs and ADRs

**Total Estimate**: 13-20 days

---

## 7. Technical Considerations

### 7.1 Performance

**Rendering Cost**:
- Current: 14 `console.print()` calls per portrait (one per row)
- Block art: 140 cell updates (10×14) via `console.ch/fg/bg` arrays
- **Impact**: Negligible — tcod rendering is fast, 140 cells is trivial

**Memory Cost**:
- Current: ~200 bytes per portrait (14 strings × ~15 chars)
- Block art (Option A): ~8.4 KB per portrait (280 pixels × 3 bytes RGB)
- Block art (Option B, RLE): ~2-4 KB per portrait (compressed)
- **Impact**: Low — 15 portraits × 8 KB = 120 KB total

### 7.2 Font Compatibility

**Requirement**: Monospace font with full Unicode block character support

**Current Font**: `data/fonts/` (libtcod default)
- ✅ Supports `▀`, `▄`, `█`, `▌`, `▐`, `░`, `▒`, `▓`
- ✅ Already verified in existing portraits

**Fallback**: If font lacks block characters, render as ASCII (backward compatibility).

### 7.3 Color Depth

**Options**:
1. **16-color palette**: Classic terminal colors (fast, retro aesthetic)
2. **256-color palette**: Extended ANSI colors (good balance)
3. **True color (24-bit RGB)**: Full color range (best quality)

**Recommendation**: Start with **256-color palette** for balance between quality and file size.

**Palette Design**:
- 16 base colors (black, white, primary/secondary colors)
- 16 skin tones (for character faces)
- 16 metal/tech colors (for cyberware, terminals)
- 16 neon colors (for cyberpunk aesthetic)
- 192 gradient colors (for smooth shading)

### 7.4 Art Creation Workflow

**Tools Needed**:
1. **Pixel Editor**: CLI tool to paint 10×28 pixel portraits
   - Arrow keys to move cursor
   - Number keys to select palette color
   - Space to paint, Backspace to erase
   - S to save, Q to quit
2. **Converter**: Script to convert images to block art
   - Input: PNG/JPG (20×56 pixels, scaled 2×)
   - Output: JSON block art portrait
   - Dithering for color reduction
3. **Previewer**: Script to preview block art in terminal
   - Render portrait at actual size
   - Compare with ASCII version side-by-side

---

## 8. Alternative Approaches (Considered and Rejected)

### 8.1 Braille Patterns (U+2800–U+28FF)

**Idea**: Use Braille characters for 2×4 pixel resolution per cell (8 dots)

**Example**: `⠿` (U+283F) = all 8 dots filled

**Pros**:
- Even higher resolution (10×14 cells → 20×56 pixels)
- Single character per cell (simpler rendering)

**Cons**:
- ❌ Only binary (on/off), no color per dot
- ❌ Harder to read/edit by hand
- ❌ Less aesthetic for portraits (too dense)

**Decision**: Rejected — block characters provide better color control and readability.

### 8.2 Sextant Characters (U+1FB00–U+1FB3B)

**Idea**: Use sextant characters for 2×3 pixel resolution per cell (6 dots)

**Example**: `🬀` (U+1FB00) = upper-left dot

**Pros**:
- Higher resolution than half-blocks
- More granular than Braille

**Cons**:
- ❌ Limited font support (Unicode 13.0+, 2020)
- ❌ May not render correctly in all terminals
- ❌ Still binary (on/off), no per-dot color

**Decision**: Rejected — too new, limited compatibility.

### 8.3 Custom Bitmap Font

**Idea**: Create custom font with 2× vertical resolution glyphs

**Pros**:
- Full control over rendering
- Could support arbitrary resolutions

**Cons**:
- ❌ Requires font file distribution
- ❌ Breaks monospace alignment
- ❌ Not compatible with standard terminals
- ❌ High implementation cost

**Decision**: Rejected — violates Pure ASCII aesthetic (ADR-0002).

---

## 9. Open Questions

1. **Color Palette Size**: 16, 256, or true color?
   - **Recommendation**: Start with 256-color, measure file size impact
2. **Art Creation Tool**: CLI or GUI?
   - **Recommendation**: CLI first (faster to implement), GUI later if needed
3. **Dithering**: Use dithering for color reduction?
   - **Recommendation**: Yes, Floyd-Steinberg dithering for smooth gradients
4. **Animation**: Support animated portraits (frame sequences)?
   - **Recommendation**: Phase 6 (future work), not in initial implementation
5. **Compression**: Use RLE or other compression?
   - **Recommendation**: Yes, RLE for rows with repeated colors (Option B)

---

## 10. References

### 10.1 Unicode Block Characters
- [Unicode Block Elements](https://en.wikipedia.org/wiki/Block_Elements) (U+2580–U+259F)
- [Unicode Box Drawing](https://en.wikipedia.org/wiki/Box-drawing_character) (U+2500–U+257F)
- [Unicode Geometric Shapes](https://en.wikipedia.org/wiki/Geometric_Shapes) (U+25A0–U+25FF)

### 10.2 python-tcod Documentation
- [tcod.console.Console](https://python-tcod.readthedocs.io/en/latest/tcod/console.html)
- [Console Arrays](https://python-tcod.readthedocs.io/en/latest/tcod/console.html#console-arrays)

### 10.3 Existing Codebase
- `prototype/src/wet_run/portraits/manager.py` — Portrait loading
- `prototype/src/wet_run/engine/graphic_novel_view.py` — Rendering
- `prototype/data/art/portraits/portraits.json` — Current ASCII portraits
- `decisions/0011-ascii-portraits.md` — ADR for portrait system

### 10.4 Related Decisions
- ADR-0002: Pure ASCII rendering style
- ADR-0011: ASCII portraits (cyberspace-only)
- ADR-0032: Graphic novel mode

---

## 11. Conclusion

**Unicode block characters are fully suitable for 2× vertical resolution portraits in python-tcod.**

**Key Findings**:
1. ✅ `▀` (upper half) and `▄` (lower half) provide 2× vertical resolution
2. ✅ python-tcod supports Unicode block characters (verified in existing code)
3. ✅ Current portrait system can be extended with minimal changes
4. ✅ Backward compatibility is achievable via format detection

**Recommended Approach**:
- **Data Format**: Option B (RLE with palette) for balance of quality and file size
- **Rendering**: Direct `console.ch/fg/bg` array manipulation for performance
- **Tooling**: CLI pixel editor + image converter
- **Migration**: Gradual (keep ASCII, add block art variants)

**Next Steps**:
1. Create proof-of-concept with single test portrait
2. Implement rendering function and verify visual quality
3. Build pixel editor tool for art creation
4. Convert 3 existing portraits and gather feedback
5. Proceed with full implementation if results are satisfactory

---

**Document Status**: Research Complete — Ready for Implementation Planning
**Author**: AI Agent (Sisyphus-Junior)
**Review**: Pending user approval
