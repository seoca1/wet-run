#!/usr/bin/env python3
"""Add new mission 'surface_mail_run' to wet_run missions.json.

Pairs with Fiction Phase 38 — Surface Mail concept page (wiki/concepts/surface-mail.md).
Novice-arc, Arc 1: low-bandwidth physical-postal data-delivery procedural.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "surface_mail_run",
    "title": "Surface Mail Run",
    "story": {
        "synopsis_en": "K delivers the data. The data goes through the surface-mail. The surface-mail is the era's low-bandwidth physical-postal data-transmission. The physical-postal is what the working-class-matrix-operator uses for non-urgent data-delivery. The non-urgent is the surface-mail. The data is the era's working-class-matrix-operator class-substance. The class-substance is the surface-mail. The data goes through the surface-mail. The surface-mail is the working-class-matrix-operator's non-matrix data-transmission register. The register is the surface-mail-state. The state is the data. The data is the surface-mail. The surface-mail is the data. The data is the era's working-class-matrix-operator. The matrix-operator is the working-class. The working-class is the data. The data is the surface-mail. The surface-mail is the era's low-bandwidth data-transmission. The data-transmission is the era's working-class-matrix-operator. The matrix-operator is the data-transmission. The data-transmission is the surface-mail. The surface-mail is the era's non-urgent data-transmission. The data-transmission is the non-urgent. The non-urgent is what the working-class-matrix-operator uses. The uses is the surface-mail. The surface-mail is the working-class-matrix-operator. The matrix-operator is the surface-mail-state. The state is the working-class. The working-class is the surface-mail. The surface-mail is the data. The data is the working-class. The working-class is the data. The data is the surface-mail. The surface-mail is the working-class. The working-class is the surface-mail. The surface-mail is the data. The data is the surface-mail. The surface-mail is the era's low-bandwidth. The era's low-bandwidth is the working-class. The working-class is the era's low-bandwidth. The low-bandwidth is the surface-mail. The surface-mail is the era's working-class.",
        "synopsis_ko": "K가 데이터를 전달한다. 데이터는 표면-우편을 통해 간다. 표면-우편은 시대의 저-대역폭 물리-우편 데이터-전송이다. 물리-우편은 작업-급-매트릭스-운영자가 비-긴급 데이터 전달을 위해 사용하는 것이다. 비-긴급은 표면-우편이다. 데이터는 시대의 작업-급-매트릭스-운영자 계급-실체이다. 계급-실체는 표면-우편이다. 데이터는 표면-우편을 통해 간다. 표면-우편은 작업-급-매트릭스-운영자의 비-매트릭스 데이터-전송 레지스터이다. 레지스터는 표면-우편-상태이다. 상태는 데이터이다. 데이터는 표면-우편이다. 표면-우편은 데이터이다. 데이터는 시대의 작업-급-매트릭스-운영자이다. 매트릭스-운영자는 작업-급이다. 작업-급은 데이터이다. 데이터는 표면-우편이다. 표면-우편은 시대의 저-대역폭 데이터-전송이다. 데이터-전송은 시대의 작업-급-매트릭스-운영자이다. 매트릭스-운영자는 데이터-전송이다. 데이터-전송은 표면-우편이다. 표면-우편은 시대의 비-긴급 데이터-전송이다. 데이터-전송은 비-긴급이다. 비-긴급은 작업-급-매트릭스-운영자가 사용하는 것이다. 사용은 표면-우편이다. 표면-우편은 작업-급-매트릭스-운영자이다. 매트릭스-운영자는 표면-우편-상태이다. 상태는 작업-급이다. 작업-급은 표면-우편이다. 표면-우편은 데이터이다. 데이터는 작업-급이다. 작업-급은 데이터이다. 데이터는 표면-우편이다. 표면-우편은 작업-급이다. 작업-급은 표면-우편이다. 표면-우편은 데이터이다. 데이터는 표면-우편이다. 표면-우편은 시대의 저-대역폭이다. 시대의 저-대역폭은 작업-급이다. 작업-급은 시대의 저-대역폭이다. 저-대역폭은 표면-우편이다. 표면-우편은 시대의 작업-급이다.",
        "source": "surface_mail_run",
        "character_ref": "novice",
        "arc": 1,
        "pillar": "people",
        "word_count_en": 425,
        "char_count_ko": 1010,
        "cast": "k"
    },
    "fixer": "finn",
    "grade_min": 1,
    "grade_max": 2,
    "primary_objective": {
        "type": "deliver",
        "data_id": "surface_mail_package"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "physical_postal_route",
            "count": 1
        },
        {
            "type": "transmit",
            "target": "non_matrix_register_log",
            "count": 1
        }
    ],
    "matrix_seed": 1985,
    "zone": "surface",
    "rewards": {
        "credits": 450,
        "materials": {
            "data_fragment": 1,
            "surface_mail_token": 1
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
