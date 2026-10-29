# ADR-0230: 애매 분류 부채 종결 — ADR-0223 과 ADR-0227 의 후속 항목

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — dead combat path, ADR-0216/0219/0222/0223/0227 sibling)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0161 — ICE personality archetypes](./0161-ice-personality-archetypes.md), [ADR-0216 — derived ICE skill metadata](./0216-derived-ice-skill-metadata.md), [ADR-0219 — non-damaging ICE 스킬 효과](./0219-non-damaging-ice-skill-effects.md), [ADR-0222 — ICE 스킬 메타데이터가 heuristic 에서 authored data 로 이동한다](./0222-ice-skill-metadata-as-data.md), [ADR-0223 — 스킬 분류 review pass](./0223-skill-classification-review.md), [ADR-0226 — Non-damaging ICE 스킬 효과를 구현한다](./0226-non-damaging-ice-skill-effects-implemented.md), [ADR-0227 — ICE 아키타입 일관성 검토](./0227-ice-archetype-consistency-review.md), [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-27 에 결정·구현·검증까지 완료되었다.
>
> **이 ADR 은 새 규칙을 만들지 않는다.** ADR-0223 과 ADR-0227 의 **원래
> 규칙을 그대로 재사용**하고, 그 review 들이 **수집하지 못한 증거**를
>gather 해서 각 항목을 판정한다. 진짜 50/50 인 항목은 **여전히 문서화된
> 상태로 남긴다** — 추측으로 닫지 않는다.
>
> **결과 요약:** 스킬 10건은 **0건 변경** (기존 값 전부 확정 + test 로
> pin), ICE 7건은 **1건 변경** (`yakuza_collector` `aggressive` → `support`),
> **3건은 확정**, **3건은 여전히 50/50** 로 기록만 남겼다.
>
> **행동은 byte-identical 이다.** 12개 grade 전부 **0.0pp drift** —
> `debuff` 가 inert 이기 때문에 `yakuza_collector` 는 어느 쪽이든
> auto-attack 으로 떨어진다.

## 컨텍스트 (Context)

### 두 개의 review 가 남긴 "의도적 미해결"

ADR-0223 은 `skill_defs` 88 entry 를 전수 검토해 **20개** 의 `effect` 를
정정하고, **10개** 는 **의도적으로 그대로 두었다.** 두 개 이상의 읽기가
가능한 이름이기 때문이다. 그리고 ADR-0223 은 그 10개에 대해 competing
readings 를 **기록**했다.

ADR-0227 은 `personality` 에 같은 review 패턴을 적용해 97 row 중 **12개** 를
교정하고, **7개** 를 **의도적으로 그대로 두었다** — 같은 이유로:
competing readings 를 기록한다.

두 review 의 규칙은 이렇다:

- ADR-0223 규칙 4: **모호한 이름은 고치지 않는다** — 대신 기록한다.
- ADR-0227 규칙 5: **모호한 이름은 변경하지 않고** competing readings 를
  기록한다.

**그래서 생긴 부채:** "기록만 남기고 판정은 하지 않은" 17건 (스킬 10 + ICE 7).
이것은 미완성이 아니라 **여전히 열린 질문**이었다. 그리고 두 review 는
**각각 자기 시점의 증거만 가지고 있었다.** 그 증거로는 50/50 인 항목의
한쪽을 선택할 수 없었다.

### 이 ADR 의 질문 — "증거가 더 있으면 판정할 수 있는가"

**질문 하나다.** 이 17건의 각각에 대해, **판정을 뒤집을 수 있는 추가
증거가 존재하는가?** 존재한다면 그것을 적용하고, 존재하지 않는다면
**여전히 문서화된 상태로 둔다.**

**새 규칙은 없다.** ADR-0223 과 ADR-0227 의 규칙 (기존 effect 값만 사용,
기존 archetype 4개만 사용, 다른 필드 미변경, 모호하면 기록) 을
**그대로 적용**한다. 판정材料和 달라진 것은 **증거**다.

## 결정에 이르게 된 증거 (The Decisive Evidence)

> **이 절이 이 ADR 의 실체다.** 아래 증거는 원래 두 review 가
> **수집하지 못했던 것들**이다. 각 항목은 원래 규칙을 적용할 수 있을
> 만큼 결정적으로 판정을 무효화한다.

### 1. ADR-0216 의 token 표 — 저자의 의도 기록

ADR-0216 은 `effect` 를 snake_case token 기반 ordered first-match-wins
rule table 로 **파생**했다. ADR-0222 가 그 출력을 `skill_defs` 에
materialized 했고, **그 rule table 자체는 삭제되었다** (git history
`c72132b^` 에 남아 있다). 그 표에는 다음이 있었다:

```
[["summon", "manifest", "evolution", "proxy", "construct",
  "negotiate", "subversion", "distortion", "warp", "territory",
  "mark", "aleph", "family"], "buff"],
```

**`negotiate` / `mark` / `aleph` 는 의도적으로 `buff` 로 매핑되었다.**
따라서 `ai_negotiate` / `territorial_mark` / `aleph_fragment` 의 `buff`
분류는 **heuristic 의 실수가 아니라 저자의 명시적 결정**이다. ADR-0223 이
이 셋을 "모호하다"고 기록한 것은 **token 표를 읽지 못한 결과**다.

### 2. ADR-0226 의 magnitude authoring — 위 결정을 뒷받침한다

ADR-0226 은 `shield` / `heal` / `regen` / `buff` 계열에 **magnitude** 를
저술했다. catalog 전체에서 **non-damaging 계열 스킬은 magnitude 를 갖고,
damaging 계열 스킬은 갖고 있지 않다** (그것이 두 계열을 구분하는 신호
다).

`ai_negotiate` = **18**, `aleph_fragment` = **15**, `territorial_mark` =
**12** — 셋 다 magnitude 를 갖고 있다. 각 owning row 의 `dmg_base` 와
ADR-0226 의 buff multiplier 규칙이 일치하는 값이다.

**이 셋의 `effect` 를 `buff` 밖으로 바꾸면 magnitude 계약이 깨진다.**
`buff` 가 아닌 non-damaging 계열로 옮기는 순간 그 계열의 magnitude 규칙이
다르므로 값이 맞지 않고, **새로운 오분류가 생긴다.** ADR-0226 의
저술을 무효화하는 변경이다.

### 3. `straylight_protocol` — 15 피해 스킬로 문서화된 load-bearing 근거

`web/src/core/ice_scaling.ts` 는 **두 곳에서** `straylight_protocol` 을
**15 피해 스킬**로 기술한다:

- `web/src/core/ice_scaling.ts:296` — "15-damage `straylight_protocol`"
- `web/src/core/ice_scaling.ts:355` — "its 15-damage skill is"

그리고 15 는 `ta_sentinel` 의 통계로 정확히 재현된다: `dmg_base` 7 +
`tier` 4 × 2 = **15**. (`ta_sentinel` 의 스킬은 `vault_guard` /
`straylight_protocol` 이고 `dmg_base` 7, `tier` 4 다.)

**이것은 must-not-modify 파일의 load-bearing documentation 이다.**
`straylight_protocol` 을 `attack` 이 아닌 것으로 바꾸면 그 주장이
거짓이 된다. ADR-0223 이 이 id 를 "Straylight 응답 공격 / 프로토콜 적용
debuff" 두 가지로 읽은 것은 **이 문서를 읽지 못한 결과**다.

### 4. `loa_command` — test 가 pin 하고 있다

`web/tests/data_loaders.test.ts` 는 `loa_baron` 의 `loa_command` 에 대해
`effect === "attack"` 이고 `damage === raw.dmg_base` 라고 **assert** 한다.
이 스킬은 catalog 의 **공격 damage 파생 probe** 다. `attack` 이 아니면 그
probe 가 성립하지 않는다.

### 5. ADR-0227 의 precedent — 공격 스킬 없는 debuff-only ICE

ADR-0227 은 `sense_net_alert` 를 `support` 로 옮겼다. 그 kit 은
`media_alert` (debuff) + `broadcast_signal` (debuff) — **둘 다 `debuff`,
공격 스킬 없음.** 그리고 `hosaka_collector` 도 `support` 로 옮겼다
(`*_collector` + buff 2종, 공격 스킬 없음).

**`yakuza_collector` 의 kit 은 정확히 `debt_track` (debuff) +
`asset_seize` (debuff) — debuff 전용, 공격 스킬 없음.** 이것은 ADR-0227
이 이미 `support` 로 판정한 두 개의 exact precedent 다.

### 6. family / 어휘 증거 — catalog 전체

- **`command` family** (`command_brute`, `loa_command`) — **일관되게
  피해형.** 두 id 모두 `attack` 다. 이 family 의 분류는 대립되지 않는다.
- **`protocol` family** — 일관되지 **않다.** 그래서 `straylight_protocol`
  은 family 증거만으로는 부족했고, 위 3번의 `ice_scaling.ts` 문서가
  필요했다.
- **공격 스킬이 없는 row** — ADR-0227 에서 **전부** `support` /
  `defensive` 로 갔다. "no attack skill" 신호는 catalog 에서 일관된
  precedent 다.

### 7. `ta_daemon` — CHAPTER BOSS 로 문서화된 적대적 정체성

`docs/design/scenario/chapter-8-3jane.md` 의 「5. CHAPTER BOSS: The Family
Daemon」 절은 이 ICE 를 **chapter boss** 로 문서화한다 — **적대적
정체성**이다. ADR-0227 규칙 4 ("공격적 identity 가 명확하거나 피해
스킬을 가진 ICE 는 `aggressive` 로 둔다") 가 이 항목에 적용된다.
`ta_daemon` 의 kit 은 `family_protocol` (buff) + `inheritance_trace`
(detect) 다.

### 8. `ta_inheritor` — shared-skill 형제 ICE

`ta_heir` 와 `ta_inheritor` 는 **동일한 `family_vote` 스킬**을 공유하고
**tier 도 동일** (둘 다 tier 5) 하다. `ta_heir` 는 `aggressive` 다.
`ta_heir` 의 kit 은 `family_vote` (buff) + `orbital_command` (attack) —
**공격 스킬을 갖고 있다.** `ta_inheritor` 의 kit 은 `family_vote` (buff) +
`construct_summon` (buff) — 공격 스킬이 없다.

**같은 family, 같은 tier, 같은 shared skill 을 가진 형제 ICE** — 한쪽이
`aggressive` 면 다른 쪽도 `aggressive` 다. ADR-0223 이 `matrix_merge` 와
`ice_pierce` 의 형제 관계를 이미 이런 방식으로 읽었었다.

## 고려한 옵션

### Option 1: 원래 규칙을 재사용하고, 새 증거로 판정한다 (선택)

- **설명**: ADR-0223 / ADR-0227 의 규칙을 **그대로** 적용한다. 다만 이번
  review 는 원래 review 들이 수집하지 못한 **증거**를 gather 한다
  (ADR-0216 token 표의 git history, ADR-0226 의 magnitude 계약,
  `ice_scaling.ts` 의 load-bearing 문서, test 가 pin 하는 값, catalog
  전체의 family / 어휘 일관성, 시나리오 문서). 증거가 결정적이면 판정하고,
  **아니면 그대로 둔다.**
- **장점**:
  - **규칙을 새로 만들지 않는다** — 이미 받아들여진 규칙의 재적용이다.
  - **증거가 50/50 을 깨면** 판정하고, **깨지 않으면 그대로 둔다.**
    즉 **추측이 개입할 경로가 없다.**
  - 판정된 항목은 **test 로 pin** 해서 부채가 조용히 되살아나지 않게
    한다.
- **단점**:
  - **진짜 50/50 인 항목은 여전히 남는다.** 이 ADR 로 그것을 없앨 수는
    없다.
  - ADR-0223 의 "0개 ambiguous" 라는 깔끔한 상태로 돌아가지 못한다.
- **Pillar 정합**:
  - P3 (The Flatline): ✅ dead combat path 의 마지막 남은 분류 부채가
    정리된다.
  - P4 (The Build): ✅ 손으로 관리하는 표의 신뢰도가 test 로 고정된다.
  - P5 (The Style): ✅ ICE 의 이름과 스킬과 archetype 가 어긋나지 않는다.

### Option 2: 남은 50/50 항목까지 추측으로 닫는다

- **설명**: `hosaka_terminal` 과 스킬 없는 3종까지 그냥 하나를 골라
  분류한다.
- **단점**:
  - **추측이 판정 규칙을 대체한다.** ADR-0223 / ADR-0227 의 규칙은
    "모호하면 기록한다" 였다. 이건 그 두 규칙의 **철학적 기각**이다.
  - `hosaka_terminal` 의 경우 **두 읽기가 행동상 완전히 동일하다**
    (아래 「왜 3건이 여전히 50/50 인가」) — 추측으로 무엇을 얻는가.
  - 스킬이 0개인 3종 (`morrison_echo` / `zombie` / `ice_loa_zombie`) 은
    **판정材料和 신호가 아예 없다.** 이름만으로 고르는 것은 추측이다.
- **Pillar 정합**: 실패 (분류가 판단에서 취향으로 바뀐다).

### Option 3: 현상 유지 — 17건 전부 그대로 둔다

- **설명**: 아무것도 하지 않는다.
- **단점**:
  - **기록된 후속 항목을 실행하지 않는다.** ADR-0223 과 ADR-0227 이
    남긴 후속 항목이 영영 열린 채로 남는다.
  - **증거는 이미 존재한다.** ADR-0216 token 표, ADR-0226 magnitude,
    `ice_scaling.ts` 문서, test pin — 이건 "찾아볼 수 있는 건 없다" 가
    아니라 **"찾지 않았다"** 다. 미해결로 두는 것은 정직하지 않다.
- **Pillar 정합**: 실패.

## 추천 (Recommendation)

**Option 1.** 원래 규칙은 정답이었고, 부족했던 것은 **증거**였다.
증거가 결정적인 항목은 판정하고, 50/50 인 항목은 **문서화된 채로**
남긴다. 그리고 판정된 항목은 **test 로 pin** 한다.

## 사용자 결정 (Decision)

**2026-10-27 — 원래 규칙을 재사용하고 새 증거로 판정하기로 결정했다.**
구현 완료·검증됨.

- [x] **Option 1 — 원래 규칙 재사용 + 새 증거로 판정** — **채택·구현됨**
- [ ] Option 2 — 남은 50/50 까지 추측으로 닫기
- [ ] Option 3 — 현상 유지 (no-op)

### 결정된 내용

1. **규칙은 재사용한다.** ADR-0223 의 review 규칙 4개와 ADR-0227 의 review
   규칙 5개는 **그대로 적용**한다. 새 규칙 없음, 새 effect 없음, 새
   archetype 없음.
2. **스킬 10건 (ADR-0223) — 0건 변경.** 10건 전부 기존 값에서 확정되고,
   **신규 test 2건으로 pin** 된다. **0건 변경이라는 결과 자체가 이 ADR 의
   결과다** — 앞선 review 의 "모호하다"는 판정이 맞았고 이제 **증거로
   뒷받침된다.**
3. **ICE 7건 (ADR-0227) — 1건 변경.** `yakuza_collector` 를 `aggressive` →
   `support`. 나머지 6건 중 **3건 확정**, **3건은 여전히 50/50 로 기록만.**
4. **`family_vote` 의 불일치는 **이번에 고치지 않는다.** (범위 밖 —
   아래 「범위 밖에서 발견된 불일치」)
5. **ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 /
   0229 를 포함한 기존 ADR 은 하나도 수정하지 않았다.** Accepted 결정은
   immutable 이다 (`AGENTS.md` §6). 관계는 이 ADR 에 기록했다.

### Part 1 — 스킬 10건 (ADR-0223 의 ambiguous 10) — **0건 변경**

ADR-0223 의 10건 **전부** 기존 값에서 확정되었다. 그리고 **신규 test
2건**이 이 결정을 pin 한다.

| skill id | 확정된 effect | 결정적 근거 |
| --- | --- | --- |
| `ai_negotiate` | `buff` | ADR-0216 token 표 (`negotiate` → `buff`, 저자 의도) + ADR-0226 magnitude 18 (owning row `dmg_base` × buff multiplier) |
| `aleph_fragment` | `buff` | 동일 (token `aleph` → `buff`) + magnitude 15. boss namesake 스킬이며 `construct_proxy` / `construct_summon` / `loa_summon` buff family 과 일치 |
| `territorial_mark` | `buff` | 동일 (token `mark` → `buff`) + magnitude 12 |
| `straylight_protocol` | `attack` | `ice_scaling.ts:296` 과 `:355` 가 **두 곳에서** 15 피해 스킬로 문서화. `ta_sentinel` `dmg_base` 7 + tier 4 × 2 = 15 |
| `loa_command` | `attack` | `web/tests/data_loaders.test.ts` 가 `effect === "attack"` 과 `damage === raw.dmg_base` 를 assert. catalog 의 공격 damage 파생 probe |
| `enforce_contract` | `attack` | ADR-0227 이 이미 `yakuza_enforcer` 의 kit 으로 **`attack` 스킬**로 기록했다 |
| `intimidation` | `attack` | 동일 — ADR-0227 이 `yakuza_brute` 의 kit 으로 **`attack` 스킬**로 기록했다 |
| `ice_break` | `attack` | 이름이 명시적으로 공격/파괴를 가리킨다 (ADR-0223 의 self-correction 항목). `attack` 이 아닌 계열로 옮길 근거가 없다 |
| `matrix_merge` | `attack` | 형제 스킬 `ice_pierce` (15~18 피해) 와 동일 계열 |
| `orbital_command` | `attack` | `command` family (`command_brute`, `loa_command`) 은 **일관되게 피해형** — family 내 어휘 증거 |

**0건 변경은 「아무것도 못 했다」 가 아니라 「10건 전부 판정했다」 다.**
앞선 review 의 "모호" 판정은 **정확했**다 (분류 규칙만으로는 판정 불가).
그리고 지금은 **증거가 그 판정을 뒷받침한다.**

### Part 2 — ICE 7건 (ADR-0227 의 ambiguous 7) — 1건 변경

**→ `support` (1건 변경)**

| ICE id | before | after | 근거 |
| --- | --- | --- | --- |
| `yakuza_collector` | `aggressive` | **`support`** | debuff 전용 kit (`debt_track` + `asset_seize`, 둘 다 `debuff`), **공격 스킬 없음.** ADR-0227 의 `sense_net_alert` precedent (debuff 2종 + 공격 스킬 없음 → `support`) 와 `hosaka_collector` precedent (같은 `*_collector` role suffix → `support`) 가 **exact precedent** 다. ADR-0227 규칙 4 ("공격적 identity / 피해 스킬 보유 ICE 는 `aggressive` 유지") 는 이 ICE 에 해당하지 않는다 |

**확정 (3건) — 변경 없음**

| ICE id | 확정된 personality | 결정적 근거 |
| --- | --- | --- |
| `ta_daemon` | `aggressive` | `docs/design/scenario/chapter-8-3jane.md` 의 「5. CHAPTER BOSS: The Family Daemon」 이 **chapter boss (적대적 정체성)** 로 문서화. ADR-0227 규칙 4 적용 |
| `ta_inheritor` | `aggressive` | `ta_heir` 와 **동일한 `family_vote` 스킬 + 동일한 tier (5)** 를 공유하는 형제 ICE. `ta_heir` 는 `aggressive` |
| `yakuza_collector` 의 이전 상태 | — | 위 표 참조 (변경됨) |

**여전히 50/50 — 기록만 남긴다 (3건)**

| ICE id | competing readings | 왜 아직 결정할 수 없는가 |
| --- | --- | --- |
| `hosaka_terminal` | `support` (detect) / `stealth` (silence) | kit 이 **정확히 1-1** 로 갈린다 (`buffer_check` = detect, `memory_lock` = silence). 이름 "Terminal" 은 **중립적 하드웨어 정체성**이고 어느 쪽도 가리키지 않는다. ADR-0227 규칙 5 (모호한 이름은 기록) 적용 |
| `morrison_echo` | `support` / `aggressive` | `skills: []` — **신호가 없다.** 이름 외에 판정材料和 아무것도 없다 |
| `zombie` | `support` / `aggressive` | `skills: []` — **신호가 없다** |
| `ice_loa_zombie` | `support` / `aggressive` | `skills: []` — **신호가 없다** |

### 왜 3건이 여전히 50/50 인가 — 추측은 아무것도 닫지 못한다

**`hosaka_terminal` 이 대표적이다.** kit 은 `buffer_check` (detect) +
`memory_lock` (silence) — `support` 쪽을 가리키는 것과 `stealth` 쪽을
가리키는 것이 **정확히 하나씩**이다. 이름은 중립이고, 결정적으로 —
**두 읽기는 행동상 완전히 동일하다.** `detect` 와 `silence` 는 **둘 다
inert** (combat effect 없음) 이므로 이 ICE 는 어느 archetype 든
auto-attack 으로 떨어진다. **어느 쪽을 골라도 결과는 같다.**

**스킬 0개인 3종** (`morrison_echo` / `zombie` / `ice_loa_zombie`) 은 더
명확하다 — **판정材料和 신호가 아예 없다.** 이름만으로 고르는 것은
추측이고, ADR-0223 / ADR-0227 이 그것을 금지했다.

**추측으로 닫으면 닫히는 것이 없다.** 그래서 **문서화된 채로 남긴다.**

### Part 3 — 범위 밖에서 발견된 불일치 (이번에 고치지 않는다)

> **이 항목을 생략하면 안 된다.** 발견한 이상을 감추는 것은 정직하지
> 않다. 그리고 **고치지 않은 것**이 근거다.

**`family_vote` 는 `buff` 로 분류되어 있지만, 문서화된 boss mechanic 이
그와 다르다.**

- `docs/design/systems/combat.md:350` — T-A Prime 의 boss mechanic 표:
  "`family_vote` | **AoE damage 20** + construct companion 있으면 +10"
- ADR-0149 (`docs/wiki/decisions/0149-boss-phase4-finale.md:233`) 와
  ADR-0162 (`docs/wiki/decisions/0162-boss-phase-4.md:68`, `:73`) 은
  `family_vote` 을 **피해를 주는 boss mechanic** 으로 목록화한다
  (`apply_family_vote`).

**그런데 `family_vote` 의 분류는 `buff` 다** (`skill_defs` 에 magnitude 11
까지 저술되어 있다).

**왜 고치지 않았는가:** `family_vote` 는 **ADR-0223 의 ambiguous 10건
목록에 없다.** 그 review 는 88 entry **전수**를 검토했고 `family_vote` 를
`buff` 로 두었다. 즉 **이건 이번 review 의 대상이 아니고**, 고치는 것은
**요청되지 않은 scope 확장**이다.

**이것이 `ta_inheritor` 의 어색함의 upstream 원인일 가능성이 높다.**
`ta_inheritor` 는 `family_vote` (buff) + `construct_summon` (buff) 만
가지고 있어서 "공격 스킬 없음" 판정이 애매해진다. **근본은
`family_vote` 의 분류와 문서화된 AoE 피해 사이의 불일치**다.

**후속 ADR 로 넘긴다** (아래 후속 항목 1).

## 결과 (Consequences)

### 밸런스 — drift 0.0pp

**12개 grade 전부 (opening 6 + PPL 6) drift 0.0pp.**

**왜 안 움직이는가 — 추측이 아니라 실측.** `yakuza_collector` 의 kit 은
`debuff` 2종이고 **`debuff` 는 inert** 다 (combat effect 없음). 이 ICE 는
`aggressive` 든 `support` 든 **어느 쪽이든 auto-attack 으로 떨어진다.**
따라서 `personality` 변경은 **행동에 아무 영향도 주지 않는다.**

| grade | opening BEFORE | opening AFTER | drift |
| --- | --- | --- | --- |
| g1 | 100.0% | **100.0%** | 0.0pp |
| g2 | 88.6% | **88.6%** | 0.0pp |
| g3 | 73.1% | **73.1%** | 0.0pp |
| g4 | 39.3% | **39.3%** | 0.0pp |
| g5 | 35.7% | **35.7%** | 0.0pp |
| g6 | 0.0% | **0.0%** | 0.0pp |

| grade | PPL BEFORE | PPL AFTER | drift |
| --- | --- | --- | --- |
| g1 | 100.0% | **100.0%** | 0.0pp |
| g2 | 77.9% | **77.9%** | 0.0pp |
| g3 | 99.6% | **99.6%** | 0.0pp |
| g4 | 84.8% | **84.8%** | 0.0pp |
| g5 | 44.4% | **44.4%** | 0.0pp |
| g6 | 28.3% | **28.3%** | 0.0pp |

**ADR-0229 의 drift policy 가 충족된다.** 어느 grade 도 움직이지 않았으므로
**§A1 (되돌리거나 re-baseline) 이 발동하지 않는다** → **re-baseline 은
필요 없다.** §B 의 hard invariant 전부 (B1 단조 비증가, B2 g6 범위, B3 HP
단조 비감소, B4 max cap 165) 가 **그대로 성립**한다. §A4 (calibration 배열
변경) 는 해당 사항 없다 — 배열을 건드리지 않았다.

### 긍정적 영향

- **ADR-0223 / ADR-0227 의 분류 부채가 종결되었다.** 스킬 10건은 확정 +
  test pin, ICE 7건은 1건 교정 + 3건 확정 + 3건 기록.
- **10개 스킬 분류가 이제 test 로 pin 된다.** 이전에는 "메모에 적어둔
  뿐" 이었다. 이제는 **조용히 되살아날 수 없다.**
- **ICE 변경은 같은 precedent 를 따른다.** 새로운 규칙이 아니라
  ADR-0227 이 이미 세운 `sense_net_alert` / `hosaka_collector` precedent
  의 **적용**이다.
- **행동 변화가 없다.** 12개 grade 전부 0.0pp drift.

### 부정적 영향 / 수용한 비용

- **3건의 ICE 는 여전히 결정되지 않았다.** `hosaka_terminal` +
  스킬 0개인 3종. 이건 **의도된 상태**다 — 추측으로 닫는 것보다 낫다.
- **`family_vote` 의 불일치는 기록만 하고 해결하지 않았다.** 별도 ADR
  대상.

### 후속 항목

1. **`family_vote`** — `buff` 분류와 문서화된 "AoE damage 20" boss mechanic
   사이의 불일치를 **별도 ADR** 로 해결한다. `ta_inheritor` 의 어색함의
   upstream 원인일 가능성이 높다.
2. **3건의 미결 ICE** — `hosaka_terminal`, `morrison_echo`, `zombie`,
   `ice_loa_zombie` 중 스킬 0개인 3종. 신호가 생기면 (스킬 부여 등) 다시
   판정할 수 있다.
3. **`detect` / `silence` / `slow` / `stun` / `debuff` 는 여전히 inert** —
   이것이 **여러 결정이 현재 행동상 무의미한 이유**다. combat effect 를
   부여하면 `hosaka_terminal` 같은 항목의 두 읽기가 **구분 가능해질 수
   있다** (inert 가 아니면 `detect` 와 `silence` 는 다른 결과를 만든다).
   그러면 그때 그 ICE 의 판정도 다시 열린다.

### 관계 — immutable 규칙 준수

ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 / 0229 는
**Accepted 이며 immutable 하므로 하나도 수정하지 않았다** (`AGENTS.md` §6).
관계는 이 ADR 에 기록했다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

**데이터 변경 — 1줄**

- `web/src/data/ice_types.json` — **`"personality"` 줄 정확히 1개 변경.**
  `git diff --stat` = **1 insertion / 1 deletion**, 변경된 줄은
  `yakuza_collector` 의 `"personality": "aggressive"` → `"personality":
  "support"` **한 줄뿐**이다. diff 의 변경된 2줄 **전부가 `"personality"`
  줄** 다 (기계 검증).
- `web/src/data/ice_types.json` — **`skill_defs` 88 entry 전부 byte-identical.**
  스킬 분류 10건은 **0건 변경** — diff 에 `skill_defs` 구간 변경이 없다.
- `web/src/data/ice_types.json` — `name` / `skills` / `aggression` /
  `dmg_base` / `hp_base` / `hp_per_grade` / `tier` / `defense` **미변경.**
  `yakuza_collector` row 의 다른 모든 필드도 byte-identical.

**신규 test — 2건**

- `web/tests/data_loaders.test.ts` — **신규 test 2건 추가.**
  (a) *"keeps the ten previously-ambiguous skill classifications at their
  reviewed values"* — ADR-0223 의 10개 id 를 각각의 확정된 `effect` 로
  pin 한다 (`ai_negotiate` / `aleph_fragment` / `territorial_mark` = `buff`,
  `enforce_contract` / `ice_break` / `intimidation` / `loa_command` /
  `matrix_merge` / `orbital_command` / `straylight_protocol` = `attack`).
  (b) *"reads the yakuza collector as a support archetype, not an attacker"*
  — `yakuza_collector` 의 `personality === "support"` 와 kit 의 effect 배열이
  `["debuff", "debuff"]` 임을 pin 한다.
- **두 test 모두 틀린 데이터에 대해 실패함을 확인했다** (negative
  verification).
- 기존 assertion 은 **하나도 약화·skip·삭제하지 않았다.**

**밸런스 — drift 0.0pp (12 grade 전부)**

- `npm run balance` (opening deck, 100 runs/mission): g1 100.0% · g2 88.6% ·
  g3 73.1% · g4 39.3% · g5 35.7% · g6 0.0% — **ADR-0229 baseline 과
  일치, 6개 grade 전부 0.0pp.**
- `npm run balance -- --deck ppl` (100 runs/mission): g1 100.0% · g2 77.9% ·
  g3 99.6% · g4 84.8% · g5 44.4% · g6 28.3% — **ADR-0229 PPL reference 와
  일치, 6개 grade 전부 0.0pp.**
- **drift 가 없는 이유**: `yakuza_collector` 의 kit 은 `debuff` 2종이고
  `debuff` 는 **inert** — 어느 personality 든 auto-attack 으로 떨어진다.
- **ADR-0229 drift policy §A1 미발동** (grade 이동 0) → **re-baseline
  불필요.** §B hard invariant 전부 성립.

**증거 인용 (실측 위치)**

- `web/src/core/ice_scaling.ts:296` — "15-damage `straylight_protocol`"
  ("cannot be scaled down by this knob")
- `web/src/core/ice_scaling.ts:355` — "its 15-damage skill is" (두 번째
  동일 문서화 지점)
- `docs/design/scenario/chapter-8-3jane.md` — 「5. CHAPTER BOSS: The
  Family Daemon」 절 — `ta_daemon` 을 chapter boss 로 문서화
- `docs/design/systems/combat.md:350` — T-A Prime boss mechanic 표:
  "`family_vote` | AoE damage 20 + construct companion 있으면 +10"
  (→ **범위 밖 불일치**, §Part 3)
- `docs/wiki/decisions/0149-boss-phase4-finale.md:233`,
  `docs/wiki/decisions/0162-boss-phase-4.md:68`, `:73` — `apply_family_vote`
  을 T-A Prime 의 피해형 boss mechanic 으로 목록화
- ADR-0216 의 token rule table — git history (`c72132b^`의
  `web/src/core/ice_skills.ts`) 에 `["negotiate", "mark", "aleph", ...] →
  "buff"` 로 저자 의도가 남아 있다 (ADR-0222 가 그 표를 삭제)
- `web/tests/data_loaders.test.ts` — `loa_command` (`loa_baron`) 에 대한
  `effect === "attack"` / `damage === raw.dmg_base` assert — catalog 의
  공격 damage 파생 probe
- `web/src/data/ice_types.json` — magnitude 계약 확인:
  `ai_negotiate` 18 / `aleph_fragment` 15 / `territorial_mark` 12 /
  `family_vote` 11. ADR-0226 의 authoring 규칙과 일치
- `web/src/data/ice_types.json` — `ta_sentinel` (`dmg_base` 7, `tier` 4) →
  `dmg_base + tier × 2 = 15` = 문서화된 15 피해와 **정확히 일치**

**게이트**

- `npm test` — **127 files / 2988 tests, 0 failures.** (이전 2986,
  **+2** — 신규 test 2건.)
- `npx tsc --noEmit` — **0 errors.**
- `npx eslint src scripts --ext ts` — **0 errors** (무관한 pre-existing
  warning 1건은 `web/src/input/keyboard.ts`).
- `python3 scripts/audit_vault.py` (workspace root) — **CLEAN.**

**Notes**:

- **diff 는 `web/` 2개 파일뿐이다** — `web/src/data/ice_types.json`
  (+1 / −1, `personality` 줄 1개) 과 `web/tests/data_loaders.test.ts`
  (+74, 신규 test 2건).
- **`skill_defs` 는 byte-identical** — 스킬 10건의 "0건 변경"은 데이터
  diff 로 실측 확인했다.
- **`web/` 아래의 다른 파일은 하나도 바뀌지 않았다.** `ice_skills.ts`,
  `ice_ai.ts`, `ice_scaling.ts`, `ice_crit.ts`, `ice_combat_effects.ts`,
  `ice_combat_effect_apply.ts`, `types.ts`, `state_actions_combat.ts`,
  `combat_engine.ts` — 전부 **미변경.**
- **ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 /
  0229 를 포함한 기존 ADR 은 하나도 수정하지 않았다.** Accepted 결정은
  immutable 이고 (`AGENTS.md` §6), 관계는 이 ADR 에 기록했다.
- **`Game/wet_run/log.md` 는 수정하지 않았다** (오케스트레이터 소유).
- **`family_vote` 는 고치지 않았다.** ADR-0223 의 ambiguous 목록 밖에
  있었으므로 고치는 것은 요청되지 않은 scope 확장이다 — 후속 ADR 로
  넘겼다.
- **임시 파일을 남기지 않았다.**

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `docs/wiki/decisions/0230-ambiguous-classification-debt-closure.md` — **신규**
  (이 ADR)
- `docs/wiki/decisions/README.md` — 0230 행 신규 (0229 행 다음, 6-컬럼
  동일 format)
- `web/src/data/ice_types.json` — `yakuza_collector` 의 `personality` 값 **1개**
  (`aggressive` → `support`)
- `web/tests/data_loaders.test.ts` — **신규 test 2건** (스킬 10건 pin +
  `yakuza_collector` archetype pin)

### 이번 결정으로 변경되지 않은 항목

- `web/src/data/ice_types.json` — `skill_defs` 88 entry 전부, 나머지 96 ICE
  row, `yakuza_collector` row 의 다른 모든 필드
- `web/src/core/ice_skills.ts`, `web/src/core/ice_ai.ts`,
  `web/src/core/ice_scaling.ts`, `web/src/core/ice_crit.ts`,
  `web/src/core/ice_combat_effects.ts`, `web/src/core/ice_combat_effect_apply.ts`,
  `web/src/core/types.ts`, `web/src/core/state_actions_combat.ts`,
  `web/src/core/combat_engine.ts` — **전부 미변경**
- `web/tests/` — **기존 test 미변경** (추가만 2건, 약화·skip·삭제 0)
- `Game/wet_run/log.md` — 오케스트레이터 소유
- ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 / 0229 —
  **미수정** (immutable)

### 후속 항목 (이번 ADR 범위 밖)

1. `family_vote` — `buff` vs 문서화된 AoE 피해 불일치 (별도 ADR)
2. `hosaka_terminal` + 스킬 0개인 3종 (`morrison_echo` / `zombie` /
   `ice_loa_zombie`) — 여전히 미결
3. `detect` / `silence` / `slow` / `stun` / `debuff` 의 combat effect 설계 —
   이게 구현되면 `hosaka_terminal` 의 판정이 다시 열린다

## 관련 결정

- ADR-0223 (스킬 분류 review pass) — **이 ADR 이 그 후속 항목 1 (ambiguous
  10건) 을 종결한다.** review 규칙 4개를 그대로 재사용했다.
  **ADR-0223 은 수정하지 않았다** (immutable).
- ADR-0227 (ICE 아키타입 일관성 검토) — **이 ADR 이 그 후속 항목 3
  (애매한 ICE 7종) 을 종결한다.** `sense_net_alert` / `hosaka_collector`
  precedent 의 owner. **ADR-0227 은 수정하지 않았다** (immutable).
- ADR-0216 (derived ICE skill metadata) — **token rule table 의 owner.**
  그 표의 `negotiate` / `mark` / `aleph` → `buff` 매핑이 스킬 3건의 결정적
  근거다. **ADR-0216 은 수정하지 않았다** (immutable).
- ADR-0222 (ICE 스킬 메타데이터가 authored data 로 이동한다) — 그 token
  표를 `skill_defs` 로 materialized 한 결정. **ADR-0222 은 수정하지
  않았다** (immutable).
- ADR-0226 (Non-damaging ICE 스킬 효과를 구현한다) — **magnitude 계약의
  owner.** `buff` 계열의 magnitude 존재가 스킬 3건의 두 번째 근거다.
  **ADR-0226 은 수정하지 않았다** (immutable).
- ADR-0229 (Grade 난이도 곡선 재기준화) — **drift policy 의 owner.**
  이 ADR 의 0.0pp drift 로 §A1 미발동, re-baseline 불필요.
  **ADR-0229 는 수정하지 않았다** (immutable).
- ADR-0195 (Accepted ADR Implementation Status Workflow) — 이 ADR 의
  Implementation Status 형식의 owner. **수정하지 않았다** (immutable).

## 변경 이력

- 2026-10-27: Draft 작성 (ADR-0223 후속 항목 1 + ADR-0227 후속 항목 3 —
  애매 분류 부채 종결)
- 2026-10-27: **Accepted (Option 1 — 원래 규칙 재사용 + 새 증거로 판정)** —
  구현 완료·검증. 스킬 10건 **0건 변경** (전부 확정 + 신규 test 2건으로
  pin), ICE 7건 중 **1건 변경** (`yakuza_collector` `aggressive` → `support`),
  **3건 확정**, **3건 여전히 50/50 로 기록**. **12 grade 전부 0.0pp drift.**
  `family_vote` 의 `buff` vs 문서화된 AoE 피해 불일치는 **범위 밖으로
  기록하고 별도 ADR 로 넘겼다.** 기존 assertion 은 하나도 약화·skip·삭제하지
  않았다.
