# -*- coding: utf-8 -*-
"""
superstock 사이트 생성기 — content/raw/*.json(WP 추출본) → 정적 HTML 전체 생성
출력: /<카테고리>/<슬러그>/index.html (기존 mystocknote URL 구조와 1:1 동일 → 향후 301 리다이렉트 가능)
      /<카테고리>/index.html, /index.html(홈), /sitemap.xml
실행: python automation/build_site.py  (리포 루트 기준)
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
import json, glob, os, re, html, sys
from urllib.parse import unquote, urlparse

BASE = "https://blog.superstockeric.workers.dev"  # 도메인 연결 시 https://superstock.blog 로 교체
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "mystocknote.blog"

NAV = [("market-catalysts", "시장재료"), ("stock-analysis", "종목분석"),
       ("theme-leaders", "테마·대장주"), ("etf-leverage-inverse", "ETF"),
       ("beginner-guide", "초보 가이드")]

CAT_DESC = {
    "market-catalysts": "가격을 움직인 재료를 매일 기록하고 수혜·피해 업종을 가른다",
    "visitor-request": "독자가 물어본 종목·계좌·세금 질문에 기준으로 답한다",
    "stock-analysis": "급등의 이유와 지속 조건을 재료 단위로 분해한다",
    "beginner-guide": "예수금 D+2부터 공매도까지, 헷갈리는 순서대로",
    "etf-leverage-inverse": "구조를 모르고 사면 손해 보는 상품의 작동 원리",
    "theme-leaders": "테마 안에서 대장이 바뀌는 시점의 신호",
    "surge-reasons": "이유 없는 급등은 없다 — 당일 수급과 재료 추적",
    "brokerage-fee-compare": "수수료·이벤트·계좌 조건을 표로 비교한다",
    "tax-isa": "세금 아끼는 구조를 계좌 단위로 설명한다",
    "ipo-listings": "공모주 청약부터 상장 첫날 대응까지",
}

DISCLAIMER = "본 사이트의 모든 콘텐츠는 정보 제공을 목적으로 하며 특정 종목의 매수·매도 추천이 아닙니다. 투자의 최종 판단과 책임은 투자자 본인에게 있습니다."


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def esc(s):
    return html.escape(s, quote=True)


def clean_content(c):
    """WP 본문 정리: 스크립트/광고 제거, 내부링크 상대화(이미지는 원 호스트 유지), lazy 이미지"""
    c = re.sub(r"<script\b[^>]*>.*?</script>", "", c, flags=re.S | re.I)
    c = re.sub(r"<ins\b[^>]*adsbygoogle[^>]*>.*?</ins>", "", c, flags=re.S | re.I)
    c = c.replace(f"https://{SRC}/wp-content", "@@WPC@@")
    c = c.replace(f"http://{SRC}/wp-content", "@@WPC@@")
    c = c.replace(f"https://{SRC}/", "/").replace(f"http://{SRC}/", "/")
    c = c.replace("@@WPC@@", f"https://{SRC}/wp-content")
    c = re.sub(r"<img\b(?![^>]*loading=)", '<img loading="lazy" ', c)
    return c


def page(title, desc, canon_path, body, extra_head=""):
    nav = "".join(f'<a href="/{s}/">{n}</a>' for s, n in NAV)
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}{canon_path}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{BASE}{canon_path}">
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="/css/style.css">
<script>try{{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
{extra_head}
</head>
<body>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="/">SUPERSTOCK<span class="tick">▲</span></a>
    <span class="brand-tag">가격이 움직인 이유를 기록한다</span>
    <nav class="main-nav" aria-label="주요 카테고리">{nav}</nav>
    <button class="theme-btn" id="themeBtn" aria-label="테마 전환">◐</button>
  </div>
</header>
{body}
<footer class="site-footer">
  <div class="wrap footer-inner">
    <div><strong>SUPERSTOCK</strong> · 주식시장에서 구별해야 할 진짜를 찾아냅니다<br>
    <a href="/market-catalysts/">전체 글</a></div>
    <p class="fine">{DISCLAIMER} © 2026 SUPERSTOCK</p>
  </div>
</footer>
<script>
document.getElementById("themeBtn").addEventListener("click",function(){{var r=document.documentElement;
var n=(r.dataset.theme||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"))==="dark"?"light":"dark";
r.dataset.theme=n;try{{localStorage.setItem("theme",n);}}catch(e){{}}}});
</script>
</body>
</html>"""


