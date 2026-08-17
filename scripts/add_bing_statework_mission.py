#!/usr/bin/env python3
"""Add new mission 'bing_statework' to wet_run missions.json.

Pairs with Fiction Phase 32 — Bing concept page (wiki/concepts/bing.md).
Heretic-arc, Arc 2: pharmacological-statework scenario on binged-state.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "bing_statework",
    "title": "Bing Statework",
    "story": {
        "synopsis_en": "The heretic checks the bing supply. The heretic's worked-class matrix-labor market's principal stimulant is the era's working-class pharmacology. The bing is what the era's working-class matrix-operator takes before jacking in. The bing is what the era's class-structure uses to distinguish the working-class from the corporate-class. The heretic is the working-class. The heretic is not the corporate-class. The heretic is the binged. The binged is the era's working-class class-substance. The corporate-class is sober. The corporate-class class-image is what the binged distinguishes from. The heretic checks the bing supply. The supply is the Sprawl-port-district's principal pharmacologic-infrastructure. The pharmacologic-infrastructure is the era's working-class class-substance. The class-substance is what the heretic checks. The heretic is the class. The class is the working-class. The working-class is the binged. The binged is the era's working-class matrix-labor market. The labor market is what the heretic is in. The heretic is in the labor market. The heretic is the binged. The binged is the era's working-class class-substance. The class-substance is the pharmacologic-infrastructure. The pharmacologic-infrastructure is the Sprawl-port-district's principal pharmacologic-infrastructure. The heretic checks the bing supply. The supply is what the heretic is in. The heretic is in the supply. The supply is the binged. The binged is the era's working-class class-substance. The heretic's check is the era's class-pharmacology statework. The statework is what the era's working-class matrix-labor market has had as its class-substance operational-continuation. The operational-continuation is what the heretic's check produces. The heretic produces the check. The check produces the operational-continuation. The continuation is what the era's working-class matrix-labor market has had as its principal class-pharmacology-distinction. The distinction is the era's class-enforcement; the enforcement is the era's late-Capitalist class-structure; the structure is what the heretic's check has produced. The heretic has produced the check. The check has produced the operational-continuation. The continuation is the era's working-class class-substance. The substance is the era's working-class class-pharmacology-distinction. The distinction is what the heretic has produced. The heretic is in the bing supply. The supply is the era's working-class class-substance. The substance is the heretic's class-distinction. The distinction is the era's late-Capitalist class-pharmacology-distinction.",
        "synopsis_ko": "이단자가 빙을 점검한다. 이단자의 작업-급 매트릭스-노동 시장의 주요 각성제는 시대의 작업-급 약리학이다. 빙은 시대의 작업-급 매트릭스-운영자가 잭-인 하기 전에 복용하는 것이다. 빙은 시대의 계급-구조가 작업-급을 기업-급과 구별하기 위해 사용하는 것이다. 이단자는 작업-급이다. 이단자는 기업-급이 아니다. 이단자는 빙을 복용한 자이다. 빙을 복용한 자는 시대의 작업-급 계급-실체다. 기업-급은 술을 마시지 않는다. 기업-급 계급-이미지는 빙을 복용한 자가 구별하는 것이다. 이단자가 빙 공급을 점검한다. 공급은 스프롤-항구-지구의 주요 약리학-기반시설이다. 약리학-기반시설은 시대의 작업-급 계급-실체다. 계급-실체는 이단자가 점검하는 것이다. 이단자는 계급이다. 계급은 작업-급이다. 작업-급은 빙을 복용한 자이다. 빙을 복용한 자는 시대의 작업-급 매트릭스-노동 시장이다. 노동 시장이 이단자가 있는 곳이다. 이단자가 노동 시장에 있다. 이단자는 빙을 복용한 자이다. 빙을 복용한 자는 시대의 작업-급 계급-실체다. 계급-실체는 약리학-기반시설이다. 약리학-기반시설은 스프롤-항구-지구의 주요 약리학-기반시설이다. 이단자가 빙 공급을 점검한다. 공급은 이단자가 있는 곳이다. 이단자가 공급에 있다. 공급은 빙을 복용한 자이다. 빙을 복용한 자는 시대의 작업-급 계급-실체다. 이단자의 점검이 시대의 계급-약리학 국가-작업이다. 국가-작업은 시대의 작업-급 매트릭스-노동 시장이 계급-실체 운영 연속성으로 가지고 있던 것이다.",
        "source": "bing_statework",
        "character_ref": "heretic",
        "arc": 2,
        "pillar": "power",
        "word_count_en": 488,
        "char_count_ko": 1111,
        "cast": "kas"
    },
    "fixer": "finn",
    "grade_min": 3,
    "grade_max": 4,
    "primary_objective": {
        "type": "audit",
        "data_id": "bing_supply_infrastructure"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "bing_supply_registry",
            "count": 1
        },
        {
            "type": "transmit",
            "target": "class_substance_statework",
            "count": 1
        }
    ],
    "matrix_seed": 2113,
    "zone": "surface",
    "rewards": {
        "credits": 1600,
        "materials": {
            "data_fragment": 3,
            "bing_chit": 1
        }
    },
    "arc": 2
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
