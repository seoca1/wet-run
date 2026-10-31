# ADR-0239: VFX spawn 의 RNG 결합 해소 — 결정적 id 전환 + 1회 재기준화

**상태**: Accepted
**날짜**: 2026-10-31
**결정자**: 사용자 (프로젝트 오너) — 2026-10-31 결정
**우선순위**: P2 (The Flatline — 밸런스 프로세스, ADR-0229 §A1 접점)
**관련**: [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md) · [ADR-0231 — Combat-feel top-3](./0231-combat-feel-top3-vfx-log-raf.md) · [ADR-0232 — Combat-feel tier 2](./0232-combat-feel-tier2-shake-damage-sfx.md) · [ADR-0238 — 밸런스·입력 결정 요청](./0238-balance-and-input-decision-request.md) · [UI 개편 트리아지 (2026-10-31)](../../design/ui-overhaul-triage-2026-10-31.md)

> **2026-10-31 프로젝트 오너가 Option B 를 채택했다** (§사용자 결정 참조). 이
> ADR 은 이제 **Accepted** 이고, 구현은 아직 시작하지 않았다 (§Implementation
> Status).
>
> **이 ADR 은 게임플레이 RNG 를 건드리지 않는다.** 바꾸는 것은 **표시 계층의 VFX
> id** 와 상태 메시지 fluff 판정뿐이다. crit roll · loot roll · 적 스킬 선택 ·
> death cycle 은 밸런스 그 자체이므로 불변이다.

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
| 상태 proc 판정 (`rng() < 0.2`) | `core/status.ts:251`·`:255` | **게임플레이** — 호출자가 그 결과로 `burn`(2뎀×3턴)·`slow`(−30%댐·2턴)을 **실제 적용**한다 (`state_actions_programs.ts:145`·`:154`). `_kind` 인자는 **무시**됨 | ❌ **범위 밖 (2026-10-31 정정)** |
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

### WF8 난이도 곡선 채점 (2026-10-31, **advisory**)

Jev WF8 (`jev-difficulty` 루브릭, 0..5) 으로 현재 곡선과 **분리 프록시 곡선**을
채점했다. Jev 는 타입화된 점수만 반환하고 근거 텍스트는 없다. 4회 호출, 보정
primary 전용(`JEV_LOCAL_FALLBACK=0`), 감사 로그는 `raw/` 대신 `/tmp/jev-calls/`.

| 곡선 | score | confidence | L0..L4 분포 |
| --- | --- | --- | --- |
| 현재 opening | **1.88** | 0.23 (낮음) | .02/.52/.08/.32/.06 |
| 현재 PPL | **0.93** | **0.86** | .12/.85/.01/.02/0 |
| 분리 프록시 opening | **1.76** | 0.34 (낮음) | .02/.58/.07/.29/.04 |
| 분리 프록시 PPL | **0.94** | **0.90** | .10/.89/0/.01/0 |

**해석 (증거 가치)**: 분리가 곡선 **형태 품질을 떨어뜨리지 않는다** — opening
1.88 → 1.76, PPL 0.93 → **0.94**. 특히 **PPL 은 두 호출 모두 고신뢰**(0.86 / 0.90)
이므로 그 비교가 더 강한 신호다. 즉 Option B 의 재기준화는 **품질 회귀가 아니라
장부 변경**이다 — 추천에 힘을 싣는다.

**한계 (반드시 함께 읽을 것)**:
- WF8 은 ground truth 가 없어 **절대 등급이 아니라 상대 추세**로만 쓴다 (gold-set
  Spearman ρ = 0.943 은 순서 검증이지 절대값 검증이 아니다).
- '분리 프록시'는 **spawn 사이트 1곳만** `Math.random` 에서 옮긴 곡선이다 — 실제
  전환(13곳 → 2개 함수)은 스트림을 **더 크게** 민다. 따라서 이 값은 실제 전환 후
  곡선의 **하한 근사**이고, 곡선형은 지표일 뿐 단정이 아니다.
- opening 곡선은 **저신뢰**(0.23 / 0.34) → 규정상 "이것만으로 행동하지 말 것".
- PPL 참조 곡선은 g2 77.9 → g3 99.6 으로 **비단조**다. 루브릭 1순위 기준이 "비단조
  = 최악 결함"이므로 PPL 이 opening 보다 낮게 나온 것은 **구성상 당연**하고, 이
  ADR 이 만든 성질이 아니다 (ADR-0229 의 기존 참조 곡선).

