# Chapter 5: The Fog (실, Veteran)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 5 명세.**
> 캐릭터: **실 (Sil) — Veteran** · 동기: 의무 · 단편: Tokyo Courier Run

## 1. 캐릭터 프로필

### 실 (Sil) — Veteran (Bridge Era)

| 항목 | 값 |
| --- | --- |
| **이름** | 실 (Sil) |
| **콜사인** | S |
| **자키 등급** | 5-fog (Veteran, Bridge Era) |
| **배경** | 2005 베이 에어리어. 안개 속 배달부. 픽시(fixie) 자전거. |
| **동기** | 다리가 *존재*해야 한다는 것. 다리 위의 사람들이 *살아야* 한다는 것. |
| **고유명사** | Ono-Sendai (픽시), LOVETIDE (스마트매터), Kombinat (기업), Sense/Net (메신저 네트워크) |
| **첫 의뢰** | 안개 속 데이터 키 전달. 다리 위의 모든 노드가 위험. |
| **엔딩 A** | 데이터를 다리에 남긴다. 거부의 승리. |
| **엔딩 B** | 데이터를 넘긴다. 다리는 무너진다. 기술의 승리. |
| **음악 테마** | `bridge_fog` (atmospheric, mist, alarm pulses) |

### 단편 매핑: Sil (Tokyo Courier Run)

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| 쿠리어 (Bridge Novelette) | 실 (S) | 단편의 *쿠리어 역할*만 차용. |
| 1인칭 시점 | 3인칭 제한 (실 관찰) |  |
| 픽시 (fixed-gear) 자전거 | 동일 (픽시 유지) |  |
| 신주쿠 / 칸다 / 요코초 | 동일 (도쿄 도심) |  |
| 씬: 데이터 키 배달 | 씬: HUB에서 미션 수락 후 곧바로 MATRIX |  |

### 캐릭터 비교 (Novice vs Veteran)

| 항목 | 셰벳 (Ch.4, Novice) | 실 (Ch.5, Veteran) |
| --- | --- | --- |
| **공간** | The Bridge (다리 위) | Tokyo City (도쿄 도심) |
| **도구** | 픽시 (자전거, analog) | 픽시 (자전거, Sense/Net 메신저 네트워크) |
| **모티프** | bridge, fixie | fog, courier, data |
| **거부 대상** | 업그레이드 (테크노 + 기업) | 기업 (콤비나트, LOVETIDE) |
| **수호 대상** | 다리 (공동체) | 다리 (사람들) |
| **엔딩 A** | 페달을 다리에 남긴다 | 데이터를 다리에 남긴다 |

---

## 2. CHAPTER 화면 연출

### 2.1 화면 구성

