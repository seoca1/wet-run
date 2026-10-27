# ADR-0218: ICE 스킬 선택의 fallback 은 사용 가능한 스킬을 고른다 (usable skill)

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline, dead combat path — ADR-0216 sibling)
**관련**: [ADR-0148 — aggression tiers](./0148-combat-depth-expansion.md), [ADR-0161 — personality archetypes](./0161-ice-personality-archetypes.md), [ADR-0216 — derived ICE skill metadata](./0216-derived-ice-skill-metadata.md), [ADR-0217](./0217-continue-restores-playable-run.md)

## 컨텍스트 (Context)

`selectSkillByPersonality` (`web/src/core/ice_ai.ts`) 는 personality preference list
(`PERSONALITY_SKILL_PREFERENCE`) 를 순회하며 ICE 가 쓸 스킬을 고른다. 아무것도 매칭되지
않으면 fallback 이 **`availableSkills[0]`** (첫 번째 스킬) 이었다.

그런데 production combat path (`web/src/core/state_actions_combat.ts:221`) 는 이 함수를
**hot path 에서** 호출하고, 스킬을 **실제로 발사하는 조건** 은 `selectedSkill.damage > 0`
이다 (`:230`). 조건을 만족하지 못하면 `usedSkill` 가 false 로 남고, `:246` 의 plain
auto-attack 으로 fall through 한다.

즉 **첫 번째 스킬이 non-damaging 인 ICE 는, damaging 스킬을 가지고 있었더라도 그것을
한 번도 쓰지 못했다.** 조용히 무한 auto-attack 만 반복한다.

### 실측 사례 — `loa_entity` (grade-5 encounter band)

`loa_entity` 의 `skills` 는 `["manifest_form", "voodoo_curse"]` 이다
(`web/src/data/ice_types.json`). `damage` 는 `parseIceSkills`
(`web/src/core/ice_skills.ts`) 가 **ICE row 의 `dmg_base`** 를 own attack stat 으로
사용해 파생한다 (`loa_entity` 의 `dmg_base` = 5). 단 non-damage effect
(`ICE_SKILL_NON_DAMAGE_EFFECTS`) 는 `damage: 0` 이 된다.

| skill id | 파생된 effect | damage |
| --- | --- | --- |
| `manifest_form` | `buff` (non-damage) | 0 |
| `voodoo_curse` | `poison` | 5 |

`loa_entity` 의 personality 는 `aggressive` 이고, `aggressive` 의 preference list 는
`heavy_attack / pierce / multi_hit / attack / lifesteal` 이다. `buff` 도 `poison` 도
그 안에 없다. 따라서 **둘 다 매칭되지 않아** fallback 이 0-damage 인 `manifest_form` 을
반환했고, combat path 는 그 스킬을 발사하지 못한 채 auto-attack 만 했다.

### 함께 고친 것 — 거짓이던 docstring 2건

`web/src/core/ice_ai.ts` 의 file header 는 `selectSkillByPersonality` 을
"a forward-facing hook" 이라고 서술하고, "the production hot path uses `chooseSkill`
(uniform random)" 이라고 적었다. **둘 다 거짓**이었다.
`state_actions_combat.ts:221` 가 hot path 에서 `selectSkillByPersonality` 을 호출한다.
`chooseSkill` 은 Python prototype `Combatant.choose_skill()` 의 포트로 남아 있을 뿐이다.

## 고려한 옵션

### Option 1: fallback 이 첫 **usable** 스킬 (damage > 0) 을 고른다 (선택)

- **설명**: preference loop 은 그대로 두고, fallback 만
  `availableSkills.find((s) => s.damage > 0) ?? availableSkills[0] ?? null` 로 바꾼다.
  사용 가능한 스킬이 하나도 없으면 첫 번째 스킬로, 목록이 비면 `null`.
- **장점**:
  - combat path 의 실제 발사 조건 (`damage > 0`) 과 fallback 이 **일치**한다.
  - preference loop 과 `PERSONALITY_SKILL_PREFERENCE` 를 건드리지 않으므로
    기존 personality semantics 는 그대로 유지된다.
  - docstring 만 고쳐도 계약이 코드와 일치하므로, 별도 리팩터링이 필요 없다.
