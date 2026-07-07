# GitHub Actions 보안 체크리스트 — superstock.blog 파이프라인

실제 해킹 사례에 대응하는 항목별 방어. ✅ = 이 리포에 이미 적용됨, ☐ = 리포 개설 후 설정 화면에서 켜야 함.

## 실제 공격 유형과 방어

| 공격 (실사례) | 방어 | 상태 |
|---|---|---|
| **공급망: 액션 태그 바꿔치기** — 2025.3 tj-actions/changed-files 해킹: v35 등 태그가 악성 커밋으로 교체되어 2만+ 리포의 시크릿 유출 | ① 서드파티 액션 사용 0개 ② 공식 액션(actions/*)도 태그가 아닌 **커밋 SHA로 고정** | ✅ publish.yml |
| **pwn request** — pull_request_target 워크플로가 포크 PR 코드를 시크릿과 함께 실행 | 트리거를 schedule/workflow_dispatch로 한정 — PR로는 어떤 워크플로도 안 돎 | ✅ publish.yml |
| **스크립트 인젝션** — PR 제목·이슈 본문 등 `${{ github.event.* }}`를 run:에 보간 | 외부 입력 보간 0개 (날짜만 사용) | ✅ publish.yml |
| **과잉 권한 토큰 탈취** | `permissions: {}` 기본 + job에만 contents: write. PAT 미사용(기본 GITHUB_TOKEN은 리포 밖 접근 불가) | ✅ publish.yml |
| **npm/pip 공급망** | pip 의존성 0(표준 라이브러리만), wrangler 정확 버전 고정. 의존성 추가 시 `--require-hashes` | ✅ publish.yml |
| **시크릿 유출 시 피해 반경** | Cloudflare 토큰은 "Workers Scripts:Edit, 해당 계정 한정"으로 발급(Global API Key 절대 금지). DART·공공데이터 키는 무료 키라 피해 미미 — 유출 시 재발급만 | ☐ 토큰 발급 시 |

## 리포 개설 직후 설정 (Settings 화면, 5분)

1. ☐ **Settings → Actions → General**
   - "Allow **actions created by GitHub** only" 선택 (서드파티 액션 실행 자체를 차단)
   - Workflow permissions: **Read repository contents** (기본 읽기 전용)
   - "Allow GitHub Actions to create and approve pull requests" 끔
2. ☐ **Settings → Rules → Rulesets**: `.github/workflows/**` 경로 변경을 리포 소유자 외 차단하는 push ruleset 생성 (봇 커밋은 facts/·posts/만 건드리므로 충돌 없음)
3. ☐ **계정 보안**: GitHub 계정 2FA(패스키 권장) — 계정 탈취가 모든 방어를 무력화하는 단일 실패점
4. ☐ **Dependabot**: `.github/dependabot.yml`에 `package-ecosystem: github-actions` 등록 — SHA 고정 액션의 보안 업데이트를 PR로 통지받음 (자동 머지 금지, 눈으로 확인 후 머지)
5. ☐ **Secrets**: Settings → Secrets and variables → Actions에만 저장. 코드·커밋·로그에 키 문자열 금지 (Actions가 자동 마스킹하지만 base64 인코딩 출력 등은 마스킹 안 됨)

## 운영 수칙

- 워크플로 파일을 수정하는 PR/커밋은 diff를 반드시 눈으로 확인 (특히 uses: 줄의 SHA 변경)
- 액션 버전 올릴 때: 릴리스 노트 확인 → 새 태그의 커밋 SHA를 직접 조회해서 교체
- 분기마다 한 번: Settings → Actions 로그에서 낯선 실행 여부, Cloudflare 대시보드에서 낯선 배포 여부 점검
- 이 리포는 public이므로 **시크릿 외에는 전부 공개라는 전제**로 운영 (내부 메모·미공개 전략 문서를 커밋하지 않는다 — docs/는 공개해도 되는 것만)
