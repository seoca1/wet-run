#!/usr/bin/env python3
"""Add new mission 'zion_vote_observation' to wet_run missions.json.

Pairs with Fiction Phase 28 — Zion Vote derivative
(derivative/sprawl-trilogy/short-stories/{en,ko}/2026-07-19_zion-vote.{md,.ko.md}).

Novice-arc, Arc 5: L-5 corridor observer mission. Operator witnesses the
cluster's 2035 vote as outsider-confederate, recording the procedural assembly.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "zion_vote_observation",
    "title": "Zion Vote Observation",
    "story": {
        "synopsis_en": "The cluster's vote is every seven years. The corporate offer is every quarter. The pilot-Cowboy stands outside the L-5 corridor's corporate-class-access zone and records the procedural assembly. The procedural assembly is the cluster's existence. Outside, in the corridor, Tessier-Ashpool has a corporate offer on the table. Inside, in the cluster's vote-hall, every seven years the cluster votes the same way: *no*. The procedural recording is what the L-5 operator's run is for: the cowboy is here to witness the *no*, the procedural recording is the matrix-presence witness, the witness is what the era's working-class-without-the-matrix has on the corporate-class's vote-tracking system. The corporate class's vote-tracking has a matrix-presence witness because the cluster has guaranteed that. The guarantee has been every seven years. Every seven years the cluster votes *no*. The pilot-Cowboy's procedural recording is what makes the vote *executable* — without the witness, the corporate-class would be able to ignore the cluster's vote. With the witness, the corporate class is bound. The binding is what the working-class-without-the-matrix posture is for. The posture is what the cluster is doing. The procedural assembly is the binding mechanism. The pilot-Cowboy's run is the procedural-record. The procedural-record is the operational. The operational is what the L-5 corridor's working-class-without-the-matrix has on the corporate class. The corporate class has nothing. The cluster has the vote. The vote has the procedural-record. The procedural-record has the pilot-Cowboy. The pilot-Cowboy has Gibson's *Neuromancer*. *Neuromancer* has the procedural-record. The procedural-record is what Maelcum's piloting-voice has been for nineteen years. The piloting-voice has been for nineteen years. Nineteen years is the procedural-record. The procedural-record is what the cluster votes *no* for. The *no* is what this run's procedural recording shows. The procedural recording shows *no*. The *no* is what the corporate-class reviewer of the L-5 corridor's vote-tracking system sees. The reviewer sees *no*. The reviewer sees what this procedural recording shows: a cluster that is working-class-without-the-matrix, that votes *no* every seven years, that has a procedural-record witness, that has a pilot-Cowboy who records *no*. The recording is the witnessing. The witnessing is the binding. The binding is the cluster's existence.",
        "synopsis_ko": "클러스터의 표결은 매 7년이다. 기업 제안은 매 분기다. 조종사-카우보이는 L-5 회랑의 기업-급-접근 구역 밖에 서서 절차적 집행을 기록한다. 절차적 집행은 클러스터의 존재다. 밖에서, 회랑에서, 테시에-아스풀이 테이블 위에 기업 제안을 가지고 있다. 안에서, 클러스터의 표결-홀에서, 매 7년마다 클러스터는 같은 방식으로 투표한다: *아니요*. 절차적 기록이 L-5 운영자의 런이 왜 존재하는지다: 카우보이는 *아니요*를 목격하기 위해 여기 있다, 절차적 기록은 매트릭스-프레젠스 목격이다, 목격은 시대의 매트릭스 없는 작업-급-일 것이 기업-급의 표결-추적 시스템에 대해 가지고 있는 것이다. 기업-급의 표결-추적은 매트릭스-프레젠스 목격이 있는 이유는 클러스터가 그것을 보장해왔기 때문이다. 보장은 매 7년이었다. 매 7년마다 클러스터는 *아니요*에 투표한다. 조종사-카우보이의 절차적 기록이 만드는 것이 있다 — 목격 없이는, 기업-급은 클러스터의 표결을 무시할 수 있을 것이다. 목격과 함께, 기업-급은 구속된다. 구속은 매트릭스 없는 작업-급-일 자세가 존재하는 이유다. 자세는 클러스터가 하고 있는 것이다. 절차적 집행은 구속 메커니즘이다. 조종사-카우보이의 런은 절차적-기록이다. 절차적-기록은 운영적이다. 운영은 L-5 회랑의 매트릭스 없는 작업-급-일이 기업-급에 대해 가지고 있는 것이다. 기업-급은 아무것도 가지지 않는다. 클러스터는 표결을 가진다. 표결은 절차적-기록을 가진다. 절차적-기록은 조종사-카우보이를 가진다. 조종사-카우보이는 깁슨의 *뉴로맨서*를 가진다. *뉴로맨서*는 절차적-기록을 가진다. 절차적-기록은 멜컴의 조종-음성이 19년 동안 했던 것이다. 조종-음성은 19년 동안이었다. 19년은 절차적-기록이다. 절차적-기록은 클러스터가 *아니요*에 투표하는 이유다. *아니요*는 이 런의 절차적 기록이 보여주는 것이다. 절차적 기록은 *아니요*를 보여준다. *아니요*는 L-5 회랑의 표결-추적 시스템의 기업-급 검토자가 보는 것이다. 검토자는 *아니요*를 본다. 검토자는 이 절차적 기록이 보여주는 것을 본다: 매트릭스-없는-작업-급-일인 클러스터, 매 7년마다 *아니요*에 투표하는, 절차적-기록 목격이 있는, *아니요*를 기록하는 조종사-카우보이가 있는. 기록은 목격이다. 목격은 구속이다. 구속은 클러스터의 존재다.",
        "source": "zion_vote_observation",
        "character_ref": "novice",
        "arc": 5,
        "pillar": "purpose",
        "word_count_en": 510,
        "char_count_ko": 1201,
        "cast": "k"
    },
    "fixer": "finn",
    "grade_min": 4,
    "grade_max": 5,
    "primary_objective": {
        "type": "record_procedural",
        "data_id": "zion_cluster_vote_2035"
    },
    "secondary_objectives": [
        {
            "type": "preserve",
            "target": "witness_record",
            "count": 1
        },
        {
            "type": "transmit",
            "target": "matrix_corporate_reviewer",
            "count": 1
        }
    ],
    "matrix_seed": 2611,
    "zone": "surface",
    "rewards": {
        "credits": 4500,
        "materials": {
            "data_fragment": 8,
            "witness_record": 1
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
