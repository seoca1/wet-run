<!-- result -->
요청한 설계안을 작성했습니다. 핵심 방향은 **세 덱의 티어 합을 모두 11로 맞추고**, CASE는 준비형, SIL은 알람 생존형, KAS는 감염 템포형으로 분리하는 것입니다.

- 구현 우선순위: `exploit → scan → rewind → virus → surge → shield → heal`
- 세 시작 덱:
  - CASE: `scan, exploit, boost, barrier, decoy`
  - SIL: `rewind, exploit, cloak, barrier, decoy`
  - KAS: `strike, exploit, virus, surge, decoy`
- 추가 피해 경로 없이 방어도·COST·상태 지속만 조정
- 3등급 승률 최대-최소 차이 `5%p 이하`
- 기존 CASE `78.4%` 대비 `2%p 이상 하락` 시 실패
- `rewind`와 `virus`의 과강 가능성 및 검증 지표 명시
- 기존 구현 수치와 `planned_description`의 불일치도 반영

전체 마크다운 파일:

[자키 정체성 설계 제안서](\/home\/ubuntu\/jockey_identity_proposal.md)

---

<!-- progress -->
설계안 본문을 작성했습니다. 이제 파일 존재 여부와 핵심 섹션(A~E)이 모두 들어갔는지만 확인한 뒤 전달하겠습니다.

---

<!-- progress -->
원문 기준으로 보면 핵심은 세 덱의 티어 합을 먼저 맞추고, 각 덱에 서로 다른 결정론적 상태 변환을 하나씩 부여하는 것입니다. 아래 제안은 추가 난수·타이밍·새 프로그램 없이, 기존 30개 ID만 사용합니다.

---

<!-- opening -->
요청하신 전체 과제 원문을 먼저 확인한 뒤, 엔진 제약을 벗어나지 않는 최소 메커니즘 증설안과 수치 검증 계획까지 한 번에 정리하겠습니다.