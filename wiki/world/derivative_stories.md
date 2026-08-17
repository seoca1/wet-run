# Derivative Stories (이차 창작 단편)

> **이 페이지는 Fiction 프로젝트의 이차 창작 단편을 게임 미션과 연결합니다.**

**현재 상태 (2026-08-08 갱신 — Phase 83 propagation)**: `prototype/data/missions/missions.json` 기준 **111 미션** 정의됨. **모든 111 미션 매핑 완료** (2026-07-30 `chevette_run` → `chevette_nightshift_run` 정정 후 unmapped 0건). 단편 stem 카운트: dashboard `dataset_health.json` 기준 **150 EN + 150 KO = 300 entries** (Fiction filesystem 상에는 139 unique stems per language).

**Fiction Phase 73-82 영향 (2026-08-08)** — 게임 미션 매핑에 직접 영향:
- **Phase 73** schema §2 단편 심화 — 9 *Burning Chrome* stories (incl. `case_jackout-30sec`, `first_jack` 미션 매핑 stem 포함) + 18 short-story-specific sections
- **Phase 74** stub cleanup — Johnny Mnemonic + 3jane-tessier-ashpool 4 sections; index ⚠️ STUB markers 2개 cleared (Johnny Mnemonic + 3jane 모두 non-stub 으로 재분류됨)
- **Phase 78** ADR-0017 backfill — **150 KO 파일 모두 `source_word_count` 필드 추가** (Phase 61 outstanding debt 해결). Game-side 영향: KO 번역 provenance 메타데이터 보존; `story.source` 매핑 무영향
- **Phase 81** verbatim text audit — 6 multi-sentence quote blocks paraphrased (게임 미션 텍스트 변경 없음, wiki 분석만 영향)

