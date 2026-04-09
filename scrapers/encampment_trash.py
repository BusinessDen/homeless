"""
Scrape encampment trash service data.
Source: Encampment_Trash_Service_PBI_View / layer 0
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import arcgis_query, epoch_to_iso, epoch_to_datetime, load_json, save_json, compute_diff, today_str

SERVICE = "Encampment_Trash_Service_PBI_View"
LAYER = 0
OUTPUT = "encampment_trash.json"
PREVIOUS = "encampment_trash_previous.json"


def scrape():
    print(f"[Encampment Trash] Querying {SERVICE}/{LAYER}...")
    raw = arcgis_query(SERVICE, LAYER)
    print(f"  Fetched {len(raw)} records")

    records = []
    for r in raw:
        records.append({
            "id": r.get("GlobalID") or r.get("OBJECTID") or f"trash-{len(records)}",
            "stream": "encampment_trash",
            "raw": {k: v for k, v in r.items() if v is not None and not k.startswith("_")},
            "first_seen": today_str(),
        })

    previous = load_json(PREVIOUS)
    diff = compute_diff(records, previous, "id")
    print(f"  Diff: {diff['summary']}")

    save_json(PREVIOUS, records)
    save_json(OUTPUT, records)
    return records


if __name__ == "__main__":
    scrape()
