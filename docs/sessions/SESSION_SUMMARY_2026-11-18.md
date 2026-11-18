# 세션 요약 + 핸드오프 — 2026-11-18

> **범위**: 성장·전투 피드백·확률 전투·시스템 감사·Manus 설계·재료 보존
> **상태**: 전부 커밋·푸시 완료. **다음 세션 첫 작업 = 비용표 2판** (§4)
> **경고**: 이 세션은 **밸런스 계약을 두 번 움직였다**(ADR-0319 회복, ADR-0321 케이스). 기록된 목표는 재기록했지만 §5의 함정을 먼저 읽을 것.

---

## 1. 이번 세션에 한 것

| ADR | 결정 | 커밋 |
| --- | --- | --- |
| **0319** | 매 전투 승리 시 **HP 50% floor** 자동 회복 (grant 아님) | `0ccdb0c6` |
| **0320** | 손패에 **실피해 범위** · ICE 에 **armor `A7`** · `armor_block` VFX · 큰 타격 흔들림 3px | `5a9b69af` |
| **0321** | **SRW식 케이스**(MISS 0 / GUARD 절반 / HIT) — **기본 표 0**(다이얼), `cloak` 이 진짜 회피 | `4fc9f7c6` |
| **0322** | **EQUIPMENT 배선**(죽은 축) + HUD 성장 한 줄 `Deck n · T평균 [· UNQ k]` | `35a0c735` |
| **0323** | **재료 보존** — 런이 *번* 것만 hoard 에 합침(3경로), `localStorage` | `984af61d` |

+ 설계 문서 3:
- `docs/design/system-map-2026-11-18.md` — **배선표 + 빈 곳**(입구는 됐고 출구가 비었다)
- `docs/design/growth-plan-2026-11-18.md` — 성장 4층·4축 + 측정
- `docs/design/crafting-and-equipment-proposal-2026-11-18.md` — **Manus 제안 + 실측 verdict 부록**

+ 하네스 1: **`npm run crafting`** (`scripts/crafting_probe.ts`) — 후보 레시피 도달률/적체 판정기.

---

## 2. 현재 기준선 (이 세션 종료 시점 실측)

| 하네스 | 값 |
| --- | --- |
| `npm run balance` (단일 교전) | `100 / 100 / 100 / 97.1 / 70.6 / 47.0` |
| `npm run survival` (미션, 스마트) | `100 / 100 / 83.4 / 83.1 / 25.9 / 42.2` (목표 `100/95/80/50/25/30`) |
| `npm run campaign` (계약) | 완주 **46.4%** · g3 50.9 · g4 61.4 · g5 3.1 · g6 20.3 |
| vitest | **228 files / 4380 tests** |
| e2e | **54 passed / 0 failed** (5 skipped) |

---

## 3. 이 세션의 핵심 발견 (다음 세션이 전제로 삼을 것)

1. **이기는 플레이에서 덱은 자라지 않는다** — 미션 종료 덱 g3 **5.03** · g4 **5.02**장(시작 5장). 항상-카드는 6.18/6.38장이지만 승률 58/54%. **수리 슬롯이 성장을 먹는다.**
2. **성장↔난이도가 같은 손잡이다** — 덱이 자라기 시작하는 회복 floor 는 **90%**(5.03→7.18), 대가는 **g4 가 100%**.
3. **등급 ≠ 난이도 대역** (ADR-0318 (f) → ADR-0319 로 분리): g4 의 난이도는 **소모전**(floor 가 지움: 분포 1.6~100% → **59~100%**), g5 는 **싸움 자체**(1.6~87.5% **변화 없음**).
4. **드롭 28종은 막다른 길이었다** — 소비처 0 + 런마다 증발. **이제 보존된다**(ADR-0323).
5. **장비 18종은 획득 경로가 0** — tier-0 기본만 장착 가능(기본값은 전투가 안 읽어 밸런스 무영향).
6. **장비 스탯 12개 중 9개를 아무도 안 읽는다** — 플레이어 방어 단계 자체가 없다.
7. **Manus 비용표는 측정을 못 넘었다** — 18종 도달률 **0.0%**. 원인은 common 이 아니라 **초희귀 재료 1개**(`rom_echo` 0.012/킬 ≈ 25미션).

