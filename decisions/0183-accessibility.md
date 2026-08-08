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