**Story-side cross-references** (Phase 73-82에서 강화된 분석):
- Johnny Mnemonic (1981) — Phase 74 심화 → [johnny-mnemonic](../../../../Fiction/wiki/works/johnny-mnemonic.md) 2,853 → 4,853 words + foundational 분석 (Shotgun-in-Adidas-Bag prose; Molly's first appearance)
- 3jane-tessier-ashpool (1982) — Phase 74 심화 → [3jane-tessier-ashpool](../../../../Fiction/wiki/works/3jane-tessier-ashpool.md) 3,334 → 3,987 words (cipher-vs-curriculum; Freeside-as-orbital-womb)

**캐노니컬 정보 소스**: `prototype/data/missions/missions.json` (각 미션의 `story.source` 필드가 단편 stem 참조)

## 연결 구조

```
Fiction/derivative/{sprawl,bridge,blue-ant}-trilogy/short-stories/
  ├── en/  (영어 원문)
  └── ko/  (한국어 번역)
        ↓ (인간 큐레이션: synopsis 발췌)
Game/wet_run/prototype/data/missions/missions.json
        ↓ (story.source 필드로 매핑)
Game/wet_run/prototype/data/story/chapters/{case,sil,kas,suit}.json
        ↓ (chapter_view.py가 렌더링)
CHAPTER 화면 (그래픽 노블 모드)
        ↓
dashboard/stories/short-stories/*.html (정적 카드)
```

## 챕터 → 단편 매핑

**총 110 미션 × 4 챕터 매핑** (각 미션의 `character_ref` 필드 기준)

### Chapter Novice (케이/K — 초짜) (31 미션)

| 미션 ID | Arc | 단편 stem | 단편 파일 |
|---|:---:|---|---|
| `chevette_nightshift_run` | 1 | `chevette_nightshift_run` | [../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_chevette_nightshift_run.md](../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_chevette_nightshift_run.md) |
| `chickenhead_rickshaw_run` | 1 | `chickenhead_rickshaw_run` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_chickenhead_rickshaw_run.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_chickenhead_rickshaw_run.md) |
| `cortex_hound_recovery` | 1 | `cortex_hound_recovery` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_cortex_hound_recovery.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_cortex_hound_recovery.md) |
| `data_retrieval` | 1 | `data_retrieval` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-25_data_retrieval.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-25_data_retrieval.md) |
| `first_jack` | 1 | `case_jackout-30sec` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_case_jackout-30sec.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_case_jackout-30sec.md) |
| `hosaka_terminal_supply` | 1 | `hosaka_terminal_supply` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_hosaka_terminal_supply.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_hosaka_terminal_supply.md) |
| `ice_run` | 1 | `ice_run` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_ice_run.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_ice_run.md) |
| `ono_sendai_repair` | 1 | `ono_sendai_repair` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_ono_sendai_repair.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_ono_sendai_repair.md) |
| `razor_work` | 1 | `razor_work` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_razor_work.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_razor_work.md) |
| `soho_blackout` | 1 | `soho_blackout` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_soho_blackout.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_soho_blackout.md) |
| `surface_mail_run` | 1 | `surface_mail_run` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_surface_mail_run.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_surface_mail_run.md) |
| `tokyo_courier_run` | 1 | `tokyo-courier-run` | [../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-15_tokyo-courier-run.md](../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-15_tokyo-courier-run.md) |
| `tutorial_maze` | 1 | `tutorial_maze` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-25_tutorial_maze.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-25_tutorial_maze.md) |
| `viktor_orbit_arc` | 1 | `viktor_orbit_arc` | [../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_viktor_orbit_arc.md](../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_viktor_orbit_arc.md) |
| `virtual_light_data_key_arc` | 1 | `virtual_light_data_key_arc` | [../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_virtual_light_data_key_arc.md](../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_virtual_light_data_key_arc.md) |
| `watchdog_patrol` | 1 | `watchdog_patrol` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_watchdog_patrol.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_watchdog_patrol.md) |
| `wendell_suburban_arc` | 1 | `wendell_suburban_arc` | [../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_wendell_suburban_arc.md](../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_wendell_suburban_arc.md) |
| `coolhunter_laney_tokyo` | 2 | `coolhunter-laney-tokyo` | [../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_coolhunter-laney-tokyo.md](../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_coolhunter-laney-tokyo.md) |
| `first_trace` | 2 | `first_trace` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_first_trace.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_first_trace.md) |
| `flatline_call` | 2 | `flatline_again` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_flatline_again.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_flatline_again.md) |
| `hosaka_corporate_infiltration` | 2 | `ta_defection` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_ta_defection.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_ta_defection.md) |
| `sense_net_infiltration` | 2 | `sense_net_infiltration` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_sense_net_infiltration.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_sense_net_infiltration.md) |
| `yakuza_loan_shark` | 2 | `yakuza_deal` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_yakuza_deal.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_yakuza_deal.md) |
| `angie_leopard_tracking` | 3 | `angie_leopard_tracking` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_angie_leopard_tracking.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_angie_leopard_tracking.md) |
| `black_ice_dream` | 3 | `black_ice_dream` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_black_ice_dream.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_black_ice_dream.md) |
| `hosaka_core` | 3 | `hosaka_core` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_hosaka_core.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_hosaka_core.md) |
| `maas_heist` | 3 | `maas_heist` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_maas_heist.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_maas_heist.md) |
| `voodoo_loa_encounter` | 4 | `loa_voodoo_contact` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_loa_voodoo_contact.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_loa_voodoo_contact.md) |
| `mollys_final_razor` | 5 | `mollys_final_razor` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_mollys_final_razor.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_mollys_final_razor.md) |
| `final_choice` | 5 | `the_choice` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_the_choice.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_the_choice.md) |
| `zion_vote_observation` | 5 | `zion_vote_observation` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_zion_vote_observation.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_zion_vote_observation.md) |

### Chapter Veteran (실/Sil — 베테랑) (24 미션)

