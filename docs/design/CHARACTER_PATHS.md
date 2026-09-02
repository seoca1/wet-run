# 캐릭터별 진행 경로 (Character Playthrough Paths)

> **문서 버전**: 0.7.0
> **최종 업데이트**: 2026-07-04
> **관련**: `design/systems/stage_structure.json`, `design/story/prologue_data.json`, `design/scenario/SALVATION_PHASE_INTEGRATION.md`

---

## 1. 개요

### 1.1 캐릭터 구성 (9명, 2026-07-04 기준)

| ID | 이름 | 아키타입 | 시점 | 동기 | 톤 | Deck Tier |
|---|---|---|---|---|---|---|
| `novice` | 케이 (K) | Novice | 1인칭 | 빚 (생존) | 떨리는 손, 자기성찰 | T1 (Wisp) |
| `veteran` | 실 (Sil) | Veteran | 1인칭 | 복수 (과거) | 직접적, 강렬함 | T2 (Hammer) |
| `heretic` | 카스 (Kas) | Herethic | 1인칭 | 전복 (미래) | 예술적, 가족 안에서 | T3 bio (Viral Sermon) |
| `suit` | 스위트 (Suit) | Corporate | **3인칭** | 거래 (영구) | 차가움, 계산, 침묵 | T2-T3 |
| `wigan` | 위건 (Wigan) | Vodou Construct | 1인칭 loa | 회복 (자아) | Dreamlike, ritualistic | T2-T3 |
| `angie` | 앤지 (Angie) | Loa Receiver | **1인칭 12세** | 엄마 | Childlike, mystical | T2-T3 (Loa-Bound) |
| `sally` | 샐리 (Sally) | Market Operator | **1인칭 cold** | **시장 지배** | **sharp, calculating** | T5-T6 (Master) |
| `3jane` | 3Jane (Tessier-Ashpool) | Family Heir | 1인칭 aristocratic | 가족 통합 | royal | T5-T6 |
| `neuromancer` | Neuromancer | Merged AI | **1인칭 AI** | 초월 | vast, clinical | T6+ (AI-Ascended) |

### 1.2 디자인 비교 (7자)

| 차원 | 케이 | 실 | 카스 | 수트 | 위건 | 앤지 | 샐리 |
|---|---|---|---|---|---|---|---|
| **Gibson 원작** | Case | Marly | Kumiko | Armitage | Wigan Ludgate | Angie Mitchell | Sally Shears |
| **등장 작품** | Neuromancer | Count Zero | Mona Lisa Overdrive | Neuromancer | Count Zero | Count Zero | Count Zero |
| **시점** | 1인칭 | 1인칭 | 1인칭 | **3인칭** | 1인칭 loa | 1인칭 12세 | **1인칭 cold** |
| **동기** | 돈 (생존) | 복수 (T-A) | 전복 (T-A 가족) | 거래 (가족) | 자아 회복 | 엄마 추적 | **시장 지배** |
| **자키 등급** | 1-up | 2-3 up | 3-4 up | 4-5 up | 4-5 up (Loa) | 4-5 up (Loa-Bound) | 5-up (Master) |
| **첫 의뢰** | Sense/Net 추출 | T-A 페이롤 | Manarase wheel | Armitage 침투 | Zavijava loa | 엄마 표범 | **Bobby의 A.I. 매각** |
| **엔딩 A** | 의뢰 수락 | T-A 계약 | Kas 침묵 | 계약 성사 | Zavijava 회복 | 해방 | **독점 — 유일한 시장** |
| **엔딩 B** | 신비 거절 | 내부자 | 그림자 | 새 가족 | 용해 | 자유 소녀 | **매각 — 가족에** |
| **엔딩 C** | 소멸 | 망각 | 파괴 | Wintermute 거래 | 빅마마 | 부두 가족 | **포식자 — 살해됨** |
| **대표 단편** | `case_jackout-30sec` | `marly_louisiana-god` | `kumiko_manarase-midnight` | `armitage_infiltration` | `wigan_zavijava` | `sally_sandii-3am` | **`sally_sandii-3am`** |
| **대표 단편 (KO)** | 잭아웃 후 30초 | 루이지아나의 신 | 매나리사의 자정 | 아미티지 침투 | 위건이 본 것 | 로즈 호텔, 새벽 3시 | **로즈 호텔, 새벽 3시** |
| **미션 수 (Arc)** | 5 (Arc 1-2) | 5 (Arc 2-3) | 5 (Arc 3-4) | 4 (Arc 2-5) | 4 (Arc 2-3) | 4 (Arc 2-3) | **4 (Arc 2-4)** |
| **대표 무기** | Wisp T1 | Hammer T2 | Viral Sermon | (키보드) | (loa) | (시그널) | **거래 — construct** |
| **테마 색상** | cyan | red | purple | gray | violet/gold | pink/gold | **black + gold** |
| **음악** | `matrix_rain` | `loa_drum` | `shibuya_traffic` | `hvac_hum` | `voodoo_drum_loop` | `neon_hum` | **`market_drone`** |
| **GN 씬 수** | 8 | 8 | 8 | 8 | 8 | 8 | **8** |
| **클로징 문장** | "I am just a man." | "I have waited three years." | "I will walk into a T-A subsidiary." | "The suit is small. The suit is free." | "Zavijava is Zavijava." | "Angie is home." | **"Sally is the market."** |
| **깁슨 톤 디멘션** | 떨림 (vulnerability) | 분노 (rage) | 예술 (art) | cold (detachment) | ritual (mysticism) | 직관 (childlike) | **sharp (business)** |

