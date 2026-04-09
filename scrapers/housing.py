"""
Scrape HOST affordable housing projects and DHS service locations.
Sources:
  HOST_AFFORDABLEHOUSING / layer 0
  DHServicesLocations_Hosted / layer 0
  AffordableHousingMap_WFL1 / layer 6 (Shelter for the Homeless)
  AffordableHousingMap_WFL1 / layer 8 (Transitional Housing)
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import arcgis_query, load_json, save_json, compute_diff, today_str

OUTPUT = "housing.json"
PREVIOUS = "housing_previous.json"


def scrape():
    records = []

    # HOST affordable housing projects
    print("[Housing] Querying HOST_AFFORDABLEHOUSING...")
    raw = arcgis_query("HOST_AFFORDABLEHOUSING", 0)
    print(f"  HOST projects: {len(raw)}")
    for r in raw:
        records.append({
            "id": f"host-{r.get('FID') or r.get('OBJECTID')}",
            "stream": "housing",
            "subtype": "host_affordable",
            "name": r.get("PROJECT_NAME"),
            "address": r.get("ADDRESS"),
            "status": r.get("STATUS"),
            "built_open_date": r.get("BUILT_OPEN_DATE"),
            "preserved_date": r.get("PRESERVED_DATE"),
            "restricted_units": r.get("RESTRICTED_UNITS"),
            "supportive_units": r.get("SUPPORTIVE_UNITS"),
            "rental_sale": r.get("RENTAL_SALE"),
            "funding_category": r.get("FUNDING_CATEGORY"),
            "neighborhood": r.get("NEIGHBORHOOD"),
            "council_district": r.get("COUNCIL_DISTRICT"),
            "lat": r.get("LAT"),
            "lng": r.get("LONG"),
            "first_seen": today_str(),
        })

    # Shelters for the Homeless (from AffordableHousingMap)
    print("[Housing] Querying AffordableHousingMap_WFL1 layer 6 (Homeless Shelters)...")
    raw_shelters = arcgis_query("AffordableHousingMap_WFL1", 6)
    print(f"  Homeless shelters: {len(raw_shelters)}")
    for r in raw_shelters:
        records.append({
            "id": f"ahm-shelter-{r.get('OBJECTID')}",
            "stream": "housing",
            "subtype": "homeless_shelter_licensed",
            "raw": {k: v for k, v in r.items() if v is not None and not k.startswith("_")},
            "first_seen": today_str(),
        })

    # Transitional Housing
    print("[Housing] Querying AffordableHousingMap_WFL1 layer 8 (Transitional Housing)...")
    raw_trans = arcgis_query("AffordableHousingMap_WFL1", 8)
    print(f"  Transitional housing: {len(raw_trans)}")
    for r in raw_trans:
        records.append({
            "id": f"ahm-trans-{r.get('OBJECTID')}",
            "stream": "housing",
            "subtype": "transitional_housing",
            "raw": {k: v for k, v in r.items() if v is not None and not k.startswith("_")},
            "first_seen": today_str(),
        })

    # DHS service locations
    print("[Housing] Querying DHServicesLocations_Hosted...")
    raw_dhs = arcgis_query("DHServicesLocations_Hosted", 0)
    print(f"  DHS locations: {len(raw_dhs)}")
    for r in raw_dhs:
        records.append({
            "id": f"dhs-{r.get('OBJECTID')}",
            "stream": "housing",
            "subtype": "dhs_service_location",
            "raw": {k: v for k, v in r.items() if v is not None and not k.startswith("_")},
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
