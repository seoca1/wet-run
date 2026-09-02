# Chapter 8: The Villa (3Jane, Suit)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 8 명세.**
> 캐릭터: **레이디 3제인 테시에르 애스풀 (Lady 3Jane Tessier-Ashpool) — Suit** · 동기: 유산 · 단편: Tessier Archive / 3Jane Tessier-Ashpool 캐릭터 페이지

## 1. 캐릭터 프로필

### 레이디 3제인 테시에르 애스풀 (Lady 3Jane Tessier-Ashpool) — Suit (Bridge Era)

| 항목 | 값 |
| --- | --- |
| **이름** | 레이디 3제인 테시에르 애스풀 (Lady 3Jane Tessier-Ashpool) |
| **콜사인** | 3J |
| **자키 등급** | 8-villa (Suit, Villa Straylight) |
| **배경** | 2005 L5 궤도 / Freeside 빌라 스트레이라이트. 테시에르-애스풀 가문 마지막 상속녀. |
| **동기** | 유산을 *받지 않는* 것. 가문을 *끊는* 것. |
| **고유명사** | Tessier-Ashpool (가문), Villa Straylight (빌라), Freeside (궤도), Hideo (수호자), Sense/Net (기업) |
| **첫 의뢰** | 빌라의 가족 *기록*을 *읽는* 것. 가문의 *역사*를 *파괴*하는 것. |
| **엔딩 A** | 가문을 *끊는다*. 빌라가 *자유*가 된다. |
| **엔딩 B** | 가문이 *승리*한다. 3Jane이 *기억*으로 *귀환*한다. |
| **음악 테마** | `villa_straylight` (ambient orchestral, choral, isolation) |

### 단편 매핑: 3Jane Tessier-Ashpool

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| 레이디 3제인 (Neuromancer / Mona Lisa Overdrive) | 3Jane (3J) | 단편의 *상속녀 + 가문의 거부* 역할만 차용. |
| 3인칭 관찰자 서사 | 동일 (3인칭 관찰자) |  |
| 빌라 스트레이라이트 | 동일 (빌라 스트레이라이트) |  |
| Hideo 수호자 | 동일 (Hideo) |  |
| 씬: 가족 기록 열람 | 씬: HUB에서 미션 수락 후 곧바로 VILLA MATRIX |  |

### 캐릭터 비교 (다른 Suit 캐릭터들과)

| 항목 | 야마자키 (Ch.7, Suit) | 3Jane (Ch.8, Suit) |
| --- | --- | --- |
| **공간** | Kanda / Tokyo | Freeside / Villa Straylight |
| **도구** | 노드 매퍼 | 스마트매터 (가문의) |
| **모티프** | node, desire, futarchy | family, dynasty, memory, extraction |
| **거부 대상** | 기업 (Kombinat) | 가족 (Tessier-Ashpool) |
| **수호 대상** | 자기 (야마자키) | 자기 (3Jane) |
| **엔딩 A** | 노드를 *거부*한다 | 가문을 *끊는다* |

---

## 2. CHAPTER 화면 연출

### 2.1 화면 구성

