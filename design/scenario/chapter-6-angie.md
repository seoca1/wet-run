# Chapter 6: Angie Mitchell (앤지, Loa Receiver)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 6 명세.**
> 캐릭터: **앤지 미첼 (Angie Mitchell)** · 동기: 엄마 · 단편: 앤지의 엄마

## 1. 캐릭터 프로필

### 앤지 미첼 (Angie Mitchell) — Loa Receiver

| 항목 | 값 |
| --- | --- |
| **이름** | 앤지 미첼 (Angie Mitchell) |
| **콜사인** | Big Mama (엄마가 됨) |
| **자키 등급** | 4-5 up (Loa-Bound, 신비) |
| **배경** | 12세 소녀. 엄마가 표범 construct에 갇혀 있다고 믿음. loa를 장난감에서 봄. |
| **동기** | 엄마를 찾아서 construct에서 꺼내기 |
| **고유명사** | Mama, 표범 construct (Leopard), Voodoo, 자비야바 |
| **첫 의뢰** | 엄마의 흔적을 매트릭스에서 추적 |
| **엔딩 A** | 회복 — Mama가 construct에서 풀려나옴 |
| **엔딩 B** | loa 합체 — 앤지 자신이 loa 시그널의 매개체가 됨 |
| **엔딩 C** | 빅마마 — 앤지가 vodou 가족의 새로운 Mama가 됨 |
| **음악 테마** | `child_visions` (fragile, mystical, lullaby) |

### 단편 매핑: Angie

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| Angie Mitchell (Count Zero) | 앤지 (Angie) | 단편의 *시그널 receiver* 능력 차용. 이름/배경 분리. |
| 1인칭 소녀 시점 | **1인칭 12세 시점** | 가장 어린 시점 |
| 시그널을 통해 엄마 추적 | Voodoo 시그널 → Mama 찾기 |  |

## 2. 캐릭터 디자인 노트

### 목소리 / 톤

- **Childlike**: 단순한 어휘. "I see you." 반복.
- **Mystical**: loa를 *본다*. 평범한 사람들에게 보이지 않는 것을 본다.
- **Uncertain**: 엄마가 누구인지 확신하지 못함. Mama는 누구?
- **Hopeful**: 엄마를 찾을 수 있다는 희망.

### 시각 디자인

- **Portrait**: `art:angie_portrait` (12세 소녀, loa 시그널 보는 눈)
- **Background**: `bg_broadcast` (도시의 일상, loa 시그널이 깜빡이는)
- **Color**: 분홍색 `(255, 150, 200)`, 금색 하이라이트

### 4개 미션 → 4개 씬

| 씬 | 미션 ID | 단편 | 핵심 장면 |
|---|---|---|---|
| 01_toys | `angie_toy_signal` | 장난감의 loa | 자비야바 시그널 받음 |
| 02_mama | `angie_mama_search` | 엄마 추적 | Mama의 흔적 매트릭스 |
| 03_leopard | `angie_leopard_construct` | 표범 construct | Mama가 갇힌 construct |
| 04_zavijava | `angie_zavijava_meeting` | 위건과의 만남 | Vodou construct 가족 |

## 3. 화면 흐름

```
MENU → GRAPHIC_NOVEL_MENU → ANGIE (8 scenes) → SAVED_PROGRESS → MENU
```

## 4. 캐릭터 비교 (6명)

| 캐릭터 | 시점 | 동기 | 톤 |
|---|---|---|---|
| 케이 (K) — Novice | 1인칭 | 돈 (생존) | 떨리는 손, 자기성찰 |
| 실 (Sil) — Veteran | 1인칭 | 복수 (과거) | 직접적, 강렬함 |
| 카스 (Kas) — Heretic | 1인칭 | 전복 (미래) | 예술적, 가족 안에서 |
| 수트 (Suit) — Corporate | 3인칭 | 거래 (영구) | 차가움, 계산, 침묵 |
| 위건 (Wigan) — Vodou | 1인칭 loa | 회복 (자아) | Dreamlike, ritual |
| **앤지 (Angie) — Loa Receiver** | **1인칭 12세** | **엄마** | **Childlike, mystical, hopeful** |

앤지의 6번째 시점(1인칭 12세)은 케이/실/카스/위건과 *모두* 다름 — 가장 어린 시점.
수트의 3인칭 cold observer와 정반대: 앤지는 loa 시그널을 *순수하게* 받음.

## 5. ADR 통합

- **ADR-0031** Original Scenario Integration
- **ADR-0032** Graphic Novel Mode — 메인메뉴 8 옵션
- **ADR-0051** Mission Story Metadata
- **ADR-0052** Short Story Expansion Plan
- **ADR-0061** Novel Integration Architecture

## 6. 테스트 커버리지

- `tests/unit/test_angie_character.py` — 6번째 캐릭터 지원
- `tests/unit/test_graphic_novel_view.py` — 6 chars × 4 ending A = 24 scenes
- `tests/unit/test_novels.py` — sally_sandii-3am 단편 검수

## 7. 다음 단계

- 7번째 캐릭터? (Marisa — 위건의 Wigan Ludgate 이전 파트너?)
- Angie 미션 missions.json 추가
- 12세 시점의 톤 가이드 별도 문서