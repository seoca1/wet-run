#!/usr/bin/env python3
"""Add new mission 'zaibatsu_statework' to wet_run missions.json.

Pairs with Fiction Phase 30 — Zaibatsu concept page (wiki/concepts/zaibatsu.md).
Suit-arc, Arc 5: corporate-statework on zaibatsu-class industrial-class substrate.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "zaibatsu_statework",
    "title": "Zaibatsu Statework",
    "story": {
        "synopsis_en": "The zaibatsu has been operating out of a Seven-Eleven in Chiba for forty years. The seven-eleven is the pacific rim's most-concentrated industrial-class substrate, run by operators whose names appear on no corporate document. The operator-pairs at the counter know which zaibatsu they work for: they know the name, they know the family tree, they know the morning-shift and the evening-shift. The Suit's office has been tracking the seven-eleven's zaibatsu-supply-chain for two years. The Suit tracks it because the supply-chain's leaked into the sprawl's working-class matrix-labor market through the Ono-Sendai / Hosaka / cybernetic-cyberdeck supply lines. The cowboy-class equipment that the working-class matrix-labor market has been buying for ten years traces to a zaibatsu-supplied industrial-substrate supply chain. The trace is the era's late-Capitalist industrial-class substrate. The trace is what the Seven-Eleven zaibatsu has been quietly running. The Suit knows. The Suit logs in. The Suit reads the seven-eleven's till-transactions. The till-transactions trace the zaibatsu-supply-chain's daily throughput. The throughput is the era's late-Capitalist industrial-class substrate, individual transactions, individual cowboy-class equipment purchases, individual working-class matrix-operative substitutions — the substitutions are what the era's industrial-class substrate has been managing through the seven-eleven. The Suit reads the substitutions. The Suit reads the daily substrate-management registry. The Suit recognizes the registry: the registry is the era's late-Capitalist industrial-class substrate's *intimate statework*. The statework is what the zaibatsu has been running through the Seven-Eleven. The Suit's log-in is part of the statework. The Suit's reading is the corporate-statework's monitoring. The monitoring is what the era's late-Capitalist industrial-class substrate has required. The Suit files the daily report. The daily report is what the corporate-statework reads as its quarterly-reassurance signal. The reassurance is what the era's late-Capitalist industrial-class substrate has had as its industrial-class operational continuity. The continuity is what the zaibatsu has produced. The Suit gets paid. The Suit goes home. The Seven-Eleven zaibatsu-supply-chain continues. The era's late-Capitalist industrial-class operational continuity continues.",
        "synopsis_ko": "자이바쓰는 40년 동안 치바의 Seven-Eleven에서 운영되어 왔다. Seven-Eleven은 어떤 기업 문서에도 이름이 나타나지 않는 운영자들에 의해 운영되는, 태평양 연안 가장 집중된 산업-급 기질이다. 계산대 앞의 운영자-짝들은 자신이 일하는 자이바쓰를 알고 있다: 그들은 이름을 알고, 가계도를 알고, 오전-교대와 저녁-교대를 안다. Suit의 사무실은 2년 동안 Seven-Eleven의 자이바쓰-공급-사슬을 추적해 왔다. Suit가 이걸 추적하는 이유는 공급-사슬이 Ono-Sendai / Hosaka / 사이버네틱-사이버덱 공급 라인을 통해 스프롤의 작업-급 매트릭스-노동 시장을 새고 흘러나왔기 때문이다. 작업-급 매트릭스-노동 시장이 10년 동안 사온 카우보이-급 장비가 자이바쓰가 공급한 산업-기질 공급 사슬에서 나온다. 추적이 시대의 후기-자본주의 산업-급 기질이다. 추적이 Seven-Eleven 자이바쓰가 조용히 운영해 온 것이다. Suit가 안다. Suit가 로그인한다. Suit가 Seven-Eleven의 계산대-거래를 읽는다. 계산대-거래는 자이바쓰-공급-사슬의 일일 처리량을 추적한다. 처리량은 시대의 후기-자본주의 산업-급 기질 — 개별 거래, 개별 카우보이-급 장비 구매, 개별 작업-급 매트릭스-운영자 교체 — 이며, 교체는 Seven-Eleven이 관리해 온 시대의 산업-급 기질이다. Suit가 교체를 읽는다. Suit가 일일 기질-관리 등록부를 읽는다. Suit가 등록부를 인식한다: 등록부는 시대의 후기-자본주의 산업-급 기질의 *친밀한 국가-작업*이다. 국가-작업은 자이바쓰가 Seven-Eleven을 통해 운영해 온 것이다. Suit의 로그인은 국가-작업의 일부이다. Suit의 읽기는 기업-국가-작업의 모니터링이다. 모니터링은 시대의 후기-자본주의 산업-급 기질이 요구한 것이다. Suit가 일일 보고서를 제출한다. 일일 보고서는 기업-국가-작업이 분기-재확신 신호로 읽는 것이다. 재확신은 시대의 후기-자본주의 산업-급 기질이 산업-급 운영 연속성으로 가지고 있던 것이다. 연속성이 자이바쓰가 만들어 온 것이다. Suit가 급여를 받는다. Suit가 집에 간다. Seven-Eleven 자이바쓰-공급-사슬이 계속된다. 시대의 후기-자본주의 산업-급 운영 연속성이 계속된다.",
        "source": "zaibatsu_statework",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "purpose",
        "word_count_en": 467,
        "char_count_ko": 1112,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "zaibatsu_supply_chain_daily"
    },
    "secondary_objectives": [
        {
            "type": "audit",
            "target": "convenience_store_throughput",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "industrial_class_continuity_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2847,
    "zone": "deep",
    "rewards": {
        "credits": 3500,
        "materials": {
            "data_fragment": 7,
            "industrial_chit": 1
        }
    },
    "arc": 5
}

with open(ROOT) as f:
    data = json.load(f)

if new_mission["id"] in data:
    print(f'WARN: {new_mission["id"]} already exists, skipping')
else:
    data[new_mission["id"]] = new_mission
    with open(ROOT, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'Added mission {new_mission["id"]}')
    print(f'Total missions: {len(data)}')
