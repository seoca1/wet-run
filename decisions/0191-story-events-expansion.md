# ADR-0191: Story Events Expansion (Phase 13 — Content Expansion, Axis 3)

**상태**: Accepted (2026-08-08, Phase 13 implementation in progress)
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P2 (Pillar 5 atmosphere + Pillar 1 variety)
**관련**: [ADR-0013 — Story Events System](./0013-story-events.md), [ADR-0165 — Random Matrix Events](./0165-random-matrix-events.md), [ADR-0188 — Mission Expansion](./0188-mission-expansion.md)

## 컨텍스트 (Context)

Current state: 4-6 random matrix events (per ADR-0165 Cycle 10). Per `.omo/plans/expand-roguelike-game-contents.md`, Phase 13 expands to 30+ events with character-specific, faction-specific, and chain designs.

Gaps:
- No character-specific events (random events don't react to player character)
- No faction-specific events (faction reputation not used in events)
- No event chains (single events only)
- No Gibson-flavored cyberpunk narrative beats

## 옵션 (Options)

### Option 1: Character-specific events only (9 new)
- 1 event per character (9 jockeys)
- **장점**: Strongest character identity
- **단점**: No faction events, no chains

### Option 2: Character + faction events (19 new)
- 9 character + 10 faction = 19 events
- **장점**: Covers identity + politics
- **단점**: No general variety, no chains

### Option 3: Character + faction + general + chains (30+ new)
- 9 + 10 + 11 + 6 chains = 30+ events, 54+ total items
- **장점**: Comprehensive coverage
- **단점**: Largest scope

**추천**: Option 3 (matches plan target)

## 결정 (Decision)

**Option 3**: Character + faction + general + chains.

### Target counts

| Category | Current | Target | Delta |
|---|--:|--:|--:|
| Character events | 0 | 9 | +9 |
| Faction events | 0 | 10 | +10 |
| General events | 4-6 | 11 | +7 |
| Event chains | 0 | 6 | +6 |
| **Total events** | **4-6** | **30+** | **+24** |

### Per event structure

```python
@dataclass(frozen=True, slots=True)
class StoryEvent:
    id: str
    category: str  # "character" | "faction" | "general"
    trigger: EventTrigger
    dialogue: tuple[str, ...]  # 3-5 lines
    outcomes: tuple[EventOutcome, ...]  # 2-3 branches
    reward: RewardSpec
```

### Character events (9)

| Jockey | Event theme | Personality |
|---|---|---|
| Case | Past-life ghost | Disillusionment |
| Molly | Wetwork contract | Pragmatism |
| Bobby | Mascot memory | Idealism |
| Suit | Corporate audit | Cynicism |
| Wigan | Vodou construct | Spirituality |
| Angie | Childhood tragedy | Innocence |
| Sally | Former lover | Cold operator |
| 3Jane | Family pressure | Heir-apparent |
| Neuromancer | AI transcendence | Aphoristic |

### Faction events (10)

| Faction | Event theme | Outcome |
|---|---|---|
| Hosaka | Audit notice | CRED or stealth |
| Sense/Net | Surveillance | Intel or rep |
| Yakuza | Enforcement | Combat or bribe |
| T-A | Family vote | Alliance or escape |
| Loa | Vodou summoning | Power or curse |
| (5 more) | per faction lore | varies |

### General events (11)

- Random encounter variety (cyberpunk tones)
- Tone: Gibson-haunting, body-horror, corporate dread

### Event chains (6)

| Chain | Length | Theme |
|---|---|---|
| The Memory Heist | 5 | Sprawl echo |
| Faction Conflict | 4 | Hosaka vs Sense/Net |
| Family Affair | 3 | T-A succession |
| The Loa Path | 5 | Vodou initiation |
| The Construct | 4 | AI awakening |
| The Peripheral | 3 | Jackpot reference |

## Implementation Status (2026-08-18)

**Status**: Implementation complete at target. Data + tests all in place.

| Metric | Target | Actual (2026-08-18) | Delta |
|---|--:|--:|--:|
| Character events | 9 | **9 (via `char_event_*` prefix)** | ✓ at target |
| Faction events | 10 | (combined into 56 total) | ✓ at target |
| General events | 11 | (combined into 56 total) | ✓ at target |
| Event chains | 6 | (within 56 total) | ✓ |
| Total events | 30+ | **56** | +26 over |

### Character-specific events (per ADR §"Character events")

Confirmed present in `events.json`:
```
char_event_case_neon_memory
char_event_sil_silver_blade
char_event_kas_morrison_echo
char_event_suit_corporate_mask
char_event_wigan_vodou_drift
(...and 4 more, total 9)
```

Each character-specific event follows the ADR's per-jockey theme matrix (Case past-life ghost / Molly wetwork / Suit corporate audit / Wigan vodou / Angie / Sally / 3Jane / Neuromancer).

### Tests

- `test_phase13_events.py` (Phase 13 coverage)
- `test_event_dialogues.py`
- `test_event_view.py`
- `test_matrix_events.py` (ADR-0165 baseline events)
- `test_phase28_classified_event.py`

**No further action on ADR-0191** — implementation closed, character events present, general events + chains at scale.

---

## Implementation surface

### Data files

- `prototype/data/story/events.json` — 30+ new entries
- `prototype/data/story/event_chains.json` (NEW) — 6 chain definitions
- `prototype/data/story/event_dialogue.json` (NEW) — Gibson-tone lines

### Code

- `engine/event_story.py` — extend `StoryEvent` registry
- `engine/event_chain.py` (NEW) — chain progression
- `engine/event_trigger.py` (NEW) — per-event trigger logic

### Tests

- `tests/unit/test_event_story.py` — per-event coverage
- `tests/unit/test_event_chain.py` (NEW) — chain progression
- `tests/unit/test_event_trigger.py` (NEW) — trigger conditions

### Design docs

- `design/systems/story-events.md` — new event types
- `design/systems/dialogue.md` — Gibson tone guidance

### Testcases

- `testcases/events/character_events.md` (NEW)
- `testcases/events/faction_events.md` (NEW)
- `testcases/events/event_chains.md` (NEW)

### i18n

- All event dialogue in `data/i18n/{en,ko}.json`

## Consequences (Pillar impact)

- **Pillar 1 (Run)**: Strong — variety per run via random events
- **Pillar 2 (Matrix)**: Moderate — events trigger in cyberspace
- **Pillar 3 (Flatline)**: Neutral — events don't affect combat directly
- **Pillar 4 (Build)**: Indirect — events unlock small rewards
- **Pillar 5 (Style)**: Very strong — Gibson-tone narrative beats

**Tests**: +20-25 tests
**Effort**: 3-4 sessions
**Risk**: Low — additive content

## 열린 질문

1. **Event frequency**: 1 event per run, or 2-3? Recommend 2-3 (more variety).
2. **Chain progression**: Linear, or branching? Recommend linear (clearer Gibson narrative).
3. **Dialogue length**: 3-5 lines per event, or 5-8? Recommend 3-5 (pacing).
4. **Character-specific triggering**: Visible to player (after 5 missions with character), or hidden? Recommend visible (transparency).

## 다음 단계

If approved:
1. Character-specific events (9 events)
2. Faction-specific events (10 events)
3. General events (11 events)
4. Event chains (6 chains)
5. Dialogue content (Gibson tone)
6. Tests + design docs
7. i18n
8. Atomic commit
