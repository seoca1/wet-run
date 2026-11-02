# ADR-0252: 세이브는 확정된 상태를 담고, 엔딩은 런을 끝낸다 — 자동 저장 시점과 런 완료

**상태**: Accepted
**날짜**: 2026-11-02
**결정자**: 사용자 (프로젝트 오너) — "모두 수정해." (A·B·C 수정 승인, B의 완료 정책은 구현자 판단으로 위임)
**우선순위**: P1 (런 완료 불가 + 강제 재전투로 패배)
**관련**: [ADR-0250 — 조우 게이트를 입구로](./0250-encounter-gate-on-entry.md) · [ADR-0246 — 던전의 역할과 런 인터랙션](./0246-dungeon-role-and-run-interaction.md) · [ADR-0217 — CONTINUE가 플레이 가능한 런을 복원](./0217-continue-restores-playable-run.md) · [ADR-0209 — IDB 저장 백엔드](./0209-wetrun-web-idb-save-backend.md) · [ADR-0185 — 저장 마이그레이션](./0185-save-migration-v2.md) · [ADR-0195 — 구현 상태 기록](./0195-adr-implementation-workflow.md)

> **이 ADR은 ADR-0250·0246의 결정을 바꾸지 않는다.** "로드는 도착으로 친다"(ADR-0250)는 그대로이며,
> 이 ADR은 그 규칙이 가정하던 것 — 세이브가 플레이어가 확정한 상태를 담는다 — 을 실제로 성립시킨다.
> 가격·피해·RNG·던전·Matrix 게이트·전투 무결성 규칙(ADR-0251)·세이브 스키마 버전은 불변이다.

## 컨텍스트 (Context)

### 오너 보고

> "맵에서 보스를 쓰러뜨린후 이동하려니 또 보스가 나와서 회복 못하고 패배하게 되던데."

### 재현 (5195 빌드 `index-B_nl8RTM.js`, 실제 키)

부트 미션 Aleph Fragment, 경로 0 → 25 → 16 → 18(ICE) → 20(보스, 유일한 출구 18).
[before trace](../../design/run-end-and-save-2026-11-02/live/before-owner-5195-trace.txt):

| 단계 | 메모리 상태 | 저장 슬롯 (IDB에서 직접 디코드) |
| --- | --- | --- |
| 25·16 이동 | `cur 25`, `cur 16` | **없음** — 전투 전에는 한 번도 저장되지 않는다 |
| 18 격파 → loot | `clr [18]`, cr 4500 | `clr []`, cr 0 (격파 직전 전투 프레임) |
| 보스 격파 → loot → ending | `clr [18,20]`, hp 63, cr 10600 | `clr [18]`, cr 4500 (보스전 중 프레임) |
| 엔딩에서 Enter, Enter, Esc | `ending / menu` 그대로 | — |
| 리로드 → CONTINUE | 보스 노드, 결정 열림, BYPASS `blocked here` | — |
| BREACH | **`wintermute 140/140`**, `Combat vs ICE — Standard` | (실전은 165/165, `ICE — Yakuza Enforcer`) |

세 결함의 결합:

1. **자동 저장이 전투 중에만 돈다.** `main.ts draw()`의 `matrix/ending/loot` 분기가 `autosave()` 전에 반환한다.
   격파 키 입력은 `runPhase: "loot"`를 만들므로 그 상태는 저장되지 않고 슬롯은 그 직전 전투 프레임을 유지한다.
2. **엔딩 화면이 막다른 길이다.** `applyEndingAction`은 `phase: "menu"`만 바꾸고 `runPhase: "ending"`을 남긴다.
   컨트롤러는 그 상태를 버리지 않으므로 모든 입력이 계속 엔딩으로 간다. 플레이어는 새로고침할 수밖에 없다.
3. **CONTINUE가 다른 ICE로 전투를 다시 만든다.** 복원은 카탈로그 첫 ICE(`standard`)를 기반 ICE로 쓰고,
   `encounterRoster`는 그 기반을 id만 바꿔 펼친다. 실전은 미션 ICE(`yakuza_enforcer`) 기반이다.

