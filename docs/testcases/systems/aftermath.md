# TC-AFTER: Combat Aftermath & Subtitles (전투 후일담 & 자막)

> **관련**: `../../decisions/0019-combat-aftermath-subtitles.md`, `../../design/systems/aftermath.md`

전투 후일담, 소설 인물 반응, 한글 자막 시나리오.

## TC-AFTER-001: Black ICE 격파 — major (P0, Active)

**Given**: 자키가 Black ICE 격파 (importance = major)
**When**: 전투 종료 → Data Salvage 후
**Then**: Aftermath 표시 (narrative en + ko, ~5초)
**Then**: Character Reaction — Dixie 표시 (`◊D◊` portrait + en + ko 자막)
**Then**: "Tap to continue" 또는 자동 Hub 복귀

## TC-AFTER-002: Construct 격파 — legendary (P0, Active)

**Given**: 자키가 Construct 격파 (importance = legendary)
**When**: 전투 종료
**Then**: Aftermath 표시 (긴 narrative, ~7초)
**Then**: Multiple reactions — Dixie, 3Jane (각 ~3초)
**Then**: Story Archive 자동 저장

## TC-AFTER-003: 일반 ICE 격파 — minor (P0, Active)

**Given**: 자키가 standard ICE 격파 (importance = minor)
**When**: 전투 종료
**Then**: Aftermath 표시 X
**Then**: 즉시 Data Salvage 메뉴

## TC-AFTER-004: 자막 형식 — en + ko stack (P0, Active)

**Given**: Event 메시지 표시
**When**: 렌더링
**Then**: 형식:
```
> You jack in. The world goes gray.
> 잭인. 세계가 회색이 된다.
```
**Then**: en = 흰색, ko = 노란색 `(255, 220, 100)`

## TC-AFTER-005: 자막 적용 범위 (P0, Active)

**Given**: Combat Aftermath / Story Event / Mission Briefing / Hub dialogue
**When**: 표시
**Then**: 자막 형식 (en + ko stack)
**And given**: HUD 수치 (PPL, ZDR, HP) / 메뉴 라벨
**Then**: 자막 미적용 (시스템 메시지)

## TC-AFTER-006: Dixie Reaction (P0, Active)

**Given**: Black ICE 격파
**When**: Reaction 표시
**Then**: Portrait `◊D◊` cyan
**Then**: en + ko 텍스트 (Gibson 톤, ROM 어투)

## TC-AFTER-007: Finn Reaction — 첫 미션 (P0, Active)

**Given**: 첫 미션 (first_jack) 완료
**When**: Mission complete
**Then**: Finn reaction (`♠F♠` magenta)
**Then**: "Don't make a habit of dying" 톤

## TC-AFTER-008: 한국어 번역 — 깁슨 톤 (P0, Active)

**Given**: Aftermath 콘텐츠
**When**: ko 번역
**Then**: 깁슨 어휘 유지 (construct, ICE, jack in, flatline)
**Then**: 고유명사 영문 유지 (Case, Dixie, Tessier-Ashpool)
**Then**: 의역/번역 (직역 X)
**Then**: 자연스러운 한국어 rhythm

## TC-AFTER-009: Story Archive 자동 저장 (P1, Active)

**Given**: Aftermath 표시 완료
**When**: 표시 종료
**Then**: Story Archive에 자동 추가
**Then**: 카테고리: "aftermath"
**Then**: 메인 메뉴 → Story Archive → "Combat" → Aftermath 목록

## TC-AFTER-010: Legendary 트리거 — 3Jane (P2, Active)

**Given**: 자키가 3Jane (T-A construct) 격파
**When**: 격파 시점
**Then**: importance = legendary 자동 설정
**Then**: 4+ 문단 narrative
**Then**: Multiple reactions (Dixie, Maelcum, Case)
**Then**: Ending hook 표시

## TC-AFTER-011: PPL/ZDR 극단 비율 — major 트리거 (P1, Active)

**Given**: PPL/ZDR > 3.0 (압도적 우위)
**When**: 전투 종료
**Then**: importance = major (auto)
**Then**: 짧은 Aftermath 표시

## TC-AFTER-012: 자막 페이드인 (Phase 7+, P2, Active)

**Given**: Aftermath 표시 시작
**When**: 0~500ms
**Then**: 페이드인 (0% → 100% opacity)
**Then**: 깁슨 글리치 (1-2 frame)
**Then**: 본문 표시

## Phase 6+ 자동화 (예정)

- `tests/unit/test_aftermath.py` — Aftermath / Reaction / Registry
- `tests/unit/test_subtitle_renderer.py` — 자막 stack 렌더링
- `tests/integration/test_combat_aftermath.py` — 전투 → Aftermath → Reaction 흐름
- 회귀 테스트: 매 서사 콘텐츠 변경 시
