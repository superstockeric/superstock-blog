# superstock.blog 자동 시작 부트스트랩
# 사용법: PowerShell에서  cd D:\superstock.blog  후  .\automation\bootstrap.ps1
# 하는 일: GitHub 로그인 → public 리포 생성·푸시 → Actions 보안설정 → 시크릿 등록 → 첫 실행

$ErrorActionPreference = "Stop"
$repo = "superstock-blog"

# 0. gh CLI 확인
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Write-Host "gh CLI가 없습니다. 설치: winget install GitHub.cli  (설치 후 새 창에서 재실행)" -ForegroundColor Red
  exit 1
}

# 1. GitHub 로그인 (브라우저 인증 — 1회만)
#    (PS5.1에서 네이티브 stderr 리다이렉트는 오류로 승격되므로 cmd 경유로 확인)
cmd /c "gh auth status >nul 2>&1"
if ($LASTEXITCODE -ne 0) {
  Write-Host "GitHub 로그인이 필요합니다. 브라우저가 열립니다..." -ForegroundColor Yellow
  gh auth login --hostname github.com --git-protocol https --web
}
$owner = gh api user --jq .login
Write-Host "로그인 계정: $owner" -ForegroundColor Green

# 2. public 리포 생성 + 푸시 (Actions 무제한 무료는 public 전제)
Set-Location "D:\superstock.blog"
cmd /c "gh repo view $owner/$repo >nul 2>&1"
if ($LASTEXITCODE -ne 0) {
  gh repo create $repo --public --source . --remote origin --push --description "가격이 움직인 이유를 기록하는 주식 분석 노트"
} else {
  Write-Host "리포가 이미 있습니다 — push만 수행" -ForegroundColor Yellow
  git push -u origin main
}

# 3. Actions 보안 설정 (SECURITY.md 체크리스트 자동 적용)
#    3-1. GitHub 공식 액션만 실행 허용
gh api "repos/$owner/$repo/actions/permissions" -X PUT -f enabled=true -f allowed_actions=selected | Out-Null
gh api "repos/$owner/$repo/actions/permissions/selected-actions" -X PUT -F github_owned_allowed=true -F verified_allowed=false | Out-Null
#    3-2. 워크플로 기본 권한 읽기 전용 + PR 승인 권한 차단
gh api "repos/$owner/$repo/actions/permissions/workflow" -X PUT -f default_workflow_permissions=read -F can_approve_pull_request_reviews=false | Out-Null
Write-Host "Actions 보안 설정 완료 (공식 액션만 허용, 기본 권한 읽기 전용)" -ForegroundColor Green

# 4. 시크릿 등록 (값은 화면에 안 보이게 입력받음)
Write-Host ""
Write-Host "API 키를 입력하세요. 아직 없으면 Enter로 건너뛰고 나중에 재실행해도 됩니다." -ForegroundColor Yellow
Write-Host "  DART 키 발급(무료·즉시): https://opendart.fss.or.kr → 인증키 신청"
$dart = Read-Host "DART_API_KEY" -AsSecureString
$dartPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($dart))
if ($dartPlain) { $dartPlain | gh secret set DART_API_KEY --repo "$owner/$repo" }

Write-Host "  공공데이터포털 키(무료·자동승인): https://www.data.go.kr → 금융위원회_주식시세정보 활용신청"
$dgk = Read-Host "DATA_GO_KR_KEY (없으면 Enter)" -AsSecureString
$dgkPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($dgk))
if ($dgkPlain) { $dgkPlain | gh secret set DATA_GO_KR_KEY --repo "$owner/$repo" }

Write-Host "  LLM 키 (Gemini 무료: https://aistudio.google.com/apikey)"
$llm = Read-Host "LLM_API_KEY (없으면 Enter)" -AsSecureString
$llmPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($llm))
if ($llmPlain) { $llmPlain | gh secret set LLM_API_KEY --repo "$owner/$repo" }

Write-Host "  Cloudflare 토큰(대시보드 → My Profile → API Tokens → 'Edit Cloudflare Workers' 템플릿, 계정 한정)"
$cft = Read-Host "CLOUDFLARE_API_TOKEN (없으면 Enter)" -AsSecureString
$cftPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($cft))
if ($cftPlain) {
  $cftPlain | gh secret set CLOUDFLARE_API_TOKEN --repo "$owner/$repo"
  $cfa = Read-Host "CLOUDFLARE_ACCOUNT_ID"
  if ($cfa) { $cfa | gh secret set CLOUDFLARE_ACCOUNT_ID --repo "$owner/$repo" }
}

# 5. 첫 실행 트리거
cmd /c "gh workflow run superstock-auto-publish --repo $owner/$repo >nul 2>&1"
Write-Host ""
Write-Host "완료! 이후는 30분마다 자동으로 돕니다." -ForegroundColor Green
Write-Host "실행 확인: https://github.com/$owner/$repo/actions"
Write-Host "남은 수동 설정(선택): 2FA 활성화, Rulesets(.github/workflows 보호) — automation\SECURITY.md 참조"
