# -*- coding: utf-8 -*-
"""mystocknote(WP)의 새 글을 30분마다 가져와 content/raw에 누적 — build_site.py가 이어서 전체 재생성"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
import json, glob, os, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "content", "raw")
FIELDS = "id,slug,link,title,date,modified,excerpt,content,categories"


def main():
    latest = ""
    known = set()
    for f in glob.glob(os.path.join(RAW, "posts-*.json")) + glob.glob(os.path.join(RAW, "sync-*.json")):
        for p in json.load(open(f, encoding="utf-8")):
            known.add(p["id"])
            latest = max(latest, p["date"])
    url = (f"https://mystocknote.blog/wp-json/wp/v2/posts?per_page=100"
           f"&after={latest}&_fields={FIELDS}")
    with urllib.request.urlopen(url, timeout=30) as r:
        new = json.loads(r.read().decode("utf-8"))
    new = [p for p in new if p["id"] not in known]
    if not new:
        print("새 글 없음")
        return
    stamp = max(p["date"] for p in new).replace(":", "").replace("-", "")
    out = os.path.join(RAW, f"sync-{stamp}.json")
    with open(out, "w", encoding="utf-8") as fp:
        json.dump(new, fp, ensure_ascii=False)
    print(f"새 글 {len(new)}건 동기화 → {os.path.basename(out)}")


if __name__ == "__main__":
    main()