def load():
    posts = []
    for f in sorted(glob.glob(os.path.join(ROOT, "content/raw/posts-*.json"))
                    + glob.glob(os.path.join(ROOT, "content/raw/sync-*.json"))):
        posts += json.load(open(f, encoding="utf-8"))
    cats = {c["id"]: c for c in json.load(open(os.path.join(ROOT, "content/raw/categories.json"), encoding="utf-8"))}
    rewritten = {}
    for f in glob.glob(os.path.join(ROOT, "content/rewritten/*.json")):
        r = json.load(open(f, encoding="utf-8"))
        rewritten[r["id"]] = r
    seen, out = set(), []
    for p in posts:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        path = unquote(urlparse(p["link"]).path)  # /category/slug/
        cid = next((c for c in p.get("categories", []) if c in cats and cats[c]["count"] > 0), None)
        cat = cats.get(cid, {"slug": "market-catalysts", "name": "오늘의 시장재료"})
        rw = rewritten.get(p["id"])
        title = rw["title"] if rw else strip_tags(html.unescape(p["title"]["rendered"]))
        content = clean_content(rw["html"] if rw else p["content"]["rendered"])
        text = strip_tags(content)
        out.append({
            "path": path, "title": title,
            "date": p["date"][:10], "time": p["date"][11:16], "modified": p["modified"][:10],
            "iso": p["date"], "iso_mod": p["modified"],
            "excerpt": (text[:120] if rw else
                        re.sub(r"상태:\s*[a-z_]+\s*", "", strip_tags(html.unescape(p["excerpt"]["rendered"])))[:120]),
            "content": content, "cat_slug": cat["slug"], "cat_name": cat["name"],
            "minutes": max(1, round(len(text) / 600)),
        })
    out.sort(key=lambda x: x["iso"], reverse=True)
    return out


def write(relpath, content):
    fp = os.path.join(ROOT, relpath.lstrip("/"))
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(content)


def render_post(p, prev_p, next_p):
    ld = json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": p["title"],
                     "datePublished": p["iso"], "dateModified": p["iso_mod"],
                     "author": {"@type": "Organization", "name": "SUPERSTOCK"},
                     "publisher": {"@type": "Organization", "name": "SUPERSTOCK"},
                     "mainEntityOfPage": BASE + p["path"], "inLanguage": "ko",
                     "articleSection": p["cat_name"]}, ensure_ascii=False)
    bc = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "홈", "item": BASE + "/"},
        {"@type": "ListItem", "position": 2, "name": p["cat_name"], "item": f"{BASE}/{p['cat_slug']}/"},
    ]}, ensure_ascii=False)
    nav_links = ""
    if prev_p:
        nav_links += f'<a href="{esc(prev_p["path"])}"><span class="dir">← 이전 글</span>{esc(prev_p["title"])}</a>'
    if next_p:
        nav_links += f'<a href="{esc(next_p["path"])}" style="text-align:right"><span class="dir">다음 글 →</span>{esc(next_p["title"])}</a>'
    body = f"""<main class="wrap article-wrap">
  <article class="article" style="max-width:760px">
    <p class="crumb"><a href="/">홈</a> › <a href="/{p['cat_slug']}/">{esc(p['cat_name'])}</a></p>
    <h1>{esc(p['title'])}</h1>
    <div class="a-meta"><span>{p['date']} {p['time']}</span><span>읽기 {p['minutes']}분</span><span class="badge">{esc(p['cat_name'])}</span></div>
    {p['content']}
    <p class="disclaimer">{DISCLAIMER}<br>최초 발행 {p['date']} · 최종 수정 {p['modified']} · 작성 SUPERSTOCK 편집부</p>
    <nav class="prevnext" aria-label="이전 다음 글">{nav_links}</nav>
  </article>
</main>"""
    head = f'<meta property="og:type" content="article">\n<script type="application/ld+json">{ld}</script>\n<script type="application/ld+json">{bc}</script>'
    return page(f"{p['title']} — SUPERSTOCK", p["excerpt"] or p["title"], p["path"], body, head)


def render_category(slug, name, plist):
    items = "".join(
        f'<li><a href="{esc(p["path"])}"><span class="d mono">{p["date"][5:]} {p["time"]}</span>'
        f'<span><h3>{esc(p["title"])}</h3><p>{esc(p["excerpt"][:80])}</p></span></a></li>'
        for p in plist)
    body = f"""<main class="wrap">
  <div class="archive-head"><h1>{esc(name)}</h1><p>{esc(CAT_DESC.get(slug, ''))} · {len(plist)}편</p></div>
  <ol class="post-list">{items}</ol>
</main>"""
    return page(f"{name} — SUPERSTOCK", f"{name} 아카이브 · {len(plist)}편. {CAT_DESC.get(slug, '')}", f"/{slug}/", body)


