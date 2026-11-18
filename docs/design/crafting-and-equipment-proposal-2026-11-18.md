# 크래프팅 · 아이템 · 장비 설계 (Manus 제안) — 2026-11-18

> **출처**: Manus 태스크 `nV6GENHMDeRuqbLnTFeuzn` · <https://manus.im/app/nV6GENHMDeRuqbLnTFeuzn>
> 프로필 `lite` · 커넥터 차단(`clear_connectors`) · 구조화 출력 사용
> **상태**: 🟡 **제안** — 밸런스 수치는 오너 승인 전이다. 이 문서는 *구현하지 않는다*.
> 요청 배경: [`system-map-2026-11-18.md`](system-map-2026-11-18.md) 의 빈 출구 P0 3건.

## ⚠️ 읽기 전 — ID 매핑 (Manus 이름 → 실제 카탈로그 id)

Manus에는 **카탈로그 ID를 주지 않고 이름만** 줬기 때문에, Manus가 그 이름을 슬러그화하면서
접두사 순서가 뒤집혔다. 아래 표로 옮겨 읽어야 한다. (두 항목은 우연히 일치한다.)

| Manus 표기 | **실제 id** | 실제 이름 |
| --- | --- | --- |
| `street_deck` | **`deck_street`** | Ono-Sendai 11 (Hot Rod) |
| `militech_eyes` | **`eyes_militech`** | Militech Eagle Eye |
| `chrome_gloves` | **`gloves_chrome`** | Chrome Surgical Gloves |
| `corporate_deck` | **`deck_corporate`** | Sakura Cybermod 'Samurai' |
| `subdermal` | **`bodysuit_subdermal`** | Subdermal Weave Mk.II |
| `trodes_ninja` | `trodes_ninja` ✅ | Stealth Trodes |
| `boots_ghost` | `boots_ghost` ✅ | Chameleon Boots |
| `militech_deck` | **`deck_militech`** | Militech Centurion |
| `tactical_body` | **`bodysuit_tactical`** | M-31 Combat Armor |
| `nano_hive` | **`implant_nanohive`** | Nano-Hive |
| `arasaka_deck` | **`deck_arasaka`** | Arasaka 'Onikiri' |
| `kereznikov` | **`head_kereznikov`** | Kereznikov Boost |
| `ghost_deck` | **`deck_ghost`** | Ghost Cartographer |
| `master_deck` | **`deck_master`** | Wintermute / Neuromancer (Merged) |
| `master_body` | **`bodysuit_master`** | Full-Body Cyborg Conversion |
| `zion_trodes` | **`trodes_zion`** | Zion Direct-Neural Link |

또 하나: Manus의 **구조화 출력(JSON)** 에서 `master_deck` 의 레시피가 **자기 자신을 재료로** 갖는
전사 오류가 있었다(`master_deck ×1`). 아래 **본문(마크다운)이 정본**이며 그 오류는 없다.

## 오너 결정이 필요한 지점 (Manus가 남긴 것)

| # | 결정 | 비고 |
| --- | --- | --- |
| 1 | ✅ **보존한다** (2026-11-18 오너 결정 → ADR-0323) | 구현 완료. 부록의 실측은 common 적체보다 **희귀 게이트**가 문제임을 보였다 → 교정 1~4 |
| 2 | 레시피 비용 (18종) | 전부 후보값 — 하네스 측정 후 조정 |
| 3 | `ICE recycler` 정제 sink (data_fragment×10 + ice_shard×10 → repair_cache) | 기존 자동 회복 floor 와 **중첩 금지** — 비교 측정 필요 |
| 4 | 시장 offer (leg당 3개 한도) | 인플레이션 측정 대상 |
| 5 | 스탯 배선 9종의 적용 위치 | 특히 `apBonus`·`programPower` 가 g5/g6 를 가장 크게 흔든다 |

## 측정 계약 (Manus 제안)

```
craftableAtTier(item, tier) = P(inventory after missions at grade == tier >= recipe cost) >= 0.50
commonPileup(id) = median(material[id] at ENDING) - median(material[id] consumed) > ownerThreshold
closure(tier) = runSpend / runIncomeInMaterialEquivalent
```

> **2026-11-18 개정 (ADR-0324)**: 판정 풀을 `missions <= tier` 에서 **`grade == tier`** 로 고쳤다.
> 옛 풀은 등급별로 국소화된 희귀 게이트(예: g6 전용 `t6_program`)를 **원리적으로 도달 불가**로 만들었다
> (낮은 등급이 풀을 희석). 게이트는 **게이트가 겨누는 등급**에서 잰다.
그리고 **가장 싼 반증 실험**: 새 전투를 만들지 않고 기존 결정적 시드 100개를 replay 해서
실패/승리, ENDING 의 common 스택, 첫 T1/T2 craft 까지 걸린 런 수를 기록한다.

---

# wet_run: 재료·제작·장비·전투 배선 설계

## 전제와 판정 기준

이 문서는 현재 제공된 브리프를 기준으로 한 구현 설계다. 저장소 소스와 `balance` 실행 결과는 이 세션에 첨부되지 않았으므로, 아래의 비용·판매가·드롭량·방어 수치는 **소유자가 결정하기 전의 측정 후보값**이다. 확정값처럼 밸런스를 주장하지 않는다. 특히 g3/g4/g5 임무의 실제 평균 수입 곡선은 기록 파일이 없으므로 계산 결과를 날조하지 않고, harness가 출력해야 할 산식과 수용 기준을 명시한다.

