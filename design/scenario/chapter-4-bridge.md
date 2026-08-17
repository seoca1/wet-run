# Chapter 4: The Bridge (셰벳, Novice)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 4 명세.**
> 캐릭터: **셰벳 워싱턴 (Chevette) — Novice** · 동기: 소속감 · 단편: [셰벳 런](../../../../Fiction/derivative/bridge-trilogy/novelettes/en/2026-07-15_chevette-run.md)

## 1. 캐릭터 프로필

### 셰벳 워싱턴 (Chevette) — Novice (Bridge Era)

| 항목 | 값 |
| --- | --- |
| **이름** | 셰벳 워싱턴 (Chevette Washington) |
| **콜사인** | C |
| **자키 등급** | 4-bridge (Novice, Bridge Era) |
| **배경** | 2005 베이 에어리어. 픽시 자전거 메신저. 금문교 서측 스팬 거주. |
| **동기** | 다리가 *나의 것*이라는 것. 다리는 업그레이드에 대한 *거부*. |
| **고유명사** | LOVETIDE (스마트매터 회사), Kombinat (문화 선물옵션 기업), Bridge (금문교 서측 스팬) |
| **첫 의뢰** | 페달에 새겨진 데이터 키 전달. 마티즈의 압박. |
| **엔딩 A** | 페달을 다리에 남긴다. 다리는 거부한다. 업그레이드 거부. |
| **엔딩 B** | 페달을 넘긴다. 다리는 해체된다. 기술 승리. |
| **음악 테마** | `bridge_resistance` (improvised jazz, fog ambience) |

### 단편 매핑: Chevette

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| Chevette Washington (Virtual Light) | 셰벳 (C) | 단편의 *거부*만 차용. 이름/외모/배경은 분리. |
| 1인칭 시점 | 1인칭 유지 (CHAPTER 화면) |  |
| 흑색 픽시 (fixed-gear) | 동일 (단순 픽시로 격하) |  |
| Bay Bridge 서측 스팬 | 동일 (금문교 서측 스팬, 즉 The Bridge) |  |
| 씬: 안개 속의 마티즈 압박 | 씬: CHAPTER 표시 후 곧바로 HUB로 |  |

### 캐릭터 비교 (다른 Novice 캐릭터들과)

| 항목 | 케이 (Ch.1, Sprawl) | 셰벳 (Ch.4, Bridge) |
| --- | --- | --- |
| **공간** | Chiba City (Sprawl) | The Bridge (Bay Area) |
| **도구** | Ono-Sendai Cyberspace 7 (deck) | Ono-Sendai Cyberspace 7 (픽시, analog) |
| **모티프** | wetware, ICE, cyberspace | bridge, fixie, smart-matter |
| **거부 대상** | 업그레이드 사이클 (기업) | 업그레이드 사이클 (테크노 + 기업) |
| **수호 대상** | Sprawl (도시) | The Bridge (공동체) |
| **엔딩 A** | 데이터를 태운다 | 페달을 다리에 남긴다 |

---

## 2. CHAPTER 화면 연출

### 2.1 화면 구성

