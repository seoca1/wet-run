# ADR-0219: Non-damaging ICE 스킬 효과의 운명 (shield / heal / regen / buff / detect)

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — dead combat path, ADR-0216/0218 sibling)
**관련**: [ADR-0161 — personality archetypes](./0161-ice-personality-archetypes.md), [ADR-0211 — ICE grade scaling](./0211-ice-grade-scaling.md), [ADR-0216 — derived ICE skill metadata](./0216-derived-ice-skill-metadata.md), [ADR-0217](./0217-continue-restores-playable-run.md), [ADR-0218 — ICE skill selection fallback](./0218-ice-skill-selection-fallback.md)

> **이 문서는 Accepted 결정 기록이다.** 사용자는 **Option B — Consistency-only** 를
> 2026-10-27 에 선택했고, 그 구현은 완료·검증되었다.
> 구현 범위는 **selection 일관성** 하나다 — `selectSkillByPersonality` 가 combat path 가
> 발사할 수 있는 스킬 (`damage > 0`) 을 반환하도록 제한되었다.
>
> **아직 착수되지 않은 것** (본 ADR 의 범위 밖, 후속 항목):
> (1) non-damaging 효과 자체의 구현 (Option A),
> (2) 88개 스킬 메타데이터 authoring (Option D),
> (3) encounter band 커버리지 확대.
> 그 외에도 이번 구현 과정에서 **새로 발견된 loader 결함** (ADR-0216 과 동일한 결함
> 계열 — `parseIce` 가 `personality` 을 누락) 이 후속 항목으로 기록되어 있다.
> 그 밖의 옵션 (A / C / D) 은 고려되었고 **연기 (deferred)** 되었다 — 아직 어떤 것도
> 구현되지 않았다.

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

> **기록용.** Draft 시점의 AI 추천안이다. 사용자는 이 추천의 **첫 단계 (Option B)** 만
> 채택했다 (2026-10-27). 아래 2단계 (D) 와 3단계 (A) 는 **연기 (deferred)** 상태다.
> 추천안 전문은 그대로 보존한다.

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

> **1~8번은 Draft 시점의 열린 질문 목록이다.** 4번은 이번 결정에서 **답이 나갔다**
> (아래 "✅ 해결됨" 표기). 나머지는 **여전히 열린 상태**이며, Option A / D / band 확대
> 시점에 처리해야 한다. 9번은 이번 구현 과정에서 **새로 발견**된 항목이다.

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
   - ✅ **해결됨 (2026-10-27)**: **trim 하지 않는다.** `shield` / `heal` / `regen` /
     `buff` / `detect` entry 를 그대로 둔다. 근거: 이 entry 들은 Option A 가 채택되면
     즉시 의미가 갖는 **전방 지향적 설계 의도** 다. 표를 trim 하면 그 의도를 버리고
     `defensive` / `support` 를 "공격만 하는 더 약한 aggressive" 로 접는다. 대신
     **selection 시점에서** 발사 가능한 스킬만 후보로 삼는다 (Option B 의 실제 구현).
     의도는 `web/src/core/ice_ai.ts` 의 표 docstring 에 기록되어 있다.
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
9. **(신규 발견) `parseIce` 의 `personality` 누락을 언제, 어떻게 고칠 것인가?**
   `web/src/core/data_loaders.ts:236` 의 `parseIce` 는 `personality` 필드를 복사하지
   않아서 **모든 catalog ICE 가 runtime 에서 `aggressive` 로 해석된다.** Option A /
   D 를 택하기 전에라도 이걸 먼저 고쳐야 archetype 가 실제로 살아난다 (12 `defensive` +
   5 `stealth` ICE 가 `aggressive` 로 동작하는 것을 멈춘다). 단 **밸런스가 움직이므로**
   별도 결정 + 재측정이 필요하다. 범위는 "Option D 의 데이터 정합성" 에 포함하거나,
   별도 loader 정합 ADR 로 분리하는 것을 고려한다. 상세는 「결과 (Consequences) →
   남은 gap (1)」.

## 사용자 결정 (Decision)

**2026-10-27 — 사용자가 Option B (Consistency-only) 를 선택했다.** 구현 완료·검증됨.

