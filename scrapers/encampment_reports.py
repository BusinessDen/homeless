"""
Scrape encampment reports from Denver's PocketGov system via ArcGIS.
Source: Encampment_Reports_AGOL / layer 5
Fields: CASENUMBER, PRIORITY, CreatedDate, SUBJECT, STATUS, ClosedDate,
        ORIGIN, ASSIGNED_AGENCY__C, STREETXY__LATITUDE__S, STREETXY__LONGITUDE__S
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import (arcgis_query, epoch_to_iso, epoch_to_datetime,
                   load_json, save_json, compute_diff, today_str)

SERVICE = "Encampment_Reports_AGOL"
LAYER = 5
OUTPUT = "encampment_reports.json"
PREVIOUS = "encampment_reports_previous.json"
ID_FIELD = "CASENUMBER"


def scrape():
    print(f"[Encampment Reports] Querying {SERVICE}/{LAYER}...")
    raw = arcgis_query(SERVICE, LAYER)
    print(f"  Fetched {len(raw)} records")

    records = []
    for r in raw:
        records.append({
            "id": r.get("CASENUMBER"),
            "stream": "encampment_reports",
            "date": epoch_to_iso(r.get("CreatedDate")),
            "created": epoch_to_datetime(r.get("CreatedDate")),
            "closed": epoch_to_datetime(r.get("ClosedDate")),
            "status": r.get("STATUS"),
            "priority": r.get("PRIORITY"),
            "subject": r.get("SUBJECT"),
            "origin": r.get("ORIGIN"),
            "agency": r.get("ASSIGNED_AGENCY__C"),
            "lat": r.get("STREETXY__LATITUDE__S"),
            "lng": r.get("STREETXY__LONGITUDE__S"),
            "council_district": r.get("CITY_COUNCIL_DISTRICT__C"),
            "police_district": r.get("POLICE_DISTRICT__C"),
            "public_danger": r.get("PUBLIC_DANGER__C"),
            "resolution": r.get("RESOLUTION__C"),
            "site_status": r.get("SiteStatus"),
            "site_name": r.get("SiteName"),
            "first_seen": today_str(),
        })

    # Diff tracking
    previous = load_json(PREVIOUS)
    diff = compute_diff(records, previous, ID_FIELD)
    print(f"  Diff: {diff['summary']}")

    # Preserve first_seen from previous
    if previous:
        prev_map = {str(r.get("id", "")): r for r in previous}
        for rec in records:
            prev = prev_map.get(str(rec.get("id", "")))
            if prev and prev.get("first_seen"):
                rec["first_seen"] = prev["first_seen"]

    # Save current as previous for next run
    save_json(PREVIOUS, records)
    save_json(OUTPUT, records)

    # Save diff summary
    diff_log = load_json("diff_log.json") or []
    diff_log.append({
        "date": today_str(),
        "stream": "encampment_reports",
        "new": len(diff["new"]),
        "removed": len(diff["removed"]),
        "changed": len(diff["changed"]),
        "total": len(records),
    })
    save_json("diff_log.json", diff_log)

    return records


if __name__ == "__main__":
    scrape()
