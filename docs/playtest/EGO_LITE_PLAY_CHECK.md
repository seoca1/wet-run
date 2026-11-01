# ego-lite 실제 플레이 점검 (Real-Play QA)

**목적**: Playwright e2e 를 **대체하지 않고 보완**한다. Playwright 는 결정적 회귀
게이트이고, 이 절차는 **실제 Chromium 에서 렌더와 조작을 눈으로 확인**한다.

**왜 둘 다 필요한가**: ego-lite 에는 **가짜 시계(fake clock) API 가 없다**. `clock`,
`fake`, `emulate` 계열 API 를 제공하지 않고 `waitForTimeout` 과 `timeout` 옵션만
있다. 그래서 `web/e2e/idle_alarm.spec.ts` 의 "20,050ms 유휴 → alarm 2" 같은 단언은
`page.clock` 이 있어야 하고, 없으면 **실제 20초를 기다려야** 한다. 이 게임은 유휴
임계 10초·알람 간격 10초처럼 **시간 게이트 메커니즘**이 핵심이므로 시간 제어가
빠지면 게이트가 관찰로 전락한다.

역할 분담:

| 역할 | 도구 | 이유 |
| --- | --- | --- |
| 회귀 게이트 | **Playwright** | 시드 결정성 · `page.clock` · `expect()` 단언 · 2개 뷰포트 · CI |
| 실제 플레이·느낌 확인 | **ego-lite** | 실제 렌더, 실제 키 입력, 실제 스크린샷. CI 불가 |

**언제 실행**: 밸런스 수치, 시간 게이트(유휴·알람·Dixie), UI 프레임·HUD 를 바꾼 뒤.

> 이 절차는 보완용이므로 실패해도 코드 회귀는 아니다. 값이 아니라 **눈으로 보는
> 것**이 목적이므로, 아래 체크리스트를 사람이 판단한다.

## 0. 전제

```bash
export PATH="$HOME/.local/bin:$PATH"   # opencode 는 최소 PATH 로 뜰 수 있다
command -v ego-browser
```

`ego-browser` 가 없으면 ego-lite 앱 설치와 온보딩이 먼저다. 에이전트 표면은
**`ego-browser nodejs` 하나뿐**이다 (공식 MCP 없음, 공개 CDP 포트 없음).

## 1. 서버

```bash
cd web
npm run build
npx vite preview --port 5195 --strictPort --host 127.0.0.1
```

`--host 127.0.0.1` 은 **필수**다. 없으면 IPv6 전용으로 바인딩되어 `127.0.0.1` 접속이
실패한다. `npm run dev` 도 가능하지만 포트를 맞춰야 한다.

## 2. 세션 시작과 전투 도달 (검증된 스크립트)

한 번의 `ego-browser nodejs` 호출로 처리한다. 아래 스크립트는 **실제로 전투까지
도달함을 확인했다** (menu → mission_select → combat).