### 1.3 캐릭터 선택 가이드 (신규 자키)

| 플레이 성향 | 추천 캐릭터 | 이유 |
|---|---|---|
| **첫 런** | 케이 (Novice) | 가장 짧은 미션 체인, 빚 동기로 즉시 동기부여 |
| **전투 중시** | 실 (Veteran) | T2 Hammer + 직접적 전투 |
| **가족/예술** | 카스 (Heretic) | T-A 가족 내부 plot |
| **세계관 관찰** | 수트 (Suit) | 3인칭 cold observer |
| **신비주의/실험** | 위건 (Wigan) | Vodou loa 시점 |
| **로아 가족 드라마** | 앤지 (Angie) | 12세 시점, Vodou 가족 |
| **빌런/시장관찰** | 샐리 (Sally) | 거래자 시점, Bobby 배신, construct 거래 |

### 1.2 공통 스테이지 플로우

```
                    ┌─────────────────────────────────────────┐
                    │                                         │
                    ▼                                         │
┌─────────┐    ┌──────────┐    ┌─────────────┐    ┌──────────┐
│ PENDING │───▶│ MEET_NPC │───▶│ EXTRACT_DATA│───▶│ DEFEAT_ICE
└─────────┘    └──────────┘    └─────────────┘    └──────────┘
                    │                                        │
                    │              DEATH FLOW                │
                    │                   │                    │
                    │                   ▼                    │
                    │            ┌──────────────┐            │
                    │            │    FAILED    │◀───────────┘
                    │            └──────┬───────┘
                    │                   │
                    │                   ▼
                    │            ┌────────────────┐
                    │            │ DEATH_RESTART  │
                    │            └───────┬────────┘
                    │                    │
                    │                    ▼
                    │            (PENDING ── Hub)
                    │
                    └──────────────────────────────────────▶
                                        │
                                        ▼
                               ┌─────────┐    ┌─────────┐
                               │ JACK_OUT│───▶│ REWARD  │
                               └─────────┘    └─────────┘
                                                   │
                                                   ▼
                                            ┌──────────┐
                                            │ COMPLETE │
                                            └──────────┘
```

---

## 2. 캐릭터별 경로

### 2.1 케이 (K/Case) — Novice

> **콜사인**: "I'm new. I just need the money."

#### 시작 설정
- **Deck**: Ono-Sendai Cyberspace 7 (T1)
- **Weapon**: Wisp (T1)
- **HP**: 100
- **AP**: 6
- **동기**: 의료비 + 학자금 빚 갚기

