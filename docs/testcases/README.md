# Test Cases (테스트 시나리오)

게임플레이 테스트 시나리오. 디자인 명세서(`design/systems/`)의 acceptance criteria로 활용.

## 디렉토리 구조 (예정)

```
testcases/
├── README.md
├── template.md
├── combat/         # 전투 시스템 시나리오
│   └── salvage.md  # TC-COMBAT-001~008: Data Salvage (ADR-0014)
├── hacking/        # 해킹 / 매트릭스 시나리오
├── missions/       # 미션 시나리오
├── progression/    # 진행 / 메타 진행 시나리오
├── economy/        # 경제 / 거래 시나리오
├── edge/           # 엣지 케이스 / 회귀 테스트
├── balance/        # 밸런스 시나리오
└── systems/        # 시스템별 시나리오
    ├── crafting.md # TC-CRAFT-001~012: Material & Crafting (ADR-0015)
    ├── avatar.md   # TC-AVATAR-001~013: Jockey Avatar (ADR-0016)
    ├── mission-material.md # TC-MISMAT-001~012: 미션-재료 통합 (ADR-0017)
    ├── animations.md # TC-ANIM-001~012: 전투 ASCII 애니메이션 (ADR-0018)
    └── aftermath.md # TC-AFTER-001~012: 전투 후일담 & 한글 자막 (ADR-0019)
```

## 작성 규칙

1. **한 시나리오 = 한 시스템 / 한 기능** — 너무 크지 않게
2. **재현 가능** — 결정성, 시드 가능 (절차적 생성 시)
3. **명확한 결과** — pass / fail 기준 명시
4. **디자인 명세 연결** — 관련 `design/systems/*.md` 참조
5. **버전 추적** — 시나리오는 디자인 변경 시 갱신

## 시나리오 ID 규칙

- `TC-[시스템]-[번호]` 예: `TC-COMBAT-001`, `TC-HACK-003`

## 우선순위

- **P0**: 핵심 게임플레이, 반드시 통과
- **P1**: 디자인 명세에 명시된 기능
- **P2**: 보조 / 폴리시

## 상태

- **Draft**: 작성 중
- **Active**: 활성 시나리오
- **Deprecated**: 더 이상 유효하지 않음
- **Skipped**: 의도적으로 보류 (사유 명시)