```
┌─────────────────────────────────────────────────────────────┐
│  [상단 바]                                                    │
│   ♠F♠ The Fog · CHAPTER 5                                    │
│                                                              │
│  [초상화]                          [단편 본문]                │
│                                                              │
│   ◉S◉                                  비가 네온을 번지게 했다. │
│   실 (S)                              시부야, 새벽 3시,       │
│   Veteran                            셋째 주 같은 비.         │
│   Bridge Era                         네온이 사인에서          │
│   Courier                            흘러나왔다.              │
│                                       프리스타일 블루.         │
│                                       Ono-Sendai 레드.        │
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
| 사운드 | 비, 자전거 체인, 도쿄 거리 (선택적) |

### 2.3 데이터

`data/story/chapters/fog.json`:

```json
{
  "character": "veteran",
  "id": "chapter_veteran",
  "title_en": "The Fog",
  "title_ko": "안개",
  "portrait": "art:sil",
  "theme": "bridge_fog",
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
> The Finn: Veteran run. Couriers are the new deck jockeys. The fog is the new cyberspace.
> KOMBINAT wants something delivered. LOVETIDE wants to intercept it. The Bridge wants it to stay.
> You're the courier. The package knows where it's going. Are you ready?
>
> [1] ACCEPT — "The package is alive."
> [2] BROWSE — "Show me other jobs."
> [3] DECLINE — "Not today."
```

### 의뢰 목록 (Mission Pool)

| Mission ID | Title | Character | Zone | Grade |
|------------|-------|-----------|------|-------|
| `tokyo_courier_run` | Tokyo Courier Run | veteran | surface | 3-4 |
| `bridge_pedal_handoff` | Bridge Pedal Handoff | veteran | bridge | 2-3 |
| `fog_delivery` | Fog Delivery | veteran | bridge | 2-3 |
| `shinya_yokocho` | Yokocho Meeting | veteran | surface | 3-4 |

---

## 4. MATRIX (매트릭스 진입)

매트릭스는 **안개 시뮬레이션**으로 표현된다. 칸다(Kanda)의 서버 팜, 신주쿠의 네온 거리, 요코초의 술집이 동시에 표시되는 다중 매트릭스.

### 4.1 Fog Matrix (Hybrid Tactical Screen)

```
┌─────────────────────────────────────────────────────────────┐
│  THE FOG · MISSION: tokyo_courier_run                        │
│                                                              │
│  신주쿠 ────┬──── 칸다 서버 팜 ────┬──── 요코초 술집           │
│            │                       │                          │
│  ░░░░░░░░░░ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │ ░░░░░░░░░░                  │
│  (START)   │ (TARGET)             │ (FIXER)                    │
│            │                       │                            │
│  체인: ▓▓░░░ | 노드 밀도: ▓▓▓▓░░ | 안개: ▓▓░░░░               │
│                                                              │
│  [F] Fixie Rush | [K] Kombinat Hack | [H] Hide | [ESC] Quit   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Matrix Movement (Fog RT-MS Hybrid)

| 액션 | 키 | 효과 |
| --- | --- | --- |
| **Fixie Rush** | `F` | 신주쿠 → 칸다 전진. 안개 증가. |
| **Kombinat Hack** | `K` | 칸다 노드 추출. 노드 밀도 +1. |
| **Hide** | `H` | 안개 정체. 체인 회복. |
| **Quit** | `ESC` | 미션 포기. 페널티: Kombinat 의심도 +15. |

### 4.3 Matrix Combat (Kombinat Drones)

도쿄 매트릭스에서의 전투는 RT-MS 시스템:

- **턴 기반**: 1초 = 1턴
- **적**: 콤비나트 드론 (마티즈의 보안 부대)
- **데미지 공식**: `node_density × fog_density × courier_speed`
- **승리 조건**: 드론 회피 또는 무력화, 데이터 키 전달

---

## 5. CHAPTER BOSS: The Data Package

### 5.1 보스 프로필: 마티즈 (Matisse) - 보스전

| 항목 | 값 |
| --- | --- |
| **이름** | 마티즈 (Matisse) |
| **소속** | Svar Corporation |
| **직위** | Middle Manager |
| **외형** | 검은 슈트, 흰 셔츠, 만년필 같은 넥타이 |
| **무기** | 말, 위협, 권총 (총알 없음), 드론 부대 |
| **취약점** | 거부의 *논리* |
| **패턴** | 도시 → 기업 → 스바 → 페달 (대상 축소) |

### 5.2 보스전 시나리오

**Phase 1 (대화)**: 마티즈가 데이터 키를 요구한다.
- "실. 당신의 패키지. 우리는 스바를 위해 만들었어요."
- 선택지:
  - [1] "패키지는 살아있어요." (거부)
  - [2] "50만 달러요?" (흥미)
  - [3] "다리에게 물어보세요." (공동체 위임)

**Phase 2 (협박)**: 마티즈가 드론 부대를 배치한다.
- "패키지를 주세요."
- 선택지:
  - [1] "아니요." (단호한 거부)
  - [2] (전투 개시)
  - [3] "당신은 우리를 이해 못 해요." (설득 시도)

**Phase 3 (안개)**: 안개가 짙어진다. 코드를 넘어선다.
- 자동 진행: 매트릭스가 *코드를 거부*한다. 데이터가 스스로 조직화된다.

### 5.3 보스전 클리어 조건

- **승리**: 실이 데이터를 다리에 남긴다 → 엔딩 A
- **패배**: 마티즈가 데이터를 뺏는다 → 엔딩 B

---

## 6. CHAPTER 클리어

### 6.1 엔딩 A: "거부의 승리" (Golden Ending)

```
> 실: 패키지는 살아있어요. 다리에게 물어보세요.
> 
> [안개가 짙어진다. 매트릭스가 코드를 거부한다. 데이터가 스스로 조직화된다.]
>
> 실: 내일 다리는 여전히 있을 거예요. 패키지도요.
>
> ACHIEVEMENT: FOG_CARRIER
> - 안개 속 데이터 키를 다리에 남겼다.
> - 엔딩 A: 승리.
> - 보상: 5000 크레딧 + 1 "Fog Data" 업적
> - 다음 챕터: Chapter 6 (Berry Rydell, Veteran)
```

### 6.2 엔딩 B: "기업의 승리" (Dark Ending)

```
> 마티즈: 패키지를 *받았습니다*. 당신의 다리는 곧 *없어질* 거예요.
>
> [마티즈가 떠난다. 안개가 걷힌다. 데이터가 코드로 *환원*된다.]
>
> 실: 나는... 나는 *넘겼다*. 다리는 *무너졌다*.
>
> ACHIEVEMENT: FOG_FALLEN
> - 거부의 페달을 넘겼다.
> - 엔딩 B: 패배.
> - 보상: 0 크레딧 (기업이 이겼음)
> - 다음 챕터: Chapter 6 (Berry Rydell, Veteran, but harder difficulty)
```

---

## 7. STORY COUPLING (스토리 연동)

### 7.1 이전 챕터 연동 (Ch.4)
- **Chapter 4 (셰벳, Novice)**: 셰벳이 다리 위에서 페달을 지킨다. → Chapter 5에서 실이 셰벳의 거부를 *계승*한다.
- **셰벳의 등장**: Chapter 5 도쿄 시퀀스의 안개 속에서 셰벳의 자전거 페달 윙윙거림이 메아리.

### 7.2 다음 챕터 연동 (Ch.6)
- **Chapter 6 (라이델, Veteran)**: 실이 데이터 키를 다리에 남긴 후, 라이델이 등장. → Chapter 6의 첫 씬은 *다리 위의 데이터 노드*.
- **다리 = 수호자**: Chapter 5에서 다리는 *거부의 상징*이었고, Chapter 6에서 다리는 *수호의 장소*가 된다.

### 7.3 Bridge Trilogy 전체 흐름

```
Chapter 4 (셰벳, Novice)  → Chapter 5 (실, Veteran)  → Chapter 6 (라이델, Veteran)
  페달을 지킨다              데이터를 지킨다           다리를 지킨다
  (거부의 시작)              (거부의 계승)            (거부의 완성)
       ↓                        ↓                       ↓
  Ch.7 (야마자키, Suit)    → Ch.8 (3Jane)         → Ch.9 (Neuromancer)
  노드를 해킹한다            빌라를 방문한다         신성모독을 직면한다
  (문화 선물옵션의 거부)    (기업의 본산에서)       (궁극의 거부)
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

### Chapter 5 특유의 톤

Chapter 5는 **안개의 미학**으로 특징된다. 안개는:
- **보이는 것과 보이지 않는 것의 경계를 흐림** (불확실성)
- **모든 노드를 동등하게 만듦** (수평성)
- **데이터를 흐리게 함** (은폐)
- **다리를 보호함** (요새화)

실은 안개 속에서 *살아가는* 사람. 안개가 그의 *집*이다.

---

## 9. CHAPTER 구현 노트

### 9.1 구현 파일

```
Game/wet_run/prototype/
├── src/wet_run/
│   ├── story/
│   │   └── chapter_fog.py  # Chapter 5 Fog 로직
│   ├── engine/
│   │   └── fog_matrix.py   # Fog Matrix 화면
│   └── combat/
│       └── rt_ms_fog.py    # Fog RT-MS 전투
└── data/
    ├── scenes/fog/         # 실의 4 씬 (prologue, chapter)
    └── missions/
        ├── tokyo_courier_run.json
        ├── bridge_pedal_handoff.json
        ├── fog_delivery.json
        └── shinya_yokocho.json
```

### 9.2 단편-게임 매핑

| 단편 | 챕터 | 캐릭터 | 미션 |
|------|------|--------|------|
| `tokyo-courier-run` (Short Story) | Ch.5 Intro | 실 (veteran) | (이야기 시작점) |
| `chevette-run` (Novelette) | Ch.4 | 셰벳 (novice) | `chevette_run` |
| `idoru-wedding-protocol` | Ch.5 Mission 2 | heretic | `idoru_wedding` |
| `bridge-construct` | Ch.6 (라이델) | veteran | `bridge_scaffold` |
| `kombinat-node-hack` | Ch.7 (야마자키) | suit | `kombinat_node_hack` |

### 9.3 테스트 케이스

```
tests/unit/test_chapter_fog.py          # Chapter 5 Fog 시나리오
tests/unit/test_fog_matrix.py           # Fog Matrix 화면
tests/unit/test_rt_ms_fog.py            # Fog RT-MS 전투
tests/unit/test_matisse_boss.py         # 마티즈 보스전
tests/unit/test_fog_delivery_mission.py # Fog Delivery 미션
```

---

## 10. ADR 연동

이 챕터는 다음 ADR을 참조:

- `decisions/0010-i18n-content-pipeline.md` — i18n 가이드
- `decisions/0030-rendering-architecture.md` — 렌더링
- `decisions/0032-graphic-novel-mode.md` — 그래픽 노블 (실의 4 씬)
- `decisions/0040-jockey-history.md` — 자키 아카이브
- `decisions/0050-chapter-4-bridge.md` — 이전 챕터 (Ch.4 Bridge)

신규 ADR 필요: **`decisions/0051-chapter-5-fog.md`** (Bridge Era Chapter 5 Veteran 게임플레이).

---

*Last updated: 2026-07-15*
*Bridge Trilogy chapter 5 design document*
*연관 단편: `Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-15_tokyo-courier-run.md`*
