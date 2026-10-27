# ADR-0219: Non-damaging ICE 스킬 효과의 운명 (shield / heal / regen / buff / detect)

**상태**: Draft
**날짜**: 2026-10-27
**결정자**: 사용자
**우선순위**: P1 (The Flatline — dead combat path, ADR-0216/0218 sibling)
**관련**: [ADR-0161 — personality archetypes](./0161-ice-personality-archetypes.md), [ADR-0211 — ICE grade scaling](./0211-ice-grade-scaling.md), [ADR-0216 — derived ICE skill metadata](./0216-derived-ice-skill-metadata.md), [ADR-0217](./0217-continue-restores-playable-run.md), [ADR-0218 — ICE skill selection fallback](./0218-ice-skill-selection-fallback.md)

> **이 문서는 결정 요청 (decision request) 이다.** 코드는 **한 줄도 변경되지 않았다.**
> 아래 세 항목 — non-damaging 효과 구현, 88개 스킬 메타데이터 authoring, encounter band
> 커버리지 확대 — 는 **모두 착수되지 않은 상태**다. 사용자가 Option 을 고른 뒤에만
> 구현 작업이 시작된다.

## 컨텍스트 (Context)

### 문제 — non-damaging ICE 스킬은 구조적으로 발사될 수 없다

production combat path (`web/src/core/state_actions_combat.ts`) 는 enemy 가 스킬을
**실제로 발사하는 조건** 이 `selectedSkill.damage > 0` 이다
(`web/src/core/state_actions_combat.ts:230`). 조건을 만족하지 못하면 `usedSkill` 가
false 로 남고, 같은 함수의 plain auto-attack 분기로 fall through 한다
(`web/src/core/state_actions_combat.ts:246`).

`damage` 는 loader (`web/src/core/ice_skills.ts`) 가 **파생**한다. offensive effect 면
ICE row 의 `dmg_base`, non-damaging effect 면 **0**
(`web/src/core/ice_skills.ts:143` — `damage: ICE_SKILL_NON_DAMAGE_EFFECTS.has(effect) ? 0 : damageBase`).
non-damaging effect 목록은 `shield / heal / regen / buff / debuff / detect / stun / slow / silence`
9개 (`web/src/core/ice_skills.ts:66-76`).

즉 **`damage > 0` 인 스킬만 발사 가능하고, 나머지는 발사 자체가 불가능**하다.
ADR-0218 이 fallback 을 고쳤지만 (usable skill 을 먼저 고르도록), **preference 매칭이
non-damaging 스킬을 먼저 반환하는 경우**는 그대로 남았다. ADR-0218 의 "Remaining Gap"
섹션이 이 ADR 이다.

### personality preference list 의 구조적 불가관측성

`PERSONALITY_SKILL_PREFERENCE` (`web/src/core/ice_ai.ts:147-154`):

| archetype | preference list (우선순위 순) |
| --- | --- |
| `aggressive` | heavy_attack, pierce, multi_hit, attack, lifesteal |
| `defensive` | **shield, heal, regen, buff**, attack |
| `stealth` | dot, poison, debuff, silence, slow |
| `support` | **heal, regen, shield, debuff, detect** |

`defensive` 와 `support` 의 상위 선호는 전부 combat path 가 발사할 수 없는 effect 다.
`stealth` 의 preference 도 `silence`/`slow`/`debuff` 는 non-damaging 목록에 들어 있어
부분적으로 불가관측이다.

### 왜 아직 문제가 "안 보인다" — 두 가지 억제 요인

**(1) catalog 실측.** `web/src/data/ice_types.json` 의 personality 분포는
`aggressive` 80 / `defensive` 12 / `stealth` 5 / **`support` 0** 이다.
**`support` archetype ICE 는 한 종도 존재하지 않는다.** 게다가 12종 `defensive` ICE 중
`skills` 를 가진 것은 5종뿐이고 (`corporate_guard`, `archive_sentinel`, `ta_sentinel`,
`watchdog_ascended`, `watchdog_defensive`), 그 중 `watchdog_defensive` 의 스킬
(`shield_protocol`, `absorb_damage`) 만 실제 non-damaging effect 로 파생된다.

