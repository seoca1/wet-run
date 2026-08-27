# Chapter 4: The Suit (수트, Corporate)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 4 명세.**
> 캐릭터: **수트 (Suit) — Corporate** · 동기: 거래 · 단편: 아미티지 침투

## 1. 캐릭터 프로필

### 수트 (Suit) — Corporate (3인칭)

| 항목 | 값 |
| --- | --- | 
| **이름** | 수트 (Suit) |
| **콜사인** | — (3인칭 POV) |
| **자키 등급** | 4-5 up (Veteran+Heretic) |
| **배경** | Tessier-Ashpool 경영자. 콘솔 위 11년. 직접 잭인은 안 함. |
| **동기** | 거래. 계약. 침묵. 자신의 손이 아닌 construct의 손으로 움직임. |
| **고유명사** | Tessier-Ashpool, Hosaka, Wintermute, Armitage (운영자) |
| **첫 의뢰** | Armitage 침투 작전 (Sense/Net 링 내부) |
| **엔딩 A** | 계약 성사 — Hosaka 거래 성공. 침묵 유지. |
| **엔딩 B** | 배신 — T-A 가족 내부 결속. 가족이 그를 삼킴. |
| **엔딩 C** | 협상 — Wintermute와의 불가역적 거래. AI의 손이 됨. |
| **음악 테마** | `executive_drone` (cold, corporate, sterile) |

### 단편 매핑: Suit

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| Armitage (Neuromancer) | 수트 (Suit) | 단편의 *감각*만 차용. 이름/외모/배경은 분리. |
| 1인칭 시점 | **3인칭 시점** (corporate observer) | 케이/실/카스와 차별화 |
| Chiba City | Sprawl (보스턴-애틀랜타) |  |
| Console cowboy | **Console suit** (키보드 위의 사령관) |  |

## 2. 캐릭터 디자인 노트

### 목소리 / 톤

- **Cold**: 감정 없음. 숫자와 계약만.
- **Calculating**: 모든 행동은 ROI 계산 후.
- **Corporate observer**: 3인칭 limited. 자기를 "the suit"으로 지칭.
- **Transactional**: 대화 = 거래 제안. 가격 명시. 침묵의 가격도 명시.

### 시각 디자인

- **Portrait**: `art:suit_terminal` (벽 위의 그림자, 손이 콘솔 위)
- **Background**: `bg_executive_suite` (창문 없는 31층 회의실)
- **Color**: corporate gray `(120, 120, 120)`, occasional cyan `(0, 255, 255)` for highlights

### 4개 미션 → 4개 씬

| 씬 | 미션 ID | 단편 | 핵심 장면 |
|---|---|---|---|
| 01_aritage | `armitage_infiltration` | Armitage 브리핑 | Sense/Net 링 침투 작전 |
| 02_hosaka | `hosaka_extraction` | Hosaka 추출 | CEO의 construct 기억 추출 |
| 03_straylight | `ta_defection` | T-A 이탈 | Straylight 별관의 3Jane과 협상 |
| 04_wintermute | `wintermute_negotiation` | 윈터뮤트 협상 | 베를린 술집에서 Wintermute와 면담 |

## 3. 화면 흐름

```
MENU → GRAPHIC_NOVEL_MENU → SUIT (4 scenes) → SAVED_PROGRESS → MENU
```

### 키 매핑 (재생 중)

| 키 | 동작 |
| --- | --- |
| (자동) | duration_ms 후 다음 대사/씬 |
| `Space` / `→` | 현재 대사 즉시 완료 |
| `S` | 현재 씬 스킵 |
| `P` | 일시정지/재개 |
| `Esc` / `Q` | 그래픽 노블 종료 → SAVED_PROGRESS |

## 4. ADR 통합

- **ADR-0031** Original Scenario Integration — 단편 → 챕터 → 초반 플레이
- **ADR-0032** Graphic Novel Mode — 메인메뉴 5 옵션 (Phase 7+ ADR-0040: 7 옵션, Phase 17+ 옵트인: 8 옵션)
- **ADR-0052** Short Story Expansion Plan — Phase B+ 신규 미션 5편 중 4편이 Suit 미션
- **ADR-0051** Mission Story Metadata — `character_ref: "suit"` 추가

## 5. 캐릭터 비교

| 캐릭터 | 시점 | 동기 | 톤 |
|---|---|---|---|
| 케이 (K) — Novice | 1인칭 | 돈 (생존) | 떨리는 손, 자기성찰 |
| 실 (Sil) — Veteran | 1인칭 | 복수 (과거) | 직접적, 강렬함 |
| 카스 (Kas) — Heretic | 1인칭 | 전복 (미래) | 예술적, 가족 안에서 |
| **수트 (Suit) — Corporate** | **3인칭** | **거래 (영구)** | **차가움, 계산적, 침묵** |

수트는 1-3 캐릭터의 *반대*:
- 시점이 3인칭 → 옵저버
- 동기가 거래 → 감정 없음
- 끝이 침묵 → 잭아웃 없음

이 4번째 시점(3인칭 corporate)은 깁슨 톤의 *cold* 디멘션을 가장 직접적으로 표현.

## 6. 테스트 커버리지

- `tests/unit/test_graphic_novel_view.py` — 4 캐릭터 지원
- `tests/unit/test_chapter_view.py` — chapter_for_character("suit") 정상 작동
- `tests/unit/test_novels.py` — 4개 suit 단편 (armitage_infiltration, hosaka_extraction, ta_defection, wintermute_negotiation) 검수

## 7. 다음 단계

- Suit 자키 자가플레이 (데스크탑 테스트)
- 그래픽 노블 → 게임 시작 시 자동 캐릭터 선택 (Suit 기본값 옵션)
- 5번째 캐릭터? (Wigan Ludgate — Vodou construct 시점)