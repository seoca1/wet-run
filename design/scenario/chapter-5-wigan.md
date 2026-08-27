# Chapter 5: Wigan Ludgate (위건, Vodou Construct)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 5 명세.**
> 캐릭터: **위건 (Wigan) — Vodou Construct** · 동기: 회복 (자아) · 단편: 위건이 본 것

## 1. 캐릭터 프로필

### 위건 (Wigan) — Vodou Construct

| 항목 | 값 |
| --- | --- |
| **이름** | 위건 (Wigan Ludgate) |
| **콜사인** | Zavijava (loa 이름) |
| **자키 등급** | 4-5 up (Loa-Bound) |
| **배경** | 죽은 자키의 의식이 vodou loa에 업로드된 construct. Bobby Quine의 deck 파트너였음. |
| **동기** | 자아의 회복. loa를 통해 본 것들을 잊지 않기. Angie's 엄마를 찾는 것. |
| **고유명사** | Zavijava (loa), Voodoo (시각 코드), Angie Mitchell (빅마마), Bobby Quine (이전 파트너) |
| **첫 의뢰** | Bobby의 시체를 찾아서 묻기 |
| **엔딩 A** | 회복 — Zavijava를 통해 자아를 회복하고 loa를 떠남 |
| **엔딩 B** | 망각 — loa에 완전히 녹아들어 자아를 잊음 |
| **엔딩 C** | 빅마마 — Angie의 엄마가 되어 vodou 가족의 일원이 됨 |
| **음악 테마** | `voodoo_drum_loop` (ritual, deep, drum-driven) |

### 단편 매핑: Wigan

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| Wigan Ludgate (Count Zero) | 위건 (Wigan) | 단편의 *시각 코드* 차용. 이름/배경 분리. |
| 1인칭 Vodou 시점 | **1인칭 loa-인플루언스드** | 카스(Kas)의 heretic과 차별화 (loa 코드 vs 가족 코드) |
| Voodoo as interface | Voodoo as **identity** |  |
| Angie Mitchell | Angie Mitchell (새 등장인물) |  |

## 2. 캐릭터 디자인 노트

### 목소리 / 톤

- **Vodou 그라머**: 문장이 의식(ritual) 형태로. loa 명명 규칙.
- **시각 코드**: 매트릭스의 데이터를 *본다* — 색깔로 해석.
- **Dreamlike**: 리얼리티가 흐릿. 자아와 loa 사이의 경계.
- **Recovering**: 자기가 누구였는지 잊지 않으려는 끊임없는 시도.

### 시각 디자인

- **Portrait**: `art:wigan_zavijava` (loa 마스크 + 깁슨의 'Zavijava' 패턴)
- **Background**: `bg_loa_channel` (vodou 시그널 인터페이스, 보라색/금색)
- **Color**: 보라색 `(180, 0, 180)`, 금색 `(255, 200, 100)` accents

### 4개 미션 → 4개 씬

| 씬 | 미션 ID | 단편 | 핵심 장면 |
|---|---|---|---|
| 01_zavijava | `wigan_zavijava` | 위건이 본 것 | Zavijava loa와 첫 만남 |
| 02_call | `wigan_call` | 위건의 호출 | Angie의 시그널 받음 |
| 03_bobby | `bobby_quine_inquest` | Bobby의 마지막 | 이전 파트너 시체 추적 |
| 04_angie | `angie_mitchell_rescue` | Angie와 만남 | Big Mama 찾기 임무 |

## 3. 화면 흐름

```
MENU → GRAPHIC_NOVEL_MENU → WIGAN (8 scenes) → SAVED_PROGRESS → MENU
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

- **ADR-0031** Original Scenario Integration
- **ADR-0032** Graphic Novel Mode — 메인메뉴 6 옵션 (Phase 7: 7 옵션, Phase 17+ 옵트인: 8 옵션)
- **ADR-0051** Mission Story Metadata
- **ADR-0052** Short Story Expansion Plan

## 5. 캐릭터 비교 (5명)

| 캐릭터 | 시점 | 동기 | 톤 |
|---|---|---|---|
| 케이 (K) — Novice | 1인칭 | 돈 (생존) | 떨리는 손, 자기성찰 |
| 실 (Sil) — Veteran | 1인칭 | 복수 (과거) | 직접적, 강렬함 |
| 카스 (Kas) — Heretic | 1인칭 | 전복 (미래) | 예술적, 가족 안에서 |
| 수트 (Suit) — Corporate | **3인칭** | 거래 (영구) | 차가움, 계산, 침묵 |
| **위건 (Wigan) — Vodou** | **1인칭 loa** | **회복 (자아)** | **Dreamlike, ritualistic** |

위건의 1인칭은 Vodou 그라머로 *감싸여 있음* — 카스의 1인칭(가족 코드)과 차이.
수트의 3인칭 cold observer와 정반대: 위건은 loa의 주관 안에서 loa를 *경험*.

## 6. 테스트 커버리지

- `tests/unit/test_wigan_character.py` — 5번째 캐릭터 지원
- `tests/unit/test_graphic_novel_view.py` — 5 chars × 4 ending A = 20 scenes
- `tests/unit/test_novels.py` — wigan_zavijava, wigan_call 단편 검수

## 7. 다음 단계

- 6번째 캐릭터? (Angie Mitchell — Vodou 시그널 receiver)
- Wigan 미션 missions.json 추가
- Wigan chapter_view chapter-5.json 활용