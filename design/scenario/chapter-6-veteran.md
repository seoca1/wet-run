# Chapter 6: The Scaffold (라이델, Veteran)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 6 명세.**
> 캐릭터: **베리 라이델 (Berry Rydell) — Veteran** · 동기: 수호 · 단편: Bridge Construct

## 1. 캐릭터 프로필

### 베리 라이델 (Berry Rydell) — Veteran (Bridge Era)

| 항목 | 값 |
| --- | --- |
| **이름** | 베리 라이델 (Berry Rydell) |
| **콜사인** | B |
| **자키 등급** | 6-bridge (Veteran, Bridge Era) |
| **배경** | 2005 베이 에어리어. 전 Loveless 보안관. 다리 자치회 수호자. |
| **동기** | 다리를 *지키는* 것. 다리 위의 *사람들*을 *지키는* 것. |
| **고유명사** | LOVETIDE (스마트매터), Kombinat (기업), IntenSecure (보안사), Grand Seiko (기계식 시계) |
| **첫 의뢰** | 다리 자치회 = LOVETIDE 스마트매터 설치 시도 저지 |
| **엔딩 A** | 다리가 스마트매터를 *흡수*한다. 공존의 승리. |
| **엔딩 B** | 다리가 스마트매터에 *대체*된다. 기술의 승리. |
| **음악 테마** | `bridge_scaffold` (industrial, structural, fog + alarm) |

