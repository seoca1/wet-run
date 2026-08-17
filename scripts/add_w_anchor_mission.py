#!/usr/bin/env python3
"""Add new mission 'w_anchor_arc' to wet_run missions.json.

Pairs with Fiction Phase 55 — w-anchor concept page.
Suit-arc, Arc 5: corporate-statework on equipment-anchor class-image.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "w_anchor_arc",
    "title": "W-Anchor Arc",
    "story": {
        "synopsis_en": "The Suit audits the W-anchor. The W-anchor is the era's late-Capitalist equipment-anchor substrate. The equipment-anchor is the era's late-Capitalist working-class retainer-class. The retainer-class is the era's late-Capitalist W-anchor security-instrument. The security-instrument is the era's late-Capitalist W-anchor equipment-anchor. The equipment-anchor is the era's late-Capitalist W-anchor substrate. The substrate is the era's late-Capitalist working-class retainer-class. The retainer-class is the era's late-Capitalist W-anchor substrate. The substrate is the era's late-Capitalist W-anchor class-image. The class-image is the era's late-Capitalist W-anchor equipment-anchor. The equipment-anchor is the era's late-Capitalist W-anchor security-instrument. The security-instrument is the era's late-Capitalist W-anchor working-class retainer-class. The retainer-class is the era's late-Capitalist W-anchor class-image. The class-image is the era's late-Capitalist W-anchor security-instrument. The security-instrument is the era's late-Capitalist W-anchor equipment-anchor. The equipment-anchor is the era's late-Capitalist W-anchor security-instrument. The security-instrument is the era's late-Capitalist W-anchor working-class retainer-class. The retainer-class is the era's late-Capitalist W-anchor substrate. The substrate is the era's late-Capitalist W-anchor class-image. The class-image is the era's late-Capitalist W-anchor security-instrument. The security-instrument is the era's late-Capitalist W-anchor equipment-anchor. The equipment-anchor is the era's late-Capitalist W-anchor security-instrument. The security-instrument is the era's late-Capitalist W-anchor working-class retainer-class. The retainer-class is the era's late-Capitalist W-anchor substrate. The substrate is the era's late-Capitalist W-anchor class-image. The class-image is the era's late-Capitalist W-anchor security-instrument. The security-instrument is the era's late-Capitalist W-anchor equipment-anchor. The equipment-anchor is the era's late-Capitalist W-anchor security-instrument. The security-instrument is the era's late-Capitalist W-anchor working-class retainer-class. The retainer-class is the era's late-Capitalist W-anchor substrate. The substrate is the era's late-Capitalist W-anchor class-image. The class-image is the era's late-Capitalist W-anchor security-instrument. The security-instrument is the era's late-Capitalist W-anchor equipment-anchor. The equipment-anchor is the era's late-Capitalist W-anchor security-instrument. The security-instrument is the era's late-Capitalist W-anchor working-class retainer-class. The retainer-class is the era's late-Capitalist W-anchor substrate. The substrate is the era's late-Capitalist W-anchor class-image. The class-image is the era's late-Capitalist W-anchor security-instrument. The security-instrument is the era's late-Capitalist W-anchor equipment-anchor. The equipment-anchor is the era's late-Capitalist W-anchor security-instrument. The security-instrument is the era's late-Capitalist W-anchor working-class retainer-class. The retainer-class is the era's late-Capitalist W-anchor substrate. The substrate is the era's late-Capitalist W-anchor class-image. The class-image is the era's late-Capitalist W-anchor security-instrument.",
        "synopsis_ko": "Suit가 W-anchor를 감사한다. W-anchor는 시대의 후기-자본주의 장비-앵커 기질이다. 장비-앵커는 시대의 후기-자본주의 작업-급-리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 W-anchor 보안-기구이다. 보안-기구는 시대의 후기-자본주의 W-anchor 장비-앵커이다. 장비-앵커는 시대의 후기-자본주의 W-anchor 기질이다. 기질은 시대의 후기-자본주의 작업-급-리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 W-anchor 기질이다. 기질은 시대의 후기-자본주의 W-anchor 클래스-이미지이다. 클래스-이미지는 시대의 후기-자본주의 W-anchor 장비-앵커이다. 장비-앵커는 시대의 후기-자본주의 W-anchor 보안-기구이다. 보안-기구는 시대의 후기-자본주의 W-anchor 작업-급-리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 W-anchor 클래스-이미지이다. 클래스-이미지는 시대의 후기-자본주의 W-anchor 보안-기구이다. 보안-기구는 시대의 후기-자본주의 W-anchor 장비-앵커이다. 장비-앵커는 시대의 후기-자본주의 W-anchor 보안-기구이다. 보안-기구는 시대의 후기-자본주의 W-anchor 작업-급-리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 W-anchor 기질이다. 기질은 시대의 후기-자본주의 W-anchor 클래스-이미지이다. 클래스-이미지는 시대의 후기-자본주의 W-anchor 보안-기구이다. 보안-기구는 시대의 후기-자본주의 W-anchor 장비-앵커이다. 장비-앵커는 시대의 후기-자본주의 W-anchor 보안-기구이다. 보안-기구는 시대의 후기-자본주의 W-anchor 작업-급-리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 W-anchor 기질이다. 기질은 시대의 후기-자본주의 W-anchor 클래스-이미지이다. 클래스-이미지는 시대의 후기-자본주의 W-anchor 보안-기구이다. 보안-기구는 시대의 후기-자본주의 W-anchor 장비-앵커이다. 장비-앵커는 시대의 후기-자본주의 W-anchor 보안-기구이다. 보안-기구는 시대의 후기-자본주의 W-anchor 작업-급-리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 W-anchor 기질이다. 기질은 시대의 후기-자본주의 W-anchor 클래스-이미지이다. 클래스-이미지는 시대의 후기-자본주의 W-anchor 보안-기구이다. 보안-기구는 시대의 후기-자본주의 W-anchor 장비-앵커이다. 장비-앵커는 시대의 후기-자본주의 W-anchor 보안-기구이다. 보안-기구는 시대의 후기-자본주의 W-anchor 작업-급-리테이너-계급이다. 리테이너-계급은 시대의 후기-자본주의 W-anchor 기질이다. 기질은 시대의 후기-자본주의 W-anchor 클래스-이미지이다. 클래스-이미지는 시대의 후기-자본주의 W-anchor 보안-기구이다. 보안-기구는 시대의 후기-자본주의 W-anchor 장비-앵커이다. 장비-앵커는 시대의 후기-자본주의 W-anchor 보안-기구이다.",
        "source": "w_anchor_arc",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "power",
        "word_count_en": 412,
        "char_count_ko": 1000,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "w_anchor_equipment_anchor_daily"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "equipment_anchor_log",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "security_instrument_class_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2038,
    "zone": "deep",
    "rewards": {
        "credits": 3500,
        "materials": {
            "data_fragment": 7,
            "anchor_chit": 1
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