**(2) encounter band 실측.** `ENCOUNTER_ICE_BY_GRADE` (`web/src/core/ice_scaling.ts:30-37`)
의 24개 항목 (18 unique id) 중 **스킬을 가진 것은 2개뿐**이다:
`loa_entity` (g5) 와 `aleph` (g6). 두 ICE 모두 `aggressive` personality 다.
band 안의 `defensive` ICE 2종 (`watchdog`, `ice_neuromancer_warden`) 은
**스킬이 아예 없다** (`skills: []`).

결국 **지금 observable 한 dead configuration 은 사실상 없다.** 이 ADR 가 다루는
문제는 "지금 고장난 것"이 아니라 "archetype 시스템의 절반이 설계상 구현되지 않은
상태이며, 그 사실을 결정으로 고쳐야 한다"는 것이다.

### 데이터의 부재 — magnitude 를 말할 수 없다

`web/src/data/ice_types.json` 의 ICE row 는 `dmg_base / dmg_per_grade / hp_base /
hp_per_grade / tier / defense / speed / resistance` 를 가지지만, **`skills` 는 bare
ID string 배열**이다 (`"skills": ["manifest_form", "voodoo_curse"]`).
per-skill metadata (magnitude, duration, 대상) 는 **어디에도 없다.**
repo 전체의 distinct skill ID 는 **88개** (ICE 97 row 에 97 entry).

ADR-0216 이 이 공백을 loader-side derivation 으로 메웠고 (ID → typed skill object),
그 derivation 이 `damage` 를 **공격 스킬에는 `dmg_base`**, **non-damaging 스킬에는 0**
으로 정한다 (`web/src/core/ice_skills.ts:143`). 파생 규칙은 `web/src/core/ice_skills.ts:23-60` 의
token rule table 이며, `shield` effect 는 token `absorb / shield / defense / fortress /
vault / guard` 로 매칭된다 (`web/src/core/ice_skills.ts:26`).

문제는 **값이 없다**는 것이다. `shield` 가 몇을 흡수하는지, `heal` 이 몇을 회복하는지,
`buff` 가 공격력을 얼마나 올리는지에 대한 **source data 가 존재하지 않는다.**
따라서 non-damaging 효과를 구현하려면 **88개 스킬의 메타데이터를 authoring 해야
한다** — ADR-0216 이 Option 1 (hand-authored catalog) 로 명시적으로 미뤘던 그 작업.

### Enemy 측 상태 — shield / heal / buff 를 표현할 곳이 없다

web combat path 의 status effect union (`web/src/core/types.ts:236-249`) 은:

```
burn | stun | slow | silence | vulnerable | stagger | regen | powered | weakened | bleed | fatigue | confused | terrified
```

**`shield` 가 없다.** `detect` 도 없다. `StatusEffectKind` 을 실제로 쓰는 모듈은
`web/src/core/types.ts` 와 `web/src/core/status.ts` 뿐이고, enemy combat path
(`state_actions_combat.ts`, `state_actions.ts`) 는 `StatusEffectKind` 을 **한 번도
참조하지 않는다.** enemy 가 status effect 를 걸어주는 경로가 존재하지 않는다.

ICE skill 의 타입 자체도 최소다 (`web/src/core/types.ts:82-88`):

```ts
readonly skills?: ReadonlyArray<{
  id: string; name: string; effect: string; cooldownMs: number; damage: number;
}>;
```

`shield` / `heal` / `buffAmount` 같은 필드가 없다. (참고: **player** Program 쪽의
`Skill` 타입 (`web/src/core/combat_models.ts:40-61`) 은 `shield` / `heal` /
`buffAmount` 필드를 **가지고**, equipment 와 wetware 에도 `shieldBonus` 가 있다
(`web/src/core/equipment.ts:69`, `web/src/core/wetware.ts:29`). 그러니 player 측
방어 개념 자체는 존재한다. **부재하는 것은 enemy/ICE 측 non-damaging 효과 구현이다.**)

### 문서화된 의도 — prototype-era `state.shield` 스택 semantics

`docs/testcases/combat/depth.md` (Python 프로토타입 시절 문서) 는 의도된 shield
semantics 를 명시한다:

