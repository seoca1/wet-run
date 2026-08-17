# Character Journeys

> 게임 진행 데모 스토리 — 챕터별 미션, 전투, 아이템, 엔딩 분기
>
> **이 문서는 게임의 실제 미션/아크/챕터/엔딩 데이터를 기반으로 자동 생성되었습니다.**
> **파생 소설(Fiction wiki 단편)과는 별개입니다.**

---

## 캐릭터 선택

| 핸들 | 챕터 | 픽서 | 동기 | 영감 원작 | 누적 credits | 미션 수 |
|---|---|---|---|---|---:|---:|
| **[케이 (K)](../../../../../Fiction/wiki/characters/novice.md)** — Novice | chapter_novice | The Finn | 돈 | Case (Neuromancer) | **<span data-stat="novice-credits-card">20,050</span>cr** | 10 |
| **[실 (Sil)](../../../../../Fiction/wiki/characters/veteran.md)** — Veteran | chapter_veteran | Finn / 변동 | 복수 | Marly (Count Zero) | **<span data-stat="veteran-credits-card">27,500</span>cr** | 11 |
| **[카스 (Kas)](../../../../../Fiction/wiki/characters/heretic.md)** — Heretic | chapter_heretic | Finn / Sally / Kumiko | 전복 | Kumiko (Mona Lisa Overdrive) | **<span data-stat="heretic-credits-card">20,100</span>cr** | 8 |

---

## 구조 검증 요약

### 1. 미션 시스템 ✅
- **29/29 미션 매핑** (15 → 18 → 29)
- 모든 미션이 미션 시스템에 등록됨
- 캐릭터별 character_ref 일관성 ✓

### 2. 아크 구조 ✅
- **5 챕터 × 5 phase = 25 phase** per 캐릭터
- 챕터 ID 매핑 (ch_case_01~05, ch_sil_01~05, ch_kas_01~05)

### 3. 챕터 스크린 ✅
- 각 챕터당 단편 본문 발췌 (12초 타이핑)
- novice: `case_jackout-30sec`
- veteran: `marly_louisiana-god`
- heretic: `kumiko_manarase-midnight`

### 4. 엔딩 시스템 ✅
| 캐릭터 | 엔딩 A | 엔딩 B |
|---|---|---|
| Novice | 🏃 Burn and Run (탈출) | 💀 The Flatline (사망) |
| Veteran | 📢 Whistleblower (폭로) | 💼 Business (사업) |
| Heretic | 🔥 Declaration (선언) | 👑 Absorption (흡수) |

### 5. 보상 시스템 ✅
| 아이템 | 용도 |
|---|---|
| `data_fragment` | 데이터 추출 보상 (공통) |
| `ice_shard` | 매트릭스 빙의 조각 |
| `rom_fragment` | ROM construct 파편 |
| `loa_fragment` | loa 매개체 파편 |
| `construct_fragment` | construct 핵심 |
| `memory_chip` | 기억 저장 |
| `unique_construct` / `unique_program` | 희귀 아이템 |
| `upgrade_t1`~`t4` | 장비 업그레이드 (T1=초급, T4=최상급) |
| `ending_token` | 엔딩 분기 결정 |

### 6. 픽서 분포 ✅
- **novice**: Finn 100% (10/10) — 단일 픽서, 단순 의뢰 체계
- **veteran**: Finn 6, Dixie 1, MaaS 1, ta_rep 1, Sally 1, Kumiko 1 — 다양한 의뢰 네트워크
- **heretic**: Finn 3, Sally 3, Kumiko 1, Yakuza 1 — 카오틱 의뢰 체계

### 7. 적(ICE) 분포 ✅
- **novice**: ICE.standard → ICE.watchdog → Black ICE (점진적 난이도 상승)
- **veteran**: ICE.corporate → ICE.construct → ICE.wintermute (loa-매개 변형)
- **heretic**: ICE.craft → ICE.ai_whisper → ICE.neuromancer (AI/loa 변형)

### 8. 챕터-미션 매핑 ✅
| Arc | Novice (10) | Veteran (11) | Heretic (8) |
|:---:|---|---|---|
| 1 | 5 (data_retrieval, first_jack, ice_run, tutorial_maze, watchdog_patrol) | 1 (delivery_to_finn) | 0 |
| 2 | 2 (first_trace, flatline_call) | 3 (first_contact, mollys_market, sense_net_tip) | 3 (craft_job, sally_sandii_3am, yakuza_deal) |
| 3 | 1 (black_ice_dream) | 3 (mollys_razor, ta_heist, vegas_stakeout) | 2 (neuromancer_whisper, sally_returns_arc3) |
| 4 | 1 (voodoo_loa_encounter) | 3 (dixies_choice, dixies_offer, winter_infiltrate) | 2 (aleph_fragment, matrix_revelation) |
| 5 | 1 (final_choice) | 1 (zion_express) | 1 (neuromancer_merger) |

---

## 게임 진행 흐름 (시각화)

