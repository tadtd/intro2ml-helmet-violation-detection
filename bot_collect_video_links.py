import time
from pathlib import Path
from urllib.parse import quote

import pandas as pd
from playwright.sync_api import sync_playwright

QUERIES = [
    "khong doi mu bao hiem xe may camera giao thong",
    "xe may khong doi mu bao hiem bi phat nguoi",
    "camera phat nguoi khong doi mu bao hiem",
    "vi pham giao thong khong doi mu bao hiem",
    "CSGT xu phat xe may khong doi mu",
    "camera hanh trinh xe may khong doi mu bao hiem",
]

NO_HELMET_KEYWORDS = [
    "khong doi mu",
    "khong doi mu bao hiem",
    "khong mu",
    "vi pham",
    "bi phat",
    "phat nguoi",
    "xu phat",
]

MAX_RESULTS_PER_QUERY = 40
SCROLL_TIMES = 8
OUT_CSV = "data/videos.csv"


def _keyword_score(text: str) -> int:
    lowered = text.lower()
    return sum(1 for kw in NO_HELMET_KEYWORDS if kw in lowered)


def collect_youtube_links() -> None:
    out_csv_path = Path(OUT_CSV)
    out_csv_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for query in QUERIES:
            search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
            page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)

            for _ in range(SCROLL_TIMES):
                page.mouse.wheel(0, 5000)
                time.sleep(2)

            anchors = page.locator("a#video-title")
            count = min(anchors.count(), MAX_RESULTS_PER_QUERY)

            seen = set()
            for i in range(count):
                try:
                    a = anchors.nth(i)
                    title = a.get_attribute("title") or ""
                    href = a.get_attribute("href") or ""
                    if not href.startswith("/watch"):
                        continue

                    video_url = "https://www.youtube.com" + href
                    if video_url in seen:
                        continue
                    seen.add(video_url)

                    rows.append(
                        {
                            "source": "youtube",
                            "query": query,
                            "title": title.strip(),
                            "video_url": video_url,
                            "no_helmet_keyword_score": _keyword_score(title),
                        }
                    )
                except Exception:
                    continue

        browser.close()

    df = pd.DataFrame(rows).drop_duplicates(subset=["video_url"])
    df.to_csv(out_csv_path, index=False, encoding="utf-8-sig")
    print(f"Saved {len(df)} video links to {out_csv_path}")


if __name__ == "__main__":
    collect_youtube_links()