- [ ] Option A — Full implementation (non-damaging 효과 + metadata + 밸런스 재-calibration) — **연기 (deferred)**
- [x] **Option B — Consistency-only (새 메커닉 없이 selection 일관성만)** — **채택·구현됨**
- [ ] Option C — 현상 유지 (no-op) — 채택되지 않음
- [ ] Option D — 메타데이터 선행 authoring (효과 구현은 별도) — **연기 (deferred)**
- [ ] B → D → A 순차 (AI 추천안) — B 만 채택, D/A 는 연기
- [ ] 기타: —
- [ ] Defer (다음 단계로 미룸) — 전체 결정은 아니나 D/A 는 연기

### 결정된 내용

1. **combat path 는 damage-only 로 유지한다.** enemy 측 `shield` / `heal` / `regen` /
   `buff` 효과 구현 (Option A) 은 하지 않는다. `StatusEffectKind` union, enemy status
   application 경로, `Ice` skill shape 모두 **변경하지 않았다.**
2. **selection 은 발사 가능한 스킬만 반환한다.** `selectSkillByPersonality`
   (`web/src/core/ice_ai.ts`) 가 후보 pool 을 **한 번만** 계산한다 — 발사 가능한 스킬
   (`damage > 0`) 이 하나라도 있으면 그 스킬들만 후보가 되고, preference loop 과
   fallback **둘 다** 그 pool 위에서 돈다. 발사 가능한 스킬이 하나도 없으면 후보 pool 은
   전체 목록이 되어 **동작이 이전과 동일하다** (기존 경로로 끝나고 combat path 가 plain
   auto-attack 으로 fall through).
3. **ADR-0218 의 "first usable" fallback 은 별도 코드가 필요 없다.** 위 pool 규칙에서
   자연스럽게 나온다 — fallback 은 `pool[0]` 이고, pool 이 사용 가능 스킬로 구성되어
   있으므로 `pool[0]` 은 곧 첫 usable 스킬이다.
4. **`PERSONALITY_SKILL_PREFERENCE` 는 의도적으로 변경하지 않았다 (trim 하지 않는다).**
   이것은 열린 질문 4번에 대한 명시적 답이다. `shield` / `heal` / `regen` / `buff` /
   `detect` entry 는 **전방 지향적 설계 의도 (forward-looking design intent)** 다 —
   Option A 가 채택되면 즉시 의미를 갖는다. 표를 trim 하면 그 의도를 버리고
   `defensive` / `support` 를 "공격만 하는 더 약한 aggressive" 로 접어버린다.
   **selection 시점에서 걸러내는 것**은 표의 의도를 보존하므로, trim 대신
   **selection-time filter** 로 해결한다. 이 근거는 표의 docstring 에 기록되어 있다.
5. **ADR-0218 의 "Remaining Gap" 이 본 ADR 로 해소되었다.** preference 매칭이 발사
   불가 스킬을 먼저 반환하는 경우가 더 이상 없다.

## 결과 (Consequences)

### 긍정적 영향

- **코드와 combat path 사이에 거짓말이 없어졌다.** preference loop 는 이제 combat path 가
  실제로 발사할 수 있는 스킬만 반환한다. "archetype preference 가 dead config" 이라는
  사실이 코드 주석에 그대로 남아 있는 대신, selection 단계에서 정직한 contract 로
  바뀌었다.
- **ADR-0218 의 Remaining Gap 이 해소되었다.** preference 매칭이 0-damage 스킬을 먼저
  지목해 auto-attack 으로 끝나던 경우가 사라진다. `defensive` ICE 가 `shield`(0) +
  `attack`(10) 을 가지고 있다면 이제 `attack` 을 발사한다.
- **ADR-0218 의 fallback 규칙이 코드에서 별도 분기 없이 자연스럽게 나온다** (pool[0]).
  규칙이 두 곳에 흩어지지 않는다.
- **밸런스는 손상되지 않았다.** `npm run balance` 의 BEFORE/AFTER 출력이 **6개 grade
  전부 모든 column 에서 동일**하다 (승률·stall·mean-turns·mean-HP-end 전부).
  grade band 하나도 이동하지 않았다.
- **새 state, 새 dependency, 새 mechantic 이 없다.** diff 는 selection 로직 한 곳 +
  회귀 테스트다. 되돌리기가 쉽다.

### 부정적 영향 / 수용한 비용

- **`defensive` / `support` preference list 는 여전히 cosmetic 이다.** 구현 불가 effect
  (shield / heal / regen / buff / detect) 는 combat path 가 발사할 수 없으므로
  `defensive` ICE 는 최종적으로 `attack` 을 쓴다. 표의 상대 순서는 여전히
  "의도 표기" 다. **다만 의도 자체는 표에 남아 있고**, Option A 가 채택되면 그대로
  살아난다 — trim 과 달리 의도를 잃지 않는다.
