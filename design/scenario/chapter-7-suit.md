# Chapter 7: The Node (야마자키, Suit)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 7 명세.**
> 캐릭터: **야마자키 (Yamazaki) — Suit** · 동기: 통제 · 단편: [Kombinat Node Hack](../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-15_kombinat-node-hack.md)

## 1. 캐릭터 프로필

### 야마자키 (Yamazaki) — Suit (Bridge Era)

| 항목 | 값 |
| --- | --- |
| **이름** | 야마자키 (Yamazaki) |
| **콜사인** | Y |
| **자키 등급** | 7-node (Suit, Bridge Era) |
| **배경** | 2005 도쿄. 칸다 서버 팜 운영자. 콤비나트 노드 매퍼. |
| **동기** | 욕망을 *예측*하는 것. 노드를 *매핑*하는 것. |
| **고유명사** | Kombinat (문화 선물옵션), Yamazaki-gumi (야쿠자), Ono-Sendai (스마트매터), Kanda (서버 팜) |
| **첫 의뢰** | 레즈-레이 토이 결혼식의 노드 매핑 — 문화 선물옵션의 핵심 거래 |
| **엔딩 A** | 노드 매핑을 *거부*한다. 욕망은 *예측 불가능*. |
| **엔딩 B** | 노드 매핑을 *수용*한다. 욕망은 *증권화*됨. |
| **음악 테마** | `kombinat_node` (electronic, corporate, ambient surveillance) |

### 단편 매핑: Yamazaki (Kombinat Node Hack)

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| 야마자키 (Idoru) | 야마자키 (Y) | 단편의 *노드 매퍼 역할*만 차용. |
| 3인칭 관찰자 서사 | 동일 (3인칭 관찰자) |  |
| 칸다 서버 팜 | 동일 (칸다 서버 팜 유지) |  |
| 노드 매핑 | 동일 (노드 매핑) |  |
| 씬: 결혼 발표 노드 매핑 | 씬: HUB에서 미션 수락 후 곧바로 NODE MATRIX |  |

### 캐릭터 비교 (다른 Suit 캐릭터들과)

| 항목 | 3Jane (Ch.8, Suit) | 야마자키 (Ch.7, Suit) |
| --- | --- | --- |
| **공간** | Freeside / Villa Straylight | Kanda / Tokyo |
| **도구** | 빌라의 스마트매터 | 서버 팜의 노드 매퍼 |
| **모티프** | family, dynasty | node, desire, futarchy |
| **거부 대상** | 가족 (Tessier-Ashpool) | 기업 (Kombinat) |
| **수호 대상** | 자기 (3Jane) | 자기 (야마자키) |
| **엔딩 A** | 노드를 *파괴*한다 | 노드를 *거부*한다 |

---

## 2. CHAPTER 화면 연출

### 2.1 화면 구성

