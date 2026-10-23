# Architecture Decisions — Redirect

> **⚠️ 2026-10-20**: `docs/architecture/` 는 **더 이상 ADR canonical 위치가 아님**. 모든 게임 ADR은 `docs/wiki/decisions/` 에 있습니다.
> 본 디렉토리의 개별 ADR 파일들은 `docs/wiki/decisions/` 로 이동되었으며, 원본 위치는 wikilink redirect stub으로 남겨 있습니다.

## 이동 규칙

| 원래 경로 | 현재 canonical 경로 |
|---|---|
| `docs/architecture/XXXX-*.md` | `docs/wiki/decisions/XXXX-*.md` |

## canonical 위치

- **ADR**: `docs/wiki/decisions/` (130 ADRs, 0001–0213)
- **인덱스**: `docs/wiki/decisions/README.md`
- **디자인 명세**: `docs/wiki/design/`
- **LLM Wiki**: `docs/wiki/lore/`, `docs/wiki/world/`

## 변경 사항 (2026-10-20)

- `0010-verification-pipeline.md` → `docs/wiki/decisions/`
- `0210-combat-vfx-effect-schema.md` → `docs/wiki/decisions/`
- `0213-far-grid-separate-expansion.md` → `docs/wiki/decisions/`
- 기존 127 ADR + 신규 3 ADR = **130 ADR** 모두 `docs/wiki/decisions/` 로 통합

## 참고

- AGENTS.md §2는 여전히 `docs/architecture/` 를 "web/ ADR 권장 위치"로 언급하나, **현행 canonical은 `docs/wiki/decisions/`** 이다.
- LLM Wiki 패턴상 `docs/wiki/` 가 query/update에 최적화되어 있어, 모든 ADR을 여기로 통합한 것에 의미가 있다.