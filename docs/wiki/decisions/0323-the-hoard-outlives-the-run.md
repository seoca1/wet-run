# ADR-0323: 재료 지갑은 런보다 오래 산다 — 획득분을 보존한다

**상태**: Accepted (오너 결정: *"보존해줘"*)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P0 (경제 · 진행)

## 컨텍스트 (Context)

[`system-map-2026-11-18.md`](../../design/system-map-2026-11-18.md) 의 빈 출구 P0-2: **드롭 28종이 적립만 되고 소비처가 없었고**, 게다가 경계가 잘못돼 있었다.

```
main.ts  this.inventory = initial.inventory;   // 런 시작 때 '미션 보상'으로 덮어씀
victory  state.inventory.materials[drop] += qty // 런 안에서만 쌓임
(런 종료) 아무 일도 없음                        // 사라짐
```

즉 **재료는 보려고 존재하는 숫자**였다. 그리고 [`crafting-and-equipment-proposal-2026-11-18.md`](../../design/crafting-and-equipment-proposal-2026-11-18.md) 부록의 실측이 이 경계의 값을 정량화했다:

> 미션 한 판이 버는 것(실측 중앙값): `data_fragment` 약 3, `ice_shard` 약 5.

**런마다 리셋하면 어떤 레시피도 "한 판 분량"을 넘을 수 없다** — 장기 목표라는 개념 자체가 성립하지 않는다.

## 결정 (Decision)

**런이 획득한 재료를 보존한다 — 승리든 실패든.**

- **런 시작**: 지갑을 **쌓아둔 것(hoard) + 미션 보상**으로 시드한다(덮어쓰지 않는다).
- **런 종료**(JACK OUT · 엔딩 · 플랫라인 세 경로 전부): **런이 *번* 것**만 hoard에 합친다.
- **보존되는 것은 "상속"이 아니라 "획득"이다.** 시드값을 기억해 두고 빼므로, **첫 프레임에 잭아웃해도 미션 보상이 hoard로 주조되지 않는다**(파밍 구멍 차단).
- **지속**: hoard는 `localStorage`(`wetrun_materials`)에 남아 새로고침을 견딘다.
- **credits는 합치지 않는다.** 런 중 `inventory.credits`에 들어오는 것이 없고, 미션 보상은 임무를 끝내기 전에는 런의 것이 아니다. 합치는 축은 **재료**다.

## 결과 (Consequences)

- **장기 목표가 성립한다**: 레시피가 여러 런의 수입을 요구할 수 있다. 실측 기준으로 `data_fragment` 8 + `ice_shard` 6 은 **2~3런**, 희귀 재료는 그보다 훨씬 길다(부록의 교정 1이 그 문제를 다룬다).
- **실패가 헛되지 않다**: 죽어도 주운 것은 남는다. Manus가 지목한 "가장 위험한 가정"의 한쪽을 오너가 선택한 것이다 — 반대쪽(런마다 리셋)은 28종 드롭을 다시 inert하게 만든다.
- **밸런스 무영향**: 재료는 전투 수치에 닿지 않는다. `npm run balance` **byte-identical**(97.1 / 70.6 / 47.0).
- **남은 위험**: 보존하면 common이 **부채**처럼 쌓일 수 있다. 다만 부록의 실측은 그 반대를 보였다 — common은 이미 *SHORT* 이고, 적체의 원인은 **희귀 게이트가 제작을 막는 것**이다. 교정 1~4가 그것을 다룬다.

## Implementation Status (2026-11-18)

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/state/wallet.ts` — `addStacks` · `seedRunWallet` · `earnedMaterials` · `mergeRunIntoWallet` · `readWalletMaterials` · `writeWalletMaterials`
- `web/src/main.ts` — 부팅 시 hoard 복원 · 잭인 시 `seedRunWallet` · **런 종료 3경로가 `endRun()`** 호출 · 종료 시 hoard 영속
- `web/tests/adr0323_the_hoard_outlives_the_run.test.ts` — 12 tests(스택 · 시드 · **획득 ≠ 상속** · 잭아웃 무주조 · 저장소 왕복/손상)
- 측정: `npm run balance` byte-identical

**Notes**: `inventory.credits` 는 의도적으로 병합하지 않는다(위 결정). 크래프팅 화면은 아직 레시피가 0개이므로 이 보존이 **오늘 눈에 보이는 효과**는 없다 — **비용표 2판의 전제**를 세운 것이다.

## 관련 결정

- ADR-0322 — 시스템 맵/성장 구조(이 문서가 빈 출구 P0-2의 경계를 고친다)
- Manus 제안 — [`crafting-and-equipment-proposal-2026-11-18.md`](../../design/crafting-and-equipment-proposal-2026-11-18.md) (오너 결정 1번 = 이 문서)
- ADR-0284 — prep 지갑(localStorage 영속의 선례)
- ADR-0322 — `equipment_store.ts`(영속 관용구의 선례)

## 변경 이력

- 2026-11-18: Accepted (오너 "보존해줘") · 구현 · 밸런스 무영향 확인
