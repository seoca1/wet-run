# ADR-0287: 크레딧은 정보를 산다 — 전력을 주지 않는 유일한 소비처

**상태**: Accepted
**날짜**: 2026-11-07
**결정자**: 오너 ("권장대로 해줘" — ADR-0286 (b))
**우선순위**: P1 (경제) · P1 (곡선 보호)
**관련**: [ADR-0286 — 상점은 자리가 없다](./0286-the-shop-has-no-room.md) · [ADR-0285 — 세 번째 전리품 칸 없음](./0285-there-is-no-third-loot-option.md) · [ADR-0284 — 크레딧이 prep 으로](./0284-credits-reach-prep.md) · [ADR-0282 — 전리품은 지출](./0282-the-loot-stop-is-a-spend.md) · [ADR-0281 — 경로가 런의 모양](./0281-the-route-is-the-run.md) · [ADR-0247 — SCAN 의 비용](./0247-dungeon-role-supplement-manus-second-opinion.md) · [ADR-0251 — 화면은 사실을 말한다](./0251-truthful-program-affordance-and-combat-integrity-rules.md)

> **다섯 번째 시도이고, 처음으로 곡선을 안 건드린다.** ADR-0282·0284·0285·0286 은 모두
> **전력을 주는** 소비처였고, fitted 곡선에 자리가 없어 전부 "약하다 or 너무 세다" 로 끝났다.
> 이번엔 **정보**를 판다: 전리품 5번 칸 = **경로 정보**. 전력을 안 주므로 곡선이 움직이지 않는다.
> 선례도 있다 — **PROBE 는 이미 위협 정보를 COST 로 판다**(ADR-0247).

## 컨텍스트 (Context)

ADR-0286 의 결론: 전력-부여 크레딧 소비처는 fitted 곡선에 들어갈 자리가 없다. 남은 방향은
**(b) 전력이 아닌 소비처**였고, 그중 이 게임에 자연스러운 것은 **정보**다.

플레이어가 실제로 모르는 것: **경로 앞에 어떤 ICE 가 있는지.** 보드는 그래프·교전 수·크레딧을
보여주지만(ADR-0281) **ICE 의 정체**는 감춘다 — 그리고 그게 "내 손패가 그 방어도를 뚫을 수 있나"를
가르는 정보다. 게다가 PROBE 가 이미 "위협 정보는 사는 것"이라는 규칙을 세웠다.

## 결정 (Decision)

### 1) 전리품 5번 칸 = INTEL

`LOOT_INTEL_PRICE_BY_GRADE = [30, 40, 60, 80, 110, 120]` — **싸다**. 정보는 세금이 아니라
결정이어야 하므로 전력 가격(카드 `tier²×60` = 60~1500, 수리 = 한 번의 교전)보다 낮게 잡았다.

구매하면 `state.intelNodes` 에 **미해결 교전 노드 전부**가 들어가고, `player.credits` 가 차감된다.

### 2) 경로 카드가 이름을 말한다

`routePreview(matrix, cleared, bypassed, destination, intelNodes)` → `knownIce`.
정보를 산 노선은 **개수를 이름으로** 바꾼다:

```
before paying   node 1  route: 2 fights · 250cr
                node 2  route: 1 to boss · 2 open · 250cr
after paying    node 1  route: wisp, hosaka_couri
                node 2  route: hosaka_couri, wisp
```

**지불하기 전에는 이름이 없다** — 정보는 산 사람만 본다.

### 3) 저장해도 남는다

`SaveSlot.intelNodes?` (선택 필드, **version 1 유지**). 플레이어가 **돈을 낸 지식**이므로
재로드에서 사라지면 안 된다. 구 슬롯은 이 필드가 없어 아무것도 안 보이던 그대로다.

## 측정 (Measurement)

### A. 전력을 주지 않는다 — 확인

`npm run survival --seeds 16`:

| 정책 | g1 | g2 | g3 | g4 | g5 | g6 |
|---|---:|---:|---:|---:|---:|---:|
| `loot=intel` | 100.0 | 84.4 | 43.8 | 37.5 | 8.3 | 0.0 |
| `loot=card` (카드 안 받음과 동급) | 100.0 | 75.4 | 44.3 | 33.1 | 9.0 | 4.2 |
| `loot=smart` (수리) | 100.0 | 98.0 | 81.8 | 45.6 | 31.9 | 18.8 |

**intel 은 "카드를 포기한 것"과 같은 궤적**이다 — HP·덱·실드 어느 것도 안 늘므로 **fitted 등급이
움직이지 않는다.** 그게 오너가 요청한 성질이다.

