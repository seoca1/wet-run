# ADR-0264: 죽음은 런을 끝낸다 — 죽음 시 슬롯을 retire

**상태**: Accepted
**날짜**: 2026-11-03
**결정자**: 오너 선택 ("A만 (죽음 시 슬롯 retire) (추천)")
**우선순위**: P1 (런 무결성 — 죽음의 대가 / 저장 복원 정합)
**관련**: [ADR-0252 — 런 종료와 저장 시점](./0252-run-end-and-save-timing.md) · [ADR-0263 — 죽음 화면 탈출](./0263-defeat-screen-must-be-escapable.md) · [ADR-0040 — 죽음/재시작 사이클](./0040-death-restart-cycle.md) · [ADR-0185 — 세이브 마이그레이션](./0185-save-migration-v2.md)

> **죽고 새로고침하면 다시 살아났다.** 슬롯에 `runPhase` 가 없어 `slotToGameState` 가 모든 저장을
> `runPhase: "matrix"` 로 복원한다. 그래서 죽음 프레임을 `write` 로 두면 **플랫라인 후 HP 0 인 채
> 보드에 서 있고**(플레이 불가), **잭아웃 후에는 HP 그대로 부활**한다. ADR-0252 §A 의
> "죽음도 write" 를 이 ADR 이 뒤집는다.

## 컨텍스트 (Context)

ADR-0263 을 처리하며 발견했다. 실측(독립 headless Chromium, preview 5195, 실제 전투):

| 죽음 | 사망 직후 상태 | 리로드 → `CONTINUE` |
|---|---|---|
| **HP 0 (FLATLINE)** | `runPhase "dead"`, `phase "defeat"`, hp 0, node 18 | **`runPhase "matrix"`, hp 0**, 도착 조우 재개방 → 플레이 불가능한 유령 보드 |
| **JACK OUT** | `runPhase "dead"`, hp 40, node 18 | **`runPhase "matrix"`, hp 40** → **부활** (죽음의 대가 소멸) |

원인은 저장 스키마에 있다:

- `SaveSlot` 에 `runPhase` 가 **없다**(`version`/mission/hp/credits/turn/덱/노드 등만).
- `slotToGameState` 는 **항상** `runPhase: "matrix"`, `phase: "approach"` 로 복원한다.
- 따라서 죽음 프레임도 "매트릭스 프레임"으로 되살아난다. `autosaveIntent` 는 죽음에 `"write"` 를
  돌려주고 있었고(ADR-0252 §A), 그 write 가 정확히 이 상태를 만들었다.

부수 확인: `deceasedJockeys`·`lastDeathSummary`·`totalDeaths` 는 슬롯에 저장되지 않는다
(`slotToGameState` 가 `deceasedJockeys: []`, `lastDeathSummary: null` 로 시작). 즉 **죽음 기록은
원래부터 보존되지 않았으므로**, 죽음 프레임을 저장해도 잃을 기록이 없다.

## 고려한 옵션

### Option A: 죽음도 슬롯 retire (선택)

`autosaveIntent` 가 `runPhase === "ending" || runPhase === "dead"` → `"retire"`.
죽음 = 런 종료 → 슬롯 비움 → `CONTINUE` 비활성 → 새 런만.

- ✅ 가장 작다 (한 조건).
- ✅ **부활 익스플로잇과 HP 0 유령 보드를 동시에 제거.**
- ✅ ADR-0252 의 원칙("끝난 런은 재개할 수 없다")과 일치 — 그 원칙을 `ending` 에만 적용한 것이
  비대칭이었다.
- ✅ 잃는 것 없음 — 죽음 기록은 어차피 슬롯에 없다.

### Option B: 슬롯에 `runPhase`(또는 `runOver`)를 저장해 죽은 런을 죽음 화면으로 복원

- `CONTINUE` → `FLATLINE` 화면 재표시 → `ENTER` → 타이틀.
- ✅ ADR-0252 §A 의 "죽음도 write" 라는 의도를 실제로 성립시킨다.
- ❌ **새 영속 필드** + `isSaveSlot` 검증 + `slotToGameState` 분기 + 마이그레이션 테스트.
  ADR-0259/0261 이 영속 필드를 비용으로 취급해 온 관행과 어긋난다.
- ❌ 얻는 것이 화면 한 번 다시 보여주기뿐이다(기록은 어차피 휘발).

**결정: Option A.** 오너가 "A만"을 선택. Option B 는 죽음 화면 재표시가 필요해지면 그때 별도 슬라이스로.

## 결과 (Consequences)

