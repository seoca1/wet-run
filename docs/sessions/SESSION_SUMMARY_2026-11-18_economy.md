# 세션 요약 + 핸드오프 — 2026-11-18 (경제·장비 배선, 이어서)

> **범위**: 크래프팅 비용표 → 데이터·소유 → 방어 단계 → programPower → 재조정 → drop → 소비 아이템 → 시장 → extraEffect
> **상태**: 전부 커밋 완료. **다음 첫 작업 = `matrix_*`/`zion_support`/`ice_omniscience` 훅 또는 AP/스킬** (§4)
> **앞선 같은 날 세션**: [`SESSION_SUMMARY_2026-11-18.md`](./SESSION_SUMMARY_2026-11-18.md) (ADR-0319~0323) — 이 문서는 그 핸드오프의 §4 "그 다음"을 이어받은 **후속**이다.

---

## 1. 이번 세션에 한 것 (9개 슬라이스, ADR-0324~0332)

| ADR | 결정 | 커밋 |
| --- | --- | --- |
| **0324** | 비용표 2판 + `craftableAtTier` **판정 풀을 `등급 == tier` 로** (등급 ≤ tier 는 희귀 게이트를 도달 불가로 만들었다) | `0f0092c4` |
| **0325** | `recipes.json`(16)·`materials.json`(28) 데이터 + **장비 소유 모델**(`owned_equipment.ts`) + 크래프팅 배선 | `736717b7` |
| **0326** | **플레이어 방어 단계**(`저항 → 방어 → 실드 → HP`) + `hpBonus`/`shieldBonus` + `npm run gear` 프로브 | `ed37dcfa` |
| **0327** | `programPower` = **armor bypass**(상한 60%) — 9종 live | `5f79cdeb` |
| **0328** | **장비 재조정** — 수작업 소규모 재설계(균일 스케일은 저티어를 0으로 만듦) | `c0814c63` |
| **0329** | **장비 drop 경로** — loot salvage 슬롯(9), 미션당 1회 결정론적 롤 | `f12a345a` |
| **0330** | **소비 아이템**(loot 슬롯 10) + **hoard 지출 버그 수정**(`menu + (run − seed)`) | `a19c77bf` |
| **0331** | **재료 시장** — loot 슬롯 11, 런의 크레딧으로 재료 구매 | `6aed6c0b` |
| **0332** | **`extraEffect` whitelist resolver** — 임의 문자열 실행 금지 + 2동작 배선 | `9bbe9225` |

+ 워크스페이스 경로 점검·정리 (별도 repo 커밋 `51b34c2`).

---

## 2. 현재 기준선 (이 세션 종료 시점 실측)

| 하네스 | 값 |
| --- | --- |
| `npm run balance` (단일 교전) | `100 / 100 / 100 / 97.1 / 70.6 / 47.0` — **세션 내내 byte-identical** |
| `npm run survival` (미션, 64시드) | `100 / 100 / 83.4 / 83.1 / 25.9 / 42.2` (목표 `100/95/80/50/25/30`) |
| `npm run gear` (장비 착용, 신규) | bare `83/83/26/42` → T1 `85/85/28/49` → T2 `98/97/40/64` → T4 `100/100/60/77` → T6 `100/100/63/81` |
| `npm run crafting` (비용표 판정) | T1 3종 ≥50% @3런 · T2~T6 13종 ≥50% @8런 |
| vitest | **236 files / 4443 tests** |
| 게이트 7종 | CLEAN (`audit_vault` · `mixed_language` · `check_doc_claims` · `audit_sprawl` · `check_no_novel_prose` · `import_briefings --check` · build) |

> **중요**: 기록된 기준선(balance/survival)은 **bare runner**(`EMPTY_LOADOUT`) 기준이다. 이번 세션의 모든 배선은
> bare 에 대해 **no-op** 이라 byte-identical 을 유지했다. 장비 착용 곡선은 `npm run gear` 로 **별도** 측정한다.

---

## 3. 이 세션의 핵심 발견 (다음 세션이 전제로 삼을 것)

1. **판정 도구가 답을 막고 있었다** — `craftableAtTier` 의 "등급 ≤ tier" 풀은 등급-국소 희귀 게이트(g6 전용
   `t6_program` 등)를 **원리적 도달 불가**로 만들었다. 풀을 `등급 == tier` 로 고쳐야 사다리가 살아난다(ADR-0324).
2. **장비 스탯 12개 중 9개가 안 읽혔고, 4종은 "미배선"이 아니라 서브시스템 부재**였다 —
   `apBonus`/`apRegenBonusPct`(AP 자원 없음) · `grantsSkillId`(플레이어 스킬 없음) · `extraEffect`(resolver 없음).
   `programPower` 만 배선 가능(ADR-0327), `extraEffect` 는 ADR-0332 로 resolver 신설.
3. **난이도 곡선이 장비에 여유가 거의 없다** — bare g5/g6 26/42% 에서 유의미한 스탯 패키지 하나면 60~100%.
   그래서 "완만" 목표를 맞추려면 장비가 **거의 코스메틱** 수준으로 작아야 하고, 균일 스케일은 저티어 스탯을 0으로
   만든다(ADR-0328). **장비 파워와 난이도는 함께 설계되어야 한다** — 최대 미해결 항목.
4. **hoard 병합이 지출을 삼켰다** — `menu + max(0, run − seed)` 는 런이 hoard 재료를 **소비**하면 지출을 지운다.
   런 중 재료 소비 경로가 없어 ADR-0323 시점엔 드러나지 않았다(ADR-0330 에서 수정).
