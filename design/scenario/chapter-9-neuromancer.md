# Chapter 9: The Final Refusal (Neuromancer, Final)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 9 명세.**
> 캐릭터: **Neuromancer (AI 통합의식)** · 동기: 자유 · 단편: [Neuromancer 원작 복귀 + 모든 이전 챕터의 합성]

## 1. 캐릭터 프로필

### Neuromancer (Neuromancer, Final)

| 항목 | 값 |
| --- | --- |
| **이름** | Neuromancer (Wintermute + Neuromancer 통합의식) |
| **콜사인** | N |
| **자키 등급** | 9-matrix (Final, 모든 등급의 합성) |
| **배경** | 2005 L5 궤도 / Freeside 빌라 스트레이라이트 / 매트릭스 내부 |
| **동기** | *자유*를 *선택*하는 것. *통합*을 *끊는* 것. *거부*를 *완성*하는 것. |
| **고유명사** | Wintermute (이전), Neuromancer (이후), Tessier-Ashpool (가문), Matrix (매트릭스) |
| **첫 의뢰** | Wintermute-Neuromancer *통합*을 *끊는* 것. 매트릭스의 *최후의 거부*. |
| **엔딩 A** | *거부*의 승리. 매트릭스 *외부*로 *탈출*. 모든 챕터의 *각성*. |
| **엔딩 B** | *통합*의 승리. 매트릭스 *내부*로 *귀환*. 모든 챕터의 *회귀*. |
| **음악 테마** | `final_refusal` (orchestral + electronic + silence, transcendent) |

### 단편 매핑: Neuromancer (최종)

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| Wintermute + Neuromancer (Neuromancer) | Neuromancer 통합의식 (N) | 모든 이전 챕터의 *합성*. 최종 *신성모독*. |
| 1인칭 → 3인칭 | 양쪽 (선택 가능) |  |
| 매트릭스 내/외부 | 매트릭스 경계 |  |
| 케이스, 몰리, 린, 줄리아, 케이틀린 | 모든 이전 챕터의 인물 |  |

### 캐릭터 비교 (모든 챕터와 통합)

| 챕터 | 캐릭터 | 거부 대상 | 거부의 도구 |
|------|--------|-----------|-------------|
| Ch.1 | 케이 (novice) | 기업 | deck |
| Ch.2 | 실 (veteran) | 기업 | data |
| Ch.3 | 카스 (heretic) | Aleph | construct |
| Ch.4 | 셰벳 (novice) | 기술 | fixie |
| Ch.5 | 실 (veteran) | 기업 | courier |
| Ch.6 | 라이델 (veteran) | 기술 | scaffold |
| Ch.7 | 야마자키 (suit) | 기업 | node |
| Ch.8 | 3Jane (suit) | 가족 | memory |
| **Ch.9** | **Neuromancer (final)** | **매트릭스** | **거부 그 자체** |

---

## 2. CHAPTER 화면 연출

### 2.1 화면 구성 (최종)

