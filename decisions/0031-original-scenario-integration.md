# ADR-0031: Original Scenario Integration (단편 → 프롤로그 → 초반 플레이 통합)

> **상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
> **날짜**: 2026-06-20
> **결정자**: 사용자
> **관련**: ADR-0009 (Story/News), ADR-0010 (i18n), ADR-0011 (Portrait), ADR-0013 (Story Events), ADR-0019 (Aftermath), ADR-0020 (Exploration), ADR-0022 (Original Story 골격)

## 1. 컨텍스트

Wet Run의 오리지널 시나리오는 다음 자산을 보유하고 있으나 **연결되지 않은 채 단절**되어 있다:

| 자산 | 위치 | 상태 |
| --- | --- | --- |
| 오리지널 캐릭터 3명 (K, Sil, Kas) | `engine/original_story.py` | 정의됨 |
| 캐릭터 선택 + 프롤로그 이벤트 | `engine/original_story.py` | 정의됨 |
| 엔딩 A/B (캐릭터당 2개, 총 6개) | `engine/original_story.py` | 정의됨 |
| 단편 5편 (Case/Marly/Kumiko/Wigan/Sally) | `Fiction/derivative/.../short-stories/` | fiction 영역에 격리 |
| 데모 스크립트 (play.py, demo.py) | `scripts/` | **character_select를 거치지 않음** |
| 대시보드 `stories.html` | `dashboard/` | 단편 5편 표시하나 게임과 미연결 |

**문제점** (실측, 2026-06-20):
1. `play.py` / `demo.py`의 state machine은 `MENU → HUB → MATRIX`만 순환. `CHARACTER_SELECT` 화면 없음.
2. `original_story.py`의 `CHARACTER_SELECT_EVENT`, 3개 `*_PROLOGUE_EVENT`는 데이터로만 존재.
3. `verify_original_prologue.py`로 단독 검증은 가능하지만 실제 게임 흐름에 통합 안 됨.
4. 단편 5편 중 3편(Case, Marly, Kumiko)이 `derivative_stories.md`에 캐릭터 매핑만 기록. 게임 내 인용/대사 미사용.

**디자인 영향**:
- Pillar 5 ("깁슨 톤") 약화 — 단편이 게임 외부에 격리되면 세계관 일관성이 깨짐
- 스토리 아크의 기점이 없음 — 플레이어가 "왜 이 의뢰를 받는지" 동기가 부재
- i18n 자산 활용도 낮음 — 단편 1,400~1,500자 분량은 게임 내 사용에 부족

## 2. 목표

| # | 목표 | 효과 |
| --- | --- | --- |
| G1 | 단편 → 프롤로그 → 초반 플레이를 하나의 시나리오로 연결 | 캐릭터 선택이 게임 시작점이 됨 |
| G2 | 캐릭터 1:1 매핑 (novice ↔ Case, veteran ↔ Marly, heretic ↔ Kumiko) | 단편이 캐릭터의 동기/배경을 설명 |
| G3 | 단편을 소설 레벨(3,000~5,000자)로 확장 | 게임 내 인용 가능한 깊이 |
| G4 | 모든 단편을 게임 자산으로 import (event dialogues, aftermath, story archive) | 깁슨 톤 일관성 |
| G5 | `play.py` / `demo.py`에 character_select + chapter 화면 통합 | 데모가 풀 시나리오 시연 |

## 3. 옵션 비교

### Option A: 통합 시나리오 (단편 → 챕터 → 매트릭스)

| 항목 | 내용 |
|---|---|
| 흐름 | MENU → CHARACTER_SELECT → CHAPTER (단편 인용 + 대사) → HUB → MATRIX → JACK_OUT → ENDING |
| 장점 | 단편이 게임 진입점. 캐릭터 동기 부여. Pillar 5 강화. |
| 단점 | 단편 3편 분량 확장 작업. 1~2 세션 추가. |
| 권장 | ✅ |

### Option B: 단편 격리 유지 (현재)

| 항목 | 내용 |
|---|---|
| 흐름 | MENU → HUB → MATRIX (변경 없음) |
| 장점 | 작업 0. |
| 단점 | 단편은 fiction 영역에 영구 격리. Pillar 5 약화 지속. 캐릭터 동기 부재. |