## 사용자 결정 (Decision)

**2026-10-31, 프로젝트 오너 직접 결정** (Jev 는 결정 보조로만 사용 — WF8 곡선
증거 제공, 결정 자체는 오너).

- [x] **Option B 채택** — 결정적 id 전환 + 1회 재기준화
- [ ] ~~Option A~~ — 현상 유지 (미채택)
- [ ] ~~Option C~~ — draw 수를 밸런스 계약으로 선언 (미채택)
- [x] 범위에 `core/status.ts` 의 fluff RNG(`:253`) **포함**
- [x] RNG draw 수 불변식 테스트를 **같은 ADR 에 포함**
- [x] ADR-0238 의 VFX 항목보다 **먼저** 처리

## 결과 (Consequences)

**Option B 기준.** 아직 구현 전이므로, 아래는 결정이 확정한 것과 예상이다.

### 결정이 확정한 것

- **재기준화 1회를 수용한다** — `import_vfx` / `import_vfx_ms` 의 id draw 제거로
  스트림이 한 번 이동하므로 6등급 곡선을 재측정하고 새 기준선으로 기록한다.
  ADR-0229 의 기존 opening 곡선(`100.0/88.6/73.1/39.3/35.7/0.0`)은 이 시점부터
  **역사적 값**이 된다. Accepted ADR 은 immutable 이므로 **ADR-0229 본문은 고치지
  않고**, 새 기준선은 **이 ADR 에 기록**하며 supersede 관계를 명시한다
  (Open questions (c) 의 권고안).
- **표시 계층 변경의 기본 비용이 0.0pp 가 된다** — 이후 VFX spawn 작업
  (ADR-0238 의 P2 잔여 · P8 · X5 · X8)은 draw 를 소비하지 않아 §A1 판정 없이
  진행할 수 있다.
- **`core/status.ts` 의 fluff 판정도 범위에 포함** — 전투 경로에서 draw 를 소비하는
  표시용 RNG 도 함께 정리한다.
- **RNG draw 수 불변식 테스트가 이 ADR 의 산출물** — ADR-0231·0232 가 수작업으로
  대조했던 것을 기계화한다.

### 긍정적 영향

- 표시 개선이 밸런스와 분리된다 — 이 세션에서 세 번 반복된 함정(표시 변경 →
  2~3pp 이동 → §A1 재판정)이 사라진다.
- 코드에만 있던 규칙을 테스트가 강제한다.

### 부정적 영향 / 수용한 비용

- **1회 재기준화** — 기준선이 바뀌므로 그 이전 곡선과의 비교는 "다른 기준선"임을
  명시해야 한다. 되돌리기가 자명하지 않다 (Open questions (f)).
- **id 충돌 의미 확대** — 동일 내용 spawn 2건이 같은 id 를 갖는다. 현행 근거(id 는
  logic 에 안 읽히고 렌더는 배열 순서)를 13개 지점 전부에서 확인해야 한다
  (Open questions (a)).
- **fluff 판정의 결정화** — 20% 확률 분기가 결정적이 되면 fluff 다양성이 줄 수
  있으므로 배분 방식을 확인해야 한다.

### 후속 항목

1. 구현: 두 헬퍼의 id 를 `deterministicVfxId` 기반으로, `status.ts` fluff 를
   결정적/주입식으로, draw 수 불변식 테스트 추가 (Open questions (a), (d)).
2. 재기준화 실행: `npm run balance` (opening) + `--deck ppl`, 6등급 전후 표를 이
   ADR 에 기록.
3. 그 뒤 ADR-0238 의 VFX 항목 착수 (이 ADR 이 먼저).

## 재기준화 결과 (2026-10-31, `c488b6d`)

Option B 의 **1회 재기준화를 승인대로 실행**했다. 이동은 예상된 결과이며, 어떤 수치도
옛 곡선으로 되돌리려 튜닝하지 않았다. **아래 "이후" 표가 새 기준선이다.**

