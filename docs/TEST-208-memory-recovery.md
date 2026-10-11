# TEST-208: Recover incomplete person memory and compact its UI

Baseline: TEST-207, 03bb73321464a423028fb4707a2bd9f041e95697.

Production reported coverage stopping at 32 of 1256 messages. TEST-207 discarded
exception categories, so its historical generic audit cannot establish whether
that particular failure was transport, JSON, schema, budget or provenance.
Do not claim to have identified a specific provider error from that screenshot.

Memory batches now allow an initial attempt plus three corrections for malformed
JSON/schema/provenance and transient transport failures. Budget/context errors
reduce the batch before retrying. Only actually processed messages advance
coverage. Authentication and rate limits do not auto-retry; storage failures
remain transactional. Failure audits and logs use allowlisted categories only,
never exception bodies, API keys or chat content. Completed earlier batches
remain usable and a manual retry resumes the unprocessed part.

The person memory panel displays person, coverage, failure state and retry action
in a compact header. Summary and history default to collapsed. Expanded history
scrolls within a bounded area, preserving open event rows during refresh, and
the update button is disabled while a job is running. Desktop and mobile tests
cover these controls, escaping, dates and horizontal overflow.

No migration, dependency or runtime-service change. Model tests use fakes.
