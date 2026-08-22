# Original Scenario (오리지널 시나리오)

> **이 문서는 `decisions/0031-original-scenario-integration.md`의 디자인 명세.**
> 단편 → 챕터 → 프롤로그 → 초반 플레이를 하나의 시나리오로 통합한다.

## 1. 개요

오리지널 시나리오는 3명의 자키(케이, 실, 카스)가 각각 다른 동기로 *콘솔 카우보이*가 되어, Sense/Net의 첫 의뢰를 수행하고, 엔딩 A(생존) 또는 B(플랫라인)를 거치는 풀 한 사이클.

| 챕터 | 캐릭터 | 단편 | 동기 | 첫 의뢰 | 엔딩 |
| --- | --- | --- | --- | --- | --- |
| **1. The First Jack** | 케이 (Novice) | 잭아웃 후 30초 | 돈 | Sense/Net 데이터 추출 | A: 태움 / B: 보관 |
| **2. The Old Score** | 실 (Veteran) | 루이지아나의 신 | 복수 | Tessier-Ashpool 계약 | A: 폭로 / B: 거래 |
| **3. The Declaration** | 카스 (Heretic) | 매나리사의 자정 | 전복 | Loa 네트워크 선언 | A: 선언 / B: 흡수 |

## 2. 화면 흐름 (Screen Flow)

```
┌─────────────────────────────────────────────────────────────┐
│ 0. MENU                                                      │
│    [NEW RUN] [CONTINUE] [OPTIONS] [CREDITS]                 │
└─────────────────────────────────────────────────────────────┘
                            │ [NEW RUN]
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. CHARACTER_SELECT                                          │
│    NPC: The Finn (♠F♠)                                      │
│    "I need a jockey. Sense/Net, first run..."               │
│    1. "I'm new. I just need the money."  → 케이 (Novice)    │
│    2. "I've been around. I know the risks." → 실 (Veteran)  │
│    3. "I'm here to burn it all down."  → 카스 (Heretic)     │
│    4. "I'm looking for someone else."  → Back to menu       │
│                                                              │
│    효과: state.character_id = "novice" | "veteran" | ...     │
│    다음 화면: CHAPTER                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CHAPTER (단편 인용)                                       │
│    - 단편 3,000~5,000자 (ko + en)                            │
│    - 타이핑 효과 (50ms per char)                             │
│    - 우상단: 캐릭터 초상화 (art:case, art:marly, ...)        │
│    - 하단: [SKIP] / [CONTINUE] 키 힌트                       │
│    - 자동 진행 12초 또는 Enter로 즉시                        │
│                                                              │
│    데이터: data/story/chapters/{char}.json                  │
│    다음 화면: HUB                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. HUB (의뢰 선택)                                            │
│    - 캐릭터의 첫 의뢰 자동 선택 표시                          │
│    - The Finn: "First run, simple data extraction."          │
│    - [ACCEPT] → MATRIX                                       │
│    - [BROWSE] → 다른 의뢰 보기                                │
│                                                              │
│    다음 화면: MATRIX                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. MATRIX (잭인)                                              │
│    - Sense/Net Surface 노드 그래프                            │
│    - Wisp T1 ICE 1~2개                                       │
│    - 데이터 추출 → JACK_OUT                                  │
│                                                              │
│    다음 화면: AFTERMATH → ENDING_PROLOGUE                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. AFTERMATH (전투 후일담)                                    │
│    - first_mission 트리거 (aftermath_mission_first)         │
│    - The Finn 반응: "First jack, eh..."                      │
│    - 4,000ms 표시                                            │
│    다음 화면: ENDING_PROLOGUE                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. ENDING_PROLOGUE (엔딩 선택)                                 │
│    - 캐릭터별 NPC 등장:                                      │
│      * Novice: Dixie Flatline (construct)                    │
│      * Veteran: Dixie Flatline                              │
│      * Heretic: Dixie Flatline                              │
│    - 선택지: A 또는 B (캐릭터별)                              │
│    - 엔딩 분기                                                │
│                                                              │
│    다음 화면: ENDING (엔딩 텍스트 표시)                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. ENDING (엔딩 표시)                                         │
│    - 엔딩 A: "Jockey Lives"                                  │
│    - 엔딩 B: "Jockey Flatlines"                              │
│    - [NEW RUN] → MENU (다른 캐릭터 선택 가능)                │
│    - [BACK TO TITLE] → MENU                                  │
└─────────────────────────────────────────────────────────────┘
```

