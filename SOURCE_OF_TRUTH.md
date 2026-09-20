# Arizona Project Radar — source of truth

## Objective
Turn newly published Arizona construction permits into an actionable review queue for contractor or supplier outreach. Initial inspiration: permit leads in Kingman and Buckeye. First version is an honest local review desk; no live collection or verified feeds are connected.

## Current state
Python standard-library server, SQLite records, CSV import, source links, text/county/status filtering, qualification status and notes. Stable `(source, permit_id)` deduplication preserves review history. Repository: https://github.com/expo7/Arizona-Project-Radar- . No production URL has been established.

## Next priority
1. Identify an authorized public feed in one jurisdiction and map its fields to the import schema.
2. Add scheduled ingestion with freshness, source attribution and change detection.
3. Add contact enrichment carefully, excluding businesses the owner doesn't want targeted.
4. Add authentication, backups, CI and exact-revision deployment before hosting.

## Guardrails
Never invent permits or mix examples with live records. Confirm source terms and current records before publishing claims. Keep credentials outside code; treat source URLs and lead status as auditable facts.