세계관 고증과 게임용 발명은 분리한다. `console cowboy`, `ICE`, `cyberspace`, Case와 Molly는 *Neuromancer*의 어휘·인물이다.[1] Hosaka, Maas, biochip, Net의 voodoo/loa는 *Count Zero*의 도서 설명에 직접 나타난다.[2] Sense/Net, Angie, Mona, Yakuza와 cyberspace를 둘러싼 충돌은 *Mona Lisa Overdrive*의 도서 설명에 나타난다.[3] 아래에서 이 고유명사를 경제의 표지로 쓰는 것은 원작 귀속이고, `ICE shard`를 화폐로 쪼개거나 `repair queue`를 만드는 것은 **이 게임을 위한 발명**이다.

## 1. material sheet

티어는 제작 게이트용 등급이다. `T0`은 임무 1부터 보이는 벌크, `T1–T2`는 중반 장비의 재료, `T3+`는 장비·콘텐츠를 여는 희소 재료다. 이름의 원작 귀속 여부보다, 플레이어가 전투 중 무엇을 회수한다고 이해하는지가 우선이다.

| id | 제안 이름 / tier | 게임 안의 정체성 | 경제 역할 |
|---|---|---|---|
| `data_fragment` | loose data / T0 | 깨진 기업 인덱스와 미완성 핸드셰이크. **발명** | bulk common; 모든 기본 제작의 소모처 |
| `ice_shard` | ICE shard / T0 | 방어 루틴에서 떨어져 나온 검증 조각. **발명** | bulk common; 수리·정제의 소모처 |
| `combat_module` | combat module / T1 | 전투 construct의 전술 루틴. **발명** | T1 장비 핵심 재료 |
| `construct_shard` | construct shard / T1 | 이름 없는 sub-construct의 실행 조각. **발명** | T1–T2 프로그램 게이트 |
| `ice_construct` | ICE construct / T2 | 현장에서 회수한 작은 ICE construct. **발명** | T2 deck/body 제작 |
| `rom_echo` | ROM echo / T1 | 오래된 ROM에 남은 행동 패턴. **발명** | T1 장비·소모품 보조 |
| `t5_program` | T5 program | 상위권 ICE에 대응하는 프로그램 설계도. **발명** | T5 장비 게이트 |
| `glitch_fragment` | glitch fragment / T1 | 검증 실패가 반복된 오류 조각. **발명** | 확률형이 아닌 `extraEffect` 계열 제작 재료 |
| `loa_chip` | loa chip / T3 | Net의 loa를 연상시키는 낯선 칩. *Count Zero*의 loa 모티프를 빌린 표지이며, 이 게임의 칩 효과는 **발명** | T3/T6 skill·program 게이트 |
| `fragment.morrison_echo` | Morrison echo / T2 | 특정 콘솔 카우보이의 잔향으로 라벨된 echo. **이 게임의 발명**; 원작 인물·사실로 취급하지 않음 | T2 eyeware/gloves 제작 |
| `ta_construct` | Tessier-Ashpool construct / T3 | T-A 계열 보안망의 봉인된 construct. T-A는 Sprawl 소설의 기업명이고, 이 드롭 형태는 **발명** | T4 deck/body 게이트 |
| `unique_construct` | unique construct / T4 | 한 번만 재구성할 수 있는 비표준 construct. **발명** | T5–T6 장비 핵심 재료 |
| `fragment.tessier_archive` | Tessier-Ashpool archive fragment / T3 | 봉인된 가문 아카이브의 암호화 단편. 기업·가문 귀속은 *Neuromancer* / *Count Zero* 세계의 표지, 드롭 사용처는 **발명** | T4–T6 deck 게이트 |
| `shield_program` | shield program / T2 | ICE의 공격을 흘리는 방어 루틴. **발명** | body·방어 소모품 후보 |
| `t6_program` | T6 program | 최상위 ICE 패턴을 해석하는 프로그램 설계도. **발명** | T6 장비 게이트 |
| `upgrade_t2` | T2 upgrade wafer | 장비 펌웨어를 T2까지 올리는 인증 wafer. **발명** | T0/T1 장비를 T2로 승급하는 upgrade 전용 재료 |
| `upgrade_t4` | T4 upgrade wafer | T4 장비군의 서명과 맞는 wafer. **발명** | T2/T3 장비를 T4로 승급하는 upgrade 전용 재료 |
| `t_a_data_fragment` | T-A data fragment / T3 | Tessier-Ashpool 망의 데이터 조각. 원작 기업명, 이 아이템은 **발명** | T4+ deck/construct 제작 |
| `wintermute_key` | Wintermute key / T4 | Wintermute를 가리키는 암호 키. Wintermute는 *Neuromancer*의 핵심 고유명사이며, 이 키의 제작 효과는 **발명** | 최종 장비 또는 unique recipe의 rare key |
| `maas_neuropozyne_dose` | Maas neuropozyne dose / T3 | Maas 계열의 neuropozyne 투여량. Maas는 *Count Zero*의 기업이고, 이 아이템이 전투 소비품이라는 것은 **발명** | consumable candidate; HP/ICE 저항의 대가 |
| `hosaka_chip` | Hosaka chip / T3 | Hosaka 계열의 고성능 칩. Hosaka는 *Count Zero*의 기업이고, 장비 효과는 **발명** | T4 eyeware/deck 제작 |
| `hosaka_archive` | Hosaka archive / T4 | Hosaka의 오래된 연구 아카이브. 기업 귀속은 *Count Zero*, archive 드롭은 **발명** | T5 deck/program 게이트 |
| `yakuza_construct` | Yakuza construct / T3 | Yakuza 쪽에서 운용한 construct. *Mona Lisa Overdrive*의 Yakuza 표지를 차용하며, 이 드롭은 **발명** | T3/T4 eyeware와 `grantsSkillId` 후보 |
| `t4_program` | T4 program | 중상위 ICE를 해석하는 설계도. **발명** | T4 장비 게이트 |
| `aleph_shard` | aleph shard / T4 | 하나의 시작점처럼 취급되는 비정상 데이터 조각. 이 명명과 효과는 **발명** | 최종 unique recipe의 희귀 키 |
| `fragment.wintermute_echo` | Wintermute echo / T5 | Wintermute를 닮은 신호의 echo. 원작 고유명사를 사용하지만 내용은 **발명** | T6 deck/skill 최종 게이트 |
| `peripheral_artifact` | peripheral artifact / T5 | 네트워크 바깥 가장자리에서만 회수되는 artifact. **발명** | 최종 body/deck 보조 재료 |
| `fragment.timeline_echo` | timeline echo / T5 | 여러 경로가 겹친 듯한 기록. **발명** | 최종 unlock 또는 캠페인 전용 craft |