```bash
ego-browser nodejs <<'EOF'
const task = await taskSpace("wet_run real-play QA");
const page = task.page("p1");
const T = (ms) => page.waitForTimeout(ms);
const press = (k) => page.keyboard.press(k);
const st = () => page.evaluate(() => {
  const s = window.wetrun?.state;
  return { screen: window.wetrun?.getScreen?.() ?? null,
           phase: window.wetrun?.getPhase?.() ?? null,
           runPhase: s?.runPhase ?? null, alarm: s?.alarmLevel ?? null,
           hp: s?.player?.hp ?? null, lead: s?.iceRoster?.[0]?.hp ?? null,
           deck: s?.deck?.length ?? null };
});

await page.goto("http://127.0.0.1:5195/", { waitUntil: "load", timeout: 30000 });
// 튜토리얼을 건너뛴다 (e2e 와 동일한 플래그). addInitScript 가 없으므로 reload 를 쓴다.
await page.evaluate(() => localStorage.setItem("wetrun_tutorial_completed", "true"));
await page.reload({ waitUntil: "load" });
await page.waitForFunction(() => window.wetrun !== undefined, undefined, { timeout: 20000 });
console.log("menu: " + JSON.stringify(await st()));

const isScreen = (w) => page.evaluate((x) => window.wetrun?.getScreen?.() === x, w);
const isRunPhase = (w) => page.evaluate((x) => window.wetrun?.state?.runPhase === x, w);
const isPhase = (w) => page.evaluate((x) => window.wetrun?.getPhase?.() === x, w);

// NEW RUN → 미션 선택
for (let i = 0; i < 8 && !(await isScreen("mission_select")); i++) { await press("Enter"); await T(700); }
// 미션 발사 → 매트릭스
for (let i = 0; i < 8 && !(await isRunPhase("matrix")); i++) { await press("Enter"); await T(700); }
// ICE 가 있는 노드까지 전진 (노드 0 은 encounter 가 없을 수 있다)
for (let i = 0; i < 30; i++) {
  const hasIce = await page.evaluate(() => {
    const s = window.wetrun?.state;
    const n = s?.matrix?.nodes?.[s?.currentNodeIndex ?? -1];
    return (n?.iceIds?.length ?? 0) > 0;
  });
  if (hasIce) break;
  await press("ArrowDown"); await T(200);
}
// 교전 (2단계: 진입이 runPhase combat 을 세우고, 두 번째 confirm 이 실제 교전)
for (let i = 0; i < 6 && !(await isRunPhase("combat")); i++) { await press("Enter"); await T(700); }
for (let i = 0; i < 6 && !(await isPhase("combat")); i++) { await press("Enter"); await T(700); }
await T(600);

console.log("combat: " + JSON.stringify(await st()));
await page.screenshot({ path: "/tmp/wetrun-combat.png" });
await task.finish({ keep: ["p1"] });
EOF
```

`waitForFunction` 의 옵션은 **세 번째 인자**다. `page.waitForFunction(fn, timedOutValue, { timeout })` — 두 번째 인자를 `undefined` 로 넘겨야 한다.

### 왜 이렇게 하는가

- **`window.wetrun` 이 자동화 표면이다**: `getScreen()`, `getPhase()`, `getMenuOptionKeys()`,
  `getSelectedMenuIndex()`, 그리고 `state.runPhase` / `state.matrix.nodes` /
  `state.currentNodeIndex`. e2e 헬퍼(`web/e2e/menu-nav.ts`)와 같은 표면이므로 두
  도구가 같은 계약을 본다.
- **고정 키 횟수를 쓰지 않는다**: 메뉴에 항목이 삽입되면 깨지므로, 목표 화면/단계가
  될 때까지 Enter 를 눌러 올린다.
- **교전은 2단계다**: 노드 진입이 `runPhase` 를 `combat` 으로 만들지만 `getPhase()` 는
  `approach` 로 남는다. 두 번째 confirm 이 실제 교전이다.

## 3. 관찰 체크리스트

스크린샷과 우측 상태 패널을 눈으로 본다.

- [ ] 상단 프레임과 헤더가 화면을 벗어나지 않는가 (ADR-0237 프레임 언어)
- [ ] `P [게이지] HP/maxHP` 에서 **HP 가 maxHP 를 넘지 않는가**
- [ ] ICE 표기가 `hp/maxHp` 로 모순되지 않는가
- [ ] 우측 패널의 `Alarm N/100` 과 `ALARM N/5`(HUD)이 서로 맞는가
- [ ] 전투 중 4~5초 멈춰 있다가 다시 입력하면 알람이 오르는가 (10초 임계)
- [ ] Dixie 발동이 **입력 횟수**에 달려 있는가 (기다린 시간에 달려 있으면 회귀)
- [ ] 카드 1~5 를 눌러 실제로 피해가 들어가고 HAND 가 줄어드는가
- [ ] 프레임/텍스트가 잘리거나 겹치지 않는가

실제 조작은 `page.keyboard.press("1")` ~ `"5"` 로 카드를 쓰고, `ArrowUp/Down` 으로
대상을 바꾼다.

## 동사 경제 검증

