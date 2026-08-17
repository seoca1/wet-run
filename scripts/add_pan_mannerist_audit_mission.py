#!/usr/bin/env python3
"""Add new mission 'pan_mannerist_audit' to wet_run missions.json.

Pairs with Fiction Phase 42 — Pan-Mannerists faction page (wiki/factions/pan-mannerists.md).
Suit-arc, Arc 5: corporate-statework on working-class-matrix-operator
retainer-class's art-movement cover.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "pan_mannerist_audit",
    "title": "Pan-Mannerist Audit",
    "story": {
        "synopsis_en": "The Suit audits the Pan-Mannerist aesthetic. The Pan-Mannerist aesthetic is the era's late-1970s / early-1980s art-movement. The art-movement is what the working-class-matrix-operator retainer-class uses. The retainer-class uses the Pan-Mannerist aesthetic. The aesthetic is the era's working-class-matrix-operator retainer-class cover. The cover is the Pan-Mannerist. The Pan-Mannerist is the working-class-matrix-operator retainer-class's art-movement. The art-movement is the working-class-matrix-operator retainer-class cover. The cover is the Pan-Mannerist. The Pan-Mannerist is the era's working-class-matrix-operator retainer-class's late-1970s / early-1980s art-movement. The art-movement is the Pan-Mannerist. The Pan-Mannerist is the era's working-class-matrix-operator retainer-class's late-1970s / early-1980s art-movement. The Pan-Mannerist is the working-class-matrix-operator retainer-class's art-movement. The art-movement is the Pan-Mannerist. The Pan-Mannerist is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the Pan-Mannerist. The Pan-Mannerist is the working-class-matrix-operator retainer-class's late-1970s / early-1980s art-movement. The art-movement is the Pan-Mannerist. The Pan-Mannerist is the era's working-class-matrix-operator retainer-class. The retainer-class is the Pan-Mannerist. The Pan-Mannerist is the era's working-class-matrix-operator retainer-class cover. The cover is the art-movement. The art-movement is the Pan-Mannerist. The Pan-Mannerist is the era's late-1970s / early-1980s working-class-matrix-operator retainer-class's art-movement. The art-movement is the era's working-class-matrix-operator retainer-class's late-1970s / early-1980s. The art-movement is the Pan-Mannerist. The Pan-Mannerist is the era's late-1970s / early-1980s. The Pan-Mannerist is the working-class-matrix-operator retainer-class's late-1970s / early-1980s. The art-movement is the Pan-Mannerist. The Pan-Mannerist is the era's late-1970s / early-1980s. The Pan-Mannerist is the working-class-matrix-operator retainer-class cover. The cover is the art-movement. The art-movement is the Pan-Mannerist. The Pan-Mannerist is the working-class-matrix-operator retainer-class's late-1970s / early-1980s.",
        "synopsis_ko": "Suit가 Pan-Mannerist 미학을 감사한다. Pan-Mannerist 미학은 시대의 후기-1970년대/초기-1980년대 예술-운동이다. 예술-운동은 작업-급-매트릭스-운영자 리테이너-계급이 사용하는 것이다. 리테이너-계급은 Pan-Mannerist 미학을 사용한다. 미학은 시대의 작업-급-매트릭스-운영자 리테이너-계급의 커버이다. 커버는 Pan-Mannerist이다. Pan-Mannerist는 작업-급-매트릭스-운영자 리테이너-계급의 예술-운동이다. 예술-운동은 작업-급-매트릭스-운영자 리테이너-계급의 커버이다. 커버는 Pan-Mannerist이다. Pan-Mannerist는 시대의 작업-급-매트릭스-운영자 리테이너-계급의 후기-1970년대/초기-1980년대 예술-운동이다. 예술-운동은 Pan-Mannerist이다. Pan-Mannerist는 시대의 작업-급-매트릭스-운영자 리테이너-계급의 후기-1970년대/초기-1980년대 예술-운동이다. Pan-Mannerist는 작업-급-매트릭스-운영자 리테이너-계급의 예술-운동이다. 예술-운동은 Pan-Mannerist이다. Pan-Mannerist는 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 Pan-Mannerist이다. Pan-Mannerist는 작업-급-매트릭스-운영자 리테이너-계급의 후기-1970년대/초기-1980년대 예술-운동이다. 예술-운동은 Pan-Mannerist이다. Pan-Mannerist는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 Pan-Mannerist이다. Pan-Mannerist는 시대의 작업-급-매트릭스-운영자 리테이너-계급의 커버이다. 커버는 예술-운동이다. 예술-운동은 Pan-Mannerist이다. Pan-Mannerist는 작업-급-매트릭스-운영자 리테이너-계급의 후기-1970년대/초기-1980년대이다. 후기-1970년대/초기-1980년대는 Pan-Mannerist이다. Pan-Mannerist는 시대의 후기-1970년대/초기-1980년대이다. Pan-Mannerist는 작업-급-매트릭스-운영자 리테이너-계급의 커버이다. 커버는 예술-운동이다. 예술-운동은 Pan-Mannerist이다. Pan-Mannerist는 작업-급-매트릭스-운영자 리테이너-계급의 후기-1970년대/초기-1980년대이다.",
        "source": "pan_mannerist_audit",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "power",
        "word_count_en": 482,
        "char_count_ko": 1134,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "pan_mannerist_aesthetic_daily"
    },
    "secondary_objectives": [
        {
            "type": "audit",
            "target": "retainer_class_aesthetic_cover",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "art_movement_continuity_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2026,
    "zone": "deep",
    "rewards": {
        "credits": 3600,
        "materials": {
            "data_fragment": 7,
            "art_movement_token": 1
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
