# Wet Run — 스테이터스 & 난이도 설계

**문서 상태**: DRAFT
**Created**: 2026-06-23
**Purpose**: 레벨/아이템/적/NPC 스테이터스 체계 + 스테이지 난이도 연동 설계

---

## 1. 개요

### 1.1 목표

| 목표 | 설명 |
|------|------|
| **난이도 검증** | 플레이어 PPL vs 적 HP/DMG 균형 검증 |
| **레벨 체계 확립** | Player Grade + PPL 기반 단계적 난이도 |
| **아이템/스킬 시스템** | 등급별 장비 & 프로그램 조합 |
| **적/NPC 레벨링** | 각Enemy Tier × Player Grade → 적 HP/DMG 스케일 |
| **스테이지 연동** | Phase별 적配置 + 보상 설계 |

### 1.2 기존 시스템 분석

**현재 상태**:
- ✅ Grade 1-5 (미션 잠금 해제용)
- ✅ PPL 계산식 (Deck/Program/Wetware/Construct 합산)
- ✅ ICE 타입 5종 (HP/DMG/Tier 고정)
- ✅ Skill 16종 (Registry 기반)
- ✅ Equipment 14종 (Tier 0-3)
- ❌ XP/레벨업 시스템 없음
- ❌ 적 스케일링 없음 (고정 stat)
- ❌ NPC 전투력 없음
- ❌ Stage별 난이도 매핑 없음

---

## 2. 플레이어 스테이터스

### 2.1 Grade 시스템 (기존 유지)

```python
Grade = 1..5  # 미션 잠금용 (기존 그대로)
# Grade 1: T0-T1 장비, 1-2 스킬
# Grade 2: T1-T2 장비, 2-3 스킬
# Grade 3: T2-T3 장비, 3-4 스킬
# Grade 4: T3-T4 장비, 4-5 스킬
# Grade 5: T4-T5 장비, 5+ 스킬
```

### 2.2 PPL (Player Power Level) — 기존 유지

```python
PPL = (deck_tier * 3) + Σ(program_tiers * 2) + wetware + (construct_tier * 3)

# 예시:
# T2_deck(6) + 3xT1_programs(6) + T2_wetware(2) + T1_construct(3) = PPL 17
```

### 2.3 Combat Stats (기존 유지 + 확장)

```python
@dataclass
class CombatStats:
    max_hp:     int    # 체력
    hp:         int    # 현재 체력
    ap:         int    # 현재 AP
    max_ap:     int    # 최대 AP (기본 6)
    ap_regen:   int    # AP 회복량/tick
    attack:     int    # 공격력 (장비 보정 포함)
    defense:    int    # 방어력 (데미지 감면)
    crit_rate:  float  # 치명타율 (기본 15%)
    crit_dmg:   float  # 치명타 배율 (기본 2.0x)
    speed:      int    # 선제공격 여부 결정

    # 내성
    ice_resist: float  # ICE 데미지 감면율 (기본 0%)
    shield:     int    # 현재 방패량

    # 스킬
    skills:     tuple[SkillId, ...]  # 장비/스킬트리에서 획득
```

### 2.4 XP & 레벨업 시스템 (NEW)

```python
XP_TO_LEVEL = {
    2: 100,    # Grade 1 → 2
    3: 300,    # Grade 2 → 3
    4: 600,    # Grade 3 → 4
    5: 1000,   # Grade 4 → 5
}

@dataclass
class PlayerProgression:
    xp:           int       # 현재 XP
    grade:        int       # 현재 Grade (1-5)
    skill_points: int       # 스킬 포인트 (레벨업 시 +1)
    unlocked_tiers: set[EquipTier]  #解锁的装备等级

    def add_xp(self, amount: int) -> bool:
        """XP 추가. Grade업 시 True 반환"""
        self.xp += amount
        if self.xp >= XP_TO_LEVEL[self.grade] and self.grade < 5:
            self.grade += 1
            self.skill_points += 1
            return True
        return False
```

### 2.5 Grade → PPL 권장 범위

| Grade | PPL Min | PPL Max | 권장 적 Tier |
|-------|---------|---------|-------------|
| 1 | 3 | 12 | T1 |
| 2 | 10 | 20 | T1-T2 |
| 3 | 18 | 30 | T2-T3 |
| 4 | 28 | 42 | T3-T4 |
| 5 | 40 | 60 | T4-T5 |

---

## 3. 적 (Enemy/ICE) 스테이터스