결과: 리로드 + CONTINUE는 ADR-0250의 "로드 = 도착"으로 보스 결정을 열고, 보스에선 BYPASS가 막혀 있으며,
BREACH는 만피 새 전투를 시작한다. 종결 경로는 15% 회복이 없다. 플레이어는 진다.

## 결정 (Decision)

### 1. 세이브 시점 규칙 — 세이브는 확정된 상태를 담는다

자동 저장(슬롯 0)은 **렌더된 모든 런 프레임**에서 쓴다: Matrix(이동 확정·조우 결정), loot, 전투, 사망.
"마지막 전투 프레임"이 아니라 **플레이어가 마지막으로 확정한 상태**가 슬롯에 있어야 한다.
전투에서 저장하는 내용은 바뀌지 않는다.

- 저장·삭제는 **순서가 보장된 큐**로 실행한다. 늦게 끝난 이전 쓰기가 이후 삭제를 덮지 못한다.
- 세이브 슬롯 내용은 그 프레임의 스냅샷이다(쓰기 시점이 아니라 렌더 시점).
- 런 도중 `screen`이 `"menu"`인 경우(CONTINUE 후) 저장 → 캐시 갱신 → 다시 그리기 → 저장의 루프가 생기므로,
  캐시 갱신은 런 상태가 없을 때만 제목 화면을 다시 그린다.

### 2. 런 완료 — 엔딩은 런을 끝낸다

- **엔딩 도착 시 자동 저장 슬롯을 폐기한다.** 미션 완료 기록·팩션·Far Grid 판정은 이미 loot 확정에서 끝났다.
- **엔딩 화면에서 Enter 또는 ESC** → 런 상태를 버리고 제목 화면으로 간다(`runAbandoned`가 만드는 것과 같은 종료 상태).
  이후 어떤 입력도 엔딩으로 가지 않는다. 엔딩 footer는 `ENTER / ESC: return to title`(이전 `ENTER: continue | ESC: back`은 사실이 아니었다).
- 제목 화면 상태줄에 `Run complete. Autosave cleared.`를 띄운다(같은 세션).

### 3. 완료 후 CONTINUE가 보이는 것

**완료한 런은 재개할 수 없다.** 엔딩에 도착한 순간 슬롯이 비므로, 제목 화면의 CONTINUE는 새 프로필과 똑같이
`CONTINUE (no save)`(회색)이고 `→ mission (turn N)` 힌트가 없으며, 눌러도 아무 런도 열지 않는다.
다음 새 런이 첫 프레임을 저장하면 CONTINUE가 다시 그 런을 가리킨다.

**이유** — 플레이어의 기대: 엔딩을 본 런은 끝났다. 끝난 미션을 중간부터 다시 여는 것(현재 동작)은 그 기대를 깨고,
이번 보고처럼 이미 이긴 보스를 다시 싸우게 한다. 대안 "마지막 세이브를 남겨 둔다"는 이번 버그 그 자체이며,
"완료 기록을 슬롯에 남겨 CONTINUE가 엔딩을 다시 보여 준다"는 스키마 필드와 화면이 새로 필요하고 얻는 것이 없다
(엔딩 목록은 이미 메뉴 `ENDINGS`의 몫이다).

### 4. 보스 loot 화면에서의 리로드

종결 노드(보스·막다른 길)가 클리어 목록에 있는 슬롯은 **그 승리의 loot 화면에서만** 생길 수 있다
(loot 확정이 런을 끝내고 슬롯을 폐기하므로). 이런 슬롯은 **loot 화면으로 복원**하고, Enter가 정상 경로로 엔딩을 연다.
보드로 복원하면 런을 끝낼 길이 없다(이번 결정 1이 만든 새 상태를 막는 조항). 스키마 변경 없음 — 노드 그래프와 클리어 목록으로 판정한다.