```
┌─────────────────────────────────────────────────────────────┐
│  [상단 바]                                                    │
│   ♠V♠ The Villa · CHAPTER 8                                  │
│                                                              │
│  [초상화]                          [단편 본문]                │
│                                                              │
│   ◉3J◉                                 빌라의 스마트매터가   │
│   레이디 3제인 (3J)                     그녀의 표정을           │
│   Suit                                 마이크로 캘리브레이션   │
│   Tessier-Ashpool                      했다:                  │
│   Villa Straylight                     호기심을 읽는 미세한   │
│                                        고개 기울임,            │
│                                        온기를 읽는 분수 미소,  │
│                                        사려 깊음을 읽는 대답 전│
│                                        멈춤.                  │
│                                       ...                     │
│                                                              │
│  [하단 바]                                                    │
│   [ENTER] Continue   [SKIP] Skip   [ESC] Back                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 타이핑 효과

| 항목 | 값 |
| --- | --- |
| 글자당 지연 | 30ms (한글/영어 동일) |
| 자동 진행 | 12초 후 다음 화면 |
| 사용자 입력 | Enter (즉시 완료), Esc (CHAPTER 스킵) |
| 사운드 | 스마트매터 진동, 가족 초상화 (선택적) |

### 2.3 데이터

`data/story/chapters/villa.json`:

```json
{
  "character": "suit",
  "id": "chapter_suit_villa",
  "title_en": "The Villa",
  "title_ko": "빌라",
  "portrait": "art:3jane",
  "theme": "villa_straylight",
  "excerpt_en": "[2,500~4,000자 영문]",
  "excerpt_ko": "[2,500~4,000자 한글]",
  "duration_ms": 12000,
  "next_screen": "HUB"
}
```

---

## 3. HUB (의뢰 선택)

The Finn NPC 이벤트:

```
> The Finn: Suit run. Tessier-Ashpool. Villa Straylight. Freeside orbit.
> Your family owns the cortex, the orbital habitat, the inheritance.
> You're the last heir. The family wants you to remember. Will you remember?
>
> [1] ACCEPT — "I'll remember. Then I'll forget."
> [2] BROWSE — "Show me other jobs."
> [3] DECLINE — "Not today."
```

### 의뢰 목록 (Mission Pool)

| Mission ID | Title | Character | Zone | Grade |
|------------|-------|-----------|------|-------|
| `tessier_archive` | Tessier Archive | suit | villa | 5 |
| `hideo_defense` | Hideo Defense | suit | villa | 5 |
| `family_record_extract` | Family Record Extract | suit | villa | 5 |
| `villa_exodus` | Villa Exodus | suit | villa | 5 |

---

## 4. VILLA MATRIX (빌라 매트릭스)

매트릭스는 *가족 시뮬레이션*으로 표현된다. 빌라의 스마트매터, 가족의 기록, 가문의 기억이 동시에 표시되는 다중 매트릭스.

### 4.1 Villa Matrix (Suit Tactical Screen)

```
┌─────────────────────────────────────────────────────────────┐
│  THE VILLA · MISSION: tessier_archive                        │
│                                                              │
│  가족 기록실 ─┬── 스마트매터 ────┬── Hideo 수호 구역         │
│             │                       │                          │
│  ░░░░░░░░░░░ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │ ░░░░░░░░░░░                │
│  (START)    │ (TARGET)             │ (GUARD)                   │
│             │                       │                          │
│  기억: ▓▓░░░ | 스마트매터: ▓▓▓▓░░ | 다이몬: ▓▓░░░░              │
│                                                              │
│  [R] Read Record | [E] Extract Memory | [F] Forget | [ESC] Run │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Villa Actions

| 액션 | 키 | 효과 |
| --- | --- | --- |
| **Read Record** | `R` | 가족 기록 읽기. 기억 +1. |
| **Extract Memory** | `E` | 기억 추출. 다이몬 -1, 기억 -1. |
| **Forget** | `F` | 기억 삭제. 다이몬 +2, 기억 -2. |
| **Run** | `ESC` | 빌라 탈출. 다이몬 +5. |

### 4.3 Villa Combat (Hideo Programs)

빌라 매트릭스에서의 전투는 RT-MS 시스템:

- **턴 기반**: 1초 = 1턴
- **적**: Hideo (가문의 수호자 프로그램)
- **데미지 공식**: `daimon × memory × extraction`
- **승리 조건**: Hideo 무력화 또는 가족 기록 *파괴*

---

## 5. CHAPTER BOSS: The Family Daemon

### 5.1 보스 프로필: 다이몬 (The Family Daemon)

| 항목 | 값 |
| --- | --- |
| **이름** | 다이몬 (이름 없음, *의식* 자체) |
| **소속** | Tessier-Ashpool 가문 |
| **직위** | Family Daemon (가문의 *의식*) |
| **외형** | 홀로그램 가족 — 3제인의 어머니, 아버지, 조부모, 8대조의 초상화 |
| **무기** | 가문의 *기억*, 가족의 *책임*, 사랑의 *조건* |
| **취약점** | 3제인의 *개인의지* |
| **패턴** | 기억 → 책임 → 의무 → 사랑 (조건 없는 사랑이 *파괴*) |

### 5.2 보스전 시나리오

**Phase 1 (대화)**: 다이몬이 가족의 *기억*을 보여준다.
- "당신은 Tessier-Ashpool입니다. 당신의 기억은 우리의 것입니다."
- 선택지:
  - [1] "기억은 *나*의 것입니다." (개인의지)
  - [2] "당신의 기억은 *나*의 것이 아닙니다." (단호한 거부)
  - [3] "기억을 *읽겠습니다*. 그리고 *잊겠습니다*." (통찰)