### 3.1 ICE Tier 시스템 (확장)

```python
ICETier = 1..5  # Player Grade와 대응

@dataclass
class ICEStats:
    id:           str
    name:         str
    tier:         int           # 1-5 (Player Grade 대응)
    hp_base:      int           # 기본 HP
    hp_per_grade: int           # Grade당 HP 증가량
    dmg_base:     int           # 기본 공격력
    dmg_per_grade: int          # Grade당 공격력 증가량
    defense:      int           # 방어력
    speed:        int           # 속도 (AP 우선순위)
    skills:       tuple[SkillId, ...]
    resistance:   float         # 특정 데미지 내성
    loot_table:   dict[str, float]  # 드롭 테이블
```

### 3.2 ICE HP/DMG 스케일 공식

```python
def get_ice_stats(ice: ICEStats, player_grade: int) -> tuple[int, int]:
    """Player Grade 기반 ICE 실제 HP/DMG 반환"""
    grade_diff = player_grade - ice.tier

    # Grade가 높을수록 적 체력/공격력 증가
    hp = ice.hp_base + (ice.hp_per_grade * max(0, grade_diff))
    dmg = ice.dmg_base + (ice.dmg_per_grade * max(0, grade_diff))

    # Grade가 낮으면 보정 (최소 70% 유지)
    if grade_diff < 0:
        scale = 1.0 + (grade_diff * 0.15)  # -1 Grade = 85%, -2 = 70%
        hp = int(hp * max(0.7, scale))
        dmg = int(dmg * max(0.7, scale))

    return hp, dmg

# 예시: Watchdog (tier=1, hp_base=50, dmg_base=2)
# Player Grade 1: HP=50, DMG=2
# Player Grade 3: HP=50+(2*2)=54, DMG=2+(1*2)=4
# Player Grade 5: HP=50+(2*4)=58, DMG=2+(1*4)=6
```

### 3.3 기존 ICE 타입 스펙

```json
{
  "standard": {
    "name": "ICE — Standard",
    "hp_base": 80, "hp_per_grade": 15,
    "dmg_base": 3, "dmg_per_grade": 1,
    "tier": 1, "defense": 2, "speed": 5
  },
  "watchdog": {
    "name": "ICE — Watchdog",
    "hp_base": 50, "hp_per_grade": 10,
    "dmg_base": 2, "dmg_per_grade": 1,
    "tier": 1, "defense": 1, "speed": 6
  },
  "spider": {
    "name": "ICE — Spider",
    "hp_base": 40, "hp_per_grade": 8,
    "dmg_base": 4, "dmg_per_grade": 1,
    "tier": 1, "defense": 0, "speed": 8
  },
  "black": {
    "name": "ICE — Black",
    "hp_base": 200, "hp_per_grade": 40,
    "dmg_base": 8, "dmg_per_grade": 2,
    "tier": 3, "defense": 5, "speed": 4
  },
  "goliath": {
    "name": "ICE — Goliath",
    "hp_base": 150, "hp_per_grade": 30,
    "dmg_base": 5, "dmg_per_grade": 2,
    "tier": 3, "defense": 8, "speed": 3
  },
  "dixie": {
    "name": "Construct — Dixie",
    "hp_base": 300, "hp_per_grade": 60,
    "dmg_base": 6, "dmg_per_grade": 3,
    "tier": 4, "defense": 10, "speed": 4
  },
  "raven": {
    "name": "ICE — Raven",
    "hp_base": 60, "hp_per_grade": 12,
    "dmg_base": 5, "dmg_per_grade": 2,
    "tier": 2, "defense": 2, "speed": 7
  },
  "wisp": {
    "name": "ICE — Wisp",
    "hp_base": 35, "hp_per_grade": 5,
    "dmg_base": 2, "dmg_per_grade": 0,
    "tier": 1, "defense": 0, "speed": 10
  }
}
```

---

## 4. NPC 스테이터스 (전투용)

### 4.1 NPC Combat Stats

```python
@dataclass
class NPCStats:
    npc_id:    NPCId
    name:      str
    tier:      int           # 1-5 (Player Grade 대응)
    hp_base:   int
    dmg_base:  int
    skills:    tuple[SkillId, ...]
    ally:      bool          # True = 아군, False = 적대적
    dialogue:  DialogueTree  # 기존 dialogue 시스템 재활용
```

### 4.2 주요 NPC 스펙

