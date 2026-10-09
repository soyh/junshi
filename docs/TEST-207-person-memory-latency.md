# TEST-207: authorized longitudinal memory, audit and import usability

Base: TEST-206 e12ae474d5c61db7977db6f03da9a526efcd0453.
User authorized three correction attempts, no hard ten-second deadline, automatic
relationship/status/summary writes including major changes, and mandatory queryable
before/after records with reasons. Original chat history remains intact.

Correction stages now allow an initial attempt plus three corrections. Transport,
authentication and arbitrary provenance failures do not gain additional retries.
Reference selection is reused inside one provider/request instance only. Timing and
attempt counts return in reply_inputs without prompts or credentials. Concurrent
generation in an unchanged scope shares one pending request.

Migration 020 only adds person_memories and person_update_events. Original migrations
001–019 are unchanged. Person summaries are derived, bounded context, never canonical
evidence. The summary updater processes batches with original timestamps/IDs and
explicitly verified source IDs; status/stage changes and an audit row commit in the
same transaction. It does not hold a write transaction across model calls. Optimistic
checks reject changed messages, person fields, relationships or competing revisions.
Edits/deletions invalidate old summaries; rebuilds start without the invalid summary.
Each refresh processes up to four batches and UI continuation processes the remainder.
Errors stop automatic continuation; users may explicitly retry.

Replies keep the latest 16 original conversation messages plus all unprocessed
messages, together with valid historical memory. This is lossful derived compression,
not a guarantee of complete recall. The full chat stays available in ordinary history
endpoints. Existing relationship selection (oldest relationship row) is preserved.

The authenticated, tenant-scoped memory endpoints expose summary coverage and paged
audit rows. Memory refresh runs separately in background work, never as a prerequisite
to displaying the current reply. Audit UI defaults the description to collapsed,
shows reasons, times in Beijing, and before/after details using textContent.

Single/media time inputs have actual current-Beijing values, persistent help, a date
calendar and explicit 24-hour hour/minute/second selectors. Chinese pipe-separated
batch examples accept 我/对方 and Chinese dates; legacy explicit ISO offsets retain
their meaning. Batch timestamps never use the single-message input.

Release requires Linux focused/full/browser acceptance, migration-copy rehearsal,
and a new deployment script that handles 019→020. Do not reuse the TEST-206 deployment
script (it requires migrations to remain unchanged). No production actions performed.
