"""
Scrape encampment services data (trash, portlets, sharps, hand washing).
Source: EncampmentsServices / layer 0
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import arcgis_query, load_json, save_json, compute_diff, today_str

SERVICE = "EncampmentsServices"
LAYER = 0
OUTPUT = "encampment_services.json"
PREVIOUS = "encampment_services_previous.json"


def scrape():
    print(f"[Encampment Services] Querying {SERVICE}/{LAYER}...")
    raw = arcgis_query(SERVICE, LAYER)
    print(f"  Fetched {len(raw)} records")

    records = []
    for r in raw:
        records.append({
            "id": r.get("OBJECTID"),
            "stream": "encampment_services",
            "location": r.get("Location"),
            "trash": r.get("Trash"),
            "portolets": r.get("Portolets"),
            "hand_washing": r.get("HandWashingStation"),
            "sharps": r.get("Sharps"),
            "first_seen": today_str(),
        })

    previous = load_json(PREVIOUS)
    diff = compute_diff(records, previous, "id")
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
