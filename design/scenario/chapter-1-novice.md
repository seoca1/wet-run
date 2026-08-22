# Chapter 1: The First Jack (케이, Novice)

> **이 문서는 [`../scenario/README.md`](../scenario/README.md)의 Chapter 1 명세.**
> 캐릭터: **케이 (K) — Novice** · 동기: 돈 · 단편: 잭아웃 후 30초

## 1. 캐릭터 프로필

### 케이 (K) — Novice

| 항목 | 값 |
| --- | --- |
| **이름** | 케이 (K) |
| **콜사인** | K |
| **자키 등급** | 1-up (Novice) |
| **배경** | Sense/Net 첫 런. Wisp T1. 싸구려 데크. |
| **동기** | 돈이 필요하다. 가족? 약? 의문. 깊이 안 알려줌. |
| **고유명사** | Ono-Sendai (데크 모델), Sense/Net (첫 의뢰), Wisp (ICE 등급) |
| **첫 의뢰** | Sense/Net 데이터 추출. 직원 ID 목록. |
| **엔딩 A** | 데이터를 태운다. Sprawl을 떠난다. 살아남음. |
| **엔딩 B** | 데이터를 지킨다. Finn의 추적. 플랫라인. |
| **음악 테마** | `matrix_rain` (standard cyberspace) |

### 단편 매핑: Case

| 단편 캐릭터 | 게임 캐릭터 | 차이점 |
| --- | --- | --- |
| Case (Neuromancer) | 케이 (K) | 단편의 *감각*만 차용. 이름/외모/배경은 분리. |
| 1인칭 시점 | 1인칭 유지 (CHAPTER 화면) |  |
| Ono-Sendai Cyberspace 7 | 동일 (Wisp T1 격하) |  |
| Chiba City | Sprawl (보스턴-애틀랜타) |  |
| 씬: 잭아웃 직후 | 씬: CHAPTER 표시 후 곧바로 HUB로 |  |

## 2. CHAPTER 화면 연출

### 2.1 화면 구성

```
┌─────────────────────────────────────────────────────────────┐
│  [상단 바]                                                    │
│   ♠F♠ The Finn's Office · CHAPTER 1                          │
│                                                              │
│  [초상화]                          [단편 본문]                │
│                                                              │
│   ◉P◉                                  30초.                 │
│   케이 (K)                              카운트다운은         │
│   Novice                                내 머릿속 어딘가에서  │
│                                          매너리즘처럼 흘렀다. │
│                                          Ono-Sendai의         │
│                                          전극이 두피에서      │
│                                          떨어지는 동안에도,   │
│                                          내 손가락은          │
│                                          여전히 키를 두드리고 │
│                                          있었다.             │
│                                          ...                 │
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
| 사운드 | 키보드 typing sound (선택적) |

### 2.3 데이터

`data/story/chapters/case.json`:

```json
{
  "character": "novice",
  "id": "chapter_novice",
  "title_en": "The First Jack",
  "title_ko": "첫 잭인",
  "portrait": "art:case",
  "theme": "matrix_rain",
  "excerpt_en": "[3,000~5,000자 영문]",
  "excerpt_ko": "[3,000~5,000자 한글]",
  "duration_ms": 12000,
  "next_screen": "HUB"
}
```

## 3. HUB (의뢰 선택)

The Finn NPC 이벤트:

```
> The Finn: First run, simple data extraction. ICE is light. Wisp-class.
> Sense/Net payroll. Names. Dates. Nothing exotic.
>
> [1] ACCEPT — "I need the money."
> [2] BROWSE — "Show me other jobs."
> [3] DECLINE — "Not today."
```

**선택지 동작**:
- 1: MATRIX 진입 (first_jack 미션)
- 2: 다른 등급 미션 보기 (Tier 1만)
- 3: MENU로 복귀 (런 포기)

## 4. MATRIX (잭인 — first_jack)

### 미션: `first_jack`

| 항목 | 값 |
| --- | --- |
| ID | `first_jack` |
| 의뢰인 | The Finn |
| 대상 | Sense/Net (Surface zone) |
| 목표 | 데이터 추출 (1 노드) |
| ICE | Wisp T1 × 1~2 |
| 보상 | 50 credits |
| ZDR | 2~3 (Novice에 적합) |
| 매트릭스 노드 | 4~6 노드 |
| 데이터 형태 | 직원 ID 목록 (외관상 무의미) |

### 노드 진행

```
[Entry] → [Sense/Net Firewall] → [Data Cache] → [Extract] → [Jack Out]
                              ↑                ↑
                              Wisp T1          데이터 노드
```

## 5. AFTERMATH (전투 후일담)

`data/story/aftermath.json`의 `aftermath_mission_first` 트리거:

```
[4,000ms 표시]
> The Finn: "First jack, eh. Don't make a habit of dying.
>           The Finn pays for results, not for funerals."
```

## 6. ENDING_PROLOGUE

Dixie Flatline (construct) 등장:

```
> Dixie Flatline: "Hey cowboy. You got the data. Now what you gonna do with it?"
>
> [1] "I burn it. I just wanted the money." → 엔딩 A (Jockey Lives)
> [2] "I keep it. I might need it someday." → 엔딩 B (Jockey Flatlines)
```

### 엔딩 A (Lives)

> **케이가 데이터를 태우고 Sprawl을 떠남. 새로운 자키로 살아남음.**

화면 연출:
- 데이터 소각 ASCII 애니메이션
- Finn의 마지막 메시지: "Smart. The Sprawl has a short memory for those who don't make waves."
- CTA: "Jockey Lives — 케이 (K) — Novice"

### 엔딩 B (Flatlines)

> **케이가 데이터를 지키려다 Finn의 추적에 당함. Flatline.**

화면 연출:
- Finn의 추적자가 매트릭스에서 접근
- 마지막 메시지: "Then Finn will find you. Tonight. Maybe sooner."
- CTA: "Jockey Flatlines — 케이 (K) — Novice"

## 7. 테스트 시나리오

1. **CHARACTER_SELECT**: 메뉴 → 옵션 1 선택 → 케이 캐릭터 설정
2. **CHAPTER 표시**: 12초 또는 Enter로 진행
3. **HUB 의뢰**: first_jack 자동 선택, [ACCEPT]
4. **MATRIX 노드**: 4~6 노드 순회, 데이터 추출
5. **JACK_OUT → AFTERMATH**: 4초 표시
6. **ENDING_PROLOGUE**: Dixie 선택지, A 또는 B
7. **엔딩 표시**: 엔딩 텍스트 + CTA

## 8. 관련 자산

- 단편: `../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_case_jackout-30sec.md`
- 미션 데이터: `data/missions/missions.json` (`first_jack`)
- 위키: `../../wiki/world/cyberspace.md`
- 모듈: `engine/original_story.py:NOVICE_PROLOGUE_EVENT`
- 단편 페이지: `dashboard/stories.html`
