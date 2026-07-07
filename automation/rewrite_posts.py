# -*- coding: utf-8 -*-
"""
새로 동기화된 글을 슈퍼스톡만의 글로 재작성 — Gemini API (LLM_API_KEY 없으면 조용히 건너뜀)

원칙:
  - 사실(숫자·회사명·사건)은 원문 그대로, 구성·제목·문체만 재창작
  - 검수: 재작성본의 모든 숫자가 원문에 존재해야 통과, 아니면 폐기(원문 그대로 게시)
  - 회차당 최대 4편 (Gemini 무료 티어 보호) — 밀린 글은 다음 회차에 처리
  - 스타일: automation/style_guide.md (네이버 상위 재테크 블로거 패턴 리서치 기반)
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
import json, glob, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "content", "raw")
REW = os.path.join(ROOT, "content", "rewritten")
MAX_PER_RUN = 4
START_DATE = "2026-07-07T10:00:00"  # 이 시각 이후 발행분만 재작성 (과거 695편은 원문 유지)

MODEL = "gemini-2.5-flash"
API = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def load_style():
    p = os.path.join(ROOT, "automation", "style_guide.md")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


PROMPT = """너는 주식 블로그 SUPERSTOCK의 전속 필자다. 아래 [원문]을 소재로, 완전히 새로 쓴 글 한 편을 만들어라.

절대 규칙:
1. 원문에 있는 사실(숫자·회사명·날짜·사건)만 사용한다. 새 숫자·새 사실 창작 금지.
2. 제목·소제목·문단 구성·서술 순서·문체를 원문과 다르게 재창작한다 (표절·유사문서 판정 회피가 아니라, 다른 관점의 새 글이어야 한다).
3. 독자에게 판단 기준을 주되 매수·매도 추천 표현 금지.
4. HTML 본문으로 작성: <p>, <h2>, <ul>/<li>, <table> 만 사용. 이미지·스크립트 금지.
5. 출력은 JSON 하나만: {{"title": "...", "html": "..."}}

스타일 가이드 (네이버 상위 재테크 블로거 패턴):
{style}

[원문 제목] {title}
[원문 본문]
{content}
"""


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "")


def numbers(s):
    return set(re.findall(r"\d[\d,.]*", strip_tags(s)))


def call_gemini(key, prompt):
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.8},
    }).encode("utf-8")
    req = urllib.request.Request(f"{API}?key={key}", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read().decode("utf-8"))
    return out["candidates"][0]["content"]["parts"][0]["text"]


def main():
    key = os.environ.get("LLM_API_KEY", "").strip()
    if not key:
        print("LLM_API_KEY 미등록 — 재작성 건너뜀 (원문 그대로 게시)")
        return
    os.makedirs(REW, exist_ok=True)
    done = {os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(REW, "*.json"))}
    posts = []
    for f in glob.glob(os.path.join(RAW, "posts-*.json")) + glob.glob(os.path.join(RAW, "sync-*.json")):
        posts += json.load(open(f, encoding="utf-8"))
    todo = sorted((p for p in posts
                   if p["date"] >= START_DATE and str(p["id"]) not in done),
                  key=lambda p: p["date"], reverse=True)[:MAX_PER_RUN]
    if not todo:
        print("재작성 대상 없음")
        return
    style = load_style()
    for p in todo:
        pid = str(p["id"])
        title = strip_tags(p["title"]["rendered"])
        content = p["content"]["rendered"]
        try:
            raw = call_gemini(key, PROMPT.format(style=style, title=title, content=strip_tags(content)[:6000]))
            obj = json.loads(raw)
            new_title, new_html = obj["title"].strip(), obj["html"]
            # 검수 1: 재작성본 숫자 ⊆ 원문 숫자 (환각 차단)
            extra = numbers(new_html) - numbers(content) - numbers(title)
            if extra:
                print(f"[{pid}] 검수 반려 — 원문에 없는 숫자 {sorted(extra)[:5]} → 원문 유지")
                continue
            # 검수 2: 최소 분량·필수 태그
            if len(strip_tags(new_html)) < 500 or "<h2" not in new_html:
                print(f"[{pid}] 검수 반려 — 분량/구조 미달 → 원문 유지")
                continue
            with open(os.path.join(REW, f"{pid}.json"), "w", encoding="utf-8") as fp:
                json.dump({"id": p["id"], "title": new_title, "html": new_html,
                           "src_title": title, "model": MODEL}, fp, ensure_ascii=False)
            print(f"[{pid}] 재작성 완료: {new_title[:40]}")
        except Exception as e:
            print(f"[{pid}] 실패({e}) — 원문 유지, 다음 회차 재시도")


if __name__ == "__main__":
    main()