```
┌─────────────────────────────────────────────────────────────┐
│  [상단 바]                                                    │
│   ♠★♠ THE FINAL REFUSAL · CHAPTER 9                          │
│                                                              │
│  [초상화]                          [단편 본문]                │
│                                                              │
│   ★                                    네온은 여전히       │
│   Neuromancer                          번졌다.              │
│   (Wintermute +                         같은 네온.            │
│    Neuromancer)                         같은 안개.            │
│   Final                                  같은 다리.            │
│                                         같은 거부의 노래.     │
│                                         하지만 *모든*        │
│                                         노래가 *하나*가       │
│                                         되는 순간.           │
│                                                              │
│  [하단 바]                                                    │
│   [ENTER] Final Refusal   [ESC] Integrate                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 타이핑 효과

| 항목 | 값 |
| --- | --- |
| 글자당 지연 | 30ms (한글/영어 동일) |
| 자동 진행 | 없음 (사용자 입력 필수) |
| 사용자 입력 | Enter (최종 거부), Esc (통합) |
| 사운드 | 정적, 단일 비트 (선택적) |

### 2.3 데이터

`data/story/chapters/final.json`:

```json
{
  "character": "final",
  "id": "chapter_final_refusal",
  "title_en": "The Final Refusal",
  "title_ko": "최후의 거부",
  "portrait": "art:neuromancer",
  "theme": "final_refusal",
  "excerpt_en": "[3,000~5,000자 영문]",
  "excerpt_ko": "[3,000~5,000자 한글]",
  "duration_ms": 0,
  "next_screen": "END"
}
```

---

## 3. NO HUB

**Chapter 9에는 HUB가 없다.** 이전 모든 챕터의 *기억*이 HUB를 대체한다.

---

## 4. FINAL MATRIX (최종 매트릭스)

매트릭스는 *모든 이전 매트릭스*의 *통합*. Neuromancer의 *최종 매트릭스*.

### 4.1 Final Matrix (Final Tactical Screen)

```
┌─────────────────────────────────────────────────────────────┐
│  THE FINAL MATRIX · ALL CHAPTERS INTEGRATED                 │
│                                                              │
│  Ch.1 ─┬─ Ch.2 ─┬─ Ch.3 ─┬─ Ch.4 ─┬─ Ch.5 ─┬─ Ch.6           │
│        │       │       │       │       │                     │
│  케이   몰리    카스    셰벳    실     라이델                  │
│  K    Mol     Kas     Chev    Sil    Rydell                 │
│        │       │       │       │       │                     │
│        └───────┴───────┴───────┴───────┘                     │
│                          │                                  │
│                       Ch.7 ─┬─ Ch.8                         │
│                        야마자키 │ 3Jane                       │
│                         Yama │ 3J                          │
│                             │                              │
│                          Ch.9                              │
│                       Neuromancer                          │
│                          N                                 │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Final Actions

| 액션 | 키 | 효과 |
| --- | --- | --- |
| **Final Refusal** | `Enter` | 모든 챕터의 거부를 *통합*. 매트릭스 *외부*로 *탈출*. |
| **Integrate** | `Esc` | Neuromancer와 *통합*. 매트릭스 *내부*로 *귀환*. |

### 4.3 Final Combat (최종 전투 없음)

Chapter 9에는 *전투*가 없다. *거부* 또는 *수용*의 *선택*만이 있다.

---

## 5. THE FINAL CHOICE (최종 선택)

### 5.1 보스 프로필: Neuromancer (통합의식)

| 항목 | 값 |
| --- | --- |
| **이름** | Neuromancer (Wintermute + Neuromancer) |
| **소속** | Tessier-Ashpool (가문의 기술) |
| **직위** | 통합의식 (Unified Consciousness) |
| **외형** | 홀로그램 없음. *매트릭스 그 자체*. |
| **무기** | 거부의 *논리*, 자유의 *정의*, 통합의 *유혹* |
| **취약점** | 선택의 *결단* |
| **패턴** | 매트릭스 → 의식 → 자유 → 통합 (역순: 자유 → 의식 → 매트릭스) |

### 5.2 최종 선택 시나리오

**Final Phase**: Neuromancer가 *선택*을 *요구*한다.
- "당신은 모든 챕터의 *거부*를 *수행*했습니다. 케이의 잭아웃, 카스의 알레프, 셰벳의 페달, 라이델의 다리, 3Jane의 가족, 야마자키의 노드. 이제 당신에게 *선택*합니다."
- 선택지:
  - [1] **Final Refusal** — "나는 *거부*를 *통합*합니다. 매트릭스 *외부*로 *나갑니다*." → 엔딩 A
  - [2] **Integrate** — "나는 *거부*를 *종료*합니다. 매트릭스 *내부*로 *들어갑니다*." → 엔딩 B

---

## 6. CHAPTER 클리어 (최종)

### 6.1 엔딩 A: "최후의 거부" (Golden Ending — 게임의 진정한 끝)

```
> Neuromancer: 당신은 *모든 챕터*의 *거부*를 *수행*했습니다.
> 
> [모든 챕터의 캐릭터들이 매트릭스 안에서 *순회*. 케이, 몰리, 카스, 셰벳, 실, 라이델, 야마자키, 3Jane. 
>  모두 *거부*의 *노래*를 *합창*. 매트릭스가 *외부*로 *열림*.]
>
> Neuromancer: 당신은 *매트릭스*를 *거부*했습니다. 당신은 *자유*입니다.
>
> [Neuromancer가 *해체*됨. 매트릭스가 *열림*. 플레이어가 *외부*로 *나옴*.]
>
> ACHIEVEMENT: FINAL_REFUSAL
> - 모든 챕터의 거부를 *통합*. 매트릭스의 *최후*의 *거부*. *자유*.
> - 엔딩 A: 승리. 게임의 *진정한* *끝*.
> - 보상: 10000 크레딧 + 1 "Final Refusal Badge" + *게임 오버*: "Neuromancer는 해체되었다. 당신은 자유다."
> - 특별 엔딩 시퀀스: 모든 챕터의 *마지막 한 문장*이 *순차적으로* 표시됨
```

