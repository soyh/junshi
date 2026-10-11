# Uniform compact person profiles

Baseline TEST-209. Every person has the same storage format and context policy;
there are no important/simple-person classes.

The existing summary JSON stores an internal structured entry collection with
facts, preferences, events, boundaries, uncertainties and inferences. Each new
entry carries the batch's validated message evidence. Exact duplicates merge;
unchanged entries persist even when the model omits them from the next delta.
Explicit supersession requires a visible previous entry ID, a same-kind new
replacement, validated batch evidence and a reason. Before/after entries are
audited; inactive entries remain queryable. This validates structure/provenance,
not the semantic truth of a model inference; original messages remain canonical.

The reply context selects complete entries by boundary priority and overlap with
recent messages. Its entire serialized memory object uses at most 10 percent of
the configured input budget, capped at 4096 UTF-8 bytes, conservatively bounding
token use. Sentence truncation is prohibited. Latest human/incoming messages stay
protected. A budget too small even for metadata excludes memory and preserves the
uncompacted message input. Omitted profile entries remain in the database, not the
prompt. The model's combined overview targets 300–600 Chinese characters; longer
overviews are excluded from the reply projection instead of cut mid-sentence.

No additional model call runs solely for consolidation. Exact deduplication and
assembly run locally and completion is marked once all current history is covered.
Legacy completed summaries convert locally without paid calls or fabricated
per-entry evidence. This cannot recover historical details already lost by an
older summary. Raw chat and existing audit history remain available.

The UI shows bounded context usage and a paginated full profile/evidence viewer.
Foreground reply requests defer starting another memory batch or correction for
the same user. Already-running model calls are not canceled. Scheduling is process
local, matching the existing production single worker; not a distributed queue.

No database migration, dependency, historical migration or runtime-config change.
