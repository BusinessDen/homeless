"""
Master runner for all Denver Homelessness Tracker scrapers.
Runs each scraper, collects results, generates daily summary.
"""

import sys
import os
import traceback
import json
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from utils import save_json, load_json, today_str

# Import all scrapers
from encampment_reports import scrape as scrape_encampment_reports
from encampment_visits import scrape as scrape_encampment_visits
from encampment_closures import scrape as scrape_encampment_closures
from encampment_disruptions import scrape as scrape_encampment_disruptions
from encampment_services import scrape as scrape_encampment_services
from encampment_trash import scrape as scrape_encampment_trash
from crime import scrape as scrape_crime
from shelters import scrape as scrape_shelters
from housing import scrape as scrape_housing
from news_rss import scrape as scrape_news
from legislation import scrape as scrape_legislation
from spending import scrape as scrape_spending
from nonprofits import scrape as scrape_nonprofits

SCRAPERS = [
    ("encampment_reports", scrape_encampment_reports),
    ("encampment_visits", scrape_encampment_visits),
    ("encampment_closures", scrape_encampment_closures),
    ("encampment_disruptions", scrape_encampment_disruptions),
    ("encampment_services", scrape_encampment_services),
    ("encampment_trash", scrape_encampment_trash),
    ("crime", scrape_crime),
    ("shelters", scrape_shelters),
    ("housing", scrape_housing),
    ("news", scrape_news),
    ("legislation", scrape_legislation),
    ("spending", scrape_spending),
    ("nonprofits", scrape_nonprofits),
]


def run_all():
    print(f"{'='*60}")
    print(f"Denver Homelessness Tracker - Scrape Run")
    print(f"Date: {today_str()}")
    print(f"{'='*60}\n")

    results = {}
    errors = []

    for name, scrape_fn in SCRAPERS:
        print(f"\n{'─'*40}")
        try:
            data = scrape_fn()
            count = len(data) if isinstance(data, list) else 0
            results[name] = {"status": "ok", "count": count}
            print(f"  ✓ {name}: {count} records")
        except Exception as e:
            tb = traceback.format_exc()
            results[name] = {"status": "error", "error": str(e)}
            errors.append({"scraper": name, "error": str(e), "traceback": tb})
            print(f"  ✗ {name}: {e}")

    # Generate daily summary
    summary = {
        "date": today_str(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scrapers": results,
        "errors": [{"scraper": e["scraper"], "error": e["error"]} for e in errors],
        "total_scrapers": len(SCRAPERS),
        "successful": sum(1 for r in results.values() if r["status"] == "ok"),
        "failed": sum(1 for r in results.values() if r["status"] == "error"),
    }

    # Append to run history
    history = load_json("run_history.json") or []
    history.insert(0, summary)
    history = history[:90]  # Keep 90 days
    save_json("run_history.json", history)

    # Generate aggregate stats
    generate_stats()

    print(f"\n{'='*60}")
    print(f"Complete: {summary['successful']}/{summary['total_scrapers']} scrapers succeeded")
    if errors:
        print(f"Errors: {', '.join(e['scraper'] for e in errors)}")
    print(f"{'='*60}")

    return summary


def generate_stats():
    """Generate aggregate statistics across all data streams."""
    stats = {"date": today_str(), "streams": {}}

    data_files = {
        "encampment_reports": "encampment_reports.json",
        "encampment_visits": "encampment_visits.json",
        "encampment_closures": "encampment_closures.json",
        "encampment_disruptions": "encampment_disruptions.json",
        "encampment_services": "encampment_services.json",
        "encampment_trash": "encampment_trash.json",
        "crime": "crime.json",
        "shelters": "shelters.json",
        "housing": "housing.json",
        "news": "news.json",
        "legislation": "legislation.json",
        "spending": "spending.json",
        "nonprofits": "nonprofits.json",
    }

    total = 0
    for stream, filename in data_files.items():
        data = load_json(filename)
        count = len(data) if isinstance(data, list) else 0
        stats["streams"][stream] = count
        total += count

    stats["total_records"] = total
    save_json("stats.json", stats)


if __name__ == "__main__":
    run_all()
