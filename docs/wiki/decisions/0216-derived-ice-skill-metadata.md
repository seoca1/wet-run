# ADR-0216: Derived ICE skill metadata (ICE 스킬 메타데이터 derived 생성)

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — dead combat path)
**관련**: [ADR-0211 — ICE 난이도 스케일링](./0211-ice-grade-scaling.md), [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md)

## 컨텍스트 (Context)

Property-based fuzzing 결과 `skillCooldowns` 가 fuzzing된 **모든 run** 에서 `{}` 로 남았고,
`enemyShouldUseSkill` 는 **한 번도 발화하지 않았다**. 즉 ICE combat 스킬 경로 전체가 dead code 였다.

### 근본 원인 — `parseIce` 의 `skills` drop

`parseIce` (`web/src/core/data_loaders.ts`) 는 `id/name/armor/tier/hp` (+`hpBase`/`hpPerGrade`)
만 복사하고 **`skills` 를 조용히 버렸다**. 결과적으로 ICE 97종 중 **44종**이 자신의 스킬을 잃었다.

### 근본 원인 2 — 데이터에 스킬 메타데이터가 없음

`web/src/data/ice_types.json` 은 스킬을 **bare ID string** 으로 선언한다:

```json
"loa_priest": { "dmg_base": 5, "skills": ["loa_summon", "spirit_guard"] }
```

그런데 **repo 어디에도 per-skill 메타데이터가 없다**: 88 개의 서로 다른 skill ID 가 있지만
JSON 에 `cooldownMs`/`damage`/`effect` 필드가 없고, skill catalog 도 존재하지 않는다.

Retire 된 Python prototype 은 ICE skill ID 를 **program registry** 기준으로 resolve 했는데,
88개 중 **2개**만 매칭되었다. 즉 누락된 필드는 **derivation** 으로 만들어낼 수밖에 없었다.

## 고려한 옵션

### Option 1: hand-authored skill catalog 를 `ice_types.json` 에 추가

- **설명**: 88개 skill ID 전부에 대한 정식 정의 table 을 JSON 에 추가.
- **장점**: 진짜 source of truth. 값이 데이터로 존재하므로 derivation heuristic 이 아님.
- **단점**: hand-maintained 데이터 88 entry 를 손으로 작성/검토해야 한다. 단기 shipping 불가.
- **Pillar 정합**: P4 (The Build) — 장점, 단 데이터 유지보수 부담.

### Option 2: Python prototype 의 program registry 재사용

- **설명**: prototype 의 registry 로 ICE skill id 를 resolve.
- **단점**: **88개 중 2개** 만 매칭된다. 해결이 아니라 오해를 재사용하는 것.
- **Pillar 정합**: 실패.

### Option 3: **Loader-side derivation** (선택)

- **설명**: loader 가 skill ID로부터 typed skill object 를 **derive** 한다. ID 는 verbatim 으로
  보존하고 나머지 필드는 규칙으로 산출.
- **장점**:
  - 즉시 shipping 가능, hand-maintained 데이터 불필요
  - ID 를 source of truth 로 보존 (id 는 JSON 그대로)
  - derivation 규칙이 한 모듈에 격리되어 검증/조정 가능
- **단점**:
  - `effect`/`damage`/`cooldownMs` 는 **authored data 가 아니라 heuristic**
  - 88개 skill ID 에 대한 canonical 정의 table 이 여전히 없음
- **Pillar 정합**:
  - P3 (The Flatline): combat depth 회복 — dead path 가 live 가 됨
  - P4 (The Build): 신규 모듈 1개, module-size 가이드 준수

## 추천 (Recommendation)

**Option 3 (Loader-side derivation)** — Option 1 이 장기적으로는 더 강하지만, 지금 ship 해야 하는
것은 dead combat path 이다. derivation 은 ID 를 verbatim 보존하므로 나중에 hand-authored catalog 로
교체해도 데이터 계약이 깨지지 않는다.

## 사용자 결정 (Decision)

[ x ] Option 3 (Derived ICE skill metadata) — 사용자가 명시적으로 승인, 코드는 이미 shipped 상태.

## 결과 (Consequences)

### 결정된 derivation 규칙

Loader 는 typed skill object 를 **읽는 것이 아니라 만든다**:

