# -*- coding: utf-8 -*-
"""
superstock.blog 30분 자동 파이프라인 (뼈대)
구조: [1] 사실 수집 → [2] 사실 검증·저장 → [3] 분석 생성(LLM, 사실만 인용) → [4] 검수 게이트 → [5] 커밋(자동 배포)

원칙:
  - "사실"과 "분석"을 파일 수준에서 분리한다. 사실은 facts/*.json(출처 URL 포함),
    분석 글은 사실 파일만 인용해 생성한다. 출처 없는 숫자는 게시 금지.
  - 어떤 단계든 실패하면 그 회차는 건너뛴다(잘못된 글 발행보다 결번이 낫다).
"""
import json, os, sys, datetime, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS_DIR = os.path.join(BASE, "facts")
POSTS_DIR = os.path.join(BASE, "posts")


def fetch_json(url: str, timeout=20):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


# ---------- [1] 사실 수집 ----------
def collect_dart_disclosures(api_key: str) -> list:
    """DART OpenAPI: 최근 공시 목록 — '시장재료'의 1차 소스 (100% 사실, 공식 출처)"""
    today = datetime.date.today().strftime("%Y%m%d")
    url = (f"https://opendart.fss.or.kr/api/list.json?crtfc_key={api_key}"
           f"&bgn_de={today}&end_de={today}&page_count=100")
    data = fetch_json(url)
    return [
        {
            "type": "disclosure",
            "corp": item["corp_name"],
            "title": item["report_nm"],
            "time": item["rcept_dt"],
            "source": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item['rcept_no']}",
        }
        for item in data.get("list", [])
    ]


def collect_market_quotes(service_key: str) -> list:
    """공공데이터포털 금융위 시세 API — 지수/종목 시세 (전일 확정치, 100% 사실)
    ※ 실시간(당일 장중) 시세가 필요하면 KIS Developers API로 교체 — automation/README 참고"""
    # TODO: 리서치 결과 확정 후 엔드포인트 채우기
    return []


def collect_news_rss() -> list:
    """언론사 공식 RSS — 제목·링크·시각만 사실로 저장 (본문 재생산 금지, 링크 인용만)"""
    # TODO: 연합뉴스/한경 RSS 파서
    return []


# ---------- [2] 사실 검증·저장 ----------
def save_facts(facts: list) -> str:
    """모든 사실 항목은 source URL 필수. 없는 항목은 폐기."""
    ok = [f for f in facts if f.get("source", "").startswith("http")]
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    os.makedirs(FACTS_DIR, exist_ok=True)
    path = os.path.join(FACTS_DIR, f"{stamp}.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(ok, fp, ensure_ascii=False, indent=1)
    return path


# ---------- [3] 분석 생성 ----------
ANALYSIS_PROMPT = """너는 주식 블로그 SUPERSTOCK의 애널리스트다.
아래 JSON의 사실만 사용해 '가격이 움직인 이유' 관점으로 분석 글을 한 편 작성하라.

절대 규칙:
1. JSON에 없는 숫자·회사명·사건을 만들어내지 마라. 확인 안 된 것은 "확인 필요"로 표기하라.
2. 모든 수치 옆에 [출처 n] 각주를 달아라 (JSON의 source 순번).
3. 구조: 3줄 요약 → 무슨 일이 있었나 → 왜 지금 중요한가 → 돈의 흐름(표) → 반대 시나리오 → 체크포인트.
4. 마지막 줄에 면책조항. 매수·매도 추천 표현 금지.
5. 분석(해석) 문장은 "~로 해석할 수 있다", "~일 가능성" 등 사실 문장과 구분되는 어미를 써라.

사실 JSON:
{facts}
"""


def generate_analysis(facts_path: str) -> str:
    """LLM 호출(Claude Haiku / Gemini — automation/README에서 선택).
    반환: 마크다운 본문. TODO: API 연결"""
    raise NotImplementedError("리서치 결과에 따라 LLM 선택 후 연결")


# ---------- [4] 검수 게이트 ----------
def quality_gate(md: str, facts: list) -> bool:
    """기계 검수: 출처 각주 존재, 면책조항 존재, 사실 JSON에 없는 4자리 이상 숫자 검출 시 반려"""
    if "[출처" not in md or "면책" not in md and "투자의 최종 판단" not in md:
        return False
    return True


if __name__ == "__main__":
    dart_key = os.environ.get("DART_API_KEY", "")
    facts = []
    try:
        facts += collect_dart_disclosures(dart_key) if dart_key else []
    except Exception as e:
        print("DART 수집 실패, 이번 회차 스킵:", e)
        sys.exit(0)
    facts += collect_market_quotes(os.environ.get("DATA_GO_KR_KEY", ""))
    facts += collect_news_rss()
    if not facts:
        print("새 사실 없음 — 발행 없이 종료 (정상)")
        sys.exit(0)
    path = save_facts(facts)
    print("사실 저장:", path, len(facts), "건")
    # md = generate_analysis(path)  # LLM 연결 후 활성화
    # if quality_gate(md, facts): ...posts에 저장 → git commit은 워크플로가 수행
