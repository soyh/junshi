# Analysis → LLM → Structured Analysis → Strategy Contract

更新时间：2026-08-29
状态：ARCHITECTURE FROZEN

## 1. Purpose

This document freezes the architectural boundary between deterministic application context, LLM-derived interpretation, and downstream strategy. It is intended to stop incremental field-by-field expansion of Analysis Context and prevent the LLM layer from leaking into persistence, evidence, learning, decision, or execution responsibilities.

The frozen pipeline is:

`Canonical Data → Canonical Evidence / Domain Context → AnalysisContext → LLM Analysis → StructuredAnalysis → Strategy → Human Confirmation → Execution / Outcome`

No database migration, persistence rewrite, or existing lifecycle rewrite is required by this contract.

## 2. Layer ownership

### Layer 1 — Persisted / canonical data

Owns durable facts and lifecycle state:

- persons
- conversations
- messages
- interactions
- action feedback / outcomes
- memory updates
- strategy decisions
- action executions

Repositories remain the only persistence access boundary for services. The LLM layer has no repository or SQLite access.

### Layer 2 — Canonical evidence and domain context

Owns deterministic, source-backed assembly of information required for analysis. Existing services remain authoritative for their domains, including conversation messages, canonical evidence, relationship state, and learning strategy context.

This layer may read and aggregate canonical data but must not call an LLM, mutate persisted state, execute actions, send messages, or convert inference into fact.

### Layer 3 — AnalysisContext

`AnalysisContext` is the stable, deterministic input contract for analysis.

It is conversation-scoped and may contain:

- conversation
- person
- messages
- evidence
- relationship_state
- learning_strategy
- existing source-backed facts / unknowns / deterministic context fields where already established by the current contract

`AnalysisContext` is not an AI answer. Its job is to provide canonical, source-backed context and constraints to the next layer.

The current `/api/v1/conversations/{conversation_id}/analysis/context` endpoint remains a context-read endpoint. It must remain read-only, deterministic, user/person isolated, and free of LLM calls.

### Layer 4 — LLM Analysis

The LLM is an interpretation engine operating on an `AnalysisContext` snapshot.

The LLM boundary is explicit:

`AnalysisContext → LLM adapter/service → StructuredAnalysis`

The LLM adapter may select/configure a provider and translate the provider response into the application contract, but it must not access repositories directly or perform domain mutations.

Provider-specific response formats must not leak into the domain contract.

### Layer 5 — StructuredAnalysis

`StructuredAnalysis` is derived output from the LLM. It is not canonical truth.

The first contract should be intentionally small and extensible. Its conceptual fields are:

- `summary`
- `observed_facts`
- `inferences`
- `unknowns`
- `hypotheses`
- `emotional_signals`
- `relationship_signals`
- `risk_signals`
- `intent_signals`
- `evidence_links`
- `analysis_constraints`

Every inference, hypothesis, or material signal should preserve links to the source evidence used to derive it. LLM output must never silently promote an inference to a persisted fact.

### Layer 6 — Strategy

Strategy consumes `StructuredAnalysis` together with the canonical context required by the existing strategy contracts.

Strategy owns:

- recommendations
- strategic reply candidates
- action-plan candidates
- strategy decision inputs

Strategy does not own persistence of LLM output as canonical fact, and it does not bypass explicit decision/confirmation boundaries.

### Layer 7 — Human confirmation and execution

Existing decision, confirmation, execution, feedback, and outcome lifecycle remains authoritative.

LLM output cannot directly:

- send a third-party message
- execute an action
- change a relationship state
- modify learning history
- mark a strategy decision as successful
- overwrite canonical evidence

## 3. No-LLM boundary

The project no longer has a global no-LLM rule.

Instead, the following layers remain explicitly no-LLM:

- persistence / repositories
- canonical evidence
- relationship state assembly
- learning strategy context assembly
- AnalysisContext construction
- existing decision / execution lifecycle services

The LLM is introduced only after the deterministic `AnalysisContext` boundary.

This preserves the guarantees established by earlier TEST stages while allowing real AI analysis to begin without refactoring the lower layers.

## 4. Source-of-truth rules

Canonical persisted data and canonical evidence are the source of truth.

LLM output is always derived interpretation.

Therefore:

1. An LLM inference is not a fact merely because the model produced it.
2. An LLM hypothesis is not a relationship-state transition.
3. An unknown must remain unknown when evidence is insufficient.
4. Evidence provenance must survive the transition from AnalysisContext to StructuredAnalysis.
5. Strategy must distinguish observed evidence from derived interpretation.
6. No downstream layer may treat model confidence as proof of truth.

