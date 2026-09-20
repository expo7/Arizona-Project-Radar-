# Arizona Project Radar — source of truth

## Objective
Turn newly published Arizona construction permits into an actionable review queue for contractor or supplier outreach. Initial inspiration: permit leads in Kingman and Buckeye. First version is an honest local review desk; no live collection or verified feeds are connected.

## Current state
Python standard-library server, SQLite records, CSV import, source links, text/county/status/stage filtering, 25-per-page review list, qualification status and notes. Lead investigation fields store plan number, parcel, owner, GC, later permits/trades, contact and evidence; stage is manually verified. Stable `(source, permit_id)` deduplication preserves review history. Local command `python sync_permits.py` pulls recently issued records from the Maricopa County Building Permits public ArcGIS view, with no scheduler yet. Separate Phoenix Project Leads task checks City of Phoenix plan-review records daily and traces successors; no Phoenix PDD ingestion or automatic verification exists in Radar. Repository: https://github.com/expo7/Arizona-Project-Radar- . No production URL has been established.

## Next priority
1. Evaluate the first feed's quality and source links; add City of Phoenix PDD plan-review ingestion and successor checks when a stable authorized source can be verified.
2. Add scheduled ingestion with freshness and change detection.
3. Add contact enrichment carefully, excluding businesses the owner doesn't want targeted.
4. Add authentication, backups, CI and exact-revision deployment before hosting.

## Guardrails
Never invent permits or mix examples with live records. Confirm source terms and current records before publishing claims. Keep credentials outside code; treat source URLs and lead status as auditable facts.
