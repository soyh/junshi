# TEST-205 — nonempty replies and current conversation responses

Baseline: TEST-204 b13d593ba18c9834094a181b7b4ad9e8867d9e20.

Explicit generation must not report success when no usable draft is produced. Reject
whitespace/control/format-only reply strings; return an allowlisted error for an empty
candidate set or invalid draft. Generic non-generating context readers retain their
existing optional-draft behavior. Do not fabricate fallback text or evidence.

Analysis orders message timestamps by their actual Julian instant instead of lexical
ISO strings, preserving created_at/rowid tie order. This handles mixed UTC offsets.
The user's reported cooking conversation followed by `你在干嘛呐` is covered, including
an imported older message whose ISO string sorts after the actual newest incoming turn.

Frontend generation captures person, conversation, auth token and a revision. Ignore
late successes AND late failures after a newer generation or evidence change. Clear
previous drafts when a new request starts. Changes during automatic generation coalesce
into one pending refresh and only run in the still-selected scope. Scheduled automatic
recovery is cancelled on scope/revision change. Display the actual latest-message
snapshot next to the result using textContent. Provenance checks remain mandatory;
referencing the correct ID is not a guarantee of semantic reply quality.

Reference retrieval is unchanged: global previews are not conversation-specific model
selection, 24 candidates out of 44 is the configured cap, and missing guide targets are
warnings. Uploaded skill documents cannot themselves enable persistent long-term memory.
No migration, dependency, production configuration, Nginx or certificate changes.

Tests use synthetic records and mocked providers only. No paid model calls. Linux CI
runs focused/full pytest plus desktop/mobile deterministic out-of-order response,
empty-draft, cross-conversation and pending-refresh browser scenarios, and TEST-203/204
browser regressions. Production deployment is a separate verified step.


## Chinese date/time presentation
Chat history, edit prompts, import previews, reply-target display and message management
use Asia/Shanghai, Chinese year/month/day labels and h23 (24-hour) time. Inputs without
an explicit offset are interpreted as +08:00; explicit ISO offsets retain their instant.
Message date filters and media evidence inputs use Beijing time, independent of device
locale/timezone. Minute-precision import previews do not invent displayed seconds.
Raw persisted timestamps are not rewritten. Invalid calendar dates/24:00 are rejected.
