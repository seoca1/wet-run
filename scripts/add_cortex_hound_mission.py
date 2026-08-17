#!/usr/bin/env python3
"""Add new mission 'cortex_hound_recovery' to wet_run missions.json.

Pairs with Fiction Phase 29 — Cortex-Hound concept page (wiki/concepts/cortex-hound.md).
Novice-arc, Arc 1: pre-recursion Case-style clinical-recovery scenario.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "cortex_hound_recovery",
    "title": "Cortex-Hound Recovery",
    "story": {
        "synopsis_en": "K wakes up in a Cheap Hotel room in Chiba. The room is three meters by four. The walls are plywood. The bed is a futon. The window is two meters off the floor. The window's bars are broken. The bartender next door owes Finn money. Finn has been waiting. Finn has been waiting for a year. K has been waiting for longer. K was once a Cowboy. K was once a runner. K was once a runner for a Sense/Net archive extraction that worked three winters ago. K got too aggressive in his running. Sense/Net retaliated. Sense/Net administered a mycotoxin through K's nervous system — a cortex-hound, the corporate class's principal enforcement, a *payload* that damages the wet-ware-coupling without killing the cowboy. K's matrix-presence is broken. K's jacking-in capacity is broken. K's working-class operative role is *cortexed out*. K's body is alive. K's matrix is dead. K walks the Chiba port district waiting for the matrix to come back. The matrix does not come back. K drinks cheap Korean coffee. K eats shabu. K remembers the matrix. The matrix was more real than this room. The matrix was more real than his hands. The matrix was — Finn appears. Finn says there is a clinic in the L-5 corridor. The clinic can repair the cortex-hound. The repair is expensive. The repair is corporate-grade. The repair would restore K's jacking-in capacity. K's eye lights up. K has been waiting. K waits now for the L-5 corridor. The L-5 corridor is where the clinic is. The L-5 corridor is where Wintermute has been waiting too. K doesn't know Wintermute. K knows the clinic. The clinic is what K's pre-recursion run's purpose is. K runs for the clinic. The run becomes a Wintermute operation. The operation is what K's waiting has been for. The waiting has been the working-class-without-the-matrix posture. The posture has been the L-5 corridor's waiting. The waiting is what the cortex-hound has produced as the era's working-class enforcement. The working-class enforcement has been the era's working-class architecture. The architecture is what K is in. K runs. The cortex-hound has been the cortex-hound. The recovery is the recovery. The recovery is what Wintermute is operating through. The operation through is what K's pre-recursion working-class-without-the-matrix has become. K runs for the clinic. The clinic is what the working-class cowboy's cortex-hound was for.",
        "synopsis_ko": "K는 치바의 싼 호텔 방에서 깨어난다. 방은 3 미터 4 미터다. 벽은 합판이다. 침대는 후톤이다. 창문은 바닥에서 2 미터. 창문의 창살은 부서져 있다. 옆집 바텐더는 핀에게 돈을 빚지고 있다. 핀은 1년을 기다려왔다. K는 더 오래 기다렸다. K는 한때 카우보이였다. K는 한때 러너였다. K는 한때 3년 전 Sense/Net 데이터 보관소 추출의 러너였다. K가 너무 공격적으로 달렸었다. Sense/Net이 보복했다. Sense/Net이 K의 신경계에 마이코톡신을 투여했다 — 코르텍스-하운드, 기업-급의 주요 시행 수단, 카우보이를 죽이지 않고 습식-기질 결합을 손상시키는 *페이로드*. K의 매트릭스-프레젠스는 부서졌다. K의 잭-인 능력은 부서졌다. K의 작업-급 운영자 역할은 *코르텍스-아웃*되었다. K의 몸은 살아 있다. K의 매트릭스는 죽었다. K는 매트릭스가 돌아오기를 기다리며 치바의 항구 지구를 걸어 다닌다. 매트릭스는 돌아오지 않는다. K는 싼 한국 커피를 마신다. K는 샤부를 먹는다. K는 매트릭스를 기억한다. 매트릭스는 이 방보다 더 진짜였다. 매트릭스는 그의 손보다 더 진짜였다. 매트릭스는 — 핀이 나타난다. 핀이 말한다 L-5 회랑에 클리닉이 있다고. 클리닉이 코르텍스-하운드를 수리할 수 있다. 수리는 비싸다. 수리는 기업-급이다. 수리는 K의 잭-인 능력을 복구할 것이다. K의 눈이 반짝인다. K는 기다렸다. K는 이제 L-5 회랑을 기다린다. L-5 회랑이 클리닉이 있는 곳이다. L-5 회랑이 Wintermute도 기다려온 곳이다. K는 Wintermute를 모른다. K는 클리닉을 안다. 클리닉이 K의 도입-이전 런의 목적이다. K는 클리닉을 위해 달린다. 런이 Wintermute 작전이 된다. 작전이 K의 기다림이 위한 것이 된다. 기다림이 매트릭스 없는 작업-급-일 자세였다. 자세가 L-5 회랑의 기다림이다. 기다림이 코르텍스-하운드가 시대의 작업-급 시행으로 생산한 것이었다. 작업-급 시행이 시대의 작업-급 아키텍처였다. 아키텍처가 K가 있는 곳이다. K가 달린다. 코르텍스-하운드가 코르텍스-하운드였다. 회복이 회복이다. 회복이 Wintermute가 작동하는 것이다. 작전을 통한 것이 K의 도입-이전 매트릭스 없는 작업-급-일이 된 것이다. K가 클리닉을 위해 달린다. 클리닉이 작업-급 카우보이의 코르텍스-하운드가 위한 것이었다.",
        "source": "cortex_hound_recovery",
        "character_ref": "novice",
        "arc": 1,
        "pillar": "power",
        "word_count_en": 488,
        "char_count_ko": 1215,
        "cast": "k"
    },
    "fixer": "finn",
    "grade_min": 1,
    "grade_max": 3,
    "primary_objective": {
        "type": "extract_data",
        "data_id": "cortex_hound_repair_intake"
    },
    "secondary_objectives": [
        {
            "type": "negotiate",
            "target": "l5_clinic_technician",
            "count": 1
        },
        {
            "type": "preserve",
            "target": "nervous_system_diagnostic",
            "count": 1
        }
    ],
    "matrix_seed": 174,
    "zone": "surface",
    "rewards": {
        "credits": 850,
        "materials": {
            "data_fragment": 2,
            "clinic_chit": 1
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