---

## 4. 🔥 다음 세션 첫 작업 — **비용표 2판**

### 목표
Manus 제안의 비용표를 **교정 1~4 반영해 다시 쓰고**, `npm run crafting` 이 `craftableAtTier ≥ 0.50` 을 통과하는지 판정한다.

### 교정 (실측 근거는 제안서 부록)
| # | 교정 |
| --- | --- |
| 1 | **T1 은 common + `combat_module`(0.125/킬) 이하만** — `rom_echo`(0.012)·`glitch_fragment`(0.006)는 T2+ |
| 2 | 희귀 게이트는 **드롭률을 올리거나** 요구량을 낮춘다 (`hosaka_archive` = 1 ICE × 0.05) |
| 3 | **`upgrade_t*` 를 게이트로 쓰지 않는다** (각 1 ICE → 승급이 곧 병목) |
| 4 | 시장가를 **크레딧 수입 자릿수**(≈3,000cr/런)에 맞춘다 (제안 `df×12 → 8cr` 는 무의미) |

### 절차
```bash
cd Game/wet_run/web
# 1. 비용표 후보를 고친다 (Manus 이름 → 실제 id 매핑 주의)
$EDITOR scripts/crafting-recipes-candidate.json
# 2. 판정
npm run crafting -- --seeds 12 --runs 3      # 도달률 ≥ 50% 를 확인
npm run crafting -- --seeds 12 --runs 8      # 희귀 재료의 상위 분위 확인(중앙값 0 은 "절반이 0")
# 3. 드롭률을 올려야 하면 데이터 쪽
$EDITOR src/data/ice_types.json              # loot_table 의 chance / quantity
```
**합격 기준**: T1 이 2~3런 안에 ≥50%, T2 가 5~8런 안에 ≥50% (오너 미확정 시 이 기본 가정).
**주의**: 비용표는 `web/scripts/crafting-recipes-candidate.json` 에 있고 **장비 id 는 접두사가 실제와 반대**로 적힌 Manus 표기를 이미 매핑해 두었다 — 새로 추가할 때 `deck_street` 형식을 쓸 것.

### 그 다음 (순서대로)
1. **데이터 파일 생성** — `materials.json` · `recipes.json` 을 만들고 `main.ts` 의 `makeRecipesFromData({})` 를 실제 import 로 교체. **빈 registry 는 throw** 하게.
2. **`craftItem` 화면 연결** — 크래프팅 화면이 recipe 를 그린다 + `craft`/`buy` 액션. 재료 차감과 소유를 한 transaction 으로.
3. **미사용 스탯 9종 배선** — 특히 **없는 플레이어 방어 단계**. 순서 고정: `저항 → 방어 → 실드 → HP`(카드의 armor 경로와 **분리**). `apBonus`·`programPower` 가 g5/g6 를 가장 크게 흔든다 → 곡선 측정 필수.
4. **`use_item`** — 첫 소비 아이템 후보 `maas_neuropozyne_dose`.

---

## 5. ⚠️ 함정 (다음 세션이 반드시 알 것)