대상은 [ADR-0246](../wiki/decisions/0246-dungeon-role-and-run-interaction.md)의 고정 동사다.
가격의 원문은 `web/src/core/state/encounter_verbs.ts`의 `ENCOUNTER_VERB_COSTS`:
PROBE 8 COST, BYPASS 60 COST (2026-11-01 오너 결정). COST는 런 중 증가만 하고 상한이
100이므로 BYPASS는 런당 최대 한 번이다. 두 번째는 120 > 100으로 거절된다.
`balance_sim.ts`는 그래프를 걷지 않으므로 가격의
비지배성을 검증하지 못한다. 아래는 **실제 선택의 관찰**이며 자동 밸런스 판정이 아니다.

### 플레이 중 답할 질문

- [ ] HP가 넉넉한 상황과 죽기 직전, COST 여유가 큰 상황과 작은 상황을 모두 봤는가?
  각 노드에서 지불 **전** COST/HP, 보상, eventKind, ICE 수와 선택 이유를 적는다.
- [ ] BYPASS가 상황과 무관하게 명백한 정답이 되는가? 60을 내고 포기한 보상·회복보다
  보존한 HP와 다음 경로가 실제로 더 중요했는가? 반대로 안 내는 편이 나았던 사례는?
- [ ] BREACH가 상황과 무관하게 명백한 정답이 되는가? 전투 후 COST/HP와 보상을 보고도
  위험한 노드에서 BYPASS를 고를 이유가 남는가? 생존과 다음 노드의 프로그램 여유도 비교한다.
- [ ] PROBE가 낭비였던 적이 있는가? 이미 방문해 알고 있던 정보, 또는 무엇이 나와도
  같은 동사를 골랐을 상황에 8을 냈는가? 공개 전 예상 동사와 공개 후 실제 동사를 적는다.
- [ ] frontier의 ICE 수·보상·eventKind만 보고, 정확한 HP는 숨겨진 채로도 **지불 전**
  의미 있는 선택을 할 수 있는가? PROBE 없이도 감수할 위험을 설명할 수 있는가?
  공개 뒤의 지식을 공개 전 판단에 소급 적용하지 않는다.
- [ ] PROBE의 8이 다음 프로그램/BYPASS를 막은 사례가 있는가? BYPASS의 60이 이후
  생존을 막았는가, 아니면 전투 회피가 런을 이어 주었는가? 노드 통과 뒤 실제 이동까지 관찰한다.

### 비지배성을 반증하는 관찰

한 번의 쉬운 전투나 한 번의 실수만으로 보편적 지배를 증명할 수는 없다. 조건이 다른
반복 사례를 남기고, 비교하지 않은 대안은 미확인으로 둔다. 다음은 가격 재검토가 필요한 실패 신호다.

| 동사 | 실패로 기록할 구체적 관찰 |
| --- | --- |
| PROBE | 정보가 필요 없던 쉬운 노드·재방문에서도 항상 먼저 누르고, 8 때문에 포기하는 후속 행동이 전혀 없다면 너무 싼 필수 세금일 수 있다. 반대로 공개가 선택을 바꾸거나 손실을 피하게 한 사례 없이 매번 같은 선택에 8만 더 냈다면 PROBE가 지배당하는 신호다. |
| BYPASS | 낮은 HP·많은 ICE에서도 BREACH 후 손실이 60보다 작고 보상·회복까지 받아, 지불 가능한 BYPASS를 합리적으로 고를 사례가 없다면 60 COST는 너무 비싼 신호다. HP와 COST는 다른 단위이므로 이 수치 비교만으로 판정하지 않는다. 반대로 보상·회복이 중요한 쉬운 노드에서도 항상 BYPASS 후 런 결과가 더 좋다면 BYPASS가 다른 선택을 지배하는 신호다. |
| BREACH | HP·COST·보상·위험이 달라도 항상 BREACH가 생존과 다음 행동 여유에서 낫다면 BYPASS의 자리가 없다. 반대로 높은 보상·쉬운 전투에서도 싸움이 생존/자원/진행 어느 쪽에서도 이득을 주지 못하고 매번 BYPASS가 낫다면 BREACH가 지배당하는 신호다. |
| JACK OUT | 어떤 감당 불가능한 전투에서도 60 지불이 불가능하거나 나쁜데도 런 포기가 합리적인 선택이 되지 않는다면 탈출 선택의 역할을 재검토한다. 정상적인 유리한 노드에서도 계속 포기가 최선이라면 전반적인 진행 경제 실패 신호다. |