`fragment.*`, `t*_program`, `upgrade_t*`는 단순히 “희귀한 돈”이 아니다. 전자는 특정 제작 계보를 표시하는 provenance, 후자는 제작자가 요구하는 설계도/승급 인증으로 UI에 별도 태그를 붙인다. 같은 물질을 시장에서 무제한 환전할 수 있게 하지 않아야 tier gate가 보존된다.

## 2. 재료가 장비와 소비품으로 바뀌는 경로

기본 원칙은 세 가지다. 첫째, 18개 장비 모두가 `craft / drop / buy` 중 적어도 하나의 **명시된** 획득 경로를 가진다. 둘째, 장비는 장착 상태와 소유 상태를 분리한다. 셋째, 재료는 메뉴 지갑에 귀속되며 run 시작 시 `initial.inventory`로 덮어쓰지 않는다.

아래 비용은 `balance`에서 조정할 후보값이다. `×`는 수량이고, 0은 재료를 요구하지 않는 직접 드롭/구매다.

| 장비 | tier | 획득 경로 | 후보 비용 / 가격 | 비용을 그렇게 두는 이유 |
|---|---:|---|---|---|
| `deck_basic` | 0 | starter와 shop | 0 / 0 | 시작점이며 제작 목표가 아님 |
| `head_basic` | 0 | starter와 shop | 0 / 0 | stock trodes의 기준선 |
| `street_deck` | 1 | craft | `data_fragment×8 + ice_shard×6 + rom_echo×1` | common을 처음으로 실제 소비시키는 저위험 upgrade |
| `militech_eyes` | 1 | craft 또는 g1/g2 drop | `data_fragment×6 + combat_module×1 + rom_echo×1` | 공격/crit의 첫 선택지를 T1에 둠. Militech 표지는 **원작 사실 주장 없이 게임 발명** |
| `chrome_gloves` | 1 | craft | `data_fragment×7 + combat_module×1 + glitch_fragment×1` | attack와 programPower를 함께 주므로 glitch로 계보를 제한 |
| `corporate_deck` | 2 | craft | `ice_shard×14 + construct_shard×4 + ice_construct×1 + t4_program×1` | T2 전환에 단순 bulk만 쓰지 않게 함 |
| `subdermal` | 2 | craft 또는 g2/g3 drop | `ice_shard×12 + combat_module×3 + shield_program×1` | defense/hp/저항이 모두 있어 방어 계열의 첫 큰 목표 |
| `trodes_ninja` | 2 | craft | `data_fragment×10 + rom_echo×2 + glitch_fragment×1` | crit 선택지지만 body보다 덜 강하므로 T1 재료 비중을 유지 |
| `boots_ghost` | 2 | craft | `data_fragment×10 + construct_shard×2 + shield_program×1` | HP/defense의 소형 대안 |
| `militech_deck` | 3 | craft 또는 rare drop | `combat_module×4 + construct_shard×5 + t4_program×1 + t_a_data_fragment×1` | 공격이 아닌 defense/crit deck로 방향 분화 |
| `tactical_body` | 3 | craft | `ice_construct×3 + shield_program×2 + t_a_data_fragment×1 + upgrade_t2×1` | HP/shield/저항을 모두 주는 강한 body라 인증 wafer 필요 |
| `nano_hive` | 3 | craft | `construct_shard×8 + glitch_fragment×2 + loa_chip×1` | 상세 stat은 기존 카탈로그 값을 그대로 사용하고, 제작만 희귀 칩으로 제한 |
| `arasaka_deck` | 4 | craft | `ta_construct×1 + fragment.tessier_archive×1 + t4_program×1 + hosaka_chip×1` | 회사 이름 경쟁이 아니라 T4 계보의 gate로 사용. Arasaka 표지 자체의 원작 귀속은 하지 않음 |
| `kereznikov` | 4 | craft | `hosaka_chip×1 + hosaka_archive×1 + t4_program×1 + upgrade_t4×1` | AP와 regen이 run tempo를 움직이므로 T4 인증과 archive를 요구 |
| `ghost_deck` | 5 | craft 또는 g5 rare drop | `unique_construct×1 + t5_program×1 + wintermute_key×1 + fragment.wintermute_echo×1` | crit/defense 최종 전 deck; rare key가 있어야 함 |
| `master_deck` | 6 | craft, g6 boss drop, 또는 one-time shop | `t6_program×1 + aleph_shard×1 + hosaka_archive×1 + fragment.timeline_echo×1` | 최상위 deck은 반복 구매가 아닌 캠페인 희귀 보상 |
| `master_body` | 6 | craft, g6 boss drop | `unique_construct×1 + t6_program×1 + peripheral_artifact×1 + upgrade_t4×1` | HP/defense/shield/AP를 모두 주므로 최종 body와 경쟁하게 함 |
| `zion_trodes` | 6 | craft 또는 g6 boss drop | `loa_chip×1 + fragment.wintermute_echo×1 + t6_program×1 + maas_neuropozyne_dose×1` | AP bonus 5의 폭발적인 tempo를 최종 계보에 묶음. Zion은 *Count Zero*의 커뮤니티 표지이며 이 장비는 **발명** |

