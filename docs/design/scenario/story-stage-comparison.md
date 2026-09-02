# 단편소설 vs 게임 상태 비교표

## 1. 개요

| 구분 | 위치 | 용도 | 파일 수 | EN 텍스트 | KO 텍스트 | 총 분량 |
|------|------|------|---------|-----------|-----------|---------|
| **단편소설 (Chapters)** | `data/story/chapters/` | NEW RUN 캐릭터 선택 후 | 3 | 4,080 | 19,637 | **23,717** |
| **그래픽 노블 씬 (Scenes)** | `data/scenes/{case,sil,kas}/` | GRAPHIC NOVEL 모드 | 24 | 44,254 | 21,220 | **65,474** |
| **게임 스테이지 (Stages)** | `src/run/state.py:Stage` | NEW RUN 미션 진행 | 10 | — | — | — |

**스토리 텍스트 총합:** EN=48,334 / KO=40,857 (약 89,191 chars)

---

## 2. 게임 상태 (Stage) — NEW RUN 미션 진행

```
PENDING → MEET_NPC → EXTRACT_DATA → DEFEAT_ICE → JACK_OUT → REWARD → COMPLETE
           ↓            ↓              ↓
         (NPC와      (데이터      (ICE 전투)
         대화)        추출)
```

| Stage | 키 | 제목 | 목표 | 비고 |
|-------|-----|------|------|------|
| `PENDING` | 대기 | Awaiting Jack-In | 없음 | Hub에서 미션 수락 대기 |
| `MEET_NPC` | npc | Meet the Construct | NPC 노드 대화 | Dixie Flatline |
| `EXTRACT_DATA` | data | Extract the Data | 데이터 노드 접근 | payload 추출 |
| `DEFEAT_ICE` | ice | Defeat the ICE | ICE 노드 전투 승리 | Wintermute 등 |
| `JACK_OUT` | none | Jack Out | disconnection 애니메이션 | 자동 진행 |
| `REWARD` | none | Mission Rewards | 보상 수령 | credits + materials |
| `DEBRIEF` | none | Debrief | 미션 요약 | 선택적 narrative |
| `COMPLETE` | none | Run Complete | 없음 | Hub 복귀 |
| `DEATH_RESTART` | none | Restart | 없음 | 사망 후 |
| `FAILED` | none | Flatline | 없음 | 미션 실패 |

---

## 3. 단편소설 (Chapter) — NEW RUN

캐릭터 선택 후 챕터 화면에서 타이핑 효과로 표시. Gibson 스타일 Opening 포함.

| 파일 | 캐릭터 | 제목 (EN) | 제목 (KO) | EN chars | KO chars | Gibson 인용 |
|------|--------|----------|----------|----------|----------|-----------|
| `case.json` | novice (케이) | **The First Jack** | 첫 잭인 | 1,406 | 4,876 | "The sky above the port was the color of television..." |
| `sil.json` | veteran (실) | **The Old Score** | 오래된 의문 | 1,359 | 6,632 | "Louisiana, address 11..." |
| `kas.json` | heretic (카스) | **The Declaration** | 선언 | 1,315 | 8,129 | "Manarase. Midnight. Shibuya, address 11..." |

**단편 합계:** EN=4,080 / KO=19,637

---

## 4. 그래픽 노블 씬 (Scene) — GRAPHIC NOVEL 모드

시각적 노블 자동재생. ASCII 배경 + 캐릭터 portrait + dialogue. 각 씬당 2~4개 dialogue 포함.

### 케이 (Case) — 8 scenes, 합계 EN=12,853 / KO=6,169