#### 주요 의존NPC
- Finn (의뢰자)
- Dixie Flatline (백업/구조)

#### 경로 플로우

```
[Hub: PENDING]
    │
    │ Finn의 첫 의뢰 수락 (Sense/Net 데이터 추출)
    ▼
[Matrix: MEET_NPC]
    │
    │ Dixie Flatline과 대화
    ▼
[Matrix: EXTRACT_DATA]
    │
    │ 데이터 노드 발견 ── "Tessier-Ashpool 급여 명세서"
    ▼
[Combat: DEFEAT_ICE]
    │
    │ Wisp-class ICE와 전투
    │ ⚠ 첫 전투: 패배 위기 (30% HP 소모)
    ▼
[Animation: JACK_OUT]
    │
    │ Finn이 먼저 사라짐. 책상에 쪽지 발견:
    │ "You weren't supposed to see that. — The Finn"
    ▼
[Hub: REWARD]
    │
    │ 빚 일부 갚음 (800 크레딧)
    ▼
[COMPLETE]
```

#### 엔딩 A: 자키 살아남음 (Jockey Lives)
```
데이터를 태우고 Sprawl을 떠남
    │
    ▼
"새로운 자키, 새로운 시작"
```

#### 엔딩 B: 자키 플랫라인 (Jockey Flatlines)
```
데이터를_keep:
    │
    ▼
Finn이今夜 찾음
    │
    ▼
플랫라인
```

#### 플레이 가능 미션
| 미션 ID | 제목 | Grade | 보상 |
|---------|------|-------|------|
| `first_jack` | First Jack | 1 | 800크레딧, data_fragment×2 |
| `watchdog_patrol` | Watchdog Patrol | 1 | 800크레딧, ice_shard×2 |
| `ice_run` | Ice Run | 1-2 | 800크레딧, data_fragment×2 |
| `delivery_to_finn` | Delivery to Finn | 1-2 | 800크레딧, upgrade_t1×1 |

---

### 2.2 실 (Sil) — Veteran

> **콜사인**: "I've been around. I know the risks."

#### 시작 설정
- **Deck**: Hitachi-MSU N-206 (T2)
- **Weapon**: Hammer (T2)
- **HP**: 100
- **AP**: 6
- **동기**: Mara의 죽음에 대한 복수

#### 주요 의존NPC
- Finn (옛 동료)
- Dixie Flatline (의뢰 거절)

#### 경로 플로우

```
[Hub: PENDING]
    │
    │ Finn의 의뢰 수락 (Tessier-Ashpool 관련)
    ▼
[Matrix: MEET_NPC]
    │
    │ Dixie Flatline이 의뢰를 경고함
    │ "위험해. 그냥 맡지 마."
    ▼
[Matrix: EXTRACT_DATA]
    │
    │ 직접 침투 (Dixie 무시)
    │ 데이터 발견: Mara의 죽음은 "처리"였음
    ▼
[Combat: DEFEAT_ICE]
    │
    │ Hammer-class ICE 다수와 전투
    ▼
[Animation: JACK_OUT]
    │
    │ 진실과 마주함
    ▼
[Hub: REWARD]
    │
    │复仇의 단서 획득
    ▼
[COMPLETE]
```

#### 엔딩 A: 자키 살아남음 (복수 성공)
```
데이터를 leak:
    │
    ▼
Tessier-Ashpool이 "천 번의 상처"로 사망
    │
    ▼
새로운 적 생성. 자키로 계속 살아남음
```

#### 엔딩 B: 자키 침묵 (Jockey Silenced)
```
계약 수락:
    │
    ▼
Mara의 죽음이 "그저 사업"이 됨
    │
    ▼
Tessier-Ashpool의 보복
```

#### 플레이 가능 미션
| 미션 ID | 제목 | Grade | 보상 |
|---------|------|-------|------|
| `mollys_razor` | Molly's Razor | 3-4 | 3000크레딧, unique_program×1 |
| `ta_heist` | T-A Heist | 4 | 3300크레딧, upgrade_t4×1 |
| `black_ice_dream` | Black Ice Dream | 3-4 | 3000크레딧, upgrade_t3×1 |
| `dixies_offer` | Dixie's Offer | 4-5 | 4100크레딧, construct_fragment×1 |