### 수동 플레이를 방해하지 않는 기록기

소스: [ego-decision-recorder.mjs](./ego-decision-recorder.mjs).
`.mjs`를 쓴 이유는 ego의 Node ESM 표면에서 빌드·TS 로더·추가 의존성 없이 import하기 위해서다.
ego의 Node 24+ native type stripping으로 순수 `iceHpForGrade`/`missionGradeOf`를 읽기 전용
import한다. [상태 추출 모듈](./ego-decision-state.mjs)은 빈 `iceHp`도 게임과 같은 계산으로 처리한다.
`recordDecisions(options, { taskSpace, listTaskSpaces })`의 인자로 경로와 Space ID를 전달한다.
이미 플레이 중인 **허가된 agent 소유 Space**의 숫자 ID와 Page 라벨을 사용한다.
없는 Space를 만들거나 user 소유 Space를 claim하지 않는다. `wet_run real-play QA`는
사용자 소유이므로 건드리지 않는다. 사람이 입력하더라도 Space의 제어권이 user로 바뀌면
기록기는 중단하며, 자동 탈환하지 않는다. 먼저 자신의 고유 이름 Space에서 런을 시작하고,
종료 전 `finish`하지 않은 상태에서 기록기를 붙인다.

서버가 없을 때만 §1의 두 명령을 실행한다. 현재 `http://127.0.0.1:5195/`가 열려 있으면
재실행·재빌드·종료하지 않는다. 별도 셸에서 다음 호출을 실행하고 그동안 사람이 플레이한다:

```bash
export PATH="$HOME/.local/bin:$PATH"
ego-browser nodejs <<'EOF'
const { recordDecisions } = await import("/Users/emilio/projects/opencodework/Game/wet_run/docs/playtest/ego-decision-recorder.mjs");
await recordDecisions({
  spaceId: 39, // 예시: 자신의 아직 종료하지 않은 Space 숫자 ID로 교체
  pageLabel: "p1",
  outputPath: "/Users/emilio/.openclaw/tmp/opencode/wet-run-verbs-pass-01.md",
  durationMs: 60000,
  intervalMs: 100,
}, { taskSpace, listTaskSpaces });
EOF
```

출력 폴더는 미리 존재해야 하고 경로는 절대 경로여야 한다. 위 예시는 Markdown과
`wet-run-verbs-pass-01.md.json`을 같은 폴더에 쓰고 동사별 행 수를 출력한다.
기존 파일은 덮어쓰지 않으므로 매 pass마다 새 이름을 쓴다. 기록기는 **상태 polling만** 하며
키·마우스·탐색·상태 쓰기·`finish`를 하지 않는다. 플레이를 마친 소유자가 §4대로 정리한다.

해석 규칙과 한계:
- 노드 index는 상태와 같은 **0-based**다. 화면 노드 번호는 여기에 1을 더한다.
- COST는 `player.alarm`이며 TRACE의 `alarmLevel`이 아니다. 두 credits 원장
  `player.credits`/`inventory.credits`를 모두 남긴다.
- `encounterDecision.selectedVerb`는 강조일 뿐이다. PROBE는 `probed: false → true`,
  BYPASS는 메뉴 종료와 `bypassedEncounterNodeIndex`, BREACH는 메뉴 종료와 전투 진입,
  JACK OUT은 메뉴 종료와 run의 menu/exit 전이로 확인한다. 거부된 confirm은 행이 아니다.
- PROBE와 그 뒤 BYPASS/BREACH는 별도 행이다. BREACH의 차이는 첫 clear/종료 관찰까지이며
  clear 뒤 loot confirm의 회복은 포함하지 않는다. 전투 진입과 실제 `phase: combat`을 구분한다.
- ICE 정체/HP는 **PROBE 후에만** 기록한다. `iceHp`가 비었으면 실제 게임의 순수 scaling 함수를 재사용한다.
  clear/bypass는 해당 방문의 결과, Continued는 이후 다른 노드로 실제 이동했는지다.