- **밸런스를 움직이지 않았다 = 플레이에서도 거의 보이지 않는다.** encounter band 안에서
  스킬을 가진 ICE 는 `loa_entity` (g5) 와 `aleph` (g6) 뿐이고 둘 다 `aggressive` 다.
  aggressive 의 damaging 스킬은 0-damage `buff` entry 보다 preference 순서상 앞서므로
  pool filter 는 이 둘에 대해 no-op 이다. 즉 **이번 수정이 실제 전투 결과에 미친 영향은
  사실상 없다.** 계약 정합만 개선되었다.

### 남은 gap

#### (1) `parseIce` 가 `personality` 을 누락한다 — **새로 발견된, 가장 중요한 후속 항목**

`parseIce` (`web/src/core/data_loaders.ts:236`) 는 `Ice` 객체에 **`personality` 필드를
복사하지 않는다.** `Ice` 타입 자체는 `personality` 을 가지고 있다
(`web/src/core/types.ts:80`) — loader 가 그냥 놓치는 것이다.

결과적으로 **runtime 에서 모든 catalog ICE 의 personality 는
`coercePersonality(undefined) === "aggressive"` 로 해석된다.** `ice_types.json` 의
personality 분포 (aggressive 80 / defensive 12 / stealth 5 / support 0) 는 **inert** 하다.
데이터에는 있으되 런타임에 닿지 않는다.

이것이 중요한 이유:

- **Option B 는 지금은 "defensive/correct 하지만 플레이에서 거의 inert" 하다.** 이 수정이
  실제로 물건은 것은 ICE 의 personality 가 `aggressive` 가 아닐 때뿐인데, **catalog ICE
  에는 그런 경우가 하나도 없다.** 방어적으로는 맞지만, 관측 가능한 차이가 아직 없다.
- **archetype 시스템의 진짜 blocker 는 non-damaging 효과의 부재가 아니라 이 loader
  gap 이다.** personality 가 전달되면 `defensive` / `stealth` preference 가 실제로
  발사되어 archetype 차이가 나타나기 시작한다. 반대로 personality 가 끊겨 있는 한
  Option A 를 구현해도 archetype 는 여전히 관측 불가하다.
- **이는 ADR-0216 과 동일한 결함 계열이다.** ADR-0216 은 `parseIce` 가 `skills` 를
  조용히 버리는 문제를 다뤘고, 이번에는 같은 loader 가 `personality` 을 조용히
  버린다. "loader 가 필드를 조용히 drop 한다" 는 패턴이 두 번째 반복되었다.

**이번 구현에서는 고치지 않았다** (Option B 의 범위 밖 — selection 일관성이 목표였고
loader 는 데이터 경로다). 후속 항목으로 기록한다.

> ⚠️ **이 gap 을 고치면 밸런스가 움직인다.** personality 가 전달되면 12 종 `defensive` +
> 5 종 `stealth` ICE 가 더 이상 `aggressive` 처럼 동작하지 않는다. 따라서 이 수정은
> **별도의 결정**을 필요로 한다 — 재측정 없이 ship 할 수 없다.
> 범위 후보는 두 가지다: (a) Option D 의 "데이터 정합성" 범위에 포함 (loader 가
> authoring 데이터까지 겸하는 경우), (b) 이 ADR 와 형제 ADR 로 분리된 별도 loader
> 정합 항목.

#### (2) non-damaging 효과 자체는 미구현 (Option A — 연기)

enemy combat path 에 `shield` / `heal` / `regen` / `buff` / `detect` 가 없다.
`StatusEffectKind` union (`web/src/core/types.ts`) 에 `shield` 가 없고, enemy combat path
는 `StatusEffectKind` 을 참조하지 않는다. magnitude source 도 없다 (88 스킬 metadata
미작업). **Option A 는 연기 상태다.**

#### (3) 88개 스킬 메타데이터는 미작업 (Option D — 연기)

`ice_types.json` 의 `skills` 는 여전히 bare ID 배열이다. ADR-0216 의 loader-side
derivation 이 유효하다. **Option D 는 연기 상태다.**

#### (4) encounter band 커버리지 확대는 미착수

