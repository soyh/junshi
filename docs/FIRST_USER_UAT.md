# TEST-156 — First User End-to-End Validation

Status: IN PROGRESS

Baseline: `9fad72ca9ef6f1721d22c458a61d97619261b4d1` (TEST-155 post-verification handover HEAD)

Production runtime remains the already accepted TEST-155 product code. TEST-156 is a real-user validation stage, not a feature-expansion stage.

## Goal

Validate that one real user can use the product from account login through real relationship evidence, AI analysis, strategic reply, explicit external sending, canonical Message recording, and the existing action/feedback/learning lifecycle without hidden side effects, scope leakage, or data loss.

## Privacy rule

Real relationship/chat content stays in the production database and must not be copied into GitHub UAT artifacts. GitHub results may contain only PASS/FAIL, step identifiers, HTTP/error text with private content removed, anonymized defect descriptions, and non-sensitive runtime metadata.

Never commit passwords, API keys, real names, raw chat messages, screenshots containing private chat content, production `.env`, database files, or recovery material.

## Safety invariants

- Port 8899 is protected and must not be stopped, rebound, modified, or reused.
- No database restore during UAT.
- No environment/data migration during UAT.
- No historical migration edits.
- Strategic Reply must never auto-send or auto-persist as a Message.
- `Prepare sent-message record` may only populate the existing browser Message composer.
- A real Message enters canonical evidence only after the user explicitly presses `Add message`.
- Person / Relationship / Conversation scope must never cross users or persons.
- LLM/derived output is decision support, not ground truth.

## Access

The production application is loopback-only. From a trusted client computer, use an SSH local tunnel rather than exposing port 18080 publicly:

```bash
ssh -N -L 18080:127.0.0.1:18080 <server-user>@<server-host>
```

Then open:

```text
http://127.0.0.1:18080/app
```

Do not route the application through or alter reserved port 8899.

## Phase A — same-session first-user gate

Phase A is the minimum gate for beginning real use. It should be completed in one ordinary product session.

### A01 — Account/session

1. Open `/app` through the trusted tunnel.
2. Register a new first-user account or log into the intended real-user account.
3. Confirm authenticated controls become enabled.
4. Refresh sessions and confirm the current session is visible.
5. Refreshing/closing the browser page may require login again; this is expected because the access token is page-memory only.

PASS: login works, no token appears in URL/local storage, and no other user's data appears.

### A02 — LLM Provider

1. Open `LLM Provider`.
2. Use `Load` first if a provider is already configured.
3. If configuration is missing, enter the intended OpenAI-compatible base URL/model/API key directly in the product UI. Do not put the API key in GitHub or chat logs.
4. Press `Test connection`.

PASS: provider connection succeeds and the API key is not rendered back into the page after save/load.

### A03 — Canonical Person / Relationship / Conversation

1. Create one real Person.
2. Create the Relationship under that Person.
3. Set only information you genuinely know; keep unknown fields unknown instead of inventing facts.
4. Create one Conversation bound to that Person and, when applicable, the Relationship.
5. Re-select the Person/Relationship/Conversation and confirm state remains consistent.

PASS: IDs/scopes remain attached to the selected Person; switching Person never displays another Person's relationship or conversation state.

### A04 — Real evidence input

Use one of the existing canonical paths:

- `Messages` for individual messages; or
- `Text Import` when importing a real conversation in the supported timestamp/sender/content format.

For Message sender types, use the actual source semantics (`user`, `person`, etc.). Enter the real sent time when known.

PASS: saved messages reappear after refresh and are ordered correctly; no duplicate or phantom Message appears.

### A05 — Evidence / Timeline

Load the evidence/timeline views for the selected Person/Conversation.

PASS: source-backed evidence corresponds to what was actually entered; missing information remains missing/unknown rather than being fabricated.

### A06 — Structured Analysis

Run Structured Analysis explicitly for the selected Conversation.

Review at minimum:

- summary;
- observed facts;
- inferences;
- unknowns;
- relationship/emotional/risk/intent signals;
- evidence linkage.

PASS: factual observations can be traced to real evidence; inference is distinguishable from fact; unknowns are preserved; no other Person's content appears.

### A07 — Strategy / Recommendation

Explicitly load Strategy / Recommendation for the same scope.

PASS: recommendations are understandable, tied to current context, and are not automatically selected/executed.

### A08 — Strategic Reply

1. Explicitly generate a Strategic Reply.
2. Review `Why this reply`, recommendations, constraints, and learning strategy.
3. Edit the draft locally if needed.
4. Test `Restore generated draft` once.
5. Re-apply the final desired edit.
6. Press `Copy edited reply`.

PASS: generation is explicit; editing/restore/copy does not create a Message; nothing is sent automatically.

### A09 — Real external send

Send the reviewed text yourself in the actual external chat application.

This external send is intentionally outside AI Love Strategist.

