"""
Scrape encampment disruption/sweep cases.
Source: Encampment_Disruption_Cases_Oct24_Oct25_WFL1
  Layer 0: Business Disruption by Person
  Layer 1: Encampment Reporting
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import arcgis_query, epoch_to_iso, epoch_to_datetime, load_json, save_json, compute_diff, today_str

SERVICE = "Encampment_Disruption_Cases_Oct24_Oct25_WFL1"
OUTPUT = "encampment_disruptions.json"
PREVIOUS = "encampment_disruptions_previous.json"
ID_FIELD = "OBJECTID"


def scrape():
    print(f"[Encampment Disruptions] Querying...")

    # Layer 1: Encampment Reporting (richer data)
    raw = arcgis_query(SERVICE, 1)
    print(f"  Layer 1 (Encampment Reporting): {len(raw)} records")

    records = []
    for r in raw:
        desc = r.get("Description") or ""
        records.append({
            "id": f"disruption-{r.get('OBJECTID')}",
            "stream": "encampment_disruptions",
            "case_number": r.get("CASENUMBER"),
            "date": epoch_to_iso(r.get("CreatedDate")),
            "created": epoch_to_datetime(r.get("CreatedDate")),
            "closed": epoch_to_datetime(r.get("ClosedDate")),
            "status": r.get("STATUS"),
            "priority": r.get("PRIORITY"),
            "subject": r.get("SUBJECT"),
            "description": desc[:500] if desc else None,
            "origin": r.get("ORIGIN"),
            "agency": r.get("ASSIGNED_AGENCY__C"),
            "lat": r.get("STREETXY__LATITUDE__S"),
            "lng": r.get("STREETXY__LONGITUDE__S"),
            "council_district": r.get("CITY_COUNCIL_DISTRICT__C"),
            "police_district": r.get("POLICE_DISTRICT__C"),
            "resolution": r.get("RESOLUTION__C"),
            "first_seen": today_str(),
        })

    # Layer 0: Business Disruption by Person
    raw_biz = arcgis_query(SERVICE, 0)
    print(f"  Layer 0 (Business Disruption): {len(raw_biz)} records")
    for r in raw_biz:
        records.append({
            "id": f"biz-disruption-{r.get('OBJECTID')}",
            "stream": "encampment_disruptions",
            "subtype": "business_disruption",
            "date": epoch_to_iso(r.get("CreatedDate") or r.get("EditDate")),
            "raw": {k: v for k, v in r.items() if v is not None},
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