| grade | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- |
| opening **이전** (구 기준선) | 100.0 | 88.6 | 73.1 | 39.3 | 35.7 | 0.0 |
| opening **이후** (새 기준선) | 100.0 | 88.3 | **70.5** | 39.5 | 36.2 | 0.0 |
| Δpp | 0.0 | −0.3 | **−2.6** | +0.2 | +0.5 | 0.0 |
| PPL **이전** | 100.0 | 77.9 | 99.6 | 84.8 | 44.4 | 28.3 |
| PPL **이후** (새 기준선) | 100.0 | 79.1 | 98.9 | 83.0 | 44.4 | **24.7** |
| Δpp | 0.0 | +1.2 | −0.7 | −1.8 | 0.0 | **−3.6** |

- **ADR-0229 관계**: 위 "이전" 값이 ADR-0229 가 기록한 곡선이며, 이 시점부터
  **역사적 값**이다. ADR-0229 는 Accepted/immutable 이므로 본문을 고치지 않고, 새
  기준선은 **이 ADR 이 보유**한다 (supersede 관계).
- **롤백 자료**: Open questions (f) 를 위해 "이전" 곡선을 위에 함께 남긴다 — 코드를
  원복하면 이 값으로 돌아가야 한다.
- **미완**: (b) 가 해결되어 caller-side seed 를 도입하면 **2차 재기준화**가 필요하다.
  그때 이 표를 다시 갱신한다.

## Implementation Status (2026-11-01)

**Status**: ✅ Implemented — VFX 절반 구현 (`c488b6d`) + `core/status.ts` 게임플레이
재분류 **확정** (Open questions (b), 오너 승인 2026-11-01 → 선택지 1).

**Evidence**:
- ✅ `core/state/state_helpers.ts:23`·`:47` — `import_vfx` / `import_vfx_ms` 의 id 가
  이제 `deterministicVfxId` 기반 (draw 0). `c488b6d`
- ✅ `web/tests/vfx_rng_neutrality.test.ts` — 0-draw 불변식 (변경 전 실패 → 후 통과).
  `use_program` 5-spawn 시나리오에서 draw **10 → 5**, 남은 5개는 전부 게임플레이
  (damage variance · crit check · burn proc · slow proc · enemy ICE crit roll)
- ✅ 안전성 확인 — `CombatVfxInstance.id` 의 유일한 독자는 `screen_shake.ts:234` 의
  `player_hit` 게이트뿐이고 그 spawn 은 `import_vfx_deterministic`(이미 content-hash)
  에서 나온다 → 13개 지점의 공유 id 는 무해
- ✅ `core/status.ts:251`·`:255` — **게임플레이로 재분류, 코드 무변경** (선택지 1,
  2026-11-01 오너 승인). draw 2개는 게임플레이 예산으로 남고, 새 테스트가 그렇게 pin 한다.
- ✅ `core/combat/state_actions_programs.ts:99`, `state_actions_combat.ts:234`·`:258`·`:333`,
  `loot.ts:30`, `death_cycle.ts:45` — **게임플레이 RNG (불변 유지)**

**Notes**: 최초 Draft 의 실측 2건은 ADR-0238 작업 중 일회성으로 수행하고 원복한
것이며 저장소에 흔적이 없다 (백업 `/tmp/p8-backup2-state_actions_programs.ts`).
구현 실측(위 재기준화 표)은 `c488b6d` 이다. (b) 가 마지막 미결 항목이었으므로 이
ADR 은 이제 **완결**이다 — 남은 열린 질문 (a)(c)(f) 는 구현 세부이며 이 ADR 의
구현 완료를 막지 않는다.

## Open questions

- **(a) id 스킴** — content hash 로 충분한가? `deterministicVfxId` 를 그대로 두
  헬퍼에 적용할지, 호출 순서 기반 counter 를 섞을지 (동일 내용 2건이 같은 id 를
  갖는 의미가 13개 지점 모두에서 안전한지 확인 필요).
