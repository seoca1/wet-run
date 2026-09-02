# ADR-0200: Git LFS D4 — 오디오 자산 관리 (현상 유지)

**상태**: **Accepted (Option 1: 현상 유지 + 명문화)** — Draft → Accepted 2026-08-26 (this session; v1.4.0 Operational Release 후속)
**날짜**: 2026-08-26
**결정자**: 사용자
**우선순위**: P3 (Operational hygiene, 차후 재평가)
**관련**: ADR-0194 (ECS-lite 격하), ADR-0195 (Implementation Workflow), `prototype/pyproject.toml` wheel/sdist exclude, `CHANGELOG.md [1.4.0]`

## 컨텍스트 (Context)

v1.4.0 Operational Release (2026-08-26, ADR-0199 후속) 후, **Git LFS D4 결정**이 미해결 항목으로 남음:

| 항목 | 측정값 (2026-08-26 18:30 KST) |
|---|---|
| 총 오디오 파일 | 153 files |
| 총 오디오 크기 | 325.6 MB (uncompressed) |
| `dashboard/sounds/full/` | 154 MB (24 mp3, 미니맥스 BGM) |
| `dashboard/sounds/v2/` | 37 MB (12+ WAV iteration) |
| `dashboard/sounds/*.wav` (root) | ~50 MB (24 root BGM) |
| `dashboard/sounds/*.v1_backup.wav` | ~22 MB (24 backup 중복) |
| `prototype/data/sounds_test/` | 61 MB (46 game runtime WAV) |
| `data/sounds_test/` | 2.3 MB (46 legacy canonical WAV) |
| Git 저장소 `.git/objects` | 258 MB (오디오 객체 압축 후) |
| size-pack | 233.63 MiB |
| `git lfs` 설치 | ❌ 미설치 (`which git-lfs` not found) |
| `.gitattributes` | ❌ 없음 |
| GitHub LFS 무료 tier | 1 GB storage + 1 GB/month bandwidth |

### Notion 통합 보고서 (WET_RUN_2026-08-24_NOTION_READY.md) §9.1 Known Limitations:
> "Git LFS migration (321MB audio) deferred to a future release — `D4` decision pending"

321MB → 현재 측정 325.6MB (BGM v2 추가분 반영).

## 고려한 옵션

### Option 1: 현상 유지 + 명문화 — **추천 (채택)**

- **설명**: Git LFS 미적용. 현재 상태를 ADR로 명시하고 향후 재평가 트리거 정의.
- **장점**:
  - 0 작업, 0 위험
  - Git history 재작성 불필요 (force-push 회피)
  - `git lfs` brew install 불필요
  - 신규 contributor 부담 0 (GitHub 클론 시 257 MB 받음)
- **단점**:
  - 신규 contributor 1회 clone 부담 (257 MB)
  - GitHub Actions CI checkout 시 storage 영향 (LFS 미사용이면 변화 없음)
- **Pillar 정합**: 중립 (모두 영향 없음)

### Option 2: 부분 LFS (dashboard mp3만)

- **설명**: `dashboard/sounds/full/*.mp3` 만 `.gitattributes`로 LFS 추적 (154 MB)
- **장점**: 신규 clone 시 dashboard mp3 부담 제거
- **단점**: 기존 history 154MB 그대로 (migrate 안 함 → 신규 사용자만 효과), `git-lfs` brew install 필요
- **Pillar 정합**: 중립

### Option 3: 전체 LFS + history migrate

- **설명**: `.gitattributes` 전체 오디오 패턴 + `git lfs migrate import` (698 commits 재작성)
- **장점**: history 압축 (~256MB → ~1MB pointer)
- **단점**: **모든 commit hash 변경 → force-push 필수**, 협업 시 위험, 작업량 큼
- **Pillar 정합**: 중립

### Option 4: v1_backup 정리 + 부분 LFS

- **설명**: `dashboard/sounds/*.v1_backup.wav` (22MB 중복) 삭제 + Option 2
- **장점**: 22MB 즉시 절약 + 중복 제거
- **단점**: 삭제도 history 재작성 필요 (force-push)
- **Pillar 정합**: 중립

### Option 5: Audio Submodule 분리

- **설명**: `dashboard/sounds/` 를 별도 Git repository로 분리
- **장점**: wet-run repo 가벼움
- **단점**: 구조 변경 (dashboard build pipeline 영향), 복잡도 증가
- **Pillar 정합**: 중립

## 추천 (Recommendation)

**Option 1 (현상 유지 + 명문화) 채택**.

### 이유