| 순서 | 파일 | 제목 (EN) | Dlg | EN | KO | Ending |
|------|------|----------|-----|-----|-----|--------|
| 1 | `01_chattos.json` | CHATTO'S 24/7 | 3 | 1,001 | 497 | A |
| 2 | `02_jackin.json` | JACK-IN | 3 | 1,128 | 579 | A |
| 3 | `03_jackout.json` | JACK-OUT | 3 | 1,217 | 609 | A |
| 4 | `04_finn.json` | THE FINN'S OFFICE | 3 | 1,154 | 596 | A |
| 5 | `05_refusal.json` | THE REFUSAL | 3 | 1,872 | 817 | **B** |
| 6 | `06_freedom.json` | FREEDOM | 3 | 2,172 | 1,006 | A |
| 7 | `07_disappear.json` | DISAPPEARANCE | 3 | 2,526 | 1,220 | A |
| 8 | `08_freeside.json` | FREESIDE | 2 | 1,783 | 845 | A |

### 실 (Sil/Marly) — 8 scenes, 합계 EN=16,003 / KO=7,696

| 순서 | 파일 | 제목 (EN) | Dlg | EN | KO | Ending |
|------|------|----------|-----|-----|-----|--------|
| 1 | `01_louisiana.json` | LOUISIANA 11 | 4 | 1,618 | 796 | A |
| 2 | `02_mask.json` | THE MASK | 3 | 1,258 | 644 | A |
| 3 | `03_payroll.json` | PAYROLL | 3 | 1,586 | 776 | A |
| 4 | `04_broadcast.json` | BROADCAST | 3 | 1,610 | 813 | A |
| 5 | `05_contract.json` | THE CONTRACT | 3 | 2,548 | 1,183 | A |
| 6 | `06_insider.json` | THE INSIDER | 3 | 2,710 | 1,258 | A |
| 7 | `07_erase.json` | ERASE | 3 | 2,790 | 1,317 | A |
| 8 | `08_blank.json` | BLANK | 2 | 1,883 | 909 | A |

### 카스 (Kas/Kumiko) — 8 scenes, 합계 EN=15,398 / KO=7,355

| 순서 | 파일 | 제목 (EN) | Dlg | EN | KO | Ending |
|------|------|----------|-----|-----|-----|--------|
| 1 | `01_manarase.json` | MANARASE MIDNIGHT | 4 | 1,729 | 825 | A |
| 2 | `02_sally.json` | SALLY SHEARER | 3 | 1,397 | 719 | A |
| 3 | `03_declaration.json` | THE DECLARATION | 3 | 1,576 | 753 | A |
| 4 | `04_wheel.json` | THE WHEEL | 3 | 1,588 | 759 | A |
| 5 | `05_silence.json` | SILENCE | 2 | 2,173 | 1,071 | A |
| 6 | `06_shadow.json` | INTO SHADOW | 3 | 2,523 | 1,220 | A |
| 7 | `07_weapon.json` | THE WEAPON | 3 | 2,794 | 1,247 | A |
| 8 | `08_burn.json` | THE BURN | 2 | 1,618 | 761 | A |

**Scenes 합계:** EN=44,254 / KO=21,220 (24 scenes, 67 dialogues)

---

## 5. 캐릭터별 스토리 플로우 vs 게임 스테이지 매핑

### 케이 (Novice)

| 순서 | 단계 | 챕터/씬 | 해당 Stage |
|------|------|---------|-----------|
| 1 | 챕터 (단편) | `case.json` The First Jack | — (선택 전) |
| 2 | 선택 | CHARACTER_SELECT (The Finn 브리핑) | PENDING |
| 3 | Hub | 미션 수락 | PENDING |
| 4 | NPC 대화 | MEET_NPC (Dixie Flatline) | MEET_NPC |
| 5 | 데이터 추출 | EXTRACT_DATA | EXTRACT_DATA |
| 6 | ICE 전투 | DEFEAT_ICE | DEFEAT_ICE |
| 7 | 잭아웃 | JACK_OUT | JACK_OUT |
| 8 | 보상 | REWARD | REWARD |
| — | GN 씬 1 | CHATTO'S 24/7 | — (GN 전용) |
| — | GN 씬 2 | JACK-IN | — |
| — | GN 씬 3 | JACK-OUT | — |
| — | GN 씬 4 | THE FINN'S OFFICE | — |
| — | GN 씬 5 | THE REFUSAL (Ending B) | — |
| ... | ... | ... | — |

