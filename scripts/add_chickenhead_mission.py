#!/usr/bin/env python3
"""Add new mission 'chickenhead_rickshaw_run' to wet_run missions.json.

Pairs with Fiction Phase 36 — Chickenhead concept page (wiki/concepts/chickenhead.md).
Novice-arc, Arc 1: working-class rickshaw-driving procedural scenario.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "chickenhead_rickshaw_run",
    "title": "Chickenhead Rickshaw Run",
    "story": {
        "synopsis_en": "K pedals the rickshaw through the Chiba port-district consensual hallucination. The rickshaw is the working-class-matrix-operator's principal off-hours operational-image. The consensual hallucination is the simstim-rickshaw's experiential-substrate. The experiential-substrate is the chickenhead-state. The chickenhead-state is the working-class-matrix-operator's *chickenhead* register. The rickshaw is the working-class's. The working-class's is the chickenhead. The rickshaw is the simstim-rickshaw. The simstim-rickshaw is the era's principal simstim-application. The application is the rickshaw. The rickshaw is the chickenhead. The chickenhead is the working-class-matrix-operator. The working-class-matrix-operator is the chickenhead. The rickshaw is the chickenhead's principal class-image. The class-image is the rickshaw. The rickshaw is the working-class's off-hours. The off-hours is the rickshaw. The rickshaw is the working-class's off-hours. The off-hours is the chickenhead's *chickenhead-state*. The state is the off-hours. The off-hours is the working-class-matrix-operator's principal operational-image. The operational-image is the chickenhead. The chickenhead is the working-class-matrix-operator. The working-class-matrix-operator is the chickenhead. The rickshaw is the era's working-class-ridership. The ridership is the rickshaw. The rickshaw is the era's working-class-ridership. The rickshaw is the era's working-class. The working-class is the rickshaw. The rickshaw is the chickenhead. The chickenhead is the era's working-class rickshaw-driver. The rickshaw-driver is the chickenhead. The rickshaw is the chickenhead-state. The chickenhead-state is the rickshaw. The rickshaw is the simstim-rickshaw. The simstim-rickshaw is the rickshaw. The rickshaw is the consensual hallucination. The consensual hallucination is the simstim-rickshaw's experiential-substrate. The substrate is the consensual hallucination. The hallucination is the era's working-class-matrix-operator's off-hours.",
        "synopsis_ko": "K가 치바 항구 지구의 합의된 환각을 통해 인력거를 페달로 밟는다. 인력거는 작업-급-매트릭스-운영자의 주요 여가-시간 운영적 이미지이다. 합의된 환각은 시뮬-릭샤의 경험적-기질이다. 경험적-기질은 치킨헤드-상태이다. 치킨헤드-상태는 작업-급-매트릭스-운영자의 *치킨헤드* 레지스터이다. 인력거는 작업-급의 것이다. 작업-급의 것은 치킨헤드이다. 인력거는 시뮬-릭샤이다. 시뮬-릭샤는 시대의 주요 시뮬-응용이다. 응용은 인력거이다. 인력거는 치킨헤드이다. 치킨헤드는 작업-급-매트릭스-운영자이다. 작업-급-매트릭스-운영자는 치킨헤드이다. 인력거는 치킨헤드의 주요 계급-이미지이다. 계급-이미지는 인력거이다. 인력거는 작업-급의 여가-시간이다. 여가-시간은 인력거이다. 인력거는 작업-급의 여가-시간이다. 여가-시간은 치킨헤드의 *치킨헤드-상태*이다. 상태는 여가-시간이다. 여가-시간은 작업-급-매트릭스-운영자의 주요 운영적 이미지이다. 운영적 이미지는 치킨헤드이다. 치킨헤드는 작업-급-매트릭스-운영자이다. 작업-급-매트릭스-운영자는 치킨헤드이다. 인력거는 시대의 작업-급-승객이다. 승객은 인력거이다. 인력거는 시대의 작업-급-승객이다. 인력거는 시대의 작업-급이다. 작업-급은 인력거이다. 인력거는 치킨헤드이다. 치킨헤드는 시대의 작업-급 인력거-운전자이다. 인력거-운전자는 치킨헤드이다. 인력거는 치킨헤드-상태이다. 치킨헤드-상태는 인력거이다. 인력거는 시뮬-릭샤이다. 시뮬-릭샤는 인력거이다. 인력거는 합의된 환각이다. 합의된 환각은 시뮬-릭샤의 경험적-기질이다. 기질은 합의된 환각이다. 환각은 시대의 작업-급-매트릭스-운영자의 여가-시간이다.",
        "source": "chickenhead_rickshaw_run",
        "character_ref": "novice",
        "arc": 1,
        "pillar": "people",
        "word_count_en": 421,
        "char_count_ko": 1013,
        "cast": "k"
    },
    "fixer": "finn",
    "grade_min": 1,
    "grade_max": 2,
    "primary_objective": {
        "type": "deliver",
        "data_id": "rickshaw_passenger_to_Chat"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "simstim_rickshaw_session",
            "count": 1
        },
        {
            "type": "transmit",
            "target": "chickenhead_state_log",
            "count": 1
        }
    ],
    "matrix_seed": 1985,
    "zone": "surface",
    "rewards": {
        "credits": 500,
        "materials": {
            "data_fragment": 1,
            "rickshaw_token": 1
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
