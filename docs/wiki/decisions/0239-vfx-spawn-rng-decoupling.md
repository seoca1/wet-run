# ADR-0239: VFX spawn 의 RNG 결합 해소 — 결정적 id 전환 + 1회 재기준화

**상태**: Draft
**날짜**: 2026-10-31
**결정자**: 사용자 (프로젝트 오너) — **결정 대기**
**우선순위**: P2 (The Flatline — 밸런스 프로세스, ADR-0229 §A1 접점)
**관련**: [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md) · [ADR-0231 — Combat-feel top-3](./0231-combat-feel-top3-vfx-log-raf.md) · [ADR-0232 — Combat-feel tier 2](./0232-combat-feel-tier2-shake-damage-sfx.md) · [ADR-0238 — 밸런스·입력 결정 요청](./0238-balance-and-input-decision-request.md) · [UI 개편 트리아지 (2026-10-31)](../../design/ui-overhaul-triage-2026-10-31.md)

> **이것은 결정 요청(Draft) 이다.** 아무것도 구현하지 않았다. 전환 자체는 2개
> 함수 수정이지만, **밸런스 기준선을 옮기는 1회 재기준화**가 따라오므로 그 결정은
> 오너의 몫이다 (ADR-0229 §A1).
>
> **이 ADR 은 게임플레이 RNG 를 건드리지 않는다.** 바꾸는 것은 **표시 계층의
> VFX id** 뿐이다. crit roll · loot roll · 적 스킬 선택 · death cycle 은 밸런스
> 그 자체이므로 불변이다.

## 컨텍스트 (Context)

### 문제 — 표시 전용 변경이 밸런스를 2~3pp 움직인다 (실측)

ADR-0238 의 P8 을 준비하면서 반증 실험을 했다. `critical_hit` spawn **한 줄**을
`import_vfx_ms` → `import_vfx_deterministic` 으로 바꾸고 `npm run balance` 를
돌린 결과 (원복 완료, 트리 clean):

| grade | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- |
| opening 기준선 | 100.0 | 88.6 | 73.1 | 39.3 | 35.7 | 0.0 |
| opening + 변경 | 100.0 | 88.4 | **71.1** | **40.4** | **36.2** | 0.0 |
| opening drift (pp) | 0.0 | −0.2 | **−2.0** | **+1.1** | **+0.5** | 0.0 |
| PPL drift (pp) | 0.0 | +1.2 | −0.7 | +0.5 | 0.0 | **−3.0** |

표시 계층만 바꿨는데 **두 덱 모두** 움직였다. 원인은 단순하다 — 하네스가
`Math.random` 을 PRNG 로 시드하므로, VFX id 를 뽑는 **draw 를 하나 늘리거나 줄이면
그 뒤의 모든 crit · proc · 적 스킬 판정이 밀린다.**

### 현행 정책과 그 구멍

`core/state/state_helpers.ts:92-105` 의 docstring 이 이미 이 결합을 알고 있다:

> "The balance harness seeds `Math.random` with a PRNG, so every draw shifts the
> seeded crit / proc / skill rolls and moves the ADR-0229 grade curve.
> `import_vfx` draws its id from `Math.random`, which is fine for the spawn sites
> that already existed (their draw count is baked into the recorded baseline) but
> NOT for newly added ones … New spawn sites use this helper so they stay
> RNG-neutral."

즉 현행 규칙은 **"새 spawn 은 `import_vfx_deterministic` 을 쓴다"** 하나뿐이다.
**기존 spawn 을 고치는 경우**에 대한 규칙이 없다 — 그 구멍이 위 실측으로 드러났다.
ADR-0231·0232 는 이 문제를 매번 **수작업 "RNG draw count before/after 일치" 확인**
으로 막아 왔다 (그 ADR 들의 기록에 남아 있다). 사람이 매번 확인해야 하는 규칙은
언젠가 빠진다.

### 수정 표면은 13곳이 아니라 **2개 함수**다

HEAD `f0530d0` 실측 — 호출 지점은 3개 헬퍼로 나뉜다:

| 헬퍼 | 정의 | 호출 지점 수 | draw 소비 |
| --- | --- | --- | --- |
| `import_vfx` | `state_helpers.ts:23` | **10** | `Math.random` (id) |
| `import_vfx_ms` | `state_helpers.ts:47` | **3** | `Math.random` (id) |
| `import_vfx_deterministic` | `state_helpers.ts:107` | 12 | **0** (content hash id) |

