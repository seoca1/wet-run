# Chapter 3: The Declaration (카스, Heretic)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 3 명세.**
> 캐릭터: **카스 (Kas) — Heretic** · 동기: 전복 · 단편: 매나리사의 자정

## 1. 캐릭터 프로필

### 카스 (Kas) — Heretic

| 항목 | 값 |
| --- | --- |
| **이름** | 카스 (Kas) |
| **콜사인** | Kas |
| **자키 등급** | 5-up (Heretic) |
| **배경** | Loa 네트워크 선언. Virus T3. 흑인 예언자. |
| **동기** | "바퀴를 부수러 왔다." Tessier-Ashpool의 시스템 자체를 무너뜨리려 한다. |
| **고유명사** | Loa (부두 신), Maelcum (교부), Virus (ICE 등급), Sense/Net (계약 상대) |
| **첫 의뢰** | Sense/Net 코어 선언 (Loa 네트워크) |
| **엔딩 A** | Loa 네트워크에 선언문 배포. Sprawl이 변한다. |
| **엔딩 B** | 데이터를 자기 것으로 삼는다. Tessier-Ashpool이 된다. |
| **음악 테마** | `sense_net` (corporate fortress) |

### 단편 매핑: Kumiko

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| Kumiko Yanaka (Mona Lisa Overdrive) | 카스 (Kas) | 단편의 *냉소* 차용. 이름/배경 분리. |
| 3인칭 제한 | 3인칭 유지 (CHAPTER 화면) |  |
| Sally Sendai (영혼 전송) | Maelcum (Loa 교부) |  |
| 야나카 패밀리 (산업) | Tessier-Ashpool (자본) |  |
| 씬: 매나리사 (자정) | 씬: CHAPTER 표시 후 곧바로 HUB로 |  |

## 2. CHAPTER 화면 연출

### 2.1 화면 구성

```
┌─────────────────────────────────────────────────────────────┐
│  [상단 바]                                                    │
│   ♠F♠ The Finn's Office · CHAPTER 3                          │
│                                                              │
│  [초상화]                          [단편 본문]                │
│                                                              │
│   ◇K◇                                  Loa는                │
│   카스 (Kas)                          깨어 있다.            │
│   Heretic                             매트릭스 깊은 곳,     │
│                                        Sense/Net 코어,      │
│                                        3백만 개의 의자,      │
│                                        3백만 명의            │
│                                        카우보이,             │
│                                        3백만 명의            │
│                                        Loa 후보.             │
│                                        그들이 깨어 있다.    │
│                                        ...                   │
│                                                              │
│  [하단 바]                                                    │
│   [ENTER] Continue   [SKIP] Skip   [ESC] Back                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 타이핑 효과

Chapter 1/2와 동일.

### 2.3 데이터

`data/story/chapters/kas.json`:

```json
{
  "character": "heretic",
  "id": "chapter_heretic",
  "title_en": "The Declaration",
  "title_ko": "선언",
  "portrait": "art:kas",
  "theme": "sense_net",
  "excerpt_en": "[3,000~5,000자 영문]",
  "excerpt_ko": "[3,000~5,000자 한글]",
  "duration_ms": 12000,
  "next_screen": "HUB"
}
```

## 3. HUB (의뢰 선택)

The Finn NPC 이벤트:

```
> The Finn: Sense/Net wants a heretic. Someone to burn the system down.
>           Virus-class ICE. Loa channels open. You go in, you don't come out.
>
> [1] ACCEPT — "I'm here to burn it all down."
> [2] BROWSE — "Show me other jobs."
> [3] DECLINE — "Not today."
```

**선택지 동작**:
- 1: MATRIX 진입 (loa_broadcast 미션)
- 2: 다른 등급 미션 보기 (Tier 3)
- 3: MENU로 복귀

## 4. MATRIX (잭인 — loa_broadcast)

### 미션: `loa_broadcast`

| 항목 | 값 |
| --- | --- |
| ID | `loa_broadcast` |
| 의뢰인 | The Finn (의뢰: Sense/Net → Finn) |
| 대상 | Sense/Net (Core zone) |
| 목표 | Loa 네트워크 선언문 배포 |
| ICE | Virus T3 × 3~4 + Black ICE (보스) |
| 보상 | 500 credits |
| ZDR | 8~9 (Heretic only) |
| 매트릭스 노드 | 8~10 노드 |
| 데이터 형태 | Loa 선언문, Sense/Net 내부 통신 |

### 노드 진행

```
[Entry] → [S/N Firewall] → [Black ICE Lair] → [Inner Net] → [Loa Channel] → [Broadcast] → [Jack Out]
                  ↑                ↑                ↑             ↑
                  Virus T3         Black ICE        Virus T3      Loa Network
```

## 5. AFTERMATH (전투 후일담)

`data/story/aftermath.json`의 `arc_advance` + `zone_core_first` 트리거:

```
[5,000ms 표시]
> Maelcum: "The matrix is vast. You are small. But the small can dream,
>           and the dream is not small, cowboy."
```

## 6. ENDING_PROLOGUE

Dixie Flatline (construct) 등장:

```
> Dixie Flatline: "Kas. Maelcum told me you'd come.
>                  He says you're the one to break the wheel."
>
> [1] "I cast the data into the Loa network. The Sprawl will hear it." → 엔딩 A
> [2] "I take it for myself. Power corrupts. Always." → 엔딩 B
```

### 엔딩 A (Lives)

> **카스가 Loa 네트워크에 선언문 배포. Sprawl 변화 시작.**

화면 연출:
- Loa 네트워크 트리 ASCII 애니메이션
- Dixie의 마지막 메시지: "Then the wheel breaks. Or you do. Either way, the Sprawl changes."
- CTA: "Jockey Changes Sprawl — 카스 (Kas) — Heretic"

### 엔딩 B (Flatlines)

> **카스가 데이터를 자기 것으로 삼음. Tessier-Ashpool이 된다.**

화면 연출:
- 데이터 자기화 ASCII 애니메이션
- Dixie의 마지막 메시지: "Then you become what you hate. Tessier-Ashpool made you. Welcome home."
- CTA: "Jockey Silenced — 카스 (Kas) — Heretic"

## 7. 테스트 시나리오

1. **CHARACTER_SELECT**: 메뉴 → 옵션 3 선택 → 카스 캐릭터 설정
2. **CHAPTER 표시**: 12초 또는 Enter로 진행
3. **HUB 의뢰**: loa_broadcast 자동 선택, [ACCEPT]
4. **MATRIX 노드**: 8~10 노드 순회, Loa 채널 진입
5. **JACK_OUT → AFTERMATH**: 5초 표시
6. **ENDING_PROLOGUE**: Dixie 선택지, A 또는 B
7. **엔딩 표시**: 엔딩 텍스트 + CTA

## 8. 관련 자산

- 단편: `../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_kumiko_manarase-midnight.md`
- 미션 데이터: `data/missions/missions.json` (`loa_broadcast` - 신규)
- 위키: `../../wiki/world/factions.md` (Loa/Vodou)
- 모듈: `engine/original_story.py:HERETIC_PROLOGUE_EVENT`
- 단편 페이지: `dashboard/stories.html`