`deck_basic`과 `head_basic`을 제외한 장비는 첫 run에서 반드시 얻어야 하는 것이 아니다. 단, harness의 seeded campaign에서 g3/g4 승리 시 T1/T2 목표 장비 중 하나를 만들 수 있는지, g5/g6 안쪽에서 최종 장비 재료가 실제로 도달하는지 별도로 assert한다.

### 프로그램 재료와 승급

- `t4_program`, `t5_program`, `t6_program`은 소비품이 아니라 recipe ingredient다. 해당 tier 장비의 “설계도”로 재료 인벤토리에서 빠진다.
- `upgrade_t2`는 T0/T1 장비의 `upgradeTo(2)`에만 쓴다. `upgrade_t4`는 T2/T3 장비의 `upgradeTo(4)`에만 쓴다. 업그레이드는 새 장비를 복제하지 않고 원본 ID의 tier variant를 만든다.
- 제안 API는 `craftItem(recipes, itemId, inventory)`를 유지하되, recipe에 `requiresTier`, `consumes`, `grantsEquipmentId`, `oneTime`을 추가한다. `oneTime` recipe는 menu inventory에 unlock flag를 기록한다.
- 직접 drop은 장비를 바로 장착하지 않는다. `loot_table`은 장비 ID를 줄 수 있지만, 동일 장비 중복은 `salvageValue`로 변환하거나 recipe 재료로 넣어야 한다. 첫 구현에서는 direct drop을 g5/g6의 명시적 보상에만 제한한다.

## 3. common material sink와 메뉴 경계

`data_fragment`와 `ice_shard`는 각각 82/97, 81/97 ICE가 드롭하므로 단순히 희귀 레시피에만 넣으면 두 물질이 쌓인다. 따라서 세 층의 sink를 둔다.

1. **제작 sink:** 모든 T1–T2 경로가 두 재료를 함께 요구한다. 특히 `street_deck`, `militech_eyes`, `chrome_gloves`, `trodes_ninja`, `boots_ghost`가 초반 bulk를 소모한다.
2. **정제 sink:** 메뉴의 `ICE recycler`에서 `data_fragment×10 + ice_shard×10`을 `repair_cache×1`로 변환한다. `repair_cache`는 다음 run 시작 시 자동 회복을 올리는 것이 아니라, loot stop에서만 현재 HP를 `max(50% maxHP, currentHP + measuredRepair)`까지 복구하는 **후보** 효과다. 이 수치는 기존 “승리 후 자동 회복 floor 50%”와 중첩되지 않도록 harness로 비교한다.
3. **시장 sink:** `makeInfoMarket`는 재료를 무한 현금화하지 않고, 한 leg당 제한된 3개 offer를 만든다. 후보 offer는 `data_fragment×12 -> credits 8`, `ice_shard×12 -> credits 8`, 또는 `data_fragment×6 + ice_shard×6 -> one common consumable`. 가격·한도는 인플레이션 측정 대상이다.

중요한 상태 수정은 다음이다.

```ts
// 잘못된 경계: run 시작 때 menu inventory를 덮어씀
this.inventory = initial.inventory

// 제안: menu wallet에서 run snapshot을 만들고, 종료 시 merge
this.run = createRun({
  deck: clone(menu.deck),
  credits: menu.credits,
  materials: clone(menu.materials),
  equipment: clone(menu.equipment),
})

onRunEnd(run) {
  menu.materials = addStacks(menu.materials, run.materialsEarned)
  menu.equipment = mergeUnique(menu.equipment, run.equipmentEarned)
  menu.credits += run.credits
}
```

