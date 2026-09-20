# Agent instructions

Read `SOURCE_OF_TRUTH.md` and `README.md` before changing the product. Preserve provenance: every imported record has a named source and stable permit ID. Do not present sample data as live. Keep the local server loopback-only until authentication and CSRF protection are in place. Run an import/deduplication and status-persistence smoke check after changing data behavior. Never add secrets or production credentials to the repository.
