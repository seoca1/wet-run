# ADR-0263: 죽음 화면에서 빠져나올 수 있어야 한다 — FLATLINE 탈출

**상태**: Accepted
**날짜**: 2026-11-03
**결정자**: 오너 플레이 리포트 ("플레이 한번 해봤는데, 보스 배틀 이후 빠져나오지 못한 버그가 있어")
**우선순위**: P0 (블로킹 버그 — 런이 끝나지 않고 플레이어가 갇힘)
**관련**: [ADR-0040 — Death & Restart Cycle](./0040-death-restart-cycle.md) · [ADR-0252 — ending 이 런을 끝낸다](./0252-run-end-and-save-timing.md) · [ADR-0251 — 어포던스 진실성 §5](./0251-truthful-program-affordance-and-combat-integrity-rules.md) · [ADR-0262 — 성장 연출](./0262-growth-reads-as-an-event.md)

> **플레이어가 갇혔다.** HP 가 0 이 되면 `FLATLINE` 화면이 뜨는데, **어떤 키도 먹지 않았다.**
> 원인은 입력 배선의 공백이다 — 죽음 화면의 유일한 탈출 액션(`select_restart`)은
> **앱에서 한 번도 디스패치된 적이 없다**(테스트/퍼저에만 존재). 리듀서도 `confirm`/`jack_out` 을
> 무시했고, 화면에는 안내 문구조차 없었다.

## 컨텍스트 (Context)

오너가 실제 브라우저에서 플레이하다 보스 전투에서 지고 `FLATLINE` 에 갇혔다.
독립 headless 재현으로 확인한 사실:

| 확인 | 결과 |
|---|---|
| 죽음 진입 | `applyCombatAction` 이 적 턴에서 HP 0 → `runPhase: "dead"`, `phase: "defeat"`, `message: "FLATLINE"` |
| 입력 디스패치 | `applyAction` → `runPhase === "dead"` → `applyDeathAction` |
| 리듀서 반응 | `trigger_death`(죽음 자체, 이미 지나감)와 `select_restart` **만** 처리. `confirm`/`jack_out`/방향키 → **상태 불변** |
| `select_restart` 발신자 | `web/src` 전체에 **없음** (테스트·퍼저에만 존재) |
| 화면 | `combat_grid.ts` 의 `phase === "defeat"` 분기는 아트만 그리고 **안내 문구 0** |
| 재현 | `Enter`/`Escape`/`←↑↓→`/`1`/`4`/`Space`/`q` 전부 **변화 없음** |

즉 죽음은 **되돌릴 수 없는 막다른 길**이었다. 브라우저 새로고침만이 탈출이었고,
그마저 ADR-0252 §A 때문에 죽음 프레임이 저장되어 `CONTINUE` 가 같은 화면으로 되돌렸다.

`select_restart` 의 4가지 선택(`same_jockey`/`new_jockey`/`hall_of_dead`/`main_menu`)은
ADR-0040 Option A 의 설계인데, web/ 포팅에서 **UI 가 한 번도 붙지 않았다**(ADR-0040 은
"web/ TypeScript 는 deceased persistence 를 구현하지 않음"을 이미 명시).

## 고려한 옵션

### Option A: ENTER/ESC → 타이틀 (선택)
죽음 화면에 `ENTER / ESC: return to title` 한 줄을 그리고, `confirm`/`jack_out` 을
**엔딩 화면과 같은 모양**으로 처리한다(런 상태를 지우고 타이틀로). 새 상태·새 문법 없음.

### Option B: ADR-0040 의 4선택 메뉴를 지금 구현
`SAME JOCKEY / NEW JOCKEY / HALL OF DEAD / MAIN MENU`. 설계 의도에 가장 충실하지만
선택 상태·렌더·입력 매핑이 새로 필요하고, 그 중 `new_jockey`/`same_jockey` 는
ADR-0040 이 "web/ 미구현"으로 남겨둔 더 큰 슬라이스다.

### Option C: 리듀서만 고치고 화면은 그대로
`confirm` → `phase: "menu"` 만 하면, 컨트롤러가 `runCompleted` 처럼 인식하지 못해
화면이 그대로 남는다. **불충분.**

**결정: Option A.** 블로킹 버그를 가장 작은 변경으로 제거하고, 화면이 실제 동작을 말하게 한다
(ADR-0251 §5). ADR-0040 의 풍부한 죽음 사이클은 별도 슬라이스로 남긴다(아래 열린 질문).

## 결과 (Consequences)

### 변경 4곳

| 파일 | 변경 |
|---|---|
| `web/src/core/state/state_actions_phases.ts` | `applyDeathAction` 이 `confirm`/`jack_out` → `phase: "menu"` (런은 계속 `runPhase: "dead"`) |
| `web/src/core/state/run_end.ts` | `runFailed(previous, next)` — 죽음 화면 이탈 판정. `FLATLINE_MESSAGE` 상수 |
| `web/src/renderer/combat_grid.ts` | 죽음 화면에 `ENTER / ESC: return to title` (손패 자리 — 죽음 화면은 그 자리가 빈다) |
| `web/src/main.ts` | `runFailed` 이면 `state = null; screen = "menu"` — 엔딩과 **같은 모양**의 탈출 |

### 왜 `runCompleted` 를 재사용하지 않았나

`runCompleted` 는 `runPhase: "ending"` 을 요구한다. 죽음은 `runPhase: "dead"` 로 남겨야
`applyDeathAction`/`lastDeathSummary`/저장이 일관되고, **엔딩과 죽음이 섞이지 않는다**
(엔딩은 슬롯을 retire, 죽음은 write — ADR-0252 §A).

