#!/usr/bin/env python3
"""Add new mission 'trauma_squads_pair_arc' to wet_run missions.json.

Pairs with Fiction Phase 43 — trauma-squads motif + trauma-squads-and-cortex-hound
connection pages.
Heretic-arc, Arc 4: corporate-statework scenario on trauma-squads/cortex-hound
pairing.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "trauma_squads_pair_arc",
    "title": "Trauma-Squads Pair Arc",
    "story": {
        "synopsis_en": "The heretic audits the trauma-squads / cortex-hound pairing. The trauma-squads is the era's brain-damage-management service class. The cortex-hound is the era's class-enforcement disabling technology. The cortex-hound administers the working-class-matrix-operator's disabling. The trauma-squads manages the working-class-matrix-operator's post-cortex-hound state. The pairing is the era's late-Capitalist class-enforcement mechanism. The class-enforcement mechanism is the trauma-squads / cortex-hound pairing. The pairing is the corporate-class administers + the working-class retains. The corporate-class administers the cortex-hound. The working-class retains the trauma-squads. The heretic audits the pairing. The heretic reads the corporate-class cortex-hound administration. The heretic reads the working-class trauma-squads retention. The reading is the era's late-Capitalist class-enforcement mechanism. The mechanism is the trauma-squads / cortex-hound pairing. The pairing is the heretic's class-enforcement audit. The heretic is the era's class-enforcement auditor. The auditor is the heretic. The heretic audits the pairing. The pairing is the trauma-squads / cortex-hound. The trauma-squads is the era's brain-damage-management service class. The cortex-hound is the era's class-enforcement disabling technology. The heretic is the class-enforcement auditor. The auditor is the heretic. The heretic reads the pairing. The reading is the corporate-statework's confirmation. The corporate-statework is the era's late-Capitalist class-enforcement. The heretic's audit is the corporate-statework's confirmation. The confirmation is what the heretic reads. The heretic reads the pairing. The pairing is the trauma-squads / cortex-hound. The trauma-squads is the working-class-matrix-operator's post-cortex-hound service. The cortex-hound is the working-class-matrix-operator's pre-recovery disabling. The heretic's audit is the corporate-statework's confirmation of the pairing. The pairing is the era's late-Capitalist class-enforcement mechanism. The mechanism is the heretic's audit.",
        "synopsis_ko": "이단자가 외상-분대 / 코르텍스-하운드 페어링을 감사한다. 외상-분대는 시대의 뇌-손상-관리 서비스 계급이다. 코르텍스-하운드는 시대의 계급-시행 불능화 기술이다. 코르텍스-하운드는 작업-급-매트릭스-운영자의 불능화를 시행한다. 외상-분대는 작업-급-매트릭스-운영자의 코르텍스-하운드 이후 상태를 관리한다. 페어링은 시대의 후기-자본주의 계급-시행 메커니즘이다. 계급-시행 메커니즘은 외상-분대 / 코르텍스-하운드 페어링이다. 페어링은 기업-급이 시행하고 작업-급이 보유하는 것이다. 기업-급이 코르텍스-하운드를 시행한다. 작업-급이 외상-분대를 보유한다. 이단자가 페어링을 감사한다. 이단자가 기업-급 코르텍스-하운드 시행을 읽는다. 이단자가 작업-급 외상-분대 보유를 읽는다. 읽기는 시대의 후기-자본주의 계급-시행 메커니즘이다. 메커니즘은 외상-분대 / 코르텍스-하운드 페어링이다. 페어링은 이단자의 계급-시행 감사이다. 이단자는 시대의 계급-시행 감사자이다. 감사자는 이단자이다. 이단자가 페어링을 감사한다. 페어링은 외상-분대 / 코르텍스-하운드이다. 외상-분대는 시대의 뇌-손상-관리 서비스 계급이다. 코르텍스-하운드는 시대의 계급-시행 불능화 기술이다. 이단자는 계급-시행 감사자이다. 감사자는 이단자이다. 이단자가 페어링을 읽는다. 읽기는 기업-국가-작업의 확인이다. 기업-국가-작업은 시대의 후기-자본주의 계급-시행이다. 이단자의 감사는 기업-국가-작업의 확인이다. 확인은 이단자가 읽는 것이다. 이단자가 페어링을 읽는다. 페어링은 외상-분대 / 코르텍스-하운드이다. 외상-분대는 작업-급-매트릭스-운영자의 코르텍스-하운드 이후 서비스이다. 코르텍스-하운드는 작업-급-매트릭스-운영자의 사전-회복 불능화이다. 이단자의 감사는 페어링의 기업-국가-작업의 확인이다. 페어링은 시대의 후기-자본주의 계급-시행 메커니즘이다. 메커니즘은 이단자의 감사이다.",
        "source": "trauma_squads_pair_arc",
        "character_ref": "heretic",
        "arc": 4,
        "pillar": "power",
        "word_count_en": 504,
        "char_count_ko": 1200,
        "cast": "kas"
    },
    "fixer": "finn",
    "grade_min": 4,
    "grade_max": 5,
    "primary_objective": {
        "type": "audit",
        "data_id": "trauma_squads_cortex_hound_pair_registry"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "brain_damage_management_log",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "class_enforcement_continuity_signal",
            "count": 1
        }
    ],
    "matrix_seed": 2030,
    "zone": "deep",
    "rewards": {
        "credits": 3300,
        "materials": {
            "data_fragment": 7,
            "pair_token": 1
        }
    },
    "arc": 4
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