## 3. 챕터 데이터 형식

`data/story/chapters/{character}.json`:

```json
{
  "character": "novice",
  "id": "chapter_novice",
  "title_en": "The First Jack",
  "title_ko": "첫 잭인",
  "portrait": "art:case",
  "theme": "matrix_rain",
  "excerpt_en": "[3,000~5,000자 영문 발췌 또는 전문]",
  "excerpt_ko": "[3,000~5,000자 한글 번역 또는 의역]",
  "duration_ms": 12000,
  "next_screen": "HUB"
}
```

## 4. 캐릭터 ↔ 단편 매핑 (깁슨 톤 보존)

| 캐릭터 | 단편 캐릭터 | 원작 | 번역 정책 |
| --- | --- | --- | --- |
| 케이 (K) — Novice | Case | Neuromancer (1984) | 1인칭 시점, 잭아웃 직후의 감각 |
| 실 (Sil) — Veteran | Marly Krushkhova | Count Zero (1986) | 3인칭 제한, Mara의 죽음 이후 |
| 카스 (Kas) — Heretic | Kumiko Yanaka | Mona Lisa Overdrive (1988) | 3인칭 제한, Sally/Sendai의 등장 |

**중요**: 단편은 *직접* 인용/연출되는 것이 아니라, 캐릭터의 *동기*를 부여하는 *문학적 배경*으로 작동. 게임 내 대사/이벤트는 캐릭터의 목소리로 재창작.

## 5. 의존성 및 제약

- **AGENTS.md 룰 4**: 깁슨 톤, 고유명사 영어 보존, meatspace 미표시
- **AGENTS.md 룰 4.1**: 단편 원문은 `Fiction/derivative/.../short-stories/` (Fiction 프로젝트 영역). 게임은 import해서 사용만.
- **AGENTS.md 룰 7**: Fiction wiki 수정 금지. 단편도 fiction 영역.
- **ADR-0009**: meatspace는 뉴스/이야기로만 전달 (Story Archive)
- **ADR-0010**: en 1차, ko 보조, 고유명사 영어 유지
- **ADR-0019**: Aftermath 시스템 — 4-importance + 소설 인물 7명 반응

## 6. 테스트 시나리오

각 챕터에 대해:

1. **CHARACTER_SELECT 진입**: 메뉴 → 캐릭터 선택 화면 표시 확인
2. **선택지 분기**: 1, 2, 3 모두 정상 처리
3. **CHAPTER 인용**: 단편 발췌가 12초 또는 Enter로 진행
4. **데이터 연결**: 챕터 데이터 JSON이 정상 로드
5. **다음 화면**: CHAPTER → HUB 전환
6. **풀 시나리오**: MENU → CHARACTER_SELECT → CHAPTER → HUB → MATRIX → JACK_OUT → AFTERMATH → ENDING

## 7. 완료 조건 (Acceptance Criteria)

- [ ] `data/story/chapters/{case,sil,kas}.json` 3개
- [ ] `engine/chapter_view.py` 신규 — chapter 화면 렌더링
- [ ] `engine/state.py` — `ScreenKind.CHARACTER_SELECT`, `ScreenKind.CHAPTER` 추가
- [ ] `engine/menu.py` — character_select 분기
- [ ] `engine/original_story.py` — chapter dialogue 3개 추가
- [ ] `scripts/play.py` — 풀 시나리오 시연
- [ ] `scripts/demo.py` — 풀 시나리오 시연
- [ ] `tests/unit/test_chapter_view.py` — 30+ tests
- [ ] `tests/unit/test_scenario_integration.py` — 20+ tests
- [ ] 단편 3편 소설 레벨 (3,000~5,000자)
- [ ] `make all` 그린 (lint + typecheck + test)
- [ ] 메타 문서 (index/log/ROADMAP) 동기화

## 8. 다음 단계

- [`chapter-1-novice.md`](chapter-1-novice.md) — Chapter 1: 케이 (K) — Novice
- [`chapter-2-veteran.md`](chapter-2-veteran.md) — Chapter 2: 실 (Sil) — Veteran
- [`chapter-3-heretic.md`](chapter-3-heretic.md) — Chapter 3: 카스 (Kas) — Heretic
- `../../../../Fiction/derivative/sprawl-trilogy/short-stories/` — 단편 원문 (3편)
