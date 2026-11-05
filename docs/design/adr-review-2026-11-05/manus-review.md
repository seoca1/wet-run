---
source: Manus API v2 (task.create → task.listMessages)
task_id: LXHmpxarQHm38S4FT5XXPX
task_url: https://manus.im/app/LXHmpxarQHm38S4FT5XXPX
agent_profile: lite
date: 2026-11-05
target: Game/wet_run/docs/wiki/decisions/0279-the-run-states-its-earnings.md
---

# Manus Review — ADR-0279

## Verdict: approve-with-caveats

## Findings

1. **[high] 최종 엔드투엔드 근거가 분리되어 있다.** `ending_distribution.txt`의 비교는 “리졸버 지갑만 교체”한 결과다. 따라서 `resolveVictory`의 미션 보상 1회 지급 변경과 `player.credits` 리졸버 변경이 함께 적용된 최종 상태의 엔딩 분포를 검증하지 않는다. 두 변경을 모두 포함한 분포 측정이 필요하다.

2. **[medium] “1회 지급”의 멱등성이 입증되지 않았다.** `isTerminalNode(state)`로 터미널 승리를 판정하는 것은 정상 진행의 1회 지급을 설명하지만, 동일한 승리 처리나 터미널 보상 처리가 재실행될 때 중복 지급을 막는 상태 조건은 ADR에 제시되지 않았다. 현재 테스트 설명도 “2교전 완주”만 검증한다고 되어 있다.

3. **[medium] 터미널 노드 정의의 경계가 불명확하다.** 결정은 보스 또는 막다른 노드에서 미션 보상을 지급한다고 하지만, 모든 미션의 마지막 보스/막다른 노드가 반드시 하나인지, 보스가 아닌 여러 막다른 경로가 있을 때 어느 시점에 지급되는지 근거가 없다.

4. **[medium] 관련 ADR-0130과의 권위 관계가 명시적으로 해소되지 않았다.** ADR-0279는 `mission.rewards.credits`, `inventory.credits`, `player.credits`를 구분하지만, 관련 ADR의 `rewards.credits` 권위 원칙과 이 구분이 어떻게 양립하는지 설명하지 않는다. 지갑의 역할과 권위 필드를 명시적으로 매핑해야 한다.

5. **[low] “5개 arc 모두 control 엔딩 보유”와 도달성 주장이 혼재한다.** 표와 본문상 arc 1·2의 `control`은 여전히 도달되지 않는다. 카탈로그에 존재한다는 뜻인지, 실제 reachable하다는 뜻인지 표현을 분리해야 한다.

## Edge cases not addressed

- 터미널 전투가 보스이면서 동시에 막다른 노드인 경우의 중복 판정.
- 미션 보상 금액이 0, 누락, 또는 비정상적으로 큰 경우.
- 터미널 승리 메시지와 전리품 화면 파싱이 실패하거나 `state.message`가 덮어써지는 경우.
- HP 회복 후 `hp > 75%` 판정 시점과 보상 지급 시점의 순서.
- 저장/재개 또는 동일 전투 결과 재처리 시 미션 보상 중복 지급.

## Open questions assessment

**(a)** 부분적으로 답할 수 있다. `npm run endings`가 HP를 기록한다는 근거는 있으나, 실제 출력이나 `hp > 75%` 충족률은 제공되지 않아 현재 답변은 불가능하다.

**(b)** 현재 증거만으로는 답할 수 없다. `purchaseItem` 호출자가 없다는 사실은 현 상태를 설명할 뿐, 통합 여부를 결정할 경제·UX 요구사항은 제공하지 않는다.

**(c)** 답할 수 없다. 노드 보상 공식은 제시됐지만 목표 총수입, 난이도별 보상 기준, 변경 후 분포가 없어 재설계 판단 근거가 부족하다.

## Suggested follow-ups

1. 두 코드 변경을 모두 포함한 최종 `npm run endings` 결과를 추가한다.
2. 동일 터미널 승리 재처리에 대한 1회 지급/멱등성 테스트를 추가한다.
3. `isTerminalNode`의 보스·막다른 노드 경계를 문서와 테스트로 고정한다.
4. ADR-0130과 세 지갑의 권위·용도를 명시적으로 연결한다.
5. (a)의 HP 분포와 (c)의 보상 곡선 검토를 별도 측정 결과로 기록한다.