PASS: the product does not claim or infer that a message was sent before you actually send it.

### A10 — Strategic Reply → canonical Message handoff

Only after the external send:

1. Return to Strategic Reply.
2. Press `Prepare sent-message record`.
3. Confirm the existing Message composer receives the text.
4. Confirm sender is `user`.
5. Confirm `Sent at` remains for user review rather than being silently fabricated.
6. Compare Message content with what was actually sent externally; edit the composer if the external text differs.
7. Enter the real sent time when known.
8. Press the existing `Add message` button separately.
9. Refresh Messages.

PASS: no Message exists before step 8; after step 8 exactly one intended outbound Message appears as canonical evidence.

### A11 — Evidence closes the loop

Reload timeline/evidence and, when useful, re-run analysis.

PASS: the newly recorded real outbound Message is now visible as evidence; the unsent/generated draft itself was never persisted separately.

## Phase A release criterion

Phase A passes when A01–A11 complete without a blocking defect and all safety invariants hold.

At that point the project is usable by the first real user for day-to-day evidence + analysis + strategic reply workflows while TEST-156 remains open for longitudinal validation.

## Phase B — longitudinal lifecycle gate

Phase B validates the longer relationship-decision lifecycle and may span multiple real interactions. It should not be artificially rushed just to close a test number.

### B01 — Incoming response

When the other person actually replies, record the real incoming Message with sender `person` and real timestamp when known.

PASS: new evidence is source-correct and scoped to the same Person/Conversation.

### B02 — Re-analysis after new evidence

Run analysis again after meaningful new evidence.

PASS: the new evidence affects derived analysis where relevant without overwriting historical source evidence.

### B03 — Action Plan

Explicitly generate/save an Action Plan when the real situation warrants one.

PASS: plan remains proposed and requires user confirmation; no Decision or Execution is silently created.

### B04 — Action Decision

Explicitly confirm or reject an appropriate proposed recommendation/action.

PASS: Decision records the user's actual choice and does not itself start Execution.

### B05 — Action Execution

Only after a confirmed decision, explicitly record/start the canonical execution step according to the existing UI contract.

PASS: execution is a separate user action and does not auto-create Outcome.

### B06 — Outcome

After the real-world action has an actual result, record `completed`, `skipped`, or `failed` truthfully.

PASS: no fabricated outcome; one outcome per eligible decision; scope remains correct.

### B07 — Feedback

Explicitly load Feedback.

PASS: observed outcome and unknown outcome are distinguished; feedback remains source-backed/read-only.

### B08 — Learning

Explicitly load/generate the existing Learning workflow as appropriate.

PASS: learning is derived from canonical history and does not rewrite source evidence.

### B09 — Persisted Learning history

Load persisted learning history for the current Person.

PASS: saved learning belongs only to that user + Person and does not invoke hidden re-analysis merely by reading history.

### B10 — Re-analysis

Explicitly run Re-analysis after meaningful outcome/learning evidence exists.

PASS: re-analysis remains user-triggered and preserves the canonical chain from source evidence to derived learning/analysis.

## Blocking defects — stop UAT immediately

Stop and report the step identifier if any of these occurs:

- another user's or another Person's private data appears;
- a generated draft is automatically saved as a real Message;
- an external message is sent automatically;
- Action Plan/Decision/Execution/Outcome is created without the documented explicit user action;
- duplicate Message/Outcome is created from one click;
- a real saved record disappears after refresh;
- a 500 error occurs on the canonical happy path;
- production becomes not-live/not-ready;
- port 8899 ownership changes;
- database restore/migration is unexpectedly triggered.

## Non-blocking usability findings

Record these even if the flow technically works:

- unclear next step;
- confusing labels;
- too many clicks;
- context difficult to understand;
- AI output useful but hard to act on;
- response latency feels disruptive;
- page requires excessive scrolling;
- difficult Person/Conversation switching;
- unclear difference between fact/inference/unknown;
- Strategic Reply requires too much manual cleanup.

## Defect reporting format

Do not include raw private conversation content.

```text
TEST-156 STEP: A08
RESULT: FAIL | PASS_WITH_ISSUE
SEVERITY: blocking | high | medium | low
EXPECTED: <sanitized expectation>
ACTUAL: <sanitized actual behavior>
ERROR: <HTTP/status/error text if any; remove private content>
REPRODUCIBLE: yes/no
NOTES: <sanitized notes>
```

## TEST-156 completion

TEST-156 becomes VERIFIED only after:

1. Phase A passes with a real user and real evidence;
2. no blocking privacy/scope/automatic-side-effect defect remains;
3. important usability defects discovered in Phase A are triaged;
4. Phase B has enough genuine real-world events to validate the existing longitudinal lifecycle rather than synthetic button-clicking;
5. final results are recorded in sanitized form, with no private relationship/chat content in GitHub.