1. **저장소 이미 origin에 push됨**: 258MB audio 객체가 이미 history에 들어가 있음. LFS 적용하려면 force-push 불가피 → 협업 위험.
2. **clone 빈도 낮음**: 주 개발자 1명, fork/re-clone 빈도 0에 가까움. 지속 비용 = 0.
3. **GitHub LFS 무료 tier 1GB 내**: 만약 LFS 적용해도 326MB < 1GB → 비용 문제 없음. Growth buffer 충분 (현재 326MB → 1GB까지 3× headroom).
4. **현재 작업 우선순위가 content/feature**: LFS는 환경 최적화(P3) — code/content authoring(P1-P2)에 비해 우선순위 낮음.
5. **옵션 트레이드오프 명시**: 향후 트리거 발생 시 Option 2/3으로 전환 가능 (ADR 본문에 트리거 정의).

### 트리거 — 다음 중 하나라도 발생 시 Option 2 또는 Option 3 재검토

- 신규 contributor 합류 (clone 빈도 증가)
- GitHub Actions CI checkout이 30초+ 소요 (storage 영향)
- 오디오 추가 합계로 1GB 초과 예상 (현재 326MB, 3× headroom)
- 외부 사용자/collaborator 추가
- GitHub가 일반 Git 압축 정책 변경 시

### 모니터링 (최소)

- 분기별 `.git/objects` 크기 확인 (`git count-objects -vH`)
- 신규 오디오 추가 시 누적 추적 (dashboard/sounds/, prototype/data/sounds_test/)
- GitHub LFS bandwidth dashboard (해당 시)

## 사용자 결정 요청

- [ ] Option 1 (현상 유지) — **채택**
- [ ] Option 2 (부분 LFS)
- [ ] Option 3 (전체 LFS + migrate)
- [ ] Option 4 (v1_backup 정리 + 부분 LFS)
- [ ] Option 5 (Submodule 분리)
- [ ] Defer (다음 결정 시점으로 미룸)

## 결과 (Consequences)

### 2026-08-26 — Option 1 채택

**핵심 결정**: Git LFS 미적용. 현상 유지하되 다음을 명문화:
- 오디오 자산은 일반 Git 추적 (대용량 binary 허용)
- GitHub LFS 무료 tier 1GB 내 머무름 (현재 326MB, 3× headroom)
- 모니터링 트리거 정의 (분기별 `.git/objects` 체크)
- 신규 오디오 추가는 `.gitignore` 검토 후 결정

### Accepted 직후 적용

- 본 ADR을 `decisions/README.md` 인덱스에 추가 (Status: Accepted)
- `log.md` 에 본 결정 기록 (v1.4.0 Operational Release 후속)
- `.gitattributes` 추가하지 않음 (LFS 미적용)

### 후속 작업 (별도 작업, user-action)

- 분기별 `.git/objects` 사이즈 체크 (1GB 초과 시 Option 2/3 재검토)
- 신규 오디오 추가는 CHANGELOG에 기록 (오디오 추가분 추적)
- GitHub Actions CI checkout 시간 모니터링 (CI workflow 최적화 필요 시)

### 거부된 옵션

- **Option 2/3**: force-push 위험, 협업 안전성 우선
- **Option 4**: 삭제도 history 재작성 필요
- **Option 5**: 구조 변경 비용 과다

## 영향 받는 항목

- `decisions/README.md` — ADR-0200 인덱스 추가
- `log.md` — 본 결정 기록
- `.gitattributes` — **추가 안 함** (LFS 미적용)

## 관련 결정

- **ADR-0199** (Accepted, 2026-08-25): Wet Run Web MVP (Tier 1) — 이 ADR의 후속으로 본 D4 결정 발생
- **CHANGELOG [1.4.0]** Known Limitations: Git LFS 321MB deferred to future release (이 ADR이 그 결정)
- **prototype/pyproject.toml** wheel/sdist exclude: `data/sounds_test/*.wav` (wheel invalid 방지) — 본 ADR은 wheel/sdist 정책과 무관

## 향후 결정

- 분기별 재평가 (`.git/objects` > 1GB 또는 다른 트리거 발생 시)
- 신규 contributor 합류 시 Option 2 (부분 LFS) 재검토
- GitHub 정책 변경 (general compression 정책 등) 시 Option 3 (전체 LFS) 재검토

## 변경 이력

- 2026-08-26: Draft 작성 (v1.4.0 Operational Release 후속, Git LFS D4 결정)
- 2026-08-26: Draft → **Accepted (Option 1: 현상 유지 + 명문화)** — 본 세션. 326MB audio in 258MB Git history, GitHub LFS 무료 tier 1GB 내 (3× headroom), clone 빈도 낮음, force-push 위험 회피. 트리거 정의 + 모니터링 권고.