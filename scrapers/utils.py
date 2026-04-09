"""
Shared utilities for Denver Homelessness Tracker scrapers.
- ArcGIS Feature Server pagination (handles 2000-record limit)
- Diff tracking (detect new/changed/removed records)
- Date helpers
- JSON I/O
"""

import json
import os
import hashlib
import time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError

ARCGIS_BASE = "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
MAX_RECORD_COUNT = 2000
REQUEST_DELAY = 0.2  # seconds between paginated requests


def arcgis_query(service_name, layer_id, where="1=1", out_fields="*",
                 extra_params=None, max_records=None):
    """
    Query an ArcGIS Feature Server with automatic pagination.
    Returns list of feature attribute dicts.
    """
    url_base = f"{ARCGIS_BASE}/{service_name}/FeatureServer/{layer_id}/query"
    all_features = []
    offset = 0

    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "f": "json",
            "resultRecordCount": MAX_RECORD_COUNT,
            "resultOffset": offset,
        }
        if extra_params:
            params.update(extra_params)

        url = f"{url_base}?{urlencode(params)}"
        try:
            req = Request(url, headers={"User-Agent": "DenverHomelessTracker/1.0"})
            with urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
        except HTTPError as e:
            print(f"  HTTP {e.code} querying {service_name}/{layer_id} at offset {offset}")
            break
        except Exception as e:
            print(f"  Error querying {service_name}/{layer_id}: {e}")
            break

        if "error" in data:
            print(f"  ArcGIS error: {data['error']}")
            break

        features = data.get("features", [])
        if not features:
            break

        for f in features:
            attrs = f.get("attributes", {})
            # Include geometry if present
            geom = f.get("geometry")
            if geom:
                if "x" in geom and "y" in geom:
                    attrs["_geo_x"] = geom["x"]
                    attrs["_geo_y"] = geom["y"]
                elif "rings" in geom:
                    attrs["_geo_rings"] = True  # polygon, skip raw data
            all_features.append(attrs)

        offset += len(features)
        if max_records and offset >= max_records:
            break
        if len(features) < MAX_RECORD_COUNT:
            break  # last page

        time.sleep(REQUEST_DELAY)

    return all_features


def epoch_to_iso(epoch_ms):
    """Convert ArcGIS epoch milliseconds to ISO date string."""
    if epoch_ms is None:
        return None
    try:
        return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except (ValueError, TypeError, OSError):
        return None


def epoch_to_datetime(epoch_ms):
    """Convert ArcGIS epoch milliseconds to ISO datetime string."""
    if epoch_ms is None:
        return None
    try:
        return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError, OSError):
        return None


def record_hash(record, key_fields):
    """Generate a stable hash for a record based on key fields."""
    key = "|".join(str(record.get(f, "")) for f in key_fields)
    return hashlib.md5(key.encode()).hexdigest()


def load_json(filename):
    """Load JSON from data directory."""
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


def save_json(filename, data):
    """Save JSON to data directory."""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  Saved {path} ({len(data) if isinstance(data, list) else 'object'})")


def compute_diff(current_records, previous_records, id_field):
    """
    Compare current vs previous records by id_field.
    Returns dict with 'new', 'removed', 'changed' lists and 'summary' string.
    """
    if previous_records is None:
        return {
            "new": current_records,
            "removed": [],
            "changed": [],
            "summary": f"Baseline: {len(current_records)} records"
        }

    prev_by_id = {str(r.get(id_field, "")): r for r in previous_records}
    curr_by_id = {str(r.get(id_field, "")): r for r in current_records}

    new = [r for rid, r in curr_by_id.items() if rid not in prev_by_id]
    removed = [r for rid, r in prev_by_id.items() if rid not in curr_by_id]
    changed = []
    for rid, r in curr_by_id.items():
        if rid in prev_by_id and json.dumps(r, sort_keys=True) != json.dumps(prev_by_id[rid], sort_keys=True):
            changed.append(r)

    summary = f"+{len(new)} new, -{len(removed)} removed, ~{len(changed)} changed (total: {len(current_records)})"
    return {"new": new, "removed": removed, "changed": changed, "summary": summary}


def today_str():
    """Return today's date as YYYY-MM-DD in Mountain Time (approx)."""
    # GitHub Actions runs in UTC; Mountain Time is UTC-7 or UTC-6
    from datetime import timedelta
    mt = datetime.now(timezone.utc) - timedelta(hours=7)
    return mt.strftime("%Y-%m-%d")


def fetch_json_url(url, timeout=30):
    """Fetch JSON from a URL."""
    req = Request(url, headers={"User-Agent": "DenverHomelessTracker/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def fetch_rss(url, timeout=30):
    """Fetch and parse RSS/Atom feed. Returns list of entry dicts."""
    import xml.etree.ElementTree as ET
    req = Request(url, headers={"User-Agent": "DenverHomelessTracker/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()

    entries = []
    root = ET.fromstring(raw)

    # Handle Atom feeds
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns):
        title = entry.findtext("atom:title", "", ns)
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "") if link_el is not None else ""
        published = entry.findtext("atom:published", "", ns) or entry.findtext("atom:updated", "", ns)
        summary = entry.findtext("atom:summary", "", ns) or entry.findtext("atom:content", "", ns) or ""
        entries.append({"title": title, "link": link, "published": published, "summary": summary[:500]})

    # Handle RSS 2.0 feeds
    for item in root.findall(".//item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        published = item.findtext("pubDate", "")
        summary = item.findtext("description", "")[:500] if item.findtext("description") else ""
        entries.append({"title": title, "link": link, "published": published, "summary": summary})

    return entries