### 왜 `select_restart` 를 재사용하지 않았나

`select_restart` 의 `main_menu` 와 `same_jockey` 는 **둘 다** `phase: "menu"`, `runPhase: "matrix"`
를 반환해 컨트롤러가 구분할 수 없다. 게다가 `runPhase: "matrix"` 는 매트릭스 화면을 그리게 해
타이틀로 돌아가지 않는다. 그래서 죽음 전용 판정을 따로 둔다.

### 불변

- **밸런스 byte-identical** — 리듀서 변경은 `phase: "defeat"` 에서만 발동하고, 하네스는 죽지 않는다.
- `autosaveIntent` 는 죽음 프레임에 `"write"` 를 유지한다(테스트 고정). 실제 슬롯이 남는지는
  열린 질문 (a) — 라이브에서는 남지 않았다.
- `select_restart`·ADR-0040 의 선택지·`deceasedJockeys` 기록·`lastDeathSummary` **무변경**.
- ADR-0262 의 성장 연출과 독립 — 죽음 이탈 시 표시 전용 프레임도 함께 정리한다.

## Implementation Status (2026-11-03)

**Status**: ✅ Implemented

**Evidence**:

- `web/tests/run_end_save.test.ts` — `runFailed`: `confirm`·`jack_out` 참, 방향키·`cycle_target` 거짓,
  죽음 그 자체는 거짓, 엔딩 완료와 혼동되지 않음, `runPhase` 가 `"dead"` 로 유지,
  `lastDeathSummary` 보존, 죽음 프레임은 계속 `"write"`, 그리고 `main.ts`/`combat_grid.ts` 소스 배선 확인.
- `web/tests/combat_grid.test.ts` — 죽음 화면이 3레이아웃 모두에서 `ENTER / ESC: return to title` 를
  보여주고, 전투 중에는 보여주지 않는다.
- 3레이아웃 before/after 캡처 24 PNG + 24 쌍(신규 `defeat` 케이스 포함) — 그리드 초과 **0** —
  [`defeat-escape-2026-11-03`](../../design/defeat-escape-2026-11-03/).
  (HUD 초과는 before/after 동일한 **기존** 좁은 레이아웃 결함, ADR-0254(c).)
- **실브라우저 재현**(독립 headless Chromium, preview 5195): 실제 전투에서 사망 →
  `runPhase "dead"`/`phase "defeat"` → **수정 전: 8개 키 전부 무반응**, **수정 후: `Enter` → 탈출**
  (타이틀에서 이후 입력 정상 동작).
- vitest **181 files / 4014 tests passed** · tsc 0 · eslint 0 errors · build PASS.

**Notes**:

- 죽음 화면의 안내는 엔딩 화면과 **같은 문구**를 쓴다(`ENTER / ESC: return to title`) — 화면 언어 일관성.
- **관찰(수정 필요)**: 죽음 프레임은 실제로 슬롯에 남지 않았다. 잭아웃 사망 후 타이틀이
  `CONTINUE (no save)` 를 보였고 `hasSaveCache === false` 였다 — `autosaveIntent(dead)` 는
  `"write"` 를 반환하는데도(테스트 고정) 그렇다. 그래서 죽은 런은 **다시 열리지 않는다**(아래 (a)).

## 열린 질문

- **(a) 죽음 프레임이 왜 저장되지 않는가.** `autosaveIntent` 는 `"write"` 인데 라이브 슬롯은 비어 있다
  (타이틀 `CONTINUE (no save)`, `hasSaveCache === false`). 쓰기 실패인지, 복원 거부인지, 아니면
  죽음 시 슬롯을 retire 하는 것이 맞는지 확인이 필요하다. (ADR-0252 §A 는 죽음도 write 로 둔다.)
- **(b) ADR-0040 죽음 사이클.** `same_jockey`/`new_jockey`/`hall_of_dead` 선택 메뉴는
  여전히 미배선이다. 죽음 화면에 선택지를 붙이는 별도 슬라이스.
- **(c) 좁은 레이아웃 HUD 압착.** 위 HUD 초과(기존 결함)는 HUD 재설계 스케일.
- **(d) COST 상한과 탈출.** 전투에서 COST(alarm)가 상한에 닿으면 프로그램이 전부 BLOCKED 이고,
  유일한 출구는 `ESC`(JACK OUT) → **런 실패** → 죽음 화면이다. 이 경로 자체는 설계(ADR-0240/0242)지만,
  플레이어가 "나갈 수 없다"고 느낀 지점이 정확히 여기다 — 안내가 더 분명해야 하는지 검토.

## 영향 받는 항목

- `web/src/core/state/state_actions_phases.ts` — `applyDeathAction` (confirm/jack_out)
- `web/src/core/state/run_end.ts` — `runFailed` · `FLATLINE_MESSAGE`
- `web/src/renderer/combat_grid.ts` — 죽음 화면 안내 문구
- `web/src/main.ts` — `runFailed` 분기
- `web/tests/run_end_save.test.ts` · `web/tests/combat_grid.test.ts`

## 관련 결정

- ADR-0040 (죽음/재시작 사이클 — 이 ADR 은 그 최소 탈출만 구현) · ADR-0252 (엔딩이 런을 끝낸다 —
  같은 패턴) · ADR-0251 (규칙 5: 화면은 실제 동작을 말한다)

## 변경 이력

- 2026-11-03: 오너 플레이 리포트 → 재현 → Draft 작성 · 구현 완료