### 실 (Veteran)

| 순서 | 단계 | 챕터/씬 | 해당 Stage |
|------|------|---------|-----------|
| 1 | 챕터 (단편) | `sil.json` The Old Score | — (선택 전) |
| ... | (vetran 미션 진행) | ... | MEET_NPC ~ REWARD |

### 카스 (Heretic)

| 순서 | 단계 | 챕터/씬 | 해당 Stage |
|------|------|---------|-----------|
| 1 | 챕터 (단편) | `kas.json` The Declaration | — (선택 전) |
| ... | (heretic 미션 진행) | ... | MEET_NPC ~ REWARD |

---

## 6. 화면 흐름 요약

### NEW RUN (실제 게임플레이)

```
MENU
  └─ [1] NEW RUN
        └─ CHARACTER_SELECT (The Finn: "I need a jockey...")
              ├─ 케이 → case.json (The First Jack) → HUB → Stage 흐름
              ├─ 실 → sil.json (The Old Score) → HUB → Stage 흐름
              └─ 카스 → kas.json (The Declaration) → HUB → Stage 흐름
```

### GRAPHIC NOVEL (스토리 모드)

```
MENU
  └─ [2] GRAPHIC NOVEL
        └─ GN MENU
              ├─ ALL CHARACTERS (12 scenes 랜덤 셔플)
              ├─ 케이 → Ending 선택 → 8 scenes 순차 재생
              ├─ 실 → Ending 선택 → 8 scenes 순차 재생
              └─ 카스 → Ending 선택 → 8 scenes 순차 재생
                    └─ ENDING A/B/C → SAVED_PROGRESS → MENU
```

### Story Cinematic (데모 전용 — 실제 게임 아님)

```
PROLOGUE_SCENE (Gibson opening) → BRIEFING_FINN_SCENE → Matrix → ...
(ONLY in: full_demo.py, prologue.py, visual_demo.py, text_demo.py)
```

---

## 7. 데모 스크립트와 스토리 관계

| 스크립트 | 사용하는 콘텐츠 | 비고 |
|---------|------------|------|
| `play.py` | GAMEPLAY (Stage 흐름) | GUI |
| `demo.py` | GAMEPLAY (Stage 흐름) | 텍스트 |
| `graphic_novel.py` | GN 씬 24개 | 텍스트 |
| `full_demo.py` | `PROLOGUE_SCENE` (EN=576) + `BRIEFING_FINN_SCENE` (EN=471) + GAMEPLAY | GUI |
| `prologue.py` | `PROLOGUE_SCENE` + `BRIEFING_FINN_SCENE` | GUI |
| `text_demo.py` | `PROLOGUE_SCENE` + `BRIEFING_FINN_SCENE` | 텍스트 |
| `visual_demo.py` | `PROLOGUE_SCENE` + `BRIEFING_FINN_SCENE` | GUI |

**DEPRECATED story_cinematic 분량:** `prologue_sprawl` EN=576/KO=291 + `briefing_finn_first_jack` EN=471/KO=262 = **EN=1,047 / KO=553**

---

## 8. 키 디자인 결정 사항

| 결정 | 내용 |
|------|------|
| Gibson 텍스트 위치 | 챕터 파일 (`case.json`, `sil.json`, `kas.json`)의 excerpt에만 포함 |
| Finn 브리핑 위치 | `CHARACTER_SELECT_EVENT` (original_story.py) — GAMEPLAY 진입 시 |
| Cinematic Gibson/Finn | **DEPRECATED** — 데모 스크립트에서만 사용. 실제 게임 흐름에 포함되지 않음 |
| GN Prologue 옵션 | "ALL CHARACTERS — 12 scenes"으로 rebranding (Gibson 프롤로그 아님) |