### Option C: 단편 인용만 (이벤트 dialogues에 1~2줄 발췌)

| 항목 | 내용 |
|---|---|
| 흐름 | 단편 발췌를 event dialogue에 인용. chapter 화면 없음. |
| 장점 | 가벼운 통합. |
| 단점 | 단편의 깊이가 손실. 캐릭터 1:1 매핑 약함. |

**추천**: **Option A** — 단편이 게임의 *진입점*이 되어야 Pillar 5가 완성됨.

## 4. 권장안 (Option A) 상세

### 4.1 캐릭터 1:1 매핑

| 캐릭터 | 단편 | 원작 | 게임 동기 |
| --- | --- | --- | --- |
| **케이 (K) — Novice** | 잭아웃 후 30초 | Neuromancer (Case 1인칭) | "돈이 필요하다. 첫 의뢰. 손이 떨린다." |
| **실 (Sil) — Veteran** | 루이지아나의 신 | Count Zero (Marly 3인칭) | "Mara의 죽음. Tessier-Ashpool에 대한 복수. 베테랑의 무게." |
| **카스 (Kas) — Heretic** | 매나리사의 자정 | Mona Lisa Overdrive (Kumiko 3인칭) | "Loa 네트워크. Sprawl의 바퀴를 부수러 왔다." |

### 4.2 시나리오 흐름

