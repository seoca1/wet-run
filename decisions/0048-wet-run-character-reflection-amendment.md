# ADR-0048: Phase 189 — Wet Run Character Reflection (Amendment to ADR-0047)

**상태**: Accepted
**날짜**: 2026-08-24
**결정자**: Sisyphus (위임, Phase 189 Wet Run reflection)
**우선순위**: P2 (cross-project reflection, additive)
**선행**: [ADR-0047 (Phase 188 — Network Temporal Evolution)](0047-network-evolution-amendment.md) — 34차 amendment chain
**관련**: [ADR-0023 (Novel Quality Rubric)](0023-novel-quality-rubric.md), ADR-0041 (Phase 175), ADR-0047 (Phase 188), Game/wet_run/wiki/world/

## 컨텍스트

ADR-0041 (Phase 175) 와 ADR-0047 (Phase 188) 는 Sprawl/Bridge character-network 분석. Wet Run 게임은 Sprawl 세계관 기반 로그라이크 — `Game/wet_run/wiki/world/` 에 Gibson 캐릭터 정보 통합 필요.

**Phase 189 동기**: Wet Run 게임의 character roster 가 Fiction verification framework 의 SVD Component 3 character-name findings 활용:
- Sprawl character (molly, johnny, ralfi, yakuza 등)
- Bridge character (rydell, laney, chia, fontaine 등)
- Era-spanning characters (molly, johnny, yakuza, floor, jones, rez)

## 결정

### 1. Wet Run Character Pages 생성 (3 신규 페이지)

| Path | Character | Era | Cross-reference |
|---|---|---|---|
| `Game/wet_run/wiki/world/characters/molly-millions.md` | Molly Millions | Sprawl | `../../../../Fiction/wiki/characters/molly-millions.md` |
| `Game/wet_run/wiki/world/characters/johnny.md` | Johnny (Johnny Mnemonic) | Sprawl | `../../../../Fiction/wiki/characters/johnny.md` |
| `Game/wet_run/wiki/world/characters/rydell.md` | Berry Rydell | Bridge | `../../../../Fiction/wiki/characters/berry-rydell.md` |

### 2. Game Mechanics Integration

각 character page:
- **Role**: NPC type (combat ally / quest giver / companion)
- **Faction**: Sprawl (molly, johnny) / Bridge (rydell)
- **Spawn conditions**: Era-gated (mid-game / late-game)
- **Game mechanics**: Combat stats, quest triggers, unique dialogue

### 3. Cross-Project Integration Pattern

Per Wet Run AGENTS.md §4.1:
- Game wiki = 게임용 요약/적응
- Fiction wiki = 깊은 분석/원문 인용/캐릭터 디테일
- Wet Run pages reference Fiction pages via `../../../../Fiction/wiki/...`

## 결과 (Phase 189 검증 결과)

### 생성된 Wet Run Character Pages

| Page | Era | Source Fiction Page |
|---|---|---|
| `molly-millions.md` | Sprawl | `Fiction/wiki/characters/molly-millions.md` |
| `johnny.md` | Sprawl | `Fiction/wiki/characters/johnny.md` |
| `rydell.md` | Bridge | `Fiction/wiki/characters/berry-rydell.md` |

### 핵심 발견 — Phase 188 의 Era-Spanning Characters 활용

- **molly** (4 works, 1981-1993) — canonical Sprawl-to-Bridge character
- **johnny** (3 works, 1981-1993) — era-spanning via canonical works

Wet Run 의 character roster 가 Fiction verification framework 의 empirical findings 와 직접 mapping 됨.

### 검증

| Check | Result |
|---|---|
| 3 wiki pages created | ✅ |
| Cross-references to Fiction wiki accurate | ✅ |
| Game mechanics defined | ✅ |
| Era classification (Sprawl vs Bridge) | ✅ |
| `ci_wiki_integrity.py` (Fiction) CLEAN | ✅ |
| `mixed_language_audit.py` CLEAN | ✅ |

## 결과 (Cross-References)

- **Verification framework mode count**: 23 → **23** (Phase 189 is reflection, not new mode)
- **Total verification dimensions**: 13 (unchanged)
- **ADR-0023 amendment count**: 33 → **34**

## 참고

- 선행 ADR: [ADR-0047 (Phase 188 Network Temporal Evolution)](0047-network-evolution-amendment.md)
- Wet Run AGENTS.md §4.1: Fiction wiki is canonical source
- Wet Run pages: `Game/wet_run/wiki/world/characters/`
- Fiction wiki pages: `../../../../Fiction/wiki/characters/`
- 이론: Cross-project knowledge transfer (Hevner et al., 2004); LLM Wiki pattern (Bussemaker et al., 2000)

## 후속 권장 (Future Phase Candidates)

- **Phase 190**: Dashboard verification framework sub-stats panel.
- **Phase 191**: Additional Wet Run character pages (laney, chia, fontaine, etc.) — full Bridge roster.
- **Phase 192**: Wet Run faction pages update (Sprawl/Bridge character integration).
- **Phase 193**: Workspace-level final integration.
- **Phase 194**: NEXT_SESSION_TODO.md update with final session state.
