# System: Economy (재화 · 거래)

> **관련**: [progression.md](./progression.md) (메타 진행), [crafting.md](./crafting.md) (제작), [missions.md](./missions.md) (의뢰)
> **구현**: `../../prototype/src/wet_run/missions/board.py` (rewards), `data/missions/missions.json` (실제 보상)

## 목적

자키의 **런 내 자원 흐름** 정의. 두 가지 재화 — **Credits** (현금) 와 **Materials** (재료) — 가 핵심.
Pillar 4 ("The Build") 와 직결 — Credits 로 무엇을 사고, Materials 로 무엇을 만드는지.

## 재화 종류

### Credits (현금)

- **획득**: 미션 완료 보상, Data Salvage (HEAL 자리에 credit drop), 재화 노드
- **소비**: Info Market (제작 재료 구매), 의뢰인에게 bribe
- **런 간 유지**: ❌ (사망 시 0 으로 리셋)

### Materials (재료)

5 종류 (`data/crafting/materials.json`):

| ID | 이름 | 용도 |
|---|---|---|
| `data_fragment` | 데이터 단편 | T1 프로그램 제작 |
| `ice_shard` | ICE 파편 | T2 컴포넌트 제작 |
| `rom_echo` | ROM 메아리 | T2 프로그램 / T3 컴포넌트 |
| `wetware_chip` | 웻웨어 칩 | T3+ 프로그램 / wetware 업그레이드 |
| `biosoft_agent` | 바이오소프트 에이전트 | T4+ construct |

- **획득**: 전투 승리 (ICE 종류별 loot table), DATA 노드 추출
- **소비**: 제작 (5 raw → 4 components → final program/item/construct)
- **런 간 유지**: ❌ (사망 시 리셋)

### Ending Tokens (엔딩 토큰)

- **획득**: Arc 5 finale 미션 (`final_choice`)
- **소비**: 없음 (엔딩 unlock 에만 사용)

## 미션 보상 공식

**Reference 공식** (CHARACTER_PATHS.md):
```
credits = arc * 800 + (grade - 1) * 300
```

예시 (Arc 3, Grade 4): `3*800 + 3*300 = 3,300` credits

**실제 값** (data/missions/missions.json):
- Arc 1 Grade 1: 300~800 credits
- Arc 5 Grade 5: 4,500~5,500 credits
- Arc 5 Grade 6 (finale): 5,500 credits (`final_choice` 는 5,500 으로 정정됨, ADR-0060+)

> 실제 보상은 공식을 60~70% 수준으로 보수적으로 설정 — 깁슨 톤
> ("the Sprawl is not a friendly place") 에 맞춰 런이 항상 빡빡함.

### 등급별 미션 분포 (209 missions, v1.4.0)

| Grade | 미션 수 | 비고 |
|---|---:|---|
| 1 | ~40 | tutorial, watchdog_patrol, first_jack, ice_run 등 |
| 2 | ~50 | craft_job, first_trace, yakuza_deal 등 |
| 3 | ~50 | mollys_razor, ta_heist, sally_returns_arc3 등 |
| 4 | ~35 | dixies_choice, winter_infiltrate, aleph_fragment 등 |
| 5 | ~30 | final_choice, neuromancer_merger, zion_express 등 |
| 6 (Arc6 + Expansion) | ~10 | Arc6 신규 4 + Expansion 6 (ADR-0206 wiring) |

> 정확한 분포는 `prototype/data/missions/missions.json` 참조 (ADR-0208 random_weight 적용).

## 인플레이션 / 싱크

런 안에서 **재화 누적** 을 막기 위해:

- **Materials**: 인벤토리 cap (등급 5 = max 50 items)
- **Credits**: 회복 아이템 구매 시 100~500 credits 소비
- **Crafting**: 5 raw → 1 component 합성 (손실률 20%)

## 구매 가능 (Info Market)

미션 허브에서 사용 가능:
- **HEAL Pack** — 200 credits, HP +30
- **Decryption Suite** — 500 credits, 다음 ICE 의 defense -2
- **Scanner Probe** — 100 credits, 미발견 DATA 노드 위치 공개

## 런 간 손실

자키가 사망하면:
- Credits = 0
- Materials = 0 (deceased jockey 의 Hall of Dead 기록으로만 남음)
- Equipment = 0

→ 매 런은 **빈 주머니로 시작**. 메타 진행 (등급 unlock) 만 유지.

## 구현 위치

| 요소 | 파일 |
|---|---|
| 미션 보상 | `data/missions/missions.json` (`rewards.credits`) |
| 재료 | `data/crafting/materials.json` |
| 인벤토리 | `src/wet_run/engine/state.py` (AppState.inventory) |
| Credits 필드 | `src/wet_run/engine/state.py:148` |
| HEAL Pack | `src/wet_run/combat/effects.py` (ItemKind.HEAL) |

## 미래 작업 (Phase 6+)

- **고정 NPC 상인** — Info Market 외에 spacer 별 전문 상인
- **암시장** — 높은 credit 으로 blacklist 아이템 구매
- **Faction 화폐** — Hosaka/Maas/Sense-Net/TA 별 별도 currency