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

2026-11-01 첫 실행에서 상태는 정상이었지만 렌더에서 두 가지가 눈에 띄었다:
ICE 표기가 `165/100`(HP 가 최대치를 초과), 우측 패널의 `Equipped: 10/8`. 둘 다
단언이 아니라 **화면을 봐서** 발견한 것이며, 이 절차의 목적을 그대로 보여준다.
