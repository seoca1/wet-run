# ADR-0290: 곡선 재기준화 + 코어는 경로 뒤에 있다

**상태**: Accepted
**날짜**: 2026-11-07
**결정자**: 오너 ("응." — ADR-0289 (a)·(b) 승인)
**우선순위**: P1 (곡선) · P1 (설계)
**관련**: [ADR-0289 — 원인은 곡선이다](./0289-the-curve-is-the-problem.md) · [ADR-0288 — 싸우는 것이 손해다](./0288-fighting-does-not-pay.md) · [ADR-0283 — prep 은 용량](./0283-prep-is-capacity-not-cards.md) · [ADR-0280 — 적은 턴마다](./0280-the-ice-acts-on-the-turn.md) · [ADR-0229 — 곡선 재기준화](./0229-grade-curve-rebaseline.md)

> ADR-0289 는 두 가지를 요구했다: **늦은 등급의 교전을 이길 수 있게** 만들고, **코어를 경로 뒤에**
> 두는 것. 하나만 넣으면 안 된다 — 곡선만 넣으면 회피가 여전히 최적이고, gate 만 넣으면 g4 가
> 12.5% 로 부서진다. **함께** 넣었고, 결과는 아래 표다.

## 결정 (Decision)

### 1) 늦은 등급의 교전을 이길 수 있게 (곡선)

| 상수 | 이전 | 이후 |
|---|---|---|
| `ENCOUNTER_HP_BY_GRADE` | `95, 95, 95, 95, 165, 165` | **`95, 95, 95, 95, 95, 95`** |
| `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` | `50, 30, -32, 20, 0, -20` | **`50, 30, -32, 0, -10, -10`** |
| `PREP_HP_BY_GRADE` | `0, 0, 20, 25, 270, 175` | **`0, 0, 20, 55, 240, 175`** |
| `PREP_SHIELD_BY_GRADE` | `0, 0, 35, 45, 650, 250` | **`0, 0, 35, 65, 400, 250`** |

g4 는 prep 이 +25 HP 뿐이어서 다른 등급보다 **어려웠다**(ADR-0289 의 비단조 원인). +55 로 올려
g3 > g4 > g5 가 성립하게 했다.

### 2) 보스 HP 를 교전 상한에서 분리 (새 상수)

```ts
export const BOSS_HP_BY_GRADE = [95, 95, 95, 95, 165, 165];
```

이전엔 교전과 보스가 **같은 상한**을 썼다. 그래서 교전을 이길 수 있게 상한을 내리면 **보스까지
같이 약해졌고**(g5/g6 보스 HP −42%), ADR-0289 의 스윕에서 g5 가 98% 로 튄 이유가 이것이었다.
`iceHpForGrade(ice, grade, isBoss)` 로 분리했고, 값은 **이전 보스 HP 를 그대로 재현**한다 —
이 결정은 **보스 난이도를 바꾸지 않는다**.

### 3) 코어는 경로 뒤에 있다 (gate)

```ts
export const BOSS_GATE_CLEARS_BY_GRADE = [0, 1, 1, 1, 1, 1];
```

`bossGateNeed(state) = min(gateClears(grade), 보드의 비-보스 교전 수)` — **보드에 있는 것보다 많이
요구하지 않으므로** 짧은 미션도, 교전이 하나도 없는 보드도 잠기지 않는다.

- 봉인 상태에서 코어로 이동하면 **이동하지 않고** `Core sealed — N more ICE must fall (h/N)` 을
  보여준다. 선택은 유지된다: **어떤** 교전을 칠지는 플레이어의 몫이고, 그것이 ADR-0287 의 intel 이
  정보를 제공하는 결정이다.
- g1 은 요구가 0 — 첫 미션은 지금까지처럼 걸어서 끝낼 수 있다.

## 측정 (Measurement)

`npm run survival --seeds 24 --loot smart`, 미션 완료율:

| 정책 | g1 | g2 | g3 | g4 | g5 | g6 |
|---|---:|---:|---:|---:|---:|---:|
| `long` — 다 싸운다 | 100.0 | 97.9 | 87.9 | **72.5** | **43.5** | **15.3** |
| `picky` — 코어로 직행(봉인되면 싸움) | 100.0 | 99.2 | 89.0 | **72.5** | **42.1** | **15.3** |
| *ADR-0288 (변경 전)* `long` | 100.0 | 97.9 | 83.0 | 45.4 | 30.6 | 18.1 |
| *ADR-0288 (변경 전)* `picky` | 100.0 | 99.2 | 93.9 | 72.5 | 64.4 | 65.3 |

**핵심: 두 정책이 모든 등급에서 노이즈 이내다.** 이것이 이 결정의 목적이다 — 이제 **싸우는 것도,
건너뛰는 것도 지배 전략이 아니다.** ADR-0288 에서는 g4 +27.1pp · g6 +47.2pp 로 회피가 압승했다.

교전당 승률(`npm run balance`, 100런, 오프닝 덱):

| | g1 | g2 | g3 | g4 | g5 | g6 |
|---|---:|---:|---:|---:|---:|---:|
| 이전 (ADR-0229 행) | 100.0 | 100.0 | 100.0 | 95.2 | 44.1 | **0.3** |
| **이후** | 100.0 | 100.0 | 100.0 | **99.7** | **88.3** | **52.3** |
| PPL 참조 | 100.0 | 100.0 | 100.0 | 98.8 | 86.1 | 83.7 |

곡선은 여전히 **단조 비증가**다. `0.3%` 라는 숫자가 이 세션 전체의 뿌리였다: **이길 수 없는
교전**은 선택이 아니라 벽이고, 벽 앞에서 회피가 최적이 되면 전리품·크레딧 소비처·경로 결정이 전부
무의미해진다.