```ts
// web/src/core/state/run_end.ts
export function autosaveIntent(state: GameState | null): "write" | "retire" | "skip" {
  if (state === null) return "skip";
  return state.runPhase === "ending" || state.runPhase === "dead"
    ? "retire"
    : "write";
}
```

- 죽음 프레임을 그리는 순간 `autosave()` 가 `clearSlot(0)` 을 실행하고, 이후 `hasSave(0)` 이 false 다.
- `CONTINUE` 가 목록에서 사라지고(`(no save)`), 타이틀에는 `FLATLINE_MESSAGE` 가 남는다.
- ADR-0263 의 탈출(죽음 화면에서 `ENTER`/`ESC` → 타이틀)은 그대로다 — 죽음 화면은 화면 안에서
  즉시 나올 수 있고, 슬롯은 그와 별개로 정리된다.

### 불변

- **밸런스 byte-identical** — `autosaveIntent` 는 하네스 경로에 없다(loot/죽음을 걷지 않는다).
- **살아있는 런 프레임은 계속 write** — 매트릭스 이동·전투·loot. "reload 가 마지막 전투 프레임이 아니라
  커밋된 상태를 복원한다"는 ADR-0252 의 핵심은 무변경.
- `version` 1 유지, 슬롯 스키마 무변경(필드 추가 없음) → 마이그레이션 불필요.
- ADR-0240/0242 의 COST(alarm) 압박, ADR-0040 의 죽음 선택지(`select_restart`) 무변경.

## Implementation Status (2026-11-03)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/state/run_end.ts` — `autosaveIntent` 가 `ending`/`dead` 둘 다 retire.
- `web/tests/run_end_save.test.ts` — "writes the slot on Matrix, loot and combat frames"(죽음 제외) +
  ADR-0263 블록의 "retires the slot on death, so a flatline is not a resumable run (ADR-0264)"
  (죽음 → `retire`, 같은 상태에서 `runPhase: "combat"` 이면 `write`).
- **실측 before/after**(독립 headless Chromium, preview 5195, 실제 전투):
  - before — HP 0 사망 → 리로드 → `CONTINUE` → `runPhase "matrix"`, **hp 0**, 조우 재개방.
    잭아웃 사망 → 리로드 → `CONTINUE` → `runPhase "matrix"`, **hp 40** (부활).
  - after — 두 경우 모두 리로드 후 `hasSave: false`, `meta: null`, `CONTINUE` → 상태 없음(타이틀 유지).
  - 기록: `docs/design/death-retires-run-2026-11-03/`.
- vitest **181 files / 4014 tests passed** · tsc 0 · eslint 0 errors · build PASS.

**Notes**:

- 죽음 화면은 여전히 `ENTER`/`ESC` 로 나온다(ADR-0263) — 슬롯 retire 는 그와 독립이다.
- ADR-0252 §A 의 문장("death frames are written")은 이 ADR 로 뒤집혔고, 그 ADR 의
  `## Implementation Status` 에 갱신 주석을 달았다(결정 내용은 불변이므로 신규 ADR 로 처리).

## 열린 질문

- **(a) 죽음 화면 재표시.** 죽고 나서 다시 그 화면을 보고 싶다면 Option B(슬롯에 `runOver` 저장)가 필요하다.
  현재는 타이틀 상태줄(`Flatline — back at the title.`)만 남는다.
- **(b) 죽음 기록 보존.** `deceasedJockeys`/`lastDeathSummary` 는 슬롯에 없다. HALL OF DEAD 를
  실제 아카이브로 만들려면 별도 영속(ADR-0040 Option A 의 Archive)이 필요하다.
- **(c) COST 상한 안내.** 전투에서 COST 가 상한이면 프로그램이 전부 `BLOCKED` 이고 남은 출구는
  `ESC`(런 실패)뿐이다. 캡 도달 시 HUD 한 줄로 알리는 것이 ADR-0251 §5 정신에 맞다(별도 슬라이스).

## 영향 받는 항목

- `web/src/core/state/run_end.ts` — `autosaveIntent`
- `web/tests/run_end_save.test.ts` — 죽음 프레임 기대값
- `docs/wiki/decisions/0252-run-end-and-save-timing.md` — Implementation Status 갱신 주석

## 관련 결정

- ADR-0252 (런 종료/저장 시점 — 이 ADR 이 죽음 케이스를 정정) · ADR-0263 (죽음 화면 탈출) ·
  ADR-0040 (죽음/재시작 사이클) · ADR-0185 (세이브 마이그레이션 — 스키마 무변경이므로 불필요)

## 변경 이력

- 2026-11-03: 오너 선택(A) → Draft 작성 · 구현 완료 · 실측 before/after
