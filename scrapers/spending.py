"""
Track federal homelessness-related spending flowing to Denver.
Sources:
  - USASpending.gov API (awards by CFDA codes for homelessness programs)
  - HUD Exchange CoC awards (annual, scraped from published data)
  - Business Impact/Opportunity Grants (ArcGIS)
  - Denver city budget (future: denvergov.org opendata)

CFDA codes for homelessness programs:
  14.231 - Emergency Solutions Grant (ESG)
  14.235 - Supportive Housing Program
  14.238 - Shelter Plus Care
  14.267 - Continuum of Care (CoC)
  93.150 - Projects for Assistance in Transition from Homelessness (PATH)
  64.024 - VA Supportive Services for Veteran Families (SSVF)
"""

import sys, os, json
from urllib.request import urlopen, Request
from urllib.parse import urlencode
sys.path.insert(0, os.path.dirname(__file__))
from utils import arcgis_query, load_json, save_json, today_str

OUTPUT = "spending.json"

CFDA_CODES = ["14.231", "14.235", "14.238", "14.267", "93.150", "64.024"]


def fetch_usaspending():
    """Query USASpending.gov for Denver homelessness awards."""
    print("  Querying USASpending.gov...")
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

    payload = json.dumps({
        "filters": {
            "keywords": ["homelessness", "homeless", "continuum of care",
                         "emergency solutions grant", "shelter plus care"],
            "recipient_locations": [{"country": "USA", "state": "CO"}],
            "time_period": [{"start_date": "2020-01-01", "end_date": today_str()}],
            "award_type_codes": ["02", "03", "04", "05"],
        },
        "fields": [
            "Award ID", "Recipient Name", "Award Amount",
            "Description", "Start Date", "End Date",
            "Awarding Agency", "Award Type"
        ],
        "limit": 100,
        "page": 1,
        "sort": "Award Amount",
        "order": "desc",
    }).encode()

    req = Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "User-Agent": "DenverHomelessTracker/1.0"
    })

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            results = data.get("results", [])
            print(f"    Found {len(results)} federal awards")
            return [{
                "id": f"usa-{r.get('Award ID', '')}",
                "stream": "spending",
                "subtype": "federal_award",
                "award_id": r.get("Award ID"),
                "recipient": r.get("Recipient Name"),
                "amount": r.get("Award Amount"),
                "description": r.get("Description", "")[:300],
                "start_date": r.get("Start Date"),
                "end_date": r.get("End Date"),
                "agency": r.get("Awarding Agency"),
                "award_type": r.get("Award Type"),
                "first_seen": today_str(),
            } for r in results]
    except Exception as e:
        print(f"    USASpending error: {e}")
        return []


def fetch_bio_grants():
    """Fetch Business Impact/Opportunity encampment grants from ArcGIS."""
    print("  Querying BIO Fund Encampment Grants...")
    raw = arcgis_query("BIO_Fund_Encampment_Grant_WFL1", 0)
    print(f"    Found {len(raw)} business grant records")
    records = []
    for r in raw:
        records.append({
            "id": f"bio-{r.get('OBJECTID')}",
            "stream": "spending",
            "subtype": "bio_encampment_grant",
            "raw": {k: v for k, v in r.items() if v is not None and not k.startswith("_")},
            "first_seen": today_str(),
        })
    return records


def scrape():
    print("[Spending] Fetching spending data...")

    records = []
    records.extend(fetch_usaspending())
    records.extend(fetch_bio_grants())

    save_json(OUTPUT, records)
    print(f"  Total spending records: {len(records)}")
    return records


if __name__ == "__main__":
    scrape()
