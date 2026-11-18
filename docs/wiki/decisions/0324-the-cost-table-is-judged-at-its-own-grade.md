# ADR-0324: 비용표는 자기 등급에서 판정된다 — 크래프팅 사다리 2판

**상태**: Accepted (오너 결정: *"B. 하네스 판정 풀 수정"*)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P0 (경제 · 크래프팅)

## 컨텍스트 (Context)

[`crafting-and-equipment-proposal-2026-11-18.md`](../../design/crafting-and-equipment-proposal-2026-11-18.md)
의 Manus 비용표(18종)는 그대로 구현할 수 없다. 부록의 실측이 반증했다 — 후보 레시피 **18종 전부 도달률 0.0%**.
원인은 common 부족이 아니라 **초희귀 게이트**였다(`rom_echo` 0.012/킬 ≈ 25미션).

그런데 교정 1~4를 반영하려 하니 **하네스 자체가 답을 막고 있었다.** `web/scripts/crafting_probe.ts`
의 `craftableAtTier` 는 **등급 ≤ tier 풀**로 도달률을 셌다(계약 문구: `missions <= tier`). 그런데
드롭은 **등급별로 국소화**되어 있다(실측, 8런):

| 재료 | 실제 드롭 등급 | 풀(g1..tier) 내 최대 도달 |
| --- | --- | --- |
| `combat_module` | g3+ | T3 에서 ≤50% (그것도 g3 의 일부만 ≥1) |
| `construct_shard` | g4+ | T4 에서 ≤33% |
| `t6_program` · `aleph_shard` | **g6 전용** | T6 에서 ≤9% |

즉 **등급 ≤ tier 풀**에서는 **common 게이트만** ≥50%를 넘길 수 있고, 정작 희귀 게이트는 **원리적으로
통과 불가**다. 게이트를 측정하려면 **게이트가 겨누는 등급에서** 재야 한다.

## 결정 (Decision)

**⑴ `craftableAtTier` 는 레시피의 *자기 등급* 런으로 판정한다** — tier-T 레시피를 grade-T 런에 대해
잰다(이전: 등급 ≤ T 풀). 핸드오프의 런 수 서술(T1 2~3런 · T2 5~8런)과 일치한다.

**⑵ 비용표 2판을 확정한다** — 교정 1~4 + 실측 분포 반영. T1 은 순수 common, 상위 tier 는 자기 등급에서
실제로 나오는 재료로 게이트한다. (`web/scripts/crafting-recipes-candidate.json`)

| tier | 항목 | 비용 |
| --- | --- | --- |
| T1 | deck_street / eyes_militech / gloves_chrome | `data_fragment×3 + ice_shard×5` / `df×3 + ice_shard×4` / `df×4 + ice_shard×3` |
| T2 | corporate / subdermal / trodes_ninja / boots_ghost | `df×16 + ice_shard×4` / `df×12 + ice_shard×4` / `df×18 + ice_shard×3` / `df×15 + ice_shard×4` |
| T3 | militech / tactical / nanohive | `df×20 + combat_module×1` / `df×16 + combat_module×1` / `df×22 + combat_module×1` |
| T4 | arasaka / kereznikov | `ice_shard×50 + combat_module×2 + construct_shard×1` / `ice_shard×45 + cm×2 + cs×1` |
| T5 | ghost | `combat_module×30 + construct_shard×20` |
| T6 | master / master_body / zion | `cm×12 + cs×8 + t6_program×1` / `cm×10 + cs×6 + aleph_shard×1` / `cm×10 + cs×6 + t6×1 + aleph×1` |

## 결과 (Consequences)

- **합격**: T1 3종 **≥50% @3런**(58.3 / 70.8 / 70.8). T2~T6 13종 **전부 ≥50% @8런**(53.6 ~ 78.7).
  사다리가 단조롭고, 각 tier 가 **자기 등급에서 실제로 나오는** 재료로 게이트된다.
- **측정이 교정 #3 을 반박했다**: "`upgrade_t*` 는 1 ICE · 0.2 chance 라 병목"이라는 전제는 틀렸다 —
  g2 ICE 가 `upgrade_t2` 를 8런 중앙값 **3개** 뱉는다. (비용표에는 여전히 안 쓴다 — g1 에 안 나와 T1 게이트로 부적합.)
- **T4 는 `data_fragment` 가 아니라 `ice_shard` 로**: g4 ICE 는 df 중앙값 **16**, ice_shard **74**.
  T4 를 df 로 게이트하면 **27.4%** 로 막힌다 — 등급마다 실제로 나오는 common 이 다르다.
- **하네스 계약 변경**: 이전 기록(18종 0.0%)은 **옛 풀 기준**이므로 역사로 남긴다.
- **남은 것** (핸드오프 §4 "그 다음"): `materials.json`·`recipes.json` 데이터 파일 생성 →
  `craftItem` 화면 연결 → 미사용 스탯 9종 배선(방어 단계) → `use_item`.