`materials`는 run 중에도 보이지만, 실패 시 보존할지 여부는 소유자가 정해야 한다. 제안은 **획득한 material은 실패해도 메뉴에 보존**, credits와 임시 HP/보드는 reset이다. 이것이 실패를 “전부 사라지는 inert drop”으로 만들지 않으면서, 장비 제작까지의 장기 목표를 만든다. 이 보존 여부는 survival harness에서 실패 run의 retry rate와 평균 장비 도달 leg를 측정한다.

## 4. 읽히지 않는 스탯의 배선

`totalStats()`가 이미 합산하므로 새 수치는 equipment 정의에 추가하지 않는다. 전투 시작 시 `derivePlayerStats(equipment, run)` 한 번만 계산해, 각각의 읽기 위치를 단일 함수로 만든다.

| 스탯 | 읽을 위치와 효과 | 곡선 이동 방향 |
|---|---|---|
| `defense` | ICE가 플레이어에게 주는 raw damage 직전에 `max(0, raw - defense)` 적용. 카드 비용이나 ICE phase rollback에는 적용하지 않음 | 생존율 상승, 평균 HP 손실 하락. 큰 defense에서 boss 4-phase가 지나치게 안전해질 위험 |
| `hpBonus` | PREP에서 `maxHP = baseMaxHP + hpBonus`; mission reset 때 maxHP는 유지하고 current HP만 지정된 reset 규칙으로 설정 | 생존율 상승. 자동 회복 floor가 `50% maxHP`라 recovery도 함께 커짐 |
| `shieldBonus` | leg 시작 시 `shield = baseShield + shieldBonus`; 받은 피해가 먼저 shield를 깎고 남은 양이 HP로 감. shield는 mission/전투 reset 규칙에 맞춰 새로 생성 | 초반과 첫 boss에 특히 강한 생존 상승. shield가 매 phase 재생되지 않게 해야 함 |
| `apBonus` | PREP/전투 시작 AP 상한 또는 시작 AP에 더함. `COST`는 그대로 유지 | 한 턴당 카드 수 증가, 공격 곡선 상승. g5/g6 one-fight kill을 가장 직접적으로 앞당김 |
| `apRegenBonusPct` | enemy phase 종료 후 AP regen 계산에 `floor(baseRegen * (100 + bonus)/100)` 적용. 최소 regen은 기존 규칙을 따름 | 긴 전투에서 상승; cost가 낮은 덱에서 과대 효과 가능 |
| `programPower` | 카드 효과 계산의 tier/표준 damage를 직접 대체하지 않고, 프로그램의 ICE 상호작용에만 사용. 후보식은 `effectiveTier = tier + floor(programPower / measuredProgramStep)`가 아니라, 우선 `programPower`를 armor bypass 또는 status check에 연결 | armor 높은 g3+에 강해짐. damage 공식을 몰래 바꾸면 기존 카드 가치 계약을 깨므로 별도 로그 필요 |
| `iceResistance` | ICE status/extra effect가 주는 피해·지속 phase를 `max(0, effect - resistance)` 또는 저항 퍼센트로 줄임. armor와 합치지 않음 | 특수 패턴 상대 생존 상승, 평타 boss curve에는 영향이 적어야 함 |
| `grantsSkillId` | PREP에서 장비 세트가 해당 skill을 unlock. skill은 run당 1회/쿨다운을 가지며, 장비를 빼면 사용 불가 | 직접적인 burst/유틸 상승. 가장 위험한 숨은 power이므로 로그에 skill source를 남김 |
| `extraEffect` | 카드/장비 발동 시 `resolveExtraEffect(effect, context)`라는 whitelist resolver만 호출. 임의 문자열 실행 금지. 예: 다음 card의 armor check 무시, loot reroll 1회 | 효과마다 다름. 기본 구현은 전투 damage가 아닌 제한된 utility로 시작 |

### 방어 단계의 정확한 순서

한 ICE 행동의 피해는 다음 순서로 기록한다. 이 순서를 고정해야 defense와 armor가 서로의 의미를 침범하지 않는다.

```ts
function receiveIceDamage(raw: number, stats: PlayerStats, state: CombatState) {
  const resisted = applyIceResistance(raw, stats.iceResistance, state.effectType)
  const afterDefense = Math.max(0, resisted - stats.defense)
  const absorbed = Math.min(state.shield, afterDefense)
  state.shield -= absorbed
  state.hp -= afterDefense - absorbed
  return { raw, resisted, afterDefense, absorbed, hpDamage: afterDefense - absorbed }
}
```

이 함수는 카드 damage의 `tier * 5 - armor` 경로와 별개다. 플레이어 defense를 카드 armor에 적용하지 않는다. `defense`, `hpBonus`, `shieldBonus`, `apBonus`, `apRegenBonusPct`, `programPower`, `iceResistance`, `grantsSkillId`, `extraEffect` 모두 combat log에 `sourceEquipmentIds`와 함께 남겨야 한다. 측정 harness는 장비 없는 seed와 장비 하나만 바꾼 seed를 비교한다.

## 5. economy arithmetic와 harness 계약