```
┌─────────────────────────────────────────────────────────────┐
│                  CHARACTER SELECT (The Finn)                  │
│       "I need a jockey. Sense/Net, first run..."            │
└─────┬─────────────────┬─────────────────┬───────────────────┘
      │                 │                 │
   ┌──▼──┐          ┌──▼──┐          ┌──▼──┐
   │  K  │          │ Sil │          │ Kas │
   │ Nov │          │ Vet │          │ Her │
   └──┬──┘          └──┬──┘          └──┬──┘
      │                 │                 │
   [CHAPTER]        [CHAPTER]        [CHAPTER]
   30 Seconds       Louisiana 11    Manarase
   (Case 1인칭)      (Marly 3인칭)    (Kumiko 3인칭)
      │                 │                 │
   ┌──▼──────────┐    ┌──▼──────────┐    ┌──▼──────────┐
   │ arc_case    │    │ arc_sil     │    │ arc_kas     │
   │ 5 chapters  │    │ 5 chapters  │    │ 5 chapters  │
   │ 10 missions │    │ 11 missions │    │ 8 missions  │
   │ 25 phases   │    │ 25 phases   │    │ 25 phases   │
   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
          │                │                │
       ┌──▼──┐          ┌──▼──┐          ┌──▼──┐
       │ A  │          │ A  │          │ A  │
       │ 탈출 │          │ 폭로 │          │선언│
       └─────┘          └─────┘          └─────┘
       ┌──▼──┐          ┌──▼──┐          ┌──▼──┐
       │ B  │          │ B  │          │ B  │
       │사망 │          │사업 │          │흡수│
       └─────┘          └─────┘          └─────┘
```

---

## 캐릭터별 비교

| 지표 | Novice (K) | Veteran (Sil) | Heretic (Kas) |
|---|---|---|---|
| 시작 동기 | 돈 | 복수 | 전복 |
| 시작 핸드폰 | Wisp T1 | Hammer T2 | Custom Viral |
| 시작 credits | 0 | 0 | 0 |
| 최종 credits | 20,050 | 27,500 | 20,100 |
| 최종 등급 | 5 | 5 | 5 |
| 최종 핸드폰 (추정) | T3 Hammer | T4 Hammer | T4 + unique_construct |
| 픽서 다양성 | 1 (Finn) | 6 (다양) | 4 (Finn/Sally/Kumiko/Yakuza) |
| 적 다양성 | ICE.standard → Black ICE | ICE.corporate → ICE.wintermute | ICE.craft → ICE.neuromancer |
| 시점 | 1인칭 | 1인칭 + 3인칭 | 1인칭 + 3인칭 |
| CHAPTER 화면 | Case (1인칭) | Marly (3인칭) | Kumiko (3인칭) |
| 원작 | Neuromancer | Count Zero | Mona Lisa Overdrive |
| 핵심 갈등 | Finn 의뢰 추적 | Tessier-Ashpool 복수 | 데이터 전복 |
| 최종 갈등 | 데이터 보관 vs 폐기 | 폭로 vs 사업화 | 선언 vs 흡수 |
| 엔딩 A (긍정) | 🏃 Burn and Run | 📢 Whistleblower | 🔥 Declaration |
| 엔딩 B (비관) | 💀 The Flatline | 💼 Business | 👑 Absorption |

---

## 챕터 메타 정보 (전 챕터 통합)

### Novice (chapter_novice)
- **이름**: The First Jack
- **부제**: Thirty Seconds After Jack-Out
- **포트레잇**: art:case
- **테마**: matrix_rain
- **duration_ms**: 12000 (12초 타이핑)
- **다음 화면**: HUB

### Veteran (chapter_veteran)
- **이름**: The Old Score
- **부제**: The Louisiana God
- **포트레잇**: art:marly
- **테마**: cyberspace
- **duration_ms**: 12000
- **다음 화면**: HUB

### Heretic (chapter_heretic)
- **이름**: The Declaration
- **부제**: Manarase at Midnight
- **포트레잇**: art:kumiko
- **테마**: sense_net
- **duration_ms**: 12000
- **다음 화면**: HUB

---

## 아이템 시스템 (인벤토리 흐름)

```
Novice:                              Veteran:                              Heretic:
─────────                            ─────────                             ─────────
Tier 1 (Arc 1-2):                  Tier 1-2 (Arc 1-2):                   Tier 1-2 (Arc 2):
  data_fragment × 12                  data_fragment × 5                     data_fragment × 0
  ice_shard × 2                       upgrade_t1 × 1                       memory_chip × 1
                                      upgrade_t2 × 1                        upgrade_t2 × 2
Tier 3 (Arc 3-4):                                                                          ↓
  rom_fragment × 1                  Tier 3-4 (Arc 3-4):                   Tier 3 (Arc 3):
  loa_fragment × 1                   construct_fragment × 1                  construct_fragment × 2
  upgrade_t3 × 1                     unique_program × 1
                                    upgrade_t4 × 1
Tier 5 (Arc 5):                    Tier 5 (Arc 5):
  ending_token × 1                   data_fragment × 5                    Tier 4-5 (Arc 4-5):
                                                                       unique_construct × 1
                                                                       data_fragment × 13
                                     Final Grade 5                       Final Grade 5
                                     27,500cr                            20,100cr
                                     T4 Hammer                           T4 + unique_construct
```

---

## 데이터 출처

```
Game/wet_run/prototype/
├── data/
│   ├── missions/missions.json           (29 미션, source: 검증 헬퍼 통과)
│   ├── story/
│   │   ├── chapters/{case,sil,kas}.json (CHAPTER 화면 데이터)
│   │   ├── arcs/{case,sil,kas}_arc.json (5 챕터 × 5 phase = 25 phase)
│   │   └── prologues/{case,sil,kas}.json (프롤로그 NPC 이벤트)
│   ├── programs/programs.json           (9개 프로그램/스킬)
│   ├── jockeys/deceased.json            (Hall of Dead — 사망 자키 기록)
│   └── i18n/{en,ko}.json                (UI 번역, 69 키)
└── src/wet_run/
    └── engine/
        ├── chapter_view.py              (CHAPTER 화면 렌더링)
        └── original_story.py            (캐릭터 선택 + 엔딩 + 씬 테마)
```

---

*Generated: 2026-06-30. 자동 검증: `verify_story_links.py` (29/29 OK), `test_story_resolver.py` (15/15 PASS)*