# ADR-0183: Accessibility (Colorblind 3 Modes, Text Size, Input Remapping)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P2 (Pillar 1 inclusivity + Pillar 5 style)
**관련**: [ADR-0175 — Tutorial System](./0175-tutorial-system.md), [ADR-0176 — Achievement System](./0176-achievement-system.md), [ADR-0182 — Run Replay](./0182-run-replay.md)

## 컨텍스트 (Context)

Current game has no accessibility options. Players with colorblindness
cannot distinguish ICE/player colors. Track G.2 introduces **3
Accessibility Modes**:

- **Colorblind**: 3 modes (deuteranopia, protanopia, tritanopia)
- **Text Size**: Small / Medium / Large
- **Input Remapping**: Custom key bindings

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class AccessibilityConfig:
    colorblind_mode: str  # "none", "deuteranopia", "protanopia", "tritanopia"
    text_size: str  # "small", "medium", "large"
    input_remapping: dict[str, str] = field(default_factory=dict)
```

### Public API

```python
# combat/accessibility.py
def get_default_accessibility() -> AccessibilityConfig
def set_colorblind_mode(config: AccessibilityConfig, mode: str) -> AccessibilityConfig
def set_text_size(config: AccessibilityConfig, size: str) -> AccessibilityConfig
def remap_key(config: AccessibilityConfig, action: str, key: str) -> AccessibilityConfig
def get_color_palette(mode: str) -> dict[str, tuple[int, int, int]]
def get_text_size_factor(size: str) -> float
```

### Colorblind palettes

| Mode | Color shift |
|---|---|
| none | Original colors |
| deuteranopia | Red/green shift |
| protanopia | Red weakness |
| tritanopia | Blue/yellow shift |

## Consequences (결과)

**Pillar 1 (Run)**: Game is accessible to colorblind players.

**Pillar 5 (Style)**: Accessibility as artistic choice, not compromise.

**Tests**: 10+ tests covering config, colorblind palettes, text size, remapping.

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/accessibility.py:40-46` — `class AccessibilityConfig` dataclass with `colorblind_mode` (default "none"), `text_size` (default "medium"), `input_remapping` (default dict)
- `prototype/src/wet_run/combat/accessibility.py:48` — `get_default_accessibility()`
- `prototype/src/wet_run/combat/accessibility.py:53` — `set_colorblind_mode(config, mode)` with validation
- `prototype/src/wet_run/combat/accessibility.py:66` — `set_text_size(config, size)`
- `prototype/src/wet_run/combat/accessibility.py:77` — `remap_key(config, action, key)`
- `prototype/src/wet_run/combat/accessibility.py:88` — `get_color_palette(mode) -> dict[str, tuple[int, int, int]]` for 3 colorblind modes (deuteranopia/protanopia/tritanopia) per ADR §"Colorblind palettes"
- `prototype/src/wet_run/combat/accessibility.py:93-113` — `get_text_size_factor`, `is_colorblind_mode`, `is_text_size`, `get_colorblind_modes`, `get_text_sizes`
- `prototype/tests/unit/test_accessibility.py` — **21 tests** collected (ADR target: 10+)
- `prototype/tests/unit/test_accessibility_settings.py` — additional settings-integration coverage

**Notes**: All 3 accessibility modes (colorblind / text size / input remapping) implemented per ADR §"Decision" verbatim. Colorblind palette table includes all 4 entries (none / deuteranopia / protanopia / tritanopia). `COLORBLIND_MODES` constant defined in module.

**No further action on ADR-0183** — implementation closed, public API stable, tests passing.