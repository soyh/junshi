# TEST-076 — StructuredAnalysis → Strategic Reply 最小消费契约

状态：IMPLEMENTATION IN PROGRESS

目标：在不建立第二套回复生成体系、不改变现有 Strategic Reply 生命周期的前提下，让 StructuredAnalysis 成为 Strategic Reply 的 request-scoped derived input。

主链：
`AnalysisContext → StructuredAnalysis → Existing Strategic Reply Context`

本阶段边界：
- Strategic Reply 读取 StructuredAnalysis，但不把 derived interpretation 写入 canonical data。
- 保留 observed_facts / inferences / hypotheses / emotional_signals / relationship_signals / risk_signals / intent_signals / unknowns。
- 每个分析项的 evidence_source_ids 原样保留。
- `reply_inputs.analysis_is_derived` 明确标记输入来源。
- `draft` 仍只来自现有 evidence-backed recommendation contract；StructuredAnalysis 本身不得直接变成 draft。
- 不自动选择 recommendation。
- 不自动发送消息。
- 不改变 relationship state。
- 不新增数据库表或 migration。

实现：
- `StrategicReplyAnalysisBridgeService`：只负责 derived input projection。
- `AnalysisStrategicReplyService`：复用现有 AnalysisLLMService 与 StrategicReplyService，完成 request-scoped orchestration。
- `GET /api/v1/conversations/{conversation_id}/strategic-reply/context`：独立于 deterministic context endpoint 的 LLM-backed derived context entrypoint。

验收重点：
1. StructuredAnalysis provenance 与 unknowns 保留。
2. derived semantics 不丢失。
3. 现有 draft/recommendation 语义不被 LLM 输出覆盖。
4. user/person/conversation isolation 不改变。
5. LLM failure 返回 502。
6. 无 action decision / execution / outcome side effect。
7. 相关专项、Strategy/Analysis 回归、全量 pytest 均通过。
