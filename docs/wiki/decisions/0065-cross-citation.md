# ADR-0065: Cross-Project Citation Integrity (Fiction ↔ wet_run)

**상태**: Accepted (2026-10-14) — immutable; 변경 시 신규 ADR
**날짜**: 2026-10-14
**결정자**: Sisyphus (session agent)
**우선순위**: P2
**관련**: ADR-0213 (PPL & ZDR), AGENTS.md §3 (dependents), AGENTS.md §6 (hard blocks)
**선행**: ADR-0063 (subagent routing), ADR-0064 (model strategy)

## 목적

Fiction 파생소설(`Fiction/derivative/xauthors/halo/en/`)과 wet-run 스토리(`Game/wet_run/`) 간 인용이 단방향(정보→게임)으로만 유지되며, 역방향 구조적 연결이 약함. 양방향 wikilink 프로토콜 + audit 확장으로 구조적 일관성 유지.

## 결정

1. **양방향 wikilink 규칙** (`docs/design/verification-framework.md` §2 참조):
   - Fiction 캐릭터/설정 → `wet_run` 인용 시 `[[...]]` + 원문/출처 인용 필수
   - `wet_run/docs/wiki/index.md` → Fiction `wiki/works/` 참조 유지 + 역참조 노트 추가
2. **검증**: `scripts/find_dashboard_broken.py` 확장으로 양방향 링크 샘플 검사; 세션 종료 전 `audit_vault.py` 0 확인
3. **변경 관리**: `AGENTS.md` §6 Accepted ADR 변경 금지 → 본 ADR 변경 시 `ADR-0066` 신규 작성

## 결과

- `docs/demo-tool-inventory.md`: 현재 상태 기록 (1019 HTML, 134 broken / 200 sample)
- `Game/wet_run/docs/wiki/index.md`: `Fiction/wiki/works/` 참조 유지 (기존)
- `docs/design/demo-journal-design.md`: Jev Noul 분류로 위반 감지 (p ≥ 0.6 기준)

## 영향

- `Fiction/` `raw/`: 읽기전용 유지; 인용 변경 시 `wiki/`만 수정
- `wet_run/web/`: 코드 변경 중 Fiction 인용 필요 시 `AGENTS.md` §3 의존성 확인
- `decisions/`: 본 ADR immutable

## Implementation Status (2026-11-04)

**Status**: ✅ Implemented

**Evidence** (2026-11-04 확인 — 본 ADR 이 참조하는 산출물이 모두 존재한다):

- `../../Fiction/derivative/` — 파생소설 트리 유지
- `docs/design/verification-framework.md` — §2 인용 규칙 문서
- `../../scripts/find_dashboard_broken.py` — 대시보드 링크 검사 (워크스페이스 루트)
- `../../scripts/audit_vault.py` — 볼트 전체 링크 감사 (0 broken 확인)
- `../../docs/demo-tool-inventory.md` — 도구 인벤토리
- `docs/design/demo-journal-design.md` — Jev Noul 분류 기록
- `docs/wiki/index.md` — Fiction 참조 유지

**Notes**:

- 이 파일은 2026-11-04 까지 **정본 위치에 없었다.** 유일한 사본이 프로젝트 AGENTS.md 가
  "prototype 잔재"라고 선언한 `Game/wet_run/decisions/ADR-0065-cross-citation.md` 에 있었고,
  인덱스에도 행이 없었다. ADR-0267(문서·구조 감사)에서 **정본으로 이동**하고 인덱스에 등재했다.
- **결정 내용은 변경하지 않았다** (Accepted ADR immutable). 파일명만 정본 규약(`0065-*.md`)에 맞췄다.
- 유효성 재판정: 참조 산출물이 모두 살아 있으므로 **Accepted 유지**.
