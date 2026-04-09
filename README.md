# Denver Homelessness Tracker

Central intelligence repository tracking everything related to homelessness in Denver. Automated daily scraping of public data sources with a minimal dashboard frontend.

## Data Streams

| Stream | Source | Frequency | Output |
|--------|--------|-----------|--------|
| Encampment Reports | Denver PocketGov / ArcGIS | Daily | `encampment_reports.json` |
| Encampment Visits | ArcGIS outreach data | Daily | `encampment_visits.json` |
| Encampment Closures | ArcGIS closure areas | Daily | `encampment_closures.json` |
| Encampment Disruptions | ArcGIS sweep/disruption data | Daily | `encampment_disruptions.json` |
| Encampment Services | ArcGIS trash/portolets/sharps | Daily | `encampment_services.json` |
| Encampment Trash | ArcGIS trash service | Daily | `encampment_trash.json` |
| Crime | Denver Open Data (NIBRS) | Daily | `crime.json`, `crime_summary.json` |
| Shelters | Active + cold weather shelters | Daily | `shelters.json` |
| Housing | HOST affordable housing, DHS | Daily | `housing.json` |
| News | RSS from 6 Denver outlets | Daily | `news.json` |
| Legislation | Colorado bills (OpenStates) | Daily | `legislation.json` |
| Spending | USASpending + BIO grants | Daily | `spending.json` |
| Nonprofits | ProPublica 990 filings | Daily | `nonprofits.json` |

## Secrets Required

| Secret | Required By | How to Get |
|--------|-------------|------------|
| `OPENSTATES_API_KEY` | `legislation.py` | Free at [openstates.org](https://openstates.org/accounts/signup/) |

No other API keys required — all ArcGIS, USASpending, ProPublica, and RSS sources are open.

## Architecture

Standard Dreck Suite pattern:
- **GitHub Actions**: deploy-first → scrape → deploy-after (DST-aware dual cron)
- **Python scrapers**: One per data source, all in `scrapers/`
- **Data output**: JSON files in `data/`, committed by workflow
- **Diff tracking**: Each scraper maintains `*_previous.json` for change detection
- **Frontend**: GitHub Pages with auth.js, Leaflet map, stats dashboard
- **Entity master**: `data/stakeholders.json` — cross-reference for analysis

## Local Development

```bash
cd scrapers
python3 run_all.py          # Run all scrapers
python3 encampment_reports.py  # Run single scraper
```

## Analysis

The primary value is the data layer. Bring JSON files into a Claude conversation for ad-hoc analysis:
- Trend encampment reports by neighborhood over time
- Correlate sweep activity with 311 complaint displacement
- Monitor shelter capacity utilization
- Track which stakeholders are most active
- Surface spending patterns and large contracts
- Connect policy actions to prior council votes