`ENCOUNTER_ICE_BY_GRADE` (`web/src/core/ice_scaling.ts:30-37`) 의 24 항목 (18 unique id)
중 스킬 보유는 `loa_entity` (g5) 와 `aleph` (g6) 뿐이고 둘 다 `aggressive` 다.
band 안의 `defensive` / `stealth` ICE (`watchdog`, `wisp`,
`ice_neuromancer_warden`) 는 **`skills: []`** 이므로 preference 매칭 자체가 일어나지
않는다. band 확대는 별도의 밸런스 결정이다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/ice_ai.ts:201-202` — 후보 pool 을 한 번만 계산:
  `const usable = availableSkills.filter((s) => s.damage > 0);`
  `const pool = usable.length > 0 ? usable : availableSkills;`
- `web/src/core/ice_ai.ts:205-211` — preference loop 이 `pool` 위에서 돈다 (발사 불가 스킬 매칭 불가)
- `web/src/core/ice_ai.ts:217` — fallback 이 `pool[0]` 이다. pool 이 사용 가능 스킬로 구성되어
  있으므로 곧 첫 usable 스킬 (ADR-0218 규칙이 자연스럽게 유도됨)
- `web/src/core/ice_ai.ts:142-156` — `PERSONALITY_SKILL_PREFERENCE` docstring 에 **trim 하지 않는
  근거** (전방 지향적 설계 의도 / selection-time filter 로 의도 보존) 기록
- `web/tests/ice_ai.test.ts:239-244` — 회귀 테스트 "skips an unfireable preferred skill and
  uses the usable one" (`defensive` ICE, `[shield(0), attack(10)]` → `attack` 선택)
- `web/tests/ice_ai.test.ts:246-252` — "orders preference among usable skills only"
- `web/tests/ice_ai.test.ts:254-258` — "returns a skill when every skill is non-damaging"
- `web/tests/ice_ai.test.ts:260-263` — "returns null for an empty skill list (regression)"
- `web/tests/personality_skill.test.ts:47-65` — `"defensive personality uses its attack skill,
  not the unfireable shield"` — 이름 변경 + assertion 반전 (양방향 assert)
- Pre-fix 검증 (`ice_ai.ts` 를 임시로 되돌림): discriminating test 가
  `expected {... "damage": 10, "effect": "attack", "id": "a", "name": "Attack" } to be
  {... "damage": 0, "effect": "shield", ...}` 로 실패했고, integration test 가
  `expected '>>> Defender attacks: 9 dmg' to contain 'Attack'` 로 실패했다 — 보고된 증상을
  그대로 재현
- 수정 후 gate: `npm test` **125 files / 2943 tests, 0 failures**;
  `tsc --noEmit` 0 errors; `eslint` 0 errors
- 밸런스 (`npm run balance`, 100 runs/mission) BEFORE vs AFTER: **6개 grade 전부 모든 column
  이 동일** — g1 100.0% / g2 88.8% / g3 73.0% / g4 47.4% / g5 42.4% / g6 0.0%,
  mean-turns 와 mean-HP-end 도 불변. **grade band 하나도 이동하지 않았다.**
- 밸런스가 안 움직인 이유 (추측이 아니라 **실측 확인**): encounter band 안에서 스킬을 가진
  ICE 는 `loa_entity` (g5) 과 `aleph` (g6) 뿐이고 둘 다 `aggressive` 다. 둘 다
  damaging 스킬이 0-damage `buff` entry 보다 preference 순서상 앞서므로 pool filter 가
  no-op 이다. band 안의 `defensive` / `stealth` ICE 3종 (`watchdog`, `wisp`,
  `ice_neuromancer_warden`) 은 `skills: []` 이므로 preference 매칭 자체가 일어나지 않는다.

**Notes**:

- **새 테스트 4건 중 discriminating 은 1건뿐이다.** `web/tests/ice_ai.test.ts:239-244` 만
  pre-fix 코드에서 실패한다. 나머지 3건 (`:246-252`, `:254-258`, `:260-263`) 은
  **guard test** 다 — 발사 불가 스킬만 있는 목록, 빈 목록 → `null`, usable 스킬 사이의
  preference 순서처럼 **변경되지 않은 동작을 pin 하는** 테스트다. 이들을 회귀 테스트
  suite 의 크기로 세면 안 된다.
