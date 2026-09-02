# ADR-0014: Data Salvage (전투 승리 보상 — 데이터 회수)

**상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
**날짜**: 2026-06-18
**결정자**: 사용자
**우선순위**: P1
**상위 결정**: ADR-0003 (RT-MS), ADR-0006 (Run structure), ADR-0008 (Progression), ADR-0011 (Portraits), ADR-0012 (PPL/ZDR)

## 컨텍스트

기존 디자인 (2026-06-18까지):
- HP는 일회용 자원. 회복 메카닉 없음.
- 전투에서 깎인 HP는 런 끝까지 유지. 0 = flatline (Pillar 3).
- 메타 진행 = unlock만. 능력치 누적 X (ADR-0006, ADR-0008).

사용자 결정 (2026-06-18):
> "전투 성공의 보상으로 회복 요소가 있어야 해."

요구: **전투 승리 시 플레이어에게 보상이 있어야 하고, 그 보상 중 하나는 회복**.

## 고려한 옵션

### Option 1: Data Salvage (데이터 회수) — **선택**

**설명**: ICE 격파 직후, "salvage" 선택지가 자동 표시. 플레이어가 **하나**를 고름:
- `HEAL` — HP +20% (max HP의 20%, 최소 1)
- `FRAG` — Program fragment (다음 런/현재 런에서 program 1개 unlock, Phase 6+)
- `CRED` — Credits (Info Market에서 사용, Phase 6+)
- `SKIP` — 아무것도 안 함 (위험 0, 보상 0)

**장점**:
- 깁슨 톤: ICE = 데이터. 격파 = 회수 가능. "data exposed" (core_loop.md L184)
- 플레이어 선택권: 무조건 회복이 아니라 *선택*. 전략적 깊이.
- Pillar 3 (The Flatline) 일부 완화하지만, *희생*이 있어야 회복. 무조건 회복 X.
- Pillar 5 (The Style): 데이터, 회수, construct — 깁슨 어휘와 정합.
- 메타 진행과 런 내 진행 모두에 활용 가능 (FRAG, CRED).

**단점**:
- 디시전 (HEAL vs FRAG vs CRED) 추가 — 메뉴 한 단계 더.
- HEAL만으로도 Pillar 3 약화. 하지만 *선택* + *승리 후만* 이라 *무게*는 유지.
- FRAG, CRED는 Phase 6+ 디자인 필요. Phase 5에서는 HEAL만 작동.

### Option 2: Construct Repair (구성체 수리)

**설명**: Construct 보유 시, 승리 후 construct가 repair 제안 (+30% HP, construct의 BW 소진).

**장점**: Pillar 4와 정합. construct 활용.
**단점**: construct 없을 시 회복 X → construct 의존. 1-up 자키는 construct 없음 → 효과 0. **기각**.

### Option 3: Conditional Victory Bonus (조건부 소폭 회복)

**설명**: 승리 시 자동 +5% HP (player HP > 50%일 때만).

**장점**: 구현 간단. Pillar 영향 최소.
**단점**: 보상 너무 작음, 선택권 없음, 깁슨 flavor 약함. **기각**.

### Option 4: Post-Combat Buffer (임시 버퍼)

**설명**: HP 회복 X, 다음 1~2 전투 동안 +10 temp shield.

**장점**: 깁슨답고, Pillar 영향 작음.
**단점**: "회복"이라기보다 "버퍼". 사용자 요구 ("회복 요소")와 거리. **기각**.

## 추천

**Option 1: Data Salvage** — 깁슨 정합, 플레이어 선택, FRAG/CRED로 Phase 6+ 확장.

## 사용자 결정

[x] **Option 1: Data Salvage** (2026-06-18)

## 결과 (Consequences)

### Data Salvage 흐름

```
[전투 종료: ICE HP 0]
  ↓
[Data Salvage 메뉴 — 시간 정지 유지]
  |
  > HEAL    — +20% max HP (Phase 5)
    FRAG    — program fragment (Phase 6+)
    CRED    — credits (Phase 6+)
    SKIP    — 아무것도 안 함
  |
  ↓
[선택 → 결과 표시 → 매트릭스 복귀]
```

### Phase 5 범위

- **HEAL만 작동** (FRAG, CRED는 placeholder, "Phase 6+: 미구현" 안내).
- 회복량: max HP의 20% (반올림). min 1.
- HP가 max인 상태에서 HEAL 선택 → "no damage to repair" 메시지 + 회복 0 (자원 낭비).

