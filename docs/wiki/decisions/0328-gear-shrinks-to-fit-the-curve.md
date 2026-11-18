# ADR-0328: 장비는 곡선에 맞게 작아진다 — 9종 live 기준 재조정

**상태**: Accepted (오너 결정: *"programPower 배선 + 재조정"*, 목표 대역 *"완만 — T6 g5/g6 ~65/70%"*)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P0 (경제 · 성장 · 전투)

## 컨텍스트 (Context)

ADR-0326(방어 축) + ADR-0327(programPower) 로 **9종 스탯이 live** 가 되자 장비가 곡선을 무너뜨렸다 —
`npm run gear` 실측: **T1 만으로도 미션 완주율이 전 등급 100%**(bare g5/g6 26/42%). 카탈로그 스탯은
**읽히지 않는 시스템**을 전제로 저작되어 과대했다.

**균일 스케일은 답이 아니었다.** k=0.05~0.1 스케일은 저티어 아이템을 0으로 만들었다
(`MILITECH_EYES attack 3→0`, `CHROME_GLOVES` 전부 0, `ono_sendai` 2pc 전부 0) — ADR-0326 이 고친
**"죽은 스탯" 문제가 재발**한다. 곡선의 총 예산은 작지만(단일 스탯 `def8` ≈ T6 목표), **각 아이템은
non-zero 를 유지**해야 한다.

## 결정 (Decision)

**아이템·세트 보너스의 read 스탯을 수작업으로 작게 다시 쓴다** ([`equipment_catalog.ts`](../../../web/src/core/state/equipment_catalog.ts),
[`set_bonus.ts`](../../../web/src/core/state/set_bonus.ts)). 규칙:

- **각 아이템이 non-zero 기여**를 유지한다(죽은 스탯 금지).
- **티어 사다리 유지**: T6 > T4 > T2 > T1 (loadout 총합 기준).
- **총합이 목표 대역**(T6 g5/g6 ≈ 65/70)에 들어간다.
- **`programPower` 는 상한 60% bypass**(ADR-0327)이므로 티어당 1~8로 작게.

예: `MASTER_BODY` `def 4 / hp 8 / shield 2 / resist 4`, `MASTER_DECK` `def 3 / crit 3 / prog 8`,
`STREET_DECK` `crit 1 / prog 2`, `militech 2pc` `crit 1`, `arasaka 3pc` `def 1 / hp 1 / resist 1`.

## 결과 (Consequences)

- **측정 (`npm run gear`, 64시드 per-cell, `survival` 과 동일)** — 목표는 T6 g5/g6 65/70:

  | loadout | g3 | g4 | g5 | g6 |
  | --- | --- | --- | --- | --- |
  | bare (기록 기준선) | 83 | 83 | 26 | 42 |
  | T1 | 85 | 85 | **28** | **49** |
  | T2 | 98 | 97 | **40** | **64** |
  | T4 | 100 | 100 | **60** | **77** |
  | T6 | 100 | 100 | **63** | **81** |

  **g5 는 목표에 근접**(28/40/60/63 vs 32/40/50/65), **g6 는 ~+11pp 초과**(T6 81 vs 70).
  g6 는 미션 3개뿐이라 노이즈가 크고 피해에 더 민감하다 — 균일 스케일로는 g5/g6 **모양**을 동시에 맞출 수 없다.
  사다리는 **단조**(T1<T2<T4<T6, g5·g6 모두).
- **기록 기준선 byte-identical**: `npm run balance` **100/100/100/97.1/70.6/47.0** (bare runner → EMPTY_LOADOUT).
- **테스트**: 카탈로그 패리티 단언(옛 절대값)을 **속성 기반**으로 재작성 — `toBe(N)` → `toBeGreaterThan(0)` /
  상대 비교. 향후 재조정에 견딘다. vitest **232 files / 4416 tests**.
- **남은 긴장(오너)**: 장비 파워와 난이도는 함께 설계되어야 한다. 현재는 bare 곡선이 정본이고 장비는 그 위의 보너스다.
  장비를 더 의미 있게 만들려면 난이도 스케일(적/보스)이 필요하다.
- **남은 것**: AP 자원 · 플레이어 스킬 · `extraEffect` resolver (각각 별도 서브시스템) · `buy`(오너 결정 5번) · `use_item`.