- ~~**(b) `core/status.ts` 재분류**~~ — ✅ **결정: 선택지 1 (게임플레이로 재분류, 코드
  무변경)** — 2026-11-01 오너 승인. 최초 결정에서 "포함"으로 정한 이 항목은
  **게임플레이**로 판명됐다. `rollStatusProc(_kind, rng)` 은 `_kind` 를 **무시**하고
  `rng() < 0.2` 만 보며, 호출자 (`state_actions_programs.ts:145`·`:154`)가 그 결과로
  **`burn`(2뎀×3턴) · `slow`(−30%댐·2턴)을 실제 적용**한다. 기존 테스트도 게임플레이로
  취급한다 (`slow_effect.test.ts` 가 `Math.random` 을 0.99 로 stub 하며 "suppress burn
  proc" 주석). 따라서 `status.ts` 안에서만 결정적으로 만들면 20% proc 이 **상수화**되어
  게임플레이가 바뀐다 — **이 ADR 의 RNG 지도가 이 항목을 "표시" 로 오분류**한 것이
  원인이다.
  - **채택: 선택지 1** — 게임플레이로 재분류해 **그대로 둔다**. 범위에서 제외되고
    draw 2개는 게임플레이 예산으로 남는다 (새 테스트가 그렇게 pin).
  - **기각: 선택지 2** — `core/combat/**` 에서 상태 기반 시드를 주입. 그 자체가
    게임플레이 변경이므로 **2차 재기준화**가 필요하고, ADR-0239 는 이미 `c488b6d` 로
    한 번 재기준화했으므로 두 번째 곡선 이동을 정당화할 이득이 없다 (2026-11-01 판단).
- **(c) 새 기준선의 지위** — **권고안: ADR-0229 본문은 immutable 이므로 고치지
  않고, 새 기준선을 이 ADR 에 기록하며 supersede 관계를 명시**한다 (별도 baseline
  문서를 새로 만들지 않는다). 오너가 이 권고를 그대로 승인하면 구현 시 그렇게 한다.
- ~~**(d) 불변식 테스트**~~ — ✅ **결정: 같은 ADR 에 포함** (§사용자 결정). 무엇을
  고정할지(draw 수 vs 첫 N draw 해시)와 CI 강제 여부는 구현 세부로 남긴다.
- ~~**(e) 순서**~~ — ✅ **결정: 이 ADR 을 먼저** 처리하고 ADR-0238 의 VFX 항목은 그
  뒤에 (§사용자 결정).
- **(f) 되돌리기 정책** — **권고안: 재기준화 직전의 곡선을 이 ADR 에 함께 기록**해
  두어 문제 발생 시 코드 원복과 기준선 원복이 함께 가능하게 한다. 롤백 판단
  기준(어떤 신호에서 되돌리는가)은 미정.

## 영향 받는 항목

### 이 결정으로 변경된 항목

- `docs/wiki/decisions/0239-vfx-spawn-rng-decoupling.md` — **신규** (이 ADR)
- `docs/wiki/decisions/README.md` — 인덱스 행 (Draft → **Accepted**)

### 구현 시 변경될 항목 (결정으로 확정 — 구현은 미착수)

- `core/state/state_helpers.ts` — `import_vfx` / `import_vfx_ms` 의 id 를
  `deterministicVfxId` 기반으로 (13개 호출 지점은 무변경)
- `core/status.ts` — fluff RNG 를 결정적/주입식으로 **(범위 포함 확정)**
- `web/tests/**` — RNG draw 수 불변식 테스트 **(같은 ADR 범위로 확정)**
- 이 ADR 본문 — 재기준화 후 6등급 전후 표 (ADR-0229 의 곡선은 supersede 관계로 명시)

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
- 2026-10-31 (2차): WF8 난이도 곡선 채점 증거 추가 (현재 vs 분리 프록시 — opening
  1.88 → 1.76 · PPL 0.93 → 0.94, PPL 고신뢰) → Option B 의 위험을 낮추는 근거.
- 2026-10-31 (3차): **Draft → Accepted.** 프로젝트 오너가 **Option B** 채택,
  `core/status.ts` fluff 포함, 불변식 테스트를 같은 ADR 에 포함, 이 ADR 을 우선
  처리. Consequences 작성, 열린 질문 (b)(d)(e) 해소, (c)(f) 는 권고안 명시.
  **구현은 아직 미착수.**
- 2026-10-31 (4차): **구현 착수 + 재기준화 실행** (`c488b6d`). `import_vfx` /
  `import_vfx_ms` 의 id 를 `deterministicVfxId` 로 전환 (13개 호출 지점 무변경),
  0-draw 불변식 테스트 추가 (변경 전 실패 → 후 통과), 양 덱 재기준화 표를 이 ADR 에
  기록. **다만 `core/status.ts` 는 게임플레이로 판명되어 범위에서 제외** — RNG 지도
  오분류를 정정하고 (b) 를 재개. Implementation Status → 🟡 Partial.