- **TC-DEPTH-004** (`docs/testcases/combat/depth.md:31-37`): "player HP 50, no shield...
  Wisp skill 1 사용 (1 AP, +1 shield, 5s) → `state.shield = 1`, player.statuses 에
  wisp 5s 추가"; skill 2 는 `state.shield = 2`, duration refresh.
- **TC-DEPTH-005** (`docs/testcases/combat/depth.md:39-44`): "player, `state.shield = 3`
  → enemy 가 10 damage 공격 → **shield 가 3 모두 흡수, 7 damage 가 player HP 에 적용**,
  Shield status 가 consumed (제거)".

즉 문서화된 설계는 **스택 카운트** (`state.shield`) + **지속 시간** + **피격 시 소모** 다.

> ⚠️ **이것은 prototype-era 문서다.** `web/` 으로 포팅되지 않았다. `web/src/core/types.ts` 의
> `StatusEffectKind` 에 `shield` 가 없고, `web/src/core/state.ts` /
> `web/src/core/combat_engine.ts` 어디에도 `shield` references 가 없다.
> `docs/testcases/` 는 "프로토타입 integration 과 함께 2026-09-15 삭제" 된 경로의
> 유산 문서다 (루트 `AGENTS.md` §2 정합 노트 참조). 따라서 이 semantics 는
> **참고 가능한 "의도"이지 현행 계약이 아니다.**

### 밸런스는 calibrate 되어 있고 evidence-backed 다

- `ENCOUNTER_HP_BY_GRADE` (`web/src/core/ice_scaling.ts:84-86`) 와
  `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` (`web/src/core/ice_scaling.ts:131-133`) 는
  ADR-0211 에서 `--runs 100` evidence 로 튜닝되었다. 각 상수의 docstring 에
  per-grade win-rate 가 기록되어 있다 (`web/src/core/ice_scaling.ts:72-82`,
  `web/src/core/ice_scaling.ts:105-120`).
- `docs/diagnostics/balance-grade-curve-root-cause-2026-09-24.md` 는 grade curve
  비단조 승률의 근본 원인 (dungeon topology 가 ICE 를 결정하고 `mission.grade` 를
  무시한다) 을 규명했다. 그 §5 "Minimal fix (NOT applied)" 가 ADR-0211/0212 로
  이어졌다.
- 현재 `npm run balance` (100 runs/mission) 출력:

  | grade | missions | win-rate | stalled | mean-turns | mean-HP-end |
  | --- | --- | --- | --- | --- | --- |
  | 1 | 4 | 100.0% | 0.0% | 2.5 | 91.7 |
  | 2 | 16 | 88.8% | 0.0% | 4.4 | 35.7 |
  | 3 | 11 | 73.0% | 0.0% | 6.1 | 24.0 |
  | 4 | 10 | 47.4% | 0.0% | 6.6 | 5.0 |
  | 5 | 9 | 42.4% | 0.0% | 5.9 | 5.6 |
  | 6 | 3 | 0.0% | 0.0% | 5.3 | 0.0 |

  이 표는 **재현 가능한 기준선 (baseline)** 이다. non-damaging 효과 구현은
  enemy 가 추가 행동을 하므로 (피해 감소, 회복, 버프) 이 표를 **반드시** 움직인다.
  재측정 없이는 ship 할 수 없다.

### 왜 이 결정이 필요한가

ADR-0218 은 fallback 만 고쳤고, 남은 gap 을 명시적으로 "본 ADR 의 범위 밖이며,
자연스러운 후속 작업"으로 남겼다 (`docs/wiki/decisions/0218-ice-skill-selection-fallback.md:157-173`).
그 후속 작업이 이것이다. 그리고 이 작업은 **밸런스 곡선을 의도적으로 다시 조율**한다.
ADR-0211 로 calibrate 된 곡선을 혼자 건드리는 것은 안 되므로, 사용자의 결정이
선행되어야 한다.

## 고려한 옵션

### 옵션 비교표

