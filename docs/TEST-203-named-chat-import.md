# TEST-203: named chat transcript import

Baseline: TEST-202 `e11309593d773fc8d3288a54ed47c2f464941dd1`.

Previously a transcript such as the following was saved as one ordinary message.
The unified importer now detects the Chinese date lines and offers a read-only
preview before writing messages to the selected conversation.

```text
ID1
2026年09月26日 10:40
早早早

ID2
2026年09月26日 10:40
早呀
```

- Paste text or upload UTF-8 `.txt` / `.md` (file limit 1 MB).
- Confirm the source UTC offset; default `+08:00` is shown explicitly.
- Choose two different detected usernames for self (`user`) and other (`person`).
  No identity is automatically assigned. Additional usernames block the import.
- Review messages, then click the existing add button and confirm the count and
  identity mapping. Preview is paginated in batches of 100 without limiting import.
- Body lines and internal blank lines are preserved. A username immediately
  followed by a Chinese date line begins the next record. This structural sequence
  inside quoted message content is inherently ambiguous; review before importing.
- Minute-only times are displayed to the minute and stored with seconds `00`.
  Optional explicit seconds are supported. Equal timestamps preserve source order.
- Invalid dates, empty messages and unrecognized preamble are rejected with line
  information. No model is used for parsing or preview.
- Editing the text/timezone or changing the conversation invalidates the preview.
  The server independently reparses the submitted original text and validates the
  complete identity mapping and conversation ownership before writing anything.
- Existing single-message and pipe-delimited import routes remain intact.

Endpoints: authenticated `POST /api/v1/text-imports/preview` (no-store), existing
`POST /api/v1/text-imports` with `source_format=named_chat`, `self_name`,
`other_name`, and `utc_offset`. Development authentication fallback is unchanged;
production preview and commit require a session.

No database migrations, runtime dependency or deployment configuration changes.
After confirmed import the existing evidence-change event is emitted, so existing
automatic analysis behavior can still call the configured model; preview does not.

Validation: parser/API regression tests, old import compatibility tests, full suite
on Linux, mocked browser flows at 390px and 1280px, and real composed-page startup.
No production server or paid model account is used in tests.