- 인과 추적기가 아니라 두 표본 사이 차이다. 100ms polling이면 각 입력 사이 최소 300ms를
  두고 메뉴 열기·PROBE·최종 선택·loot를 구분한다. 빠른 연속 입력은 중간 결정을 놓칠 수 있다.
  관찰 시작 전 지불은 복원하지 않는다. clear 표본을 놓치면 회복이 섞일 수 있다.
  `pending`/`incomplete`/`unknown`은 관찰 부족이며 실패·미계속으로 단정하지 않는다.
  재시작은 null 상태·런 식별 값 변경·turnCount 감소로 구분하지만 표본 사이 같은 런 재시작은 놓칠 수 있다.

파서 회귀 검증은 브라우저 없이 `node --test docs/playtest/ego-decision-recorder.test.mjs`로 실행한다.
상태 계약 출처: `web/src/core/types.ts`의 `encounterDecision`/`bypassedEncounterNodeIndex`,
`web/src/core/state/state_actions_phases.ts`의 메뉴 개방·이동,
`web/src/core/state/encounter_verbs.ts`의 confirm 결과,
`web/src/core/state/state.ts`의 clear 기록.

## 4. 정리

```js
await task.finish({ keep: [] });   // 공간을 닫는다
```

`keep: []` 는 알려진 CDP teardown 문제로 **exit 1** 을 낼 수 있지만 공간은 닫힌다.
종료된 공간은 **사용자 소유로 넘어가므로 되찾지 않는다**(`claimTaskSpace` 는 사용자가
명시적으로 승인할 때만). 다시 점검할 때는 **다른 공간 이름**을 쓰는 편이 빠르다.
공간 이름은 고유하므로 같은 이름을 재사용하면 이전 공간에 이어붙는다.

## 알아둘 점

- **`window.wetrun.state` 는 메뉴 화면에서 null 이다.** 상태를 읽으려면 전투까지
  들어가야 한다.
- **새 런 전투에서 `getScreen()` 은 여전히 `mission_select` 를 반환한다.** 화면 종류로
  판정하지 말고 `runPhase`/`getPhase()` 로 판단한다 (ADR-0240 구현 중 발견).
- 스크린샷은 절대 경로로 저장한다. 스크립트는 셸의 작업 디렉터리와 환경 변수를
  물려받지 않는다.

## 한계

- **헤드리스가 아니다** — 보이는 앱이므로 CI 에 넣을 수 없다.
- **가짜 시계가 없다** — 시간 게이트는 실제로 기다려야 한다. 그래서 결정적 회귀는
  Playwright 가 담당한다.
- **단언 레이어가 없다** — 이 절차는 합격/불합격이 아니라 사람의 관찰이다.

## 이 절차로 실제로 잡은 것 (예)

2026-11-01 첫 실행에서 발견한 두 건은 **확정된 표시 결함이며 수정 완료**다
([ADR-0245 — 원인·수정·회귀 테스트·실측 증거](../wiki/decisions/0245-combat-hud-display-defects.md)):

- **ICE `165/100`**: renderer가 최대 HP를 `100`으로 하드코딩했다. 실제 상태는
  `hp=165, maxHp=165`로 정상이었다. 게이지·분모·색상을 `ice.maxHp`로 통일해
  `165/165`로 표시하며, 절반 HP에서는 게이지도 절반만 찬다.
- **`Equipped: 10/8`**: `Object.values(loadout)`이 슬롯 맵과 메서드 9개를 세었다.
  실제 채운 슬롯은 `allSlotsFilled().length`, 분모는 `EQUIP_SLOTS.length`로 바꿔
  `Equipped: N/8`로 표시한다.

둘 다 기존 단언이 아니라 **실제 화면을 봐서** 발견했다. 신규 회귀 16건과
typecheck/lint/test/build 및 Playwright E2E를 통과했고, 양 덱 no-idle 승률은
ADR-0239 대비 전 grade **0.0pp**다. 게임플레이·AI·RNG는 변경하지 않았다.
수정 후 ego-lite 재플레이는 이번 수정 세션에서 수행하지 않았다.
