---
title:
  en: "Cross-Project Integration: Fiction ↔ roguelike_sprawl"
  ko: "크로스 프로젝트 통합: Fiction ↔ 로그라이크 스프롤"
created: 2026-07-26
updated: 2026-08-08
phase: "Phase 83 (post-Fiction-Phase-73-82 propagation)"
description:
  en: "How roguelike_sprawl integrates with the Fiction derivative short story corpus. Two-way link mechanics, validation, and known orphan references. Updated 2026-08-08 to reflect Fiction Phase 73-82 corpus deepening + ADR-0017 backfill + verbatim text audit + 6th synthesis page (Operative-Class Across Trilogies)."
  ko: "로그라이크 스프롤이 Fiction 파생 단편 코퍼스와 어떻게 통합되는지 정리. 양방향 링크 메커니즘, 검증, 알려진 orphan 참조. 2026-08-08 Fiction Phase 73-82 코퍼스 확장 + ADR-0017 백필 + verbatim 텍스트 감사 + 6번째 신서시스 페이지 반영 갱신."
language: en
related:
  - "[[sprawl_universe]]"
  - "[[derivative_stories]]"
  - "[[connections/roguelike_sprawl-missions|roguelike_sprawl-missions]]"
---

# Cross-Project Integration: Fiction ↔ roguelike_sprawl

> **Phase α-J status (2026-07-26)**: Bidirectional link established.
> 100 Fiction stories linked to missions, 81/81 GN scenes linked to missions,
> 0 orphan references. Boss B-3 features wired across 5/5 boss profiles.
> 100 Fiction stories linked to missions, 81/81 GN scenes linked to missions,
> 0 orphan references. All verified by `verify_story_links.py`.

## Why this matters

The roguelike_sprawl game references a Fiction derivative short story
for nearly every mission. The Fiction corpus was written first, and the
game borrows narrative weight from it. Without a formal cross-project
link, the two sides drift apart over time (orphan references, duplicate
work, contradictory references).

This page describes the integration mechanism and its current state.

## Link direction 1: Mission → Fiction (game references story)

**Mechanism**: `missions.json[story].source` field declares the Fiction
stem (filename minus date prefix) that the mission is based on.

**Example** (`aleph_fragment` mission):
```json
{
  "aleph_fragment": {
    "id": "aleph_fragment",
    "title": "Aleph Fragment",
    "story": {
      "source": "aleph_fragment",
      "synopsis_en": "...",
      ...
    }
  }
}
```

**Resolver**: `prototype/src/roguelike_sprawl/data/story_resolver.py` searches
Fiction derivative directories (sprawl-trilogy → bridge-trilogy → blue-ant)
for the file. Falls back to default (first_jack) if not found.

## Link direction 2: Fiction → Mission (story declares its game link)

**Mechanism**: Fiction `.md` file frontmatter `game_mission_id` field
declares the roguelike_sprawl mission_id that the story belongs to.

**Example** (`aleph_fragment.md` Fiction file):
```yaml
---
title: Aleph Fragment
game_mission_id: aleph_fragment
series: 'Sprawl #4.4 (heretic arc-4)'
source_text: Original story for Roguelike Sprawl
---
```

**Resolver**: `story_resolver.py:get_fiction_story_for_mission(mission_id, repo_root)`
scans Fiction frontmatter for the mission_id match. Returns dict with
title, character_ref, word_count, trilogy.

## Bidirectional validation

The cross-project integrity CI (`.github/workflows/cross-project-integrity.yml`)
runs `verify_story_links.py` which checks:
- Every `mission.story.source` resolves to a real Fiction file
- Every `game_mission_id` in Fiction resolves to a real mission_id
- No orphan references (broken links either direction)

**Current state** (as of 2026-07-26 → **updated 2026-08-08**):
- 33/33 mission sources resolve correctly
- 102 Fiction stories declare game_mission_id
- 0 orphan references (informational: 17 missions intentionally have
  no Fiction source — Bridge/Blue Ant characters, out of scope per
  AGENTS.md §4.0)

