# ADR-0248: 두 alarm 계기의 명칭 분리 — COST와 TRACE (a0)

**상태**: Accepted
**날짜**: 2026-11-01
**결정자**: 사용자 (프로젝트 오너) — a0 명칭 분리 직접 지정
**우선순위**: P2 (The Style — 플레이어 표시 혼동 결함)
**관련**: [ADR-0240 열린 질문 (k)](./0240-idle-pressure-and-alarm-loop.md#open-questions) · [ADR-0246 선행 조건](./0246-dungeon-role-and-run-interaction.md#선행-조건) · [ADR-0195](./0195-adr-implementation-workflow.md) · [ADR-0239 기준선](./0239-vfx-spawn-rng-decoupling.md) · [디자인 기둥](../../design/pillars.md)

## 컨텍스트 (Context)

플레이어는 서로 반대의 원인으로 올라가는 두 계기를 모두 alarm으로 보았다.
`player.alarm` (0–100)은 프로그램을 쓸 때 쌓이는 행동 비용이고, `alarmLevel` (0–5)은
아무것도 하지 않을 때 쌓여 적을 강화하는 유휴 압력이다. 실제 결함은 두 메커닉의
존재가 아니라 **같은 이름 때문에 플레이어가 둘을 구분할 수 없다는 것**이다.
명확한 위험 표시(P1)와 명료한 표현(P5)을 위해 이름부터 구별한다.

## 옵션 비교와 결정 (Decision)

| 안 | 효과 | 결정 |
| --- | --- | --- |
| **(a0) 명칭만 분리** | 행동 비용은 COST, 유휴 압력은 TRACE. 규칙·저장·밸런스 그대로 | **채택·구현** |
| **(a) 표시 통합** | 하나의 가시 위험 계기로 표시; 두 값의 관계·효과 정의가 필요 | **Deferred — 보류, 이번에 채택하지 않음** |
| **(b) 메커닉 병합** | 숙고로 쌓인 위험이 프로그램 사용 가능성에도 관여 | **별도 설계 결정으로 기각** — 숙고와 행동 능력을 결합하며 재기준화(re-baseline)가 필요 |

두 메커닉은 **UNCHANGED**, 병합하지 않는다. 표시만 다음과 같이 바꾼다:

- `Alarm N/100` → **`COST N/100`**: 프로그램 비용 누산기. 100을 초과할 프로그램은 실패.
- `ALARM N/5` → **`TRACE N/5`**: 유휴 압력. tick 피드백도 `TRACE N/5`로 통일.
- 프로그램 실패·튜토리얼·진입 힌트·프로그램/뮤테이터 설명도 같은 어휘를 사용한다.

`player.alarm`, `alarmLevel`, `lastAlarmTickMs` 등 상태 필드·세이브 스키마는 그대로 둔다.
10초 임계·10초 간격·상한 5·피해 +4%/레벨·스킬 확률 +1pp/레벨도 불변이다.

## 결과 (Consequences)

- 행동 비용과 유휴 비용이 이름으로 구분된다. 혼동 제거가 실제 결함 수정이며 자원 추가가 아니다.
- ADR-0240 (k)의 이번 답은 a0다. 표시 통합 (a)을 구현한 것으로 주장하지 않는다.
- ADR-0246의 **새 자원 이전 하나의 가시 위험 계기** 선행 조건은 아직 충족되지 않았다.
  a0는 명칭 결함만 해결하며, 통합·새 자원·던전 변경을 승인하지 않는다.
- ADR-0240/0246/0247의 Accepted 결정 본문은 수정하지 않는다. 통합 재검토는 별도 결정이 필요하다.
- 튜토리얼의 기존 “100 = flatline” 문구는 기존 코드의 실제 초과 비용 실패 규칙으로 설명한다.
  HOT TRACE 뮤테이터의 설명도 실제 `double_alarm` 프로그램 비용 배율을 COST로 설명한다.

## Implementation Status (2026-11-01)

**Status**: ✅ Implemented — a0 명칭 분리만 적용 (미커밋 작업 트리).

**Evidence**:
- `web/src/core/state/state.ts:201,210` — COST / TRACE HUD. TRACE 0의 기존 숨김 동작 유지.
- `web/src/core/combat/combat_engine.ts:211` — tick 피드백 `TRACE N/5`.
- `web/src/core/combat/state_actions_programs.ts:62` — `Cost too high — program failed`; 비용 판정 불변.
- `web/src/renderer/tutorial.ts:53,57`, `web/src/core/state/onboarding.ts:74` — COST 설명.
- `web/src/core/state/starter_deck.ts:98`, `web/src/core/state/run_mutators.ts:68` — 설명 어휘 정합.
- `web/tests/state.test.ts:177`, `web/tests/combat_engine.test.ts:434`, `web/tests/menu_stage_combat_flow.test.ts:533` — 새 표시 문구 직접 단언; 값·실패 결과 단언 유지.
- `web/tests/screen_frames.test.ts:267`, `web/e2e/idle_alarm.spec.ts:43` — 40×60/60×40/80×50 프레임·TRACE 피드백 회귀와 실제 rAF 메시지 단언.

**Notes**: ADR-0195 Status / Evidence / Notes 형식. 메커닉·튜닝·RNG·저장 필드 무변경.
검증 명령의 실제 결과는 아래에 기록한다. 크롤러 자체 alarm, `core/status.ts`, VFX 구현, `raw/`는 범위 밖이다.

## 검증 기록

- 변경한 `src/**` 7개 파일만 `npx prettier --write` 후 `--check` 통과. repo-wide format 실행 없음.
- `npm run typecheck` — exit 0, 타입 오류 0.
- `npm run lint` — exit 0, 오류 0 / 기존 `web/src/input/keyboard.ts:14` 경고 1개.
- `npm test` — **161 files / 3664 passed / 0 failed** (기준 3658 + 회귀 6).
  첫 실행에서 기존 onboarding의 `flatline` 단언 1건이 실패하여 새 COST 제한 문구 전체 단언으로 갱신;
  다음 전체 실행 통과. 기존 HP·비용·tick·덱 단언은 삭제/완화하지 않았다.
- `npm run build` — 통과, Vite 5.4.21 / 117 modules / 472ms.
- `npm run balance` 및 `npm run balance -- --deck ppl` — 수정 전후 **전체 stdout `cmp` exit 0**.
  ADR-0239 opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`,
  PPL `100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7` 유지. 턴·HP·percentile도 전후 동일.
- E2E: `npx vite preview --port 5195 --strictPort --host 127.0.0.1` 후
  `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots`
  → **76 passed / 4 skipped / 0 failed (4.4m)**. finally에서 preview 프로세스 그룹 종료.
- LSP diagnostics는 TypeScript 서버 미설치·기존 설치 거절로 실행 불가. 설치/우회하지 않았으며 LSP clean을 주장하지 않는다.
- diff 검토: 프로덕션 TS 변경은 **표시 문자열 9개뿐**. 추가 상태/도우미/분기/의존성/타입 escape hatch 없음.

### 밸런스 stdout (공통 npm 실행 헤더 제외)

```text
Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 0ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         42.7   29/57
    3        11     70.5%     0.0%         6.8         13.8    4/30
    4        10     39.5%     0.0%         6.5          5.3    0/14
    5         9     36.2%     0.0%         5.8          4.9    1/12
    6         3      0.0%     0.0%         5.2          0.0    0/0

Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 0ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.9   28/45
    3        11     98.9%     0.0%         5.7         30.2   19/39
    4        10     83.0%     0.0%         5.9         22.1   11/29
    5         9     44.4%     0.0%         5.2         15.3   11/18
    6         3     24.7%     0.0%         5.2          1.2    0/2
```

## 변경 이력

- 2026-11-01: 오너 지정 a0 채택·구현. 두 alarm의 명칭을 COST/TRACE로 분리하여 혼동 제거.
  (a) 표시 통합 Deferred, (b) 병합 기각·재기준화 필요를 명시. 기존 Accepted 결정 본문 불변, stage/commit 없음.