| 미션 ID | Arc | 단편 stem | 단편 파일 |
|---|:---:|---|---|
| `bigend_laney_lunch` | 1 | `bigend-laney-lunch` | [../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_bigend-laney-lunch.md](../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_bigend-laney-lunch.md) |
| `delivery_to_finn` | 1 | `marly_louisiana-god` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_marly_louisiana-god.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_marly_louisiana-god.md) |
| `first_contact` | 2 | `first_contact` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-25_first_contact.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-25_first_contact.md) |
| `hideo_contract` | 2 | `hideo_contract` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_hideo_contract.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_hideo_contract.md) |
| `laney_node_signal_run` | 2 | `laney_node_signal_run` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_laney_node_signal_run.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_laney_node_signal_run.md) |
| `molly_decides` | 2 | `molly_decides` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-14_molly_decides.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-14_molly_decides.md) |
| `mollys_market` | 2 | `mollys_market` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_mollys_market.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_mollys_market.md) |
| `panther_negotiate` | 2 | `panther_negotiate` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_panther_negotiate.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_panther_negotiate.md) |
| `sense_net_tip` | 2 | `sense_net_trace` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_sense_net_trace.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_sense_net_trace.md) |
| `tokyo_pachinko_run` | 2 | `tokyo_pachinko_run` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_tokyo_pachinko_run.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_tokyo_pachinko_run.md) |
| `bridge_scaffold` | 3 | `bridge-construct` | [../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-15_bridge-construct.md](../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-15_bridge-construct.md) |
| `mollys_razor` | 3 | `mollys_razor` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-08_mollys_razor.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-08_mollys_razor.md) |
| `sense_net_media_extract` | 3 | `hosaka_extraction` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_hosaka_extraction.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_hosaka_extraction.md) |
| `straylight_approach` | 3 | `straylight_approach` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_straylight_approach.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_straylight_approach.md) |
| `ta_heist` | 3 | `ta_heist` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-08_ta_heist.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-08_ta_heist.md) |
| `vegas_stakeout` | 3 | `vegas_stakeout` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_vegas_stakeout.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_vegas_stakeout.md) |
| `case_meets_cayce` | 4 | `case-meets-cayce` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_case-meets-cayce.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_case-meets-cayce.md) |
| `dixies_choice` | 4 | `dixies_choice` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_dixies_choice.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_dixies_choice.md) |
| `dixies_offer` | 4 | `dixies_last_run` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_dixies_last_run.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_dixies_last_run.md) |
| `ta_payroll_archive` | 4 | `straylight_approach` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_straylight_approach.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_straylight_approach.md) |
| `winter_infiltrate` | 4 | `winter_infiltrate` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_winter_infiltrate.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_winter_infiltrate.md) |
| `finn_final_reckoning` | 5 | `finn_final_reckoning` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_finn_final_reckoning.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_finn_final_reckoning.md) |
| `ta_straylight_archive` | 5 | `straylight_approach` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_straylight_approach.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_straylight_approach.md) |
| `zion_express` | 5 | `zion_express` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_zion_express.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_zion_express.md) |

### Chapter Heretic (카스/Kas — 이단) (26 미션)

| 미션 ID | Arc | 단편 stem | 단편 파일 |
|---|:---:|---|---|
| `cayce_footage_audit_run` | 1 | `cayce_footage_audit_run` | [../../../../Fiction/derivative/blue-ant/short-stories/en/2026-07-19_cayce_footage_audit_run.md](../../../../Fiction/derivative/blue-ant/short-stories/en/2026-07-19_cayce_footage_audit_run.md) |
| `bing_statework` | 2 | `bing_statework` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_bing_statework.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_bing_statework.md) |
| `craft_job` | 2 | `kumiko_manarase-midnight` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_kumiko_manarase-midnight.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_kumiko_manarase-midnight.md) |
| `eurydice_arc` | 2 | `eurydice_arc` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_eurydice_arc.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_eurydice_arc.md) |
| `idoru_wedding` | 2 | `idoru_wedding_arc` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_idoru_wedding_arc.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_idoru_wedding_arc.md) |
| `sally_sandii_3am` | 2 | `sally_sandii-3am` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_sally_sandii-3am.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_sally_sandii-3am.md) |
| `wigan_call` | 2 | `wigan_call` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_wigan_call.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_wigan_call.md) |
| `wigan_construct_reach` | 2 | `wigan_construct_reach` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_wigan_construct_reach.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_wigan_construct_reach.md) |
| `yakuza_deal` | 2 | `yakuza_deal` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_yakuza_deal.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_yakuza_deal.md) |
| `beijing_memory_courier` | 3 | `beijing_memory_courier` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-11_beijing_memory_courier.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-11_beijing_memory_courier.md) |
| `g_boys_arc` | 3 | `g_boys_arc` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_g_boys_arc.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_g_boys_arc.md) |
| `idoru_wedding_arc` | 3 | `idoru_wedding_arc` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_idoru_wedding_arc.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_idoru_wedding_arc.md) |
| `neuromancer_whisper` | 3 | `neuromancer_whisper` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/ko/2026-06-29_neuromancer_whisper.ko.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/ko/2026-06-29_neuromancer_whisper.ko.md) |
| `sally_returns_arc3` | 3 | `sally_returns` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_sally_returns.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_sally_returns.md) |
| `voodoo_zoneload` | 3 | `voodoo_zoneload` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_voodoo_zoneload.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_voodoo_zoneload.md) |
| `aleph_fragment` | 4 | `aleph_fragment` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-30_aleph_fragment.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-30_aleph_fragment.md) |
| `heretic_loa_conscription` | 4 | `heretic_loa_conscription` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_heretic_loa_conscription.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_heretic_loa_conscription.md) |
| `maas_neural_extract` | 4 | `maas_heist` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_maas_heist.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-01_maas_heist.md) |
| `matrix_revelation` | 4 | `matrix_revelation` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/ko/2026-06-29_matrix_revelation.ko.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/ko/2026-06-29_matrix_revelation.ko.md) |
| `sally_construct_market` | 4 | `sally_construct_market` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_sally_construct_market.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_sally_construct_market.md) |
| `straylight_inquiry` | 4 | `straylight_inquiry` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_straylight_inquiry.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_straylight_inquiry.md) |
| `trauma_squads_pair_arc` | 4 | `trauma_squads_pair_arc` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_trauma_squads_pair_arc.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_trauma_squads_pair_arc.md) |
| `ta_3jane_betrayal` | 5 | `ta_defection` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_ta_defection.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_ta_defection.md) |
| `construct_memory_rescue` | 5 | `dixies_last_run` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_dixies_last_run.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-23_dixies_last_run.md) |
| `neuromancer_merger` | 5 | `neuromancer_merger` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_neuromancer_merger.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_neuromancer_merger.md) |
| `salvation_wigan_zavijava` | 5 | `salvation_wigan_zavijava` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_salvation_wigan_zavijava.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_salvation_wigan_zavijava.md) |