- **기존 passing test 하나가 결함을 pin 하고 있었다.**
  `web/tests/personality_skill.test.ts` 의 `"defensive personality prefers shield/heal
  skills"` 는 `toContain("attacks:")` 를 assert 했다 — 즉 **`defensive` ICE 가
  `[shield(0), attack(10)]` 을 가지고 있을 때 0-damage `shield` 를 선택하고, 그 결과
  combat path 의 `damage > 0` 게이트에 막혀 auto-attack 으로 degrade 되는** 것을
  의도된 동작으로 고정하고 있었다. 이번에 이름을
  `"defensive personality uses its attack skill, not the unfireable shield"` 로 바꾸고
  assertion 을 반전했다 — 이제 **공격 스킬이 실제로 발사되는지**와 **auto-attack fallback 이
  일어나지 않는지**를 둘 다 assert 한다. 이전 assertion 보다 **엄격하다** (positive +
  negative 양쪽을 검사).
- `PERSONALITY_SKILL_PREFERENCE` 는 **변경하지 않았다.** `shield` / `heal` / `regen` /
  `buff` / `detect` entry 가 그대로 남아 있다 (열린 질문 4번의 답 — 근거는 위 docstring).
- `chooseSkill` (uniform random, Python prototype 포트) 은 변경하지 않았다.
- combat path (`web/src/core/state_actions_combat.ts`), `web/src/core/ice_skills.ts`,
  `web/src/core/types.ts`, `web/src/core/ice_scaling.ts`, `web/src/data/ice_types.json`
  는 **모두 미변경**이다.
- 후속 항목: `parseIce` 의 `personality` 누락 (ADR-0216 과 동일 결함 계열) — 위
  「결과 (Consequences) → 남은 gap (1)」 참조. 이건 **미수정**이며, 고치면 밸런스가
  움직이므로 별도 결정이 필요하다.

## 영향 받는 항목

### 이번 결정 (Option B) 으로 실제 변경된 항목

- `web/src/core/ice_ai.ts` — `selectSkillByPersonality` 의 후보 pool 계산 +
  `PERSONALITY_SKILL_PREFERENCE` docstring (trim 하지 않는 근거 기록)
- `web/tests/ice_ai.test.ts` — 회귀 테스트 4건 추가 (1건 discriminating + 3건 guard)
- `web/tests/personality_skill.test.ts` — 기존 테스트 이름 변경 + assertion 반전

### 이번 결정으로 변경되지 않은 항목 (Option 별 — 미착수)

- `web/src/core/state_actions_combat.ts` — enemy combat path (Option A — 연기)
- `web/src/core/ice_skills.ts` — derivation 규칙 → authored data 전환 (Option D — 연기)
- `web/src/core/types.ts` — `StatusEffectKind` (`shield` 추가) + ICE skill shape (Option A — 연기)
- `web/src/core/ice_scaling.ts` — `ENCOUNTER_HP_BY_GRADE` / `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` (Option A — 연기)
- `web/src/data/ice_types.json` — 88 스킬 metadata (Option A/D — 연기)
- `docs/testcases/combat/depth.md` — prototype-era 문서 (Option A 시 갱신)

### 후속 항목 (이번 ADR 범위 밖)

- `web/src/core/data_loaders.ts` — `parseIce` 의 `personality` 누락 (ADR-0216 과 동일 결함
  계열). 밸런스에 영향이 있으므로 별도 결정 필요. Option D 의 "데이터 정합성" 범위에
  포함하거나 별도 ADR 로 분리할 수 있다.

## 관련 결정

- ADR-0148 (aggression tiers) — `enemyShouldUseSkill` 게이트와 짝
- ADR-0161 (personality archetypes) — `PERSONALITY_SKILL_PREFERENCE` 의 의래
- ADR-0211 (ICE grade scaling) — 밸런스 상수의 owner
- ADR-0212 (grade 기반 ICE encounter 배선) — `ENCOUNTER_ICE_BY_GRADE` 의 owner
- ADR-0216 (derived ICE skill metadata) — derivation 규칙의 owner, Option D 가 대체 대상.
  `parseIce` 가 필드를 조용히 drop 하는 결함 계열이 여기서 두 번째 반복되었다
  (`skills` → `personality`)
- ADR-0217 — sibling ADR
- ADR-0218 (ICE skill selection fallback) — 본 ADR 이 답하는 "Remaining Gap" 의 출처.
  본 ADR 이 그 gap 을 **닫았다.**

## 변경 이력

- 2026-10-27: Draft 작성 (결정 요청 — B → D → A 순차 추천)
- 2026-10-27: **Accepted (Option B — Consistency-only)** — 사용자가 선택, 구현 완료·검증.
  Consequences / Implementation Status 채움. `parseIce` 의 `personality` 누락을
  후속 항목으로 신규 발견·기록.
