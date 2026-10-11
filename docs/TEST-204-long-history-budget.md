# TEST-204 — long-history request budgeting

Baseline: TEST-203 `74cfd1373fd7f876ee1e7a27bb196cea630996fb`.

## Problem
The provider previously reduced reference documents only. A conversation containing
many messages, or an old person's large derived learning inputs, could exceed the
local UTF-8-byte input bound even after all references had been removed. This failed
before sending an analysis request. The persisted conversation was not damaged.

## Behavior
All reduction happens on the existing deep-copied provider snapshot. Under budget,
contexts are unchanged. When over budget:

1. Omit oversized person-wide derived learning inputs, preserving strategy constraints.
2. Reduce oldest identified chat records in batches, initially retaining eight recent
   messages and all explicit current-turn, required, and recommendation evidence IDs.
3. Remove optional draft evidence only when it is neither current focus nor supporting
   a recommendation. Reduce references using the existing policy.
4. If still needed, reduce the recent window to two messages plus protected records.

Each request carries an explicit history_window coverage/omission notice. It is not
an abstractive summary and does not claim to retain every old fact or boundary. The
analysis result carries a Chinese coverage notice in analysis_constraints, displayed
in the reply workspace. Message bodies, timestamps, IDs, latest target, recommendations,
and their required provenance are never partially truncated. Stored history is unchanged.

If mandatory content or fixed request/schema overhead still cannot fit, fail before
network access with a specific actionable error. A single oversized latest message is
not automatically split. No unlimited-history or exact token-count guarantee is made:
the existing input setting remains a conservative UTF-8 byte bound including request
schema/system overhead, with output reserved separately.

A provider context-length error may trigger one smaller-budget context retry, including
when no references exist. Authentication, rate-limit and other errors are not retried.
Logs contain sizes/counts, not chat text, credentials or IDs. No new runtime dependencies,
DB migrations, provider accounts, background tasks or production configuration changes.

## Validation
Mocked DeepSeek/Qwen analysis and drafting; required historical provenance; latest user
turn; oversized mandatory message rejection; no mutation; smaller context retry; no
retry on auth/rate-limit/upstream errors. Real application route/database pipeline with
60 messages verifies a generated reply citing the newest incoming message and no DB
changes. Existing TEST-200, TEST-203, freshness and UI tests remain intact. Linux full
suite and mobile/desktop browser checks run in the TEST-204 workflow.

## Deployment boundary
GitHub CI success is not production deployment. Upload an exact Git bundle, run server
isolation, then deploy from TEST-203 with final backup and rollback. Do not run an extra
default timestamp-named backup immediately before systemd start: ExecStartPre already
creates one. Use the unique deployment baseline backup for manual preflight instead.