| 필드 | 파생 방식 |
|---|---|
| `id` | JSON 에서 verbatim (source of truth 보존) |
| `name` | snake_case id 를 humanize (`loa_summon` → `Loa Summon`) |
| `effect` | **snake_case token** 기준 (ordered, first-match-wins rule table, `attack` fallback) |
| `damage` | 해당 row 의 `dmg_base`. **non-damaging effect 는 0** |
| `cooldownMs` | `4000` (auto-attack interval 2000ms 의 2배) |

`effect` 는 **token 매칭이며 substring 매칭이 아니다**. substring 매칭은 `enforce_contract` 를
multi-hit 로 잘못 분류했다 ("enforce" 안에 "force" 가 들어있다).

`damage` 를 non-damaging effect 에서 0 으로 두는 이유: `state_actions_combat.ts` 는
**`damage > 0` 일 때만** 스킬을 발화한다. 그래야 defensive/utility 스킬이 아무것도 하지 못한 채
쿨다운만 태우지 않는다.

Derivation 은 전용 모듈 **`web/src/core/ice_skills.ts`** (147 LOC) 에 있다. 덕분에
`data_loaders.ts` 는 다시 **320 LOC** 로 내려왔다 (461 LOC 까지 늘어나서 100-300 권장치를 초과했음).

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/ice_skills.ts:118` — `parseIceSkills` — bare ID 배열 → typed `{id, name, effect, cooldownMs, damage}` 변환
- `web/src/core/ice_skills.ts:83` — `iceSkillEffectFor` — snake_case token 기반 ordered first-match-wins rule table (`attack` fallback)
- `web/src/core/ice_skills.ts:96` — `iceSkillNameFor` — `loa_summon` → `Loa Summon` humanize
- `web/src/core/ice_skills.ts:80` — `ICE_SKILL_COOLDOWN_MS = 4000` (auto-attack 2000ms 의 2배)
- `web/src/core/ice_skills.ts:66` — `ICE_SKILL_NON_DAMAGE_EFFECTS` — non-damaging effect 는 damage 0
- `web/src/core/data_loaders.ts:267` — `parseIce` 가 `parseIceSkills(r.skills, ...)` 호출 (기존 `skills` drop 해소)
- `web/src/core/data_loaders.ts:276` — 복원된 `skills` 가 `Ice` 에 spread (필드 없으면 key 자체 생략)
- `web/src/core/state_actions_combat.ts:230` — `selectedSkill.damage > 0` 일 때만 스킬 발화 — derivation 규칙과 정합
- `web/src/core/state_actions_combat.ts:240` — `skillCooldowns` 갱신 (`${enemy.id}_${selectedSkill.id}` 키)
- ICE 97종 중 **44종**이 스킬을 노출 (이전 0종). `skillCooldowns` 가 이제 populate 됨 (예: `corporate_guard → {"corporate_guard_report":4000}`)
- NaN/HP/invariant regression 없음. `npm run balance` 출력이 before/after **byte-identical** — encounter-band ICE 24종 중 2종만 스킬을 carry 하므로 opening-deck harness 는 거의 인지하지 못함

**Notes**: encounter band ICE id 24종 중 **2종**만 스킬을 carry 한다 (`ice_scaling.ts` 의
`ENCOUNTER_ICE_BY_GRADE`). 따라서 이 기능은 실제 플레이에서 거의 보이지 않는다 —
그것은 밸런스 변경이며 재-calibration 이 필요하다.

## 영향 받는 항목

- `web/src/core/ice_skills.ts` — 신규 모듈 (ICE skill derivation 규칙)
- `web/src/core/data_loaders.ts` — `parseIce` 가 `skills` 를 복원 (461 → 320 LOC)
- `web/src/core/state_actions_combat.ts` — 소비측 (변경 없음, `damage > 0` 규칙이 derivation 과 정합)
- `web/src/data/ice_types.json` — 변경 없음 (source of truth 로 ID 만 사용)

## 관련 결정

- ADR-0110 (모듈 사이즈 정책) — 신규 모듈은 이 가이드를 따른다 (ADR-0110 §결과, web TypeScript 평균 100-300 LOC)
- ADR-0211 (ICE 난이도 스케일링) — `dmg_base` / `hp_base` / `hp_per_grade` 파생 계열
- ADR-0212 (grade 기반 ICE encounter 배선) — encounter band ICE 구성

## 변경 이력

- 2026-10-27: Draft 작성 + Accepted (Option 3, Derived ICE skill metadata) — 코드 shipped 상태
