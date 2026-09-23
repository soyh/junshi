# TEST-178 VERIFIED

Branch: `test-178-multi-llm-message-history-controls`

Verified SHA: `dcb12fe1e6a2e82c2922aabdbd91e6b157e795a2`

Verified on production server on 2026-09-23.

## Verification summary

- GitHub CI focused suite: 210 passed.
- GitHub CI full suite: 1016 passed.
- Isolated server acceptance: passed.
- Production deployment: passed.
- Production health check on `127.0.0.1:18080`: passed.
- Port 8899 remained unchanged during deployment.
- SQLite migrations 015 and 016 applied successfully.
- SQLite integrity check: `ok`.
- Production functional acceptance: passed.
- Temporary acceptance Person and Conversation were deleted successfully after verification.

## Verified TEST-178 capabilities

### Multi-LLM profiles

- Multiple LLM provider/model profiles per user.
- Active profile selection.
- Provider profile create/update/delete/activate/test APIs.
- Legacy `/api/v1/settings/llm` compatibility retained.
- API keys remain server-side encrypted and are not returned in plaintext.

### Conversation history controls

- Historical message PATCH and DELETE.
- Backend time-window query support using `from`, `to`, and `before`.
- Default history window is the latest 100 messages.
- Older messages can be loaded using `before`.
- UI history window no longer requires loading the complete conversation into the browser.
- Complete canonical history remains available to server-side analysis flows.

### TEST-177 capabilities preserved

- Image/video media attachments.
- Multimodal evidence ingestion and conversation-chain integration.
- Existing authenticated workspace and conversation controls.
- Safe DOM boundary retained.

## Production state at verification

- Branch: `test-178-multi-llm-message-history-controls`
- SHA: `dcb12fe1e6a2e82c2922aabdbd91e6b157e795a2`
- Application port: 18080
- Protected unrelated port: 8899 unchanged
- Database: `/opt/ai-love-strategist/data/app.sqlite3`
- Deployment backup: `/opt/ai-love-backups/test178-20260923-222120`

This SHA is the TEST-178 VERIFIED baseline for subsequent work.
