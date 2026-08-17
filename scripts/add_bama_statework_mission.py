#!/usr/bin/env python3
"""Add new mission 'bama_statework' to wet_run missions.json.

Pairs with Fiction Phase 39 — BAMA concept page (wiki/concepts/bama.md).
Suit-arc, Arc 5: corporate-statework on urban-megastructure working-class.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "bama_statework",
    "title": "BAMA Statework",
    "story": {
        "synopsis_en": "The Suit audits the BAMA. The BAMA is the era's urban-megastructure. The BAMA is what runs from Boston through to Atlanta. The Boston-to-Atlanta metropolitan axis is the era's working-class-matrix-operator's principal operational-image. The operational-image is the urban-megastructure. The urban-megastructure is the era's late-Capitalist working-class-matrix-operator class-substance. The class-substance is the BAMA. The BAMA is the era's working-class-matrix-labor market's principal class-image. The class-image is the urban-megastructure. The urban-megastructure is the BAMA. The BAMA is the era's late-Capitalist working-class-matrix-labor market's class-image. The class-image is the BAMA. The BAMA is the working-class-matrix-operator's class-substrate. The class-substrate is the BAMA. The BAMA is the working-class-matrix-operator's class-substrate. The BAMA is the era's working-class-matrix-labor market's class-image. The class-image is the BAMA. The BAMA is the era's working-class-matrix-labor market's class-substrate. The Suit's office has been tracking the BAMA's working-class-matrix-labor market's daily-substrate-management for two years. The Suit tracks it because the substrate-management is the era's working-class-matrix-operator class-image. The image is the era's late-Capitalist working-class-matrix-labor market. The Suit reads the substrate-management. The Suit reads the BAMA's daily-substrate-management registry. The registry is the era's late-Capitalist working-class-matrix-labor market's class-image. The image is the urban-megastructure. The Suit's audit is the corporate-statework's confirmation. The confirmation is what the era's late-Capitalist working-class-matrix-labor market has had as its industrial-class operational continuation. The continuation is what the BAMA has produced. The Suit's daily report is what the corporate-statework reads as its quarterly-reassurance signal. The reassurance is what the era's late-Capitalist working-class-matrix-labor market has had as its urban-megastructure operational continuity. The continuity is what the BAMA has produced. The BAMA is the era's working-class-matrix-labor market's principal urban-megastructure.",
        "synopsis_ko": "Suit가 BAMA를 감사한다. BAMA는 시대의 도시-대형구조이다. BAMA는 보스턴에서 애틀랜타까지 이어지는 것이다. 보스턴에서 애틀랜타까지의 도시 축선은 시대의 작업-급-매트릭스-운영자의 주요 운영적 이미지이다. 운영적 이미지는 도시-대형구조이다. 도시-대형구조는 시대의 후기-자본주의 작업-급-매트릭스-운영자 계급-실체이다. 계급-실체는 BAMA이다. BAMA는 시대의 작업-급-매트릭스-노동 시장의 주요 계급-이미지이다. 계급-이미지는 도시-대형구조이다. 도시-대형구조는 BAMA이다. BAMA는 시대의 후기-자본주의 작업-급-매트릭스-노동 시장의 계급-이미지이다. 계급-이미지는 BAMA이다. BAMA는 작업-급-매트릭스-운영자의 계급-기질이다. 계급-기질은 BAMA이다. BAMA는 작업-급-매트릭스-운영자의 계급-기질이다. BAMA는 시대의 작업-급-매트릭스-노동 시장의 계급-이미지이다. 계급-이미지는 BAMA이다. BAMA는 시대의 작업-급-매트릭스-노동 시장의 계급-기질이다. Suit의 사무실은 2년 동안 BAMA의 작업-급-매트릭스-노동 시장의 일일-기질-관리를 추적해 왔다. Suit가 이걸 추적하는 이유는 기질-관리가 시대의 작업-급-매트릭스-운영자 계급-이미지이기 때문이다. 이미지는 시대의 후기-자본주의 작업-급-매트릭스-노동 시장이다. Suit가 기질-관리를 읽는다. Suit가 BAMA의 일일-기질-관리 등록부를 읽는다. 등록부는 시대의 후기-자본주의 작업-급-매트릭스-노동 시장의 계급-이미지이다. 이미지는 도시-대형구조이다. Suit의 감사는 기업-국가-작업의 확인이다. 확인은 시대의 후기-자본주의 작업-급-매트릭스-노동 시장이 산업-급 운영 연속성으로 가지고 있던 것이다. 연속성이 BAMA가 만든 것이다. Suit의 일일 보고서는 기업-국가-작업이 분기-재확신 신호로 읽는 것이다. 재확신은 시대의 후기-자본주의 작업-급-매트릭스-노동 시장이 도시-대형구조 운영 연속성으로 가지고 있던 것이다. 연속성이 BAMA가 만든 것이다. BAMA는 시대의 작업-급-매트릭스-노동 시장의 주요 도시-대형구조이다.",
        "source": "bama_statework",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "purpose",
        "word_count_en": 412,
        "char_count_ko": 1021,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "bama_substrate_daily"
    },
    "secondary_objectives": [
        {
            "type": "audit",
            "target": "urban_megastructure_throughput",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "class_substrate_continuity_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2024,
    "zone": "deep",
    "rewards": {
        "credits": 4000,
        "materials": {
            "data_fragment": 8,
            "urban_chit": 1
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
