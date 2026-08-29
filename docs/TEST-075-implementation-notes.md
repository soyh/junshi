# TEST-075 Implementation Notes

The Strategy Decision consumer receives StructuredAnalysis only as derived, request-scoped input.

The existing decision lifecycle remains authoritative: candidates and candidate identity come from the existing Strategy Decision synthesis; `selection_status` remains `requires_explicit_decision`; analysis cannot create or confirm a decision.

The bridge preserves `evidence_source_ids` and keeps unknowns separate from observed facts. No StructuredAnalysis persistence or action decision/execution/outcome side effects are introduced.