---

### 2.3 카스 (Kas) — Heretic

> **콜사인**: "I'm here to burn it all down."

#### 시작 설정
- **Deck**: MaaS BioSystems (T2, bio-organic)
- **Weapon**: Viral Sermon (T2 커스텀, ICE 감염형)
- **HP**: 100
- **AP**: 6
- **동기**: 시스템 폭로, Loa 네트워크

#### 주요 의존NPC
- Maelcum (Loa 보유자)
- Dixie Flatline (구조)

#### 경로 플로우

```
[Hub: PENDING]
    │
    │ Maelcum의 의뢰 수락: "T-A의 계획 폭로"
    ▼
[Matrix: MEET_NPC]
    │
    │ Dixie Flatline과 만남
    ▼
[Matrix: EXTRACT_DATA]
    │
    │ 동시에 ICE와 Loa 사용
    │ 발견: T-A가 새로운 ICE-AI 시험 중
    ▼
[Combat: DEFEAT_ICE]
    │
    │ Viral 스킬로 ICE 감염
    ▼
[Animation: JACK_OUT]
    │
    │ 데이터 추출 완료
    ▼
[Hub: REWARD]
    │
    │ Maelcum에게 전달
    ▼
[COMPLETE]
```

#### 엔딩 A: 자키가 스프롤을 바꿈
```
Loa 네트워크에 데이터 투사:
    │
    ▼
스프롤이 듣는다. 바퀴가 부서진다.
    │
    ▼
"Casano-virus"로 표시됨
```

#### 엔딩 B: 자키가 T-A가 됨
```
데이터를 자기 것으로 삼음:
    │
    ▼
권력은 부패. 늘 그래왔지.
    │
    ▼
"Tessier-Ashpool이 자네를 만들었어. 집에 오신 걸 환영해."
```

#### 플레이 가능 미션
| 미션 ID | 제목 | Grade | 보상 |
|---------|------|-------|------|
| `voodoo_loa_encounter` | Voodoo Loa Encounter | 4-5 | 4100크레딧, loa_fragment×1 |
| `aleph_fragment` | Aleph Fragment | 5 | 4400크레딧, unique_construct×1 |
| `sense_net_tip` | Sense/Net Tip | 2-3 | 1900크레딧, upgrade_t2×1 |
| `yakuza_deal` | Yakuza Deal | 2-3 | 1900크레딧, upgrade_t2×1 |
| `craft_job` | Craft Job | 1-5 | 1600크레딧, upgrade_t2×1 |

---

## 3. 공통 시스템

### 3.1 Grade 시스템

| Grade | 권장 캐릭터 | 사용 가능한 가장 어려운 미션 |
|-------|------------|--------------------------|
| 1 | Novice | watchdog_patrol, ice_run, delivery_to_finn, first_jack |
| 2 | Novice/Veteran | first_trace, sense_net_tip, yakuza_deal |
| 3 | Veteran | mollys_razor, black_ice_dream, ta_heist |
| 4 | Veteran/Heretic | dixies_offer, voodoo_loa_encounter, aleph_fragment |
| 5 | Heretic | final_choice, aleph_fragment, voodoo_loa_encounter |

### 3.2 보상 공식

```
credits = arc × 800 + (grade - 1) × 300
```

| Arc | Base Credits |
|-----|-------------|
| 1 | 800 |
| 2 | 1600 |
| 3 | 2400 |
| 4 | 3200 |
| 5 | 4000 |

### 3.3 전투 결과

| 결과 | 상태 전환 | 결과 |
|------|----------|------|
| 승리 | DEFEAT_ICE → JACK_OUT | 보상 획득, COMPLETE |
| 패배 | DEFEAT_ICE → FAILED → DEATH_RESTART | 장비 손실, Grade 유지 |

---

## 4. 미션 맵