비결정적 spawn 13곳은 **모두 `import_vfx` / `import_vfx_ms` 두 함수를 지난다.**
따라서 그 두 함수의 id 를 결정적으로 바꾸면 **13곳이 한 번에** 중립화되고,
호출 지점은 손댈 필요가 없다. `import_vfx_deterministic` 의 id 스킴
(`deterministicVfxId(kind, payload, payloadNum, duration)`) 과 그 안전성 근거는
이미 그 docstring 에 적혀 있다:

> "The id is derived from the spawn's own content … Two spawns with identical
> content therefore share an id; nothing reads `CombatVfxInstance.id` for logic
> (it is an identity key only) and rendering composites by array order, not by id."

### RNG 소비 지도 (HEAD `f0530d0`, 전수 확인)

| 소비처 | 위치 | 성격 | 이 ADR 범위 |
| --- | --- | --- | --- |
| `import_vfx` id | `core/state/state_helpers.ts:23` | 표시 | ✅ **범위** |
| `import_vfx_ms` id | `core/state/state_helpers.ts:47` | 표시 | ✅ **범위** |
| 상태 메시지 fluff 판정 (`rng() < 0.2`) | `core/status.ts:253`·`:255` | 표시 — **단 전투 reducer 경로에서 소비됨** (`state_actions_programs.ts` 가 `../status` 를 import) | ⚠️ **범위 후보** |
| 그래픽노블 씬 선택 | `core/graphic_novel/graphic_novel_loaders.ts:112` · `graphic_novel_player.ts:42` | 표시 (하네스 밖) | 범위 밖 |
| 데미지 · crit roll | `core/combat/state_actions_programs.ts:99` | **게임플레이** | ❌ 불변 |
| 적 스킬 선택 · ICE crit roll | `core/combat/state_actions_combat.ts:234`·`:258`·`:333`, `core/combat/ice_crit.ts` | **게임플레이** | ❌ 불변 |
| loot roll | `core/state/loot.ts:30` | **게임플레이** | ❌ 불변 |
| death / restart | `core/state/death_cycle.ts:45` | **게임플레이** | ❌ 불변 |

주석·문서에서만 `Math.random` 을 언급하는 파일(`renderer/screen_shake.ts`,
`core/state/touch_feedback.ts`, `core/combat/combat_entry_vfx.ts`,
`core/dungeon/matrix.ts`, `core/state/state_actions_phases.ts`)은 **draw 를 소비하지
않는다** — 이미 그렇게 정리돼 있다.

### 이 ADR 의 질문

**표시 계층의 VFX id draw 를 지금 한 번 정리해 "앞으로 표시 변경은 밸런스를
건드리지 않는다" 를 참으로 만들 것인가 — 아니면 지금처럼 매 변경마다 ADR-0229 §A1
판정을 치를 것인가?** 정리하면 **1회 재기준화**가 필요하다 (그 대가를 지불해야
한다는 것이 이 결정의 핵심).

## 고려한 옵션

### Option A — 현상 유지 + 현행 규칙 명문화

`import_vfx`/`import_vfx_ms` 를 그대로 두고, "기존 spawn 을 고치면 draw 수가 변해
밸런스가 움직인다" 를 규칙으로 명문화한다.

| 장점 | 단점 / 위험 |
| --- | --- |
| 변경 0 · 재기준화 0 | 표시 개선마다 2~3pp 이동을 §A1 로 판정해야 한다 |
| 기준선 유지 | ADR-0238 의 P2·P8·X5·X8 이 전부 이 세금을 낸다 |
| — | draw 수 정합을 **사람이** 확인해야 한다 (ADR-0231/0232 방식) — 반복 실수 위험 |

### Option B — 두 헬퍼를 결정적 id 로 전환 + **1회 재기준화** (채택 추천)

`import_vfx` / `import_vfx_ms` 의 id 를 content hash 로 바꾼다 (13개 호출 지점은
무변경). 그 결과 스트림이 **한 번 크게** 밀리므로, ADR-0229 §A1 프로세스로
6등급을 **재측정하고 새 기준선으로 기록**한다. 이후에는 어떤 표시 변경도 draw 를
소비하지 않는다.

