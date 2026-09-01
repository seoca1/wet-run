# Unicode Block Art Research — Executive Summary

**Date**: 2026-07-10
**Status**: Research Complete — Ready for Implementation
**Full Report**: [`unicode-block-art.md`](./unicode-block-art.md)

---

## TL;DR

✅ **Unicode block characters are fully suitable for 2× vertical resolution portraits in python-tcod.**

**Current**: 10×14 cell ASCII portraits (140 characters)
**Proposed**: 10×28 pixel block art portraits (280 pixels, 2× vertical resolution)

---

## Key Findings

### 1. Unicode Block Characters ✅

| Character | Use | Result |
|-----------|-----|--------|
| `▀` (U+2580) | Upper half block | Top pixel in cell |
| `▄` (U+2584) | Lower half block | Bottom pixel in cell |
| `█` (U+2588) | Full block | Solid fill |
| `░`/`▒`/`▓` | Shades | Gradients/textures |

**How it works**: Each console cell displays TWO vertical pixels by using `▀` with different foreground (upper pixel) and background (lower pixel) colors.

### 2. python-tcod Compatibility ✅

**Already verified in codebase**:
- `▌` (left half) in portraits: `case_decision`, `marly_smile`, `kumiko_sally`
- `▓` (dark shade) in portraits: `case_terminal`, `marly_data`, `armitage_suit`
- `░` (light shade) in portraits: `case_hands`, `sally_neutral`
- `▒` (medium shade) in backgrounds: `bg_chat_room`

**Rendering API**:
```python
# Method 1: String rendering
console.print(x=5, y=10, string="▀▄█", fg=(255, 255, 255))

# Method 2: Direct array access (for block art)
console.ch[y, x] = ord('▀')
console.fg[y, x] = (255, 0, 0)   # Upper pixel color
console.bg[y, x] = (0, 0, 255)   # Lower pixel color
```

### 3. Current Portrait System ✅

**Architecture**:
- `PortraitManager` (`portraits/manager.py`) — Load/cache portraits from JSON
- `Portrait` dataclass — id, title, character, size, art array
- `data/art/portraits/portraits.json` — 15 ASCII portraits (10×14)
- `graphic_novel_view.py` — Renders portraits in scenes

**Current Format**:
```json
{
  "case_think": {
    "id": "case_think",
    "size": [10, 14],
    "art": [
      "  ╭─────╮  ",
      "  │ ◉   │  ",
      ...
    ]
  }
}
```

**Limitation**: Single foreground color per portrait, no per-pixel color control.

### 4. Proposed Rendering Approach ✅

**Data Format** (Option B — Recommended):
```json
{
  "case_think_hires": {
    "format": "block_art_rle",
    "size": [10, 14],
    "palette": [
      [0, 0, 0],      // 0: black
      [255, 255, 255], // 1: white
      [0, 255, 0],    // 2: green
      ...
    ],
    "rows": [
      "0:5,1:3,0:2",  // Row 0: 5 black, 3 white, 2 black
      "0:10",         // Row 1: 10 black
      ...
    ]
  }
}
```

**Rendering Algorithm**:
```python
for cell_y in range(height):
    for cell_x in range(width):
        upper_pixel = pixels[cell_y * 2][cell_x]
        lower_pixel = pixels[cell_y * 2 + 1][cell_x]
        
        if upper_pixel == lower_pixel:
            char = '█' if upper_pixel != [0,0,0] else ' '
            fg = tuple(upper_pixel)
            bg = (0, 0, 0)
        else:
            char = '▀'
            fg = tuple(upper_pixel)   # Upper pixel
            bg = tuple(lower_pixel)   # Lower pixel
        
        console.ch[y + cell_y, x + cell_x] = ord(char)
        console.fg[y + cell_y, x + cell_x] = fg
        console.bg[y + cell_y, x + cell_x] = bg
```

---

## Implementation Roadmap

| Phase | Duration | Tasks |
|-------|----------|-------|
| **1. Proof of Concept** | 1-2 days | Single test portrait, rendering function, performance test |
| **2. Tooling** | 2-3 days | Pixel editor (CLI), image converter, previewer |
| **3. Content Creation** | 3-5 days | Convert 3 existing + create 3 new portraits |
| **4. Integration** | 2-3 days | Update PortraitManager, add tests, documentation |
| **5. Full Migration** | 5-7 days | Convert all 15 portraits, optimization, visual QA |
| **Total** | **13-20 days** | |

---

## Technical Considerations

### Performance
- **Rendering**: 140 cell updates (10×14) — negligible cost
- **Memory**: ~2-4 KB per portrait (RLE) × 15 = 30-60 KB total
- **Impact**: Low — tcod rendering is fast, memory overhead minimal

### Color Depth
**Recommended**: 256-color palette
- 16 base colors (black, white, primaries)
- 16 skin tones (character faces)
- 16 metal/tech colors (cyberware, terminals)
- 16 neon colors (cyberpunk aesthetic)
- 192 gradient colors (smooth shading)

### Backward Compatibility
**Strategy**: Format detection
```python
def load_portrait(data: dict) -> Portrait:
    if "format" in data and data["format"] == "block_art":
        return load_block_art_portrait(data)
    else:
        return load_ascii_portrait(data)  # Existing format
```

**Migration Path**:
1. Keep existing ASCII portraits
2. Add new block art portraits with `_hires` suffix
3. Graphic novel view checks for `_hires` variant first, falls back to ASCII

---

## Alternatives Considered (and Rejected)

### Braille Patterns (U+2800–U+28FF)
- ❌ Only binary (on/off), no color per dot
- ❌ Too dense, less aesthetic for portraits

### Sextant Characters (U+1FB00–U+1FB3B)
- ❌ Limited font support (Unicode 13.0+, 2020)
- ❌ May not render correctly in all terminals

### Custom Bitmap Font
- ❌ Requires font file distribution
- ❌ Breaks monospace alignment
- ❌ Violates Pure ASCII aesthetic (ADR-0002)

---

## Next Steps

1. **User Approval**: Review research findings and approve implementation
2. **Phase 1**: Create proof-of-concept with single test portrait
3. **Verify Quality**: Render test portrait and assess visual improvement
4. **Build Tooling**: Implement pixel editor for art creation
5. **Pilot Conversion**: Convert 3 existing portraits (Case, Marly, Kumiko)
6. **Gather Feedback**: Test in graphic novel mode, iterate on approach
7. **Full Implementation**: Proceed with remaining phases if results are satisfactory

---

## References

- **Full Research**: [`unicode-block-art.md`](./unicode-block-art.md) (11KB, comprehensive analysis)
- **Current System**: `prototype/src/wet_run/portraits/manager.py`
- **Rendering**: `prototype/src/wet_run/engine/graphic_novel_view.py`
- **Data**: `prototype/data/art/portraits/portraits.json`
- **ADRs**: ADR-0002 (Pure ASCII), ADR-0011 (ASCII Portraits), ADR-0032 (Graphic Novel Mode)

---

**Conclusion**: Unicode block characters provide a clean, performant, and backward-compatible path to 2× vertical resolution portraits. The approach is technically sound, already partially in use, and ready for implementation.
