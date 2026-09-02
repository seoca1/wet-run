# Zone Content Expansion (Mid/Core/TA) — Phase 7.2

> **문서 버전**: 0.1.0
> **최종 업데이트**: 2026-07-04
> **관련**: `data/missions/missions.json`, `data/crafting/market.json`, `data/ice/ice_types.json`

---

## 1. 컨텍스트

ROADMAP Phase 7.2 — Zone 콘텐츠 보강. 현재 zone 분포:

| Zone | Depth | 미션 수 | 상태 |
|---|---|---|---|
| SURFACE | 1-3 | 12 | ✅ 충분 |
| MID | 4-8 | 2 | ⚠️ 부족 |
| DEEP | 6-10 | 10 | ✅ 충분 (Vodou/loa) |
| CORE | 9-15 | 3 | ⚠️ 부족 |
| TA | 20-30 | 1 | ⚠️ 부족 |
| FREESIDE | 25-35 | 5 | ✅ 충분 |

**목표**: MID +3, CORE +3, TA +3 = **9 신규 미션**

## 2. MID Zone (Depth 4-8) — Sprawl Mid-Corporate

깁슨 톤: 산업 지대, 사무실 빌딩, 지하 주차장. 기업 본사 침투.

| 미션 ID | Arc | 등급 | 의뢰인 | 톤 |
|---|---|---|---|---|
| `hosaka_corporate_infiltration` | 2 | 2-3 | Finn | 기업 사무소 잠입 |
| `sense_net_media_extract` | 3 | 3-4 | Sally Shears | 미디어 본부 데이터 추출 |
| `yakuza_loan_shark` | 2 | 2-3 | Yakuza 의뢰인 | 야쿠자 채무 추적 |

## 3. CORE Zone (Depth 9-15) — Corporate Core Systems

깁슨 톤: 깊은 매트릭스, construct 기억, Hosaka/T-A/Maas 코어.

| 미션 ID | Arc | 등급 | 의뢰인 | 톤 |
|---|---|---|---|---|
| `ta_payroll_archive` | 4 | 4-5 | 익명 (T-A 내부) | T-A 페이롤 핵심 기록 추출 |
| `maas_neural_extract` | 4 | 4-5 | Finn | Maas 신경 매핑 추출 |
| `construct_memory_rescue` | 5 | 4-5 | Dixie Flatline (loa) | 죽은 construct 기억 복구 |

## 4. TA Zone (Depth 20-30) — Tessier-Ashpool Inner

깁슨 톤: Straylight 깊숙이, 3Jane의 영역, Wintermute의 코어.

| 미션 ID | Arc | 등급 | 의뢰인 | 톤 |
|---|---|---|---|---|
| `ta_straylight_archive` | 5 | 5-6 | 3Jane | Straylight 기록 보관소 열기 |
| `ta_3jane_betrayal` | 5 | 5-6 | Armitage | 3Jane 배신 |
| `ta_wintermute_direct` | 5 | 5-6 | Wintermute (suit) | Wintermute 직접 협상 |

## 5. ICE 추가

각 zone별 특수 ICE:

| Zone | ICE | HP | DMG | 특수 |
|---|---|---|---|---|
| MID | `corporate_guard` | 100 | 4 | 기업 보안 ICE |
| MID | `media_sentinel` | 90 | 5 | 미디어 모니터링 |
| CORE | `archive_sentinel` | 180 | 8 | 깊은 archive 방어 |
| CORE | `neural_defender` | 200 | 9 | Maas 신경 방어 |
| CORE | `construct_warden` | 220 | 10 | construct 기억 보호 |
| TA | `family_guard` | 280 | 12 | T-A family 내부 |
| TA | `inner_sentinel` | 300 | 14 | Straylight 깊은 방어 |
| TA | `wintermute_proxy` | 400 | 18 | Wintermute의 proxy |

## 6. 보상 곡선

| Zone | Credits | Materials |
|---|---|---|
| MID | 2,000-3,500 | T2-T3 업그레이드 |
| CORE | 4,000-6,000 | T4-T5 업그레이드, loa_chip |
| TA | 6,000-10,000 | T5-T6 업그레이드, unique_construct |

## 7. ADR 영향

- **ADR-0012** Combat Difficulty — PPL/ZDR 공식 확장
- **ADR-0017** Mission-Material Integration — Core zone 재료
- **ADR-0050** Boss ICE System — TA zone boss
- **ADR-0052** Short Story Expansion Plan — 4편 신규 단편

## 8. 테스트

- `tests/unit/test_missions.py` — zone별 미션 분포
- `tests/unit/test_zone_difficulty.py` — ZDR 계산 검증
- `tests/unit/test_ice_types.py` — ICE HP/DMG 확인

## 9. 다음 단계

- Zone별 단편 3편 (Hosaka/Sense-Net/T-A 내부)
- Zone 진입 시 cinematic
- Zone 깊이별 그래픽 노블 씬 (MID 1 / CORE 1 / TA 1)