| 장점 | 단점 / 위험 |
| --- | --- |
| 표시 계층이 **영구히** RNG 중립 → 이후 표시 변경은 진짜 0.0pp | **1회 재기준화**: 6등급 곡선이 움직이고 새 기준선을 승인해야 한다 |
| 수정은 **2개 함수** (13개 호출 지점 무변경) | id 충돌 의미가 전체 spawn 으로 확대 (동일 내용 2건이 같은 id) |
| ADR-0238 의 VFX 항목들이 세금 없이 진행 가능 | 재기준화 후 ADR-0229 문서·기록 갱신 필요 |
| 사람이 draw 수를 대조할 필요가 없어진다 | |

### Option C — draw 수를 밸런스 계약의 일부로 선언

결합을 없애지 않고 **인정**한다: "VFX spawn 의 draw 수는 밸런스 입력의 일부이며,
변경은 항상 밸런스 변경이다." 문서화만 한다.

| 장점 | 단점 / 위험 |
| --- | --- |
| 정직하고 변경 0 | 결합을 영구 고정 — 표시 작업이 계속 밸런스 작업이 된다 |
| — | 근본 원인이 남아 다음 사람도 같은 함정에 빠진다 |

### Option D — 별도 ADR 로 분리

이미 별도 문서다. 분할할 대상이 없다.

### 비교표

| 축 | A 현상 유지 | **B 결정적 id + 재기준화** | C 계약화 |
| --- | --- | --- | --- |
| 코드 변경 | 0 | **2 함수** | 0 |
| 1회 재기준화 | 불필요 | **필요** | 불필요 |
| 이후 표시 변경 비용 | 매번 §A1 판정 (2~3pp) | **0.0pp** | 매번 §A1 판정 (영구) |
| ADR-0238 VFX 항목 | 세금 발생 | **세금 없음** | 세금 발생 |
| draw 수 수동 대조 | 필요 | **불필요** | 필요 |
| 되돌리기 난이도 | — | 높음 (기준선이 바뀜) | — |

## 추천 (Recommendation)

**Option B.** 근거:

1. **세금이 실재하고 반복된다** — 표시 1줄 변경이 g3 −2.0pp · PPL g6 −3.0pp 를
   움직였다. ADR-0238 의 VFX 관련 항목(P2 잔여 3종 · P8 · X5 · X8)이 모두 같은
   세금을 낸다.
2. **수정이 작다** — 13개 호출 지점이 아니라 **2개 함수**이고, id 스킴과 그 안전성
   근거(content hash · id 는 logic 에 안 읽히고 렌더는 배열 순서)는
   `import_vfx_deterministic` 에 이미 구현·문서화돼 있다.
3. **재기준화는 이미 해본 절차다** — ADR-0229 가 §A1/§B/§C/§D 정책과 함께
   baseline 을 다시 세운 선례가 있다.

**단, 순서를 권한다**: 이 ADR 을 먼저 처리하고 **그 뒤에** ADR-0238 의 VFX 항목을
구현한다. 반대로 하면 그 항목들이 재기준화 대상이 되어 두 번 일하게 된다.

**부수 권고 (강하게)**: 전환과 함께 **RNG draw 수 불변식을 테스트로 고정**한다.
ADR-0231·0232 는 "draw count before/after 일치" 를 **수작업으로** 확인했고, 그래서
이번 같은 구멍이 남았다. 하네스가 시드 고정 전후의 draw 수(또는 첫 N draw 의 해시)를
기록·단언하도록 만들면, 이 부류의 위반이 **기계적으로** 잡힌다.

## 사용자 결정 (Decision)

- [ ] **Option A** — 현상 유지 + 규칙 명문화 only
- [ ] **Option B** — 결정적 id 전환 + 1회 재기준화 **(추천)**
- [ ] **Option C** — draw 수를 밸런스 계약으로 선언
- [ ] 범위에 `core/status.ts` 의 fluff RNG(`:253`)도 포함할지
- [ ] 부수 권고(RNG draw 수 불변식 테스트)를 같은 ADR 에 포함할지, 분리할지
- [ ] ADR-0238 의 VFX 항목보다 **먼저** 처리하는 순서에 동의하는지

## 결과 (Consequences)

**결정 후 작성.** (Option B 기준으로 예상되는 결과: 6등급 곡선이 1회 이동하고 새
기준선이 ADR-0229 기록을 대체한다. 그 이후 표시 계층 변경은 0.0pp 를 기본값으로
갖는다.)

## Implementation Status (2026-10-31)

