# ADR-0102: v1.0.0 Release Decision

**상태**: Accepted
**날짜**: 2026-07-08
**결정자**: 사용자
**우선순위**: P2

## 컨텍스트 (Context)

Phase 7 완료 상태 — 4146 테스트 통과, 9자키/72씬/47미션/41 ICE, 모든 ADR Accepted. 로컬 빌드 `wet_run-1.0.0a1-py3-none-any.whl` 존재. v1.0.0으로 공식 태그 + PyPI 업로드 필요.

## 고려한 옵션

### Option 1: Release as 1.0.0a1 (현재 빌드 그대로)
- **설명**: `pyproject.toml` version = `"1.0.0-alpha.1"` 그대로 사용. 태그 `v1.0.0a1` 생성 후 GitHub Actions로 PyPI 업로드.
- **장점**:
  - 추가 빌드 불필요 — `dist/` 에 이미 존재하는 whl/tar.gz 활용
  -保守적 — alpha 상태 유지, 기대치 낮음
  - CI/CD 변경 최소
- **단점**:
  - PyPI 사용자가 "alpha" 버전으로 인식
  - `"Development Status :: 3 - Alpha"` classifier 유지

### Option 2: Bump to 1.0.0b1 (beta)
- **설명**: `version = "1.0.0-beta.1"` 변경 후 빌드 → 태그 `v1.0.0b1` → PyPI 업로드
- **장점**:
  - beta는 production에 가까운 안정성 표시
  - 더 넓은 사용자층 확보 가능
  - classifier `"Development Status :: 4 - Beta"` 로 변경
- **단점**:
  - 신규 빌드 필요 (`uv build`)
  - PyPI 문서에서 beta 사용 시 주의 필요

### Option 3: Release as 1.0.0 (final)
- **설명**: `version = "1.0.0"` 변경 → 빌드 → 태그 `v1.0.0` → PyPI 업로드
- **장점**:
  - 가장 깔끔한 버전 넘버링
  -pip installwet-run` 로 최신 안정 버전 획득 가능
- **단점**:
  - 아직 alpha/beta 단계의 프로젝트를 "1.0.0 final"로 표시하는 것은 사용자 기대치 오해 가능
  - classifier `"Development Status :: 4 - Beta"` 또는 `"5 - Production/Stable"` 으로 변경 필요
  - 신규 빌드 + 테스트 검증 필요

### Option 4: Release as 1.0.0a2 (증강 alpha)
- **설명**: 현재 1.0.0a1 빌드를 유지하되, pages.yml fix 등 추가 수정을 1.0.0a2로 태그
- **장점**:
  - incremental release — 위험 최소화
  - 현재 빌드는 건드리지 않음
- **단점**:
  - 의미 있는 사용자 가치 제공 없음
  - alpha太多了 — 사용자 혼란

## 추천 (Recommendation)

**Option 1 (1.0.0a1)** 또는 **Option 2 (1.0.0b1)** 권장.

선택 기준:
- 내부/매우 초기 사용자 대상 → **Option 1** (현 상태 그대로)
- 더 넓은 공개 테스트 목표 → **Option 2** (beta로 격상)

현재 Phase 7 완료이고 모든 핵심 시스템 구현 완료 → **Option 2 (1.0.0b1)** 이 적절한 Upgrade로 보임.

## PyPI Release Workflow 옵션

### A: 자동 Release (태그 트리거)
- `ci.yml` 에 `v*` 태그 푸시 시 자동 PyPI 업로드 job 추가
- `PYPI_API_TOKEN` secret 필요

### B: 수동 Release (workflow_dispatch)
- 별도 `release.yml` workflow — 수동 트리거 시 PyPI 업로드
- 더 안전하지만 수동 조작 필요

**권장**: Option B (수동) — 초기에 실수 방지

## 사용자 결정 (Decision)

### 버전
- **Selected**: Option 2: 1.0.0b1 (beta로 격상)

### Release Workflow
- **Selected**: Option B: 수동 (workflow_dispatch) — 사용자가 수동 트리거

### PyPI Token
- **Pending**: PYPI_API_TOKEN repository secret 추가 필요 (아직 미설정)

## 결과 (Consequences)

- `pyproject.toml` version은 release.yml workflow_dispatch가 동적으로 업데이트 (1.0.0b1로 빌드 시)
- `Development Status :: 4 - Beta` classifier로 설정됨
- PyPI 업로드는 workflow_dispatch 트리거 후 수동 실행
- GitHub tag `v1.0.0b1` 자동 생성됨
- `--prelease` 플래그로 PyPI에 betaとして 업로드

## 결과 (Consequences)

(결정 후 작성)

## 영향 받는 항목

- `prototype/pyproject.toml` (version, classifiers)
- `.github/workflows/release.yml` (신규 또는 ci.yml 확장)
- `dist/` 빌드 결과물

## 관련 결정

- ADR-0030 (GitHub 활용 계획 — MIT License 포함)

## 변경 이력

- 2026-07-08: Draft 작성
