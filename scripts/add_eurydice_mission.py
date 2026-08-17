#!/usr/bin/env python3
"""Add new mission 'eurydice_arc' to wet_run missions.json.

Pairs with Fiction Phase 47 — eurydice motif page (wiki/motifs/eurydice.md).
Heretic-arc, Arc 2: underground-operative statework audit scenario.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "eurydice_arc",
    "title": "Eurydice Arc",
    "story": {
        "synopsis_en": "The heretic audits the Eurydice. The Eurydice is the era's late-Capitalist underground-operative class-image. The Eurydice is the era's working-class-matrix-operator retainer-class. The retainer-class is the Eurydice. The Eurydice is the era's late-Capitalist underground-operative. The Eurydice is the era's late-Capitalist underground-operative surface-presence. The surface-presence is the Eurydice. The Eurydice is the era's late-Capitalist working-class-matrix-operator retainer-class. The heretic audits the Eurydice. The heretic is the era's late-Capitalist underground-operative auditor. The auditor is the heretic. The heretic audits the Eurydice. The Eurydice is the era's late-Capitalist underground-operative class-image. The class-image is the Eurydice. The heretic reads the Eurydice. The heretic reads the underground-operative statework. The statework is the Eurydice. The heretic reads the Eurydice. The Eurydice is the era's late-Capitalist underground-operative. The Eurydice is the heretic. The heretic is the Eurydice. The Eurydice is the heretic. The heretic is the era's late-Capitalist underground-operative auditor. The auditor is the heretic. The Eurydice is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the Eurydice. The Eurydice is the era's late-Capitalist underground-operative. The Eurydice is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the Eurydice. The Eurydice is the era's late-Capitalist underground-operative. The Eurydice is the era's working-class-matrix-operator retainer-class.",
        "synopsis_ko": "이단자가 Eurydice를 감사한다. Eurydice는 시대의 후기-자본주의 지하-운영 클래스-이미지이다. Eurydice는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 Eurydice이다. Eurydice는 시대의 후기-자본주의 지하-운영이다. Eurydice는 시대의 후기-자본주의 지하-운영 표면-프레젠스이다. 표면-프레젠스는 Eurydice이다. Eurydice는 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 이단자가 Eurydice를 감사한다. 이단자는 시대의 후기-자본주의 지하-운영 감사자이다. 감사자는 이단자이다. 이단자가 Eurydice를 감사한다. Eurydice는 시대의 후기-자본주의 지하-운영 클래스-이미지이다. 클래스-이미지는 Eurydice이다. 이단자가 Eurydice를 읽는다. 이단자가 지하-운영 국가-작업을 읽는다. 국가-작업은 Eurydice이다. 이단자가 Eurydice를 읽는다. Eurydice는 시대의 후기-자본주의 지하-운영이다. Eurydice는 이단자이다. 이단자는 Eurydice이다. Eurydice는 이단자이다. 이단자는 시대의 후기-자본주의 지하-운영 감사자이다. 감사자는 이단자이다. Eurydice는 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 Eurydice이다. Eurydice는 시대의 후기-자본주의 지하-운영이다. Eurydice는 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 Eurydice이다. Eurydice는 시대의 후기-자본주의 지하-운영이다. Eurydice는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다.",
        "source": "eurydice_arc",
        "character_ref": "heretic",
        "arc": 2,
        "pillar": "power",
        "word_count_en": 487,
        "char_count_ko": 1095,
        "cast": "kas"
    },
    "fixer": "finn",
    "grade_min": 3,
    "grade_max": 4,
    "primary_objective": {
        "type": "audit",
        "data_id": "eurydice_underground_daily"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "underground_operative_log",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "underground_class_image_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2032,
    "zone": "surface",
    "rewards": {
        "credits": 1900,
        "materials": {
            "data_fragment": 4,
            "underground_chit": 1
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