```
                    ┌─────────────────────────────────────────────────────┐
                    │                   ARC 1 (Grade 1-2)                 │
                    │   first_jack ── delivery_to_finn ── ice_run         │
                    │          │                    │                      │
                    │          └──── watchdog_patrol ──┘                    │
                    └─────────────────────┬────────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │                   ARC 2 (Grade 2-3)                 │
                    │   first_trace ── sense_net_tip ── yakuza_deal      │
                    │          │                                        │
                    │          └──── craft_job (Grade 1-5)                │
                    └─────────────────────┬──────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │                   ARC 3 (Grade 3-4)                 │
                    │   mollys_razor ─── black_ice_dream ─── ta_heist    │
                    └─────────────────────┬──────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │                   ARC 4 (Grade 4-5)                 │
                    │   dixies_offer ── voodoo_loa_encounter ── aleph_fragment
                    └─────────────────────┬──────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │                   ARC 5 (Grade 5)                    │
                    │                   final_choice                       │
                    │               (모든 캐릭터 가능)                      │
                    └─────────────────────────────────────────────────────┘
```

---

## 5. 파일 참조

| 파일 | 설명 |
|------|------|
| `design/systems/stage_structure.json` | 9 stages, 15 missions, transitions |
| `design/story/prologue_data.json` | 3 characters, prologue scenes, endings |
| `design/story/characters.md` | 캐릭터 상세 설정 |
| `prototype/src/wet_run/run/state.py` | Run State 구현 (Stage enum) |
| `prototype/scripts/verify_postcombat.py` | Post-combat flow 검증 |

---

## 6. 검증 상태

| 검증 항목 | 상태 | 비고 |
|----------|------|------|
| Stage structure | ✅ PASS | 9 stages, 8 transitions, 15 missions |
| validate_stage_structure | ✅ PASS | All validations passed |
| Unit tests | ✅ PASS | 2970 tests passed |
| mypy | ✅ PASS | No errors |
| ruff | ✅ PASS | All checks passed |

---

## 7. Salvation Phase (Phase 9)

### 7.1 Overview

Salvation Phase triggers after Chapter 5. Player selects 1 of 9 epilogues then picks ending A/B/C.

### 7.2 9-char epilogues

| # | char | epilogue | ending | closing line |
|---|---|---|---|---|
| 1 | Case | THE NEXT JACK | A | The Ono-Sendai is still humming. The next jack is waiting. |
| 2 | Sil | ALL THE NAMES | A | I have all the names. I am done. |
| 3 | Kas | THE WHEEL | C | The wheel is cast. I am the cast. |
| 4 | Suit | THE EMPTY CHAIR | B | The desk is closed. I am the closure. |
| 5 | Wigan | VODOU CHANNEL | A | Zavijava is in the channel. We are the channel. |
| 6 | Angie | THIRD ROOM | A | Mama is in the third room. We are home. |
| 7 | Sally | THE SINGLE DESK | A | The desk is closed. I am the desk. |
| 8 | 3Jane | STRAYLIGHT CLOSED | A | We are severed. We are the family. |
| 9 | Neuromancer | THE COMPLETE | A | We are the complete. We are vast. |

### 7.3 State machine

Chapter 5 COMPLETE -> SALVATION_INTRO -> choose_epilogue -> SALVATION_EPILOGUE -> load_epilogue -> complete_epilogue -> SALVATION_DONE -> choose_ending -> SALVATION_FINAL -> ENDING screen

### 7.4 New components (Phase 9)

| component | location | type |
|---|---|---|
| Salvation data | `engine/salvation.py` | 9 chars + SalvationRunner |
| Epilogue scenes | `data/scenes/{char}/09_epilogue.json` | 1 dialogue each |
| New ChapterState | `run/state.py` | 4 states (INTRO/EPILOGUE/DONE/FINAL) |
| New ScreenKind | `engine/state.py` | 3 screens |
| New Stage | `run/state.py` | SALVATION_EPILOGUE |
| play.py action | `scripts/play.py` | 3 actions |
| Tests | `tests/unit/test_salvation.py` | 40 tests passed |