### 단편 매핑: Rydell (Bridge Construct)

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| 베리 라이델 (All Tomorrow's Parties) | 라이델 (B) | 단편의 *수호자 역할*만 차용. |
| 3인칭 제한 서사 | 동일 (3인칭 제한) |  |
| 3번 케이블 행거 | 동일 (3번 행거 유지) |  |
| Grand Seiko 기계식 시계 | 동일 |  |
| 씬: LOVETIDE 드론 배치 | 씬: HUB에서 미션 수락 후 곧바로 BRIDGE |  |

### 캐릭터 비교 (다른 Veteran 캐릭터들과)

| 항목 | 실 (Ch.5, Veteran) | 라이델 (Ch.6, Veteran) |
| --- | --- | --- |
| **공간** | Tokyo (도쿄 시티) | Bridge (다리 위) |
| **도구** | 픽시 (메신저, Sense/Net) | Grand Seiko (시계), 빈 홀스터 |
| **모티프** | courier, fog, data | bridge, scaffold, smart-matter |
| **거부 대상** | 기업 (콤비나트, LOVETIDE) | 기업 (LOVETIDE) + 기술 (스마트매터) |
| **수호 대상** | 다리 (사람들) | 다리 (공동체 + 구조) |
| **엔딩 A** | 데이터를 다리에 남긴다 | 다리가 스마트매터를 *흡수*한다 |

---

## 2. CHAPTER 화면 연출

### 2.1 화면 구성

```
┌─────────────────────────────────────────────────────────────┐
│  [상단 바]                                                    │
│   ♠B♠ The Scaffold · CHAPTER 6                               │
│                                                              │
│  [초상화]                          [단편 본문]                │
│                                                              │
│   ◉B◉                                  다리가 도시를          │
│   베리 라이델 (B)                       떠받쳤다.              │
│   Veteran                              도시는 다리를 눌렀다.  │
│   Bridge Era                                                     │
│   Scaffold Guardian                   [3번 케이블 행거에서   │
│                                       시작...]                │
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
| 사운드 | 스마트매터 진동, 케이블 윙윙거림 (선택적) |

### 2.3 데이터

`data/story/chapters/scaffold.json`:

```json
{
  "character": "veteran",
  "id": "chapter_veteran_scaffold",
  "title_en": "The Scaffold",
  "title_ko": "새들",
  "portrait": "art:rydell",
  "theme": "bridge_scaffold",
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
> The Finn: Veteran run. Loveless trained you. The Bridge is training you harder.
> LOVETIDE wants to wrap smart-matter around the Golden Gate. The squatters have their own protocol.
> You're the only one who speaks both languages. Will you speak for them?
>
> [1] ACCEPT — "The Bridge decides. Not LOVETIDE."
> [2] BROWSE — "Show me other jobs."
> [3] DECLINE — "Not today."
```

### 의뢰 목록 (Mission Pool)

| Mission ID | Title | Character | Zone | Grade |
|------------|-------|-----------|------|-------|
| `bridge_scaffold` | Bridge Scaffold | veteran | bridge | 4-5 |
| `bridge_pedal_handoff` | Bridge Pedal Handoff | veteran | bridge | 3-4 |
| `fog_delivery` | Fog Delivery | veteran | bridge | 3-4 |
| `smart_matter_defense` | Smart-Matter Defense | veteran | bridge | 4 |

---

## 4. THE BRIDGE (맵)

다리는 HUB에서 직접 접근 가능한 *지형적 무대*. 매트릭스 진입 없이 다리 위에서 직접 게임플레이.

### 4.1 Bridge Map (Tactical Screen)

```
┌─────────────────────────────────────────────────────────────┐
│  THE BRIDGE · MISSION: bridge_scaffold                       │
│                                                              │
│  11번 행거 ▓▓▓▓░░░░░░░░░ 7번 행거 ▓▓▓░░░░░░░░░ 3번 행거 │
│  [START]  →  ▓▓▓░░░  →  [COMBAT]    →  ▓▓▓░░  →  [BOSS]    │
│                                                              │
│  자전거 체인: ▓▓▓▓░░ (4/5) | 안개: ▓▓▓░░░ (3/5)           │
│                                                              │
│  [F] Fixie Rush | [S] Scaffold | [H] Hide | [ESC] Retreat    │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Bridge Actions

| 액션 | 키 | 효과 |
| --- | --- | --- |
| **Fixie Rush** | `F` | 1행거 전진. 안개 +1. |
| **Scaffold** | `S` | 스쾃터 배선 강화. 안개 -1, 체인 -1. |
| **Hide** | `H` | 0행거. 안개 정체, 체인 회복. |
| **Retreat** | `ESC` | 의뢰 포기. 다리 신뢰 -10. |

### 4.3 Bridge Combat (Smart-Matter Drones)

다리 위 전투는 RT-MS 시스템:

- **턴 기반**: 1초 = 1턴
- **적**: LOVETIDE 드론 (스마트매터 나노 구조체)
- **데미지 공식**: `bridge_integrity × fog_density × upgrade_cycles`
- **승리 조건**: 드론 무력화 + 스마트매터 패치 실패 (즉흥 배선과의 충돌)

---

## 5. CHAPTER BOSS: The Smart-Matter Architect

### 5.1 보스 프로필: LOVETIDE 수석 엔지니어

| 항목 | 값 |
| --- | --- |
| **이름** | 수석 엔지니어 (이름 없음, 직함만) |
| **소속** | LOVETIDE |
| **직위** | Senior Structural Engineer |
| **외형** | Ono-Sendai 태블릿, 작업복, 안전모 |
| **무기** | 스마트매터 드론, 즉흥 배선 차단 명령 |
| **취약점** | 다리의 *언어*를 *모르는* 것 |
| **패턴** | 기술 → 기업 → 다리 → 사람 (역순: 사람 → 다리 → 기업 → 기술) |

### 5.2 보스전 시나리오

**Phase 1 (대화)**: 수석 엔지니어가 스마트매터 설치의 *필요성*을 설명한다.
- "다리는 위험합니다. 1989년 로마 프리에타 이후. 스마트매터가 *안전*을 제공합니다."
- 선택지:
  - [1] "다리는 *이미* 안전합니다." (거부)
  - [2] "다리는 *우리가* 안전하게 합니다." (공동체)
  - [3] "당신의 안전은 *우리*의 안전이 *아닙니다*." (단호한 거부)

**Phase 2 (시공)**: 수석 엔지니어가 드론을 배치한다.
- "드론 배치를 시작합니다."
- 선택지:
  - [1] "배선을 *우리가* 강화합니다." (방어)
  - [2] (전투 개시)
  - [3] "다리가 *결정*합니다." (다리에 맡김)

**Phase 3 (공존)**: 스마트매터가 즉흥 배선과 *충돌*한다.
- 자동 진행: 다리의 신경계가 스마트매터를 *흡수*한다. 공존이 시작된다.

### 5.3 보스전 클리어 조건

- **승리**: 다리가 스마트매터를 *흡수*한다 → 엔딩 A
- **패배**: 다리가 스마트매터에 *대체*된다 → 엔딩 B

---

## 6. CHAPTER 클리어

### 6.1 엔딩 A: "다리의 승리" (Golden Ending)

```
> 라이델: 다리가 *결정*했습니다. 당신의 안전은 *우리*의 안전이 *아닙니다*.
> 
> [스마트매터가 다리의 신경계에 *동화*된다. 공존이 시작된다.]
>
> 라이델: 내일 다리는 여전히 있을 거예요. 다리가 *우리*와 함께.
>
> ACHIEVEMENT: SCAFFOLD_GUARDIAN
> - 다리가 스마트매터를 *흡수*했다. 공존의 승리.
> - 엔딩 A: 승리.
> - 보상: 4000 크레딧 + 1 "Scaffold Badge" 업적
> - 다음 챕터: Chapter 7 (야마자키, Suit)
```

### 6.2 엔딩 B: "기술의 승리" (Dark Ending)

```
> 수석 엔지니어: 스마트매터 설치 완료. 무결성 400% 향상.
>
> [드론이 다리를 *대체*한다. 다리는 무너진다. 스쾃터들은 *옮겨진다*.]
>
> 라이델: 나는... 다리를 *잃었다*.
>
> ACHIEVEMENT: BRIDGE_LOST
> - 다리가 스마트매터에 *대체*되었다. 기술의 승리.
> - 엔딩 B: 패배.
> - 보상: 0 크레딧 (기술이 이겼음)
> - 다음 챕터: Chapter 7 (야마자키, Suit, but harder difficulty)
```

---

## 7. STORY COUPLING (스토리 연동)

### 7.1 이전 챕터 연동 (Ch.5)
- **Chapter 5 (실, Veteran)**: 실이 데이터 키를 다리에 남긴다. → Chapter 6에서 라이델이 *그 데이터를 다리의 신경계에 통합*한다.
- **데이터의 이동**: 칸다 서버 팜 → 요코초 술집 → 다리 케이블 → 스마트매터 패치 → 다리 흡수.

### 7.2 다음 챕터 연동 (Ch.7)
- **Chapter 7 (야마자키, Suit)**: 라이델이 다리를 지킨 후, 야마자키가 등장. → Chapter 7은 *콤비나트의 문화 선물옵션*을 다리에서 *거부*하는 챕터.
- **다리 = 축제**: Chapter 6의 다리는 *수호*의 장소. Chapter 7의 다리는 *축제*의 장소 (All Tomorrow's Parties의 *파티*).

### 7.3 Bridge Trilogy 전체 흐름

```
Chapter 4 (셰벳, Novice)  → Chapter 5 (실, Veteran)  → Chapter 6 (라이델, Veteran)  → Chapter 7 (야마자키, Suit)
  페달을 지킨다              데이터를 지킨다           다리를 지킨다              노드를 해킹한다
  (거부의 시작)              (거부의 계승)            (거부의 완성)               (문화 선물옵션의 거부)
       ↓                        ↓                       ↓                          ↓
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

### Chapter 6 특유의 톤

Chapter 6은 **수호의 미학**으로 특징된다. 수호는:
- **다리의 신경계와 시계의 째깍거림 사이** (인간 vs 기계)
- **스마트매터와 즉흥 배선 사이** (기업 vs 공동체)
- **라이델의 빈 홀스터와 풍화된 다리 사이** (과거 vs 현재)

라이델은 *수호자*다. 그의 수호는 *기술*이 아니라 *사람*이다.

---

## 9. CHAPTER 구현 노트

### 9.1 구현 파일

```
Game/wet_run/prototype/
├── src/wet_run/
│   ├── story/
│   │   └── chapter_scaffold.py  # Chapter 6 Scaffold 로직
│   ├── engine/
│   │   └── bridge_scaffold.py   # Bridge Scaffold 화면
│   └── combat/
│       └── rt_ms_scaffold.py    # Scaffold RT-MS 전투
└── data/
    ├── scenes/scaffold/        # 라이델의 4 씬
    └── missions/
        ├── bridge_scaffold.json
        ├── bridge_pedal_handoff.json
        ├── fog_delivery.json
        └── smart_matter_defense.json
```

### 9.2 단편-게임 매핑

| 단편 | 챕터 | 캐릭터 | 미션 |
|------|------|--------|------|
| `bridge-construct` (Short Story) | Ch.6 Intro | 라이델 (veteran) | (이야기 시작점) |
| `chevette-run` (Novelette) | Ch.4 | 셰벳 (novice) | `chevette_run` |
| `tokyo-courier-run` | Ch.5 | 실 (veteran) | `tokyo_courier_run` |
| `kombinat-node-hack` | Ch.7 (야마자키) | suit | `kombinat_node_hack` |

### 9.3 테스트 케이스

```
tests/unit/test_chapter_scaffold.py    # Chapter 6 Scaffold 시나리오
tests/unit/test_bridge_scaffold_map.py  # Bridge Scaffold Map
tests/unit/test_rt_ms_scaffold.py       # Scaffold RT-MS 전투
tests/unit/test_lovetide_boss.py        # LOVETIDE 엔지니어 보스전
tests/unit/test_smart_matter_defense.py # Smart-Matter Defense 미션
```

---

## 10. ADR 연동

이 챕터는 다음 ADR을 참조:

- `decisions/0010-i18n-content-pipeline.md` — i18n 가이드
- `decisions/0030-rendering-architecture.md` — 렌더링
- `decisions/0032-graphic-novel-mode.md` — 그래픽 노블 (라이델의 4 씬)
- `decisions/0040-jockey-history.md` — 자키 아카이브
- `decisions/0050-chapter-4-bridge.md` — 이전 챕터 (Ch.4 Bridge)
- `decisions/0051-chapter-5-fog.md` — 이전 챕터 (Ch.5 Fog)

신규 ADR 필요: **`decisions/0052-chapter-6-scaffold.md`** (Bridge Era Chapter 6 Veteran 게임플레이).

---

*Last updated: 2026-07-15*
*Bridge Trilogy chapter 6 design document*
*연관 단편: `Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-15_bridge-construct.md`*
