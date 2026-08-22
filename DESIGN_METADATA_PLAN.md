# Dashboard Game Design Metadata Plan

## 현재 상태 분석

### Dashboard Stats 파일 (10개)
| 파일 | 내용 | 게임 설계 반영 |
|---|---|---|
| `index_stats.json` | tests: 4185, missions: 47, NPCs: 5, stages: 9 | △ 정량만 |
| `character_stats.json` | 케이/실/카스 3명 属性 | △ 캐릭터 중심 |
| `mission_stats.json` | 47미션, arcs, chapters, reactions | △ |
| `library_stats.json` | 39 stories (36 short + 3 novelette) | △ |
| `combat_stats.json` | 41 ICE types, 9 programs | △ |
| `cyberspace_stats.json` | 2 worlds / 4 sectors / 6 servers / 8 nodes / 6 depths | △ |
| `run_stats.json` | 14 stages, 18 chapter states | ○ |
| `stages_stats.json` | stages/transitions/objectives 수 | ○ |
| `journey_stats.json` | 3 arc별 credits/missions/deaths/grade | ○ |
| `event_dialogues_stats.json` | NPCs/dialogues/lines | ○ |

### 디자인 문서 vs Dashboard 반영

| 디자인 문서 내용 | Dashboard 반영 | 상태 |
|---|---|---|
| **5 Design Pillars** | 없음 | ❌ |
| **Anti-patterns (비-기둥 7개)** | 없음 | ❌ |
| **PPL/ZDR 난이도 시스템** | 없음 | ❌ |
| **Tier System (T1-T6)** | combat_stats에 프로그램 9개만 | △ |
| **Alarm/Trace Mechanic** | 없음 | ❌ |
| **Pillar × Mission 분포** | 없음 | ❌ |
| **World Hierarchy** | cyberspace_stats에 수만 | ○ |
| **Core Loop (Macro/Micro)** | 없음 | ❌ |
| **RT-MS Combat** | combat_stats에 이름만 | △ |
| **5 Factions** | 없음 | ❌ |

---

##_metadata.json 설계

새 파일: `dashboard/data/design_system.json`

### 구조

