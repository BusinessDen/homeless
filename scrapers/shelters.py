"""
Scrape active shelter and cold weather activation shelter data.
Sources:
  Active_Shelters / layer 0
  Cold_Weather_Activation_Shelters / layer 0
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import arcgis_query, epoch_to_iso, load_json, save_json, compute_diff, today_str

OUTPUT = "shelters.json"
PREVIOUS = "shelters_previous.json"


def scrape():
    print("[Shelters] Querying Active_Shelters...")
    active = arcgis_query("Active_Shelters", 0)
    print(f"  Active shelters: {len(active)}")

    print("[Shelters] Querying Cold_Weather_Activation_Shelters...")
    cold = arcgis_query("Cold_Weather_Activation_Shelters", 0)
    print(f"  Cold weather shelters: {len(cold)}")

    records = []

    for r in active:
        records.append({
            "id": f"active-{r.get('Unique_ID') or r.get('OBJECTID')}",
            "stream": "shelters",
            "subtype": "active",
            "name": r.get("Name"),
            "address": r.get("Address"),
            "status": r.get("Project_Status"),
            "data_date": epoch_to_iso(r.get("Data_Date")),
            "display_name": r.get("Name_to_Display_on_Map"),
            "display_info": r.get("Info_to_Display_on_Map"),
            "alias": r.get("Name_Alias"),
            "tenure_type": r.get("Tenure_Type"),
            "property_type": r.get("Property_Type"),
            "lat": r.get("Coordinates__Latitude_"),
            "lng": r.get("Coordinates__Longitude_"),
            "neighborhood": r.get("City_of_Denver_Neighborhood"),
            "census_tract": r.get("Census_Tract"),
            "zip": r.get("Zip_Code"),
            "pit_count": r.get("Show_on_PIT_Count_Map"),
            "first_seen": today_str(),
        })

    for r in cold:
        records.append({
            "id": f"cold-{r.get('OBJECTID')}",
            "stream": "shelters",
            "subtype": "cold_weather",
            "raw": {k: v for k, v in r.items() if v is not None},
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
