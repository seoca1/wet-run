# Chapter 7: Sally Shears (샐리, Market Operator)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 7 명세.**
> 캐릭터: **샐리 시어스 (Sally Shears)** · 동기: 시장 지배 · 단편: 로즈 호텔, 새벽 3시

## 1. 캐릭터 프로필

### 샐리 시어스 (Sally Shears) — Market Operator

| 항목 | 값 |
| --- | --- |
| **이름** | 샐리 시어스 (Sally Shears) |
| **콜사인** | Sally |
| **자키 등급** | 5-up (Master Operator) |
| **배경** | A.I. 암시장 운영. Bobby Quine과 파트너였으나 배신. voodoo loa와 거래. |
| **동기** | 시장 지배 — 모든 정보/construct의 유일한 중개상 |
| **고유명사** | A.I. 시장, Bobby Quine, Marly, Angie Mitchell, voodoo |
| **첫 의뢰** | Bobby의 A.I. 매각 |
| **엔딩 A** | 시장 지배 — 모든 A.I.의 유일한 중개상 |
| **엔딩 B** | 매각 — T-A에 자신을 매각 |
| **엔딩 C** | 파멸 — 자기 construct에게 살해됨 |
| **음악 테마** | `market_drone` (cold, electronic, business) |

### 단편 매핑: Sally

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| Sally Shears (Count Zero) | 샐리 (Sally) | 단편의 *시장 운영* 능력 차용 |
| 1인칭 빌런 시점 | **1인칭 cold operator** | 7번째 시점 — 거래만 보는 인간 |
| 3인칭 관찰자 | 1인칭 — *그러나 거래 도구로만 사용* |  |

## 2. 캐릭터 디자인 노트

### 목소리 / 톤

- **Sharp**: 문장이 짧고 정확함. 불필요한 단어 없음.
- **Business**: 모든 것이 거래. 감정 없음.
- **Calculating**: 11단계 앞을 봄.
- **Cold**: 시장 가격만 봄. 인간을 도구로 봄.

### 시각 디자인

- **Portrait**: `art:sally_neutral` (sharp, businesslike)
- **Background**: `bg_industrial` (시카고 공장, 거래소)
- **Color**: 검정+금색 `(0, 0, 0)` + `(255, 200, 100)`

### 4개 미션 → 4개 씬

| 씬 | 미션 ID | 단편 | 핵심 장면 |
|---|---|---|---|
| 01_market | `sally_market_open` | 시장 개설 | A.I. 시장 첫 거래 |
| 02_bobby | `sally_bobby_betrayal` | Bobby 배신 | Bobby의 A.I. 매각 |
| 03_marly | `sally_marly_meeting` | Marly 만남 | 시장 협상 |
| 04_angie | `sally_angie_threat` | Angie 위협 | loa 시그널러 거래 |

## 3. 화면 흐름

```
MENU → GRAPHIC_NOVEL_MENU → SALLY (8 scenes) → SAVED_PROGRESS → MENU
```

## 4. ADR 통합

- **ADR-0031** Original Scenario Integration
- **ADR-0032** Graphic Novel Mode — 메인메뉴 7~8 옵션 (Phase 7+ ADR-0040 HELP, Phase 17+ 옵트인 STATS)
- **ADR-0052** Short Story Expansion Plan

## 5. 캐릭터 비교 (7명)

| 캐릭터 | 시점 | 동기 | 톤 |
|---|---|---|---|
| 케이 (K) — Novice | 1인칭 | 돈 (생존) | 떨림 |
| 실 (Sil) — Veteran | 1인칭 | 복수 | 분노 |
| 카스 (Kas) — Heretic | 1인칭 | 전복 | 예술 |
| 수트 (Suit) — Corporate | 3인칭 | 거래 | cold |
| 위건 (Wigan) — Vodou | 1인칭 loa | 회복 | ritual |
| 앤지 (Angie) — Loa Receiver | 1인칭 12세 | 엄마 | 직관 |
| **샐리 (Sally) — Market Operator** | **1인칭 cold** | **시장 지배** | **sharp, calculating** |

샐리의 1인칭은 위건/앤지와 다른 *cold 거래자* 시점. 7번째 시점.

## 6. 테스트

- `tests/unit/test_sally_character.py` — 7번째 캐릭터 지원
- `tests/unit/test_graphic_novel_view.py` — 7 chars × 4 ending A = 28 scenes
- `tests/unit/test_novels.py` — sally_sandii-3am 단편 검수

## 7. 다음 단계

- 8번째 캐릭터? (3Jane — TA 시점)
- Sally 미션 missions.json 추가
- 시장 운영 미니게임 (Phase 8+)