```json
{
  "design_pillars": [
    {
      "id": 1,
      "name": "The Run",
      "tagline_ko": "한 번의 침투, 명확한 끝",
      "tagline_en": "One run, one job, one clear ending",
      "color": "#66ffcc",
      "mechanics": ["job 단위 진행", "PPL/ZDR 난이도 명시", "Story Events"],
      "anti_these": ["무한 진행 모드", "일일 미션", "강제 진입"]
    },
    {
      "id": 2,
      "name": "The Matrix",
      "tagline_ko": "사이버스페이스가 유일한 시각적 공간",
      "tagline_en": "Cyberspace is the only visual space",
      "color": "#00ccff",
      "mechanics": ["meatspace 절대 시각화 안함", "ASCII portrait는 cyberspace 안의 존재만"],
      "anti_these": ["meatspace 메인 게임", "현실 세계 직접 묘사"]
    },
    {
      "id": 3,
      "name": "The Flatline",
      "tagline_ko": "죽음에 진짜 무게",
      "tagline_en": "Death has real weight",
      "color": "#ff5555",
      "mechanics": ["평시 캐릭터 Loss", "리스폰 없음", "메타 진행은 공격적이지 않음"],
      "anti_these": ["리스폰/부활", "가벼운 죽음 페널티"]
    },
    {
      "id": 4,
      "name": "The Build",
      "tagline_ko": "런 사이 진행은 더 좋은 도구로",
      "tagline_en": "Between runs, better tools",
      "color": "#ffaa55",
      "mechanics": ["레벨업 = 아이템/장비 티어 (T1-T6)", "combat 강도는 program tier에 비례"],
      "anti_these": ["스탯 누적", "XP/레벨 시스템"]
    },
    {
      "id": 5,
      "name": "The Style",
      "tagline_ko": "사이버펑크 미학 - 네온, 크롬, 가죽",
      "tagline_en": "Cyberpunk aesthetics — neon, chrome, leather",
      "color": "#9b59b6",
      "mechanics": ["깁슨 톤 정확히", "거칠고 비관적", "mediated world"],
      "anti_these": ["미니멀/유토피아 미래", "Cyberpunk 2077 톤"]
    }
  ],

  "anti_patterns": [
    {"id": "AP-1", "name": "Loot Grind", "description_ko": "무한히 강한 적 = 무한히 좋은 loot"},
    {"id": "AP-2", "name": "Multiplayer/Social", "description_ko": "1인칭 솔로 경험"},
    {"id": "AP-3", "name": "Skins/Cosmetics", "description_ko": "시각적 다양성보다 의미"},
    {"id": "AP-4", "name": "Daily Login", "description_ko": "게임이 사용자 시간을 빼앗지 않음"},
    {"id": "AP-5", "name": "Infinite Scaling", "description_ko": "적이 계속 강해지는 시스템"},
    {"id": "AP-6", "name": "Prestige", "description_ko": "반복 플레이를 위한 인위적 시스템"},
    {"id": "AP-7", "name": "Mobile/F2P", "description_ko": "PC/Mac 솔로 게임"}
  ],

  "core_loop": {
    "macro": {
      "ko": "Hub → Run(매트릭스 진입) → Extraction/Death → Result → Hub",
      "stages": ["BRIEFING", "TRAVEL", "MEET_NPC", "EXTRACT_DATA", "BYPASS_SECURITY", "DEFEAT_ICE", "JACK_OUT", "REWARD", "DEBRIEF"]
    },
    "micro": {
      "ko": "Navigation → Node 발견 → Decision → Action → Combat(RT-MS) → State Update",
      "alarm_levels": [0, 1, 2, 3, 4, 5]
    },
    "combat": {
      "name": "RT-MS (Real-Time Missile Storm)",
      "ko": "실시간 자동 공격 + 메뉴 스킬",
      "tick_rate": "1 attack / 2초, 양쪽 동시",
      "skill_count": 14,
      "skill_effects": 15
    }
  },

  "difficulty_system": {
    "ppl_zdr": {
      "ko": "전투 전/중 위험 명시화 시스템",
      "ppl": {"ko": "Player Power Level — 자키의 현재 힘 (데크/프로그램 티어 합산)", "range": "1-99"},
      "zdr": {"ko": "Zone Difficulty Rating — 현재 zone의 위험", "range": "1-99"},
      "status": [
        {"name": "SAFE", "ratio": "PPL > ZDR*1.5", "color": "#66ffcc"},
        {"name": "MATCH", "ratio": "ZDR*0.8 < PPL <= ZDR*1.5", "color": "#00ccff"},
        {"name": "TOUGH", "ratio": "ZDR*0.5 < PPL <= ZDR*0.8", "color": "#ffaa55"},
        {"name": "DEADLY", "ratio": "ZDR*0.25 < PPL <= ZDR*0.5", "color": "#ff5555"},
        {"name": "FUTILE", "ratio": "PPL <= ZDR*0.25", "color": "#ff0000"}
      ]
    },
    "grade_progression": {
      "grades": [1, 2, 3, 4, 5, 6],
      "tier_map": {"grade_1": "T1", "grade_2": "T2", "grade_3": "T3", "grade_4": "T4", "grade_5": "T5", "grade_6": "T6"}
    }
  },

  "tier_system": {
    "max_tier": 6,
    "programs_count": 9,
    "program_tiers": {
      "T1": ["wisp", "strike", "shield", "probe"],
      "T2": ["hammer", "virus"],
      "T3": ["goliath"],
      "T4": ["wardrone"],
      "T5": ["kraken"],
      "T6": ["master_tbd"]
    }
  },

  "mission_distribution": {
    "by_pillar": {
      "power": 19,
      "code": 14,
      "purpose": 7,
      "people": 4,
      "identity": 2,
      "memory": 1
    },
    "by_arc": {
      "1": 6, "2": 13, "3": 11, "4": 9, "5": 8
    },
    "by_zone": {
      "surface": 12,
      "deep": 10,
      "mid": 9,
      "core": 7,
      "freeside": 5,
      "ta": 4
    },
    "by_grade_range": {
      "grade_1-1": 2,
      "grade_1-2": 4,
      "grade_1-5": 1,
      "grade_2-2": 3,
      "grade_2-3": 3,
      "grade_3-4": 6,
      "grade_4-4": 5,
      "grade_4-5": 4,
      "grade_5-5": 7,
      "grade_5-6": 3,
      "grade_6-6": 2
    }
  },

  "world_hierarchy": {
    "worlds": 2,
    "world_names": ["Chiba City", "Night City"],
    "sectors_per_world": {"chiba": 2, "night_city": 2},
    "total_sectors": 4,
    "total_servers": 6,
    "node_kinds": 8,
    "zone_depths": 6
  },

  "run_stages": {
    "count": 14,
    "names": ["PENDING", "BRIEFING", "TRAVEL", "MEET_NPC", "EXTRACT_DATA", "BYPASS_SECURITY", "DEFEAT_ICE", "JACK_OUT", "REWARD", "DEBRIEF", "COMPLETE", "DEATH_RESTART", "FAILED", "SALVATION_EPILOGUE"],
    "death_stages": ["DEATH_RESTART", "FAILED"]
  },

  "alarm_system": {
    "levels": 6,
    "level_descriptions": [
      {"level": 0, "name_ko": "평온", "ice_ko": "없음", "risk_ko": "없음"},
      {"level": 1, "name_ko": "인지", "ice_ko": "기본 배치", "risk_ko": "낮음"},
      {"level": 2, "name_ko": "정찰", "ice_ko": "watchdog", "risk_ko": "중간"},
      {"level": 3, "name_ko": "추적", "ice_ko": "hellhound", "risk_ko": "높음"},
      {"level": 4, "name_ko": "黑色ICE", "ice_ko": "black ICE, trace 진행", "risk_ko": "매우 높음"},
      {"level": 5, "name_ko": "trace 완료", "ice_ko": "flatline 임박", "risk_ko": "치명적"}
    ]
  },

  "_source_files": [
    "design/pillars.md",
    "design/core_loop.md",
    "prototype/data/missions/missions.json",
    "prototype/data/programs/programs.json",
    "prototype/data/cyberspace/worlds.json"
  ]
}
```

