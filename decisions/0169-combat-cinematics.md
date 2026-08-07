# ADR-0169: Combat Cinematics (Per Boss Phase Intro)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P2 (Pillar 5 style, Pillar 1 climax)
**관련**: [ADR-0149 — Boss Phase 4 Finale](./0149-boss-phase4-finale.md), [ADR-0162 — Boss Phase 5 Last Stand](./0162-boss-phase-4.md), [ADR-0168 — Death Taunts](./0168-death-taunts.md), [ADR-0170 — Gibson Fluff Library](./0170-gibson-fluff-library.md)

## 컨텍스트 (Context)

Boss fights have intro cinematic sequences (built in ADR-0149, ADR-0162),
but each phase transition within a boss fight has only a basic screen
flash. Players don't get the same "wow" moment for each phase as they
do for the initial boss intro.

Track D.2 adds **per-boss-phase intro cinematics** — each phase
transition (1→2, 2→3, 3→4, 4→5 for bosses that have phases) gets a
distinctive intro sequence with:
- Phase-specific color tint
- Phase name callout (Korean)
- Phase-specific glyph animation
- CinematicSequence of 3-5 frames

## 결정 (Decision)

### Cinematic schema

```python
@dataclass(frozen=True, slots=True)
class PhaseCinematic:
    phase_number: int
    color: tuple[int, int, int]
    duration_ms: int
    frames: tuple[str, ...]
    name_ko: str
    name_en: str
```

### Implementation surface

**`combat/phase_cinematics.py`** (NEW):
- `get_phase_cinematic(boss_id, phase_number) -> PhaseCinematic`
- `phase_intro_sequence(boss_id, phase_number) -> CinematicSequence`
- `PHASE_CINEMATICS: dict[str, dict[int, PhaseCinematic]]` — per-boss, per-phase
- `CINEMATIC_TEMPLATES` — pre-built templates for speed

**`tests/unit/test_phase_cinematics.py`** (NEW):
- 8+ tests covering lookup, sequence generation, templates.

## Consequences (결과)

**Pillar 1 (The Run)**: Each boss phase feels like a new encounter.

**Pillar 5 (The Style)**: Cinematic frames use Gibson tone ("the construct shifts, voice metallic").

**Test additions**: ~8 tests.
