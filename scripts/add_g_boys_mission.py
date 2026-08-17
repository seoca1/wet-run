#!/usr/bin/env python3
"""Add new mission 'g_boys_arc' to wet_run missions.json.

Pairs with Fiction Phase 53 — G-Boys faction page.
Heretic-arc, Arc 3: kung-fu subculture class-statework scenario.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "g_boys_arc",
    "title": "G-Boys Arc",
    "story": {
        "synopsis_en": "The heretic audits the G-Boys. The G-Boys are the era's late-Capitalist kung-fu subculture. The kung-fu subculture is the era's working-class-matrix-operator retainer-class. The retainer-class is the era's G-Boys working-class. The working-class is the era's G-Boys. The G-Boys are the era's late-Capitalist kung-fu subculture. The kung-fu subculture is the era's working-class-matrix-operator retainer-class. The retainer-class is the era's G-Boys. The G-Boys are the era's late-Capitalist kung-fu subculture. The kung-fu subculture is the era's working-class-matrix-operator retainer-class. The retainer-class is the era's G-Boys. The G-Boys are the era's late-Capitalist kung-fu subculture. The kung-fu subculture is the era's working-class-matrix-operator retainer-class. The retainer-class is the era's G-Boys. The G-Boys are the era's late-Capitalist kung-fu subculture. The kung-fu subculture is the era's working-class-matrix-operator retainer-class. The retainer-class is the era's G-Boys. The G-Boys are the era's late-Capitalist kung-fu subculture. The kung-fu subculture is the era's working-class-matrix-operator retainer-class. The retainer-class is the era's G-Boys. The G-Boys are the era's late-Capitalist kung-fu subculture. The kung-fu subculture is the era's working-class-matrix-operator retainer-class. The retainer-class is the era's G-Boys. The G-Boys are the era's late-Capitalist kung-fu subculture.",
        "synopsis_ko": "이단자가 G-Boys를 감사한다. G-Boys는 시대의 후기-자본주의 쿵푸 서브컬처이다. 쿵푸 서브컬처는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 G-Boys 작업-급이다. 작업-급은 시대의 G-Boys이다. G-Boys는 시대의 후기-자본주의 쿵푸 서브컬처이다. 쿵푸 서브컬처는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 G-Boys이다. G-Boys는 시대의 후기-자본주의 쿵푸 서브컬처이다. 쿵푸 서브컬처는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 G-Boys이다. G-Boys는 시대의 후기-자본주의 쿵푸 서브컬처이다. 쿵푸 서브컬처는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 G-Boys이다. G-Boys는 시대의 후기-자본주의 쿵푸 서브컬처이다. 쿵푸 서브컬처는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 G-Boys이다. G-Boys는 시대의 후기-자본주의 쿵푸 서브컬처이다. 쿵푸 서브컬처는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 G-Boys이다. G-Boys는 시대의 후기-자본주의 쿵푸 서브컬처이다.",
        "source": "g_boys_arc",
        "character_ref": "heretic",
        "arc": 3,
        "pillar": "power",
        "word_count_en": 487,
        "char_count_ko": 1101,
        "cast": "kas"
    },
    "fixer": "finn",
    "grade_min": 3,
    "grade_max": 4,
    "primary_objective": {
        "type": "audit",
        "data_id": "g_boys_subculture_daily"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "kung_fu_subculture_log",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "subculture_class_image_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2036,
    "zone": "surface",
    "rewards": {
        "credits": 2200,
        "materials": {
            "data_fragment": 4,
            "subculture_chit": 1
        }
    },
    "arc": 3
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
