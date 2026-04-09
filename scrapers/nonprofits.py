"""
Track nonprofit financials for major Denver homelessness service providers.
Source: ProPublica Nonprofit Explorer API (no key required)
"""

import sys, os, json
from urllib.request import urlopen, Request
sys.path.insert(0, os.path.dirname(__file__))
from utils import load_json, save_json, today_str

OUTPUT = "nonprofits.json"
PROPUBLICA_BASE = "https://projects.propublica.org/nonprofits/api/v2"

# Major Denver homelessness service providers and their EINs
ORGANIZATIONS = [
    "Colorado Coalition for the Homeless",
    "Denver Rescue Mission",
    "Urban Peak",
    "The Delores Project",
    "Colorado Village Collaborative",
    "Bayaud Enterprises",
    "St Francis Center",
    "Mental Health Center of Denver",
    "Metro Denver Homeless Initiative",
    "Denver Housing Authority",
    "Volunteers of America Colorado",
    "Catholic Charities Denver",
    "Samaritan House",
]


def search_org(name):
    """Search ProPublica for an organization by name in Colorado."""
    from urllib.parse import quote
    url = f"{PROPUBLICA_BASE}/search.json?q={quote(name)}&state%5Bid%5D=CO"
    req = Request(url, headers={"User-Agent": "DenverHomelessTracker/1.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            orgs = data.get("organizations", [])
            # Return first Denver-area match
            for o in orgs:
                if o.get("city", "").upper() in ["DENVER", "AURORA", "LAKEWOOD", "ENGLEWOOD", "LITTLETON"]:
                    return o
            return orgs[0] if orgs else None
    except Exception:
        return None


def scrape():
    print("[Nonprofits] Fetching 990 data from ProPublica...")

    records = []
    for name in ORGANIZATIONS:
        o = search_org(name)
        if not o:
            print(f"  {name}: not found")
            continue

        ein = o.get("ein", "")
        records.append({
            "id": f"np-{ein}",
            "stream": "nonprofits",
            "name": o.get("name", name),
            "ein": ein,
            "city": o.get("city"),
            "state": o.get("state"),
            "ntee_code": o.get("ntee_code"),
            "total_revenue": o.get("income_amount"),
            "total_assets": o.get("asset_amount"),
            "score": o.get("score"),
            "first_seen": today_str(),
            "last_updated": today_str(),
        })
        rev = o.get("income_amount")
        rev_str = f"${rev:,.0f}" if rev else "N/A"
        print(f"  {o.get('name')}: EIN={ein}, revenue={rev_str}")

    save_json(OUTPUT, records)
    print(f"  Total: {len(records)} organizations")
    return records


if __name__ == "__main__":
    scrape()