현재 첨부된 브리프에는 “기록된 g3/g4/g5 곡선”의 숫자 자체가 없고, 97 ICE 전체에 대한 드롭 발생 횟수만 있다. 그러므로 다음이 현재 계산 가능한 유일한 표본이다.

- `data_fragment`: 82/97 = 약 84.5%의 ICE가 드롭
- `ice_shard`: 81/97 = 약 83.5%
- `combat_module`: 15/97 = 약 15.5%
- `construct_shard`: 12/97 = 약 12.4%
- `ice_construct`: 7/97 = 약 7.2%

이 비율은 “한 ICE가 한 번만 loot roll을 한다”는 가정에서도 드롭 기회의 상한/분포를 보여줄 뿐, g3/g4/g5 **임무의 평균 ICE 수·credits·loot quantity**를 알려주지 않는다. 따라서 전형 run의 수입은 다음 로그를 먼저 추가해야 한다.

```ts
type MissionEconomySample = {
  seed: number
  missionTier: 3 | 4 | 5
  iceDefeated: number
  creditsBefore: number
  creditsEarned: number
  materialsEarned: Record<string, number>
  crafts: Array<{ itemId: string; cost: Record<string, number> }>
  marketSinks: Record<string, number>
  repairCachesSpent: number
}
```

그 다음 각 tier의 중앙값과 p10/p90을 산출한다.

```text
runIncome(tier) = median(sum creditsEarned over that mission tier)
runMaterial(tier, id) = median(sum material[id] over that mission tier)
runSpend(tier) = median(craft + market + repair material consumed)
closure(tier) = runSpend / runIncomeInMaterialEquivalent
```

**후보 목표**(확정값 아님)는 다음처럼 검증한다. g3 mission의 중앙값 수입으로 T1 장비 1개 또는 repair cache 몇 개 중 하나를 살 수 있어야 한다. g4는 T2/T3 recipe를 향해 material gate를 한 단계 진전시켜야 한다. g5는 최종 장비를 완성시키지 않되, `t5_program`/unique 계보의 일부를 제공해야 한다. g6 direct drop은 `master_*` 중 하나를 완성할 수 있는 마지막 piece가 될 수 있지만, g6 전투가 반복 farm으로 변하지 않도록 one-time claim을 측정한다.

각 후보 recipe의 cost는 다음 테스트를 통과하거나 조정한다.

```text
craftableAtTier(item, tier) =
  P(material inventory after missions at grade == tier >= recipe cost) >= 0.50
  # 2026-11-18 (ADR-0324): 풀은 '등급 == tier'. '등급 <= tier' 는 등급별로 국소화된
  # 희귀 게이트를 도달 불가로 만들었다 (낮은 등급이 풀을 희석).

commonPileup(id) =
  median(material[id] at ENDING) - median(material[id] consumed) > ownerThreshold
```

`ownerThreshold` 역시 소유자가 정할 값이다. 임시 시작값을 넣는다면 `data_fragment`와 `ice_shard` 각각 평균 1 recipe 이상이 남는지와, ENDING에서 3 mission을 끝내도 3–5 recipe분 이상 무소비로 누적되는지를 별도 리포트한다. `credits`는 material 가격을 합산해 이중 계산하지 않는다. credits 시장과 craft 재료는 서로 다른 지갑이며, 시장 환전량·offer 수를 로그로 제한한다.

## 6. 구현 순서와 테스트

1. 데이터 파일을 추가한다: `materials.json`, `recipes.json`, `sets.json` 또는 현재 registry가 기대하는 동등한 TypeScript 상수. 모든 28 material과 18 equipment ID에 대해 schema test를 둔다.
2. `makeRecipesFromData`, `makeMaterialsFromData`, `makeInfoMarket`를 빈 객체 호출에서 실제 data import로 바꾼다. 빈 registry는 개발 환경에서 throw한다.
3. `loot_table -> run.inventory.materials`를 유지하고, run 시작 시 menu inventory를 덮어쓰지 않는 snapshot/merge 경계를 구현한다.
4. `craft`와 `buy` action을 메뉴에 연결한다. craft는 재료 차감과 장비 소유를 한 transaction으로 처리한다.
5. `use_item`을 추가한다. 첫 consumable은 `maas_neuropozyne_dose`를 후보로 하되, 효과 수치는 harness 전까지 placeholder로 둔다. 사용 불가능한 T3 희귀물을 자동 소비시키지 않는다.
6. `receiveIceDamage`를 combat phase에 연결한다. AP와 program stats는 각각 AP 계산기와 program resolver에서만 읽는다.
7. loot stop의 자동 회복과 repair cache가 중복되지 않는지 seeded campaign으로 확인한다.

최소 테스트 목록은 다음과 같다.

- 28 material이 모두 registry에 존재하고 tier/role이 누락되지 않는다.
- 18 equipment이 모두 craft/drop/buy 중 하나의 reachable path를 가진다.
- `craftItem`은 부족한 재료에서 inventory를 부분 차감하지 않는다.
- run 시작 전 menu material은 유지되고, run 종료 시 획득 material은 한 번만 merge된다.
- 실패 run의 보존 정책이 seed마다 동일하다.
- defense는 raw ICE damage를 줄이고, 카드가 ICE에 주는 damage에는 영향을 주지 않는다.
- shield가 HP보다 먼저 소모되고, `hpBonus`는 recovery floor 계산에 일관되게 반영된다.
- `grantsSkillId`와 `extraEffect`는 whitelist 밖의 문자열을 실행하지 않는다.
- balance/survival/campaign 출력에 recipe spend, material pileup, stat contribution이 포함된다.