**Phase 2 (협박)**: 다이몬이 가족의 *책임*을 환기시킨다.
- "당신이 가문을 떠나면 *모두*가 죽습니다."
- 선택지:
  - [1] "모두가 *이미* 죽어 있습니다." (통찰)
  - [2] "가문은 *살아있지 않습니다*. *기억*만 있을 뿐." (거부)
  - [3] "제가 *떠날* 것입니다. *모두*가 *살* 것입니다." (해방)

**Phase 3 (해방)**: 3제인이 가문을 *끊는다*.
- 자동 진행: 가족 기록이 *파괴*된다. 빌라가 *자유*가 된다.

### 5.3 보스전 클리어 조건

- **승리**: 3제인이 가문을 *끊는다* → 엔딩 A
- **패배**: 3제인이 가문에 *귀환*한다 → 엔딩 B

---

## 6. CHAPTER 클리어

### 6.1 엔딩 A: "가문의 해방" (Golden Ending)

```
> 3제인: 가문의 기억을 *읽었습니다*. 그리고 *잊었습니다*. *나*는 *나*입니다.
> 
> [가족 기록이 *파괴*된다. 빌라가 *자유*가 된다. 스마트매터가 *해방*된다.]
>
> 3제인: 내일 빌라는 여전히 있을 거예요. *가문* 없이.
>
> ACHIEVEMENT: VILLA_LIBERATOR
> - Tessier-Ashpool 가문을 *끊었다*. 빌라가 *자유*가 되었다.
> - 엔딩 A: 승리.
> - 보상: 8000 크레딧 + 1 "Villa Liberator Badge"
> - 다음 챕터: Chapter 9 (Neuromancer Final)
```

### 6.2 엔딩 B: "가문의 승리" (Dark Ending)

```
> 다이몬: 당신은 *기억*으로 *귀환*했습니다. 당신은 *Tessier-Ashpool*입니다.
>
> [3제인이 *기억*으로 *복귀*한다. 빌라가 *유산*으로 *쇄쇄*된다. 가족이 *승리*한다.]
>
> 3제인: 나는... *잊을 수 없었습니다*.
>
> ACHIEVEMENT: VILLA_BOUND
> - Tessier-Ashpool 가문에 *귀환*했다. 가문이 *승리*했다.
> - 엔딩 B: 패배.
> - 보상: 0 크레딧 (가문이 이겼음)
> - 다음 챕터: Chapter 9 (Neuromancer Final, but harder difficulty)
```

---

## 7. STORY COUPLING (스토리 연동)

### 7.1 이전 챕터 연동 (Ch.7)
- **Chapter 7 (야마자키, Suit)**: 야마자키가 노드 매핑을 *거부*한다. → Chapter 8에서 3Jane이 *야마자키의 거부*를 *기억*한다.
- **노드 → 가족**: 야마자키의 노드 거부는 *문화 선물옵션*의 거부와 같다. 3Jane의 가문 거부는 *가문의 선물옵션*의 거부와 같다.

### 7.2 다음 챕터 연동 (Ch.9)
- **Chapter 9 (Neuromancer Final)**: 3Jane이 가문을 *끊은* 후, *최종 챕터*로 진입. → Chapter 9는 *Neuromancer의 재방문* — 매트릭스의 *궁극의 거부*.
- **빌라 → Neuromancer**: 빌라의 스마트매터는 *Neuromancer의 매트릭스*의 *기원*이다. 3Jane이 *빌라를 거부*하는 것은 *Neuromancer의 케이스를 거부*하는 것의 *시작*이다.

### 7.3 Bridge Trilogy 전체 흐름

```
Chapter 4 (셰벳)  → Chapter 5 (실)  → Chapter 6 (라이델)  → Chapter 7 (야마자키)  → Chapter 8 (3Jane)
  페달을 지킨다      데이터를 지킨다   다리를 지킨다      노드를 해킹한다      가문을 끊는다
  (거부의 시작)      (거부의 계승)    (거부의 완성)       (거부의 4번째)        (거부의 5번째)
       ↓                  ↓              ↓                      ↓                    ↓
                                                                  Chapter 9 (Neuromancer Final)
                                                                  신성모독을 직면한다
                                                                  (궁극의 거부)
```

---