| 함정 | 내용 |
| --- | --- |
| **기록된 목표가 방금 움직였다** | ADR-0321 이 시드 스트림을 바꿔 캠페인이 47.4% → **46.4%**(최악 −4.0pp)로 이동 → `CONTRACT_TARGETS` 재기록함. **다른 밸런스 변경을 하면 다시 재기록**해야 한다 |
| **하네스 NOTE 의 드리프트** | `campaign_survival.ts` 의 NOTE 가 숫자를 **하드코딩**해 표와 어긋났다 → **live 값 보간으로 고침**. 새 노트는 리터럴을 쓰지 말 것 |
| **`GRADE_TARGETS` 는 손대지 않았다** | g4 가 **+33.1pp 초과**인 것이 **의도된 신호**(ADR-0319 열린 질문). 목표를 옮기면 그 신호가 사라진다 |
| **재료는 런 사이에 리셋되지 않는다** | 단 **계약의 다리 사이에는 리셋된다** — `startNextLeg` 이 `makeInitialState` 를 다시 불러 leg 의 미션 보상으로 인벤토리를 새로 만든다. 즉 계약 3다리 안에서 재료는 안 쌓인다(미해결) |
| **장비 기본값은 전투에 무영향** | tier-0 기본 장비(`programPower`·`apBonus`)는 어떤 전투 경로도 안 읽는다. 그래서 ADR-0322 는 byte-identical |
| **e2e 를 돌릴 때** | 새 화면/키를 먹는 화면을 추가하면 **소크·story trace·`run_end_save` 3개 드라이버**를 같이 고쳐야 한다(ADR-0319 전례). 안 고치면 소크가 **가짜 freeze** 를 보고한다 |
| **Manus 이전 아티팩트 3건 미착륙** | `jockey_identity_proposal.md` · `wet_run_growth_direction.md` · 웹사이트 "Wet Run — UI Direction Lab". 필요하면 `artifact.list` 로 꺼낼 것(URL 은 만료됨 → 다시 받아야 함) |

---

## 6. 오너 결정 대기 (5건)

| # | 결정 | 현재 상태 |
| --- | --- | --- |
| 1 | **비용표의 도달 목표**(T1 몇 런 / T2 몇 런) | 미정 — 기본 가정 T1 3런 / T2 8런 |
| 2 | **SRW 케이스 기본 표의 값**(ADR-0321) | 기본 0. `miss 6/guard 12` 면 g4 +42pp → 값을 정하면 ICE 피해를 그에 맞춰 올려야 함 |
| 3 | **수리 슬롯 → 영구 `+최대 HP`?** | 성장 대신 난이도가 크게 낮아짐(측정 있음) |
| 4 | **`ICE recycler` 정제 sink** | 기존 자동 회복 floor 와 **중첩 금지** — 비교 측정 필요 |
| 5 | **레시피 비용·시장 offer** | 비용표 2판에서 제안 |

---

## 7. 검증 명령 (이 세션이 쓴 그대로)

```bash
cd Game/wet_run/web
npm test                 # 228 files / 4380 tests
npm run typecheck && npm run lint
npm run build && npm run balance
npm run survival -- --seeds 64 --cards best --loot value
npm run campaign -- --seeds 64
npm run crafting -- --seeds 12 --runs 3     # 새 하네스
# e2e (preview 서버 필요)
npm run build && (npx vite preview --port 5195 --host 127.0.0.1 &)
PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --project=desktop-chromium
# 게이트 7종 (워크스페이스 루트에서)
cd ../.. && python3 scripts/audit_vault.py && python3 scripts/mixed_language_audit.py
cd Game/wet_run && python3 scripts/check_doc_claims.py && python3 scripts/tools/audit_sprawl.py \
  && python3 scripts/check_no_novel_prose.py && python3 scripts/tools/import_briefings.py --check
```

---

## 8. 이전 세션에서 이월된 것 (이번 세션에 안 건드림)

- **Fiction 백필 후속**: `import_briefings.py --check` 는 통과(33/33)하지만, 대시보드 `missions.json` `story.source` 포인터 오류 3건(`ta_heist`/`mollys_razor`/`construct_memory_rescue`), 임포터 `SLOP_MARKERS` 추가, 쌍둥이 diff 35건 정본 선택.
- **고아 소설 미션 id 173~181개** — 게임에 없는 이야기들(별도 콘텐츠 슬라이스).
- **허브 대사 3편**(`wim_hub`·`maelcum_intro`·`maelcum_caught`) — 대화 트리 화면 필요.