- **단점**:
  - preference **매칭** 결과가 non-damaging 인 경우는 여전히 auto-attack 으로 끝난다
    (아래 Remaining Gap 참조).
- **Pillar 정합**:
  - P3 (The Flatline): ✅ 스킬이 존재하는데 발사되지 않던 dead path 를 되살린다.

### Option 2: preference loop 도 `damage > 0` 인 스킬만 고르게 한다

- **설명**: 매칭 단계에서 `damage > 0` 조건을 함께 요구한다.
- **장점**: 모든 경로에서 "발사 가능한 스킬" 만 골라진다.
- **단점**:
  - `defensive` / `support` archetype 의 preference list (shield / heal / regen /
    buff / detect) 가 **구조적으로 관측 불가능** 해진다. 그 list 의 우선순위가
    코드로 표현되지 않는다.
  - personality semantics 를 바꾸는 결정이므로 본 ADR 의 범위를 넘어선다.
- **Pillar 정합**: P3: 부분적, 그러나 archetype semantics 변경이라 별도 결정 필요.

### Option 3: combat path 가 non-damaging 스킬도 발사하도록 바꾼다

- **설명**: `state_actions_combat.ts` 가 `damage > 0` 검사 대신 skill effect 를
  처리한다 (shield / heal / regen / buff / detect 실제 효과 구현).
- **장점**: 근본 원인 자체를 제거한다.
- **단점**:
  - combat path 의 스킬 효과 시스템 전체를 새로 구현해야 한다.
  - 밸런스 영향이 band 수준이 아니라 전투 전반에 퍼진다.
- **Pillar 정합**: P3: 근본 해결이나 본 ADR 범위 밖.

### Option 4: 현상 유지 (no-op)

- **설명**: fallback 을 `availableSkills[0]` 로 둔다.
- **장점**: 코드 변경 없음.
- **단점**: 0-damage 스킬이 앞에 있는 ICE 는 damaging 스킬을 영원히 못 쓴다.
- **Pillar 정합**: 실패.

## 추천 (Recommendation)

**Option 1** — fallback 계약만 combat path 의 발사 조건과 맞춘다.
preference loop 은 건드리지 않으므로 기존 테스트 (`defensive` personality 가
shield/heal 을 선호) 는 그대로 통과한다.

## 사용자 결정 (Decision)

[ x ] Option 1 (fallback 이 첫 usable skill 을 고른다) — 코드는 이미 shipped 상태.

## 결정된 내용

1. **fallback 은 첫 usable 스킬을 고른다.**
   `availableSkills.find((skill) => skill.damage > 0) ?? availableSkills[0] ?? null`.
   사용 가능한 스킬이 없으면 첫 번째 스킬, 목록이 비면 `null`.
2. **preference loop 과 `PERSONALITY_SKILL_PREFERENCE` 는 바뀌지 않는다.**
   preference 매칭이 여전히 우선한다. 매칭된 스킬이 non-damaging 이면
   (그 결과가 auto-attack 이더라도) 그대로 사용된다.