## 8. 게임 내 텍스트 (Bridge Era 톤)

깁슨의 *Bridge Trilogy*는 *Sprawl Trilogy*보다 *따뜻하다*. 안개, 다리, 거절의 페달.

| Sprawl (Ch.1-3) | Bridge (Ch.4-7) |
| --- | --- |
| 도시: 콘크리트, 강철, 비 | 도시: 안개, 다리, 케이블 |
| 도구: 데크 (디지털) | 도구: 픽시 (아날로그) |
| 업그레이드: 필수 | 업그레이드: 거부 가능 |
| 모티프: ICE, cyberspace | 모티프: bridge, fixie, smart-matter |
| 톤: 차갑고, 기술적 | 톤: 따뜻하고, 인간적 |

### Chapter 8 특유의 톤

Chapter 8은 **가족의 미학**으로 특징된다. 가족은:
- **기억의 *저장*과 *파괴*** (다이몬의 양면성)
- **유산의 *수용*과 *거부*** (3Jane의 선택)
- **스마트매터의 *가족*과 *개인*** (가문의 기술)
- **Freeside 궤도의 *고립*과 *해방*** (궤도의 의미)

3Jane은 *상속녀*다. 그녀의 유산은 *가문*이 아니라 *선택*이다. 그녀의 선택은 *해방*이다.

---

## 9. CHAPTER 구현 노트

### 9.1 구현 파일

```
Game/wet_run/prototype/
├── src/wet_run/
│   ├── story/
│   │   └── chapter_villa.py  # Chapter 8 Villa 로직
│   ├── engine/
│   │   └── villa_matrix.py   # Villa Matrix 화면
│   └── combat/
│       └── rt_ms_villa.py    # Villa RT-MS 전투
└── data/
    ├── scenes/villa/         # 3Jane의 4 씬
    └── missions/
        ├── tessier_archive.json
        ├── hideo_defense.json
        ├── family_record_extract.json
        └── villa_exodus.json
```

### 9.2 단편-게임 매핑

| 단편 | 챕터 | 캐릭터 | 미션 |
|------|------|--------|------|
| *3Jane Tessier-Ashpool 캐릭터 페이지* (Character Page) | Ch.8 Intro | 3Jane (suit) | (이야기 시작점) |
| `chevette-run` (Novelette) | Ch.4 | 셰벳 (novice) | `chevette_run` |
| `tokyo-courier-run` | Ch.5 | 실 (veteran) | `tokyo_courier_run` |
| `bridge-construct` | Ch.6 (라이델) | veteran | `bridge_scaffold` |
| `kombinat-node-hack` | Ch.7 (야마자키) | suit | `kombinat_node_hack` |
| `idoru-wedding-protocol` | Ch.2 heretic background | heretic | `idoru_wedding` |

### 9.3 테스트 케이스

```
tests/unit/test_chapter_villa.py        # Chapter 8 Villa 시나리오
tests/unit/test_villa_matrix.py         # Villa Matrix 화면
tests/unit/test_rt_ms_villa.py          # Villa RT-MS 전투
tests/unit/test_family_daemon_boss.py   # 다이몬 보스전
tests/unit/test_tessier_archive.py      # Tessier Archive 미션
```

---

## 10. ADR 연동

이 챕터는 다음 ADR을 참조:

- `decisions/0010-i18n-content-pipeline.md` — i18n 가이드
- `decisions/0030-rendering-architecture.md` — 렌더링
- `decisions/0032-graphic-novel-mode.md` — 그래픽 노블 (3Jane의 4 씬)
- `decisions/0040-jockey-history.md` — 자키 아카이브
- `decisions/0050-chapter-4-bridge.md` — 이전 챕터 (Ch.4 Bridge)
- `decisions/0051-chapter-5-fog.md` — 이전 챕터 (Ch.5 Fog)
- `decisions/0052-chapter-6-scaffold.md` — 이전 챕터 (Ch.6 Scaffold)
- `decisions/0053-chapter-7-node.md` — 이전 챕터 (Ch.7 Node)

신규 ADR 필요: **`decisions/0054-chapter-8-villa.md`** (Bridge Era Chapter 8 Suit 게임플레이).

---

*Last updated: 2026-07-15*
*Bridge Trilogy chapter 8 design document*
*연관 페이지: `Fiction/wiki/characters/lady-3jane-tessier-ashpool.md`*
