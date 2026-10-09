---
title: "Cyberpunk Sources Prep"
category: world
---

# Cyberpunk Sources Prep

**Status**: Ready — Far Grid 입주처 확정 (ADR-0213 Accepted 2026-10-07). Raw provision pending (user-side), then Fiction ingest.

**Source inventory**: `Fiction/SOURCES_INVENTORY.md` §SF_F Drive Collection (2026-10-07, 48 authors). This page is the cyberpunk-only subset with wet-run linkage points.

## Charter tension (must resolve before any ingest)

Wet-run `AGENTS.md` §8 forbids borrowing tone/terms from non-Gibson cyberpunk works. Fiction charter is Gibson-only (expansion needs ADR-0054 Accepted). So this page is **reference tracking only** — any actual ingest needs:
1. Fiction ADR-0054 (or successor) Accepted for the author in question
2. A wet-run design decision on how non-Gibson material enters canon (Gibson-tone adaptation, not direct borrowing)

## Candidate works (cyberpunk core)

| Work | Author | Year | SF_F status | Wet-run hooks |
|------|--------|------|-------------|---------------|
| Hardwired | Walter J. Williams | 1986 | 12-item folder, 4 txt | Smuggler/panzerboy factions, orbital-ground runs, cyberware gear |
| Voice of the Whirlwind | Walter J. Williams | 1987 | same folder | Clone operative concept, faction intrigue missions |
| Halo | Tom Maddox | 1991 | 1 rar | Corporate AI intrigue, mission framing |
| True Names | Vernor Vinge | 1981 | txt present | Proto-cyberspace concepts → [[glossary]], ICE archetypes |
| Across Realtime | Vernor Vinge | 1986 | rar/zip | Low-tech vs high-tech zone design |
| Otherland (series) | Tad Williams | 1996-2001 | Otherland 2 in 12-item folder | VR dungeon/node design, long-run campaign structure |

## Adjacent (New Wave / precursor — lower priority)

| Work | Author | Year | SF_F status | Wet-run hooks |
|------|--------|------|-------------|---------------|
| Nova / Dhalgren | Samuel L. Delany | 1968/1975 | Nova txt present | Urban sprawl texture, sous les pavillons style reference |
| Camp Concentration | Thomas M. Disch | 1968 | txt present | Dystopia mission tone |

## Known gaps (not in SF_F — do not plan around)

- Bruce Sterling solo (Schismatrix) — only Gibson-Sterling collabs present
- Rudy Rucker, John Shirley, Pat Cadigan — absent entirely
- Philip K. Dick — absent (Thomas M. Disch folder is a different author)

## Pipeline (when raw arrives)

1. User provisions raw → Fiction ingest (ADR-0022 Stage 2-3 pattern, or ADR-0054 pilot)
2. Fiction wiki canonical pages first (`Fiction/wiki/` — game never ingests raw directly)
3. Game adaptation stub here in `works/` (mirror pattern: thin stub + Primary source link, e.g. neuromancer.md)
4. Mission/glossary/faction wiring via `cross-project-integration` mechanism

## Cross-Reference

- Primary pattern: [[sprawl_universe]] (Sprawl canon overview)
- Terms: [[glossary]] (where adapted terms land)
- Factions: [[factions]] (where adapted factions land)
- Cyberspace: [[cyberspace]] (where adapted matrix concepts land)
- Upstream inventory: `Fiction/SOURCES_INVENTORY.md` §SF_F Drive Collection
- Expansion governance: `Fiction/decisions/0054-sf-collection-expansion.md` (Draft)