**Updated 2026-08-08 (Phase 83)** — Fiction wiki Phase 73-82 expansion reflected:
- Phase 73: 9 *Burning Chrome* stories deepened with 18 short-story-specific sections (schema §2 closure)
- Phase 74: Johnny Mnemonic + 3jane-tessier-ashpool deepened (4 sections + 2 stub markers cleared from index)
- Phase 75: Agrippa (1992 artist's book) deepened (2 sections)
- Phase 76: Burning Chrome (collection) overview deepened (2 sections)
- Phase 77: New synthesis page — **Short Fiction as Corpus Foundation** (216 lines, 12 works × foundational-pattern mapping)
- Phase 78: ADR-0017 + 150 KO file `source_word_count` backfill (Phase 61 outstanding debt fully resolved)
- Phase 79-80: Sterling + Gibson author page deepening (cross-author parity, 2 sections each)
- Phase 81: Verbatim text audit (6 multi-sentence quote paraphrases, 24/24 novels §4-compliant)
- Phase 82: New synthesis page — **Operative-Class Across the Four Trilogies** (197 lines, 4-era operative-class evolution)

**Cross-project integrity status** (post Fiction Phase 73-82):
- All Fiction wiki pages cited by roguelike_sprawl wiki remain valid (no Fiction edits removed referenced content)
- ADR-0017 added `source_word_count` field to 150 KO derivative files — game-mission references via `game_mission_id` continue to resolve
- Verbatim text audit (Phase 81) paraphrased 6 multi-sentence quote blocks across 4 novels — game mission text unchanged
- New synthesis pages (Phase 77 + 82) provide roguelike_sprawl cross-references for short-fiction corpus foundation + operative-class evolution

**Cross-references to Fiction synthesis pages** (Phase 83 enhancement):
- [../../../../Fiction/wiki/concepts/short-fiction-as-corpus-foundation.md](../../../../Fiction/wiki/concepts/short-fiction-as-corpus-foundation.md) — 12 short-fiction works as the corpus's foundational substrate
- [../../../../Fiction/wiki/concepts/operative-class-across-trilogies.md](../../../../Fiction/wiki/concepts/operative-class-across-trilogies.md) — operative-class evolution (console cowboys → couriers → coolhunters → peripherals)

## GN scene ↔ mission linkage (Phase β-2 + Phase G)

GN (graphic novel) scenes represent character-arc narrative content.
81 scenes × 9 jockeys = 81 total. Each scene may declare `mission_id`
in its JSON to indicate the gameplay mission it relates to.

**Phase G (2026-07-26)**: All 81 GN scenes now declare mission_id.
Mapping uses conservative narrative alignment (epilogues → final_choice,
abstract scenes → closest thematic match).

**Use case**:
- `get_mission_for_scene(scene_id, jockey, repo_root)` looks up mission
- `get_fiction_story_for_mission(mission_id, repo_root)` looks up Fiction
- Combined: scene → mission → Fiction (3-layer narrative breadcrumb)

## Orphan source stems (historical record)

19 mission source stems were originally orphans (Fiction files
referenced by missions but not yet written). Resolution in Phase
follow-up:

| Category | Count | Resolution |
|---|---|---|
| Bridge trilogy (out of scope) | 13 | Removed `story.source` from 13 missions |
| Blue Ant (out of scope) | 4 | Removed `story.source` from 4 missions |
| Sprawl-related, missing file | 2 | Wrote 2 new Fiction short stories (neon_tokyo_courier, sense_net_archive_intrusion) |

After resolution: 0 orphan references. The 17 informational entries
are intentional (Bridge/Blue Ant are out of game scope per policy).

See `docs/cross-project/orphan_source_stems.json` for the full historical
record (also in fiction wiki: `orphan_source_stems.json`).

## Fiction wiki cross-reference

The Fiction project wiki contains a corresponding index:
`Fiction/wiki/connections/roguelike_sprawl-missions.md` — all 111 missions
with their linked Fiction stories (94 linked + 17 informational).

This is the **reverse index**: from Fiction's perspective, what missions
reference each story.

## Adding new content

### To add a new Fiction story that should be a mission:

1. Create `Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-XX_<stem>.md`
2. Add frontmatter:
   ```yaml
   ---
   game_mission_id: my_mission_id
   series: 'Sprawl #X.Y (arc-Z)'
   source_text: Original story for Roguelike Sprawl
   ---
   ```
3. Add a Korean `.ko.md` translation
4. Add a mission entry to `prototype/data/missions/missions.json`:
   ```json
   {
     "my_mission_id": {
       "id": "my_mission_id",
       "title": "My Mission",
       "story": {
         "source": "my_mission_id",
         ...
       }
     }
   }
   ```
5. Run `prototype/scripts/verify_story_links.py` to verify

### To add a new mission that should reference existing Fiction:

1. Find the existing Fiction stem (e.g. from `Fiction/derivative/sprawl-trilogy/short-stories/en/`)
2. Add mission entry with `story.source = "<stem>"`
3. Verify with `verify_story_links.py`

### To add a new mission with custom stage flow:

1. Add mission entry to `prototype/data/missions/missions.json`:
   ```json
   {
     "my_mission": {
       "id": "my_mission",
       "title": "My Mission",
       "story": {
         "source": "my_mission",
         ...
       },
       "stage_flow": [
         "briefing", "travel", "meet_npc", "bypass_security",
         "defeat_ice", "jack_out", "reward", "complete"
       ]
     }
   }
   ```
2. Verify with `verify_story_links.py` (also validates stage_flow)

Available stages (from `run/state.py`):
- briefing, travel, meet_npc, extract_data, defeat_ice,
  bypass_security, black_market, ghost_encounter,
  jack_out, reward, debrief, complete
- Special: salvation_epilogue (Phase 9)

## E-3 balance audit

A balance audit (Phase E-3) was performed on 2026-07-26 covering:
- 33 playable missions × 6 grades × PPL formula
- Reward distribution (credits / tier)
- Zone distribution
- ICE archetype distribution

See `prototype/docs/balance/E3-balance-audit.md` for findings and
recommendations. Key findings:
- Grade 6 has only 1 mission (aleph_fragment) — under-represented
- All reward_credits / reward_tier fields were 0/None → backfilled
- Surface zone over-represented (27/94 = 29%)

## ADR history

- ADR-0006: Cross-project content (game ↔ fiction integrity baseline)
- ADR-0010: i18n content pipeline
- ADR-0032: Graphic novel mode (GN scene origin)
- ADR-0050: Boss ICE multi-phase (target of B-3 enhancements)
- ADR-0125: Boss Phase AoE + Minion Spawn (B-3 implementation)

## Related files

- `prototype/data/missions/missions.json` (single source of truth for game)
- `Fiction/derivative/sprawl-trilogy/{short-stories,novelettes}/` (Fiction source)
- `prototype/src/roguelike_sprawl/data/story_resolver.py` (resolver implementation)
- `prototype/scripts/verify_story_links.py` (validator)
- `prototype/docs/cross-project/orphan_source_stems.json` (historical record)
- `Fiction/wiki/connections/roguelike_sprawl-missions.md` (reverse index)
- `.github/workflows/cross-project-integrity.yml` (CI enforcement)