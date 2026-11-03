# 죽음은 런을 끝낸다 (2026-11-03)

[ADR-0264](../../wiki/decisions/0264-death-retires-the-run.md) 의 실측 증거다.
[ADR-0263](../../wiki/decisions/0263-defeat-screen-must-be-escapable.md) 을 처리하다 발견했다.

## 무엇이 문제였나

`SaveSlot` 에 **`runPhase` 가 없고**, `slotToGameState` 가 **모든 저장을 `runPhase: "matrix"` 로**
복원한다. 그래서 죽음 프레임을 write 로 두면 죽음이 되살아난다.

| 죽음 | 사망 직후 | 리로드 → `CONTINUE` (before) |
|---|---|---|
| **HP 0 (FLATLINE)** | `runPhase dead` / hp 0 / node 18 | `runPhase matrix` / **hp 0** / 도착 조우 재개방 → 플레이 불가능한 유령 보드 |
| **JACK OUT** | `runPhase dead` / hp 40 / node 18 | `runPhase matrix` / **hp 40** → **부활** (죽음의 대가 소멸) |

잭아웃은 전투에서 `ESC` 한 번이고, COST 가 상한이면 그게 유일한 출구다 — 즉 **죽기 직전에 ESC 하고
새로고침하면 그대로 살아난다.**

부수 확인: `deceasedJockeys`·`lastDeathSummary` 는 슬롯에 없다(`slotToGameState` 가 `[]`/`null` 로
시작). 죽음 기록은 원래부터 휘발이므로, 죽음 프레임을 저장해도 잃을 기록이 없다.

## 바뀐 것

```ts
// web/src/core/state/run_end.ts
return state.runPhase === "ending" || state.runPhase === "dead"
  ? "retire"
  : "write";
```

## 이 폴더의 파일

| 파일 | 무엇 |
|---|---|
| `before.txt` | 수정 **전** 빌드(커밋 `3b937caa`)에서 같은 프로브를 돌린 기록 |
| `after.txt` | 수정 **후** 빌드에서 같은 프로브를 돌린 기록 |

프로브 스크립트: 실제 전투에서 ① HP 0 사망 ② 잭아웃 사망을 만들고, 각각
**리로드 후 `hasSave`/`meta` 와 `CONTINUE` 복원 결과**를 읽는다(독립 headless Chromium, preview 5195).

`before.txt` 는 `hasSave: true` + `CONTINUE` 가 죽은 런을 매트릭스로 되살리는 것을,
`after.txt` 는 두 경우 모두 `hasSave: false` + `CONTINUE` 무동작을 보여준다.
