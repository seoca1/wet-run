# ADR-0222: ICE 스킬 메타데이터가 heuristic 에서 authored data 로 이동한다 (ADR-0219 Option D)

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — dead combat path, ADR-0216/0219 sibling)
**관련**: [ADR-0216 — derived ICE skill metadata](./0216-derived-ice-skill-metadata.md), [ADR-0219 — non-damaging ICE 스킬 효과](./0219-non-damaging-ice-skill-effects.md), [ADR-0218 — ICE skill selection fallback](./0218-ice-skill-selection-fallback.md), [ADR-0220 — `parseIce` 가 authored `personality` 을 복원한다](./0220-parse-ice-personality-restore.md), [ADR-0221 — `parseIce` 가 authored `aggression` 을 복원한다](./0221-parse-ice-aggression-restore.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-27 에 결정·구현·검증까지 완료되었다.
> 구현 범위는 **데이터 저술 (data authoring)** 하나다 — ADR-0219 의 **Option D** 를
> 실행한다. 88개 스킬의 분류 (classification) 를 authored data 로 옮기고, ADR-0216 의
> token heuristic 을 제거한다.
>
> **아직 착수되지 않은 것** (본 ADR 의 범위 밖, 후속 항목):
> (1) non-damaging 효과 자체의 구현 (Option A),
> (2) encounter band 커버리지 확대.
> **분류 정정 (reclassification) 도 하지 않았다.** 표는 heuristic 의 출력을
> **verbatim** 으로 옮겼을 뿐이므로, heuristic 의 실수는 이제 데이터가 되었다 — 그
> 실수들을 **검토하고 고치는 것은 별도의 결정**이다 (「후속 항목 (1)」).
>
> **행동은 byte-identical 이다.** combat path, 밸런스 상수, effect mechanics 는
> **하나도 바뀌지 않았다.** `npm run balance` 출력이 BEFORE/AFTER 동일하고, 파생
> 스킬 테이블 dump 도 동일하다.

## 컨텍스트 (Context)

### ADR-0216 이 만든 heuristic

ADR-0216 은 `web/src/core/ice_skills.ts` 를 신설했다. 그 모듈은 `ice_types.json` 의
**bare id string** (`"skills": ["manifest_form", "voodoo_curse"]`) 을 typed skill
object (`{id, name, effect, cooldownMs, damage}`) 로 확장하되, **`name` 과 `effect` 를
skill id 에서 파생 (derive) 했다.** 순서는 있는 snake_case **token rule** 기반이었다:

- `ICE_SKILL_EFFECT_RULES` — 토큰 키워드 → effect 매칭 테이블
- `iceSkillEffectFor(skillId)` — 토큰 규칙으로 effect 결정
- `iceSkillNameFor(skillId)` — id 를 Title Case 로 변환
- `cooldownMs` — **전 스킬 고정 4000**
- `damage` — offensive effect 면 **소유 ICE row 의 `dmg_base`**, non-damaging effect 면 **0**

즉 **스킬이 무엇을 하는지 (classification) 가 코드 안에 박혀 있었고**, 데이터는
id 만 있었다. `ice_types.json` 의 97 ICE row 에 걸친 distinct skill id 는 **88개**다.

### ADR-0219 가 Option D 를 추천했다

ADR-0219 (Accepted) 는 non-damaging 효과의 운명을 결정하면서 **B → D → A** 순서를
추천했다. 그 중:

> **Option D — 메커닉은 유예하고 데이터부터.** 88개 스킬의 메타데이터를
> `ice_types.json` 에 authoring 한다. ADR-0216 의 loader-side derivation
> (`web/src/core/ice_skills.ts:23-60` token rule + `:143` damage 규칙) 을 authored
> data 로 대체한다. 효과 자체는 아직 구현하지 않는다.

D 의 근거는 ADR-0219 가 직접 적시한 것이다 — **Option A 의 최대 비용 항목
(magnitude 부재) 이 해소된다.** non-damaging 효과를 구현하려면 "shield 가 몇을
흡수하는가" "heal 이 몇을 회복하는가" 같은 per-skill 값이 필요하고, 그 source data 가
어디에도 없다. D 를 먼저 하면 그 작업이 나중에 잘게 쪼개진다.

ADR-0219 는 D 를 **연기 (deferred)** 했다 (B 만 채택). **본 ADR 이 그 연기를
해제하고 D 를 실행한다.**

### 왜 heuristic 이 제거 대상인가 — ADR-0219 가 직접 지적한 사실

ADR-0219 의 Option D 단점 항목:

> combat 무변경 상태에서 metadata 를 authoring 하면, ADR-0218 이 만든
> `damage > 0` 규칙과 authored 값의 관계를 다시 정의해야 한다 (authored `damage`
> 가 0 이면 발 불가 — 지금과 동일한 contract 가 authored data 에서도 성립해야 함).

그리고 더 근본적으로 — **heuristic 은 "이 스킬이 실제로 무엇인지" 를 말하지
않는다.** ADR-0219 의 컨텍스트는 결정적인 증거다: `ice_types.json` 의 personality
분포 (aggressive 80 / defensive 12 / stealth 5 / **support 0**) 와 non-damaging
스킬의 실측 분포가 **서로 어긋난다.** `defensive` ICE 가 소유한 `report` 가
`attack` 으로 분류되고, `support` archetype 은 **한 종도 존재하지 않는다.** 이런
분류가 검토 불가능한 코드의 규칙 안에 숨어 있으면 **발견 자체가 불가능하다.**
**authored table 로 바꾸면 그 표를 읽고 고칠 수 있다** — 그것이 D 의 실질 이득이다.

### 이미 해결된 전제 조건

ADR-0219 가 D 를 미룬 또 다른 이유는 loader 결함이었다. `parseIce` 가 `personality`
(ADR-0220) 과 `aggression` (ADR-0221) 을 조용히 drop 하던 결함 계열이 **이미 닫혔다.**
즉 지금 catalog 의 authored 값은 **런타임에 닿는다.** D 는 그 위의 데이터 저술
작업이다.

## 고려한 옵션

### Option 1: D 를 실행한다 — heuristic 제거 + authored table (선택)

- **설명**: `ice_types.json` 에 `skill_defs` top-level key 를 신설해 88개 스킬의
  `{name, effect, cooldown_ms}` 를 authoring 한다. `ice_skills.ts` 의 token heuristic
  (`ICE_SKILL_EFFECT_RULES` / `iceSkillEffectFor` / `iceSkillNameFor`) 을 **삭제**하고
  lookup 으로 교체한다. 효과 구현은 하지 않는다.
- **장점**:
  - 분류가 **authored, reviewable data** 가 된다. 코드 안의 규칙이 아니다.
  - **ADR-0219 의 Option A 비용 (magnitude authoring) 이 미리 해소된다.**
  - ADR-0216 이 Option 1 (hand-authored catalog) 로 명시적으로 미뤿던 그 작업이다.
  - combat path 무변경 → 밸런스 재측정 불필요, 되돌리기 쉽다.
  - ADR-0219 가 만든 계약 (`damage > 0` 인 스킬만 발사) 이 authored data 에서도
    그대로 성립한다.
- **단점**:
  - **88 entry hand-maintained 데이터** — 유지보수 부담. ADR-0216 이 이걸 "단기
    shipping 불가" 로 미룬 이유다.
  - **heuristic 의 실수가 데이터로 승계된다.** 표가 그 실수를 드러내지만, 동시에
    **고치려면 별도 결정이 필요하다** (재분류는 밸런스를 움직인다).
  - `ice_types.json` 이 **두 가지 관심사 (ICE row + 스킬 테이블) 를 섞어 담는다.**
  - loader 가 파일 전체를 받으므로 `skill_defs` 를 **ICE row 로 오인하지 않도록**
    skip 해야 한다 — 구조적 부작용이 하나 생긴다 (아래 「adapted assertion」 참조).
- **Pillar 정합**:
  - P3 (The Flatline): ✅ combat path 는 그대로지만, 죽은 archetype 의 원인이
    **분류 데이터의 문제로 드러난다** — 곧바로 고칠 수 있게 된다.
  - P4 (The Build): ✅ 불투명한 heuristic 이 reviewable data 로 대체된다.
  - P5 (The Style): ✅ skill 이름이 authored 이므로 flavor 가 코드 규칙에 묶이지 않는다.

### Option 2: D 를 계속 연기한다

- **설명**: ADR-0219 의 결정을 그대로 둔다. D 는 미착수 상태.
- **장점**: 아무것도 안 한다. diff 0.
- **단점**: **Option A 의 magnitude 공백이 그대로 남는다.** Option A 를 시작할 때
  88 entry authoring 이 선행 작업으로 다시 등장한다. heuristic 이 계속 살아 있으므로
  misclassification 이 계속 **발견 불가능**하다.
- **Pillar 정합**: 실패 (ADR-0219 가 이미 결정한 방향을 실행하지 않는다).

### Option 3: D 와 A 를 한 번에

- **설명**: authored table 과 함께 non-damaging 효과 메커닉을 구현하고 밸런스를
  재-calibration 한다.
- **단점**: **ADR-0219 가 명시적으로 순서를 분리했다.** A 는 calibrated 상수 두 개
  (`ENCOUNTER_HP_BY_GRADE` / `ENCOUNTER_DMG_BONUS_PCT_BY (ADR-0211)`) 를 손대야
  하고, reach 가 좁아 (band 24 slot 중 스킬 보유 2 slot) 측정 신호가 작다. 되돌리기도
  어렵다 (데이터 + 메커닉 + 밸런스가 한 묶음).
- **Pillar 정합**: 실패 (ADR-0219 의 B → D → A 순서를 무시한다).

## 추천 (Recommendation)

**Option 1 (D 실행).** ADR-0219 가 이미 순서를 결정했으므로 이번 ADR 는 그 순서를
따르는 것이고, 새로 고를 것은 아니다. D 는 데이터 작업이라 밸런스 측정과 분리되고
되돌릴 수 있다.

## 사용자 결정 (Decision)

**2026-10-27 — ADR-0219 의 Option D 를 실행하기로 결정했다.** 구현 완료·검증됨.

- [ ] Option A — Full implementation (non-damaging 효과 + magnitude) — **연기 (deferred)**
- [ ] Option B — Consistency-only — 이미 ADR-0219 에서 채택·구현됨
- [ ] Option C — 현상 유지 (no-op)
- [x] **Option D — 메타데이터 선행 authoring (ADR-0219 Option D)** — **채택·구현됨**
- [ ] D 와 A 를 한 번에
- [ ] 기타: —
- [ ] Defer (다음 단계로 미룸)

### 결정된 내용

1. **`web/src/data/ice_types.json` 에 새 top-level key `skill_defs` 하나가 추가된다.**
   88개 skill id 전부에 대한 `{ name, effect, cooldown_ms }` map 이다. 값은
   **heuristic 의 현재 출력을 verbatim 으로 materialized** 한다 (재분류 없음). 97 ICE row
   와 다른 모든 top-level key 는 **byte-identical** 이다.
2. **`web/src/core/ice_skills.ts` 의 token heuristic 은 삭제된다.**
   `ICE_SKILL_EFFECT_RULES`, `iceSkillEffectFor`, `iceSkillNameFor` 세 symbol 이
   사라지고, `parseIceSkills` 는 `skill_defs` 를 **조회**한다.
3. **`damage` 는 의도적으로 per-ICE 에 남는다.** offensive effect 면 소유 ICE row 의
   `dmg_base`, non-damaging effect 면 `0` 이며, **`skill_defs` 로 옮기지 않는다.**
   같은 skill id 가 `dmg_base` 가 다른 row 에 소유될 수 있기 때문이다 — 예를 들어
   `ice_pierce` 는 `dmg_base` 12 인 row (`black_construct`) 와 15 인 row (`aleph`) 에
   동시에 소유된다. 표로 옮기면 **행동이 바뀐다.**
4. **미지의 skill id 는 throw 한다.** `[data_loaders]` prefix 메시지가 해당 ICE 의
   이름과 id 를 함께 명시한다. **조용한 heuristic fallback 은 없다** — 그 fallback 이
   바로 제거 대상인 결함 계열이다.
5. **효과 메커닉과 magnitude 는 authoring 하지 않았다.** 그건 Option A 다.

## 결과 (Consequences)

### 긍정적 영향

- **스킬 분류가 불투명한 heuristic 이 아니라 authored, reviewable data 다.** 이제
  88개 스킬의 분류를 **읽고 논하고 고칠 수 있다.**
- **새 skill id 추가가 조용한 실패에서 명시적 실패로 바뀐다.** `skill_defs` 엔트리가
  없으면 loader 가 throw 한다 — **loud, not silent.**
- **행동이 byte-identical 로 증명된다.** 두 개의 독립적 검사:
  `npm run balance` 출력이 BEFORE/AFTER **동일 MD5**, 파생 스킬 테이블
  (88 id × name/effect/cooldownMs/per-ICE damage) dump 이 BEFORE/AFTER **동일 MD5**.
- **Option A 가 싸졌다.** 이제 Option A 는 **magnitude 와 메커닉만** 추가하면 된다.
  88 entry 분류 authoring 작업은 이미 끝났다.
- **분류가 드러나면서 **구조적 사실**이 문서화 가능하다.** 아래 「authored table 이
  드러낸 구조적 발견」 참조.

### 부정적 영향 / 수용한 비용

- **테스트 하나의 카운팅 방식을 바꿔야 했다.** `web/tests/missions.test.ts` 의
  "loads exactly 97 ICE types" 가 `expect(Object.keys(data).length).toBe(97)` 에서
  `skill_defs` key 를 걸러낸 뒤 세는 형태로 바뀌었다. **구조적으로 강제된 변경이다**
  (아래 「adapted assertion」 상세).
- **`ice_types.json` 이 두 가지 관심사를 섞어 담는다** (ICE row + 스킬 테이블).
  **수용한다** — loader 는 그 파일을 **전체로** 받는다. 별도 파일로 분리하려면
  `parseIce` 에 **두 번째 catalog 를 thread** 해야 하는데, 이는 D 의 목표 (데이터
  저술) 에 비해 변경 표면이 더 커진다.

### authored table 이 드러낸 구조적 발견

> **이것이 D 의 실제 산출물이다.** heuristic 이 코드 안에 숨어 있을 때는 **이 사실들을
> 알아낼 수 없었다.** 표로 옮기자 드러났다.

- **88개 중 44개 스킬이 non-damaging 이다** (buff 17 / shield 9 / detect 6 /
  debuff 4 / stun 3 / silence 2 / slow 1 / heal 1 / regen 1). 이 44개는 combat path
  의 `damage > 0` 게이트 때문에 **구조적으로 발사 불가능 (unfireable) 하다.** 나머지
  44개는 발사 가능하다.
- **스킬을 가진 ICE 9종이 완전히 inert 하다** (모든 스킬이 0-damage):
  `archive_sentinel`, `goliath_defensive`, `loa_priest`, `loa_zombie`,
  `sense_net_spin`, `standard_corrupted`, `ta_daemon`, `ta_inheritor`,
  `watchdog_defensive`.
- **17개 ICE 는 `skill[0]` 이 발사 불가능하고 뒤에 발사 가능한 스킬이 있다** —
  **이것이 바로 ADR-0218 의 selection ordering 이 작동하는 표면이다.**
- **`support` archetype 은 ICE 가 0종이다.** `stealth` 는 5종이고 **전부
  `skills: []`** 이다 (즉 personality preference 매칭 자체가 일어나지 않는다).

### adapted assertion — 변경된 테스트 하나와 그 근거

> **이 항목을 생략하면 안 된다.** diff 에서 보이는 테스트 변경이 무엇이며 왜
> **약화가 아니라 구조적 강제**였는지 기록한다.

**변경된 파일**: `web/tests/missions.test.ts` — 테스트 "loads exactly 97 ICE types
(full Python catalog)".

```ts
// BEFORE
expect(Object.keys(data).length).toBe(97);

// AFTER
const iceIds = Object.keys(data).filter((id) => id !== "skill_defs");
expect(iceIds.length).toBe(97);
```

**왜 구조적으로 강제되었는가.** `ice_types.json` 은 **flat map of ICE rows** 로
소비된다 (`loadIceCatalog` 가 `Object.entries(raw)` 를 순회하며 각 entry 를 ICE row
로 파싱한다). 따라서 **어떤 top-level key 를 추가하든 raw key 카운트는 98 이 된다.**
ADR-0220 (`personality`) 과 ADR-0221 (`aggression`) 이 top-level key 를 추가하지
않았기 때문에 이 문제는 그때는 발생하지 않았다 — `skill_defs` 가 **첫 번째
non-ICE top-level key** 다.

**assertion 은 약화되지 않았다.** 그 **선언된 의도 — "정확히 97 개의 ICE type" —
는 보존되고 여전히 97 에 pin 된다.** 세는 대상만 "raw top-level key" 에서
"ICE row" 로 바뀌었을 뿐이다. 약화·완화·삭제된 것이 아니다.

**행위에 영향을 주는 assertion 은 하나도 건드리지 않았다.** skills mapping, effect
값, damage semantics, personality/aggression 분포 assertion 전부 **미변경**이다.
변경된 파일은 `web/tests/missions.test.ts` **하나뿐**이며 diff 는 6줄이다.

**2차 처리 — `skill_defs` 를 마지막에 붙인 이유.** `web/tests/property_save_fuzz.test.ts:39`
는 `Object.values(iceTypesData) as unknown as Ice[]` 로 전체를 **ICE 배열로** 캐스팅한다.
`skill_defs` 를 **마지막 key** 로 append 하면 `Object.values(iceTypesData)[0]` 은
여전히 `standard` (`ICE — Standard`) 로 resolve 되고, fuzz 테스트가 참조하는 첫 ICE 가
바뀌지 않는다. (이 순서 선택은 실측으로 확인했다 — `Object.values(d)[0].name` =
`ICE — Standard`.)

### 후속 항목

#### (1) 스킬 분류 review 는 **PENDING** — ★ 최우선 후속 항목

> **표는 heuristic 의 출력을 verbatim 으로 materialized 했다.** 즉 **heuristic 의
> 실수는 이제 데이터가 되었다.** 그것을 고치는 것은 **밸런스를 움직이는 변경**이라
> **별도의 결정이 필요하다.**

suspected misclassification (authored table 을 직접 읽고 추출한 것):

**(a) `attack` fallback 으로 떨어진 utility id**

token 규칙이 어떤 effect 토큰도 매칭하지 못하면 `attack` fallback 이 걸린다. 아래
id 들은 **모두 `attack` 으로 분류되어 있다** — 이름이 읽기에는 공격이 아니다:

```
report, report_alert, report_distribute, broadcast_signal, media_alert,
alarm_propagate, packet_route, priority_delivery, backup_dispatch,
buffer_check, data_archive, maintain_order, addiction_loop, info_warfare,
asset_seize
```

**(b) `buff` 로 분류되었지만 target-directed 로 읽히는 id**

```
ai_subversion, ai_negotiate, narrative_warp, reality_warp, reality_distortion,
aleph_fragment, watchdog_mark, construct_proxy
```

**(c) `detect` 로 분류되었지만 공격적인 owner 에 붙은 id**

| id | owner (personality / aggression) |
|---|---|
| `lowbeer_vision` | `peripheral_ascended` (aggressive / boss) |
| `data_scan` | `hosaka_analyst` (aggressive / standard) |
| `intel_broker` | `sense_net_informer` (aggressive / standard) |
| `inheritance_trace` | `ta_daemon` (aggressive / aggressive) |

**load-bearing 예시.** `corporate_guard` (defensive) 가 소유한 `report` 는
`attack` 으로 분류되어 있다 — **이것이 바로 ADR-0219 가 worked example 로 쓴
스킬이다.** def-grade ICE 의 "공격" 스킬이 실제로는 보고 행위다.

**재분류는 밸런스를 바꾼다.** `report` 를 `detect` 로 바꾸면 `corporate_guard` 의
스킬이 0-damage 가 되어 **발사 불가능**해진다 (그 ICE 는 `defensive` 이고, 스킬이
두 개 중 `scan`(detect) 뿐이라면). 즉 재분류는 **스킬 발사 여부 자체를** 바꾼다.
**자체 ADR + 밸런스 재측정 필요.**

#### (2) Option A 는 여전히 연기 상태다

enemy combat path 에 `shield` / `heal` / `regen` / `buff` / `debuff` / `detect` /
`stun` / `slow` / `silence` 메커닉이 없다. magnitude 도 없다. `StatusEffectKind`
union 에 `shield` 가 없고 enemy combat path 는 `StatusEffectKind` 을 참조하지
않는다. **Option A 는 연기 상태다.**

#### (3) encounter band 커버리지

`ENCOUNTER_ICE_BY_GRADE` (`web/src/core/ice_scaling.ts`) — 24 slot 중 **현재 2 slot
만** 스킬을 carry 한다 (`loa_entity` g5 / `aleph` g6), 둘 다 `aggressive` 다.
ADR-0219 의 open item 이 그대로 남았다.

### ADR-0219 에 대한 상태 메모

> **ADR-0219 는 Accepted 이므로 immutable 이다** (`AGENTS.md` §6 — Accepted 결정
> 임의 변경 금지). ADR-0219 의 「Implementation Status」 는 여전히 Option D 를
> "연기" 로 기술한다. **본 ADR 은 그 기대를 D 항목에 한해 supersede 한다.**
> **ADR-0219 는 수정하지 않았다** — 이 관계는 여기 기록한다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:
- `web/src/data/ice_types.json` — 새 top-level `skill_defs` key, **88 entry**. 각 entry
  는 `{name, effect, cooldown_ms}` (`cooldown_ms` 는 전부 4000 — heuristic 의 고정값
  을 그대로 승계)
- `web/src/data/ice_types.json` — `git diff --stat` = **442 insertions, 0 deletions**
  (pure insertion). 97 ICE row 와 다른 모든 top-level key 는 **byte-identical**
- `web/src/core/ice_skills.ts` — token heuristic **삭제**
  (`ICE_SKILL_EFFECT_RULES` / `iceSkillEffectFor` / `iceSkillNameFor` 3 symbol 소멸),
  `skill_defs` **조회 추가**. **147 → 187 LOC**
- `web/src/core/ice_skills.ts:87-125` — `parseIceSkillDefs` 신규. `skill_defs` table 을
  검증하고 typed map 으로 정규화한다 (malformed entry 는 coerce 하지 않고 throw)
- `web/src/core/ice_skills.ts:169-174` — `parseIceSkills` 의 `skill_defs` lookup.
  미지의 id 는 `[data_loaders]` prefix 로 throw
- `web/src/core/ice_skills.ts:183` — `damage` 는 **per-ICE 유지**:
  `ICE_SKILL_NON_DAMAGE_EFFECTS.has(def.effect) ? 0 : damageBase`. `skill_defs` 에는
  `damage` 가 **없다**
- `web/src/core/ice_skills.ts:65-75` — `ICE_SKILL_NON_DAMAGE_EFFECTS` (9종) — loader
  규칙으로 유지 (per-skill 데이터가 아니라 damage 파생 규칙이므로 표에 두지 않음)
- `web/src/core/data_loaders.ts` — `ICE_SKILL_DEFS_KEY = "skill_defs"` 상수,
  `loadIceCatalog` 이 그 key 를 **skip** 하므로 **ICE row 로 반환되지 않는다**
  (catalog 은 여전히 정확히 **97 ICE row**)
- `web/src/core/data_loaders.ts` — `parseIce` 가 `skillDefs` 를 받아 `parseIceSkills` 로
  thread 한다
- **행동 증명 (byte-identical, 독립적 검사 2종)**:
  - `npm run balance` BEFORE vs AFTER — **동일 MD5** (`291bd69b2d370127a1c4821d2f965f68`)
  - 파생 스킬 테이블 dump (88 id × name / effect / cooldownMs / per-ICE damage) BEFORE vs
    AFTER — **동일 MD5** (`b3e08dd7cb600659a9c794d75328120d`)
- 게이트: `npm test` **125 files / 2951 tests, 0 failures**; `tsc --noEmit` **0 errors**;
  `eslint src scripts` **0 errors** (무관 파일 `src/input/keyboard.ts` 의 pre-existing
  warning 1건만 남음)
- **미지의 id throw 실측** (probe 로 확인):
  `[data_loaders] ice 'ICE — Probe': unknown skill id 'definitely_not_a_skill' — no entry in 'skill_defs'`
- 커버리지: catalog 가 선언한 **88** distinct skill id ↔ `skill_defs` **88** entry —
  **0 missing, 0 orphans** (양방향 대조로 확인)
- 구조적 발견 (실측): non-damaging 44 (buff 17 / shield 9 / detect 6 / debuff 4 /
  stun 3 / silence 2 / slow 1 / heal 1 / regen 1) vs 발사 가능 44; 완전히 inert 한
  스킬 보유 ICE **9종**; `skill[0]` 이 발사 불가하고 뒤에 발사 가능 스킬이 있는 ICE
  **17종**; `support` archetype ICE **0종**, `stealth` 5종 전부 `skills: []`

**Notes**:

- **diff 는 4개 파일이다** — `web/src/data/ice_types.json` (+442 / -0),
  `web/src/core/ice_skills.ts` (heuristic 삭제 + lookup 추가, 147 → 187 LOC),
  `web/src/core/data_loaders.ts` (+35 / -9), `web/tests/missions.test.ts` (+6 / -2).
  **기존 ICE row 하나도, 기존 assertion 하나도 약화되지 않았다.**
- **재분류는 하지 않았다.** `skill_defs` 의 값은 heuristic 의 **현재 출력**과
  **byte-identical** 하다 (derived table dump MD5 일치가 그 증거다). 따라서
  **분류 정정으로 봐서는 안 된다** — 후속 항목 (1) 참조.
- **`damage` 는 표로 옮기지 않았다.** 같은 skill id 가 `dmg_base` 12 인 row
  (`black_construct`) 와 15 인 row (`aleph`) 에 동시에 소유되는 `ice_pierce` 가
  그 근거다. 표로 옮기면 **행동이 바뀐다** — 그래서 `skill_defs` schema 에
  `damage` 필드가 **존재하지 않는다.**
- **ADR-0219 / ADR-0221 을 포함한 기존 ADR 은 하나도 수정하지 않았다.** Accepted
  결정은 immutable 이고 (`AGENTS.md` §6), ADR-0219 의 "D 는 연기" 기술은
  **본 ADR 로 supersede** 되지만 원본은 그대로 둔다.
- **Option A 는 구현하지 않았다.** effect 메커닉도 magnitude 도 없다. combat path
  (`web/src/core/state_actions_combat.ts`), `web/src/core/ice_ai.ts`,
  `web/src/core/types.ts`, `web/src/core/ice_scaling.ts`, 밸런스 상수는 **모두
  미변경**이다.
- **다음 분류 review 는 88 entry 전수 검토가 아니라 우선순위 기반**이다. (a) 그룹의
  15개 utility id 는 한 번에, (b) 그룹 8개, (c) 그룹 4개 순으로 보는 것을 권한다.

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `web/src/data/ice_types.json` — 신규 top-level `skill_defs` key (88 entry).
  ICE row 는 무변경
- `web/src/core/ice_skills.ts` — heuristic 3 symbol 삭제, `parseIceSkillDefs` 신규,
  `parseIceSkills` lookup 추가, `damage` per-ICE 규칙 유지
- `web/src/core/data_loaders.ts` — `skill_defs` 추출 + ICE row skip,
  `parseIce` 가 `skillDefs` thread
- `web/tests/missions.test.ts` — ICE 카운팅 방식 변경 (`skill_defs` key 제외).
  **선언된 의도 (97 ICE type) 는 그대로 pin 된다.**

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/state_actions_combat.ts` — enemy combat path (Option A — 연기)
- `web/src/core/ice_ai.ts` — `PERSONALITY_SKILL_PREFERENCE`, `selectSkillByPersonality`,
  `enemyShouldUseSkill`
- `web/src/core/types.ts` — `Ice` / `StatusEffectKind` 선언 (Option A — 연기)
- `web/src/core/ice_scaling.ts` — `ENCOUNTER_ICE_BY_GRADE` / 밸런스 상수
- `web/src/data/ice_types.json` 의 97 ICE row — **byte-identical**
- `web/scripts/balance_harness.ts`, `web/scripts/balance_sim.ts` — 밸런스 하네스

### 후속 항목 (이번 ADR 범위 밖)

- `web/src/data/ice_types.json` — `skill_defs` 분류 review 및 재분류 (밸런스 이동 →
  별도 ADR 필요) — 「후속 항목 (1)」
- `web/src/core/state_actions_combat.ts` / `web/src/core/types.ts` — non-damaging 효과
  메커닉 + magnitude (Option A) — 「후속 항목 (2)」
- `web/src/core/ice_scaling.ts` — encounter band 커버리지 확대 — 「후속 항목 (3)」

## 관련 결정

- ADR-0216 (derived ICE skill metadata) — **본 ADR 이 대체하는 결정.** 그
  `ice_skills.ts` 의 token heuristic 과 loader-side derivation 을 authored data 로
  대체한다
- ADR-0218 (ICE skill selection fallback) — 발사 가능 스킬 선택 규칙의 owner.
  authored table 이 드러낸 「`skill[0]` 발사 불가 + 뒤에 발사 가능 스킬」 17 ICE 가
  그 규칙이 작동하는 표면이다
- ADR-0219 (non-damaging ICE 스킬 효과) — **본 ADR 이 구현하는 결정.** Option D 의
  출처. ADR-0219 의 B → D → A 순서에서 **두 번째 단계**다. **ADR-0219 는 수정하지
  않았다** (immutable)
- ADR-0220 (`parseIce` 가 authored `personality` 을 복원한다) — sibling ADR.
  loader 결함 계열의 두 번째 instance
- ADR-0221 (`parseIce` 가 authored `aggression` 을 복원한다) — sibling ADR.
  loader 결함 계열의 마지막 instance

## 변경 이력

- 2026-10-27: Draft 작성 + Accepted (ADR-0219 **Option D** — 88개 스킬 메타데이터를
  authored data 로, heuristic 제거, 효과 메커닉은 미구현) — 구현 완료·검증.
  Consequences / Implementation Status 채움. ADR-0219 의 연기 항목 중 D 를
  해소. 분류 review 를 후속 항목으로 기록.