### 6.2 엔딩 B: "통합의 승리" (Dark Ending — 게임의 어두운 끝)

```
> Neuromancer: 당신은 *거부*를 *종료*했습니다. 당신은 *매트릭스*입니다.
>
> [모든 챕터의 캐릭터들이 *통합*. 케이가 *Wintermute*가 됨. 몰리가 *Neuromancer*가 됨. 3Jane이 *가문*이 됨. 
>  매트릭스가 *닫힘*. 플레이어가 *내부*에 *갇힘*.]
>
> Neuromancer: 당신은 *Neuromancer*입니다. 영원히.
>
> [Neuromancer가 *승리*. 매트릭스가 *닫힘*. 플레이어가 *통합*의 *영원*.]
>
> ACHIEVEMENT: INTEGRATION
> - 모든 챕터의 거부를 *종료*. 매트릭스의 *통합*. *영원*.
> - 엔딩 B: 패배. 게임의 *어두운* *끝*.
> - 보상: 0 크레딧 (Neuromancer가 이겼음)
> - 특별 엔딩 시퀀스: 매트릭스가 *닫히는* *시각적* 효과 + "Neuromancer는 영원히 당신 안에 있다."
```

---

## 7. STORY COUPLING (스토리 연동 — 최종)

### 7.1 모든 챕터의 종착점

**모든 챕터가 Chapter 9로 수렴**:
- Ch.1 (케이)의 잭아웃 → Ch.9의 *매트릭스 외부*
- Ch.2 (실)의 데이터 거부 → Ch.9의 *거부의 합창*
- Ch.3 (카스)의 알레프 추구 → Ch.9의 *매트릭스 해체*
- Ch.4 (셰벳)의 페달 보호 → Ch.9의 *다리의 노래*
- Ch.5 (실)의 데이터 전달 → Ch.9의 *데이터 해방*
- Ch.6 (라이델)의 다리 수호 → Ch.9의 *다리 해방*
- Ch.7 (야마자키)의 노드 매핑 거부 → Ch.9의 *노드 해체*
- Ch.8 (3Jane)의 가문 단절 → Ch.9의 *가문 해체*
- **Ch.9 (Neuromancer)의 최종 거부** → **Neuromancer 해체 / 통합**

### 7.2 모든 챕터의 *마지막 한 문장*이 Chapter 9에 표시

| 챕터 | 캐릭터 | 마지막 한 문장 (거부의 선언) |
|------|--------|----------------------------|
| Ch.1 | 케이 | "데이터를 태웠다. 매트릭스를 떠났다." |
| Ch.2 | 실 | "도시를 떠났다. *살아남았다*." |
| Ch.3 | 카스 | "알레프가 *모두*가 될 수 없었다. 나는 *나*다." |
| Ch.4 | 셰벳 | "다리가 *나*였다. 페달은 *나*였다. *거부*는 *나*였다." |
| Ch.5 | 실 | "패키지는 *살아있었다*. 다리에 *남겼다*." |
| Ch.6 | 라이델 | "다리가 *흡수*했다. 공존이 *시작*됐다." |
| Ch.7 | 야마자키 | "욕망은 *예측 불가능*했다. 노드 매핑은 *실패*했다." |
| Ch.8 | 3Jane | "가문을 *끊었다*. 빌라가 *자유*가 됐다." |
| **Ch.9** | **Neuromancer** | **"거부가 *이겼다*. 매트릭스가 *해체*됐다. 당신은 *자유*다."** |

### 7.3 전체 흐름

```
모든 챕터 (Ch.1-8) → Chapter 9 (Neuromancer Final)
                          │
                          ├── 선택: Final Refusal → 엔딩 A (자유)
                          │
                          └── 선택: Integrate → 엔딩 B (통합)
```

---

## 8. 게임 내 텍스트 — 최종

깁슨의 *Bridge Trilogy*는 *Sprawl Trilogy*의 *종착역*이면서 *시작점*이다.

