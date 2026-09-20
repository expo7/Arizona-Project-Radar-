# Arizona Project Radar

A local-first desk for reviewing Arizona construction permit leads. Import public permit CSV exports, search by location and project details, follow source links, and save a status and notes for each record. No sample records are presented as real leads.

## Maricopa County permit feed

With the local server stopped or running, run `python sync_permits.py` from this directory to fetch **issued** building permits from the [Maricopa County public Building Permits layer](https://www.arcgis.com/home/item.html?id=86909eb1ea9149308abaadba377f388f). Then refresh the browser. The default window is the past 14 days; `python sync_permits.py --days 30` expands it (maximum 90). Run again whenever you want fresh permits. It does not run automatically or require a key.

The feed covers Maricopa County's published layer, not all Arizona jurisdictions or necessarily every incorporated city. The source link on each card opens the county dataset for verification. Its public layer describes itself as a **snapshot of current permits**; records can disappear or change upstream. We record the date labeled `IssuedDate` as issued date and leave city and value empty because the layer does not provide them. Imported records are retained locally and repeated syncs preserve your notes and statuses. A sync failure leaves existing records alone.

## Run

Requires Python 3.11+. Run `python server.py` and open <http://127.0.0.1:8000>. Data is stored in `radar.sqlite3` in the project directory; override with `RADAR_DB=/path/to/file.sqlite3`.

The desk shows 25 permits per page, newest first. Search and filters apply to all loaded records; changing a filter returns to page one. The overall counts remain totals across all records.

## Investigating early Phoenix leads

The separate Phoenix Project Leads task watches **City of Phoenix plan-review and issued-permit records** for potentially early commercial or industrial work. Its workflow checks a plan number against later building and trade permits, the same parcel and address, and any named general contractor before calling a lead actionable. `TO BE BID` is a prioritization clue, **not proof** that a bid is open. Freshness matters; an old plan or a later named GC is generally a poor early lead.

The review panel now records a plan number, parcel, owner, named GC, later permits/trades, suggested first contact, and evidence notes. You can manually mark a record `TO BE BID · verified` only after adding a plan number or later-permit evidence; other stages are `Unverified`, `GC named`, `Trade work progressed`, and `Closed / stale`. Filter the list by opportunity stage. These fields persist across imports and feed syncs. A blank contractor field in the Maricopa feed means **unknown**, not an unassigned job.

The existing automated feed is **Maricopa County's issued-permit snapshot**, not the City of Phoenix PDD plan-review source. This app does not yet ingest the Phoenix plan-review records or run successor checks automatically. For manual cross-checks, use the [Phoenix plan-review search](https://apps-secure.phoenix.gov/PDD/Search/PlanReviews), [issued-permit search](https://apps-secure.phoenix.gov/PDD/Search/IssuedPermit), and [permit-history search](https://apps-secure.phoenix.gov/pdd/search/permits). Keep the separate task active for daily discovery and alerts.

### Import Phoenix's issued-permit export

The [City of Phoenix issued-permit search](https://apps-secure.phoenix.gov/PDD/Search/IssuedPermit) provides a **Create File** CSV export. Choose a bounded date range there and download the file. From this project folder run `python import_phoenix.py /path/to/download.csv`, then refresh Radar. The command accepts the city's search-criteria line above the CSV header, and maps permit number, issue date, address, parcel, plan number, owner, contractor, and valuation. It fills empty investigation fields but never replaces review entries you have already written. Reimporting the same permit preserves its status and notes.

This is a manual export/import, not an unattended City of Phoenix feed. The importer has been checked against the city's published column names and a representative CSV fixture; it has not yet been verified against a downloaded Phoenix export. A contractor value in an issued-permit export is a reported field, not proof that procurement for all site services is closed. Plan reviews and later permit links still need to be checked before assigning an opportunity stage.

## Import format

The CSV header is `source,permit_id,description,address,city,county,issued_date,permit_type,value,source_url`. All columns are required, but values other than `source`, `permit_id`, and `description` may be blank. Dates use `YYYY-MM-DD`. Use stable source names and permit IDs: imports skip matching pairs and preserve existing review state. The import is atomic and capped at 10,000 records and 5 MB. The UI offers an empty template.

## Scope and next steps

This is a single-user local MVP. It does not scrape permit portals, provide authentication, or send alerts. Before public deployment: add authentication and CSRF protection, backups and deployment checks. Do not expose this server to the internet as is. The default bind address is loopback only.

See `SOURCE_OF_TRUTH.md` for product decisions and `AGENTS.md` for development constraints.