### 5. CONTINUE는 같은 전투를 다시 만든다 (요청 C)

`slotToGameState`에 **선택 인자** ICE 카탈로그를 추가한다. 주어지면 기반 ICE를 런 시작과 같은 함수
`missionIce(mission, catalog)`(이전 `main.ts loadIce`, 이동만)로 다시 유도한다. 미션의 `ice_id` 또는 등급+시드로 결정되므로
**세이브에 아무것도 더할 필요가 없다** — 새 필드도, 스키마 버전 변경도 없다. 인자를 넘기지 않는 기존 호출자는 이전과 같다.
결과: 복원된 보스 roster `wintermute 165/165`, 이름 `ICE — Yakuza Enforcer` = 실전과 동일(deep-equal 테스트).

## 불변 (Must hold)

- **ADR-0250 결정 2·4 유지**: 로드는 도착이다. 미해결 ICE 위의 슬롯(전투 중 저장 포함)은 결정을 다시 열고, 보스 BYPASS는 막혀 있다.
  전투 중 리로드는 그 전투를 처음부터 다시 연다 — roster HP는 세이브에 없다(기존 계약; 이 ADR은 그것을 바꾸지 않는다).
- 세이브 스키마 `version: 1`, 필드 추가 없음(ADR-0185). 구 세이브는 그대로 로드된다.
- 가격·피해·RNG·비용·던전·Matrix 게이트·종결 조건·ADR-0251 규칙 불변. 양 덱 balance stdout은 ADR-0239와 byte-identical.

## 대안과 기각 (Alternatives)

| 안 | 내용 | 판정 |
| --- | --- | --- |
| 저장을 리듀서 경계(입력 핸들러)로 옮김 | 매 액션 뒤 저장 | **기각** — 결과는 같고, 이미 `draw(persist)`가 렌더/저장 경계다. 전투 경로의 저장 내용을 바꿀 위험만 늘어난다 |
| loot에서는 저장하지 않음 | 회복 미리보기 손실을 피함 | **기각** — 보스 loot에서 리로드하면 보스 직전 전투 프레임으로 되감긴다(이번 버그) |
| 완료 후에도 슬롯 유지 | 현재 동작 | **기각** — 끝난 미션이 다시 열린다 |
| 완료 표식 필드 추가 | CONTINUE가 엔딩을 다시 표시 | **기각** — 스키마·화면 추가, 이득 없음 |
| C: roster HP·기반 ICE id를 세이브에 저장 | 선택 필드 | **불필요** — 기반 ICE는 미션에서 결정적으로 유도된다 |

## 결과 (Consequences)

**얻는 것**: 리로드가 더 이상 이전 전투로 되감지 않는다. 엔딩이 제목 화면으로 끝난다. 완료한 미션은 다시 열리지 않는다.
복원된 전투는 실전과 같은 ICE다. ADR-0250의 "로드 = 도착"이 가정하던 저장 상태가 성립한다.

**감수하는 것**
- 비종결 노드의 loot 화면에서 리로드하면 보드(해당 노드 클리어)로 복원되고 그 loot의 15% 회복은 받지 못한다
  (회복은 loot 확정에서 적용되며, 세이브는 "loot 대기"를 구분하지 않는다). 되감기보다 낫고, 스키마 필드 없이는 구분할 수 없다.
- 보스/종결 노드 loot에서 복원하면 loot 화면의 보상 줄(`+N credits`, `Loot:`)은 비어 있다(메시지에서 읽는 표시; 크레딧 자체는 복원됨).
- Matrix 프레임마다 IDB 쓰기가 늘어난다(같은 상태 참조는 건너뜀). 전투는 원래 매 입력 저장이었다.

## 열린 질문

1. 종결 노드의 loot 화면은 `HEAL applied → N/M`과 `ENTER: route selection`을 보여 주지만, 거기서 Enter는 런을 끝내고 회복은 적용되지 않는다.
   **로직은 의도로 판단한다**(아래) — 화면 문구만 사실과 다르다. 고칠지는 오너 판단(이번 범위 밖, 미변경).