```
┌─────────────────────────────────────────────────────────────┐
│  [상단 바]                                                    │
│   ♠B♠ The Bridge · CHAPTER 4                                │
│                                                              │
│  [초상화]                          [단편 본문]                │
│                                                              │
│   ◉C◉                                  비는 안개가 될 운명이었다.│
│   셰벳 (C)                             안개가 비가 될 운명이었다.│
│   Novice                               샌프란시스코의 하늘은      │
│   Bridge Era                           1993년의 거대한 텔레비전처럼│
│   Cyclist                              늘 죽은 채널에 맞춰져    │
│                                        있었다.                   │
│                                        ...                    │
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
| 사운드 | 안개 속 자전거 체인, 새 (선택적) |

### 2.3 데이터

`data/story/chapters/bridge.json`:

```json
{
  "character": "novice",
  "id": "chapter_bridge",
  "title_en": "The Bridge",
  "title_ko": "다리",
  "portrait": "art:chevette",
  "theme": "bridge_resistance",
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
> The Finn: The Bridge has its own economy, kid. Couriers. Fixers. Squatters.
> No chrome, no matrix, no ICE. Just the fog and the chain.
> LOVETIDE wants a piece of the bridge. Kombinat wants the whole bridge.
> And someone wants me to deliver a data key hidden in a bicycle pedal.
>
> [1] ACCEPT — "The pedal is mine. The bridge is mine."
> [2] BROWSE — "Show me other jobs."
> [3] DECLINE — "Not today."
```

### 의뢰 목록 (Mission Pool)

| Mission ID | Title | Character | Zone | Grade |
|------------|-------|-----------|------|-------|
| `tokyo_courier_run` | Tokyo Courier Run | novice | surface | 1-2 |
| `chevette_run` | Chevette Run | novice | surface | 1-2 |
| `bridge_pedal_handoff` | Bridge Pedal Handoff | novice | bridge | 1-2 |
| `fog_delivery` | Fog Delivery | novice | bridge | 1 |

---

## 4. MATRIX (매트릭스 진입)

매트릭스 진입은 **없음**. 셰벳은 데커가 아니다. 셰벳은 *라이더*다.

대신, HUB에서 미션을 수락하면 **THE BRIDGE (맵)** 화면으로 전환된다. 픽시 자전거로 다리 케이블을 따라 이동하며, **선택형 분기**를 통해 의뢰를 수행한다.

### 4.1 Bridge Map (Tactical Screen)

```
┌─────────────────────────────────────────────────────────────┐
│  THE BRIDGE · MISSION: bridge_pedal_handoff                   │
│                                                              │
│  11번 행거 ▓▓▓▓░░░░░░░░░ 7번 행거 ▓▓▓░░░░░░░░░ 3번 행거 │
│  [START]  →  ▓▓▓░░░  →  [COMBAT?]  →  ▓▓▓░░  →  [BOSS]    │
│                                                              │
│  자전거 체인: ▓▓▓▓░░ (4/5) | 안개: ▓▓▓░░░ (3/5)           │
│                                                              │
│  [F] Fixie Rush | [G] Gear Shift | [H] Hide | [ESC] Retreat    │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Bridge Movement (RT-MS Hybrid)

| 액션 | 키 | 효과 |
| --- | --- | --- |
| **Fixie Rush** | `F` | 1행거 전진. 안개 증가. |
| **Gear Shift** | `G` | 0.5행거 전진. 체인 소모. 안개 감소. |
| **Hide** | `H` | 0행거. 안개 정체. 체인 회복. |
| **Retreat** | `ESC` | 의뢰 포기. 페널티: Komabnat 의심도 +10. |

### 4.3 Bridge Combat (실시간 메시지 시스템)

다리 위 전투는 RT-MS (Real-Time with Message Speed) 시스템 사용:

- **턴 기반**: 1초 = 1턴
- **액션 선택**: 체인 펌프(F), 핸드브레이크(G), 점프(H)
- **데미지 공식**: `collision_speed × chain_tension × fog_density`
- **승리 조건**: 적(LOVETIDE 드론, 스쾃터, 마티즈 부하) 회피 또는 무력화

---

## 5. CHAPTER BOSS: The Pedal

### 5.1 보스 프로필: 마티즈 (Matisse)

| 항목 | 값 |
| --- | --- |
| **이름** | 마티즈 (Matisse) |
| **소속** | Svar Corporation |
| **직위** | Middle Manager |
| **외형** | 검은 슈트, 흰 셔츠, 만년필 같은 넥타이 |
| **무기** | 말, 위협, 권총 (권총은 총알 없음) |
| **취약점** | 거부의 *논리* |
| **패턴** | 도시 → 기업 → 스바 → 페달 (대상 축소) |

### 5.2 보스전 시나리오

**Phase 1 (대화)**: 마티즈가 페달을 요구한다.
- "셰벳 워싱턴. 당신의 페달. 우리는 스바를 위해 만들었어요."
- 선택지:
  - [1] "내 페달이에요." (거부)
  - [2] "50만 달러요?" (흥미)
  - [3] "다리에게 물어보세요." (공동체 위임)

**Phase 2 (협박)**: 마티즈가 권총을 꺼낸다.
- "페달을 주세요."
- 선택지:
  - [1] "아니요." (단호한 거부)
  - [2] (무기력 침묵)
  - [3] "당신은 우리를 이해 못 해요." (설득 시도)

**Phase 3 (안개)**: 안개가 짙어진다. 마티즈와 셰벳이 사라진다. **다리만 남는다.**
- 자동 진행: 다리가 *노래*한다. 노랫말은 *거부*.

### 5.3 보스전 클리어 조건

- **승리**: 셰벳이 페달을 다리에 남긴다 → 엔딩 A
- **패배**: 마티즈가 페달을 뺏는다 → 엔딩 B

---

## 6. CHAPTER 클리어

### 6.1 엔딩 A: "다리가 *나*였다" (Golden Ending)

```
> 셰벳: 페달은 다리의 것이에요. 당신은 내 페달을 받을 자격이 없어요.
> 
> [안개가 짙어진다. 다리가 울린다. 페달이 *노래*한다.]
>
> 셰벳: 내일 다리는 여전히 있을 거예요. 나도요.
>
> ACHIEVEMENT: BRIDGE_BUILDER
> - 다리의 거부가 *너*의 거부가 되었다.
> - 엔딩 A: 승리.
> - 보상: 3000 크레딧 + 1 "Fixie's Pedal" 업적
> - 다음 챕터: Chapter 5 (실, Veteran)
```

### 6.2 엔딩 B: "기술이 이겼다" (Dark Ending)

```
> 마티즈: 페달을 *받았습니다*. 당신의 다리는 곧 *없어질* 거예요.
>
> [마티즈가 떠난다. 안개가 걷힌다. 다리가 *운다*.]
>
> 셰벳: 나는... 나는 아무것도 못 했어요.
>
> ACHIEVEMENT: BRIDGE_FALLEN
> - 거부의 페달을 넘겼다.
> - 엔딩 B: 패배.
> - 보상: 0 크레딧 (기술이 이겼음)
> - 다음 챕터: Chapter 5 (실, Veteran, but harder difficulty)
```

---

## 7. STORY COUPLING (스토리 연동)

### 7.1 이전 챕터 연동
- **Chapter 1 (케이, Novice)**: 케이가 잭아웃한 후, Sprawl을 떠난다. → Chapter 4에서 케이는 다리 위의 스쾃터로 등장 (카메오)
- **Chapter 3 (카스, Heretic)**: 카스가 알레프를 추구하면서, 다리 위의 데이터 흔적을 만남. → Chapter 4의 안개 속에서 카스의 시그니처 등장

### 7.2 다음 챕터 연동
- **Chapter 5 (실, Veteran)**: 셰벳이 페달을 지킨 후, 실이 다리에서 *운명*을 읽음. → Chapter 5의 시놉시스에 셰벳의 거울이 등장
- **Chapter 8 (3Jane)**: 3Jane이 빌라 스트레이라이트에서, 셰벳의 *거부*를 데이터로 인식. → Chapter 8의 드림 시퀀스에 다리 이미지 등장

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

---

## 9. CHAPTER 구현 노트

### 9.1 구현 파일

```
Game/wet_run/prototype/
├── src/wet_run/
│   ├── story/
│   │   └── chapter_bridge.py  # Chapter 4 Bridge 로직
│   ├── engine/
│   │   └── bridge_map.py      # Bridge Tactical Map
│   └── combat/
│       └── rt_ms_bridge.py    # Bridge RT-MS 전투
└── data/
    ├── scenes/bridge/         # 셰벳의 4 씬 (prologue, chapter)
    └── missions/
        ├── tokyo_courier_run.json
        ├── chevette_run.json
        ├── bridge_pedal_handoff.json
        └── fog_delivery.json
```

### 9.2 단편-게임 매핑

| 단편 | 챕터 | 캐릭터 | 미션 |
|------|------|--------|------|
| `chevette-run` (Novelette) | Ch.4 Intro | 셰벳 | (이야기 시작점) |
| `tokyo-courier-run` | Ch.4 Mission 1 | novice | `tokyo_courier_run` |
| `idoru-wedding-protocol` | Ch.5 (실) | heretic | `idoru_wedding` |
| `bridge-construct` | Ch.6 (라이델) | veteran | `bridge_construct` |
| `kombinat-node-hack` | Ch.7 (야마자키) | suit | `kombinat_node_hack` |

### 9.3 테스트 케이스

```
tests/unit/test_chapter_bridge.py        # Chapter 4 Bridge 시나리오
tests/unit/test_bridge_map.py            # Bridge Tactical Map
tests/unit/test_rt_ms_bridge.py          # Bridge RT-MS 전투
tests/unit/test_bridge_pedal_boss.py     # 마티즈 보스전
tests/unit/test_bridge_pedal_handoff.py  # Handoff 미션
```

---

## 10. ADR 연동

이 챕터는 다음 ADR을 참조:

- `decisions/0010-i18n-content-pipeline.md` — i18n 가이드
- `decisions/0030-rendering-architecture.md` — 렌더링
- `decisions/0032-graphic-novel-mode.md` — 그래픽 노블 (셰벳 4 씬 자동재생)
- `decisions/0040-jockey-history.md` — 자키 아카이브

신규 ADR 필요: **`decisions/0050-chapter-4-bridge.md`** (Bridge Era 게임플레이).

---

*Last updated: 2026-07-15*
*Bridge Trilogy chapter 4 design document*
*연관 단편: `Fiction/derivative/bridge-trilogy/novelettes/en/2026-07-15_chevette-run.md`*
