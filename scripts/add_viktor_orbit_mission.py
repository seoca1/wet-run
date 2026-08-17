#!/usr/bin/env python3
"""Add new mission 'viktor_orbit_arc' to wet_run missions.json.

Pairs with Fiction Phase 56 — Viktor character page.
Novice-arc, Arc 1: orbit-rigger procedural scenario.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "viktor_orbit_arc",
    "title": "Viktor Orbit Arc",
    "story": {
        "synopsis_en": "K rigs the orbit. The orbit is the era's late-Capitalist orbit-rigger substrate. The orbit-rigger is the era's working-class-matrix-operator retainer-class. The retainer-class is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist orbit-rigger class-image. The orbit-rigger class-image is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist orbit-rigger class-image. The orbit-rigger class-image is the era's late-Capitalist Russian-Mafia orbit-rigger class-image. The Russian-Mafia orbit-rigger class-image is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist Russian-Mafia orbit-rigger class-image. The orbit-rigger class-image is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist Russian-Mafia orbit-rigger class-image. The orbit-rigger class-image is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist Russian-Mafia orbit-rigger class-image. The orbit-rigger class-image is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist Russian-Mafia orbit-rigger class-image. The orbit-rigger class-image is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist Russian-Mafia orbit-rigger class-image. The orbit-rigger class-image is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist Russian-Mafia orbit-rigger class-image. The orbit-rigger class-image is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist Russian-Mafia orbit-rigger class-image. The orbit-rigger class-image is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist Russian-Mafia orbit-rigger class-image. The orbit-rigger class-image is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist Russian-Mafia orbit-rigger class-image. The orbit-rigger class-image is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist Russian-Mafia orbit-rigger class-image. The orbit-rigger class-image is the era's Viktor working-class-aspirant. The aspirant is the era's late-Capitalist Russian-Mafia orbit-rigger class-image. The orbit-rigger class-image is the era's Viktor working-class-aspirant.",
        "synopsis_ko": "K가 궤도를 리깅한다. 궤도는 시대의 후기-자본주의 궤도-리거 기질이다. 궤도-리거는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 궤도-리거 클래스-이미지이다. 궤도-리거 클래스-이미지는 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 궤도-리거 클래스-이미지이다. 궤도-리거 클래스-이미지는 시대의 후기-자본주의 러시아-마피아 궤도-리거 클래스-이미지이다. 러시아-마피아 궤도-리거 클래스-이미지는 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 러시아-마피아 궤도-리거 클래스-이미지이다. 궤도-리거 클래스-이미지는 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 러시아-마피아 궤도-리거 클래스-이미지이다. 궤도-리거 클래스-이미지는 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 러시아-마피아 궤도-리거 클래스-이미지이다. 궤도-리거 클래스-이미지는 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 러시아-마피아 궤도-리거 클래스-이미지이다. 궤도-리거 클래스-이미지는 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 러시아-마피아 궤도-리거 클래스-이미지이다. 궤도-리거 클래스-이미지는 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 러시아-마피아 궤도-리거 클래스-이미지이다. 궤도-리거 클래스-이미지는 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 러시아-마피아 궤도-리거 클래스-이미지이다. 궤도-리거 클래스-이미지는 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 러시아-마피아 궤도-리거 클래스-이미지이다. 궤도-리거 클래스-이미지는 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 러시아-마피아 궤도-리거 클래스-이미지이다. 궤도-리거 클래스-이미지는 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 러시아-마피아 궤도-리거 클래스-이미지이다. 궤도-리거 클래스-이미지는 시대의 Viktor 작업-급-지원자이다. 지원자는 시대의 후기-자본주의 러시아-마피아 궤도-리거 클래스-이미지이다.",
        "source": "viktor_orbit_arc",
        "character_ref": "novice",
        "arc": 1,
        "pillar": "purpose",
        "word_count_en": 376,
        "char_count_ko": 851,
        "cast": "k"
    },
    "fixer": "finn",
    "grade_min": 1,
    "grade_max": 2,
    "primary_objective": {
        "type": "deliver",
        "data_id": "orbit_rigging_daily"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "orbit_daily_log",
            "count": 1
        },
        {
            "type": "transmit",
            "target": "rigger_state_log",
            "count": 1
        }
    ],
    "matrix_seed": 2039,
    "zone": "surface",
    "rewards": {
        "credits": 410,
        "materials": {
            "data_fragment": 1,
            "rigger_token": 1
        }
    },
    "arc": 1
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