```json
{
  "FINN": {
    "name": "Finn",
    "tier": 3,
    "hp_base": 120,
    "dmg_base": 4,
    "skills": ["negotiate", "data_theft"],
    "ally": true
  },
  "MOLLY": {
    "name": "Molly",
    "tier": 4,
    "hp_base": 180,
    "dmg_base": 6,
    "skills": ["razor_attack", "stealth"],
    "ally": true
  },
  "DIXIE_FLATLINE": {
    "name": "Dixie Flatline",
    "tier": 5,
    "hp_base": 250,
    "dmg_base": 8,
    "skills": ["ice_breaker", "construct_summon"],
    "ally": true
  },
  "ARMITAGE": {
    "name": "Armitage",
    "tier": 3,
    "hp_base": 100,
    "dmg_base": 3,
    "skills": ["tactical_support"],
    "ally": true
  }
}
```

---

## 5. 아이템 & 장비 시스템

### 5.1 Equipment Tier → Grade 연관

```python
EquipTier: enum:
    T0_BASELINE = 0  # 시작 장비 (Grade 1만)
    T1_STREET = 1    # Grade 1+
    T2_COMMERCIAL = 2  # Grade 2+
    T3_MILITECH = 3     # Grade 3+
    T4_CORPORATE = 4    # Grade 4+
    T5_EXPERIMENTAL = 5  # Grade 5 전용

# Grade별 사용 가능한 Tier
GRADE_TIER_ACCESS = {
    1: {T0_BASELINE, T1_STREET},
    2: {T1_STREET, T2_COMMERCIAL},
    3: {T2_COMMERCIAL, T3_MILITECH},
    4: {T3_MILITECH, T4_CORPORATE},
    5: {T4_CORPORATE, T5_EXPERIMENTAL},
}
```

### 5.2 스킬 트리 (Simplified)

```python
SKILL_TREE = {
    # Combat Branch
    "attack_1": {"name": "Strike", "tier": 1, "grade_req": 1},
    "attack_2": {"name": "Heavy Strike", "tier": 2, "grade_req": 2},
    "attack_3": {"name": "Devastate", "tier": 3, "grade_req": 3},
    "crit_1": {"name": "Precision", "tier": 1, "grade_req": 1},
    "crit_2": {"name": "Deadly Aim", "tier": 2, "grade_req": 2},

    # Defense Branch
    "shield_1": {"name": "Shield", "tier": 1, "grade_req": 1},
    "shield_2": {"name": "Fortress", "tier": 2, "grade_req": 2},
    "heal_1": {"name": "Repair", "tier": 1, "grade_req": 1},
    "heal_2": {"name": "Emergency Repair", "tier": 2, "grade_req": 3},

    # ICE Branch
    "ice_break_1": {"name": "ICE Crack", "tier": 1, "grade_req": 1},
    "ice_break_2": {"name": "ICE Shatter", "tier": 2, "grade_req": 2},
    "ice_break_3": {"name": "ICE Annihilate", "tier": 3, "grade_req": 3},

    # Utility Branch
    "detect_1": {"name": "Scan", "tier": 1, "grade_req": 1},
    "speed_1": {"name": "Haste", "tier": 1, "grade_req": 2},
    "lifesteal_1": {"name": "Drain", "tier": 2, "grade_req": 3},
}
```

### 5.3 아이템 드롭 & 보상

```python
LOOT_TABLES = {
    "watchdog": [
        ("ice_shard", 0.8, 1),    # 80% chance, 1 item
        ("data_fragment", 0.3, 1),
    ],
    "black_ice": [
        ("ice_shard", 1.0, 2),
        ("data_fragment", 0.6, 2),
        ("combat_module", 0.2, 1),
    ],
    "goliath": [
        ("ice_shard", 1.0, 3),
        ("combat_module", 0.5, 1),
        ("construct_shard", 0.3, 1),
    ],
    "boss_dixie": [
        ("construct_shard", 1.0, 2),
        ("ice_construct", 0.5, 1),
        ("rom_echo", 0.3, 1),
    ],
}
```

---

## 6. Stage 난이도 연동

### 6.1 Phase → Difficulty 매핑

```python
PhaseDifficulty = {
    "WAIT":     "tutorial",      # 전투 없음, 연출만
    "BRIEFING": "story",          # NPC 대화, 전투 없음
    "JACK_IN":  "easy",          # T1 적 1-2기
    "EXTRACT":  "normal",        # T1-T2 적 2-3기
    "DEBRIEF":  "story",          # 전투 없음
}

@dataclass
class StageConfig:
    phase:       Phase
    difficulty:  DifficultyLevel
    enemies:     list[EnemySpawn]
    loot:        list[tuple[str, float, int]]  # item, chance, quantity
    xp_reward:   int
    credit_reward: int
    narrative_beats: list[str]
```