## 7. 리스크와 가장 위험한 가정

가장 위험한 가정은 **“재료를 실패 후에도 보존하면 common sink가 충분히 작동하고, 동시에 장비 목표가 재미를 만든다”**는 것이다. 보존은 장기 진행을 살리지만, `data_fragment`와 `ice_shard`가 run 실패마다 계속 쌓이면 결국 제작 화면이 선택지가 아니라 누적된 부채 목록이 된다. 반대로 보존하지 않으면 28개 drop이 다시 inert하게 느껴질 수 있다.

가장 싼 반증 측정은 새 전투를 만들지 않고 기존 deterministic seed 100개를 replay하는 것이다. 각 seed에 대해 실패/승리 여부, ENDING의 common stack, T1/T2 첫 craft까지 필요한 run 수, 메뉴에서 실제로 사용된 common 비율을 기록한다. `common material consumed / common material earned`가 owner가 정한 최소선보다 낮거나, 첫 craft가 대부분의 seed에서 불가능하면 repair cache의 비용·시장 offer·recipe cost 중 하나만 바꿔 재측정한다.

두 번째 위험은 `defense`와 `hpBonus`가 자동 회복 floor와 결합해 곡선을 동시에 밀어 올리는 것이다. 장비 없는 baseline, defense-only, hp-only, shield-only를 같은 seed에서 비교해 boss별 damage taken과 g5/g6 survival을 기록한다. AP와 `programPower`는 g5/g6의 한 전투 kill 여부를 바꿀 가능성이 커서, 이 둘은 평균 생존율보다 “한 전투 안에 죽인 boss phase 수”를 먼저 본다.

세 번째 위험은 원작 고유명사가 시스템 기능을 과도하게 설명하는 것이다. `Wintermute key`, `loa chip`, `Zion trodes`는 표지와 분위기에만 쓰고, 원작의 사건이나 인물 관계를 게임의 사실로 재서술하지 않는다. 원작에서 확인되는 이름과 이 게임이 발명한 드롭·효과를 UI tooltip에서도 같은 방식으로 구분한다.

## References

[1]: https://books.google.com/books/about/Neuromancer.html?id=TiMKzwEACAAJ "Neuromancer — William Gibson, Google Books description"
[2]: https://books.google.com/books/about/Count_Zero.html?id=dFX1xN7q-AgC "Count Zero — William Gibson, Google Books description"
[3]: https://books.google.com/books/about/Mona_Lisa_Overdrive.html?id=wbdaAAAAMAAJ "Mona Lisa Overdrive — William Gibson, Google Books description"

---

# 부록 — 실측 verdict (2026-11-18, `npm run crafting`)

위 비용표를 **그대로 구현하면 안 된다.** 결정적 시드를 replay 해 측정했고, 결과가 제안을 반증한다.

## 측정 방법

`web/scripts/crafting_probe.ts` = `npm run crafting` — 기존 시드 replay(새 시뮬레이션 없음), 등급별로
`--runs`(기본 3)회 실행해 지갑을 누적하고, 후보 레시피 18종의 도달률과 common 적체를 계산한다.
레시피 후보는 `web/scripts/crafting-recipes-candidate.json`.

## 결과 1 — 드롭 경제 (실측)

| 재료 | 드롭 ICE | **기대값/킬** | chance | qty |
| --- | ---: | ---: | ---: | ---: |
| `data_fragment` | 82 | **0.654** | 1.00 | 6 |
| `ice_shard` | 81 | **1.433** | 1.00 | 10 |
| `combat_module` | 15 | **0.125** | 1.00 | 3 |
| `construct_shard` | 12 | 0.174 | 1.00 | 3 |
| `ice_construct` | 7 | 0.039 | 0.70 | 1 |
| `rom_echo` | 4 | **0.012** | 0.30 | 1 |
| `glitch_fragment` | 4 | **0.006** | 0.18 | 1 |
| `shield_program` | 2 | **0.003** | 0.15 | 1 |
| `t4_program` | 1 | **0.001** | 0.10 | 1 |
| `hosaka_archive` | 1 | **0.001** | 0.05 | 1 |
| `wintermute_key` | 1 | 0.002 | 0.15 | 1 |

미션당 킬 수는 `data_fragment` 실측(1.75/런) ÷ 기대값(0.654/킬) ≈ **3킬**로 역산된다.
즉 `rom_echo` 는 **미션당 약 0.04개** — 하나 얻는 데 **약 25미션**이 걸린다.

## 결과 2 — 도달률 **18종 전부 0.0%**

```
deck_street        T1  0.0%  data_fragment×8 ice_shard×6 rom_echo×1
eyes_militech      T1  0.0%  data_fragment×6 combat_module×1 rom_echo×1
…                  …   0.0%  …
```