| | Option A — Full implementation | Option B — Consistency-only | Option C — 현상 유지 | Option D — 메타데이터 선행 |
| --- | --- | --- | --- | --- |
| **무엇을 하는가** | enemy combat path 에 `shield` / `heal` / `regen` / `buff` 효과를 구현한다. prototype-era `depth.md` semantics (흡수 스택 + duration) 를 근거로. | combat path 는 damage-only 로 유지한다. selection 일관성만 확보한다 — preference loop 이 발사 불가 스킬을 반환하지 않게. | 아무것도 하지 않는다. dead configuration 을 문서로 인정한다. | 88개 스킬의 메타데이터를 `ice_types.json` 에 authoring 한다. 효과 구현은 나중. |
| **필요한 신규 state** | 있음. enemy 측 `shield` 스택 / heal amount / buff amount 를 표현할 state + `StatusEffectKind` 확장 (현재 `shield` 없음). | 없음. | 없음. | 없음 (순 데이터). 단 authoring schema 신설. |
| **magnitude source** | **없음 → authoring 필요.** 88 skill ID 에 대한 per-skill 값이 존재하지 않는다. | 불필요. | 불필요. | **이 옵션이 바로 그 작업이다.** |
| **밸런스 재측정** | **필수.** `ENCOUNTER_HP_BY_GRADE` / `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` (ADR-0211) 를 grade 별로 재-calibration 하고 `npm run balance` 로 재측정. | **불필요** 예상. combat path 의 damage 계산이 바뀌지 않는다. | 불필요. | 불필요 (데이터만, combat 불변). |
| **effort** | 최대. mechanics + state + 88 metadata + 밸런스 + 회귀 테스트. | 최소. selection 로직 1곳 + preference table 정리. | 0. | 중간. 88 entry hand-authoring + loader 갱신. |
| **risk** | 높음. 새 mechanic 이 밸런스 전체를 움직이고, 두 개의 calibrated 상수를 손대야 한다. 되돌리기 어려움 (데이터 + 밸런스 동시 변경). | 낮음. combat path 무변경. 되돌리기 쉬움. | 0. | 낮음. combat 무변경. 단 hand-maintained 데이터 오류 위험이 있고, ADR-0216 의 derivation 을 대체해야 해 loader 도 건드린다. |
| **reach (실제 플레이 영향)** | **거의 없다.** band 24 항목 중 스킬 보유는 `loa_entity` (g5) / `aleph` (g6) 뿐이고 둘 다 `aggressive` 다. `defensive` ICE 는 band 안에서 스킬이 없다. | 거의 없다 (마찬가지). | 0. | 0 (구현 전). |
| **archetype 해방** | `defensive` / `support` 가 의미를 갖게 된다. 단 **`support` ICE 가 catalog 에 0종**이라 `support` 는 여전히 비어 있다 — 해방되지 않는다. | 아니다. `defensive` / `support` preference list 는 **여전히 cosmetic**. 구현 불가 entry 를 제거하면 list 는 "공격만 있는 ICE" 가 되어 archetype 차이 자체가 사라진다. | 아니다. | 아니다 (구현 전). |
| **reversibility** | 낮음. 밸런스 상수 + 데이터 + 메커닉이 함께 바뀌어 부분 되돌리기가 어렵다. | 높음. 단일 로직 변경. | — | 높음. 데이터 되돌리기로 충분. |

### Option A — Full implementation

- **설명**: web combat path 에 non-damaging 효과를 구현한다. prototype-era
  `docs/testcases/combat/depth.md:31-44` semantics 를 근거로 — `shield` 는
  스택 카운트 + duration, `heal` / `regen` 은 HP 회복 (`maxHp` 상한), `buff` 는
  공격력 보너스. `StatusEffectKind` 에 `shield` (와 필요시 `detect`) 를 추가하고
  enemy 측 status application 경로를 만든다. magnitude 는 **88개 스킬 metadata 를
  authoring** 해서 공급한다. 마지막으로 `ENCOUNTER_HP_BY_GRADE` /
  `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` 를 재-calibration 하고 `npm run balance` 로
  재측정한다.
- **장점**:
  - `defensive` archetype 가 실제로 다른 행동을 한다 — 지금은 완전히 관측 불가.
  - prototype-era 설계가 문서로 남아 있으므로 semantics 근거가 방대하지 않다.
  - 근본 원인 (효과 미구현) 을 제거한다.
