# superstock.blog — 고성능 주식 분석 블로그

mystocknote.blog(WordPress, TTFB ~1초)를 대체하는 정적 사이트 프로토타입.
목표: **TTFB 50ms 이하, LCP 1초 이하, 서버비 0원.**

## 구성
```
index.html        홈 (시세 스트립 · 리드 분석 · 와이어 피드 · 토픽 맵 · 초보 코스)
post.html         글 상세 템플릿 (3줄 요약 · 목차 · 표 · 반대 시나리오 · JSON-LD 3종)
category.html     카테고리 아카이브 (필터 칩 · 타임스탬프 리스트)
css/style.css     단일 스타일시트 (~12KB, 라이트/다크 토큰 시스템)
docs/분석보고서.md  원본 사이트 진단 + 벤치마킹 + 전략 전문
```
JS는 테마 토글 10줄이 전부. 프레임워크·jQuery 없음.

## 로컬 미리보기
탐색기에서 `index.html` 더블클릭 (빌드 불필요).

## 배포 (Cloudflare Pages, 무료)
1. https://dash.cloudflare.com → Workers & Pages → Create → Pages → **Direct Upload**
2. 이 폴더를 드래그 업로드 → `superstock-blog.pages.dev` 즉시 발급
3. 도메인 연결: Pages 프로젝트 → Custom domains → `superstock.blog` 추가
   (도메인 네임서버를 Cloudflare로 변경 — 등록기관에서 NS 2개 교체)
4. 이후 수정은 폴더 재업로드 또는 GitHub 연동(push 시 자동 배포)

## 확장 로드맵 (글 679개 규모 대응)
1. **Astro로 전환**: Node.js 설치 후 `npm create astro@latest` → 이 HTML을 레이아웃 컴포넌트로 이식, 글은 Markdown 컬렉션으로 관리
2. **기존 글 추출**: `https://mystocknote.blog/wp-json/wp/v2/posts?per_page=100&page=N` 반복 호출 → Markdown 변환 → `src/content/` 커밋
3. **자동발행 연동**: 기존 30분 파이프라인의 출력을 "WP 글 등록" 대신 "md 파일 커밋"으로 변경 → Pages가 자동 빌드·배포
4. **301 리다이렉트**: `_redirects` 파일에 구 URL → 신 URL 매핑 (검색 자산 보존)
5. 시세 스트립 실데이터: Cloudflare Workers(무료)로 시세 API 프록시 + 60초 엣지 캐시

## 성능 원칙 (수정 시 지킬 것)
- HTML ≤ 30KB, CSS 단일 파일 ≤ 15KB, 이미지 lazy + width/height 명시
- 광고 슬롯은 min-height 예약 (CLS < 0.05)
- 서드파티 스크립트 추가 금지 (광고 1개 예외, defer)