**Status**: ❌ Not started

**Evidence**:
- `core/state/state_helpers.ts:23` — `import_vfx` 의 id draw (`Math.random`)
- `core/state/state_helpers.ts:47` — `import_vfx_ms` 의 id draw
- `core/state/state_helpers.ts:107` — `import_vfx_deterministic` (content hash id, draw 0)
- `core/state/state_helpers.ts:92-105` — 현행 정책 docstring ("새 spawn" 규칙만 존재)
- `core/status.ts:253`·`:255` — fluff 판정 RNG (`rng() < 0.2`, 전투 경로에서 소비)
- `core/combat/state_actions_programs.ts:99`, `state_actions_combat.ts:234`·`:258`·`:333`,
  `loot.ts:30`, `death_cycle.ts:45` — **게임플레이 RNG (불변)**

**Notes**: 이 ADR 은 아무것도 구현하지 않았다. 아래 실측 2건은 **ADR-0238 작업 중
일회성으로 수행하고 원복**한 것이며, 저장소에는 흔적이 없다 (`git diff HEAD` 비어
있음 · 백업 `/tmp/p8-backup2-state_actions_programs.ts`).

## Open questions

- **(a) id 스킴** — content hash 로 충분한가? `deterministicVfxId` 를 그대로 두
  헬퍼에 적용할지, 호출 순서 기반 counter 를 섞을지 (동일 내용 2건이 같은 id 를
  갖는 의미가 13개 지점 모두에서 안전한지 확인 필요).
- **(b) fluff RNG** — `core/status.ts:253` 의 20% 판정도 결정적이어야 하는가,
  주입된 시드 rng 를 쓰게 할 것인가? 표시이지만 전투 경로에서 소비된다.
- **(c) 새 기준선의 지위** — 재기준화한 곡선을 ADR-0229 의 새 baseline 으로
  기록하는가(그러면 ADR-0229 의 기존 곡선 표기가 superseded 됨)? 아니면 별도
  baseline 문서를 두는가?
- **(d) 불변식 테스트** — draw 수/해시를 어떻게 고정할지, CI 에서 강제할지.
- **(e) 순서** — ADR-0238 의 VFX 항목(P2 잔여 · P8 · X5 · X8)을 이 ADR **뒤**로
  미룰지.
- **(f) 되돌리기 정책** — 전환 후 문제가 생기면 기준선이 이미 바뀌어 "원복"이
  자명하지 않다. 롤백 기준을 정해 둘지.

## 영향 받는 항목

### 이 결정 요청으로 변경된 항목

- `docs/wiki/decisions/0239-vfx-spawn-rng-decoupling.md` — **신규** (이 ADR)

### 결정 · 구현 시 변경될 수 있는 항목 (예정 — 결정에 따라)

- `core/state/state_helpers.ts` — `import_vfx` / `import_vfx_ms` 의 id 를 결정적으로
- (선택) `core/status.ts` — fluff RNG 를 결정적/주입식으로
- `web/tests/**` — RNG draw 수 불변식 테스트 (부수 권고 채택 시)
- ADR-0229 의 baseline 기록 (재기준화 시)

### 변경되지 않는 항목

- `core/combat/state_actions_programs.ts:99` · `state_actions_combat.ts` ·
  `ice_crit.ts` · `loot.ts` · `death_cycle.ts` — **게임플레이 RNG, 불변**
- `GameState` · `SaveSlot` · `web/src/data/**` · `PALETTE` / `PALETTE_VARIANTS`
- 렌더러 (`renderer/**`) — id 는 logic 에 읽히지 않는다
- Accepted ADR 본문 (0229 포함) — 변경 필요 시 이 ADR 이 supersede 방식을 기록

## 관련 결정

- ADR-0229 — drift policy · §A1/§A2/§A3/§B/§C (이 ADR 의 절차 근거)
- ADR-0231 · ADR-0232 — RNG non-neutrality 최초 발견과 pivot (`import_vfx_deterministic`)
- ADR-0238 — P8 실측(이 ADR 의 문제 제기 근거) · P2/P8/X5/X8 이 이 ADR 에 의존

## 변경 이력

- 2026-10-31: Draft 작성 — 문제 실측(opening · PPL 양 덱), RNG 소비 지도, 옵션 4종
  (실질 3종), Option B 추천, 불변식 테스트 부수 권고, 열린 질문 6건. **구현 없음.**
