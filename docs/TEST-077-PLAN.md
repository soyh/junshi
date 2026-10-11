# TEST-077 Plan

## Scope

Define the smallest downstream contract after TEST-076 for Strategic Reply, while preserving the existing Strategy Decision / Human Confirmation / Execution lifecycle.

## Required reading before implementation

- `docs/ANALYSIS_LLM_STRATEGY_CONTRACT.md`
- TEST-075 StructuredAnalysis → Strategy Decision service/schema/tests
- TEST-076 Strategic Reply analysis bridge/route/schema/tests
- Existing Strategic Reply, Strategy Decision, Action Plan, and Execution services/schema/tests

## Invariants

- `AnalysisContext` remains deterministic, source-backed, and read-only.
- `StructuredAnalysis` remains derived, request-scoped output.
- `reply_inputs` remains derived input, never canonical fact.
- Evidence provenance and unknown semantics must survive every downstream projection.
- No LLM access to Repository/SQLite.
- No automatic decision confirmation.
- No automatic message sending.
- No automatic action execution.
- No relationship mutation caused by LLM output.
- No learning-history writes caused by LLM output.
- No fabricated outcome success.
- Existing user/person/conversation isolation remains authoritative.
- No new database migration unless a separate persistence requirement is proven and explicitly designed.

## Implementation method

1. Inspect the existing downstream Strategic Reply / Decision / Action Plan / Execution boundaries.
2. Identify the smallest real product contract required after TEST-076.
3. Add contract tests first.
4. Implement only the minimum adapter/service/schema changes required by those tests.
5. Run focused TEST-077 tests.
6. Run related Strategy/Strategic Reply regressions.
7. Run the full test suite.
8. Perform server smoke testing last; verify derived-input flow only and verify no send/execute/outcome side effects.