## 5. Evidence provenance contract

A derived item should identify the canonical evidence supporting it whenever applicable.

Conceptually:

```json
{
  "type": "inference",
  "content": "...",
  "confidence": 0.72,
  "evidence_source_ids": ["message-id-1", "interaction-id-2"]
}
```

`confidence` is model confidence/uncertainty metadata, not a truth score and not an execution authorization.

The exact JSON/schema representation may evolve, but the provenance requirement is frozen.

## 6. Strategy boundary

The Strategy layer may use StructuredAnalysis to generate or rank candidate strategies according to its own deterministic constraints and existing contracts.

It must not:

- turn unsupported model claims into canonical facts
- bypass `requires_explicit_decision`
- bypass human confirmation
- auto-send
- auto-execute
- rewrite learning evidence
- fabricate successful outcomes

Existing Strategy Decision, Strategic Reply, Action Plan, learning, feedback, and execution contracts remain authoritative.

## 7. API boundary

The existing context endpoint remains deterministic:

`GET /api/v1/conversations/{conversation_id}/analysis/context`

A future LLM analysis endpoint must be a separate contract from the context endpoint. It must not change the meaning of the existing context endpoint into “AI answer”.

The preferred conceptual separation is:

`GET .../analysis/context` → canonical input context

`POST .../analysis` or equivalent future endpoint → derived StructuredAnalysis

The exact endpoint name is intentionally not frozen yet; the layer boundary is frozen first.

## 8. Persistence policy

The first LLM implementation does not require a new database table.

StructuredAnalysis should initially be treated as derived, request-scoped output unless a later product requirement proves that persistence is necessary.

If persistence is later introduced, it must be a separate explicit design decision and migration. It must not silently reuse canonical fact tables.

## 9. Error and determinism rules

The deterministic context layer must continue to return stable, reproducible data for the same underlying state.

LLM calls are inherently non-deterministic and must therefore be isolated from deterministic context tests.

Tests for AnalysisContext must continue to work without network/provider credentials and without making an LLM call.

LLM tests should validate:

- input contract compatibility
- structured output validation
- evidence provenance preservation
- unknown preservation
- provider failure handling
- malformed model output handling
- no mutation / no execution side effects

## 10. Security and isolation

All existing user/person isolation rules remain unchanged.

An LLM call must receive only the context authorized for the requested user/person/conversation.

The LLM service must not fetch unrelated users, persons, conversations, or repository records.

Secrets/provider credentials belong to configuration infrastructure and must never become part of AnalysisContext or StructuredAnalysis.

## 11. Frozen non-goals

The following are explicitly out of scope for the first LLM boundary:

- vector database
- PostgreSQL
- Redis
- Elasticsearch
- direct repository access from LLM code
- autonomous messaging
- autonomous action execution
- autonomous relationship-state mutation
- automatic learning writes
- automatic strategy-decision confirmation
- replacing canonical evidence with model-generated evidence
- large-scale refactoring of existing services

## 12. Minimal implementation sequence

The next implementation should follow this order:

1. Freeze and document `AnalysisContext` as the deterministic input contract.
2. Add a provider-neutral LLM adapter boundary.
3. Define a minimal `StructuredAnalysis` schema with strict validation.
4. Add an analysis service that maps `AnalysisContext → StructuredAnalysis`.
5. Add focused tests for provenance, unknowns, isolation, malformed output, provider failure, and no side effects.
6. Integrate StructuredAnalysis into Strategy without changing existing decision/execution semantics.
7. Run focused regression tests, then the full suite.

No TEST should be created solely to propagate another field between layers unless that field represents a real contract requirement.

## 13. Frozen architectural invariants

The following invariants are binding for subsequent development:

1. `AnalysisContext` is deterministic, source-backed context, not AI output.
2. LLM code cannot access repositories or SQLite.
3. LLM output is derived interpretation, never canonical truth by default.
4. StructuredAnalysis preserves evidence provenance.
5. Unknowns are preserved rather than guessed away.
6. Strategy consumes StructuredAnalysis but cannot bypass decision/confirmation.
7. Execution remains human-authorized and lifecycle-controlled.
8. Existing persistence, evidence, learning, decision, and execution contracts are not rewritten merely to introduce LLM analysis.
9. Existing MVP infrastructure constraints remain unchanged.
10. The system may use LLMs only behind the explicit AnalysisContext → StructuredAnalysis boundary.