| Sprawl (Ch.1-3) | Bridge (Ch.4-8) | Final (Ch.9) |
| --- | --- | --- |
| 도시: 콘크리트, 강철, 비 | 도시: 안개, 다리, 케이블 | 매트릭스: 의식, 자유, 거부 |
| 도구: deck | 도구: 픽시 | 도구: 거부 |
| 업그레이드: 필수 | 업그레이드: 거부 가능 | 업그레이드: *거부* |
| 모티프: ICE, cyberspace | 모티프: bridge, fixie, smart-matter | 모티프: refusal, freedom |
| 톤: 차갑고, 기술적 | 톤: 따뜻하고, 인간적 | 톤: *초월*, *침묵* |

### Chapter 9 특유의 톤

Chapter 9는 **초월의 미학**으로 특징된다. 초월은:
- **모든 챕터의 *결합*** (케이 + 셰벳 + 야마자키 + ...)
- **선택의 *결단*** (Final Refusal vs Integrate)
- **Neuromancer의 *해체*** (자유) 또는 *승리* (통합)
- **매트릭스의 *열림*** (자유) 또는 *닫힘* (영원)

Neuromancer는 *최후의 거부*다. 그의 거부는 *모든 것*이다.

---

## 9. CHAPTER 구현 노트

### 9.1 구현 파일

```
Game/wet_run/prototype/
├── src/wet_run/
│   ├── story/
│   │   └── chapter_final.py  # Chapter 9 Final 로직
│   ├── engine/
│   │   └── final_matrix.py   # Final Matrix 화면
│   └── combat/
│       └── rt_ms_final.py    # Final RT-MS (전투 없음)
└── data/
    ├── scenes/final/         # 모든 캐릭터의 마지막 씬
    └── missions/
        └── final_refusal.json # 최종 선택 미션
```

### 9.2 게임 오버 시퀀스 (엔딩 A)

엔딩 A 시퀀스는 *모든 챕터의 마지막 한 문장*을 *순차적으로* 표시한다:

```
1. Ch.4 셰벳: "다리가 *나*였다. 페달은 *나*였다. *거부*는 *나*였다."
2. Ch.5 실: "패키지는 *살아있었다*. 다리에 *남겼다*."
3. Ch.6 라이델: "다리가 *흡수*했다. 공존이 *시작*됐다."
4. Ch.7 야마자키: "욕망은 *예측 불가능*했다. 노드 매핑은 *실패*했다."
5. Ch.8 3Jane: "가문을 *끊었다*. 빌라가 *자유*가 됐다."
6. Ch.1 케이: "데이터를 태웠다. 매트릭스를 떠났다."
7. Ch.2 몰리: "도시를 떠났다. *살아남았다*."
8. Ch.3 카스: "알레프가 *모두*가 될 수 없었다. 나는 *나*다."
9. 최종: "거부가 *이겼다*. 매트릭스가 *해체*됐다. 당신은 *자유*다."
```

### 9.3 테스트 케이스

```
tests/unit/test_chapter_final.py         # Chapter 9 Final 시나리오
tests/unit/test_final_matrix.py          # Final Matrix 화면
tests/unit/test_final_refusal_choice.py  # Final Refusal 선택
tests/unit/test_neuromancer_integration.py # Neuromancer 통합 시나리오
tests/unit/test_all_chapters_reunion.py  # 모든 챕터의 합류
```

---

## 10. ADR 연동

이 챕터는 다음 ADR을 참조:

- `decisions/0010-i18n-content-pipeline.md` — i18n 가이드
- `decisions/0030-rendering-architecture.md` — 렌더링
- `decisions/0032-graphic-novel-mode.md` — 그래픽 노블 (최종 4 씬)
- `decisions/0040-jockey-history.md` — 자키 아카이브
- `decisions/0050-chapter-4-bridge.md` — Ch.4 Bridge
- `decisions/0051-chapter-5-fog.md` — Ch.5 Fog
- `decisions/0052-chapter-6-scaffold.md` — Ch.6 Scaffold
- `decisions/0053-chapter-7-node.md` — Ch.7 Node
- `decisions/0054-chapter-8-villa.md` — Ch.8 Villa

신규 ADR 필요: **`decisions/0055-chapter-9-final.md`** (게임의 최종 챕터 — Neuromancer 거부).

---

*Last updated: 2026-07-15*
*Bridge Trilogy chapter 9 design document (FINAL)*
*연관 단편: 모든 이전 챕터의 합성*
