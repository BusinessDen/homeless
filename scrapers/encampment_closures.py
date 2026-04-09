"""
Scrape encampment closure areas.
Source: EncampmentClosureAreas / layer 0
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import arcgis_query, epoch_to_iso, load_json, save_json, compute_diff, today_str

SERVICE = "EncampmentClosureAreas"
LAYER = 0
OUTPUT = "encampment_closures.json"
PREVIOUS = "encampment_closures_previous.json"
ID_FIELD = "OBJECTID"


def scrape():
    print(f"[Encampment Closures] Querying {SERVICE}/{LAYER}...")
    raw = arcgis_query(SERVICE, LAYER)
    print(f"  Fetched {len(raw)} records")

    records = []
    for r in raw:
        records.append({
            "id": r.get("OBJECTID"),
            "stream": "encampment_closures",
            "site_name": r.get("SiteName"),
            "site_status": r.get("SiteStatus"),
            "category": r.get("Category"),
            "opening_date": epoch_to_iso(r.get("OpeningDate")),
            "closing_date": epoch_to_iso(r.get("ClosingDate")),
            "posting_date": epoch_to_iso(r.get("PostingDate")),
            "move_in_date": epoch_to_iso(r.get("Move_In_Date")),
            "people_sheltered": r.get("People_Sheltered"),
            "police_district": r.get("POLICE_DIST"),
            "sqft": r.get("sqft"),
            "city_blocks": r.get("city_blocks"),
            "first_seen": today_str(),
        })

    previous = load_json(PREVIOUS)
    diff = compute_diff(records, previous, ID_FIELD)
    print(f"  Diff: {diff['summary']}")

    if previous:
        prev_map = {str(r.get("id", "")): r for r in previous}
        for rec in records:
            prev = prev_map.get(str(rec.get("id", "")))
            if prev and prev.get("first_seen"):
                rec["first_seen"] = prev["first_seen"]

    save_json(PREVIOUS, records)
    save_json(OUTPUT, records)
    return records


if __name__ == "__main__":
    scrape()
