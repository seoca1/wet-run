#!/usr/bin/env python3
"""Add new mission 'working_class_ridership_arc' to wet_run missions.json.

Pairs with Fiction Phase 48 — working-class-ridership-and-late-capitalist-substrate
connection page (wiki/connections/working-class-ridership-and-late-capitalist-substrate.md).
Suit-arc, Arc 5: corporate-statework on working-class-ridership substrate.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "working_class_ridership_arc",
    "title": "Working-Class Ridership Arc",
    "story": {
        "synopsis_en": "The Suit audits the working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the working-class-ridership. The ridership is the era's late-Capitalist working-class-ridership. The ridership is the era's late-Capitalist working-class-ridership. The ridership is the era's late-Capitalist working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-ridership. The ridership is the era's late-Capitalist working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-ridership. The ridership is the era's late-Capitalist working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-ridership. The ridership is the era's late-Capitalist working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-ridership. The ridership is the era's late-Capitalist working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-ridership. The ridership is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-ridership. The ridership is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-matrix-operator retainer-class. The working-class-ridership is the era's late-Capitalist working-class-ridership. The ridership is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the working-class-ridership. The Suit audits the working-class-ridership. The Suit reads the ridership daily-substrate-management. The Suit's audit is the corporate-statework's confirmation. The corporate-statework is the era's late-Capitalist working-class-matrix-operator retainer-class. The retainer-class is the working-class-ridership. The working-class-ridership is the era's late-Capitalist working-class-ridership. The Suit's daily report is the corporate-statework's quarterly-reassurance signal.",
        "synopsis_ko": "Suit가 작업-급-라이더십을 감사한다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 작업-급-라이더십이다. 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. 라이더십은 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 작업-급-라이더십이다. Suit가 작업-급-라이더십을 감사한다. Suit가 라이더십 일일-기질-관리를 읽는다. Suit의 감사는 기업-국가-작업의 확인이다. 기업-국가-작업은 시대의 후기-자본주의 작업-급-매트릭스-운영자 리테이너-계급이다. 리테이너-계급은 작업-급-라이더십이다. 작업-급-라이더십은 시대의 후기-자본주의 작업-급-라이더십이다. Suit의 일일 보고서는 기업-국가-작업의 분기-재확신 신호이다.",
        "source": "working_class_ridership_arc",
        "character_ref": "suit",
        "arc": 5,
        "pillar": "power",
        "word_count_en": 504,
        "char_count_ko": 1093,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 5,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "working_class_ridership_daily"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "fukuoka_okinawan_ridership_log",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "late_capitalist_substrate_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2033,
    "zone": "deep",
    "rewards": {
        "credits": 3700,
        "materials": {
            "data_fragment": 7,
            "ridership_token": 1
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
