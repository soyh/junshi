# TEST-206 Latest-turn recovery

Baseline: TEST-205 fb9d996bb11ed8b86a45b66035bf3c5864905ca4, deployed successfully.

The public error `latest conversation was not incorporated` combined two failures:
no usable recommendation cited the latest incoming message, or the final draft did
not cite it. Analysis may mention the latest message in observed facts but only
analysis hypotheses produce recommendations. Merely recognizing that message is
therefore insufficient. A real provider response has not been captured; we cannot
claim which stage caused this user's particular failure.

Put the exact latest-message ID and stage-specific instructions prominently in the
provider prompt. Correct a typed freshness failure once per affected stage, using
the original context and mandatory IDs. Retain all canonical/provenance validation;
never append citations to model output or manufacture a hypothesis/draft. Healthy
requests still use one analysis and one drafting call. Each stage has at most one
extra generation attempt. Reference routing and existing bounded transport/context
fallbacks remain separate. No automatic retry of auth/network errors or arbitrary
invalid provenance is added.

If correction also fails, report the failing stage in Chinese without private IDs,
chat contents or upstream response bodies. The browser must not automatically rerun
the entire pipeline after this bounded correction is exhausted. Explicit manual
retry remains available.

Tests use HTTP mocks with the user's qwen3.7-flash model name and DashScope-compatible
URL. These verify the real adapter, prompt, orchestration and persisted-data boundary;
they do not call a paid account or prove the real model will always comply. Existing
strict freshness rejection tests stay unchanged. Linux CI runs focused and full tests
and browser regressions. No migrations, dependencies or deployment settings change.