### B. 결정 가치는 **이 하네스로 측정 불가** — 그리고 그건 봇의 성질이다

정보를 쓰는 정책(드러난 ICE 중 **가장 약한 쪽**으로 경로):

| 정책 | g2 | g3 | g4 |
|---|---:|---:|---:|
| 정보를 보고 라우팅 | 82.0 | 46.6 | 37.5 |
| 정보를 무시하고 라우팅 | 84.4 | 43.8 | 37.5 |

**노이즈 이내다.** 이유는 명확하다: **봇은 이미 `matrix.nodes` 를 직접 읽어** 그래프와 ICE 구성을
알고 있다. 즉 **이미 다 보는 플레이어에게 정보를 팔면 가치가 0** 이다. 사람은 그래프는 보지만
**ICE 는 못 보므로**, 가치는 지각·결정의 문제이고 이 하네스가 가격을 매길 수 없다.

**이 한계를 숨기지 않는다.** ADR-0285·0286 이 "지배당한다"는 측정으로 기각된 것과 달리,
이 옵션은 **지배당한다고 측정되지 않았다** — 측정할 수가 없다.

원자료: `docs/design/adr-0287/intel-sink.txt`.

## 결과 (Consequences)

- **크레딧에 처음으로 소비처가 생겼고, 곡선은 그대로다**(A).
- **전리품 5번 칸이 부활했다** — ADR-0285 에서 지웠던 자리지만, 그때는 전력(패치)이라 지배당했고
  지금은 정보다.
- **불변**: 곡선·전투·엔딩 리졸버 무영향. `SaveSlot` version 1 유지(선택 필드).

## Implementation Status (2026-11-07)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/state/loot_choice.ts` — `LOOT_INTEL_SLOT` · `LOOT_INTEL_PRICE_BY_GRADE` ·
  `lootIntelPrice` · `intelTargets`.
- `web/src/core/state/state_actions_phases.ts` — `takeLootIntel` (차감 + 공개 + 거절).
- `web/src/core/dungeon/route_preview.ts` — `knownIce` + 정보를 산 노선만 이름 표시.
- `web/src/renderer/matrix.ts` · `matrix_nodes.ts` · `run_screen.ts` — intel 전달 · 경로 카드 ·
  전리품 5번 줄.
- `web/src/core/types.ts` · `state.ts` — `intelNodes` (GameState 선택 필드 + `SaveSlot` 선택 필드 +
  양방향 왕복).
- `web/tests/adr0287_intel.test.ts` (5) · `loot_choice.test.ts` 갱신.
- 측정: `docs/design/adr-0287/intel-sink.txt`.
- vitest **196 files / 4123 tests** · typecheck 0 · lint 0 errors · build PASS · 소크 frozen 0 ·
  story trace 통과.

**Notes**:

- **e2e 드라이버 수정 불필요** — 화면 수 그대로, 키 하나 추가.
- 전리품 화면은 이제 `1-3` 카드 · `4` 수리 · `5` 정보(가격 표시).
- `intelTargets` 는 **미해결 교전 전체**를 공개한다(부분 공개는 결정을 흐린다).

## 열린 질문

- **(a) 정보의 값을 측정할 방법.** 지금 하네스는 완전정보 봇이라 원리적으로 불가능하다. 측정하려면
  **부분정보 봇**(ICE 를 모르는 상태에서 결정)을 만들어야 하고, 그러면 "정보를 산 봇 vs 안 산 봇"의
  차이가 곧 정보의 값이 된다. **이게 이 ADR 의 가장 정직한 후속 작업이다.**
- **(b) 정보의 범위.** 지금은 미해결 교전 전체를 한 번에 공개한다. **경로별로** 팔거나(더 비싸게),
  **보스만** 공개하는 등 층이 가능하다.
- **(c) 재구매.** 이미 산 정보를 다시 사면 돈만 나간다(이미 공개됨). 화면이 그걸 표시해야 한다.
- **(d) 크레딧의 다른 소비처.** 정보는 곡선을 안 건드리므로 **더 만들 수 있다** — 예: 우회 비용
  할인(COST 는 런의 시계라 전력에 가깝다, 주의), 픽서의 힌트.

## 변경 이력

- 2026-11-07: Draft → Accepted (오너 "권장대로" = ADR-0286 (b)). 전리품 5번 = INTEL, 경로 카드가
  ICE 이름을 표시, 저장 왕복. 곡선 무영향 확인, 결정 가치는 측정 불가로 명시.