2. 엔딩 HUD `Choice: arc4_liberation_front`는 40×60의 16열 HUD를 넘는다(기존, 미변경).

**종결 경로의 15% 회복 부재 (보고만, 미변경)** — 의도로 본다. 회복은 "다음 전투로 이어지는" loot의 몫이며
(`applyLootAction`: 비종결 경로만 `runPhase: "matrix"`로 돌아가며 회복), 종결 노드에선 다음 전투가 없다.
또한 `resolveEnding`이 `hp/maxHp`를 엔딩 판정 입력으로 쓰므로, 엔딩 직전에 회복을 넣으면 **엔딩 결과가 바뀐다** — 그것은 밸런스/서사 결정이다.
오너 보고의 패배는 회복 부재 때문이 아니라 끝난 런이 다시 열렸기 때문이었다(결정 2·3이 해소).

## Implementation Status (2026-11-02)

**Status**: ✅ Implemented (미커밋·미스테이징)

**Evidence**:
- `web/src/core/state/run_end.ts` (신규) — `isTerminalNode`(loot의 완료 조건을 그대로 추출), `autosaveIntent`(`ending` → retire, 그 외 런 → write), `runCompleted`(ending에서 Enter/ESC), `RUN_COMPLETE_MESSAGE`.
- `web/src/core/state/mission_ice.ts` (신규) — `missionIce`: `main.ts loadIce` 본문 그대로 이동.
- `web/src/main.ts` — `draw()`가 `matrix/ending/loot` 분기에서도 `autosave()`; `autosave()`는 순서 큐(`persistQueue`) + 같은 상태 참조 생략 + retire 시 `clear(0)`; 입력 핸들러의 `runCompleted` → 상태 null·제목·상태줄; `refreshSaveCache`는 런 상태가 없을 때만 다시 그림; CONTINUE가 ICE 카탈로그를 넘김; `loadIce` → `missionIce`.
- `web/src/core/state/state.ts` — `slotToGameState(…, iceCatalog?)` 기반 ICE 유도, 클리어된 종결 노드는 loot로 복원. `state_actions_phases.ts` — 완료 조건을 `isTerminalNode`로(의미 불변). `renderer/ending.ts` — footer 문구.
- 테스트: 신규 `web/tests/run_end_save.test.ts` 18개 — HEAD에서 **12 failed / 6 passed**(통과 6개는 가드: 이동·승리가 리듀서 상태엔 이미 있음, 비종결 loot 복원, ADR-0250 보스/비보스 재개방 2개, 구 호출자) → **18 passed**. 신규 `web/e2e/run_end_save.spec.ts` 3개×2 프로젝트 — HEAD 빌드에서 **6 failed** → **6 passed**.
- 검증: typecheck 0; lint 0 errors(기존 `keyboard.ts:14` warning 1); `npm test` **175 files / 3932 passed**(기준 174/3914); build PASS(`index-DKOoa0XB.js`); 편집 `src/**`만 Prettier, `--check` PASS; 양 덱 balance stdout ADR-0239와 byte-identical; E2E **88 passed / 4 skipped / 0 failed**(기준 82 + 신규 6; `continue.spec.ts` 무수정 통과), 5195 preview(pid 75395) 유지.
- 증거: [run-end-and-save-2026-11-02](../../design/run-end-and-save-2026-11-02/README.md) — 실제 키 before/after trace(슬롯 디코드 포함), 3 사례 × 3 레이아웃 캡처, 폭 검사 9/9.

**Notes**: 열린 질문 1·2는 미변경. 결정 내용(ADR-0250·0246) 무변경.

## 변경 이력

- **2026-11-02**: 신규. 오너 "모두 수정해." 승인. B의 완료 정책(엔딩 도착 시 슬롯 폐기, CONTINUE 비활성)은 구현자 판단으로 기록.