### Phase 6+ 확장

- **FRAG**: program 1개 unlock (런 내 — unlock이 런 내에 머무름, 메타 X)
- **CRED**: Info Market (픽서 construct)에서 정보 구매 — 미션 목표 힌트, alarm 감소 아이템 등
- 디시전 트레이드오프: HEAL 즉시 vs FRAG/CRED 장기 보상

### Disengage / Death

- **Disengage (철수)**: ICE 격파 X → salvage 없음. (이미 ADR-0003)
- **Death (자키 HP 0)**: salvage 없음. flatline.

### Pillar 정합

- **P1 (The Run)**: 한 런 = 한 무게. 회복은 *승리의 보상*. 매번 모든 전투 이길 수 없음 → 자키는 여전히 위험.
- **P2 (The Matrix)**: salvage는 매트릭스 안의 *데이터 추출*. Pillar 2 정합.
- **P3 (The Flatline)**: 
  - 회복이 *있지만* (a) 이겨야만, (b) HEAL만, (c) 20%만.
  - 무조건 회복 X. *무게*는 유지.
  - 자키가 5번 싸워서 1번 회복할 수 있는 구조 — 무게 유지.
- **P4 (The Build)**: FRAG (런 내 unlock), CRED (메타 진행) — Pillar 4와 정합.
- **P5 (The Style)**: ICE 격파 → "data exposed" → salvage — 깁슨 어휘.

### 기존 ADR 영향

- **ADR-0003 (RT-MS)**: 전투 종료 후 "salvage phase" 추가. 시간 정지 유지.
- **ADR-0006 (Run structure)**: 회복은 *메타 진행 아님*. 런 내 자원 순환.
- **ADR-0008 (Progression)**: HP 풀은 티어에 비례 (T1~T5). 회복 비율(20%)은 동일.
- **ADR-0012 (PPL/ZDR)**: ZDR/PPL 비등 시 회복으로 *살짝* 유리. 단 20%는 한계.
- **ADR-0011 (Portraits)**: ICE 격파 시 portrait fade-out 효과 (선택).

### 디자인 영향

- **`design/systems/combat.md`** (신규) — combat 시스템 명세에 salvage 흐름 추가
- **`design/core_loop.md`** — combat micro-loop에 "salvage" 단계 추가
- **`design/glossary.md`** — "Salvage" 용어 추가
- **`design/systems/economy.md`** (향후) — credits 시스템에 CRED salvage 추가
- **`design/systems/progression.md`** (향후) — FRAG salvage 추가

### 구현 영향 (Phase 5+)

- `combat/salvage.py` — `SalvageMenu`, `apply_salvage(choice, player)`
- `data/i18n/{en,ko}.json` — salvage 키 추가
- Player state: `hp: int`, `max_hp: int`
- 전투 종료 hook: ICE HP 0 → salvage menu → matrix 복귀
- HEAL 비율: 0.20 (상수, ADR로 고정)

### 향후 결정

- HEAL 비율 (20% 적절? 15%? 25%?)
- HEAL 외 추가 회복원 (픽서 repair, construct 등)
- FRAG / CRED 시스템 상세 (Phase 6+)
- 알람 / trace와 salvage의 상호작용 (alarm 높을 때 salvage 위험?)

## 영향 받는 항목

- `design/systems/combat.md` (신규)
- `design/core_loop.md`
- `design/glossary.md`
- `design/GDD.md` (Open Questions)
- `testcases/systems/combat.md` (신규)

## 관련 결정

- ADR-0003 (Accepted) — combat system
- ADR-0006 (Accepted) — run structure
- ADR-0008 (Accepted, Revised) — progression
- ADR-0012 (Accepted) — PPL/ZDR
- ADR-0013 (Accepted) — story events

## 변경 이력

- 2026-06-18: Draft 작성
- 2026-06-18: Accepted (Option 1: Data Salvage, HEAL만 Phase 5)

### Auto-conversion Confirmation (2026-08-05)

본 ADR은 사용자 결정 (질의 응답으로 confirm, 2026-08-05)에 의해 auto-convert 완료. 증거 기반 검증 통과.

**구현 증거 (2026-08-05)**: 전투 종료 시 HEAL 20% + FRAG/CRED 보상이 `combat/state.py` (30KB) 및 111개 미션(`data/missions/missions.json`)에 통합. 회수 메카닉이 combat loop에 포함되어 ADR-0014의 데이터 회수 의도가 실현됨.

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).
