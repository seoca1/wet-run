# Chapter 2: The Old Score (실, Veteran)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 2 명세.**
> 캐릭터: **실 (Sil) — Veteran** · 동기: 복수 · 단편: 루이지아나의 신

## 1. 캐릭터 프로필

### 실 (Sil) — Veteran

| 항목 | 값 |
| --- | --- |
| **이름** | 실 (Sil) |
| **콜사인** | Sil |
| **자키 등급** | 3-up (Veteran) |
| **배경** | Sense/Net 복수 런. Hammer T2. 5년 경력. |
| **동기** | Mara의 죽음. Tessier-Ashpool이 그녀를 데려갔다. 복수. |
| **고유명사** | Tessier-Ashpool (T-A, 3Jane의 가문), Hammer (ICE 등급), Mara (과거 동료) |
| **첫 의뢰** | Tessier-Ashpool 계약 (스파이) |
| **엔딩 A** | 데이터를 폭로. 천 번의 상처로 T-A를 죽인다. 복수 성공. |
| **엔딩 B** | T-A의 계약에 응한다. 침묵의 값. Mara의 죽음은 사업. |
| **음악 테마** | `cyberspace` (deeper cyberspace) |

### 단편 매핑: Marly

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| Marly Krushkhova (Count Zero) | 실 (Sil) | 단편의 *세련됨* 차용. 이름/배경 분리. |
| 3인칭 제한 | 3인칭 유지 (CHAPTER 화면) |  |
| 루이지아나 (Voudou) | Sprawl의 부두 (T-A 관련) |  |
| Josef Eigenveit (미술품 위조) | T-A 위조 계약 |  |
| 씬: 루이지아나 부두 | 씬: CHAPTER 표시 후 곧바로 HUB로 |  |

## 2. CHAPTER 화면 연출

### 2.1 화면 구성

```
┌─────────────────────────────────────────────────────────────┐
│  [상단 바]                                                    │
│   ♠F♠ The Finn's Office · CHAPTER 2                          │
│                                                              │
│  [초상화]                          [단편 본문]                │
│                                                              │
│   ◆P◆                                  Chiba의 비는          │
│   실 (Sil)                            나를 데려가지          │
│   Veteran                             않는다. 비는            │
│                                        여기서 오지 않는다.   │
│                                        Sprawl의 비는          │
│                                        다르다. — 더럽다.      │
│                                        전기로 가득하고,       │
│                                        가스와 먼지로          │
│                                        가득하고,              │
│                                        죽은 계약으로          │
│                                        가득하다.              │
│                                        ...                   │
│                                                              │
│  [하단 바]                                                    │
│   [ENTER] Continue   [SKIP] Skip   [ESC] Back                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 타이핑 효과

Chapter 1과 동일 (30ms/char, 12초 자동 진행).

### 2.3 데이터

`data/story/chapters/sil.json`:

```json
{
  "character": "veteran",
  "id": "chapter_veteran",
  "title_en": "The Old Score",
  "title_ko": "오래된 의문",
  "portrait": "art:sil",
  "theme": "cyberspace",
  "excerpt_en": "[3,000~5,000자 영문]",
  "excerpt_ko": "[3,000~5,000자 한글]",
  "duration_ms": 12000,
  "next_screen": "HUB"
}
```

## 3. HUB (의뢰 선택)

The Finn NPC 이벤트:

```
> The Finn: Tessier-Ashpool wants a spy. In. Out. Names. Dates.
>           They pay double for veterans. Hammer-class ICE on the perimeter.
>
> [1] ACCEPT — "I've been around. I know the risks."
> [2] BROWSE — "Show me other jobs."
> [3] DECLINE — "Not today."
```

**선택지 동작**:
- 1: MATRIX 진입 (watchdog_patrol 미션)
- 2: 다른 등급 미션 보기 (Tier 2)
- 3: MENU로 복귀

## 4. MATRIX (잭인 — watchdog_patrol)

### 미션: `watchdog_patrol`

| 항목 | 값 |
| --- | --- |
| ID | `watchdog_patrol` |
| 의뢰인 | The Finn (의뢰: T-A → Finn) |
| 대상 | Tessier-Ashpool subsidiary (Mid zone) |
| 목표 | 데이터 추출 (T-A 계약 목록) |
| ICE | Hammer T2 × 2~3 |
| 보상 | 200 credits |
| ZDR | 5~6 (Veteran 적합) |
| 매트릭스 노드 | 6~8 노드 |
| 데이터 형태 | T-A 계약 목록, 사내 통신 |

### 노드 진행

```
[Entry] → [T-A Perimeter] → [Watchdog] → [Inner Net] → [Data Core] → [Extract] → [Jack Out]
                       ↑                  ↑             ↑
                       Hammer T2          Hammer T2     Watchdog
```

## 5. AFTERMATH (전투 후일담)

`data/story/aftermath.json`의 `aftermath_mission_first` + `arc_advance` 트리거:

```
[4,500ms 표시]
> Dixie Flatline: "Tessier-Ashpool. That's a heavy name, cowboy.
>                  You crossed a line tonight. The fixers noticed."
```

## 6. ENDING_PROLOGUE

Dixie Flatline (construct) 등장:

```
> Dixie Flatline: "Sil. I know who you are. I knew Mara.
>                  Tessier-Ashpool took her. You know that now."
>
> [1] "I leak the data. Tessier-Ashpool dies by a thousand cuts." → 엔딩 A
> [2] "I take the contract. Tessier-Ashpool pays well for silence." → 엔딩 B
```

### 엔딩 A (Lives)

> **실이 Tessier-Ashpool의 데이터를 폭로. 복수 성공. 새로운 적 생성.**

화면 연출:
- 데이터 폭로 ASCII 애니메이션
- Dixie의 마지막 메시지: "Revenge. The oldest story in the Sprawl. Make it count."
- CTA: "Jockey Lives — 실 (Sil) — Veteran"

### 엔딩 B (Flatlines)

> **실이 Tessier-Ashpool의 계약에 응함. 마라의 죽음이 그저 사업이 됨.**

화면 연출:
- 계약 체결 ASCII 애니메이션
- Dixie의 마지막 메시지: "Then Mara's death is just business. Sprawl respects that, but Tessier-Ashpool won't."
- CTA: "Jockey Flatlines — 실 (Sil) — Veteran"

## 7. 테스트 시나리오

1. **CHARACTER_SELECT**: 메뉴 → 옵션 2 선택 → 실 캐릭터 설정
2. **CHAPTER 표시**: 12초 또는 Enter로 진행
3. **HUB 의뢰**: watchdog_patrol 자동 선택, [ACCEPT]
4. **MATRIX 노드**: 6~8 노드 순회, 데이터 추출
5. **JACK_OUT → AFTERMATH**: 4.5초 표시
6. **ENDING_PROLOGUE**: Dixie 선택지, A 또는 B
7. **엔딩 표시**: 엔딩 텍스트 + CTA

## 8. 관련 자산

- 단편: `../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_marly_louisiana-god.md`
- 미션 데이터: `data/missions/missions.json` (`watchdog_patrol`)
- 위키: `../../wiki/world/factions.md` (Tessier-Ashpool)
- 모듈: `engine/original_story.py:VETERAN_PROLOGUE_EVENT`
- 단편 페이지: `dashboard/stories.html`