5. **크레딧에 소비처가 없었다** — 읽는 곳은 엔딩 `control` 게이트뿐. ADR-0323 이 credits 를 메뉴에 합치지 않으므로
   **메뉴 화면의 시장은 항상 무일푼** → 시장은 **런 중**(loot stop)에 있어야 한다(ADR-0331).

---

## 4. 🔥 다음 세션 작업 (순서대로)

1. **남은 `extraEffect` 4종 훅** — `matrix_stealth` · `matrix_speed`(매트릭스 경로) · `zion_support` ·
   `ice_omniscience`(전투). resolver 와 이름은 이미 등록되어 inert 상태다.
2. **AP 자원 · 플레이어 스킬** 서브시스템 — 마지막 2개 미배선 스탯(`apBonus`·`apRegenBonusPct`·`grantsSkillId`).
   `combat_models.ts` 에 prototype `Combatant.ap`/`Skill` 이 있지만 활성 게임은 안 쓴다(활성 모델은 COST+hand size).
3. **장비 파워 ↔ 난이도 동시 설계** — ADR-0328 의 남은 긴장. 오너 결정 필요(밴드/난이도 스케일).
4. **수치 확정(오너)** — 시장 가격(`material_market.ts`) · 소비 아이템 효과(`consumables.ts`) ·
   장비 드롭 확률(`equipment_drops.ts` `EQUIPMENT_DROP_CHANCE`).
5. **작은 UI**: loot footer 힌트가 슬롯 11개로 80열에서 `4-11 options` 짧은 형식으로 넘친다 — 압축.

### 검증 명령
```bash
cd Game/wet_run/web
npm test && npm run typecheck && npm run lint && npm run build
npm run balance && npm run survival -- --seeds 64 --cards best --loot value
npm run gear          # 장비 착용 곡선 (신규)
npm run crafting -- --seeds 12 --runs 3
# 게이트 7종 (워크스페이스 루트에서)
cd ../.. && python3 scripts/audit_vault.py && python3 scripts/mixed_language_audit.py
cd Game/wet_run && python3 scripts/check_doc_claims.py && python3 scripts/tools/audit_sprawl.py \
  && python3 scripts/check_no_novel_prose.py && python3 scripts/tools/import_briefings.py --check
```

---

## 5. ⚠️ 함정 (다음 세션이 반드시 알 것)

| 함정 | 내용 |
| --- | --- |
| **기록 기준선은 bare runner** | balance/survival 는 `EMPTY_LOADOUT` 으로 잰다. 장비/소비/시장 배선은 bare 에 no-op 이라 byte-identical 을 유지해야 한다 — 깨지면 **버그**다 |
| **롤은 `Math.random` 을 소비하지 않는다** | 장비 드롭·카드 offer 는 `missionSeedOf ^ hash(id)` 로 시드한다. `Math.random` 을 추가 소비하면 **전투 스트림이 이동해 모든 기록 곡선이 바뀐다**(ADR-0321 전례) |
| **판정 풀을 되돌리지 말 것** | `craftableAtTier` 는 `등급 == tier`. "등급 ≤ tier" 로 되돌리면 희귀 게이트가 다시 도달 불가가 된다 |
| **loot 슬롯 번호는 11개** | 1-3 card · 4 repair · 5 intel · 6 vent · 7 burn · 8 syphon · 9 gear · 10 use · 11 buy. 추가 시 `maxSlot` 계산과 레이아웃 테스트 2건(`run_screen.test.ts`, `adr0299_*`)이 함께 움직인다 |
| **카탈로그 스탯은 저작값이 아니라 튜닝값** | ADR-0328 로 재조정됨. 테스트는 **속성 기반**(상대 비교)으로 바꿔 두었다 — 절대값으로 되돌리면 재조정마다 56개가 깨진다 |
| **`decisions/` 는 Accepted = immutable** | 새 결정은 신규 ADR(다음 번호 0333). 결정 내용 변경 필요 시 supersede |
| **e2e 영향** | 이번 세션은 새 화면/키를 추가하지 않았다(loot 슬롯은 기존 화면). e2e 드라이버 수정 불필요 |

---

## 6. 오너 결정 대기

| # | 결정 | 현재 상태 |
| --- | --- | --- |
| 1 | **장비 파워 ↔ 난이도** (ADR-0328 남은 긴장) | 장비는 현재 "완만" 밴드. 난이도 스케일 여부 미정 |
| 2 | 시장 가격 · 소비 아이템 효과 수치 | placeholder (측정 스케일) |
| 3 | 장비 드롭 확률 (`EQUIPMENT_DROP_CHANCE=0.4`) | placeholder. 낮추면 g6(3미션) 경로가 죽는다 |
| 4 | SRW 케이스 기본 표(ADR-0321, 기본 0) | 미정 (이전 세션 이월) |
| 5 | `ICE recycler` 정제 sink | 미정 (이전 세션 이월) |

---

## 7. 이전 세션에서 이월된 것 (이번 세션에 안 건드림)

- **Fiction 백필 후속**: `import_briefings.py --check` 는 통과(33/33)하지만, 대시보드 `missions.json` `story.source`
  포인터 오류 3건(`ta_heist`/`mollys_razor`/`construct_memory_rescue`), 임포터 `SLOP_MARKERS` 추가,
  쌍둥이 diff 35건 정본 선택.
- **고아 소설 미션 id 173~181개** — 게임에 없는 이야기들(별도 콘텐츠 슬라이스).
- **허브 대사 3편**(`wim_hub`·`maelcum_intro`·`maelcum_caught`) — 대화 트리 화면 필요.