### Chapter Suit (스uit — 코퍼레이트) (29 미션)

| 미션 ID | Arc | 단편 stem | 단편 파일 |
|---|:---:|---|---|
| `threjane_family_log` | 1 | `threjane_family_log` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_threjane_family_log.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_threjane_family_log.md) |
| `armitage_infiltration` | 2 | `armitage_infiltration` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_armitage_infiltration.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_armitage_infiltration.md) |
| `finn_factory_labour_run` | 2 | `finn_factory_labour_run` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_finn_factory_labour_run.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_finn_factory_labour_run.md) |
| `neuromancer_first_ping` | 2 | `neuromancer_first_ping` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_neuromancer_first_ping.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_neuromancer_first_ping.md) |
| `freeside_payroll` | 3 | `freeside_payroll` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_freeside_payroll.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_freeside_payroll.md) |
| `hosaka_extraction` | 3 | `hosaka_extraction` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_hosaka_extraction.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_hosaka_extraction.md) |
| `armitage_infiltration_2` | 4 | `armitage_infiltration_2` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_armitage_infiltration_2.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_armitage_infiltration_2.md) |
| `kombinat_node_hack` | 4 | `kombinat-node-hack` | [../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-15_kombinat-node-hack.md](../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-15_kombinat-node-hack.md) |
| `sense_net_archive_intrusion` | 4 | `sense_net_archive_intrusion` | [../../../../Fiction/derivative/blue-ant/short-stories/en/2026-07-19_sense_net_archive_intrusion.md](../../../../Fiction/derivative/blue-ant/short-stories/en/2026-07-19_sense_net_archive_intrusion.md) |
| `ta_defection` | 4 | `ta_defection` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_ta_defection.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_ta_defection.md) |
| `wintermute_merger_run` | 4 | `wintermute_merger_run` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_wintermute_merger_run.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_wintermute_merger_run.md) |
| `bama_statework` | 5 | `bama_statework` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_bama_statework.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_bama_statework.md) |
| `boone_tokyo_electronics_arc` | 5 | `boone_tokyo_electronics_arc` | [../../../../Fiction/derivative/blue-ant/short-stories/en/2026-07-19_boone_tokyo_electronics_arc.md](../../../../Fiction/derivative/blue-ant/short-stories/en/2026-07-19_boone_tokyo_electronics_arc.md) |
| `core_memory_dump` | 5 | `core_memory_dump` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_core_memory_dump.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_core_memory_dump.md) |
| `fido_statework` | 5 | `fido_statework` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_fido_statework.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_fido_statework.md) |
| `fukuoka_ridership_arc` | 5 | `fukuoka_ridership_arc` | [../../../../Fiction/derivative/blue-ant/short-stories/en/2026-07-19_fukuoka_ridership_arc.md](../../../../Fiction/derivative/blue-ant/short-stories/en/2026-07-19_fukuoka_ridership_arc.md) |
| `hounds_arc` | 5 | `hounds_arc` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_hounds_arc.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_hounds_arc.md) |
| `mona_bridge_arc` | 5 | `mona_bridge_arc` | [../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_mona_bridge_arc.md](../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_mona_bridge_arc.md) |
| `pacific_empire_arc` | 5 | `pacific_empire_arc` | [../../../../Fiction/derivative/blue-ant/short-stories/en/2026-07-19_pacific_empire_arc.md](../../../../Fiction/derivative/blue-ant/short-stories/en/2026-07-19_pacific_empire_arc.md) |
| `pan_mannerist_audit` | 5 | `pan_mannerist_audit` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_pan_mannerist_audit.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_pan_mannerist_audit.md) |
| `tessier_sleeper_arc` | 5 | `tessier_sleeper_arc` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_tessier_sleeper_arc.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_tessier_sleeper_arc.md) |
| `trauma_squads_audit` | 5 | `trauma_squads_audit` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_trauma_squads_audit.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_trauma_squads_audit.md) |
| `w_anchor_arc` | 5 | `w_anchor_arc` | [../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_w_anchor_arc.md](../../../../Fiction/derivative/bridge-trilogy/short-stories/en/2026-07-19_w_anchor_arc.md) |
| `ta_wintermute_direct` | 5 | `wintermute_negotiation` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_wintermute_negotiation.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_wintermute_negotiation.md) |
| `wintermute_negotiation` | 5 | `wintermute_negotiation` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_wintermute_negotiation.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_wintermute_negotiation.md) |
| `wintermute_witness` | 5 | `wintermute_witness` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_wintermute_witness.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-25_wintermute_witness.md) |
| `working_class_ridership_arc` | 5 | `working_class_ridership_arc` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_working_class_ridership_arc.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_working_class_ridership_arc.md) |
| `yanaka_family_power_arc` | 5 | `yanaka_family_power_arc` | [../../../../Fiction/derivative/blue-ant/short-stories/en/2026-07-19_yanaka_family_power_arc.md](../../../../Fiction/derivative/blue-ant/short-stories/en/2026-07-19_yanaka_family_power_arc.md) |
| `zaibatsu_statework` | 5 | `zaibatsu_statework` | [../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_zaibatsu_statework.md](../../../../Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-19_zaibatsu_statework.md) |

