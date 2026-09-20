# Arizona Project Radar

A local-first desk for reviewing Arizona construction permit leads. Import public permit CSV exports, search by location and project details, follow source links, and save a status and notes for each record. No sample records are presented as real leads.

## Maricopa County permit feed

With the local server stopped or running, run `python sync_permits.py` from this directory to fetch **issued** building permits from the [Maricopa County public Building Permits layer](https://www.arcgis.com/home/item.html?id=86909eb1ea9149308abaadba377f388f). Then refresh the browser. The default window is the past 14 days; `python sync_permits.py --days 30` expands it (maximum 90). Run again whenever you want fresh permits. It does not run automatically or require a key.

The feed covers Maricopa County's published layer, not all Arizona jurisdictions or necessarily every incorporated city. The source link on each card opens the county dataset for verification. Its public layer describes itself as a **snapshot of current permits**; records can disappear or change upstream. We record the date labeled `IssuedDate` as issued date and leave city and value empty because the layer does not provide them. Imported records are retained locally and repeated syncs preserve your notes and statuses. A sync failure leaves existing records alone.

## Run

Requires Python 3.11+. Run `python server.py` and open <http://127.0.0.1:8000>. Data is stored in `radar.sqlite3` in the project directory; override with `RADAR_DB=/path/to/file.sqlite3`.

The desk shows 25 permits per page, newest first. Search and filters apply to all loaded records; changing a filter returns to page one. The overall counts remain totals across all records.

## Import format

The CSV header is `source,permit_id,description,address,city,county,issued_date,permit_type,value,source_url`. All columns are required, but values other than `source`, `permit_id`, and `description` may be blank. Dates use `YYYY-MM-DD`. Use stable source names and permit IDs: imports skip matching pairs and preserve existing review state. The import is atomic and capped at 10,000 records and 5 MB. The UI offers an empty template.

## Scope and next steps

This is a single-user local MVP. It does not scrape permit portals, provide authentication, or send alerts. Before public deployment: add authentication and CSRF protection, backups and deployment checks. Do not expose this server to the internet as is. The default bind address is loopback only.

See `SOURCE_OF_TRUTH.md` for product decisions and `AGENTS.md` for development constraints.
