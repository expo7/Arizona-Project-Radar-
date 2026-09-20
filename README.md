# Arizona Project Radar

A local-first desk for reviewing Arizona construction permit leads. Import public permit CSV exports, search by location and project details, follow source links, and save a status and notes for each record. No sample records are presented as real leads.

## Run

Requires Python 3.11+. Run `python server.py` and open <http://127.0.0.1:8000>. Data is stored in `radar.sqlite3` in the project directory; override with `RADAR_DB=/path/to/file.sqlite3`.

## Import format

The CSV header is `source,permit_id,description,address,city,county,issued_date,permit_type,value,source_url`. All columns are required, but values other than `source`, `permit_id`, and `description` may be blank. Dates use `YYYY-MM-DD`. Use stable source names and permit IDs: imports skip matching pairs and preserve existing review state. The import is atomic and capped at 10,000 records and 5 MB. The UI offers an empty template.

## Scope and next steps

This is a single-user local MVP. It does not scrape permit portals, provide authentication, or send alerts. Before public deployment: choose the first authorized Arizona jurisdiction data source; build a scheduled source adapter and provenance checks; add authentication and CSRF protection; set up backup and deployment checks. Do not expose this server to the internet as is. The default bind address is loopback only.

See `SOURCE_OF_TRUTH.md` for product decisions and `AGENTS.md` for development constraints.