## 결과 (Consequences)

- **싸움이 선택이 됐다**: 두 전략이 같아졌으므로 "무엇을 얻기 위해 무엇을 치를까"가 실제 결정이다.
- **ADR-0287 의 intel 이 처음으로 의미를 가질 수 있다** — 고를 교전이 생겼기 때문. (측정은 여전히
  완전정보 봇의 한계로 불가; ADR-0287 B 참조.)
- **곡선 재기준화**: 목표 `100/95/80/50/25/10` 은 **폐기**하고 측정값 `100/97.9/87.9/72.5/43.5/15.3`
  을 새 baseline 으로 삼는다. g6 15.3% 는 목표 10% 보다 높지만, "이길 수 있는 마지막 등급"이라는
  설계 의도에 맞춘 값이다.
- **불변**: 결말 리졸버·전투 리듀서·저장 형식 무영향. `SaveSlot` version 1 그대로.

## Implementation Status (2026-11-07)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/combat/ice_scaling.ts` — `ENCOUNTER_HP_BY_GRADE` · `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`
  · **`BOSS_HP_BY_GRADE`** · `iceHpForGrade(ice, grade, isBoss)` · `bossGateClears` · `bossGateNeed`.
- `web/src/core/dungeon/matrix.ts` · `web/src/core/state/encounter_verbs.ts` — 보스 플래그 전달.
- `web/src/core/state/prep.ts` — `PREP_HP_BY_GRADE` · `PREP_SHIELD_BY_GRADE`.
- `web/src/core/state/state_actions_phases.ts` — 이동 시 봉인 검사 + 메시지.
- `web/scripts/play_policy.ts` — `nearestObjective` 가 **봉인 중에는 보스를 목적지로 삼지 않는다**
  (이것이 없으면 봇이 봉인 앞에서 영원히 재시도한다 — ADR-0289 의 "데드락" 오진의 정체).
- `web/tests/adr0290_the_core_opens_after_a_path.test.ts` (5) · `balance_sim.test.ts` ·
  `ice_scaling.test.ts` 갱신.
- vitest **197 files / 4128 tests** · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 ·
  story trace 통과(g4·기본 미션).

**Notes**:

- **e2e 드라이버 수정 불필요** — 새 화면 없음. story trace 는 봉인을 만나면 교전하고 코어로 간다.
- **`picky` 의 이전 g6 0.0% 의혹(`fewestFightsNextHop`)은 별개**로 남는다 — 이 결정은 그 정책을
  쓰지 않는다.
- **2026-11-08 갱신 (브라우저 재검증) — 하네스 미반영 + 소프트락 1건.**
  ⑴ **위 Evidence 의 봉인 회피는 `play_policy.ts`(헤드리스)에만 들어갔다.** 브라우저 소크의
  `nextHop`(`soak_playthrough.spec.ts`)은 봉인된 apex 를 그대로 목표로 삼아, 159런 중 **18런**이
  `Core sealed — 1 more ICE must fall (0/1)` 를 **320스텝 동안** 누르며 헛돌았다(보스가 인접 ICE 보다
  먼저 정렬되는 8개 미션, 3정책 공통). 봉인이 풀릴 때까지 보스를 business 에서 제외해 **18 → 3**.
  ⑵ **소프트락 — 미수정, 오너 결정 필요.** `BYPASS` 는 노드를 `bypassedEncounterNodes` 에 넣지만
  `iceIds` 를 지우지 않고, `bossGateNeed` 의 clamp 는 `iceIds.length > 0` 을 센다. 그래서 보드의
  **유일한 비-보스 교전을 우회하면 코어가 영구히 봉인**된다(탈출은 JACK OUT 뿐). 재현: `Flatline's Call`
  → ICE(9) BYPASS → 보스 앞 ENTER → `Core sealed — 1 more ICE must fall (0/1)`(bypassed=[9], cleared=[]).
  최종 census 의 `no_end_in_steps` **3/99 가 전부 이 원인**(`random` 정책만 BYPASS 를 시도한다).
  후보: **ⓐ** clamp 에서 이미 우회한 노드를 제외 → 우회가 "해결된 교전"으로 인정됨 **ⓑ**
  `have = cleared.length + bypassed.length`. **→ ADR-0308 로 종결**: Jev Choice **p = 0.94** 로
  **ⓐ 채택**(clamp 에서 우회 노드 제외). 소크 census `no_end_in_steps` **3 → 0**, 밸런스
  **byte-identical**(헤드리스 정책은 BREACH 만 쓴다).

## 열린 질문

- **(a) g6 15.3% 가 적절한가.** 목표 10% 보다 높다. 낮추려면 `BOSS_HP_BY_GRADE[5]` 또는 aleph 의
  skill 빈도를 조정해야 하고, 그러면 g5/g6 격차가 벌어진다.
- **(b) prep 곡선의 절벽.** `PREP_HP_BY_GRADE` 가 g4 55 → g5 240 으로 뛴다. 보스 HP 가 95 → 165 로
  뛰기 때문이고, 매끄럽게 만들려면 보스 테이블을 다시 재야 한다(시도 3종 모두 g5 를 2-11% 로
  떨어뜨렸다).
- **(c) gate 요구량 2+.** 지금은 전 등급 1. 2로 올리면 "어떤 둘을 칠까"가 더 강한 결정이 되지만
  g4 가 다시 어려워진다.
- **(d) intel 의 값 재측정.** 고를 교전이 생겼으므로 ADR-0287 (a) 를 다시 시도할 가치가 있다.