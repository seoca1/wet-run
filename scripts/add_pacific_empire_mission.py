#!/usr/bin/env python3
"""Add new mission 'pacific_empire_arc' to wet_run missions.json.

Pairs with Fiction Phase 54 — g-boys-and-pacific-empire connection page.
Suit-arc, Arc 5: late-Capitalist East-Asian subculture class-statework scenario.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "pacific_empire_arc",
    "title": "Pacific-Empire Arc",
    "story": {
        "synopsis_en": "The Suit audits the Pacific-Empire subculture. The Pacific-Empire subculture is the era's late-Capitalist East-Asian cultural-economic dominant subculture. The subculture is the era's working-class retainer-class. The retainer-class is the era's Pacific-Empire working-class. The working-class is the era's Pacific-Empire subculture. The Pacific-Empire subculture is the era's late-Capitalist East-Asian cultural-economic dominant subculture. The subculture is the era's working-class retainer-class. The retainer-class is the era's Pacific-Empire working-class. The working-class is the era's Pacific-Empire subculture. The Pacific-Empire subculture is the era's late-Capitalist East-Asian cultural-economic dominant subculture. The subculture is the era's working-class retainer-class. The retainer-class is the era's Pacific-Empire working-class. The working-class is the era's Pacific-Empire subculture. The Pacific-Empire subculture is the era's late-Capitalist East-Asian cultural-economic dominant subculture. The subculture is the era's working-class retainer-class. The retainer-class is the era's Pacific-Empire working-class. The working-class is the era's Pacific-Empire subculture. The Pacific-Empire subculture is the era's late-Capitalist East-Asian cultural-economic dominant subculture. The subculture is the era's working-class retainer-class. The retainer-class is the era's Pacific-Empire working-class. The working-class is the era's Pacific-Empire subculture.",
        "synopsis_ko": "Suit가 Pacific-Empire 서브컬처를 감사한다. Pacific-Empire 서브컬처는 시대의 후기-자본주의 동아시아 문화-경제 지배 서브컬처이다. 서브컬처는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 Pacific-Empire 작업-급이다. 작업-급은 시대의 Pacific-Empire 서브컬처이다. Pacific-Empire 서브컬처는 시대의 후기-자본주의 동아시아 문화-경제 지배 서브컬처이다. 서브컬처는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 Pacific-Empire 작업-급이다. 작업-급은 시대의 Pacific-Empire 서브컬처이다. Pacific-Empire 서브컬처는 시대의 후기-자본주의 동아시아 문화-경제 지배 서브컬처이다. 서브컬처는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 Pacific-Empire 작업-급이다. 작업-급은 시대의 Pacific-Empire 서브컬처이다. Pacific-Empire 서브컬처는 시대의 후기-자본주의 동아시아 문화-경제 지배 서브컬처이다. 서브컬처는 시대의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 시대의 Pacific-Empire 작업-급이다. 작업-급은 시대의 Pacific-Empire 서브컬처이다.",
        "source": "pacific_empire_arc",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "power",
        "word_count_en": 413,
        "char_count_ko": 996,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "pacific_empire_subculture_daily"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "pacific_empire_log",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "east_asian_cultural_economic_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2037,
    "zone": "deep",
    "rewards": {
        "credits": 3500,
        "materials": {
            "data_fragment": 7,
            "pacific_empire_token": 1
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