- **단점**:
  - **reach 가 거의 없다.** band 안 스킬 보유 ICE 2종은 둘 다 `aggressive` 다.
    구현만 하고 band 를 안 건드리면 플레이에서 체감이 거의 없다. 가시성을 높이려면
    `ENCOUNTER_ICE_BY_GRADE` 도 함께 바꿔야 하는데, **그것은 별도의 밸런스 결정**이다.
  - **`support` archetype 는 해방되지 않는다.** catalog 에 `support` ICE 가 0종이다.
    `support` preference list 는 스킬을 authoring 해도 매칭될 대상이 없다.
  - 88개 metadata authoring 은 손 작업이고, 그 품질이 곧 밸런스가 된다.
  - calibrated 밸런스 상수 2개 + 메커닉을 동시에 바꾸므로 되돌리기 어렵다.
- **Pillar 정합**:
  - P3 (The Flatline): ✅ 관측 불가 archetype 를 관측 가능하게 한다.
  - P5 (The Style): ⚠️ ID token 기반 effect 매칭 (`ice_skills.ts:23-60`) 은 authoring
    데이터로 대체하는 편이 flavor 에 가깝다.

### Option B — Consistency-only (새 메커닉 없음)

- **설명**: combat path 는 damage-only 로 유지한다. 대신 selection 을 일관되게 만든다 —
  preference loop 이 **발사 가능한 스킬**만 반환하도록 하거나, preference table 에서
  구현 불가 effect 를 제거해 표와 코드가 일치하게 한다. 발사 가능한 스킬이 하나도
  없는 ICE 는 깔끔하게 auto-attack 으로 떨어진다 (ADR-0218 의 fallback 이 이미
  `availableSkills.find((s) => s.damage > 0) ?? availableSkills[0] ?? null` 로
  정리되어 있다 — `web/src/core/ice_ai.ts:192`).
- **장점**:
  - combat path 무변경 → 밸런스 재측정 불필요, `npm run balance` 출력이 그대로.
  - 새 state 없음, 새 dependency 없음, diff 최소.
  - "Archetype 시스템이 절반 구현되지 않았다" 는 사실을 **코드와 문서 양쪽에서
    정직하게 드러낸다.**
  - 되돌리기 쉽다.
- **단점**:
  - **`defensive` / `support` preference list 는 여전히 cosmetic.** 구현 불가 entry 를
    제거하면 그 archetype 는 "공격만 하는, 더 약한 aggressive" 가 된다. 그러면
    archetype 자체가 사라진다 — list 를 유지하면 dead config, 제거하면 archetype 소멸.
    둘 중 어느 쪽이든 **아키텍처 결정이 필요**하다 (열린 질문 참조).
  - `defensive` ICE 12종 중 band 안의 2종은 스킬이 없어 preference 매칭 자체가
    일어나지 않는다. 이건 Option B 로도 고쳐지지 않는다 (데이터 문제).
- **Pillar 정합**:
  - P3 (The Flatline): ✅ dead path 의 **관측 가능성**은 정리되지만, 기능이 늘지는 않는다.
  - P5 (The Style): ⚠️ flavor loss 가능 (아키텍처 표가 드러나게 줄어듦).

### Option C — 현상 유지 (no-op)

- **설명**: 아무것도 바꾸지 않는다. dead configuration 을 문서로 인정한다.
- **장점**: 리스크 0. 코드·데이터·밸런스 전부 그대로.
- **단점**: ADR-0218 의 "Remaining Gap" 이 영구 미해결로 남는다. `defensive` /
  `support` archetype 는 계약이 아니라 죽은 데이터다.
- **Pillar 정합**: 실패 (설계 의도가 코드에 반영되지 않는다).

### Option D — 메커닉은 유예하고 데이터부터

- **설명**: 88개 스킬의 메타데이터를 `ice_types.json` 에 authoring 한다. ADR-0216 의
  loader-side derivation (`web/src/core/ice_skills.ts:23-60` token rule + `:143` damage
  규칙) 을 authored data 로 대체한다. 효과 자체는 아직 구현하지 않는다.
- **장점**:
  - Option A 의 최대 비용 항목 (magnitude 부재) 이 해소된다. 나중에 mechanics 를
    넣을 때 authoring 작업이 필요 없다.
  - ADR-0216 이 Option 1 로 명시적으로 미룬 그 작업이다.
  - combat path 무변경 → 밸런스 재측정 불필요.
