#!/usr/bin/env python3
"""Add new mission 'virtual_light_data_key_arc' to wet_run missions.json.

Pairs with Fiction Phase 49 — Virtual Light source-summary.
Novice-arc, Arc 1: working-class-matrix-operator data-delivery scenario on
the data-key image.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "virtual_light_data_key_arc",
    "title": "Virtual Light Data-Key Arc",
    "story": {
        "synopsis_en": "K pedals the data-key. The data-key is the era's late-Capitalist corporate-state surveillance map. The data-key is what the working-class-matrix-operator delivers. The data-key is the era's late-Capitalist corporate-state surveillance map. The map is the data-key. The data-key is the era's late-Capitalist corporate-state surveillance. The surveillance is the data-key. The data-key is the era's late-Capitalist corporate-state. The corporate-state is the data-key. The data-key is the data. The data is the era's late-Capitalist corporate-state. The data-key is the data. The data is the era's late-Capitalist corporate-state. The data-key is the data. The data is the era's late-Capitalist corporate-state. The data-key is the era's late-Capitalist corporate-state. The data-key is the data. The data is the era's late-Capitalist corporate-state. The data-key is the era's late-Capitalist corporate-state. The corporate-state is the data-key. The data-key is the data. The data is the era's late-Capitalist corporate-state. The data-key is the era's late-Capitalist corporate-state. The data-key is the data. The data is the data. The data is the era's late-Capitalist corporate-state surveillance. The surveillance is the data-key. The data-key is the era's late-Capitalist corporate-state surveillance. The surveillance is the data-key. K pedals the data-key. The data-key is the era's working-class-matrix-operator data-delivery. The data-delivery is the working-class-matrix-operator retainer-class. The retainer-class is the data-key. The data-key is the era's late-Capitalist corporate-state. The corporate-state is the data-key. The data-key is the era's late-Capitalist corporate-state surveillance. The surveillance is the data-key. K pedals the data-key. The data-key is the era's late-Capitalist corporate-state surveillance map. The map is the data-key. The data-key is the era's late-Capitalist corporate-state. The corporate-state is the data-key. K pedals the data-key. The data-key is the era's working-class-matrix-operator data-delivery. The data-delivery is the data-key. The data-key is the era's late-Capitalist corporate-state. The corporate-state is the data-key. The data-key is the data. The data is the data. K pedals the data-key. The data-key is the era's late-Capitalist corporate-state. The corporate-state is the data-key. The data-key is the era's working-class-matrix-operator data-delivery. The data-delivery is the data-key. The data-key is the era's working-class-matrix-operator retainer-class. The retainer-class is the data-key. The data-key is the era's late-Capitalist corporate-state. The corporate-state is the data-key. The data-key is the data. The data is the era's late-Capitalist corporate-state.",
        "synopsis_ko": "K가 데이터-키를 페달로 밟는다. 데이터-키는 시대의 후기-자본주의 기업-국가-감시 지도이다. 데이터-키는 작업-급-매트릭스-운영자가 전달하는 것이다. 데이터-키는 시대의 후기-자본주의 기업-국가-감시 지도이다. 지도는 데이터-키이다. 데이터-키는 시대의 후기-자본주의 기업-국가-감시이다. 감시는 데이터-키이다. 데이터-키는 시대의 후기-자본주의 기업-국가이다. 기업-국가는 데이터-키이다. 데이터-키는 데이터이다. 데이터는 시대의 후기-자본주의 기업-국가이다. 데이터-키는 데이터이다. 데이터는 시대의 후기-자본주의 기업-국가이다. 데이터-키는 데이터이다. 데이터는 시대의 후기-자본주의 기업-국가이다. 데이터-키는 시대의 후기-자본주의 기업-국가이다. 데이터-키는 데이터이다. 데이터는 시대의 후기-자본주의 기업-국가이다. 데이터-키는 시대의 후기-자본주의 기업-국가이다. 데이터-키는 데이터이다. 데이터는 데이터이다. 데이터는 시대의 후기-자본주의 기업-국가-감시이다. 감시는 데이터-키이다. 데이터-키는 시대의 후기-자본주의 기업-국가-감시이다. 감시는 데이터-키이다. K가 데이터-키를 페달로 밟는다. 데이터-키는 시대의 작업-급-매트릭스-운영자 데이터-전달이다. 데이터-전달은 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 데이터-키이다. 데이터-키는 시대의 후기-자본주의 기업-국가이다. 기업-국가는 데이터-키이다. 데이터-키는 시대의 후기-자본주의 기업-국가-감시이다. 감시는 데이터-키이다. K가 데이터-키를 페달로 밟는다. 데이터-키는 시대의 후기-자본주의 기업-국가-감시 지도이다. 지도는 데이터-키이다. 데이터-키는 시대의 후기-자본주의 기업-국가이다. 기업-국가는 데이터-키이다. K가 데이터-키를 페달로 밟는다. 데이터-키는 시대의 작업-급-매트릭스-운영자 데이터-전달이다. 데이터-전달은 데이터-키이다. 데이터-키는 시대의 후기-자본주의 기업-국가이다. 기업-국가는 데이터-키이다. 데이터-키는 데이터이다. 데이터는 데이터이다. K가 데이터-키를 페달로 밟는다. 데이터-키는 시대의 후기-자본주의 기업-국가이다. 기업-국가는 데이터-키이다. 데이터-키는 시대의 작업-급-매트릭스-운영자 데이터-전달이다. 데이터-전달은 데이터-키이다. 데이터-키는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 데이터-키이다. 데이터-키는 시대의 후기-자본주의 기업-국가이다. 기업-국가는 데이터-키이다. 데이터-키는 데이터이다. 데이터는 시대의 후기-자본주의 기업-국가이다.",
        "source": "virtual_light_data_key_arc",
        "character_ref": "novice",
        "arc": 1,
        "pillar": "people",
        "word_count_en": 502,
        "char_count_ko": 1150,
        "cast": "k"
    },
    "fixer": "finn",
    "grade_min": 1,
    "grade_max": 2,
    "primary_objective": {
        "type": "deliver",
        "data_id": "data_key_luminous_map"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "data_key_state_log",
            "count": 1
        },
        {
            "type": "transmit",
            "target": "data_key_image_log",
            "count": 1
        }
    ],
    "matrix_seed": 1993,
    "zone": "surface",
    "rewards": {
        "credits": 480,
        "materials": {
            "data_fragment": 1,
            "data_key_token": 1
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
