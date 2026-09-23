# TEST-179 VERIFIED Handoff

## Baseline

- Functional branch: `test-179-vision-model-routing-runtime-config`
- VERIFIED candidate SHA: `d2bf2df935d2add9a11d3c3e370ef0e862a7839b`
- Parent VERIFIED baseline: `TEST-178-VERIFIED` / `dcb12fe1e6a2e82c2922aabdbd91e6b157e795a2`
- Production branch: `test-179-vision-model-routing-runtime-config`
- Production 18080 PID at final acceptance: `680724`
- Port 8899 remained untouched at PID `52822`

## Delivered capability

- Primary text/analysis model and vision/media model are independently selectable.
- Existing `is_active` continues to represent the primary model for backward compatibility.
- A dedicated per-user vision selection is stored in `user_llm_vision_profile_selection`.
- If no vision profile is selected, media analysis falls back to the primary model.
- Media image/video analysis resolves through the vision provider path and continues to write recognized media evidence into the conversation evidence chain.
- UI exposes primary model, vision model, follow-primary fallback, and real vision-capability testing.
- Vision capability test sends a real image request using the same `image_url` payload shape used by production media analysis.
- Runtime `.env` loading uses stable absolute project paths so `LLM_CONFIG_ENCRYPTION_KEY` is not dependent on uvicorn working directory.

## Production model roles at acceptance

- Primary profile: `Default`
- Primary provider: `qwen`
- Primary model: `qwen3.7-flash`
- Vision profile: `Qwen Vision`
- Vision provider: `qwen`
- Vision model: `qwen3-vl-flash`
- Exactly one primary profile remained active.
- API key plaintext was not returned by profile or vision APIs.

## Database

- Migration `017_vision_llm_profile_selection.sql` applied successfully.
- Existing encrypted API-key ciphertext remained decryptable after deployment.
- SQLite `PRAGMA integrity_check` returned `ok`.
- Migration 017 was verified idempotent on an isolated production DB copy before deployment.

## CI and regression

Final GitHub Actions run for `d2bf2df935d2add9a11d3c3e370ef0e862a7839b`:

- TEST-179 focused suite: `217 passed`
- Full suite: `1023 passed`
- Workflow conclusion: `success`

The final probe fix changed only:

- `backend/app/services/vision_llm_provider.py`
- `backend/tests/test_179_vision_model_routing.py`

## Server acceptance

Isolated server acceptance passed before production switch:

- Focused regression: `217 passed`
- Full regression: `1023 passed`
- Migration 017 on DB copy: PASS
- CWD-independent encryption-key loading: PASS
- Existing API-key decryptability: PASS
- Production branch/service/DB remained untouched during isolated acceptance.

Production deployment acceptance passed:

- Branch/SHA locked to TEST-179 candidate.
- `/health`: PASS
- Vision routes registered and authenticated boundary verified.
- TEST-179 UI markers present.
- Migration 017 present.
- DB integrity: `ok`.
- Port 8899 unchanged.

## Real production functional acceptance

Authenticated production acceptance passed with a real account:

- Profile count: `2`
- Primary profile remained `Default / qwen3.7-flash`.
- Vision profile remained `Qwen Vision / qwen3-vl-flash`.
- Primary/vision independence: PASS
- Vision selection persistence: PASS
- Real image request through `/api/v1/settings/llm/vision/test`: PASS
- Result: `status=ok`, `code=ok`
- API key exposure check: PASS

## Backup

Final vision-fix deployment backup:

`/opt/ai-love-backups/test179-vision-fix-20260924-005359`

## Release lock

Create annotated tag:

`TEST-179-VERIFIED`

pointing to:

`d2bf2df935d2add9a11d3c3e370ef0e862a7839b`

Recommended tag message:

`TEST-179 VERIFIED: independent primary and vision model routing`

Future TEST stages should branch from `TEST-179-VERIFIED` / `d2bf2df935d2add9a11d3c3e370ef0e862a7839b`, not from the unrelated current `main` history until main reconciliation is explicitly handled.
