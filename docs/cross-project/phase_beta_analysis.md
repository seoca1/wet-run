# Phase β — Mission / Story / Scene Unification Analysis

> **Generated**: 2026-07-26 (Phase α follow-up)
> **Scope**: Analyze overlap between three narrative layers for each wet_run mission
> **Recommendation**: No content deduplication needed; possible UI integration improvements

## Executive Summary

Each wet_run mission can have **three independent narrative representations**:

| Layer | Source | Purpose | Size | Count |
|---|---|---|---|---|
| **Mission synopsis** | `prototype/data/missions/missions.json` `story.synopsis_en` | Game design summary, used in HUB / mission select UI | ~50-200 words | 111 (all missions) |
| **Fiction derivative** | `Fiction/derivative/sprawl-trilogy/{short-stories,novelettes}/en/` | Full standalone narrative for reading | 1000-1500 words avg | 100 (with `game_mission_id`) |
| **GN scene dialogue** | `prototype/data/scenes/{jockey}/*.json` | Auto-play in-game narration | 200-400 chars per dialogue | 81 scenes × 9 jockeys |

**Key finding**: These three layers serve fundamentally different purposes and have minimal content duplication. They complement each other in a layered narrative architecture.

## Cross-Layer Statistics (2026-07-26)

| Metric | Value |
|---|---|
| Total missions | 111 |
| Missions with synopsis_en | 111 (100%) |
| Missions with Fiction derivative | 100 (90%) |
| Missions with GN scene reference | 1 (wigan_call → wigan/01_zavijava.json) |
| Total GN scenes | 81 (9 jockeys × 9 scenes each) |
| Total dialogues across GN scenes | 223 |
| Total words in GN scene JSON | 45,347 |
| Fiction derivative EN+KO | 206 files |
| Average Fiction words/story | 1,391 |

## Layer-by-Layer Purpose

### Layer 1: Mission synopsis (game-design summary)

**Purpose**: HUB UI display, mission select screen, Codex-style archive

**Example** (`aleph_fragment`):
```
Rain hit the neon in Shibuya. A courier on a fixed-gear bike carries
a package that shouldn't exist — warm, alive, humming with data that
organizes itself.
```

**Audience**: Player making run/decision choices
**Lifecycle**: Static, updated when mission design changes

### Layer 2: Fiction derivative short story (canonical narrative)

**Purpose**: Standalone reading experience, dashboard display, literary reference

**Example** (`aleph_fragment`): 1,233 words of first-person narrative
following Case POV through Chiba City, discussing the Aleph construct.

**Audience**: Reader interested in lore
**Lifecycle**: Stable once written; rarely modified (frontmatter updates only)

### Layer 3: GN scene dialogue (in-game auto-play)

**Purpose**: Cinematic narration during game flow (CHAPTER, ARC_PHASE screens)

**Example** (`scene_case_jackout`):
```json
{
  "speaker": "case",
  "text_en": "Thirty seconds. The Ono-Sendai electrodes lift from my scalp..."
}
```

**Audience**: Player experiencing the story moment in-game
**Lifecycle**: Refined alongside gameplay balance

## Overlap Analysis

### Syntactic overlap: minimal

- Mission synopsis → Fiction: Different writing style (descriptive vs narrative)
- Mission synopsis → GN scene: Different voice (omniscient vs first-person)
- Fiction → GN scene: Different format (prose vs dialogue)

### Thematic overlap: intentional

All three layers share:
- Same character POV (e.g., `aleph_fragment` is Kas POV across layers)
- Same time period (post-merger / arc-5 etc.)
- Same key events (referenced in mission.story.cast and gn_scene.dialogue)

This is **architectural coherence**, not duplication. Each layer offers a different access mode to the same lore.

### Direct mission_id references in scenes: rare

Only **1 of 81 GN scenes** references a mission_id directly (`wigan_call`).
This suggests GN scenes are currently standalone prologue/epilogue content
not directly tied to mission gameplay.

## Recommendations

### Short-term (Phase β-1): UI integration (no content changes)

1. **Mission select screen**: When player picks a mission, show both:
   - Mission synopsis (current behavior)
   - Link to corresponding Fiction derivative (NEW)
2. **Codex/Archive screen**: Show 3-layer narrative breadcrumb
   - Mission ID + tier + archetype
   - Fiction derivative (linked)
   - Related GN scenes (jockey-specific)
3. **Dashboard update**: `character_stats.json` already includes
   `game_mission_id`; ensure HUD references this for player-facing links

### Medium-term (Phase β-2): GN scene ↔ mission linkage (optional)

Only 1 of 81 GN scenes references a mission_id. To improve integration:
- Add `mission_id` field to GN scene JSON (optional)
- Update `chapter_view.py` and `arc_phase.py` to look up mission by current scene
- Use mission synopsis as fallback when no scene dialogue exists

**Risk**: 80 of 81 scenes lack mission references. Adding the field would
be optional per-scene and would not break existing content.

### Long-term (Phase β-3): Content unification (low priority)

Currently the three layers are written independently. Future work could:
- Generate mission synopsis from Fiction first paragraph (semi-automated)
- Auto-link GN scenes to mission by content matching (requires NLP)

**Recommendation**: Defer to Phase 8+. Current layered approach is intentional
and provides flexible authoring.

## Cross-Reference Architecture

```
wet_run mission
├─ missions.json[story]
│   ├─ synopsis_en         → HUB / Codex
│   ├─ source              → Fiction stem
│   └─ game_mission_id     → (set by Fiction frontmatter)
├─ Fiction derivative
│   └─ game_mission_id     → mission_id (Phase α)
└─ GN scene
    └─ mission_id           → (optional, 1/81 currently)
```

**Phase α status**: Mission ↔ Fiction bidirectional link established (100%)
**Phase β-1 target**: Mission ↔ Fiction UI integration
**Phase β-2 target**: GN scene ↔ mission optional linkage

## Conclusion

Phase α successfully closed the bidirectional Fiction↔mission gap. Phase β
should focus on **exposing this link in player-facing UI** rather than
deduplicating content. The three narrative layers are complementary by
design and should remain independent for authoring flexibility.