---

## 구현 순서 (Priority Order)

### Phase 1: 핵심 설계 메타데이터 ✅ 2026-07-08
1. ✅ **`design_system.json`** 생성 — 5 pillars, anti-patterns, PPL/ZDR, tier, alarm
2. ✅ **`build_dashboard.py`** 업데이트 — `load_design_system()` + `load_faction_stats()`
3. ✅ **`index.html`** Design System 패널 — 5 pillars + RT-MS + PPL/ZDR + Alarm + Mission distribution

### Phase 2: 미션 설계 분포 ✅ 2026-07-08
4. ✅ `design_system.json` mission_distribution (pillar/arc/zone/grade_range)
5. ✅ world hierarchy (cyberspace_stats.json 강화 → design_system.json world_hierarchy)

### Phase 3: 고급 설계 뷰 ✅ 2026-07-08
6. ✅ Core loop ASCII 흐름도 (index.html Design System 패널)
7. ✅ Alarm system 시각화 (index.html Alarm card)
8. ⏳ Faction/reputation 시스템 — `faction_stats.json` 완성 (코드에서 추출), 대시보드 연동은将来

---

## 검증 체크리스트

### Metadata 작성 전 확인 ✅
- [x] missions.json: 47개 전부 `pillar` 필드 ✅
- [x] programs.json: 9개 전부 `tier` 필드 ✅
- [x] worlds.json: world/sector/server 계층 완비 ✅
- [x] Alarm system: 6단계 정의/design_system.json 반영 ✅
- [x] Faction reputation: Faction enum (5개) + tier thresholds 추출 ✅

### Dashboard integration 검증 ✅
- [x] `design_system.json`이 `build_dashboard.py`로 생성 ✅
- [x] index.html Design System 패널 완성 ✅
- [x] Factions 섹션 (5 factions + reputation tiers) ✅
- [x] Core loop ASCII 흐름도 ✅
- [x] build_dashboard.py dry-run 정상 ✅

### Stats 파일 (12개)
```
✅ combat_stats.json        ✅ library_stats.json
✅ mission_stats.json        ✅ event_dialogues_stats.json
✅ stages_stats.json         ✅ cyberspace_stats.json
✅ journey_stats.json       ✅ index_stats.json
✅ character_stats.json      ✅ run_stats.json
✅ design_system.json        ✅ faction_stats.json
```

### 남은 작업
- Faction/reputation 런타임 연동 (code-only, 대시보드 표시 불필요)
- [ ] `design_system.json`이 `build_dashboard.py`로 생성되는가?
- [ ] index.html의 stat panels이 새 JSON을 참조하는가?
- [ ] pillar 카드 클릭 → 해당 mechanic 설명으로 드릴다운 가능한가?
- [ ] PPL/ZDR 시각화가 실제 전투 HUD와 일치하는가?