```
┌─────────────────────────────────────────────────────────────┐
│  [상단 바]                                                    │
│   ♠N♠ The Node · CHAPTER 7                                  │
│                                                              │
│  [초상화]                          [단편 본문]                │
│                                                              │
│   ◉Y◉                                  콤비나트(The Kombinat)는│
│   야마자키 (Y)                       욕망을 계획한다.       │
│   Suit                               노드(Node)가           │
│   Bridge Era                         그것을 지각한다.       │
│   Node Mapper                        다리(The Bridge)가      │
│                                      둘 다를 거부한다.       │
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
| 사운드 | 서버 팬, 데이터 윙윙거림 (선택적) |

### 2.3 데이터

`data/story/chapters/node.json`:

```json
{
  "character": "suit",
  "id": "chapter_suit_node",
  "title_en": "The Node",
  "title_ko": "노드",
  "portrait": "art:yamazaki",
  "theme": "kombinat_node",
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
> The Finn: Suit run. You're not a courier. You're not a runner. You're a mapper.
> KOMBINAT wants the Rez-Rei Toei marriage mapped. Every node. Every desire. Every giri.
> The Yamazaki-gumi wants the yakushi-8's protection. The Bridge wants both gone.
> Who do you serve?
>
> [1] ACCEPT — "I serve the node."
> [2] BROWSE — "Show me other jobs."
> [3] DECLINE — "Not today."
```

### 의뢰 목록 (Mission Pool)

| Mission ID | Title | Character | Zone | Grade |
|------------|-------|-----------|------|-------|
| `kombinat_node_hack` | Kombinat Node Hack | suit | core | 4-5 |
| `yamazaki_yokocho` | Yokocho Confession | suit | surface | 4-5 |
| `rei_toi_wedding_map` | Rei Toi Wedding Map | suit | deep | 5 |

---

## 4. NODE MATRIX (노드 매트릭스)

매트릭스는 *데이터 시뮬레이션*으로 표현된다. 칸다의 서버 팜, 도쿄의 노드 그래프가 동시에 표시되는 다중 매트릭스.

### 4.1 Node Matrix (Suit Tactical Screen)

```
┌─────────────────────────────────────────────────────────────┐
│  THE NODE · MISSION: kombinat_node_hack                      │
│                                                              │
│  칸다 팜 ────┬──── 신주쿠 노드 ────┬──── 요코초 노드          │
│             │                       │                          │
│  ░░░░░░░░░░░ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │ ░░░░░░░░░░░                │
│  (START)    │ (TARGET)             │ (FIXER)                  │
│             │                       │                          │
│  노드: ▓▓▓░░░ | 욕망 밀도: ▓▓▓▓░░ | giri: ▓▓░░░░              │
│                                                              │
│  [M] Map Node | [D] Desire Fut | [H] Hide | [ESC] Refuse     │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Node Actions

| 액션 | 키 | 효과 |
| --- | --- | --- |
| **Map Node** | `M` | 노드 매핑 진행. 욕망 밀도 +1. |
| **Desire Future** | `D` | 선물옵션 거래. 의심도 +1, 보상 ↑. |
| **Hide** | `H` | 노드 매핑 일시정지. 욕망 밀도 -1. |
| **Refuse** | `ESC` | 노드 매핑 거부. 의심도 -5, kombinat_doubt +10. |

### 4.3 Node Combat (ICE Black Programs)

노드 매트릭스에서의 전투는 RT-MS 시스템:

- **턴 기반**: 1초 = 1턴
- **적**: ICE Black programs (콤비나트 보안 부대)
- **데미지 공식**: `node_density × desire_density × yakushi_loyalty`
- **승리 조건**: ICE Black 무력화 또는 노드 매핑 완료

---

## 5. CHAPTER BOSS: The Architect

### 5.1 보스 프로필: 콤비나트 아키텍트 (The Architect)

| 항목 | 값 |
| --- | --- |
| **이름** | 아키텍트 (이름 없음, 직함만) |
| **소속** | Kombinat |
| **직위** | Chief Synthesist (AI collective) |
| **외형** | 홀로그램, Ono-Sendai 태블릿, AI 보컬 |
| **무기** | ICE Black, 문화 선물옵션, 드론 |
| **취약점** | 욕망의 *예측 불가능성* |
| **패턴** | 노드 → 욕망 → 선물옵션 → 미래 (선형 시간) |

### 5.2 보스전 시나리오

**Phase 1 (대화)**: 아키텍트가 노드 매핑의 *필요성*을 설명한다.
- "레즈-레이 토이 결혼은 *문화 선물옵션*의 핵심 거래입니다. 우리는 노드 매핑으로 *미래*를 *예측*합니다."
- 선택지:
  - [1] "예측은 *통제*입니다." (통찰)
  - [2] "미래는 *예측 불가능*합니다." (거부)
  - [3] "욕망은 *예측 불가능*합니다." (통찰)

**Phase 2 (위협)**: 아키텍트가 ICE Black 부대를 배치한다.
- "예측 불가능성은 *제거*됩니다."
- 선택지:
  - [1] "제거는 *거부*입니다." (거부)
  - [2] (전투 개시)
  - [3] "노드가 *자기*를 *매핑*합니다." (통찰)

**Phase 3 (각성)**: 레이스 토이가 *각성*한다.
- 자동 진행: 레이 토이가 자기 *욕망*을 *인지*한다. 노드 매핑이 *실패*한다.

### 5.3 보스전 클리어 조건

- **승리**: 야마자키가 노드 매핑을 *거부*한다 → 엔딩 A
- **패배**: 야마자키가 노드 매핑을 *수용*한다 → 엔딩 B

---

## 6. CHAPTER 클리어

### 6.1 엔딩 A: "거부의 승리" (Golden Ending)

```
> 야마자키: 욕망은 *예측 불가능*합니다. 당신의 *선물옵션*은 *무효*입니다.
> 
> [레이 토이가 자기 *욕망*을 *인지*한다. 노드 매핑이 *실패*한다. 욕망은 *자유*다.]
>
> 야마자키: 내일 서버는 여전히 돌 것입니다. 욕망은 여전히 *예측 불가능*합니다.
>
> ACHIEVEMENT: NODE_REFUSER
> - 노드 매핑을 *거부*했다. 욕망의 *예측 불가능성*을 *증명*했다.
> - 엔딩 A: 승리.
> - 보상: 5000 크레딧 + 1 "Node Refuser Badge"
> - 다음 챕터: Chapter 8 (3Jane, Suit)
```

### 6.2 엔딩 B: "기업의 승리" (Dark Ending)

```
> 아키텍트: 노드 매핑 *완료*. 욕망의 *증권화*가 *시작*됩니다.
>
> [레이 토이가 *코드*로 *환원*된다. 욕망이 *상품*이 된다.]
>
> 야마자키: 나는... *예측*했다. 하지만 *거부*를 *잊었다*.
>
> ACHIEVEMENT: NODE_MAPPER
> - 노드 매핑을 *수용*했다. 욕망이 *증권화*되었다.
> - 엔딩 B: 패배.
> - 보상: 0 크레딧 (기업이 이겼음)
> - 다음 챕터: Chapter 8 (3Jane, Suit, but harder difficulty)
```

---

## 7. STORY COUPLING (스토리 연동)

### 7.1 이전 챕터 연동 (Ch.6)
- **Chapter 6 (라이델, Veteran)**: 라이델이 다리를 *지킨다*. → Chapter 7에서 야마자키가 *다리 너머 도쿄*를 *매핑*한다.
- **노드 매핑의 한계**: 다리는 *예측 불가능*. 라이델의 저항이 *노드 매핑*을 *실패*하게 만든다.

### 7.2 다음 챕터 연동 (Ch.8)
- **Chapter 8 (3Jane, Suit)**: 야마자키가 노드 매핑을 거부한 후, 3Jane이 등장. → Chapter 8의 첫 씬은 *야마자키의 Kanda 서버 팜 방문*.
- **3Jane → 야마자키**: 3Jane은 야마자키의 노드 매핑이 *실패*한 것을 *기억*한다. 기억은 *가족*의 것이다.

### 7.3 Bridge Trilogy 전체 흐름

```
Chapter 4 (셰벳)  → Chapter 5 (실)  → Chapter 6 (라이델)  → Chapter 7 (야마자키)
  페달을 지킨다      데이터를 지킨다   다리를 지킨다      노드를 해킹한다
  (거부의 시작)      (거부의 계승)    (거부의 완성)       (문화 선물옵션의 거부)
       ↓                  ↓              ↓                      ↓
                                          Chapter 8 (3Jane)         → Ch.9 (Neuromancer)
                                          빌라를 방문한다             신성모독을 직면한다
                                          (기업의 본산에서)           (궁극의 거부)
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

### Chapter 7 특유의 톤

Chapter 7은 **예측의 미학**으로 특징된다. 예측은:
- **욕망을 *읽는* 행위** (문화 선물옵션의 본질)
- **노드 매핑의 *유혹*** (코드가 패턴을 인식하는 것)
- **예측 불가능성의 *증명*** (레이 토이의 각성)
- **기업의 *거부 불가능성*에 대한 *거부*** (야마자키의 선택)

야마자키는 *예측자*다. 그의 예측은 *거부*다. 거부는 *문화*다.

---

## 9. CHAPTER 구현 노트

### 9.1 구현 파일

```
Game/wet_run/prototype/
├── src/wet_run/
│   ├── story/
│   │   └── chapter_node.py  # Chapter 7 Node 로직
│   ├── engine/
│   │   └── node_matrix.py   # Node Matrix 화면
│   └── combat/
│       └── rt_ms_node.py     # Node RT-MS 전투
└── data/
    ├── scenes/node/          # 야마자키의 4 씬
    └── missions/
        ├── kombinat_node_hack.json
        ├── yamazaki_yokocho.json
        └── rei_toi_wedding_map.json
```

### 9.2 단편-게임 매핑

| 단편 | 챕터 | 캐릭터 | 미션 |
|------|------|--------|------|
| `kombinat-node-hack` (Short Story) | Ch.7 Intro | 야마자키 (suit) | (이야기 시작점) |
| `chevette-run` (Novelette) | Ch.4 | 셰벳 (novice) | `chevette_run` |
| `tokyo-courier-run` | Ch.5 | 실 (veteran) | `tokyo_courier_run` |
| `bridge-construct` | Ch.6 (라이델) | veteran | `bridge_scaffold` |

### 9.3 테스트 케이스

```
tests/unit/test_chapter_node.py          # Chapter 7 Node 시나리오
tests/unit/test_node_matrix.py           # Node Matrix 화면
tests/unit/test_rt_ms_node.py             # Node RT-MS 전투
tests/unit/test_architect_boss.py         # 아키텍트 보스전
tests/unit/test_rei_toi_wedding_map.py   # Rei Toi Wedding Map 미션
```

---

## 10. ADR 연동

이 챕터는 다음 ADR을 참조:

- `decisions/0010-i18n-content-pipeline.md` — i18n 가이드
- `decisions/0030-rendering-architecture.md` — 렌더링
- `decisions/0032-graphic-novel-mode.md` — 그래픽 노블 (야마자키의 4 씬)
- `decisions/0040-jockey-history.md` — 자키 아카이브
- `decisions/0050-chapter-4-bridge.md` — 이전 챕터 (Ch.4 Bridge)
- `decisions/0051-chapter-5-fog.md` — 이전 챕터 (Ch.5 Fog)
- `decisions/0052-chapter-6-scaffold.md` — 이전 챕터 (Ch.6 Scaffold)

신규 ADR 필요: **`decisions/0053-chapter-7-node.md`** (Bridge Era Chapter 7 Suit 게임플레이).

---

*Last updated: 2026-07-15*
*Bridge Trilogy chapter 7 design document*
*연관 단편: `Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-15_kombinat-node-hack.md`*
