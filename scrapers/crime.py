"""
Scrape crime data filtered to categories correlated with homelessness.
Source: ODC_CRIME_OFFENSES_P / layer 324
Filters: trespass, criminal mischief, drug/alcohol, public disorder, theft from person
Only pulls last 90 days to keep dataset manageable.
"""

import sys, os
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from utils import arcgis_query, epoch_to_iso, epoch_to_datetime, load_json, save_json, today_str

SERVICE = "ODC_CRIME_OFFENSES_P"
LAYER = 324
OUTPUT = "crime.json"

# Offense categories and types correlated with homelessness
RELEVANT_CATEGORIES = [
    "public-disorder",
    "drug-alcohol",
    "all-other-crimes",
]


def scrape():
    print(f"[Crime] Querying {SERVICE}/{LAYER}...")

    # Last 90 days using ArcGIS timestamp syntax
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    # Query by category (avoids overly long IN clauses)
    raw = []
    for cat in RELEVANT_CATEGORIES:
        where = f"REPORTED_DATE > timestamp '{cutoff_str}' AND OFFENSE_CATEGORY_ID = '{cat}'"
        batch = arcgis_query(SERVICE, LAYER, where=where)
        print(f"  {cat}: {len(batch)} records")
        raw.extend(batch)
    print(f"  Total: {len(raw)} crime records (last 90 days)")


    records = []
    for r in raw:
        records.append({
            "id": r.get("OFFENSE_ID"),
            "stream": "crime",
            "incident_id": r.get("INCIDENT_ID"),
            "date": epoch_to_iso(r.get("REPORTED_DATE")),
            "reported": epoch_to_datetime(r.get("REPORTED_DATE")),
            "first_occurrence": epoch_to_datetime(r.get("FIRST_OCCURRENCE_DATE")),
            "offense_type": r.get("OFFENSE_TYPE_ID"),
            "offense_category": r.get("OFFENSE_CATEGORY_ID"),
            "offense_code": r.get("OFFENSE_CODE"),
            "address": r.get("INCIDENT_ADDRESS"),
            "lat": r.get("GEO_LAT"),
            "lng": r.get("GEO_LON"),
            "district": r.get("DISTRICT_ID"),
            "precinct": r.get("PRECINCT_ID"),
            "neighborhood": r.get("NEIGHBORHOOD_ID"),
            "is_crime": r.get("IS_CRIME"),
            "victim_count": r.get("VICTIM_COUNT"),
        })

    save_json(OUTPUT, records)

    # Also save a neighborhood summary
    from collections import Counter
    hood_counts = Counter(r["neighborhood"] for r in records if r.get("neighborhood"))
    type_counts = Counter(r["offense_type"] for r in records if r.get("offense_type"))

    summary = {
        "date": today_str(),
        "total_records": len(records),
        "period": "last_90_days",
        "by_neighborhood": dict(hood_counts.most_common(30)),
        "by_offense_type": dict(type_counts.most_common(20)),
    }
    save_json("crime_summary.json", summary)

    return records


if __name__ == "__main__":
    scrape()
