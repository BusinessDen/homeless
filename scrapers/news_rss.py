"""
Aggregate news from Denver media outlets, filtered for homelessness-related coverage.
Sources: RSS feeds from Denver Post, Denverite, CPR, Westword, 9News, Denver7, BusinessDen
"""

import sys, os, re, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from utils import fetch_rss, load_json, save_json, today_str

OUTPUT = "news.json"

# RSS feeds to monitor
FEEDS = [
    {"name": "Denverite", "url": "https://denverite.com/feed/", "source": "denverite"},
    {"name": "CPR News", "url": "https://www.cpr.org/feed/", "source": "cpr"},
    {"name": "Colorado Sun", "url": "https://coloradosun.com/feed/", "source": "colorado_sun"},
    {"name": "BusinessDen", "url": "https://businessden.com/feed/", "source": "businessden"},
    {"name": "9News", "url": "https://www.9news.com/feeds/syndication/rss/news", "source": "9news"},
    {"name": "Denver Post", "url": "https://feeds.denverpost.com/dp-news-breaking", "source": "denver_post"},
]

# Keywords that indicate homelessness-related coverage
KEYWORDS = [
    r"\bhomeless\b", r"\bhomelessness\b", r"\bencampment\b", r"\bunsheltered\b",
    r"\bshelter\b", r"\bhousing\s+stability\b", r"\bHOST\b", r"\ball\s+in\s+mile\s+high\b",
    r"\bcamping\s+ban\b", r"\btent\b", r"\bsweep\b", r"\bsafe\s+outdoor\s+space\b",
    r"\bmicro.?communit\b", r"\bnavigation\s+center\b", r"\btiny\s+home\b",
    r"\bdenver\s+rescue\s+mission\b", r"\bcolorado\s+coalition\s+for\s+the\s+homeless\b",
    r"\bsaint\s+francis\s+center\b", r"\bst\.?\s+francis\s+center\b",
    r"\burban\s+peak\b", r"\bpoint.in.time\b", r"\bpit\s+count\b",
    r"\bfentanyl\b", r"\boverdose\b", r"\bnaloxone\b", r"\bnarcan\b",
    r"\bvagran\b", r"\bpanhandl\b", r"\btransient\b",
    r"\bhousing\s+first\b", r"\bsupportive\s+housing\b", r"\baffordable\s+housing\b",
    r"\bjohnston.*homeless\b", r"\bhomeless.*johnston\b",
]

KEYWORD_PATTERN = re.compile("|".join(KEYWORDS), re.IGNORECASE)


def matches_keywords(text):
    """Check if text contains any homelessness-related keywords."""
    return bool(KEYWORD_PATTERN.search(text))


def article_id(url, title):
    """Generate stable ID from URL or title."""
    key = url or title
    return hashlib.md5(key.encode()).hexdigest()[:12]


def scrape():
    print("[News] Fetching RSS feeds...")

    # Load existing articles to avoid duplicates
    existing = load_json(OUTPUT) or []
    existing_ids = {a["id"] for a in existing}

    new_articles = []
    for feed in FEEDS:
        try:
            entries = fetch_rss(feed["url"])
            matched = 0
            for entry in entries:
                text = f"{entry.get('title', '')} {entry.get('summary', '')}"
                if matches_keywords(text):
                    aid = article_id(entry.get("link", ""), entry.get("title", ""))
                    if aid not in existing_ids:
                        new_articles.append({
                            "id": aid,
                            "stream": "news",
                            "source": feed["source"],
                            "source_name": feed["name"],
                            "title": entry.get("title", ""),
                            "url": entry.get("link", ""),
                            "published": entry.get("published", ""),
                            "summary": entry.get("summary", "")[:300],
                            "first_seen": today_str(),
                        })
                        existing_ids.add(aid)
                        matched += 1
            print(f"  {feed['name']}: {len(entries)} entries, {matched} matched")
        except Exception as e:
            print(f"  {feed['name']}: ERROR - {e}")

    # Merge new with existing, keep last 1000 articles
    all_articles = new_articles + existing
    all_articles = all_articles[:1000]

    save_json(OUTPUT, all_articles)
    print(f"  Total: {len(all_articles)} articles ({len(new_articles)} new)")
    return all_articles


if __name__ == "__main__":
    scrape()