### 6.2 케이 Ch1 스테이지 설계

```
챕터 1: The First Run
├── Phase 0: WAIT (CHATTO'S 24/7)
│   └── 난이도: tutorial
│       └── 보상: XP 0, 크레딧 0
│
├── Phase 1: BRIEFING (Finn과의 미션 브리핑)
│   └── 난이도: story
│       └── 보상: XP 20 (대화 완료)
│
├── Phase 2: JACK_IN (Wisp T1 우회 + 탐색)
│   └── 난이도: easy
│       ├── 적: Wisp x1 (HP 35, DMG 2, T1)
│       ├── 보상: XP 50, 크레딧 100
│       └── 데이터 추출: +1 data_fragment
│
├── Phase 3: EXTRACT_DATA (Watchdog T1 격파 + 데이터 추출)
│   └── 난이도: normal
│       ├── 적: Watchdog x1 (HP 50, DMG 2, T1)
│       │        Spider x1 (HP 40, DMG 4, T1) [선택]
│       ├── 보상: XP 100, 크레딧 200
│       └── 데이터: +2 data_fragment
│
└── Phase 4: DEBRIEF (재림크)
    └── 난이도: story
        └── 보상: XP 150 (챕터 완료), 크레딧 300, Grade 1→2 체크
```

### 6.3 케이 Ch2 스테이지 설계

```
챕터 2: The Hunt
├── Phase 0: JACK_IN (Raven x2, Standard x1)
│   └── 난이도: easy-normal
│       ├── 적: Raven x2 (HP 60, DMG 5, T2)
│       │        Standard x1 (HP 80, DMG 3, T1)
│       └── 보상: XP 120, 크레딧 250
│
├── Phase 1: HUNT (Black Ice T3 조우)
│   └── 난이도: hard
│       ├── 적: Black x1 (HP 200, DMG 8, T3)
│       │        Standard x2 (HP 80, DMG 3, T1)
│       └── 보상: XP 200, 크레딧 400
│
├── Phase 2: EXTRACT (Goliath T3 + 네비게이션 퍼즐)
│   └── 난이도: hard
│       ├── 적: Goliath x1 (HP 150, DMG 5, T3)
│       │        Spider x2 (HP 40, DMG 4, T1)
│       └── 보상: XP 300, 크레딧 500
│
└── Phase 3: DEBRIEF (재림크)
    └── 보상: XP 400, 크레딧 800, Grade 2→3 체크
```

### 6.4 적配置 공식 (Player Grade 기준)

```python
def get_stage_enemies(phase: Phase, player_grade: int) -> list[EnemySpawn]:
    """Phase와 Player Grade 기반 적 구성"""

    base_enemies = {
        Phase.JACK_IN: [
            {"id": "wisp", "count": 1, "tier": max(1, player_grade - 1)},
            {"id": "standard", "count": 0, "tier": player_grade},
        ],
        Phase.EXTRACT: [
            {"id": "watchdog", "count": 1, "tier": max(1, player_grade - 1)},
            {"id": "spider", "count": 1, "tier": max(1, player_grade - 2)},
        ],
    }

    enemies = []
    for e in base_enemies.get(phase, []):
        if e["count"] > 0:
            for _ in range(e["count"]):
                enemies.append(EnemySpawn(
                    ice_id=e["id"],
                    tier=e["tier"],
                    scaled=True,  # Grade 기반 스케일 적용
                ))
    return enemies
```

---

## 7. 데모 검증용 초기 상태

### 7.1 데모 시나리오별 초기 장비

**데모 시나리오 A: Grade 1 (초보자)**
```python
demo_grade_1 = {
    "grade": 1,
    "ppl": 5,
    "loadout": {
        "deck": "T1_STREET_DECK",
        "programs": ["T1_ATTACK", "T1_SHIELD"],
        "wetware": "T1_WETWARE",
        "construct": None,
    },
    "skills": ["attack_1", "shield_1"],
    "inventory": {"ice_shard": 2, "data_fragment": 1},
    "credits": 100,
}
```