```
┌─────────────────────────────────────────────────────────────┐
│ MENU (Press START)                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ CHARACTER_SELECT                                            │
│  - "The Finn" (♠F♠) NPC 이벤트                             │
│  - 3 옵션: 1.케이(돈) 2.실(복수) 3.카스(전복)                │
│  - 선택 → character_id 저장 + Chapter 화면 큐               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ CHAPTER (단편 인용 + 캐릭터 대사)                            │
│  - 단편 발췌 3,000~5,000자 (한글 + 영어)                     │
│  - "Press any key" 로 매트릭스 진입                         │
│  - 데이터: data/story/chapters/{char}.json                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ HUB (의뢰 선택)                                              │
│  - Chapter 직후: 선택한 캐릭터의 첫 의뢰 자동 표시          │
│  - 플레이어: [ACCEPT] / [BROWSE OTHER JOBS]                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ MATRIX (잭인) — 첫 의뢰                                      │
│  - Sense/Net Surface 노드 그래프                            │
│  - Wisp T1 ICE 1~2개                                        │
│  - 데이터 추출 → JACK_OUT                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ AFTERMATH (전투 후일담)                                      │
│  - 캐릭터별 first_mission 반응 (Dixie, Finn 등)             │
│  - 4,000ms 화면                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ENDING_PROLOGUE (캐릭터 선택지)                              │
│  - 엔딩 A: 자키 살아남음 (데이터 처리 결정)                 │
│  - 엔딩 B: 자키 플랫라인 (데이터 보존/거래)                 │
│  - 두 선택지 모두 Chapter 1 종료. 다음 런은 다른 캐릭터?    │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 단편 분량 확장 (소설 레벨)

| 항목 | 현재 | 목표 |
|---|---|---|
| 단편 분량 (한글 기준) | 1,400~1,500자 | 3,000~5,000자 |
| 구조 | 도입/전개/절정/결말 (4섹션) | 동일 + **에필로그** 섹션 |
| 등장인물 대사 | 0~1개 | 2~4개 |
| 환경 묘사 | 1~2 문장 | 단락 단위 (3~5 문장) |
| 단편 ↔ 게임 연결 | `derivative_stories.md` 단편 페이지 | **게임 내 인용 + 캐릭터 동기 부여** |

### 4.4 데이터 구조 (신규)

```json
// data/story/chapters/case.json
{
  "character": "novice",
  "id": "chapter_novice",
  "title_en": "The First Jack",
  "title_ko": "첫 잭인",
  "excerpt_en": "...",  // 3000~5000 chars
  "excerpt_ko": "...",  // 3000~5000 chars
  "portrait": "art:case",
  "theme": "matrix_rain",
  "duration_ms": 12000,
  "next_screen": "HUB"
}
```

### 4.5 게임 통합 모듈

| 파일 | 변경 |
|---|---|
| `engine/original_story.py` | 챕터 dialogue 3개 추가 (CHAPTER_CASE / CHAPTER_SIL / CHAPTER_KAS) |
| `engine/state.py` | `ScreenKind.CHARACTER_SELECT`, `ScreenKind.CHAPTER` enum 추가 |
| `engine/menu.py` | character_select screen으로 분기 |
| `engine/chapter_view.py` (신규) | 단편 인용 화면 (12초 타이핑 효과) |
| `scripts/play.py` | MENU → CHARACTER_SELECT → CHAPTER → HUB → MATRIX |
| `scripts/demo.py` | 동일 |
| `data/story/chapters/*.json` | 3개 신규 |
| `tests/unit/test_chapter_view.py` (신규) | 30+ tests |
| `tests/unit/test_scenario_integration.py` (신규) | 20+ integration tests |

## 5. 결과 (Consequences)

### 긍정적
- ✅ 단편이 게임의 *진입점*이 되어 Pillar 5 강화
- ✅ 캐릭터 3명 모두 동기 부여 (왜 자키가 되었는지)
- ✅ 데모가 풀 시나리오를 시연 (캐릭터 선택 → 챕터 → 매트릭스)
- ✅ 깁슨 톤 일관성 (단편 원문 인용 + 대사)
- ✅ i18n 자산 활용도 증가 (단편 ko/en 둘 다 게임에 import)
- ✅ 대시보드 `stories.html`과 게임 내 챕터 화면이 동기화

### 부정적
- ❌ 단편 3편 분량 확장 작업 (각 30분)
- ❌ 신규 view 모듈 (chapter_view.py) — 1 세션
- ❌ 테스트 50+ 추가 — 1 세션

### 중립
- 단편 파일은 fiction 영역에 유지. 게임은 import해서 사용.
- 단편 자체는 깁슨 분석이므로 Fiction 프로젝트 영역 (AGENTS.md 룰 7 준수)

## 6. 열린 질문 (Open Questions)

1. **단편 인용 범위**: 단편 *전체* 표시 vs 발췌 1,500자 + "계속 읽기" 선택?
2. **챕터 화면 길이**: 12초 타이핑 효과 vs 플레이어 직접 페이지 넘김?
3. **재플레이 동기**: 엔딩 후 "다른 캐릭터로 다시 시작" CTA 표시?
4. **단편 인용 타이밍**: CHAPTER 화면 1회 vs HUB에서 다시 읽기 가능?

## 7. 열린 결정 사항

- [ ] 단편 인용 범위 (전체 vs 발췌)
- [ ] 챕터 화면 UX (자동 진행 vs 사용자 입력)
- [ ] 캐릭터 선택 UI (The Finn NPC vs 메뉴 옵션)

## 8. 다음 단계

사용자 결정 후:
1. `design/scenario/` 디렉토리 + Chapter 1/2/3 디자인 문서
2. 단편 3편 소설 레벨 재작성
3. `engine/chapter_view.py` (신규) + `engine/state.py` ScreenKind 추가
4. `data/story/chapters/*.json` 3개
5. `play.py` / `demo.py` 갱신
6. 테스트 50+ 추가 + 데모 검증
7. 메타 문서 (index/log/ROADMAP) 동기화

## 9. 참고

- `engine/original_story.py` — 3 캐릭터 + 6 엔딩 정의
- `Fiction/derivative/sprawl-trilogy/short-stories/` — 5편 단편
- `wiki/world/derivative_stories.md` — 단편 ↔ 게임 시스템 매핑
- `dashboard/stories.html` — 단편 페이지
- `ADR-0009` (Story/News) — meatspace 미표시 원칙
- `ADR-0010` (i18n) — en 1차, ko 보조
- `ADR-0019` (Aftermath) — 4-importance + 7인물 반응

## 결과 (Consequences)

본 ADR은 사용자 결정 (질의 응답으로 confirm, 2026-08-05)에 의해 Accepted 로 auto-convert 완료. 증거 기반 검증 통과.

**구현 증거 (2026-08-05)**: `engine/original_story.py` (17.5KB) + `data/scenes/{case,sil,kas,suit,wigan,angie,sally,3jane,neuromancer}/` 81 씬 + `data/story/chapters/` JSON. 9자 × 8 씬 + 4 ending 패턴 통합 완료.

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).
