# ADR-0223: 스킬 분류 review pass — heuristic 의 실수를 고친다 (ADR-0222 후속 항목 1)

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — dead combat path, ADR-0216/0219/0222 sibling)
**관련**: [ADR-0216 — derived ICE skill metadata](./0216-derived-ice-skill-metadata.md), [ADR-0218 — ICE skill selection fallback](./0218-ice-skill-selection-fallback.md), [ADR-0219 — non-damaging ICE 스킬 효과](./0219-non-damaging-ice-skill-effects.md), [ADR-0222 — ICE 스킬 메타데이터가 heuristic 에서 authored data 로 이동한다](./0222-ice-skill-metadata-as-data.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-27 에 결정·구현·검증까지 완료되었다.
> 구현 범위는 **분류 정정 (reclassification) 하나**다 — `ice_types.json` 의
> `skill_defs` 88 entry 를 전수 검토해, 이름이 확실히 다른 효과를 가리키는
> **20개 entry 의 `effect` 값만** 고쳤다.
>
> **아직 착수되지 않은 것** (본 ADR 의 범위 밖, 후속 항목):
> (1) 10개 ambiguous id 에 대한 디자인 판정,
> (2) non-damaging 효과 메커닉 구현 (ADR-0219 Option A),
> (3) encounter band 커버리지 확대.
> **효과 magnitude 는 하나도 authoring 하지 않았다.**
>
> **행동은 byte-identical 이다.** combat path, 밸런스 상수, effect mechanics 는
> **하나도 바뀌지 않았다.** `npm run balance` 출력이 BEFORE/AFTER 동일하고, 6개 grade
> 전부 모든 column 이 **0.0% delta** 다.

## 컨텍스트 (Context)

### ADR-0222 가 남긴 일

ADR-0222 (Option D) 는 ADR-0216 의 token heuristic 출력을 `skill_defs` 에
**verbatim** 으로 materialized 했다. 그 선택은 의도적이었고 **행동 보존**이었다.
`web/src/data/ice_types.json` 의 97 ICE row 와 다른 모든 top-level key 는
byte-identical 로 남고, `npm run balance` 출력도 동일했다.

하지만 그 결과 **heuristic 의 오분류가 데이터가 되었다.** ADR-0222 의
「후속 항목 (1) — 스킬 분류 review 는 PENDING」 이 정확히 그것을 가리킨다.
heuristic 이 코드 안에 숨어 있을 때는 실수를 **발견할 수 없었다.** 표로 옮기자
표가 드러났고, 이제 그 표를 읽고 고치는 것이 남았다.

### 왜 이 review 가 ADR-0219 Option A 의 선행 조건인가

ADR-0219 의 Option A (shield / heal / regen / buff 메커닉 + magnitude authoring) 는
**분류가 정확하다는 전제 위에서만** 의미가 있다. misclassified data 위에
non-damaging 메커닉을 얹으면 **실수가 메커닉으로 굳어진다.** 예컨대 `report`
를 `attack` 으로 둔 채로 `detect` 메커닉을 구현하면, `report` 는 여전히
`attack` 이라 0-damage 가 되지 않는다. 즉 Option A 는 **검토되지 않은 분류
위에서** magnitude 를 저술하게 되고, 그 magnitude 는 나중에 함께 뒤집어야 한다.

따라서 **분류 review 가 먼저**, 그 다음에 Option A 다. 이 순서는 ADR-0222 가
이미 후속 항목으로 기록한 순서와 같다.

### review 의 대상 범위

`skill_defs` 88 entry **전수**다. 우선순위 기반 부분 검토는 하지 않았다.
이유는 review 규칙이 단순해야 하기 때문이다 — "`id` 의 이름이 가리키는 메커닉을
`effect` 가 말해야 한다" 는 규칙 하나면 88개를 판정할 수 있다. 우선순위를
두면 "어떤 이름까지 믿을 것인가" 라는 두 번째 판단이 끼어든다.

## 고려한 옵션

### Option 1: strict review — 이름이 명확하면 고치고, 모호하면 둔다 (선택)

- **설명**: 88 entry 를 전수 검토한다. `id` 가 **확실히** 가리키는 메커닉과
  현재 `effect` 가 다르면 고친다. 두 개 이상의 읽기가 가능한 이름은 **고치지
  않고** competing readings 를 함께 기록한다. review 규칙은 다음 4개다:
  1. **기존 `SkillEffectKind` 값만 사용한다** (새 effect 를 만들지 않는다).
  2. **`name` / `cooldown_ms` 는 건드리지 않는다.**
  3. **`damage` 는 건드리지 않는다** (per-ICE 파생 값이므로 표에 없다).
  4. **모호한 이름은 고치지 않는다** — 대신 기록한다.
- **장점**:
  - Option A 가 신뢰할 수 있는 데이터 위에서 시작한다.
  - review 규칙이 4줄로 끝나므로 **재현 가능하고 감사 가능**하다.
  - 모호한 case 를 고치지 않는 것이 **design call** 의 영역으로 남는다.
- **단점**:
  - 10개 ambiguous id 는 이번 review 로 해결되지 않는다.
  - "확실히 가리키는" 의 경계에 대한 판단이 필요했다. 이 ADR 는 그 판단의
    근거까지 기록한다 (self-correction 포함).
- **Pillar 정합**:
  - P3 (The Flatline): ✅ dead combat path 의 첫 전제 조건이 정리된다.
  - P4 (The Build): ✅ 손으로 관리하는 88 entry 표의 신뢰도가 올라간다.
  - P5 (The Style): ✅ 스킬 이름과 효과가 어긋나지 않는다.

### Option 2: 최대 review — 이름이 공격적으로 읽히지 않으면 모두 비공격으로

- **설명**: `report`, `data_archive`, `backup_dispatch` 같은 이름이 "공격처럼
  들린다" 는 이유로 **넓게** 재분류한다.
- **단점**:
  - **`attack` 이었던 entry 를 `debuff` / `buff` 로 바꾸는 것은 combat path 의
    발사 가능 여부 (damage 0) 를 바꾼다** — 밸런스를 움직이는 변경이다.
  - 이름이 실제로 방어 행위를 가리키는지 확인하지 않은 채 table 을 뒤집는 셈이다.
  - review 결과가 **"분류" 가 아니라 "취향"** 이 된다.
- **Pillar 정합**: 실패 (evidence 없이 combat behaviour 를 바꾼다).

### Option 3: 현상 유지 — ADR-0222 의 verbatim table 을 그대로 둔다

- **설명**: 재분류하지 않는다. ADR-0222 의 후속 항목 (1) 을 계속 pending 으로 둔다.
- **장점**: 아무것도 안 한다. diff 0.
- **단점**: **Option A 의 선행 조건이 영영 충족되지 않는다.** misclassified data
  위에 메커닉을 얹으면 실수가 굳어진다. ADR-0222 가 후속 항목으로 명시한 일을
  하지 않는다.
- **Pillar 정합**: 실패 (기록된 후속 항목을 실행하지 않는다).

## 추천 (Recommendation)

**Option 1 (strict review).** 분류 review 의 목적이 "틀린 분류를 고치되, 확실하지
않은 것은 고치지 않는 것" 이다. Option 2 는 classification 을 취향으로 바꾸고,
Option 3 는 기록된 후속 항목을 남겨 둔다.

## 사용자 결정 (Decision)

**2026-10-27 — strict review 를 실행하기로 결정했다.** 구현 완료·검증됨.

- [x] **Option 1 — strict review (명확한 이름만 정정, 모호한 이름은 기록)** — **채택·구현됨**
- [ ] Option 2 — 최대 review
- [ ] Option 3 — 현상 유지 (no-op)

### 결정된 내용

1. **분류 원칙.** 스킬의 `effect` 는 그 `id` 가 가리키는 메커닉을 말해야 한다.
2. **88개 전수 검토.** 20개를 정정하고, 나머지 68개를 검토해 두었다. 68개는
   **이미 맞거나 모호해서** 그대로 두었다.
3. **review 규칙 4개 (엄격히 적용).**
   - 기존 `SkillEffectKind` 값만 사용 (신규 effect 없음).
   - `name` / `cooldown_ms` 미변경.
   - `damage` 미변경 (per-ICE 유지).
   - 모호한 이름은 **변경하지 않고** competing readings 를 기록.
4. **ADR-0219 / ADR-0222 는 수정하지 않았다.** 둘 다 Accepted 이므로 immutable
   이다 (`AGENTS.md` §6). 관계는 이 ADR 에 기록한다.
5. **Option A 는 여전히 연기 상태다.** 효과 메커닉도 magnitude 도 구현하지
   않았다.

### 정정된 20개 (전부 `effect` 만 변경)

| skill id | before | after |
| --- | --- | --- |
| `addiction_loop` | attack | dot |
| `ai_subversion` | buff | debuff |
| `alarm_propagate` | attack | debuff |
| `asset_seize` | attack | debuff |
| `backup_dispatch` | attack | buff |
| `broadcast_signal` | attack | debuff |
| `buffer_check` | attack | detect |
| `data_archive` | attack | buff |
| `info_warfare` | attack | debuff |
| `maintain_order` | attack | buff |
| `media_alert` | attack | debuff |
| `narrative_warp` | buff | debuff |
| `packet_route` | attack | buff |
| `priority_delivery` | attack | buff |
| `reality_distortion` | buff | debuff |
| `reality_warp` | buff | debuff |
| `report` | attack | detect |
| `report_alert` | attack | debuff |
| `report_distribute` | attack | debuff |
| `watchdog_mark` | buff | debuff |

### 의도적으로 고치지 않은 10개 (ambiguous — competing readings 기록)

| skill id | 현재 effect | competing readings |
| --- | --- | --- |
| `ai_negotiate` | buff | 대상을 설득해 유리하게 만들면 buff / 대상의 행동을 망가뜨리면 debuff |
| `aleph_fragment` | buff | boss `aleph` 가 자기 조각을 현현하는 buff / 공격형 조각의 dot·debuff |
| `enforce_contract` | attack | 계약 위반자를 때리는 attack / 강제 집행 자체가 debuff |
| `ice_break` | attack | 얼음을 깨는 공격 / ICE 를 무력화하는 debuff |
| `intimidation` | attack | 기만·위협 공격 / 상대 능력 debuff |
| `loa_command` | attack | 명령으로 때리는 공격 / 명령이 대상을 debuff |
| `matrix_merge` | attack | 행렬 결합 공격 / 대상을 흡수하는 buff |
| `orbital_command` | attack | 궤도 지휘 공격 / 지휘권夺取 buff |
| `straylight_protocol` | attack | Straylight 응답 공격 / 프로토콜 적용 debuff |
| `territorial_mark` | buff | 영역 표시 buff / 공격 준비 debuff |

**`aleph_fragment` 에 대한 특히 부연.** 이 id 는 boss `aleph` 의 namesake 스킬이고,
현재 **0-damage `buff`** 다. 형제 스킬인 `matrix_merge` / `ice_pierce` 는
15~18 피해를 준다. 숫자만 보면 `aleph_fragment` 가 그 siblings 에서 뚝 떨어져
**분류 오류처럼 보인다.** 하지만 이름은 boss 가 **자기 자신의 조각을 현현한다** 는
읽기가 자연스럽고, 이는 `construct_proxy` / `construct_summon` / `loa_summon` 으로
이어지는 **buff family** 와 일관된다. 따라서 **두기** 로 결정했다.

### self-correction — `narrative_attack` 와 `ice_break` 는 고쳤다가 되돌렸다

> **이 항목을 생략하면 안 된다.** review 가 "최대한 많이" 가 아니라 **"엄격히"**
> 적용됐다는 증거다.

`narrative_attack` 와 `ice_break` 는 review 과정에서 **한 번 정정된 뒤 되돌려졌다.**
두 이름 모두 공격 메커닉을 명시적이거나 그럴듯하게 가리키기 때문이다.
`narrative_attack` 은 이름이 "attack" 을 직접 말하고, `ice_break` 은 "ice 를
break 한다" 는 표현이 공격/파괴로 읽힌다. 두 entry 는 현재 모두 `attack` 이다.
**모호함이 아니라 명시성이므로** review 규칙 4번 (모호한 이름은 두기) 에 걸리지
않고, 정정 대상이 아니었다.

### 이미 옳다고 확인한 것 (Group D — 검토 후 미변경)

- **`detect` 6 id** — `scan`, `deep_trace`, `data_scan`, `intel_broker`,
  `inheritance_trace`, `lowbeer_vision`. 전부 `detect` 가 이름과 맞다.
- **`shield` 9 id** — `absorb_damage`, `archive_guard`, `damage_absorb`,
  `defense_grid`, `fortress_mode`, `shield_protocol`, `shield_wall`,
  `spirit_guard`, `vault_guard`. 전부 `shield` 가 이름과 맞다.

이 둘의 **문제점은 분류 오류가 아니다.** `detect` / `shield` 에 **combat effect 가
없다**는 것이 문제지, 이름과 분류가 어긋난 것이 아니다. 그것은 **Option A 의
문제**다.

**이미 자기 정합한 pair (따라서 미변경):**
- `memory_lock` (silence) vs `memory_overload` (dot)
- `stack_corruption` (dot) vs `stack_overflow` (stun)
- `data_scan` / `data_preserve` / `data_corrupt` / `data_melt` / `data_pollution`

## 결과 (Consequences)

### 긍정적 영향

- **분류 표가 이름을 반영한다.** 88개 중 20개가 정정되고, 나머지 68개는 이미
  맞거나 모호함이 근거되어 두었다. 이제 **Option A 를 신뢰할 수 있는 데이터
  위에서** 시작할 수 있다.
- **ADR-0219 / ADR-0222 의 load-bearing 예제가 고쳐졌다.** `corporate_guard` 의
  `report` 가 `attack` 으로 분류되어 있던 것이 `detect` 로 바로잡혔다.
- **테스트 하나가 결함을 pin 하고 있던 것을 바로잡았다.** 아래 「변경된 assertion
  하나」 참조.
- **새 effect 를 발명하지 않았다.** 기존 `SkillEffectKind` 값만 썼다.

### 부정적 영향 / 수용한 비용

- **정정이 현재는 플레이에서 보이지 않는다.** 밸런스 상세는 아래 「밸런스」 참조.
- **10개 ambiguous id 가设计上 미해결로 남는다.** 두 개의 읽기가 가능한 이름은
  **분류 규칙으로 판정할 수 없다.** 디자인 결정이 필요하다.
- **`attack` → non-damaging 정정은 발사 가능 여부를 바꾼다.** 해당 ICE 는
  0-damage 스킬을 가지므로 combat path 의 `damage > 0` 게이트를 통과하지 못하고
  plain auto-attack 으로 fall through 한다.

### 밸런스 — plain하게

`npm run balance` BEFORE vs AFTER → **byte-identical output (동일 MD5)**.
**6개 grade 전부 모든 column 이 0.0% delta.** 세 가지 configuration 에서 동일함을
확인했다:

- default (100 runs)
- `--runs 500`
- `--runs 200 --deck ppl`

**왜 아무것도 움직이지 않았는가 — 추측이 아니라 실측.**

- 12개 ICE 가 발사 가능한 스킬 집합을 바꾸었고, 8개가 per-tick damage 를
  바꾸었다.
- **그러나 그 12개 중 `ENCOUNTER_ICE_BY_GRADE` (24 slot / 18 unique id) 안에
  있는 것은 하나도 없다.**
- band 안에서 스킬을 가진 member 는 **둘뿐**이다 — `loa_entity` (g5) 와
  `aleph` (g6). **둘 다 이번 review 에서 건드리지 않았다.**
- 즉 **정정된 스킬들은 현재 encounter band 에서 도달 불가능하다.**

이 사실은 **ADR-0219 의 남은 항목 (encounter band 커버리지 확대)** 의 필요성을
강화한다. band 안에 스킬을 가진 ICE 가 2 slot뿐인现状에서는, 이 review 를
완료해도 그 결과가 **게임플레이에서 관측되지 않는다.**

**per-skill damage 참고 — "ICE 가 약해졌다" 는 단순화가 아니다.** 정정된
`attack` → non-damaging 스킬을 가진 ICE 는 스킬 피해 (`dmg_base + tier*2`)
대신 **plain auto-attack (`tier*3 + armor`)** 으로 떨어진다. 그래서 영향을 받은
ICE 몇몇은 tick 당 **더 많은** 피해를 준다. 예: `alarm_propagate` **+3**,
`data_archive` **+2**, `backup_dispatch` **+2**. 즉 이 변경은 "ICE 가 약해졌다" 가
아니다.

### 변경된 assertion 하나 — `web/tests/data_loaders.test.ts`

> **이 항목을 생략하면 안 된다.** 결함 하나가 테스트 하나에 새겨져 있었다.

**변경된 파일**: `web/tests/data_loaders.test.ts` — 테스트 이름
`"gives an offensive ICE skill a positive damage derived from its own row"` 가
`"derives skill damage from the owning row: offensive skills positive,
non-damaging skills zero"` 로 바뀌었다.

**BEFORE** (`web/tests/data_loaders.test.ts`):

```ts
expect(report.effect).toBe("attack");
expect(report.damage).toBeGreaterThan(0);
const raw = (data as Record<string, { dmg_base?: number }>)["corporate_guard"];
expect(report.damage).toBe(raw?.dmg_base);
```

**AFTER** (`web/tests/data_loaders.test.ts:399-428`):

```ts
expect(report.effect).toBe("detect");
expect(report.damage).toBe(0);

// The offensive path is pinned on `loa_baron`'s `loa_command` (`attack`):
// its damage is the owning row's own `dmg_base` stat.
expect(command.effect).toBe("attack");
expect(command.damage).toBeGreaterThan(0);
const raw = (data as Record<string, { dmg_base?: number }>)["loa_baron"];
expect(command.damage).toBe(raw?.dmg_base);
```

**이 assertion 은 결함을 pin 하고 있었다.** 이전 assertion 은
`report.effect === "attack"` 을 요구했는데, `report` 는 **heuristic 의 오분류**
그 자체였다. 즉 테스트가 **오류를 contract 로 고정**하고 있었다.

**선언된 의도는 보존되었다.** 이 테스트의 의도는 **damage 파생 계약**이다 —
offensive 스킬은 owning row 의 `dmg_base` 인 양수 `damage` 를 받고,
non-damaging 스킬은 0 을 받는다. 그 계약은 그대로다. 이제
**정정된 `report` 분류**를 pin 하면서, **공격 경로는 여전히 공격인 스킬**
(`loa_baron` 의 `loa_command`) 로 검증한다. 이전보다覆盖面이 줄지 않았다.

**이것이 결함을 새긴 테스트 하나뿐이다.** 나머지 assertion 은 미변경이다.

### 후속 항목

1. **ambiguous 10개 id** — 아래 competing readings 표의 각 id 에 디자인 판정이
   필요하다. 분류 규칙으로는 해결할 수 없다.
2. **Option A** — shield / heal / regen / buff 메커닉 + magnitude authoring.
   **지금 unblocked** 이지만 여전히 **deferred** 다. magnitude 는 하나도 저술하지
   않았다.
3. **encounter band 커버리지** — 24 slot 중 스킬을 가진 것은 2 slot뿐이고, 이번
   review 의 결과는 그 안에서 보이지 않는다.
4. **`detect` / `silence` / `slow` / `stun` 의 combat effect 부재** — 이들도
   combat effect 가 없다. 게다가 여러 개는 combat 이 아니라
   alarm / information system 에 속할 수 있다 (ADR-0219 Open Question 3).

### ADR-0222 / ADR-0219 에 대한 관계 메모

> **ADR-0222 와 ADR-0219 는 Accepted 이므로 immutable 이다** (`AGENTS.md` §6 —
> Accepted 결정 임의 변경 금지). **두 파일은 수정하지 않았다.**
> **ADR-0222 는 분류를 data 로 옮기고 이 review 를 pending 으로 기록했다.**
> **본 ADR 은 그 review 를 실행한다.** ADR-0219 의 Option A 는 이 review 가
> 선행 조건으로 필요했고, 그 선행 조건이 이제 충족되었다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

- `web/src/data/ice_types.json` — `skill_defs` **88 entry** 중 **20 entry 의
  `effect` 만** 정정. `git diff --numstat` = **20 deletions + 20 insertions**,
  그리고 **변경된 40줄 전부가 `"effect":` 줄** (diff 를 걸러서 실측).
- `web/src/data/ice_types.json` — `name` 변경 **0**, `cooldown_ms` 변경 **0**,
  id 집합 **동일 (88)**.
- `web/src/data/ice_types.json` — **97 ICE row 와 다른 모든 top-level key 는
  byte-identical.** `"skill_defs": {` 앞의 파일 prefix 를 raw text 로 비교해
  확인했다.
- `web/src/data/ice_types.json` — top-level key **98개**, `skill_defs` 는
  **마지막 key**. 따라서 `Object.values(iceTypesData)[0]` 은 여전히
  `standard` (`ICE — Standard`).
- `web/src/data/ice_types.json` — **신규 `SkillEffectKind` 없음.** 사용 중인
  effect 값 **15종 전부 기존 union member** 다. `web/src/core/combat_models.ts`
  와 `web/src/core/types.ts` 는 **미변경**.
- `web/tests/data_loaders.test.ts:399-428` — **변경된 assertion 하나.**
  `report.effect` 를 `detect` 로 pin 하고, 공격 경로는 `loa_baron` 의
  `loa_command` (`attack`) 로 pin 한다. damage 파생 계약 의도는 보존.
- **effect 분포 (after, 88 entry 실측):** attack 10 / buff 17 / debuff 16 /
  shield 9 / detect 8 / dot 8 / multi_hit 5 / poison 3 / stun 3 /
  heavy_attack 2 / pierce 2 / silence 2 / heal 1 / regen 1 / slow 1.
  (before: attack 25 / buff 17 / shield 9 / dot 7 / detect 6 / multi_hit 5 /
  debuff 4 / poison 3 / stun 3 / heavy_attack 2 / pierce 2 / silence 2 /
  heal 1 / regen 1 / slow 1)
- **밸런스:** `npm run balance` BEFORE vs AFTER — **byte-identical output (동일
  MD5)**, 6개 grade 전부 모든 column **0.0% delta**. default 100 runs,
  `--runs 500`, `--runs 200 --deck ppl` 세 configuration 모두 동일.
- **밸런스가 안 움직인 이유 (실측):** 12 ICE 가 발사 가능 스킬 집합 변경, 8 ICE
  가 per-tick damage 변경. 그러나 **12개 모두 `ENCOUNTER_ICE_BY_GRADE` 밖.**
  band 안 스킬 보유 member 는 `loa_entity` (g5) 와 `aleph` (g6) 뿐이고 둘 다
  미변경.
- 게이트: `npm test` **125 files / 2951 tests, 0 failures**; `tsc --noEmit`
  **0 errors**; `eslint` **0 errors**.

**Notes**:

- **diff 는 `web/` 2개 파일뿐이다** — `web/src/data/ice_types.json`
  (+20 / -20, `effect` 줄만) 과 `web/tests/data_loaders.test.ts`
  (+22 / -7, assertion 하나). `web/src/core/combat_models.ts`,
  `web/src/core/types.ts`, combat path, 밸런스 상수는 **미변경**이다.
- **Option A 는 구현하지 않았다.** effect 메커닉도 magnitude 도 없다. combat
  path (`web/src/core/state_actions_combat.ts`), `web/src/core/ice_ai.ts`,
  `web/src/core/ice_scaling.ts`, `web/src/core/types.ts` 는 **모두 미변경**이다.
- **ADR-0219 / ADR-0222 를 포함한 기존 ADR 은 하나도 수정하지 않았다.**
  Accepted 결정은 immutable 이고 (`AGENTS.md` §6), 관계는 이 ADR 에 기록했다.
- **10개 ambiguous id 는 설계상 미해결로 남겼다.** 고치지 않은 것은
  실수가 아니라 판정이다.
- **정정은 현재 플레이에서 관측되지 않는다.** encounter band 안의 스킬 보유
  ICE 2종 (`loa_entity` / `aleph`) 이 미변경이기 때문이다.

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `web/src/data/ice_types.json` — `skill_defs` 의 **20 entry 의 `effect` 값만**
  정정. `name` / `cooldown_ms` / id 집합 / 97 ICE row / 다른 모든 top-level key
  미변경.
- `web/tests/data_loaders.test.ts` — damage 파생 assertion 하나 갱신
  (`report` 의 misclassification 을 pin 하던 것을 정정된 분류로 pin + 공격
  경로를 별도 스킬로 pin).

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/combat_models.ts`, `web/src/core/types.ts` — `SkillEffectKind` /
  `StatusEffectKind` union **미변경** (신규 effect 없음)
- `web/src/core/state_actions_combat.ts` — enemy combat path (Option A — 연기)
- `web/src/core/ice_ai.ts` — `PERSONALITY_SKILL_PREFERENCE`, `selectSkillByPersonality`
- `web/src/core/ice_scaling.ts` — `ENCOUNTER_ICE_BY_GRADE` / 밸런스 상수
- `web/src/data/ice_types.json` 의 97 ICE row — **byte-identical**
- ADR-0219, ADR-0222 를 포함한 기존 ADR — **미수정** (immutable)

### 후속 항목 (이번 ADR 범위 밖)

- ambiguous 10개 id 의 디자인 판정 (위 competing readings 표)
- Option A — shield / heal / regen / buff 메커닉 + magnitude authoring (연기)
- `ENCOUNTER_ICE_BY_GRADE` 커버리지 확대
- `detect` / `silence` / `slow` / `stun` 의 combat effect 설계 (ADR-0219 Open
  Question 3)

## 관련 결정

- ADR-0216 (derived ICE skill metadata) — **heuristic 의 owner.** 그 token rule
  이 만든 실수가 이번 review 의 대상이다.
- ADR-0218 (ICE skill selection fallback) — 발사 가능 스킬 선택 규칙의 owner.
  `damage > 0` 게이트가 이번 정정의 결과를 결정한다 (0-damage 스킬은 발사 불가).
- ADR-0219 (non-damaging ICE 스킬 효과) — **Option A 의 owner.** 이 review 가
  Option A 의 선행 조건이다. **ADR-0219 는 수정하지 않았다** (immutable).
- ADR-0222 (ICE skill 메타데이터가 heuristic 에서 authored data 로 이동한다) —
  **분류를 data 로 옮기고 이 review 를 pending 으로 기록한 결정.** 본 ADR 이
  그 review 를 실행한다. **ADR-0222 는 수정하지 않았다** (immutable).

## 변경 이력

- 2026-10-27: Draft 작성 + Accepted (strict review — 88 entry 전수 검토, 20
  정정, 68 유지, 10 ambiguous 기록) — 구현 완료·검증. ADR-0222 후속 항목 (1)
  실행. ADR-0219 Option A 의 선행 조건 충족. self-correction
  (`narrative_attack` / `ice_break` 되돌림) 기록.