---

## ⚠️ 매핑 누락 (Unmatched)

**None** (모든 111 미션 매핑 완료 — `chevette_run` → `chevette_nightshift_run` stem 정정 2026-07-30)

## Trilogy × Chapter 분포

| Trilogy | Novice | Veteran | Heretic | Suit | Total |
|---|--:|--:|--:|--:|--:|
| derivative | 31 | 24 | 26 | 29 | 110 |

---

## 검증 명령

```bash
# 매핑 검증
python3 << 'PYEOF'
import json
from pathlib import Path
missions = json.load(open('Game/wet_run/prototype/data/missions/missions.json'))
en_stems = set()
for f in Path('Fiction/derivative').rglob('*/short-stories/en/*.md'):
    parts = f.stem.split('_', 3)
    s = parts[3] if len(parts) > 3 and parts[0].isdigit() else f.stem
    en_stems.add(s)
matched = sum(1 for m in missions.values() if m.get('story', {}).get('source') in en_stems)
print(f"{matched}/{len(missions)} missions matched")
PYEOF
```

## 갱신 이력

- **2026-08-07**: 단편 카운트 정정 (242 → 300, dashboard `dataset_health.json` 기준). 모든 111 미션 매핑 확인 (110 → 111, `chevette_nightshift_run` 매핑 후).
- **2026-07-30**: 47→110 미션 매핑 (전체 갱신 — 2026-07-21 이후 추가된 64+ 미션 반영)
- **2026-07-21**: 초기 47 미션 매핑