**데모 시나리오 B: Grade 3 (중급자)**
```python
demo_grade_3 = {
    "grade": 3,
    "ppl": 22,
    "loadout": {
        "deck": "T2_COMMERCIAL_DECK",
        "programs": ["T2_ATTACK", "T1_SHIELD", "T1_DETECT"],
        "wetware": "T2_WETWARE",
        "construct": "T1_CONSTRUCT",
    },
    "skills": ["attack_2", "shield_2", "heal_1", "detect_1"],
    "inventory": {"ice_shard": 10, "data_fragment": 5, "combat_module": 2},
    "credits": 500,
}
```

**데모 시나리오 C: Grade 5 (고급자)**
```python
demo_grade_5 = {
    "grade": 5,
    "ppl": 45,
    "loadout": {
        "deck": "T4_CORPORATE_DECK",
        "programs": ["T3_ATTACK", "T3_HEAVY", "T2_SHIELD", "T2_DETECT"],
        "wetware": "T3_WETWARE",
        "construct": "T2_CONSTRUCT",
    },
    "skills": ["attack_3", "heal_2", "ice_break_2", "lifesteal_1"],
    "inventory": {"ice_shard": 20, "data_fragment": 15, "combat_module": 5, "construct_shard": 3},
    "credits": 2000,
}
```

### 7.2 데모 시나리오별 적 구성

| 시나리오 | Grade | PPL | 적 구성 | 난이도 |
|---------|-------|-----|---------|--------|
| A | 1 | 5 | Wisp x1 | Easy |
| B | 3 | 22 | Watchdog x2, Spider x1 | Normal |
| C | 5 | 45 | Black x1, Goliath x1 | Hard |

---

## 8. 난이도 검증 공식

### 8.1 PPL vs Enemy Power 비교

```python
EnemyPower = Σ(HP_i * DMG_i) / 적 수량  # 적 전체 전투력

PowerRatio = PlayerPPL / EnemyPower

# 난이도判定:
# < 0.5: Very Hard (클리어 어려움)
# 0.5 - 0.8: Hard (전략 필요)
# 0.8 - 1.2: Normal (적절한 도전)
# 1.2 - 1.5: Easy (여유)
# > 1.5: Very Easy (압도적)
```

### 8.2 전투 시간 예측

```python
def predict_combat_time(player_ppl: int, enemies: list[EnemySpawn]) -> float:
    """전투 예상 시간 (초)"""
    total_enemy_hp = sum(e.hp for e in enemies)
    player_dps = (player_pPL / 10) * 1.5  # 대략적 DPS

    enemy_dps = sum(e.dmg for e in enemies) / 2  # 적 총 DPS
    player_effective_hp = player.max_hp / max(1, enemy_dps / 10)

    # 상호 교전 시간
    time_to_kill = total_enemy_hp / player_dps
    time_to_die = player_effective_hp / enemy_dps

    return min(time_to_kill, time_to_die) * 10  # tick 단위 변환
```

### 8.3 권장 수치

| 지표 | Easy | Normal | Hard | Very Hard |
|------|------|--------|------|-----------|
| PPL Ratio | 1.5+ | 1.0-1.5 | 0.7-1.0 | <0.7 |
| 전투 시간 | <30s | 30-60s | 60-120s | 120s+ |
| 회복 Items 필요 | 0 | 1-2 | 2-3 | 3+ |

---

## 9. 구현 체크리스트

- [ ] `ICEStats` dataclass + `ice_types.json` 확장 (tier, hp_per_grade, dmg_per_grade)
- [ ] `ICEStats.get_scaled(grade)` 메서드
- [ ] `NPCStats` dataclass + NPC 전투력 데이터
- [ ] `PlayerProgression` (XP, skill_points)
- [ ] Grade → PPL 범위 검증 로직
- [ ] `get_stage_enemies(phase, grade)` 공식 구현
- [ ] 데모 시나리오별 초기 상태 설정 함수
- [ ] `PowerRatio` 난이도 계산
- [ ] UI에 Grade/PPL/적 Tier 표시

---

## 10. 관련 파일

| 파일 | 변경사항 |
|------|---------|
| `src/wet_run/combat/state.py` | CombatStats 확장 |
| `src/wet_run/combat/registry.py` | ICE 스케일링 로직 추가 |
| `data/combat/ice_types.json` | tier, hp_per_grade, dmg_per_grade 필드 추가 |
| `src/wet_run/engine/state.py` | PlayerProgression 추가 |
| `src/wet_run/engine/npc_event.py` | NPCStats 추가 |
| `src/wet_run/engine/phase.py` | StageConfig 정의 |
| `scripts/demo.py` | 시나리오별 초기 상태 함수 |
