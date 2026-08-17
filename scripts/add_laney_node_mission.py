#!/usr/bin/env python3
"""Add new mission 'laney_node_signal_run' to wet_run missions.json.

Pairs with Fiction Phase 41 — nodal-points concept + Bridge derivative
(derivative/bridge-trilogy/short-stories/{en,ko}/2026-07-19_laney_node_signal.{md,.ko.md}).
Veteran-arc, Arc 2: data-pattern perception procedural.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "laney_node_signal_run",
    "title": "Laney Node Signal Run",
    "story": {
        "synopsis_en": "Laney perceives the nodal points. The nodal points are the data-flow convergences. The convergences are what Laney perceives. Laney is the data-perceiver. The data-perceiver is Laney. Laney is the working-class-data-perceiver. The working-class-data-perceiver is Laney. Laney perceives the nodal points. The nodal points are the era's data-flow convergences. The convergences are the nodal points. The nodal points are the era's data-flow. The data-flow is the era's. The era's data-flow is the nodal points. Laney perceives the nodal points. The nodal points are the era's working-class-data-perceiver's class-substance. The class-substance is the nodal points. The nodal points are Laney's data-perception. The data-perception is the nodal points. Laney perceives the nodal points. The nodal points are the era's data-perceiver's class-substance. The class-substance is the nodal points. The nodal points are the data-perceiver. The data-perceiver is the nodal points. The nodal points are the data-flow convergences. The convergences are the data-flow. The data-flow is the convergences. The convergences are the nodal points. Laney perceives the nodal points. The nodal points are the data-flow convergences. The convergences are the data-perceiver's data-perception. The data-perception is the era's working-class-data-perceiver's class-substance. The class-substance is the nodal points. The nodal points are the data-flow convergences. The convergences are the nodal points. Laney is the data-perceiver. The data-perceiver is Laney. The data-perceiver is the era's working-class-data-perceiver. The working-class-data-perceiver is Laney. The data-perceiver is the working-class. The working-class is the data-perceiver. The data-perceiver is Laney. The nodal points are the data-flow. The data-flow is the nodal points. Laney perceives the nodal points. The nodal points are the era's. The era's nodal points are the data-flow convergences. The convergences are the data-flow. The data-flow is the era's. The era's data-flow is the nodal points. Laney is the working-class-data-perceiver. The working-class-data-perceiver is Laney. The working-class-data-perceiver is the era's nodal-points register. The register is the era's working-class-data-perceiver. The working-class-data-perceiver is the era's nodal-points register. The register is Laney.",
        "synopsis_ko": "레니가 노드 포인트를 인식한다. 노드 포인트는 데이터-흐름 수렴들이다. 수렴들은 레니가 인식하는 것이다. 레니는 데이터-인식자이다. 데이터-인식자는 레니이다. 레니는 작업-급-데이터-인식자이다. 작업-급-데이터-인식자는 레니이다. 레니가 노드 포인트를 인식한다. 노드 포인트는 시대의 데이터-흐름 수렴들이다. 수렴들은 노드 포인트이다. 노드 포인트는 시대의 데이터-흐름이다. 데이터-흐름은 시대의 것이다. 시대의 데이터-흐름은 노드 포인트이다. 레니가 노드 포인트를 인식한다. 노드 포인트는 시대의 작업-급-데이터-인식자의 계급-실체이다. 계급-실체는 노드 포인트이다. 노드 포인트는 레니의 데이터-인식이다. 데이터-인식은 노드 포인트이다. 레니가 노드 포인트를 인식한다. 노드 포인트는 시대의 데이터-인식자의 계급-실체이다. 계급-실체는 노드 포인트이다. 노드 포인트는 데이터-인식자이다. 데이터-인식자는 노드 포인트이다. 노드 포인트는 데이터-흐름 수렴들이다. 수렴들은 데이터-흐름이다. 데이터-흐름은 수렴들이다. 수렴들은 노드 포인트이다. 레니가 노드 포인트를 인식한다. 노드 포인트는 데이터-흐름 수렴들이다. 수렴들은 데이터-인식자의 데이터-인식이다. 데이터-인식은 시대의 작업-급-데이터-인식자의 계급-실체이다. 계급-실체는 노드 포인트이다. 노드 포인트는 데이터-흐름 수렴들이다. 수렴들은 노드 포인트이다. 레니는 데이터-인식자이다. 데이터-인식자는 레니이다. 데이터-인식자는 시대의 작업-급-데이터-인식자이다. 작업-급-데이터-인식자는 레니이다. 데이터-인식자는 작업-급이다. 작업-급은 데이터-인식자이다. 데이터-인식자는 레니이다. 노드 포인트는 데이터-흐름이다. 데이터-흐름은 노드 포인트이다. 레니가 노드 포인트를 인식한다. 노드 포인트는 시대의 것이다. 시대의 노드 포인트는 데이터-흐름 수렴들이다. 수렴들은 데이터-흐름이다. 데이터-흐름은 시대의 것이다. 시대의 데이터-흐름은 노드 포인트이다. 레니는 작업-급-데이터-인식자이다. 작업-급-데이터-인식자는 레니이다. 작업-급-데이터-인식자는 시대의 노드 포인트 레지스터이다. 레지스터는 시대의 작업-급-데이터-인식자이다. 작업-급-데이터-인식자는 시대의 노드 포인트 레지스터이다. 레지스터는 레니이다.",
        "source": "laney_node_signal_run",
        "character_ref": "veteran",
        "arc": 2,
        "pillar": "power",
        "word_count_en": 491,
        "char_count_ko": 1160,
        "cast": "k"
    },
    "fixer": "finn",
    "grade_min": 2,
    "grade_max": 3,
    "primary_objective": {
        "type": "audit",
        "data_id": "nodal_point_registry"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "data_flow_convergence_log",
            "count": 1
        },
        {
            "type": "transmit",
            "target": "laney_node_signal_log",
            "count": 1
        }
    ],
    "matrix_seed": 1996,
    "zone": "deep",
    "rewards": {
        "credits": 950,
        "materials": {
            "data_fragment": 2,
            "node_signal_token": 1
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
