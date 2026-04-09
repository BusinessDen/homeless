"""
Scrape encampment visit/outreach data.
Source: Encampment_Visits / layer 0
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import arcgis_query, epoch_to_iso, epoch_to_datetime, load_json, save_json, compute_diff, today_str

SERVICE = "Encampment_Visits"
LAYER = 0
OUTPUT = "encampment_visits.json"
PREVIOUS = "encampment_visits_previous.json"
ID_FIELD = "GlobalID"


def scrape():
    print(f"[Encampment Visits] Querying {SERVICE}/{LAYER}...")
    raw = arcgis_query(SERVICE, LAYER)
    print(f"  Fetched {len(raw)} records")

    records = []
    for r in raw:
        records.append({
            "id": r.get("GlobalID") or r.get("OBJECTID"),
            "stream": "encampment_visits",
            "date": epoch_to_iso(r.get("CreationDate")),
            "created": epoch_to_datetime(r.get("CreationDate")),
            "edited": epoch_to_datetime(r.get("EditDate")),
            "site": r.get("EncampmentSite"),
            "num_people": r.get("NumPeople"),
            "num_vehicles": r.get("NumVehicles"),
            "num_structures": r.get("Number_Structures"),
            "status": r.get("Status"),
            "category": r.get("Category"),
            "agency": r.get("Agency"),
            "notes": r.get("Notes"),
            "total_score": r.get("TotalScore"),
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