- **단점**:
  - **hand-maintained 데이터 88 entry 를 작성·검토해야 한다.** ADR-0216 이 이걸
    "단기 shipping 불가" 로 미룬 이유다.
  - **그 자체로는 아무것도 안 보인다.** 구현이 없으므로 플레이에 변화가 없다.
  - ADR-0216 의 derivation 을 대체하므로 loader 도 건드려야 한다 — diff 가
    "데이터만" 에서는 끝나지 않는다.
  - combat 무변경 상태에서 metadata 를 authoring 하면, ADR-0218 이 만든
    `damage > 0` 규칙과 authored 값의 관계를 다시 정의해야 한다 (authored `damage`
    가 0 이면 발 불가 — 지금과 동일한 contract 가 authored data 에서도 성립해야 함).
- **Pillar 정합**:
  - P4 (The Build): ✅ 데이터 기반 설계의 정합성 회복, 단 유지보수 부담.

## 추천 (Recommendation)

**B 지금 → D 를 그 선행으로 → A 는 별도 feature 로.** 순서대로 말하면:

1. **Option B 를 지금 결정한다.** selection 일관성만 확보한다. 새 메커닉 없이,
   combat path 를 건드리지 않고, 밸런스 재측정 없이, "archetype 의 절반이 구현되지
   않았다"는 사실을 코드가 아니라 **의사 결정**으로 정리한다.
2. **Option D 를 B 의 후행으로 결정한다.** B 는 "preference 가 발사 불가 스킬을
   지목하면 어쩌나"를 답하지만 magnitude 문제는 그대로 남는다. D 가 그 해법이다.
   D 는 데이터 작업이라 밸런스 측정과 분리되고 되돌릴 수 있다.
3. **Option A 는 별도 feature 로 미룬다.** A 는 밸런스 곡선을 다시 조율하는 결정이고,
   reach 가 거의 없다. 지금 하면 calibrated 상수 두 개를 흔들면서도 플레이에서
   체감하기 어렵다.

**이 순서를 택한 이유:**

- **(a) 현재 시스템은 부분적으로만 cosmetic 이다.** `support` archetype 는 catalog 에
  **0종**이고, band 안의 `defensive` ICE 2종은 **스킬이 없다**. 즉 "구현하면
  archetype 가 살아난다" 는 전제 자체가 약하다. A 를 지금 해도 `support` 는 그대로
  비어 있고 `defensive` 는 band 밖 12종 중 5종이 스킬을 가질 뿐이다.
- **(b) 밸런스 곡선은 calibrate 되어 있고 재측정 비용이 크다.** ADR-0211 은
  `--runs 100` evidence 로 두 상수를 튜닝했고, 그 근거가 docstring 에 남아 있다.
  A 는 그 두 상수를 반드시 손대야 한다. reach 가 좁은 (= 측정 신호가 작은) 상태에서
  곡선을 흔들면 **재현 가능한 근거 없이 튜닝하게 된다.**
- **(c) reach 가 좁다.** band 24 항목 중 스킬 보유는 2개이고 둘 다 `aggressive` 다.
  A 는 `ENCOUNTER_ICE_BY_GRADE` 변경 없이는 거의 보이지 않는다 — 그런데 band 를
  바꾸는 것은 그 자체로 별도의 밸런스 결정이다.
- **(d) B 는 되돌릴 수 있고, D 는 되돌릴 수 있고, A 는 아니다.** A 는 메커닉 +
  데이터 + 밸런스를 한 묶음으로 바꾸므로 부분 되돌리기가 어렵다. B/D 는 각각
  독립적이고 격리 가능하다.
- **(e) B 는 "dead config" 를 "dead config 으로 유지" 가 아니라 "정직한 contract" 로
  바꾼다.** preference 가 발사 불가 effect 를 지목하지 않게 하면, archetype table
  과 combat path 사이에 거짓말이 없어진다.

**이 추천이 틀린 경우** — B 가 충분하지 않다고 판단되는 근거는 (c) 의 reach 문제다.
`ENCOUNTER_ICE_BY_GRADE` 를 함께 넓혀서 (i) `defensive` ICE 를 band 에 넣고,
(ii) `support` archetype ICE 를 catalog 에 최소 1종 추가하면, A 의 가시성이 생긴다.
하지만 그 두 변경은 **밸런스 결정**이며 별도 ADR 대상이다.