def render_home(posts, cat_counts):
    lead = posts[0]
    wire = "".join(
        f'<li><a href="{esc(p["path"])}"><span class="t mono">{p["date"][5:]} {p["time"]}</span>'
        f'<span class="headline">{esc(p["title"])}<span class="cat">{esc(p["cat_name"])}</span></span></a></li>'
        for p in posts[1:8])
    deep = [p for p in posts if p["cat_slug"] != "market-catalysts"][:3]
    cards = "".join(
        f'<article class="card"><span class="cat">{esc(p["cat_name"])}</span>'
        f'<h3><a href="{esc(p["path"])}">{esc(p["title"])}</a></h3><p>{esc(p["excerpt"][:70])}</p>'
        f'<span class="meta">{p["date"]} · 읽기 {p["minutes"]}분</span></article>' for p in deep)
    topics = "".join(
        f'<a class="topic" href="/{s}/"><span class="n mono">{c}편</span><h3>{esc(n)}</h3><p>{esc(CAT_DESC.get(s, ""))}</p></a>'
        for s, n, c in cat_counts)
    ld = json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": "SUPERSTOCK",
                     "url": BASE + "/", "description": "가격이 움직인 이유를 기록하는 주식 분석 노트",
                     "inLanguage": "ko"}, ensure_ascii=False)
    body = f"""<main class="wrap">
  <div class="home-grid">
    <article class="lead-card">
      <p class="eyebrow">최신 분석</p>
      <h1><a href="{esc(lead['path'])}">{esc(lead['title'])}</a></h1>
      <p class="deck">{esc(lead['excerpt'])}</p>
      <div class="lead-meta"><span class="badge">{esc(lead['cat_name'])}</span><span>{lead['date']} {lead['time']}</span><span>읽기 {lead['minutes']}분</span></div>
    </article>
    <aside class="wire" aria-label="최신 글 피드">
      <div class="wire-head"><span class="live-dot" aria-hidden="true"></span> 시장재료 와이어 <span style="margin-left:auto;color:var(--muted);font-weight:400">수시 기록</span></div>
      <ol>{wire}</ol>
      <a class="wire-more" href="/market-catalysts/">전체 시장재료 보기 →</a>
    </aside>
  </div>
  <section class="section"><div class="section-head"><h2>토픽 맵</h2><span class="sub">주제별로 쌓아온 판단 기준</span></div>
  <div class="topics">{topics}</div></section>
  <section class="section"><div class="section-head"><h2>심층 분석</h2><a class="more" href="/stock-analysis/">전체 보기 →</a></div>
  <div class="cards">{cards}</div></section>
</main>"""
    return page("SUPERSTOCK — 가격이 움직인 이유를 기록한다",
                "뉴스 제목이 아니라 가격이 움직인 이유를 추적하는 주식 분석 노트. 시장재료·종목분석·테마 흐름을 수시로 기록합니다.",
                "/", body, f'<script type="application/ld+json">{ld}</script>')


def main():
    posts = load()
    print("posts:", len(posts))
    by_cat = {}
    for p in posts:
        by_cat.setdefault((p["cat_slug"], p["cat_name"]), []).append(p)

    for i, p in enumerate(posts):
        prev_p = posts[i + 1] if i + 1 < len(posts) else None  # 시간상 이전 글
        next_p = posts[i - 1] if i > 0 else None
        write(p["path"] + "index.html", render_post(p, prev_p, next_p))

    for (slug, name), plist in by_cat.items():
        write(f"/{slug}/index.html", render_category(slug, name, plist))

    cat_counts = sorted(((s, n, len(pl)) for (s, n), pl in by_cat.items()), key=lambda x: -x[2])[:8]
    write("/index.html", render_home(posts, cat_counts))

    urls = [f"<url><loc>{BASE}/</loc><lastmod>{posts[0]['modified']}</lastmod></url>"]
    urls += [f"<url><loc>{BASE}/{s}/</loc><lastmod>{pl[0]['modified']}</lastmod></url>" for (s, n), pl in by_cat.items()]
    urls += [f"<url><loc>{BASE}{p['path']}</loc><lastmod>{p['modified']}</lastmod></url>" for p in posts]
    write("/sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "\n".join(urls) + "\n</urlset>")
    print("done:", len(posts), "posts,", len(by_cat), "categories")


if __name__ == "__main__":
    main()