3. **거짓이던 docstring 2건을 정정한다.**
   file header 와 `selectSkillByPersonality` docstring 이 실제 hot path 와
   새로운 fallback 계약을 기술한다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/ice_ai.ts` — fallback 이 `availableSkills.find((s) => s.damage > 0) ?? availableSkills[0] ?? null` 로 변경, file header 와 함수 docstring 정정
- `web/tests/ice_ai.test.ts` — unit test 3건 (선행 0-damage 스킬을 넘겨 첫 usable 선택 / usable 없으면 첫 available 선택 / 빈 목록이면 `null`)
- `web/tests/personality_skill.test.ts` — integration test: `aggressive` ICE 의 스킬이 `[{buff, damage:0}, {poison, damage:5}]` 일 때 poison 스킬 이름이 포함된 message 를 낸다
- Pre-fix 검증 (fallback 을 임시로 되돌림): unit test 가 5-damage `poison` 대신 0-damage `buff` 를 받았고,
  integration test 가 `expected '>>> Loa attacks: 9 dmg' to contain 'Voodoo Curse'` 로 실패 —
  보고된 증상을 그대로 재현
- 수정 후 gate: `npm test` **125 files / 2939 tests, 0 failures**;
  `tsc --noEmit` 0 errors; `eslint` 0 errors (기존 warning 1건은 `web/src/input/keyboard.ts` 의 `no-explicit-any`, 본 변경과 무관)
- 밸런스 (`npm run balance`): 6개 grade 전부 **byte-identical** —
  유일한 차이는 grade-5 `mean-HP-end` 5.5 → 5.6 (소수 평균의 반올림 수준).
  win-rate / stall / turn band 는 하나도 이동하지 않음.
  영향 범위는 좁다: encounter band 의 24개 id 항목 중 스킬을 가진 것은 2개뿐이고,
  그중 fallback 에 도달하는 것은 `loa_entity` (g5) 뿐이다.
  `aleph` (g6) 는 이미 preference 에 매칭되어 (`ice_pierce`, damage 15) 영향을 받지 않는다.
- `web/tests/personality_skill.test.ts` 의 "defensive personality prefers shield/heal skills" 는
  **수정 없이 그대로 통과**한다 (변경하지 않은 preference loop 에서 `shield` 매칭).

**Notes**: `chooseSkill` (uniform random) 은 Python prototype 포트로 그대로 남아 있다.
`stealth_only` mutator filter 는 `ice_skills.ts` 의 effect 판정에 의존하므로
이번 변경의 영향을 받지 않는다.

## 결과 (Consequences)

### 긍정적 영향

- 첫 스킬이 non-damaging 인 ICE 가 이제 자신의 damaging 스킬을 쓴다.
- 함수의 docstring 이 더 이상 코드와 모순되지 않는다.
- preference 매칭 semantics 는 그대로이므로 personality diversity 가 보존된다.

### 부정적 영향 / 수용한 비용

- 실질적 비용 없음. 밸런스는 band 수준에서 변하지 않는다.

### 남은 gap (중요 — 반드시 기록)

이번 수정은 **fallback 만** 고친다. personality preference 에 **매칭되지만**
`damage: 0` 인 스킬은 여전히 auto-attack 으로 끝난다. combat path 가 `damage > 0` 를
요구하는데 preference loop 가 그런 스킬을 먼저 반환하기 때문이다.

구체적 사례:
- `defensive` ICE 의 목록에 `shield` 가 있으면 (`defensive` preference list 의 첫 항목) —
  매칭되어 0-damage 이므로 auto-attack.
- `support` ICE 의 목록이 `heal` 로 시작하면 — 동일하게 auto-attack.

근본 원인: **non-damaging 스킬 효과 (shield / heal / regen / buff / detect) 가 combat path
에 아예 구현되어 있지 않다.** 그래서 `defensive` 와 `support` archetype 의 preference list 는
구조적으로 관측 불가능하다 — list 의 상대 순서가 무엇이든 결과가 동일하다.

해소하려면 `state_actions_combat.ts` 에 그 효과들을 구현하거나 archetype semantics 를
바꾸어야 한다. 둘 다 본 ADR 의 범위 밖이며, 자연스러운 후속 작업이다.

## 영향 받는 항목

- `web/src/core/ice_ai.ts` — fallback 계약 + docstring 정정
- `web/tests/ice_ai.test.ts` — unit test 3건
- `web/tests/personality_skill.test.ts` — integration test 1건

## 관련 결정

- ADR-0148 (aggression tiers) — `enemyShouldUseSkill` 게이트와 짝을 이루는 결정
- ADR-0161 (personality archetypes) — `PERSONALITY_SKILL_PREFERENCE` 정의
- ADR-0216 (derived ICE skill metadata) — `damage` 가 어디서 파생되는지 정의한 sibling ADR
- ADR-0217 — sibling ADR, 동일 날짜

## 변경 이력

- 2026-10-27: Draft 작성 + Accepted (Option 1, fallback 이 첫 usable skill 을 고른다) — 코드 shipped 상태
