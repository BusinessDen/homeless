"""
Track Colorado state legislation related to homelessness.
Source: OpenStates API (https://v3.openstates.org)
Requires: OPENSTATES_API_KEY secret

Also scrapes Denver city council agendas from legislativestar if available.
"""

import sys, os, json
from urllib.request import urlopen, Request
from urllib.parse import urlencode
sys.path.insert(0, os.path.dirname(__file__))
from utils import load_json, save_json, today_str

OUTPUT = "legislation.json"
OPENSTATES_BASE = "https://v3.openstates.org"

# Search terms for homelessness-related bills
SEARCH_TERMS = [
    "homeless", "homelessness", "encampment", "unsheltered",
    "camping ban", "shelter", "housing stability", "supportive housing",
    "affordable housing", "housing first", "continuum of care",
    "navigation center", "tiny home", "safe outdoor space",
    "vagrancy", "panhandling", "trespass",
    "fentanyl", "overdose", "naloxone", "mental health crisis",
]


def query_openstates(endpoint, params=None):
    """Query OpenStates API v3."""
    api_key = os.environ.get("OPENSTATES_API_KEY")
    if not api_key:
        print("  WARNING: OPENSTATES_API_KEY not set, skipping legislation scrape")
        return None

    url = f"{OPENSTATES_BASE}{endpoint}"
    if params:
        url += f"?{urlencode(params)}"

    req = Request(url, headers={
        "X-API-KEY": api_key,
        "User-Agent": "DenverHomelessTracker/1.0"
    })
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  OpenStates error: {e}")
        return None


def scrape():
    print("[Legislation] Searching Colorado bills...")

    existing = load_json(OUTPUT) or []
    existing_ids = {b["id"] for b in existing}

    new_bills = []
    for term in SEARCH_TERMS:
        data = query_openstates("/bills", {
            "jurisdiction": "Colorado",
            "q": term,
            "sort": "updated_desc",
            "per_page": 20,
        })
        if data is None:
            break  # No API key

        results = data.get("results", [])
        for bill in results:
            bill_id = bill.get("id", "")
            if bill_id in existing_ids:
                continue

            # Extract sponsors
            sponsors = []
            for s in bill.get("sponsorships", []):
                sponsors.append({
                    "name": s.get("name"),
                    "primary": s.get("primary"),
                    "classification": s.get("classification"),
                })

            # Extract latest action
            actions = bill.get("actions", [])
            latest_action = actions[-1] if actions else {}

            new_bills.append({
                "id": bill_id,
                "stream": "legislation",
                "identifier": bill.get("identifier"),
                "title": bill.get("title"),
                "session": bill.get("session"),
                "classification": bill.get("classification"),
                "subject": bill.get("subject", []),
                "sponsors": sponsors,
                "latest_action": latest_action.get("description", ""),
                "latest_action_date": latest_action.get("date", ""),
                "openstates_url": bill.get("openstates_url"),
                "sources": [s.get("url") for s in bill.get("sources", [])],
                "search_term": term,
                "first_seen": today_str(),
            })
            existing_ids.add(bill_id)

        if data is None:
            break

    # Merge and deduplicate
    all_bills = new_bills + existing

    # Deduplicate by identifier (same bill matched by multiple search terms)
    seen_identifiers = {}
    deduped = []
    for b in all_bills:
        ident = b.get("identifier", b["id"])
        if ident not in seen_identifiers:
            seen_identifiers[ident] = True
            deduped.append(b)

    save_json(OUTPUT, deduped)
    print(f"  Total: {len(deduped)} bills ({len(new_bills)} new)")
    return deduped


if __name__ == "__main__":
    scrape()