## 열린 질문 (Open Questions)

1. **ICE `shield` 는 stack 되나, duration 으로 소멸하나, hit count 로 소멸하나?**
   prototype-era `docs/testcases/combat/depth.md:31-37` 은 **stack + duration refresh**
   (TC-DEPTH-004), `:39-44` 는 **피격 시 소모** (TC-DEPTH-005, "shield 가 3 모두
   흡수... Shield status 가 consumed") 를 함께 서술한다. **stack + duration + hit-count
   중 무엇이 정칙인가, 아니면 셋을 합치는가?** 이 답이 metadata schema 를 결정한다.
2. **`heal` 은 `maxHp` 를 넘을 수 있는가?** — **안 된다** (cap 한다). 단 `regen` 은
   tick 단위 회복이므로 cap 규칙과 "회복 우선순위" (HP가 낮을수록 먼저 회복?) 를
   정해야 한다. `heal` 과 `regen` 이 별개 effect 인 이유가 있는가?
3. **`detect` / `silence` / `slow` 는 combat effect 가 아니라 alarm system 이나
   information mechanic 이어야 하는가?** `detect` 는 현재 `StatusEffectKind` 에도 없고
   enemy path 어디에도 없다. `silence`/`slow` 는 `StatusEffectKind` 에 **있지만**
   enemy combat path 는 `StatusEffectKind` 을 참조하지 않는다. 이 셋이 "전투 내부
   status" 인지 "alarm / stealth 시스템과 interact" 해야 하는지 결정해야
   archetype semantics 가 갈린다. (참고: `stealth_only` mutator filter 는 이미
   `silence`/`slow`/`debuff`/`dot`/`poison` 을 effect 문자열로 걸러낸다 —
   `web/src/core/state_actions_combat.ts:208-213`.)
4. **Option B 를 택하면 preference table 을 발사 가능 effect 만으로 trim 할 것인가,
   아니면 dead entry 를 남기고 "미구현" 으로 표기할 것인가?** trim 은 `defensive` /
   `support` 를 사실상 지우고 archetype 구분을 없앤다. 남기면 list 의 상대 순서가
   여전히 무의미하다. 어느 쪽이든 **ICE flavor 의 의도** (ADR-0161 가 만든
   `defensive` / `support` 상상)와 충돌하므로, 그 의도가 무엇이었는지 확인해야 한다.
5. **`support` archetype ICE 를 catalog 에 추가해야 하는가?** 현재 `support` 는
   **0종**이다. 구현하지 않으면 `support` preference list 는 영원히 dead다.
   추가한다면 88 metadata authoring 범위에 "새 ICE row + skill" 가 포함된다.
6. **Option A 를 택하면 밸런스 재-calibration 의 owner 는 누구인가?** `ENCOUNTER_HP_BY_GRADE`
   와 `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` 를 다시 튜닝해야 하고, 근거는
   `npm run balance` 의 `--runs` 출력이다. "재측정 몇 회, 어떤 목표 band" 같은
   기준을 이 ADR (또는 후속 ADR) 가 정해야 한다. 목표 band 자체가 바뀔 수도 있다.
7. **`ENCOUNTER_ICE_BY_GRADE` 확대는 이 ADR 의 범위에 포함되는가, 별도 ADR 인가?**
   A 의 가시성은 band 의 내용에 달려 있다 (reach 2/18). band 확대는 밸런스 결정이므로
   분리하는 편이 명확하다.
8. **88 metadata 의 authoring 은 어느 granularity 인가?** skill id 별 개별 entry,
   아니면 archetype/ICE-family 별 template + 예외 목록? 후자는 작성량은 적지만
   "88개 각각의 값" 이라는 ADR-0216 Option 1 의 의도와 어긋난다.

## 사용자 결정 (Decision)

[ ] Option A — Full implementation (non-damaging 효과 + metadata + 밸런스 재-calibration)
[ ] Option B — Consistency-only (새 메커닉 없이 selection 일관성만)
[ ] Option C — 현상 유지 (no-op)
[ ] Option D — 메타데이터 선행 authoring (효과 구현은 별도)
[ ] B → D → A 순차 (AI 추천안)
[ ] 기타: ___
[ ] Defer (다음 단계로 미룸)

## 결과 (Consequences)

(결정 후 작성 — 사용자가 Option 을 선택하면 이 섹션과 Implementation Status 를 채운다.)

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ❌ Not started

**Evidence**:
- 이 ADR 은 **코드를 변경하지 않았다.** `web/` 아래 어떤 파일도 수정되지 않았다.
- `web/src/core/state_actions_combat.ts:230` — `selectedSkill.damage > 0` 일 때만 스킬 발화 (현행 동작, 미변경)
- `web/src/core/state_actions_combat.ts:246` — `usedSkill` false 면 plain auto-attack 으로 fall through (현행 동작, 미변경)
- `web/src/core/ice_ai.ts:147-154` — `PERSONALITY_SKILL_PREFERENCE` (현행 동작, 미변경)
- `web/src/core/ice_skills.ts:143` — non-damaging effect 의 `damage` 는 0 (현행 동작, 미변경)
- `web/src/core/ice_skills.ts:66-76` — `ICE_SKILL_NON_DAMAGE_EFFECTS` (현행 동작, 미변경)
- `web/src/core/types.ts:82-88` — ICE skill shape 에 `shield`/`heal`/`buffAmount` 필드 없음 (현행 동작, 미변경)
- `web/src/core/types.ts:236-249` — `StatusEffectKind` union 에 `shield` 없음 (현행 동작, 미변경)
- `web/src/core/ice_scaling.ts:30-37` — `ENCOUNTER_ICE_BY_GRADE` (현행 동작, 미변경)
- `web/src/core/ice_scaling.ts:84-86`, `:131-133` — `ENCOUNTER_HP_BY_GRADE` / `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` (현행 동작, 미변경)
- 기준선 측정 (2026-10-27, `npm run balance`, 100 runs/mission): g1 100.0% / g2 88.8% /
  g3 73.0% / g4 47.4% / g5 42.4% / g6 0.0%

**Notes**: 본 ADR 이 다루는 세 항목은 **모두 착수되지 않았다** —
(1) non-damaging 효과 구현, (2) 88개 스킬 metadata authoring,
(3) encounter band 커버리지 확대.
밸런스 곡선은 ADR-0211 상태 그대로이며, 재측정은 이 ADR 이 Accepted 되고
구현 범위가 정해진 뒤에만 수행한다.

## 영향 받는 항목

결정 시 영향을 받는 항목 (Option 별):

- `web/src/core/state_actions_combat.ts` — enemy combat path (Option A)
- `web/src/core/ice_ai.ts` — preference loop / `PERSONALITY_SKILL_PREFERENCE` (Option B)
- `web/src/core/ice_skills.ts` — derivation 규칙 → authored data 전환 (Option D)
- `web/src/core/types.ts` — `StatusEffectKind` (`shield` 추가) + ICE skill shape (Option A)
- `web/src/core/ice_scaling.ts` — `ENCOUNTER_HP_BY_GRADE` / `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` (Option A)
- `web/src/data/ice_types.json` — 88 스킬 metadata (Option A/D)
- `web/tests/` — 회귀 테스트 (Option 별)
- `docs/testcases/combat/depth.md` — prototype-era 문서 (Option A 시 갱신)

## 관련 결정

- ADR-0148 (aggression tiers) — `enemyShouldUseSkill` 게이트와 짝
- ADR-0161 (personality archetypes) — `PERSONALITY_SKILL_PREFERENCE` 의 의래
- ADR-0211 (ICE grade scaling) — 밸런스 상수의 owner
- ADR-0212 (grade 기반 ICE encounter 배선) — `ENCOUNTER_ICE_BY_GRADE` 의 owner
- ADR-0216 (derived ICE skill metadata) — derivation 규칙의 owner, Option D 가 대체 대상
- ADR-0217 — sibling ADR
- ADR-0218 (ICE skill selection fallback) — 본 ADR 이 답하는 "Remaining Gap" 의 출처

## 변경 이력

- 2026-10-27: Draft 작성 (결정 요청 — B → D → A 순차 추천)