**원인은 common이 아니라 초희귀 재료 1개다.** `deck_street` 는 `data_fragment×8 + ice_shard×6` 를
g3에서 이미 충족하는데(3런 누적 df 9, ice_shard 15), **`rom_echo×1` 이 없어 0%** 가 된다.
T1 세 종이 각각 `rom_echo` · `combat_module` · `glitch_fragment` 를 요구하는데, 앞뒤 둘은 사실상 안 나온다.

## 결과 3 — common은 **모자란다** (적체가 아니다)

| 재료 | g3–g6 3런 중앙값 | 18종 전체 제작 계획 소요 | 판정 |
| --- | ---: | ---: | --- |
| `data_fragment` | 16.0 | 41 | **SHORT** |
| `ice_shard` | 18.0 | 32 | **SHORT** |
| `combat_module` | 2.0 | 9 | SHORT |
| `construct_shard` | 1.0 | 19 | SHORT |

Manus는 common이 **쌓일 것**을 걱정했지만, 실측은 반대다 — **희귀 게이트가 제작을 막아서** common이
쓰이지 못하고 남는다(적체의 원인은 희귀 재료 쪽이다).

## 결과 4 — 시장 가격이 3자릿수 배 어긋난다

실측 런 수입 중앙값: **g3 9,860cr / 3런 ≈ 3,300cr/런**(g4 14,400/3 ≈ 4,800, g5 ≈ 4,840).
Manus의 offer `data_fragment×12 → credits 8` 은 12개를 **8크레딧**에 파는 것 — 한 런의 df(≈3)로 2크레딧을
버는 셈이라 **의미가 없다**. 가격은 크레딧 수입과 같은 자릿수에서 다시 정해야 한다.

## 교정 제안 (측정 근거)

| # | 교정 | 근거 |
| --- | --- | --- |
| 1 | **T1은 common + `combat_module`(0.125/킬) 이하만 요구한다.** `rom_echo`·`glitch_fragment` 는 T2+로 올린다 | 기대값/킬이 0.01 미만이면 T1 게이트로 부적합 |
| 2 | 희귀 게이트를 쓰려면 **드롭률을 올리거나**(chance/드롭 ICE 수), **수량 요구를 낮춘다** | `hosaka_archive` 0.05 chance × 1 ICE = 사실상 캠페인 1회용 |
| 3 | **`upgrade_t*` 는 희귀 게이트로 쓰지 않는다** — 각 1개 ICE, 0.2/0.3 chance | 승급 인증이 곧 병목이 되면 승급이 죽는다 |
| 4 | 시장 offer 가격을 **크레딧 수입 자릿수**(≈3,000cr/런)에 맞춘다 | 위 결과 4 |
| 5 | `craftableAtTier` 목표(≥0.50)를 **측정 가능한 통과 기준**으로 유지한다 | `npm run crafting` 이 그대로 판정한다 |

## 비용표 2판 — 교정 반영 결과 (2026-11-18, ADR-0324)

교정 1~4를 반영하고, **판정 풀을 `등급 == tier` 로 고친 뒤**(위 계약 개정) 하네스가 전부 통과했다.
비용표 정본: `web/scripts/crafting-recipes-candidate.json`. 결정: ADR-0324.

| tier | 항목 | 비용 | P(afford) |
| --- | --- | --- | --- |
| T1 @3런 | deck_street / eyes_militech / gloves_chrome | `df×3+ice_shard×5` / `df×3+ice_shard×4` / `df×4+ice_shard×3` | 58.3 / 70.8 / 70.8% |
| T2 @8런 | corporate / subdermal / trodes_ninja / boots_ghost | `df×16+ice_shard×4` / `df×12+ice_shard×4` / `df×18+ice_shard×3` / `df×15+ice_shard×4` | 56.7 / 56.7 / 58.3 / 56.7% |
| T3 @8런 | militech / tactical / nanohive | `df×20+cm×1` / `df×16+cm×1` / `df×22+cm×1` | 53.6% ×3 |
| T4 @8런 | arasaka / kereznikov | `ice_shard×50+cm×2+cs×1` / `ice_shard×45+cm×2+cs×1` | 54.8% ×2 |
| T5 @8런 | ghost | `combat_module×30+construct_shard×20` | 78.7% |
| T6 @8런 | master / master_body / zion | `cm×12+cs×8+t6_program×1` / `cm×10+cs×6+aleph_shard×1` / `cm×10+cs×6+t6×1+aleph×1` | 63.9 / 66.7 / 63.9% |

핵심: **등급마다 실제로 나오는 common 이 다르다.** g4 ICE 는 `data_fragment` 중앙값 **16** / `ice_shard` **74** 라서
T4 를 df 로 게이트하면 27.4% 로 막힌다. 또 g2 ICE 가 `upgrade_t2` 를 8런 중앙값 **3개** 뱉어, 교정 #3 의
"`upgrade_t*` 는 병목" 전제는 실측과 어긋난다(비용표에는 여전히 미사용 — g1 에 안 나옴).

## 남은 것

- ~~비용표 2판 미작성~~ → **작성·통과** (위 절 · ADR-0324).
- `--runs` 를 늘리면(예: 5–8) 희귀 재료의 상위 분위가 드러난다(중앙값 0은 "절반이 0"이라는 뜻).
- 재료를 실패 런에서 보존할지는 여전히 **오너 결정 1번**이다 — 이 실험은 보존을 가정했다(ADR-0323 으로 구현됨).
